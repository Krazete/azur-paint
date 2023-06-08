import os
import UnityPy
from PIL import Image

def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

# aiface = UnityPy.load('input/paintingface/aijiang')
# for value in aiface.assets[0].values():
#     if value.type.name == 'Mesh':
#         obj = value.read()
#         print(obj)
#     if value.type.name == 'Texture2D':
#         png = value.read()
#         fn = png.name
#         print(fn, png.image)

def check_unique(array, label):
    if len(array) < 1:
        print('  No {} found.'.format(label))
        return None
    if len(array) > 1:
        print('  Multiple {} found: {}'.format(label, array))
    return array[0]

def get_size(env):
    sizes = []
    for asset in env.assets:
        for value in asset.values():
            if value.type.name == 'MonoBehaviour':
                tree = value.read_typetree()
                if 'mRawSpriteSize' in tree:
                    sizes.append((
                        int(tree['mRawSpriteSize']['x']),
                        int(tree['mRawSpriteSize']['y'])
                    ))
    return check_unique(sizes, 'reported sizes')

def get_mesh_and_texture(asset, save=False):
    meshes = []
    textures = []
    for value in asset.values():
        if value.type.name == 'Mesh':
            meshes.append(value.read())
        if value.type.name == 'Texture2D':
            textures.append(value.read())
    mesh = check_unique(meshes, 'meshes')
    texture = check_unique(textures, 'textures')
    if save:
        mkdir('output/intermediate')
        if mesh:
            with open('output/intermediate/{}.obj'.format(mesh.name), 'w', newline='') as file:
                file.write(mesh.export())
        if texture:
            texture.image.save('output/intermediate/{}.png'.format(texture.name))
    return mesh, texture

def get_vertices(mesh, texture):
    v_raw = [] # mesh vertices
    vt_raw = [] # texture vertices
    # unused: g (group names), f (faces)
    for line in mesh.export().splitlines():
        if line.startswith('v '):
            split = line.split(' ')[1:]
            v_raw.append([int(n) for n in split])
        if line.startswith('vt '):
            split = line.split(' ')[1:]
            vt_raw.append([float(n) for n in split])
    assert len(v_raw) == len(vt_raw), 'Unequal number of mesh vertices to texture vertices.'
    xmax = max(x for x, y, z in v_raw)
    ymax = max(y for x, y, z in v_raw)
    v = [(xmax - x, ymax - y) for x, y, z in v_raw]
    w = texture.image.width
    h = texture.image.height
    vt = [(w * x, h - h * y) for x, y in vt_raw]
    return v, vt

def get_patches(texture, vt, save=False):
    patches = []
    n = int(len(vt) / 4)
    for i in range(n):
        a = i * 4
        b = a + 4
        xmin = min(x for x, y in vt[a:b])
        xmax = max(x for x, y in vt[a:b])
        ymin = min(y for x, y in vt[a:b])
        ymax = max(y for x, y in vt[a:b])
        patch = texture.image.crop((xmin, ymin, xmax, ymax))
        if save:
            mkdir('output/intermediate')
            mkdir('output/intermediate/{}'.format(texture.name))
            patch.save('output/intermediate/{}/{:03d}.png'.format(texture.name, i))
        patches.append(patch)
    return patches

def get_canvas(v, size=None):
    xmin = min(x for x, y in v)
    xmax = max(x for x, y in v)
    ymin = min(y for x, y in v)
    ymax = max(y for x, y in v)
    dx = 1 + xmax - xmin
    dy = 1 + ymax - ymin
    if size and size[0] != dx:
        print('  Reported width ({}) and mesh width ({}) do not match.'.format(size[0], dx))
    if size and size[1] != dy:
        print('  Reported height ({}) and mesh height ({}) do not match.'.format(size[1], dy))
    return Image.new('RGBA', (dx, dy))

def stitch_patches(canvas, patches, v):
    for i, patch in enumerate(patches):
        a = i * 4
        b = a + 4
        xmin = min(x for x, y in v[a:b])
        ymin = min(y for x, y in v[a:b])
        canvas.paste(patch, (xmin, ymin))

def rebuild_sprite(name, show=False, save=True, save_intermediate=False):
    print(name)
    mkdir('output')
    info = UnityPy.load('input/painting/{}'.format(name))
    size = get_size(info)
    kit = UnityPy.load('input/painting/{}_tex'.format(name))
    for asset in kit.assets:
        mesh, texture = get_mesh_and_texture(asset, save_intermediate)
        if mesh:
            v, vt = get_vertices(mesh, texture)
            patches = get_patches(texture, vt, save_intermediate)
            canvas = get_canvas(v, size)
            stitch_patches(canvas, patches, v)
        else:
            canvas = texture.image
        if show:
            canvas.show()
        if save:
            canvas.save('output/{}.png'.format(name))
    return info, kit

if __name__ == '__main__':
    info, kit = rebuild_sprite('aijiang', save_intermediate=True)

    for root, dirs, files in os.walk("input/painting"):
        for file in files:
            if file.startswith('vtuber') and file.endswith('_tex'):
                info, kit = rebuild_sprite(file[:-4])
