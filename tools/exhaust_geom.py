"""Giovann's side exhaust as kn5-ready geometry, built directly in the model's frame (metres).
Returns (V Nx11, I) via build(side_x, y, z_front, z_rear). UV rows (texture 1024^2, 5 rows, see exhaust_texture.py):
0 steel silencer, 1 wrapped elbow, 2 black mesh guard, 3 black, 4 dull stainless tailpipe."""
import numpy as np, math
ROWS = 5

def _tube(pts, radius, row, segs=20, u_scale=1.0, caps=False, cap_rows=None, arc=None):
    """caps: close both ends; cap_rows=(row_start, row_end) picks each cap's texture row (None leaves that end open).
    arc=(deg0, deg1): only that part of the circumference, 0 is up and 90 is outward (+x) for a tube running along z."""
    pts = [np.array(p, float) for p in pts]
    q = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        for k in range(1, 4): q.append(a + (b - a) * k / 3)
    pts = q
    tans = []
    for i in range(len(pts)):
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]; tans.append(d / np.linalg.norm(d))
    up = np.array([0, 1.0, 0]) if abs(tans[0] @ np.array([0, 1.0, 0])) < 0.9 else np.array([1.0, 0, 0])
    n = up - tans[0] * (up @ tans[0]); n /= np.linalg.norm(n); normals = [n]
    for i in range(1, len(pts)):
        n = normals[-1] - tans[i] * (normals[-1] @ tans[i]); normals.append(n / np.linalg.norm(n))
    L = sum(np.linalg.norm(b - a) for a, b in zip(pts, pts[1:])); s = 0
    V, I = [], []
    for i, p in enumerate(pts):
        if i: s += np.linalg.norm(pts[i] - pts[i - 1])
        bn = np.cross(tans[i], normals[i])
        for k in range(segs + 1):            # +1: duplicate seam vertex so UVs do not wrap
            a = math.radians(arc[0] + (arc[1] - arc[0]) * k / segs) if arc else 2 * math.pi * k / segs
            nrm = normals[i] * math.cos(a) + bn * math.sin(a)
            V.append([*(p + nrm * radius), *nrm, s / L * u_scale, (row + 0.08 + (k / segs) * 0.84) / ROWS - 1.0, 0, 0, 0])   # image_y = 1 + v
    w = segs + 1
    for i in range(len(pts) - 1):
        for k in range(segs):
            a, b, c, d = i * w + k, i * w + k + 1, (i + 1) * w + k + 1, (i + 1) * w + k
            I += [a, b, c, a, c, d]      # counter-clockwise about the outward normal, as the mod's meshes are wound (the game culls back faces)
    if caps and cap_rows is None: cap_rows = (3, 3)
    if cap_rows:
        for ring, tn, crow in ((0, -tans[0], cap_rows[0]), (len(pts) - 1, tans[-1], cap_rows[1])):
            if crow is None: continue
            c = len(V); V.append([*pts[ring], *tn, 0.5, (crow + 0.5) / ROWS - 1.0, 0, 0, 0])
            for k in range(segs):
                a, b = ring * w + k, ring * w + k + 1
                I += ([c, a, b] if ring == 0 else [c, b, a])
    return np.array(V, np.float32), np.array(I, np.int64)


def _annulus(c, r_in, r_out, row, segs=40, nx=1.0, depth=0.004):
    """flat ring facing +x (nx=+1) or -x, with a short outer lip of `depth`; UV row of the exhaust texture"""
    cx, cy, cz = c; V, I = [], []
    for k in range(segs + 1):
        a = 2 * math.pi * k / segs; ca, sa = math.cos(a), math.sin(a)
        for r in (r_in, r_out):
            V.append([cx, cy + r * ca, cz + r * sa, nx, 0, 0, k / segs, (row + 0.5) / ROWS - 1.0, 0, 0, 1])
    for k in range(segs):
        a, b, c2, d = 2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2
        I += ([a, b, c2, a, c2, d] if nx > 0 else [a, c2, b, a, d, c2])
    base = len(V)
    for k in range(segs + 1):                       # lip: outer edge back to the panel
        a = 2 * math.pi * k / segs; ca, sa = math.cos(a), math.sin(a)
        V.append([cx, cy + r_out * ca, cz + r_out * sa, 0, ca, sa, k / segs, (row + 0.5) / ROWS - 1.0, 0, 0, 1])
        V.append([cx - nx * depth, cy + r_out * ca, cz + r_out * sa, 0, ca, sa, k / segs, (row + 0.5) / ROWS - 1.0, 0, 0, 1])
    for k in range(segs):
        a, b, c2, d = base + 2 * k, base + 2 * k + 1, base + 2 * k + 3, base + 2 * k + 2
        I += ([a, c2, b, a, d, c2] if nx > 0 else [a, b, c2, a, c2, d])
    return np.array(V, np.float32), np.array(I, np.int64)

def _disc_z(c, r_in, r_out, row, nz=-1.0, segs=40):
    """flat ring in the x-y plane facing +z (nz=+1, forward) or -z (rearward): closes the open end of the mesh guard"""
    cx, cy, cz = c; V, I = [], []
    for k in range(segs + 1):
        a = 2 * math.pi * k / segs; ca, sa = math.cos(a), math.sin(a)
        for r in (r_in, r_out):
            V.append([cx + r * ca, cy + r * sa, cz, 0, 0, nz, k / segs, (row + 0.5) / ROWS - 1.0, 1, 0, 0])
    for k in range(segs):
        a, b, c2, d = 2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2
        I += ([a, c2, b, a, d, c2] if nz > 0 else [a, b, c2, a, c2, d])
    return np.array(V, np.float32), np.array(I, np.int64)


def build(Y=0.118, z_front=0.665, z_rear=-0.405, x_front=0.491, x_rear=0.581, y_hole=0.23, z_hole=0.80, x_panel=0.37):
    # y_hole/z_hole/x_panel: the mod's own 14 x 13 cm cut-out in the left lower panel (the Caterham manifold hole); the elbow goes through it
    """Silencer axis follows the tapering body side (x_front at z_front, x_rear at z_rear). The elbow leaves the flat side
    panel at (x_panel, y_hole, z_hole), comes out into the open and curves down into the top of the silencer's front end."""
    parts = []
    def axis(z):
        t = (z - z_front) / (z_rear - z_front); return x_front + (x_rear - x_front) * t
    xe = axis(z_front) + 0.0
    # elbow: from inside the bay, through the panel, out and down into the silencer front
    parts.append(_tube([(x_panel - 0.14, y_hole, z_hole), (x_panel + 0.02, y_hole, z_hole), (x_panel + 0.07, y_hole - 0.01, z_hole - 0.005),
                        (xe - 0.01, y_hole - 0.05, z_hole - 0.04), (xe, Y + 0.05, z_hole - 0.09), (xe, Y, z_hole - 0.125), (xe, Y, z_hole - 0.17)], 0.031, 1))   # last leg runs 4 cm into the silencer so the join is buried
    # rubber grommet flush with the panel
    # rubber edge trim round the cut-out: a slim black ring just proud of the panel, and a dark back plate 4 cm inside so the opening has depth
    parts.append(_annulus((x_panel + 0.006, y_hole, z_hole), 0.080, 0.097, 3, nx=1.0, depth=0.008))
    from rack_geom import _box
    parts.append(_box((x_panel - 0.04, y_hole, z_hole), (0.004, 0.19, 0.19), 3))   # round grommet wide enough to cover the rectangular cut-out's corners
    # silencer, guard and bands along the angled axis
    parts.append(_tube([(axis(z_front), Y, z_front), (axis(z_rear), Y, z_rear)], 0.045, 0, cap_rows=(0, 0)))          # 90 mm silencer
    parts.append(_tube([(axis(z_front - 0.02), Y, z_front - 0.02), (axis(z_rear + 0.02), Y, z_rear + 0.02)], 0.053, 2, segs=16, u_scale=0.73, arc=(-20, 200)))   # the guard is a half shell on the outer side only, 106 mm, tucked just under the top and bottom
    for z in (z_front - 0.02, z_front - 0.56, z_front - 0.96, z_rear + 0.02):
        parts.append(_tube([(axis(z + 0.012), Y, z + 0.012), (axis(z - 0.012), Y, z - 0.012)], 0.056, 3, segs=24))
    # the guard is open-ended, so close both ends with a black ring (the game culls its inner faces, which read as a hole)
    parts.append(_disc_z((axis(z_rear + 0.02), Y, z_rear + 0.02), 0.027, 0.056, 3, nz=-1.0))
    parts.append(_disc_z((axis(z_front - 0.02), Y, z_front - 0.02), 0.027, 0.056, 3, nz=1.0))
    # tailpipe, as on his car: out of the guard end, straight back about 9 cm, then a tight bend down ahead of the rear wheel,
    # leaning out a little, the mouth hanging just below the guard and pointing at the ground. Bare stainless, so its own texture row.
    xr = axis(z_rear)
    parts.append(_tube([(xr, Y, z_rear + 0.015), (xr, Y, z_rear - 0.09), (xr + 0.012, Y - 0.012, z_rear - 0.135),
                        (xr + 0.03, Y - 0.04, z_rear - 0.162), (xr + 0.04, Y - 0.07, z_rear - 0.17), (xr + 0.046, Y - 0.095, z_rear - 0.172)],
                       0.026, 4, segs=24, cap_rows=(None, 3)))          # 52 mm tailpipe
    V = np.concatenate([p[0] for p in parts]); I = []; off = 0
    for v, i in parts: I += list(i + off); off += len(v)
    I = np.array(I, np.uint16)
    T = np.zeros((len(V), 3))
    for a, b, c in I.reshape(-1, 3):
        e1, e2 = V[b, :3] - V[a, :3], V[c, :3] - V[a, :3]; d1, d2 = V[b, 6:8] - V[a, 6:8], V[c, 6:8] - V[a, 6:8]
        det = d1[0] * d2[1] - d2[0] * d1[1]
        if abs(det) < 1e-12: continue
        tg = (e1 * d2[1] - e2 * d1[1]) / det; T[a] += tg; T[b] += tg; T[c] += tg
    nrm = np.linalg.norm(T, axis=1); nrm[nrm == 0] = 1; V[:, 8:11] = T / nrm[:, None]
    return V, I

def to_local(V, world):
    """world-space verts (kn5 row convention P_w = [p,1] @ M) into a node's local frame; normals and tangents rotated too"""
    R = world[:3, :3]; t = world[3, :3]; Ri = np.linalg.inv(R)
    V = V.copy(); V[:, :3] = (V[:, :3] - t) @ Ri; V[:, 3:6] = V[:, 3:6] @ Ri; V[:, 8:11] = V[:, 8:11] @ Ri
    return V

if __name__ == '__main__':
    V, I = build(); print(len(V), 'verts', len(I) // 3, 'tris', 'bbox', V[:, :3].min(0).round(3), V[:, :3].max(0).round(3))
