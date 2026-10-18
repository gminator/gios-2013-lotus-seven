"""Find a boundary loop (a hole) in a kn5 mesh and build a cap that fills it exactly, using the loop's own vertices.
cap(b, x, near=(x, y, z)) -> (V Nx11 world-space, I) with normals up."""
import struct, numpy as np
from collections import defaultdict

def loops(b, x):
    V = np.array([struct.unpack_from('<3f', b, x['voff'] + i * 44) for i in range(x['nv'])])
    P = (np.c_[V, np.ones(len(V))] @ x['world'])[:, :3]
    I = np.frombuffer(b, dtype='<u2', count=x['ni'], offset=x['ioff']).reshape(-1, 3)
    key = {}; weld = np.zeros(len(P), int); pos = []
    for i, p in enumerate(P):
        k = tuple(np.round(p, 4))
        if k not in key: key[k] = len(pos); pos.append(p)
        weld[i] = key[k]
    pos = np.array(pos)
    cnt = defaultdict(int)
    for t in I:
        for a, c in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            cnt[tuple(sorted((weld[a], weld[c])))] += 1
    adj = defaultdict(list)
    for (a, c), n in cnt.items():
        if n == 1: adj[a].append(c); adj[c].append(a)
    seen, out = set(), []
    for s in adj:
        if s in seen: continue
        loop, prev, cur = [s], None, s
        seen.add(s)
        while True:
            nxt = [v for v in adj[cur] if v != prev and (v not in seen or (v == s and len(loop) > 2))]
            if not nxt: break
            if nxt[0] == s: break
            prev, cur = cur, nxt[0]; seen.add(cur); loop.append(cur)
        out.append(pos[loop])
    return out

def _earclip(P2):
    n = len(P2); idx = list(range(n))
    area = sum(P2[i][0] * P2[(i + 1) % n][1] - P2[(i + 1) % n][0] * P2[i][1] for i in range(n))
    if area < 0: idx.reverse()
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
    tris = []; guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1; ok = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = P2[i0], P2[i1], P2[i2]
            if cross(a, b, c) <= 1e-12: continue
            if any(inside(P2[j], a, b, c) for j in idx if j not in (i0, i1, i2)): continue
            tris.append((i0, i1, i2)); idx.pop(k); ok = True; break
        if not ok: break
    if len(idx) == 3: tris.append(tuple(idx))
    return tris

def cap(b, x, near, lift=0.0):
    L = min(loops(b, x), key=lambda l: np.linalg.norm(l.mean(axis=0) - np.array(near)))
    c = L.mean(axis=0)
    # fan from the centre: every rim vertex is used exactly as the body has it, so the cap meets the hole edge with no gap
    V = np.array([[c[0], c[1] + lift, c[2], 0, 1, 0, 0.5, -0.5, 1, 0, 0]] + [[p[0], p[1] + lift, p[2], 0, 1, 0, 0.5, -0.5, 1, 0, 0] for p in L], dtype=np.float32)
    n = len(L); I = np.array([[0, 1 + i, 1 + (i + 1) % n] for i in range(n)], dtype=np.int64)
    T = V[:, :3][I]; up = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])[:, 1]
    I[up < 0] = I[up < 0][:, [0, 2, 1]]                 # every triangle faces up, including the folded ones at the seam notches
    I = I.reshape(-1)
    T = V[:, :3][I.reshape(-1, 3)]; nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    if nrm[:, 1].mean() < 0: I = I.reshape(-1, 3)[:, [0, 2, 1]].reshape(-1)
    T2 = V[:, [0, 2]][I.reshape(-1, 3)]
    sgn = np.sign((T2[:, 1, 0] - T2[:, 0, 0]) * (T2[:, 2, 1] - T2[:, 0, 1]) - (T2[:, 1, 1] - T2[:, 0, 1]) * (T2[:, 2, 0] - T2[:, 0, 0]))
    return V, I, L, int((sgn == sgn[0]).sum()), len(sgn)
