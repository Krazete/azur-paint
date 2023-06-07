import os
import UnityPy
from PIL import Image

def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

mkdir('output')

aitex = UnityPy.load('input/painting/aijiang_tex')

# aiface = UnityPy.load('input/paintingface/aijiang')
# for value in aiface.assets[0].values():
#     if value.type.name == 'Mesh':
#         obj = value.read()
#         print(obj)
#     if value.type.name == 'Texture2D':
#         png = value.read()
#         fn = png.name
#         print(fn, png.image)

# aiinfo = UnityPy.load('input/painting/aijiang')
# for value in aiinfo.assets[0].values():
#     if value.type.name == 'GameObject':
#         print(value.read().name)
#         for component in value.read().m_Component[0].values():
#             print(component.read().m_LocalPosition)
#         print(value.read().m_Component[0].values())
#         print()
#         break

def get_mesh_and_texture(asset, save=False):
    mesh = None
    texture = None
    for value in asset.values():
        if value.type.name == 'Mesh':
            if mesh:
                print('Multiple meshes found in asset:', asset.name)
            mesh = value.read()
        if value.type.name == 'Texture2D':
            if texture:
                print('Multiple textures found in asset:', asset.name)
            texture = value.read()
    if save:
        mkdir('output/intermediate')
        with open('output/intermediate/mesh.obj', 'w', newline='') as file:
            file.write(mesh.export())
        texture.image.save('output/intermediate/texture.png')
    return mesh, texture

def get_vertices(mesh, texture):
    w = texture.image.width
    h = texture.image.height
    v = [] # mesh vertices
    vt = [] # texture vertices
    # unused: g (group names), f (faces)
    for line in mesh.export().splitlines():
        if line.startswith('v '):
            x, y, z = line.split(' ')[1:]
            v.append((int(x), int(y), int(z)))
        if line.startswith('vt '):
            x, y = line.split(' ')[1:]
            vt.append((w * float(x), h - h * float(y)))
    assert len(v) == len(vt), 'Unequal number of mesh vertices to texture vertices.'
    xmax = max(x for x, y, z in v)
    ymax = max(y for x, y, z in v)
    v = [(xmax - x, ymax - y, z) for x, y, z in v]
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
            mkdir('output/intermediate/patches')
            patch.save('output/intermediate/patches/{:04d}.png'.format(i))
        patches.append(patch)
    return patches

def get_canvas(v):
    xmin = min(x for x, y, z in v)
    xmax = max(x for x, y, z in v)
    ymin = min(y for x, y, z in v)
    ymax = max(y for x, y, z in v)
    # true dimensions are found in input/paintings/aijiang
    # within assets[0].values() of type name MonoBehaviour
    # where value.read_typetree() has the key mRawSpriteSize
    return Image.new('RGBA', (xmax - xmin, ymax - ymin))

def stitch_patches(canvas, patches, v):
    for i, patch in enumerate(patches):
        a = i * 4
        b = a + 4
        xmin = min(x for x, y, z in v[a:b])
        ymin = min(y for x, y, z in v[a:b])
        canvas.paste(patch, (xmin, ymin))

def rebuild_sprite(env, show=False, save=False, save_intermediate=False):
    for asset in env.assets:
        mesh, texture = get_mesh_and_texture(asset, save_intermediate)
        v, vt = get_vertices(mesh, texture)
        patches = get_patches(texture, vt, save_intermediate)
        canvas = get_canvas(v)
        stitch_patches(canvas, patches, v)
        if show:
            canvas.show()
        if save:
            canvas.save('output/result.png')

if __name__ == '__main__':
    rebuild_sprite(aitex, False, True, True)
