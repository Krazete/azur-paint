from main import *

# name = 'shaenhuosite_alter'
# info, kit, canvas = rebuild_sprite(name)
# for asset in info.assets:
#     for value in asset.values():
#         tree = value.read_typetree()
#         print(value.read())
#         for key in tree:
#             if 'm' in key.lower():
#                 print(tree)
#                 break
#             try:
#                 if 'm' in tree[key].lower():
#                     print(tree)
#                     break
#             except:
#                 pass
#         print()

def get_layers(env):
    asset = env.assets[0]
    for value in asset.values():
        if value.type.name == 'AssetBundle':
            bundle = value.read_typetree()

    layers = []
    first_id = bundle['m_Container'][0][1]['asset']['m_PathID']
    first = asset[first_id].read_typetree()
    layers.append(first)

    child_id = first['m_Component'][0]['component']['m_PathID']
    child = asset[child_id].read_typetree()
    grand_id = child['m_Children'][0]['m_PathID']
    grand = asset[grand_id].read_typetree()
    for ptr in grand['m_Children']:
        rect_id = ptr['m_PathID']
        rect = asset[rect_id].read_typetree()
        layer_id = rect['m_GameObject']['m_PathID']
        layer = asset[layer_id].read_typetree()
        layers.append(layer)
    return layers



# env = UnityPy.load('input/painting/shaenhuosite_alter')
# env = UnityPy.load('input/painting/makeboluo')
env = UnityPy.load('input/painting/tower')
layers = get_layers(env)

layersinfo = {}
rawlayersinfo = []

asset = env.assets[0]
for layer in layers:
    rawlinfo = []
    name = layer['m_Name']
    cdl = layer['m_Component']
    rawlinfo.append(name)
    for cd in cdl:
        component_id = cd['component']['m_PathID']
        component = asset[component_id].read_typetree()
        rawlinfo.append(component)
        # print(component)
        if 'mMesh' in component:
            mesh_id = component['mMesh']['m_PathID']
            sprite_id = component['m_Sprite']['m_PathID']
            size = component['mRawSpriteSize']
        if 'm_SizeDelta' in component:
            delta = component['m_SizeDelta']
            pivot = component['m_Pivot']
            anchpos = component['m_AnchoredPosition']
    layersinfo[name] = [mesh_id, sprite_id, size, delta, pivot, anchpos]
    rawlayersinfo.append(rawlinfo)
    print(name, layersinfo[name])
    print('---')

for name in layersinfo:
    linfo = layersinfo[name]
    kit = UnityPy.load('input/painting/{}_tex'.format(name))
    kass = kit.assets[0]
    mesh = kass[linfo[0]].read()
    sprite = kass[linfo[1]].read_typetree()
    texture_id = sprite['m_RD']['texture']['m_PathID']
    texture = kass[texture_id].read()
    # mesh, texture = get_mesh_and_texture(kass)
    v, vt = get_vertices(mesh, texture)
    patches = get_patches(texture, vt)
    canvas = get_canvas(v, (int(linfo[2]['x']), int(linfo[2]['y'])))
    stitch_patches(canvas, patches, v)
    layersinfo[name].append(canvas)
for name in layersinfo:
    linfo = layersinfo[name]
    layersinfo[name].append(linfo[-1].resize((int(linfo[3]['x']), int(linfo[3]['y']))))

for i, name in enumerate(layersinfo):
    linfo = layersinfo[name]
    # linfo[-1].save('{}.png'.format(i))
    if i == 0:
        body = linfo[-1].copy()
        size0 = linfo[3]
    else:
        pivot = linfo[4]
        anchpos = linfo[5]
        p = (
            int((size0['x'] - linfo[3]['x'] + anchpos['x']) * pivot['x']),
            int((size0['y'] - linfo[3]['y'] + anchpos['y']) * pivot['y'])
        )
        # should be (1155, 3135) for tower_rw
        body.paste(linfo[-1], p, linfo[-1]) # doesn't do transparency properly
body.show()



# todo:
# - find where (x, y) to paste layers
