from main import *
from pathlib import Path
import re
import math

root = Path('AssetBundles')

def get_primary(asset):
    # Returns typetree of the primary asset (as reported by the AssetBundle).
    bundle = asset.objects[1] # m_PathID is always 1 for the AssetBundle
    if bundle.type.name != 'AssetBundle': # in case the above isn't true
        print('Object at m_PathID=1 is not an AssetBundle.\nSearching for AssetBundle...')
        found = False
        for value in asset.values():
            if value.type.name == 'AssetBundle':
                bundle = value
                print('AssetBundle found at m_PathID=', bundle.path_id, '.', sep='')
                found = True
                break
        assert found, 'No AssetBundle found.'
    bundletree = bundle.read_typetree()
    primaryid = bundletree['m_Container'][0][1]['asset']['m_PathID']
    primary = asset.objects[primaryid]
    return primaryid, primary.read_typetree()

def get_dependencies():
    # Returns dependency map linking asset files to their texture files.
    env = UnityPyLoad(str(Path(root, 'dependencies')))
    id, primary = get_primary(env.assets[0])
    dependencies = {}
    for m_Value in primary['m_Values']:
        m_FileName = re.sub('^.*?(/painting/.*)?$', '\g<1>', m_Value['m_FileName'])[1:]
        # m_FileName = re.sub('^.*?(/painting(?:face)?/.*)?$', '\g<1>', m_Value['m_FileName'])[1:] # includes paintingface
        if m_FileName:
            if m_FileName.endswith('_tex'):
                if m_Value['m_Dependencies']:
                    print('Texture file includes dependencies:',  m_FileName)
            elif not m_Value['m_Dependencies']:
                print('Non-texture file without dependencies:', m_FileName)
            dependencies.setdefault(m_FileName, m_Value['m_Dependencies'])
    return dependencies

def get_layers(asset, textures, layers={}, id=None, parent=None, face=None):
    if id is None:
        id, gameobject = get_primary(asset)
    else:
        gameobject = asset[id].read_typetree()

    if gameobject['m_Name'] == 'shop_hx': # the shop_hx layer is white fog censorship
        return

    children = None
    mesh_id = None
    entry = {}
    for ptr in gameobject['m_Component']:
        component_id = ptr['component']['m_PathID']
        component = asset[component_id]
        tree = component.read_typetree()
        if component.type.name == 'RectTransform':
            entry['position'] = tree['m_LocalPosition'] # unused; inaccurate as of 2024-05-16
            entry['scale'] = tree['m_LocalScale']
            entry['delta'] = tree['m_SizeDelta']
            entry['pivot'] = tree['m_Pivot']

            # calculate true m_LocalPosition
            anchormin = tree['m_AnchorMin']
            anchormax = tree['m_AnchorMax']
            anchorpos = tree['m_AnchoredPosition']
            if parent is None:
                entry['bound'] = entry['delta']
                entry['anchor'] = {
                    'x': entry['delta']['x'] * entry['pivot']['x'],
                    'y': entry['delta']['y'] * entry['pivot']['y']
                }
                entry['position'] = anchorpos
            else:
                pl = layers[parent]
                entry['bound'] = { # bounding box width and height
                    'x': pl['bound']['x'] * (anchormax['x'] - anchormin['x']) + entry['delta']['x'],
                    'y': pl['bound']['y'] * (anchormax['y'] - anchormin['y']) + entry['delta']['y']
                }
                entry['anchor'] = { # bounding box anchor in relation to box corner
                    'x': (entry['bound']['x'] - entry['delta']['x']) * entry['pivot']['x'] + pl['bound']['x'] * anchormin['x'],
                    'y': (entry['bound']['y'] - entry['delta']['y']) * entry['pivot']['y'] + pl['bound']['y'] * anchormin['y']
                }
                entry['position'] = { # anchor in relation to parent anchor
                    'x': entry['anchor']['x'] - pl['anchor']['x'] + anchorpos['x'],
                    'y': entry['anchor']['y'] - pl['anchor']['y'] + anchorpos['y']
                }
            # print(id, parent)
            # print(entry['bound'], entry['anchor'], entry['position'])

            if gameobject['m_Name'] == 'face' and face != None: # transplant face into layers
                entry['isFace'] = True
                entry['texture'] = face
                entry['size'] = entry['delta'] # todo: dunno if this is needed
                print(entry)

            children = tree['m_Children']
        if 'mMesh' in tree:
            mesh_id = tree['mMesh']['m_PathID']
            sprite_id = tree['m_Sprite']['m_PathID']
            entry['size'] = tree['mRawSpriteSize']
    if mesh_id is not None:
        texas = {}
        for i in range(len(textures.assets)): # todo: remake this as a function
            texas = texas | textures.assets[i].objects
        try:
            entry['mesh'] = texas[mesh_id].read()
        except:
            print('No mesh found.')
        sprite = texas[sprite_id].read_typetree()
        texture_id = sprite['m_RD']['texture']['m_PathID']
        print('txt', texture_id)
        entry['texture'] = texas[texture_id].read()
    if parent is not None:
        entry['parent'] = parent

    layers[id] = entry

    if children is not None:
        for rt_ptr in children:
            rt_id = rt_ptr['m_PathID']
            rt = asset[rt_id].read_typetree()
            child_id = rt['m_GameObject']['m_PathID']
            get_layers(asset, textures, layers, child_id, id, face)

def wrapped(painting_name, out_file, crop, keep, facename, facetype, factor):
    ################################################################
    # todo: check and delete (patch 2024-05-16 changed everything)
    ################################################################
    # oddity: jiahe_3-5 output jiahe_6 for some reason
    #         also linghangyuan33_1 (TBPeppy) outputs linghangyuan33_2 (TBPeppySchool)
    #         in these cases, use https://github.com/Krazete/azur-paint/blob/c7689d/main.py
    #                         and maybe change line 101
    #                        from return Image.new('RGBA', size)
    #                          to return Image.new('RGBA', (dx, dy))
    ################################################################

    # painting_name = 'shaenhuosite_alter'
    # painting_name = 'makeboluo'
    # painting_name = 'tower'
    # painting_name = 'adaerbote_2'
    # painting_name = 'ankeleiqi'
    # painting_name = 'kelaimengsuo'
    # painting_name = 'buleisite_2'

    depmap = get_dependencies()
    textures = UnityPyLoad(*['{}/{}'.format(root, fn) for fn in depmap['painting/{}'.format(painting_name)]])

    # face stuff
    face = None
    if facename != None:
        faces = UnityPyLoad(str(Path(root, 'paintingface', facename)))
        for value in faces.assets[0].values():
            if value.type.name == 'Texture2D':
                face = value.read()
                if face.name == facetype:
                    break

    env = UnityPyLoad(str(Path(root, 'painting', painting_name)))
    layers = {}
    get_layers(env.assets[0], textures, layers, face=face) # keys ordered bottom to top

    for i in layers: # todo: find a better way to search for the base layer
        layer = layers[i]
        if 'parent' not in layer:
            layer['scale'] = {'x': 1, 'y': 1, 'z': 1} # quickfix, ignores topmost scaling

    def get_position_box(layer, x=None, y=None, w=None, h=None): # todo: add upscale parameter
        if x is None or y is None:
            x = layer['delta']['x'] * layer['pivot']['x'] * layer['scale']['x'] - layer['position']['x']
            y = layer['delta']['y'] * layer['pivot']['y'] * layer['scale']['y'] - layer['position']['y']
            w = layer['delta']['x'] * layer['scale']['x']
            h = layer['delta']['y'] * layer['scale']['y']
        if 'parent' in layer:
            parent = layers[layer['parent']]
            x = x * parent['scale']['x'] - parent['position']['x']
            y = y * parent['scale']['y'] - parent['position']['y']
            w *= parent['scale']['x']
            h *= parent['scale']['y']
            return get_position_box(parent, x, y, w, h)
        return -x, -y, w - x, h - y

    # how to properly position:
    # - first: -(sizedelta * pivot * scale - localposition)
    # - subsq: -((sizedelta * pivot * scale - localposition) * parentscale - parentposition)
    # - also scale by total scale

    from math import inf

    x0 = inf
    y0 = inf
    x1 = -inf
    y1 = -inf
    for i in layers:
        layer = layers[i]
        if 'size' in layer:
            xi, yi, xj, yj = get_position_box(layer)
            layer['box'] = [xi, yi, xj, yj]
            x0 = min(x0, xi)
            y0 = min(y0, yi)
            x1 = max(x1, xj)
            y1 = max(y1, yj)
    print(x0, y0)
    for i in layers:
        layer = layers[i]
        if 'box' in layer:
            layer['box'][0] -= x0
            layer['box'][1] -= y0
            layer['box'][2] -= x0
            layer['box'][3] -= y0
            print(layer['box'])
    master = Image.new('RGBA', (int(x1 - x0), int(y1 - y0)))

    for i in layers:
        layer = layers[i]
        if 'mesh' in layer and 'texture' in layer:
            v, vt = get_vertices(layer['mesh'], layer['texture'])
            patches = get_patches(layer['texture'], vt)
            canvas, truesize = get_canvas(v, (int(layer['size']['x']), int(layer['size']['y'])))
            print(truesize, layer['size'])
            stitch_patches(canvas, patches, v, layer['mesh'])
            scaled_flipped_canvas = canvas.resize((
                int((layer['box'][2] - layer['box'][0]) * (truesize[0] / layer['size']['x'])),
                int((layer['box'][3] - layer['box'][1]) * (truesize[1] / layer['size']['y']))
            )).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            master.alpha_composite(scaled_flipped_canvas, (int(layer['box'][0]), int(layer['box'][1])))
        elif 'texture' in layer: # no mesh found
            # todo: check if this face-specific stuff breaks other no-mesh texture scenarios that aren't faces
            #       tashigan_2: bg is resized exactly the same
            #                   so it doesn't break non-faces, but faces still need special treatment for y position (thus isFace for face detection)
            #       jianwu_3: has a non-face that requires resizing with bounds like a face
            #                 so nvm about isFace detection (hopefully this doesn't screw up bgs)
            #       fubo_2: idfk; it's fixed with y + 6, x - 55
            if layer['bound']: # face
                scaled_flipped_texture = layer['texture'].image.resize((int(layer['bound']['x']), int(layer['bound']['y']))).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                layer['position']['y'] = math.ceil(layer['position']['y'])
                # rounding up y seems to fix face positions (works for unknown4, tashigan_2, weizhang_3)
            else:
                scaled_flipped_texture = layer['texture'].image.resize(master.size).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            master.alpha_composite(scaled_flipped_texture, (
                int(layer['position']['x'] - layer['bound']['x'] * layer['pivot']['x'] - x0),
                int(layer['position']['y'] - layer['bound']['y'] * layer['pivot']['y'] - y0)
            ))
    unflipped_master = master.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    # unflipped_master.show()

    def crop_and_downscale(im, crop, factor='maxsize'):
        if crop:
            bbox = im.getbbox()
            im = im.crop(bbox)
        if factor == 'pixelcount':
            pixels = im.width * im.height
            maxpixels = 2048 * 2048
            if pixels > maxpixels:
                return im.resize([round(d * math.sqrt(maxpixels / pixels)) for d in im.size])
        else:
            dmax = max(im.size)
            if dmax > 2048:
                return im.resize([round(d * 2048 / dmax) for d in im.size])
        return im

    os.makedirs('output2', exist_ok=True)
    if out_file:
        name = out_file # todo: sanitize
    else:
        name = painting_name
    if keep:
        os.makedirs('output2/original', exist_ok=True)
        unflipped_master.save('output2/original/{}.png'.format(name))
    unflipped_master = crop_and_downscale(unflipped_master, crop, factor)
    unflipped_master.save('output2/{}.png'.format(name))

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--painting_name', type=str, default='', help='name of painting assetbundle file(s) (separate by colons)')
    parser.add_argument('-f', '--face_name', type=str, help='paintingface name')
    parser.add_argument('-t', '--face_type', type=str, help='paintingface index')
    parser.add_argument('-d', '--asset_directory', type=Path, default=Path('AssetBundles'), help='directory containing all client assets')
    parser.add_argument('-o', '--out_file', type=str, default='', help='output filename(s) (separate by colons)')
    parser.add_argument('-c', '--crop', action='store_true', help='trim empty space from output')
    parser.add_argument('-k', '--keep_original', action='store_true', help='save full resolution sprite too')
    parser.add_argument('-s', '--scale_factor', type=str, help='downscale factor: maxsize (max(w,h) < 2048; default) or pixelcount (w*h < 2048^2)')
    args = parser.parse_args()

    if not args.painting_name:
        import tkinter as tk
        from tkinter import filedialog
        scapegoat= tk.Tk()
        scapegoat.withdraw()
        assetfilename = filedialog.askopenfilename(
            initialdir=Path(args.asset_directory, 'painting'),
            title='Select asset file (a /painting/ file not ending in _tex)'
        )
        args.asset_directory = Path('/', *assetfilename.split('/')[1:-2]) # C drive only
        args.painting_name = assetfilename.split('/')[-1]

    root = args.asset_directory

    if ':' in args.painting_name or ':' in args.out_file:
        for painting_name, out_file in zip(args.painting_name.split(':'), args.out_file.split(':')):
            wrapped(painting_name, out_file, args.crop, args.keep_original, args.face_name, args.face_type, args.scale_factor)
    else:
        wrapped(args.painting_name, args.out_file, args.crop, args.keep_original, args.face_name, args.face_type, args.scale_factor)
