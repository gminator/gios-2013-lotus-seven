"""Export named meshes from a kn5 to OBJ in car space: python3 kn5_to_obj.py car.kn5 out.obj mesh1,mesh2,..."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kn5 import parse
import numpy as np
b, ver, T, M, X = parse(sys.argv[1]); names = sys.argv[3].split(',')
out = open(sys.argv[2], 'w'); base = 1
for x in X:
    if x['name'] not in names: continue
    V = np.array([struct.unpack_from('<11f', b, x['voff'] + i * 44) for i in range(x['nv'])])
    P = np.c_[V[:, :3], np.ones(len(V))] @ x['world']
    idx = struct.unpack_from(f"<{x['ni']}H", b, x['ioff'])
    out.write(f"o {x['name'].replace(' ', '_')}\n")
    for p, v in zip(P, V):
        out.write(f"v {p[0]:.5f} {p[1]:.5f} {p[2]:.5f}\nvt {v[6]:.5f} {-v[7]:.5f}\n")
    for t in range(0, x['ni'], 3):
        a, bb, c = (idx[t + j] + base for j in range(3))
        out.write(f"f {a}/{a} {bb}/{bb} {c}/{c}\n")
    base += x['nv']
    print('exported', x['name'], x['nv'], 'verts')
