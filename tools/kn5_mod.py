"""Rewrite a kn5: add textures, add materials, reassign mesh materials. No offset table in kn5, so the
texture and material blocks are rebuilt and the node tree is copied with material ids patched in place.

    from kn5_mod import Kn5Mod
    k = Kn5Mod('in.kn5'); k.add_texture('wood.dds', 'wood.dds')
    k.add_material('wood', 'ksPerPixel', {'ksAmbient':0.5,'ksDiffuse':0.6,'ksSpecular':0.3,'ksSpecularEXP':40,'ksEmissive':0,'ksAlphaRef':0}, {'txDiffuse':'wood.dds'})
    k.set_mesh_material('dashboard_lp_SUB0', 'wood'); k.save('out.kn5')
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kn5 import parse

def _s(x): b = x.encode('latin-1'); return struct.pack('<I', len(b)) + b

class Kn5Mod:
    def __init__(self, path):
        self.b, self.ver, self.T, self.M, self.X = parse(path)
        self.tex_start = self.T[0]['offset'] - 12 - len(self.T[0]['name'])
        self.tex_end = self.T[-1]['offset'] + self.T[-1]['size']
        # material block: starts right after textures (count int) and ends where the node tree starts
        p = self.tex_end
        n = struct.unpack_from('<I', self.b, p)[0]; p += 4
        self.mat_start = self.tex_end
        for _ in range(n):
            p = self._skip_material(p)
        self.mat_end = p
        self.new_tex = []; self.new_mat = []; self.remap = {}
    def _skip_material(self, p):
        b = self.b
        for _ in range(2):
            p += 4 + struct.unpack_from('<I', b, p)[0]
        p += 1 + 1 + 4
        np_ = struct.unpack_from('<I', b, p)[0]; p += 4
        for _ in range(np_):
            p += 4 + struct.unpack_from('<I', b, p)[0]; p += 4 + 8 + 12 + 16
        nt = struct.unpack_from('<I', b, p)[0]; p += 4
        for _ in range(nt):
            p += 4 + struct.unpack_from('<I', b, p)[0]; p += 4
            p += 4 + struct.unpack_from('<I', b, p)[0]
        return p
    def add_texture(self, name, path):
        self.new_tex.append((name, open(path, 'rb').read()))
    def add_material(self, name, shader, props, textures, blend=0, atest=0, depth=0):
        self.new_mat.append((name, shader, props, textures, blend, atest, depth))
    def set_mesh_material(self, mesh, material):
        self.remap[mesh] = material
    def save(self, path):
        b = self.b
        out = bytearray(b[:self.tex_start - 4])
        out += struct.pack('<I', len(self.T) + len(self.new_tex))
        out += b[self.tex_start:self.tex_end]
        for name, data in self.new_tex:
            out += struct.pack('<I', 1) + _s(name) + struct.pack('<I', len(data)) + data
        out += struct.pack('<I', len(self.M) + len(self.new_mat))
        out += b[self.mat_start + 4:self.mat_end]
        for name, shader, props, textures, blend, atest, depth in self.new_mat:
            out += _s(name) + _s(shader) + bytes([blend, atest]) + struct.pack('<i', depth)
            out += struct.pack('<I', len(props))
            for k, v in props.items():
                out += _s(k) + struct.pack('<f', float(v)) + b'\0' * 36
            out += struct.pack('<I', len(textures))
            for slot, (k, v) in enumerate(textures.items()):
                out += _s(k) + struct.pack('<I', slot) + _s(v)
        nodes = bytearray(b[self.mat_end:])
        names = [m['name'] for m in self.M] + [m[0] for m in self.new_mat]
        for x in self.X:
            if x['name'] in self.remap:
                mat_off = x['ioff'] + x['ni'] * 2 - self.mat_end       # material id follows the index buffer
                struct.pack_into('<i', nodes, mat_off, names.index(self.remap[x['name']]))
        out += nodes
        open(path, 'wb').write(out)
        b2, v2, T2, M2, X2 = parse(path)
        assert len(T2) == len(self.T) + len(self.new_tex) and len(M2) == len(self.M) + len(self.new_mat) and len(X2) == len(self.X)
        for x in X2:
            if x['name'] in self.remap:
                assert M2[x['mat']]['name'] == self.remap[x['name']], x['name']
        return path

# ---- mesh replacement -------------------------------------------------------------------------
import numpy as _np

def obj_to_mesh(obj_path, flip_winding=False):
    """Read an OBJ (v / vt / vn / f with v/vt/vn), return (verts Nx11: pos, normal, uv, tangent; indices)."""
    P, UV, N, tris = [], [], [], []
    for line in open(obj_path):
        p = line.split()
        if not p: continue
        if p[0] == 'v': P.append(tuple(map(float, p[1:4])))
        elif p[0] == 'vt': UV.append(tuple(map(float, p[1:3])))
        elif p[0] == 'vn': N.append(tuple(map(float, p[1:4])))
        elif p[0] == 'f':
            f = [tuple(int(k) - 1 if k else -1 for k in (c.split('/') + ['', ''])[:3]) for c in p[1:]]
            for i in range(1, len(f) - 1): tris.append((f[0], f[i], f[i + 1]))
    key = {}; verts = []; idx = []
    for tri in tris:
        tri = (tri[0], tri[2], tri[1]) if flip_winding else tri
        for (vi, ti, ni) in tri:
            k = (vi, ti, ni)
            if k not in key:
                key[k] = len(verts)
                pos = P[vi]; uv = UV[ti] if ti >= 0 else (0, 0); n = N[ni] if ni >= 0 else (0, 1, 0)
                verts.append([*pos, *n, uv[0], uv[1] - 1.0, 0, 0, 0])      # OBJ v is bottom-up; kn5 stores -v_directx = v_obj - 1
            idx.append(key[k])
    V = _np.array(verts, dtype=_np.float32); I = _np.array(idx, dtype=_np.uint16)
    # tangents from the uv gradient, per triangle, accumulated per vertex
    T = _np.zeros((len(V), 3))
    for a, b, c in I.reshape(-1, 3):
        p0, p1, p2 = V[a, :3], V[b, :3], V[c, :3]; u0, u1, u2 = V[a, 6:8], V[b, 6:8], V[c, 6:8]
        e1, e2 = p1 - p0, p2 - p0; d1, d2 = u1 - u0, u2 - u0
        det = d1[0] * d2[1] - d2[0] * d1[1]
        if abs(det) < 1e-12: continue
        tg = (e1 * d2[1] - e2 * d1[1]) / det
        T[a] += tg; T[b] += tg; T[c] += tg
    n = _np.linalg.norm(T, axis=1); n[n == 0] = 1; T = T / n[:, None]
    T[_np.isnan(T).any(axis=1)] = (1, 0, 0)
    V[:, 8:11] = T
    return V, I

def _mesh_node_bytes(name, V, I, mat_id, layer=0, lod_in=0.0, lod_out=0.0):
    import struct
    center = (V[:, :3].max(0) + V[:, :3].min(0)) / 2; radius = float(_np.linalg.norm(V[:, :3] - center, axis=1).max())
    out = struct.pack('<i', 2) + _s(name) + struct.pack('<I', 0) + bytes([1, 1, 1, 0])
    out += struct.pack('<I', len(V)) + V.astype('<f4').tobytes()
    out += struct.pack('<I', len(I)) + I.astype('<u2').tobytes()
    out += struct.pack('<iiff', mat_id, layer, lod_in, lod_out) + struct.pack('<4f', *center, radius) + bytes([1])
    return out

def replace_mesh(self, mesh_name, V, I, material=None):
    """Swap the geometry of an existing mesh node (keeps its place in the tree; material by name or unchanged)."""
    x = [m for m in self.X if m['name'] == mesh_name][0]
    names = [m['name'] for m in self.M] + [m[0] for m in self.new_mat]
    mat_id = names.index(material) if material else x['mat']
    self.mesh_swaps = getattr(self, 'mesh_swaps', {}); self.mesh_swaps[mesh_name] = (V, I, mat_id)
Kn5Mod.replace_mesh = replace_mesh

_old_save = Kn5Mod.save
def _save_with_swaps(self, path):
    swaps = getattr(self, 'mesh_swaps', {})
    if not swaps: return _old_save(self, path)
    import struct
    b = self.b; out = bytearray(b[:self.tex_start - 4])
    out += struct.pack('<I', len(self.T) + len(self.new_tex)) + b[self.tex_start:self.tex_end]
    for name, data in self.new_tex: out += struct.pack('<I', 1) + _s(name) + struct.pack('<I', len(data)) + data
    out += struct.pack('<I', len(self.M) + len(self.new_mat)) + b[self.mat_start + 4:self.mat_end]
    for name, shader, props, textures, blend, atest, depth in self.new_mat:
        out += _s(name) + _s(shader) + bytes([blend, atest]) + struct.pack('<i', depth) + struct.pack('<I', len(props))
        for k, v in props.items(): out += _s(k) + struct.pack('<f', float(v)) + b'\0' * 36
        out += struct.pack('<I', len(textures))
        for slot, (k, v) in enumerate(textures.items()): out += _s(k) + struct.pack('<I', slot) + _s(v)
    names = [m['name'] for m in self.M] + [m[0] for m in self.new_mat]
    pos = self.mat_end
    for x in sorted(self.X, key=lambda m: m['nstart']):
        if x['name'] in swaps:
            V, I, mat_id = swaps[x['name']]
            out += b[pos:x['nstart']] + _mesh_node_bytes(x['name'], V, I, mat_id); pos = x['nend']
        elif x['name'] in self.remap:
            seg = bytearray(b[pos:x['nend']]); struct.pack_into('<i', seg, x['ioff'] + x['ni'] * 2 - pos, names.index(self.remap[x['name']]))
            out += seg; pos = x['nend']
    out += b[pos:]
    open(path, 'wb').write(out)
    b2, v2, T2, M2, X2 = parse(path)
    assert len(X2) == len(self.X), 'mesh count changed'
    for x in X2:
        if x['name'] in swaps: assert x['nv'] == len(swaps[x['name']][0]), x['name']
    return path
Kn5Mod.save = _save_with_swaps
