"""Satin-varnished hardwood like his dash: warm medium brown, straight fine grain with soft figure. Tileable.
    python3 wood_texture.py out.png [size]"""
import sys, numpy as np
from PIL import Image, ImageFilter
out = sys.argv[1]; S = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
rng = np.random.default_rng(11)
def tile_noise(freq_x, freq_y, octaves=4, seed=0):
    """value noise, periodic, stretched: freq_x cells across the grain, freq_y along it"""
    r = np.random.default_rng(seed); acc = np.zeros((S, S)); amp = 1.0
    for o in range(octaves):
        fx, fy = freq_x * 2 ** o, freq_y * 2 ** o
        g = r.random((fy + 1, fx + 1)); g[-1] = g[0]; g[:, -1] = g[:, 0]
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC)
        acc += (np.asarray(im) / 255.0 - 0.5) * amp; amp *= 0.5
    return acc
figure = tile_noise(3, 2, 3, 1)                 # broad light/dark figure
grain = tile_noise(220, 3, 3, 2)                # fine lines across x (grain runs along y)
pores = tile_noise(400, 40, 1, 3)
t = 0.5 + 0.9 * figure + 0.35 * grain + 0.12 * pores
t = np.clip(t, 0, 1)
dark = np.array([112, 62, 30]); light = np.array([178, 116, 62])
rgb = dark + (light - dark) * t[..., None]
# soft varnish sheen bands
sheen = 0.06 * tile_noise(2, 6, 2, 4)
rgb = np.clip(rgb * (1 + sheen[..., None]), 0, 255).astype(np.uint8)
img = Image.fromarray(rgb).rotate(90, expand=True)   # grain along x, like the dash plank
img = img.filter(ImageFilter.GaussianBlur(0.4)); img.save(out); print('wood written', out)
