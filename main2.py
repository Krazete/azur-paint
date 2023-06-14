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


master = Image.new(encompassing_rect)
for i in layers:
    layer = layers[i]
    if 'mesh' in layer and 'texture' in layer:
        v, vt = get_vertices(layer['mesh'], layer['texture'])
        patches = get_patches(layer['texture'], vt)
        canvas = get_canvas(v, (int(layer['size']['x']), int(layer['size']['y'])))
        stitch_patches(canvas, patches, v)
        scaled_canvas = canvas.resize((int(layer['delta']['x']), int(layer['delta']['y'])))
        do_other_transforming_things_to_scaled_canvas()
        maybe_also_flip_everything_first()
        master.alpha_composite(canvas) # paste loses color info
unflip_everything_if_needed()
master.show()        

def get_position(layer, x=None, y=None):
    if x is None or y is None:
        x = layer['delta']['x'] * layer['pivot']['x'] * layer['scale']['x'] - layer['position']['x']
        y = layer['delta']['y'] * layer['pivot']['y'] * layer['scale']['y'] - layer['position']['y']
    if 'parent' in layer:
        parent = layers[layer['parent']]
        x = x * parent['scale']['x'] - parent['position']['x']
        y = y * parent['scale']['y'] - parent['position']['y']
        return get_position(parent, x, y)
    return (-x, -y)

# how to properly position:
# - first: -(sizedelta * pivot * scale - localposition)
# - subsq: -((sizedelta * pivot * scale - localposition) * parentscale - parentposition)
# - also scale by total scale
