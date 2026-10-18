"""Seat backs with 'LOTUS' over '7' stitched in orange, like the real seats.
The mod's seats tile a 512 px suede texture about 4.6 times. We rescale the two seat-back meshes' UVs into 0..1,
then give the forward-facing seat-back triangles their own planar mapping onto a reserved patch of a 2048 texture
that repeats the fabric and carries the stitching (one patch per seat). The game reads v from the bottom: image_y = 1 + v."""
import struct, numpy as np
from PIL import Image, ImageDraw, ImageFont
SCALE, UOFF, VOFF = 4.6, 1.8, 1.4        # chosen so every seat vertex lands inside 0..0.78 of the texture, nothing wraps into the patches
S = 2048
SEATS = {'sit L_SUB0': (60, 1630, 960, 2040), 'sit R_SUB0': (1080, 1630, 1980, 2040)}   # text patches in pixels (x0, y0, x1, y1)

def _verts(b, x):
    V = np.array([struct.unpack_from('<11f', b, x['voff'] + i * 44) for i in range(x['nv'])], dtype=np.float32)
    I = np.frombuffer(b, dtype='<u2', count=x['ni'], offset=x['ioff']).copy()
    return V, I

def remap(b, x, patch):
    V, I = _verts(b, x)
    u = V[:, 6].copy(); vimg = 1.0 + V[:, 7]
    V[:, 6] = (u + UOFF) / SCALE; V[:, 7] = (vimg + VOFF) / SCALE - 1.0
    P = np.c_[V[:, :3], np.ones(len(V))] @ x['world']; Nw = V[:, 3:6] @ x['world'][:3, :3]
    front = (P[:, 1] > 0.34) & (P[:, 1] < 0.62) & (Nw[:, 2] > 0.30)          # upper seat back, the forward-facing part below the shoulders
    tri = I.reshape(-1, 3); ftri = front[tri].all(axis=1)
    fv = np.unique(tri[ftri])
    xmin, xmax = P[fv, 0].min(), P[fv, 0].max(); ymin, ymax = P[fv, 1].min(), P[fv, 1].max()
    x0, y0, x1, y1 = patch
    newidx, extra = {}, []
    for vi in fv:
        nv = V[vi].copy()
        # seen from in front of the seat looking rearward, the reader's right is the car's right (-x)
        nv[6] = (x0 + (xmax - P[vi, 0]) / (xmax - xmin) * (x1 - x0)) / S
        nv[7] = (y0 + (ymax - P[vi, 1]) / (ymax - ymin) * (y1 - y0)) / S - 1.0
        newidx[vi] = len(V) + len(extra); extra.append(nv)
    V = np.vstack([V, np.array(extra, dtype=np.float32)])
    tri = tri.copy()
    for k in np.where(ftri)[0]:
        tri[k] = [newidx[a] for a in tri[k]]
    return V, tri.reshape(-1).astype(np.uint16), (xmax - xmin, ymax - ymin)

def _stitched(d, canvas, text, font, cx, cy):
    """orange stitched lettering: dark outline, orange fill, light thread hatch"""
    tmp = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tmp)
    td.text((cx, cy), text, font=font, fill=(236, 120, 20, 255), anchor='mm', stroke_width=6, stroke_fill=(150, 60, 6, 255))
    mask = tmp.split()[3].point(lambda a: 255 if a > 90 else 0)
    hatch = Image.new('RGBA', canvas.size, (0, 0, 0, 0)); hd = ImageDraw.Draw(hatch); W, H = canvas.size
    for k in range(-H, W + H, 7): hd.line([(k, 0), (k + H, H)], fill=(255, 175, 90, 130), width=2)
    tmp.paste(hatch, (0, 0), Image.composite(hatch.split()[3], Image.new('L', canvas.size, 0), mask))
    canvas.paste(tmp, (0, 0), tmp)

def make_textures(suede_png, suede_nrm_png, out_dds, out_nrm_dds, check_png=None):
    tile = int(round(S / SCALE))
    base = Image.open(suede_png).convert('RGBA').resize((tile, tile)); nrm = Image.open(suede_nrm_png).convert('RGBA').resize((tile, tile))
    tex = Image.new('RGBA', (S, S)); ntex = Image.new('RGBA', (S, S))
    for i in range(0, S, tile):
        for j in range(0, S, tile):
            tex.paste(base, (i, j)); ntex.paste(nrm, (i, j))
    for (x0, y0, x1, y1) in SEATS.values():
        w, h = x1 - x0, y1 - y0
        canvas = tex.crop((x0, y0, x1, y1)); d = ImageDraw.Draw(canvas)
        big = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', int(h * 0.40))
        small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', int(h * 0.26))
        _stitched(d, canvas, 'LOTUS', big, w / 2, h * 0.28)
        _stitched(d, canvas, '7', small, w / 2, h * 0.64)
        tex.paste(canvas, (x0, y0))
    tex.save(out_dds, pixel_format='DXT5'); ntex.save(out_nrm_dds, pixel_format='DXT5')
    if check_png: tex.resize((1024, 1024)).save(check_png)

def apply(k, b, X, ov_dir):
    import os
    k.add_texture('gio_seat.dds', os.path.join(ov_dir, 'kn5_textures', 'gio_seat.dds'))
    k.add_texture('gio_seat_nrm.dds', os.path.join(ov_dir, 'kn5_textures', 'gio_seat_nrm.dds'))
    # black leather rather than suede: a little more sheen than the mod's fabric
    k.add_material('gio_seat', 'ksPerPixelAT_NM', dict(ksAmbient=0.4, ksDiffuse=0.45, ksSpecular=0.25, ksSpecularEXP=30, ksEmissive=0, ksAlphaRef=0), {'txDiffuse': 'gio_seat.dds', 'txNormal': 'gio_seat_nrm.dds'}, atest=1)
    for name, patch in SEATS.items():
        x = [m for m in X if m['name'] == name][0]
        V, I, size = remap(b, x, patch); k.replace_mesh(name, V, I, material='gio_seat')
