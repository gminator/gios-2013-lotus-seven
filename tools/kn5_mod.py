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
