"""Seat backs with 'LOTUS 7' stitched on the headrests.
The mod's seats tile a 512 px suede texture about 4.6 times. We rescale the two seat-back meshes' UVs into 0..1,
then give the forward-facing headrest triangles their own planar mapping onto a reserved patch of a 2048 texture
that repeats the suede and carries the stitching (one patch per seat, so nothing overlaps)."""
import struct, numpy as np
from PIL import Image, ImageDraw, ImageFont
SCALE, UOFF, VOFF = 4.6, 1.8, 1.3
S = 2048
SEATS = {'sit L_SUB0': (100, 1650, 920, 2040), 'sit R_SUB0': (1100, 1650, 1920, 2040)}   # text patches in pixels

def _verts(b, x):
    V = np.array([struct.unpack_from('<11f', b, x['voff'] + i * 44) for i in range(x['nv'])], dtype=np.float32)
    I = np.frombuffer(b, dtype='<u2', count=x['ni'], offset=x['ioff']).copy()
    return V, I

def remap(b, x, patch):
    V, I = _verts(b, x)
    u = V[:, 6].copy(); v = -V[:, 7]
    V[:, 6] = (u + UOFF) / SCALE; V[:, 7] = -((v + VOFF) / SCALE)
    P = np.c_[V[:, :3], np.ones(len(V))] @ x['world']; Nw = V[:, 3:6] @ x['world'][:3, :3]
    front = (P[:, 1] > 0.80) & (Nw[:, 2] > 0.5)
    tri = I.reshape(-1, 3); ftri = front[tri].all(axis=1)
    fv = np.unique(tri[ftri])
    xmin, xmax = P[fv, 0].min(), P[fv, 0].max(); ymin, ymax = P[fv, 1].min(), P[fv, 1].max()
    x0, y0, x1, y1 = patch
    newidx = {}
    extra = []
    for vi in fv:
        nv = V[vi].copy()
        # seen from in front of the seat (looking rearward) the reader's right is the car's right (-x): u grows as x falls; up is up
        nv[6] = (x0 + (xmax - P[vi, 0]) / (xmax - xmin) * (x1 - x0)) / S
        nv[7] = -((y0 + (ymax - P[vi, 1]) / (ymax - ymin) * (y1 - y0)) / S)
        newidx[vi] = len(V) + len(extra); extra.append(nv)
    V = np.vstack([V, np.array(extra, dtype=np.float32)])
    tri = tri.copy()
    for k in np.where(ftri)[0]:
        tri[k] = [newidx[a] for a in tri[k]]
    return V, tri.reshape(-1).astype(np.uint16), (xmax - xmin, ymax - ymin)

def make_textures(suede_png, suede_nrm_png, out_dds, out_nrm_dds, check_png=None):
    tile = int(round(S / SCALE))
    base = Image.open(suede_png).convert('RGBA').resize((tile, tile)); nrm = Image.open(suede_nrm_png).convert('RGBA').resize((tile, tile))
    tex = Image.new('RGBA', (S, S)); ntex = Image.new('RGBA', (S, S))
    for i in range(0, S, tile):
        for j in range(0, S, tile):
            tex.paste(base, (i, j)); ntex.paste(nrm, (i, j))
    for (x0, y0, x1, y1) in SEATS.values():
        w, h = x1 - x0, y1 - y0
        font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf', int(h * 0.42))
        txt = Image.new('RGBA', (w, h), (0, 0, 0, 0)); td = ImageDraw.Draw(txt)
        td.text((w / 2, h / 2), 'LOTUS 7', font=font, fill=(236, 120, 20, 255), anchor='mm', stroke_width=5, stroke_fill=(175, 78, 8, 255))
        mask = txt.split()[3].point(lambda a: 255 if a > 100 else 0)
        hatch = Image.new('RGBA', (w, h), (0, 0, 0, 0)); hd = ImageDraw.Draw(hatch)
        for k in range(-h, w + h, 5):
            hd.line([(k, 0), (k + h, h)], fill=(255, 165, 70, 120), width=2)
        txt.paste(hatch, (0, 0), Image.composite(hatch.split()[3], Image.new('L', (w, h), 0), mask))
        tex.paste(txt, (x0, y0), txt)
    tex.save(out_dds, pixel_format='DXT5'); ntex.save(out_nrm_dds, pixel_format='DXT5')
    if check_png: tex.resize((1024, 1024)).save(check_png)

def apply(k, b, X, ov_dir):
    """add the seat material and swap both seat backs in a Kn5Mod (k) given parsed data (b, X)"""
    import os
    k.add_texture('gio_seat.dds', os.path.join(ov_dir, 'kn5_textures', 'gio_seat.dds'))
    k.add_texture('gio_seat_nrm.dds', os.path.join(ov_dir, 'kn5_textures', 'gio_seat_nrm.dds'))
    k.add_material('gio_seat', 'ksPerPixelAT_NM', dict(ksAmbient=0.4, ksDiffuse=0.4, ksSpecular=0.005, ksSpecularEXP=10, ksEmissive=0, ksAlphaRef=0), {'txDiffuse': 'gio_seat.dds', 'txNormal': 'gio_seat_nrm.dds'}, atest=1)
    for name, patch in SEATS.items():
        x = [m for m in X if m['name'] == name][0]
        V, I, size = remap(b, x, patch); k.replace_mesh(name, V, I, material='gio_seat')
