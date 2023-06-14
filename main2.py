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

# env = UnityPy.load('input/painting/shaenhuosite_alter')
# env = UnityPy.load('input/painting/makeboluo')
env = UnityPy.load('input/painting/tower')
# env = UnityPy.load('input/painting/adaerbote_2')
# env = UnityPy.load('input/painting/ankeleiqi')
layers = {}
get_layers(env.assets[0], layers) # keys ordered bottom to top

for i in layers:
    layer = layers[i]
    if 'mesh' in layer:
        print(layer['texture'])

layersinfo = {}

asset = env.assets[0]
for layer in layers:
    name = layer['m_Name']
    cdl = layer['m_Component']
    for cd in cdl:
        component_id = cd['component']['m_PathID']
        component = asset[component_id].read_typetree()
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
        # or, maybe (1155, 3575)?
        body.alpha_composite(linfo[-1], p) # paste loses color info
body.show()

# how to properly position:
# - first: -(sizedelta * pivot * scale - localposition)
# - subsq: -((sizedelta * pivot * scale - localposition) * parentscale - parentposition)
# - also scale by total scale
