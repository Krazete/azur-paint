import os
import UnityPy
from PIL import Image

def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

mkdir('output')

aitex = UnityPy.load('input/painting/aijiang_tex')
# aitex = UnityPy.load('input/painting/tbniang_tex')

for asset in aitex.assets:
    obj = False
    png = False
    fn = False
    for value in asset.values():
        if value.type.name == 'Mesh':
            if obj:
                print('Multiple meshes found.')
            obj = value.read()
        if value.type.name == 'Texture2D':
            if png or fn:
                print('Multiple textures found.')
            png = value.read()
            fn = png.name
    with open('output/mesh.obj', 'w', newline='') as fp:
        fp.write(mesh.export())
    png.image.save('output/texture.png')
    print(fn)

    # get vertices

    w = png.image.width
    h = png.image.height

    v = []
    vt = []
    for line in obj.export().split('\n'):
        if line[:2] == 'v ':
            ints = [int(n) for n in line.split(' ')[1:]]
            assert ints[2] == 0
            v.append(ints[:2])
        if line[:3] == 'vt ':
            floats = [float(n) for n in line.split(' ')[1:]]
            vt.append([w * floats[0], h - h * floats[1]])

    # cut rectangles from textures

    assert len(v) == len(vt)

    p = []
    vtlen = int(len(vt) / 4)
    for n in range(vtlen):
        i = n * 4
        j = i + 4
        x0 = min(x for x, y in vt[i:j])
        x1 = max(x for x, y in vt[i:j])
        y0 = min(y for x, y in vt[i:j])
        y1 = max(y for x, y in vt[i:j])
        p.append(png.image.crop([x0, y0, x1, y1]))

    # make canvas

    cx0 = min(x for x, y in v)
    cx1 = max(x for x, y in v)
    cy0 = min(y for x, y in v)
    cy1 = max(y for x, y in v)
    canvas = Image.new('RGBA', (cx1 - cx0, cy1 - cy0))

    # paste rectangles onto canvas

    mkdir('output/pieces')

    n = 0
    for piece in p:
        i = n * 4
        j = i + 4
        x0 = min(x for x, y in v[i:j])
        x1 = max(x for x, y in v[i:j])
        y0 = min(y for x, y in v[i:j])
        y1 = max(y for x, y in v[i:j])
        piece.save('output/pieces/{:0d}.png'.format(n))
        canvas.paste(piece, (-x1, cy1 - y1))
        n += 1

# canvas.show()
canvas.save('output/result.png')
# help(canvas.paste)
# piece.size
# dir(obj)
# obj.get_raw_data().tolist()
