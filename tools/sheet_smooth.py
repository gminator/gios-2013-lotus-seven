"""Turn a draped (tarp-like) mesh into a smooth sheet: keep x/z, relax y of the visible top by Laplacian smoothing
with the edge and the skirt held fixed, then recompute smooth normals (skirt normals kept straight up)."""
import numpy as np
from collections import defaultdict

def smooth_sheet(Pw, Nw, I, iters=400, top_ny=0.55):
    """Pw: Nx3 world positions, Nw: Nx3 world normals, I: flat index array. Returns new positions and normals (world)."""
    key = {}; weld = np.zeros(len(Pw), int); rep = []
    for i, p in enumerate(Pw):
        k = (round(p[0], 4), round(p[1], 4), round(p[2], 4))
        if k not in key: key[k] = len(rep); rep.append(i)
        weld[i] = key[k]
    n = len(rep); P = Pw[rep].copy(); N = Nw[rep]
    tri = weld[I.reshape(-1, 3)]
    nbr = defaultdict(set); ecount = defaultdict(int)
    for a, b, c in tri:
        for u, v in ((a, b), (b, c), (c, a)):
            nbr[u].add(v); nbr[v].add(u); ecount[tuple(sorted((u, v)))] += 1
    boundary = {v for e, c in ecount.items() if c == 1 for v in e}
    free = np.array([i not in boundary and N[i, 1] > top_ny for i in range(n)])
    nb = [np.array(sorted(nbr[i])) for i in range(n)]
    y = P[:, 1].copy()
    for _ in range(iters):
        ny = y.copy()
        for i in np.where(free)[0]:
            if len(nb[i]): ny[i] = y[nb[i]].mean()
        y = ny
    P[:, 1] = y
    # smooth normals from the new shape
    acc = np.zeros((n, 3))
    for a, b, c in tri:
        fn = np.cross(P[b] - P[a], P[c] - P[a]); acc[a] += fn; acc[b] += fn; acc[c] += fn
    L = np.linalg.norm(acc, axis=1); L[L == 0] = 1; Nn = acc / L[:, None]
    Nn[Nn[:, 1] < 0] *= -1                                   # all up-facing
    Nn[~free] = (0.0, 1.0, 0.0)                              # skirt / edge: straight up so the rolled edge never goes dark
    return P[weld], Nn[weld], int(free.sum()), n
