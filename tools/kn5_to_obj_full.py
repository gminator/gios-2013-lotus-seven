"""Export a whole kn5 car to OBJ + MTL with its textures as PNG, for viewing or GLB export.
    python3 kn5_to_obj_full.py car.kn5 out_dir [skin_dir]
The skin's body_metal_detail / alloy textures stand in for the paint and rims when a skin dir is given."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kn5 import parse
import numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]; skin = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(os.path.join(out, 'tex'), exist_ok=True)
b, ver, T, M, X = parse(src)
tex_by_name = {t['name']: t for t in T}
def tex_png(name):
    p = os.path.join(out, 'tex', os.path.splitext(name)[0] + '.png')
    if not os.path.exists(p):
        t = tex_by_name.get(name)
        if not t: return None
        tmp = os.path.join(out, 'tex', '_tmp_' + name); open(tmp, 'wb').write(b[t['offset']:t['offset'] + t['size']])
        try:
            im = Image.open(tmp).convert('RGBA')
            if im.size[0] > 1024: im = im.resize((1024, int(1024 * im.size[1] / im.size[0])))
            im.save(p)
        except Exception as e:
            print('skip texture', name, e); os.remove(tmp); return None
        os.remove(tmp)
    return os.path.relpath(p, out)
overrides = {}
if skin:
    for k, f in (('carpaint baked', 'body_metal_detail.dds'), ('alloy', 'alloy.dds'), ('alloy_blur', 'alloy_blur.dds'), ('seven_color', 'color7.dds'), ('plates', 'plates.dds')):
        fp = os.path.join(skin, f)
        if os.path.exists(fp):
            im = Image.open(fp).convert('RGBA'); im.thumbnail((1024, 1024)); p = os.path.join(out, 'tex', 'skin_' + os.path.splitext(f)[0] + '.png'); im.save(p); overrides[k] = os.path.relpath(p, out)
mtl = open(os.path.join(out, 'car.mtl'), 'w'); done = set()
obj = open(os.path.join(out, 'car.obj'), 'w'); obj.write('mtllib car.mtl\n'); base = 1
hidden = {'collider'}
for x in X:
    if x.get('skinned') or x['nv'] < 3 or x['name'] in hidden: continue
    m = M[x['mat']]; mname = m['name'].replace(' ', '_')
    if m['name'] not in done:
        done.add(m['name'])
        mtl.write(f'newmtl {mname}\nKd 0.8 0.8 0.8\nd 1.0\n')
        d = overrides.get(m['name']) or (tex_png(m['tex']['txDiffuse']) if 'txDiffuse' in m['tex'] else None)
        if d: mtl.write(f'map_Kd {d}\n')
        mtl.write('\n')
    V = np.array([struct.unpack_from('<11f', b, x['voff'] + i * 44) for i in range(x['nv'])])
    P = np.c_[V[:, :3], np.ones(len(V))] @ x['world']; N = V[:, 3:6] @ x['world'][:3, :3]
    idx = struct.unpack_from(f"<{x['ni']}H", b, x['ioff'])
    obj.write(f"o {x['name'].replace(' ', '_')}\nusemtl {mname}\n")
    for p, n, v in zip(P, N, V):
        obj.write(f"v {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}\nvt {v[6]:.5f} {-v[7]:.5f}\nvn {n[0]:.4f} {n[1]:.4f} {n[2]:.4f}\n")   # OBJ v counts from the bottom; the game reads image_y = 1 + v
    for t in range(0, x['ni'], 3):
        a, bb, c = (idx[t + j] + base for j in range(3))
        obj.write(f"f {a}/{a}/{a} {bb}/{bb}/{bb} {c}/{c}/{c}\n")
    base += x['nv']
print('wrote', os.path.join(out, 'car.obj'), 'materials', len(done))
