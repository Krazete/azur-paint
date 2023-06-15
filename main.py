import os
import UnityPy
from PIL import Image

def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

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
    if not size:
        print('  No reported size given.')
        return Image.new('RGBA', (dx, dy))
    if size[0] != dx:
        print('  Reported width ({}) and mesh width ({}) do not match.'.format(size[0], dx))
    if size[1] != dy:
        print('  Reported height ({}) and mesh height ({}) do not match.'.format(size[1], dy))
    return Image.new('RGBA', size)

def stitch_patches(canvas, patches, v, mesh):
    for i, patch in enumerate(patches):
        a = i * 4
        b = a + 4
        xmin = min(x for x, y in v[a:b])
        ymin = min(y for x, y in v[a:b])
        canvas.paste(patch, (
            int(xmin + mesh.read_typetree()['m_LocalAABB']['m_Center']['x'] - mesh.read_typetree()['m_LocalAABB']['m_Extent']['x']),
            int(ymin + canvas.height - mesh.read_typetree()['m_LocalAABB']['m_Center']['y'] - mesh.read_typetree()['m_LocalAABB']['m_Extent']['y'])
        ))

def rebuild_sprite(name, show=False, save=True, save_intermediate=False):
    print(name)
    mkdir('output')
    info = UnityPy.load('input/painting/{}'.format(name))
    size = get_size(info)
    kit = UnityPy.load('input/painting/{}_tex'.format(name))
    for asset in kit.assets:
        mesh, texture = get_mesh_and_texture(asset, save_intermediate)
        if mesh and texture:
            v, vt = get_vertices(mesh, texture)
            patches = get_patches(texture, vt, save_intermediate)
            canvas = get_canvas(v, size)
            stitch_patches(canvas, patches, v, mesh)
        elif texture:
            canvas = texture.image
        else:
            canvas = None
            print('  Cannot rebuild sprite for {}.'.format(name))
            break
        if show:
            canvas.show()
        if save:
            canvas.save('output/{}.png'.format(name))
    return info, kit, canvas

def get_faces(name, save=True):
    kit = UnityPy.load('input/paintingface/{}'.format(name))
    faces = []
    for asset in kit.assets:
        for value in asset.values():
            if value.type.name == 'Texture2D':
                faces.append(value.read())
    if save:
        mkdir('output/faces')
        for face in faces:
            face.image.save('output/faces/{}-{}.png'.format(name, face.name))
    return faces

def get_face_anchor(info):
    anchors = []
    for asset in info.assets:
        for value in asset.values():
            if value.type.name == 'GameObject':
                gameobject = value.read()
                if gameobject.name == 'face':
                    tree = gameobject.read_typetree()
                    for componentptr in tree['m_Component']:
                        pid = componentptr['component']['m_PathID']
                        component = asset[pid]
                        if component.type.name == 'RectTransform':
                            recttransform = component.read_typetree()
                            anchors.append(recttransform['m_AnchoredPosition'])
    return check_unique(anchors, 'face anchors')

def paste_face(name, canvas, face, anchor, show=False, save=True):
    # this function is slightly inaccurate
    # either the anchor position or the canvas creation is off
    # also this fails for many cases e.g. tower
    copy = canvas.copy()
    copy.paste(face.image, (
        int((canvas.width - face.image.width) / 2 + anchor['x']),
        int((canvas.height - face.image.height) / 2 - anchor['y'])
    ))
    if show:
        copy.show()
    if save:
        mkdir('output/expressions')
        copy.save('output/expressions/{}-{}.png'.format(name, face.name))

if __name__ == '__main__':
    info, kit, canvas = rebuild_sprite('aijiang', save_intermediate=True)
    faces = get_faces('tbniang')

    for root, dirs, files in os.walk("input/painting"):
        for file in files:
            if file.startswith('vtuber') and file.endswith('_tex'):
                info, kit, canvas = rebuild_sprite(file[:-4])

    name = 'unknown3' # purifier
    info, kit, canvas = rebuild_sprite(name, save=False)
    faces = get_faces(name, save=False)
    anchor = get_face_anchor(info)
    for face in faces:
        paste_face(name, canvas, face, anchor)
