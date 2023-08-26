from main import *

def get_layers(asset, layers={}, id=None, parent=None):
    if id is None:
        for value in asset.values():
            if value.type.name == 'AssetBundle':
                bundle = value.read_typetree()
        id = bundle['m_Container'][0][1]['asset']['m_PathID']
    print(id)
    gameobject = asset[id].read_typetree()

    children = None
    mesh_id = None
    entry = {}
    for ptr in gameobject['m_Component']:
        component_id = ptr['component']['m_PathID']
        component = asset[component_id]
        tree = component.read_typetree()
        if component.type.name == 'RectTransform':
            entry['position'] = tree['m_LocalPosition']
            entry['scale'] = tree['m_LocalScale']
            entry['delta'] = tree['m_SizeDelta']
            entry['pivot'] = tree['m_Pivot']
            children = tree['m_Children']
        if 'mMesh' in tree:
            mesh_id = tree['mMesh']['m_PathID']
            sprite_id = tree['m_Sprite']['m_PathID']
            entry['size'] = tree['mRawSpriteSize']
    if mesh_id is not None:
        tex = UnityPy.load('input/painting/{}_tex'.format(gameobject['m_Name']))
        texas = tex.assets[0]
        entry['mesh'] = texas[mesh_id].read()
        sprite = texas[sprite_id].read_typetree()
        texture_id = sprite['m_RD']['texture']['m_PathID']
        entry['texture'] = texas[texture_id].read()
    if parent is not None:
        entry['parent'] = parent

    layers[id] = entry

    if children is not None:
        for rt_ptr in children:
            rt_id = rt_ptr['m_PathID']
            rt = asset[rt_id].read_typetree()
            child_id = rt['m_GameObject']['m_PathID']
            get_layers(asset, layers, child_id, id)

# oddity: jiahe_3-5 output jiahe_6 for some reason

# name = 'shaenhuosite_alter'
# name = 'makeboluo'
# name = 'tower'
# name = 'adaerbote_2'
name = 'ankeleiqi'
# name = 'buleisite_2'
env = UnityPy.load('input/painting/{}'.format(name))
layers = {}
get_layers(env.assets[0], layers) # keys ordered bottom to top

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
master = Image.new('RGBA', (int(x1 - x0 + 1), int(y1 - y0 + 1)))

for i in layers:
    layer = layers[i]
    if 'mesh' in layer and 'texture' in layer:
        v, vt = get_vertices(layer['mesh'], layer['texture'], True)
        patches = get_patches(layer['texture'], vt, True)
        canvas = get_canvas(v, (int(layer['size']['x']), int(layer['size']['y'])))
        stitch_patches(canvas, patches, v, layer['mesh'])
        scaled_flipped_canvas = canvas.resize((
            int(layer['box'][2] - layer['box'][0]),
            int(layer['box'][3] - layer['box'][1])
        )).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        master.alpha_composite(scaled_flipped_canvas, (int(layer['box'][0]), int(layer['box'][1])))
unflipped_master = master.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
# unflipped_master.show()

def downscale(im):
    dmax = max(im.size)
    if dmax > 2048:
        return im.resize([round(d * 2048 / dmax) for d in im.size])
    return im

mkdir('output2')
downscale(unflipped_master).save('output2/{}.png'.format(name))
