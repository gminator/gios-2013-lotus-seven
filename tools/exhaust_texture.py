"""The exhaust texture: 1024 x 1024, five horizontal rows that exhaust_geom.py maps onto its tubes.
    python3 tools/exhaust_texture.py overlay/kn5_textures/gio_exhaust.dds [check.png]
Row 0 steel silencer (light, seen through the mesh), 1 heat-wrapped elbow, 2 the black expanded-metal guard with the light
silencer showing through its holes, 3 black bands and end rings, 4 the bare stainless tailpipe, dull with a faint heat tint."""
import sys, numpy as np
from PIL import Image, ImageDraw
W = 1024; R = W // 5
rng = np.random.default_rng(7)
def noise(h, base, amp): return np.clip(base + rng.normal(0, amp, (h, W, 1)), 0, 255)
rows = []
rows.append(noise(R, np.array([196, 198, 202]), 6))                                   # 0 steel, brushed
wrap = noise(R, np.array([72, 73, 74]), 10)
yy, xx = np.mgrid[0:R, 0:W]; weave = ((xx // 6 + yy // 6) % 2) * 14 - 7
rows.append(np.clip(wrap + weave[:, :, None], 0, 255))                               # 1 wrap, woven
mesh = Image.new('RGB', (W, R), (188, 190, 194)); d = ImageDraw.Draw(mesh)             # 2 mesh: light silencer behind black strands
pw, ph, t = 14, 8, 4           # about 28 x 16 mm diamonds on the guard          # strands cover about half the area, so the guard reads black with the silencer glinting through
for j in range(-1, R // ph + 2):
    for i in range(-1, W // pw + 2):
        cx = i * pw + (pw // 2 if j % 2 else 0); cy = j * ph
        d.line([(cx - pw // 2, cy), (cx, cy - ph // 2), (cx + pw // 2, cy), (cx, cy + ph // 2), (cx - pw // 2, cy)], fill=(22, 22, 24), width=t)
rows.append(np.array(mesh, float) * 0.92 + rng.normal(0, 4, (R, W, 1)))
rows.append(noise(R, np.array([28, 28, 29]), 5))                                      # 3 black
tail = noise(W - 4 * R, np.array([146, 146, 144]), 7)
grad = np.linspace(0, 1, W)[None, :, None]; tint = np.array([[[10, 2, -10]]]) * grad   # faint straw/brown heat tint along the pipe
rows.append(np.clip(tail + tint, 0, 255))                                              # 4 dull stainless
img = Image.fromarray(np.concatenate(rows).astype(np.uint8)).convert('RGBA')
img.save(sys.argv[1], pixel_format='DXT5')
if len(sys.argv) > 2: img.convert('RGB').save(sys.argv[2])
print('wrote', sys.argv[1], img.size)
