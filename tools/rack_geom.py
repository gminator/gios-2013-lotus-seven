"""Wooden luggage rack on the rear deck: two ash slats on a chrome rail with a raised hoop at the back.
Car space, from the model's deck measurements; UV rows: 0 wood, 1 chrome (texture gio_rack.dds)."""
import numpy as np
from exhaust_geom import _tube

def _box(c, size, row):
    V, I = [], []
    faces = [((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (-1, 0, 0), (0, 1, 0)), ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
             ((-1, 0, 0), (0, 0, 1), (0, 1, 0)), ((0, 1, 0), (1, 0, 0), (0, 0, -1)), ((0, -1, 0), (1, 0, 0), (0, 0, 1))]
    half = np.array(size) / 2
    for n, a, b in faces:
        n, a, b = np.array(n, float), np.array(a, float), np.array(b, float)
        base = len(V)
        for sa, sb, u, v in ((-1, -1, 0, 0), (1, -1, 1, 0), (1, 1, 1, 1), (-1, 1, 0, 1)):
            p = np.array(c) + n * half + a * half * sa + b * half * sb
            V.append([*p, *n, u * 0.9 + 0.05, (row + 0.1 + v * 0.8) / 4 - 1.0, *a])
        I += [base, base + 2, base + 1, base, base + 3, base + 2]
    return np.array(V, np.float32), np.array(I, np.int64)

def build(deck_y=0.72, z_centre=-1.12, half_width=0.27):
    parts = []
    y_rail = deck_y + 0.025
    for z in (z_centre + 0.06, z_centre - 0.06):
        parts.append(_box((0, y_rail + 0.017, z), (half_width * 2, 0.022, 0.09), 0))
    r = 0.006
    loop = [(-half_width, y_rail, z_centre + 0.13), (half_width, y_rail, z_centre + 0.13), (half_width, y_rail, z_centre - 0.13), (-half_width, y_rail, z_centre - 0.13), (-half_width, y_rail, z_centre + 0.13)]
    parts.append(_tube(loop, r, 1, segs=10, u_scale=8))
    for x in (-half_width, -half_width * 0.5, 0, half_width * 0.5, half_width):
        parts.append(_tube([(x, deck_y - 0.01, z_centre + 0.13), (x, y_rail, z_centre + 0.13)], r, 1, segs=8))
        parts.append(_tube([(x, deck_y - 0.01, z_centre - 0.13), (x, y_rail, z_centre - 0.13)], r, 1, segs=8))
    hw = half_width * 0.6
    parts.append(_tube([(-hw, y_rail, z_centre - 0.13), (-hw, y_rail + 0.08, z_centre - 0.13), (-hw, y_rail + 0.09, z_centre - 0.12), (hw, y_rail + 0.09, z_centre - 0.12), (hw, y_rail + 0.08, z_centre - 0.13), (hw, y_rail, z_centre - 0.13)], r, 1, segs=10, u_scale=6))
    V = np.concatenate([p[0] for p in parts]); I = []; off = 0
    for v, i in parts: I += list(np.asarray(i) + off); off += len(v)
    return V, np.array(I, np.uint16)
