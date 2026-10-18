"""Giovann's side exhaust as kn5-ready geometry, built directly in the model's frame (metres).
Returns (V Nx11, I) via build(side_x, y, z_front, z_rear). UV rows (texture 1024^2, 4 rows): 0 steel, 1 wrapped elbow, 2 mesh guard, 3 black."""
import numpy as np, math

def _tube(pts, radius, row, segs=20, u_scale=1.0, caps=False):
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
            a = 2 * math.pi * k / segs; nrm = normals[i] * math.cos(a) + bn * math.sin(a)
            V.append([*(p + nrm * radius), *nrm, s / L * u_scale, (row + 0.08 + (k / segs) * 0.84) / 4 - 1.0, 0, 0, 0])   # image_y = 1 + v
    w = segs + 1
    for i in range(len(pts) - 1):
        for k in range(segs):
            a, b, c, d = i * w + k, i * w + k + 1, (i + 1) * w + k + 1, (i + 1) * w + k
            I += [a, b, c, a, c, d]      # counter-clockwise about the outward normal, as the mod's meshes are wound (the game culls back faces)
    if caps:
        for ring, tn in ((0, -tans[0]), (len(pts) - 1, tans[-1])):
            c = len(V); V.append([*pts[ring], *tn, 0.5, 3.5 / 4 - 1.0, 0, 0, 0])
            for k in range(segs):
                a, b = ring * w + k, ring * w + k + 1
                I += ([c, a, b] if ring == 0 else [c, b, a])
    return np.array(V, np.float32), np.array(I, np.int64)

def build(Y=0.135, z_front=0.665, z_rear=-0.405, x_front=0.491, x_rear=0.581, y_hole=0.23, z_hole=0.80, x_panel=0.37):
    # y_hole/z_hole/x_panel: the mod's own 14 x 13 cm cut-out in the left lower panel (the Caterham manifold hole); the elbow goes through it
    """Silencer axis follows the tapering body side (x_front at z_front, x_rear at z_rear). The elbow leaves the flat side
    panel at (x_panel, y_hole, z_hole), comes out into the open and curves down into the top of the silencer's front end."""
    parts = []
    def axis(z):
        t = (z - z_front) / (z_rear - z_front); return x_front + (x_rear - x_front) * t
    xe = axis(z_front) + 0.0
    # elbow: from inside the bay, through the panel, out and down into the silencer front
    parts.append(_tube([(x_panel - 0.14, y_hole, z_hole), (x_panel + 0.02, y_hole, z_hole), (x_panel + 0.07, y_hole - 0.01, z_hole - 0.005),
                        (xe - 0.01, y_hole - 0.05, z_hole - 0.04), (xe, Y + 0.05, z_hole - 0.09), (xe, Y, z_hole - 0.125), (xe, Y, z_hole - 0.17)], 0.034, 1))   # last leg runs 4 cm into the silencer so the join is buried
    # rubber grommet flush with the panel
    parts.append(_tube([(x_panel - 0.004, y_hole, z_hole), (x_panel + 0.012, y_hole, z_hole)], 0.097, 3, segs=36, caps=True))   # round grommet wide enough to cover the rectangular cut-out's corners
    # silencer, guard and bands along the angled axis
    parts.append(_tube([(axis(z_front), Y, z_front), (axis(z_rear), Y, z_rear)], 0.062, 0, caps=True))
    parts.append(_tube([(axis(z_front - 0.02), Y, z_front - 0.02), (axis(z_rear + 0.02), Y, z_rear + 0.02)], 0.082, 2, segs=24, u_scale=6.0))
    for z in (z_front - 0.02, z_front - 0.56, z_front - 0.96, z_rear + 0.02):
        parts.append(_tube([(axis(z + 0.012), Y, z + 0.012), (axis(z - 0.012), Y, z - 0.012)], 0.086, 3, segs=24))
    # tailpipe sweeps outward with a slight drop
    xr = axis(z_rear)
    parts.append(_tube([(xr, Y, z_rear), (xr, Y, z_rear - 0.06), (xr + 0.02, Y - 0.004, z_rear - 0.10), (xr + 0.07, Y - 0.015, z_rear - 0.135), (xr + 0.13, Y - 0.03, z_rear - 0.15), (xr + 0.19, Y - 0.04, z_rear - 0.155)], 0.03, 0))
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
