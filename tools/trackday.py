"""Killarney track day from the Garmin 1 Hz trace: laps, heat map, lines, best-lap trace.
    python3 tools/trackday.py trackday/2026-10-14/garmin-1hz.csv trackday/2026-10-14"""
import csv, math, sys, os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
src, out = sys.argv[1], sys.argv[2]
rows = [r for r in csv.DictReader(open(src)) if r['lat'] and r['speed_kmh']]
t = np.array([float(r['t']) for r in rows]); lat = np.array([float(r['lat']) for r in rows]); lon = np.array([float(r['lon']) for r in rows])
v = np.array([float(r['speed_kmh']) for r in rows])
lat0, lon0 = lat.mean(), lon.mean(); x = (lon - lon0) * 111320 * math.cos(math.radians(lat0)); y = (lat - lat0) * 110540
# start line: perpendicular to the main straight, 6 s before the fastest point
i_max = int(np.argmax(v)); j = i_max - 6
d = np.array([x[j + 1] - x[j - 1], y[j + 1] - y[j - 1]]); d /= np.linalg.norm(d); px, py = x[j], y[j]
s = (x - px) * d[0] + (y - py) * d[1]; lateral = np.abs(-(x - px) * d[1] + (y - py) * d[0])
cross = [i for i in range(1, len(t)) if s[i - 1] < 0 <= s[i] and lateral[i] < 25 and v[i] > 50]
def tcross(i): return t[i - 1] + (t[i] - t[i - 1]) * (-s[i - 1]) / (s[i] - s[i - 1])
laps = []
for a, b in zip(cross, cross[1:]):
    ta, tb = tcross(a), tcross(b)
    laps.append(dict(a=a, b=b, time=tb - ta, vmax=v[a:b].max(), start=ta))
flying = [l for l in laps if l['time'] < 300]
for k, l in enumerate(laps): l['n'] = k + 1
# stints: split where a lap is a pit stop (> 5 min)
stint, sn = [], 1
for l in laps:
    if l['time'] >= 300: sn += 1; continue
    l['stint'] = sn
best = min(flying, key=lambda l: l['time'])
INK = '#1f1f1f'; MUTED = '#7a7a7a'; GRID = '#e6e6e2'; BRG = '#0b3d2e'; YEL = '#e2aa09'
plt.rcParams.update({'font.family': 'Helvetica Neue', 'font.size': 11, 'axes.edgecolor': GRID, 'axes.labelcolor': MUTED, 'xtick.color': MUTED, 'ytick.color': MUTED, 'figure.facecolor': '#fafaf7', 'axes.facecolor': '#fafaf7'})
greens = LinearSegmentedColormap.from_list('greens', ['#dcebe2', '#7fb39a', '#2f7a5c', BRG])
def fmt(sec): return f"{int(sec // 60)}:{sec % 60:06.3f}"
# 1. heat map: every flying lap's line coloured by speed (one hue, light = slow, dark = fast)
fig, ax = plt.subplots(figsize=(9, 9)); ax.set_aspect('equal'); ax.axis('off')
for l in flying:
    a, b = l['a'], l['b']; pts = np.c_[x[a:b + 1], y[a:b + 1]].reshape(-1, 1, 2); segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    lc = LineCollection(segs, cmap=greens, norm=plt.Normalize(40, 150), linewidth=2.2, alpha=0.9); lc.set_array(v[a:b]); ax.add_collection(lc)
ax.autoscale()
cb = fig.colorbar(lc, ax=ax, fraction=0.03, pad=0.01, ticks=[40, 60, 80, 100, 120, 140]); cb.set_label('km/h', color=MUTED); cb.outline.set_visible(False); cb.ax.tick_params(color=MUTED, labelcolor=MUTED)
# direct labels: slowest point of each corner on the best lap, and the top speed
a, b = best['a'], best['b']; vb = v[a:b]; xb, yb = x[a:b], y[a:b]
mins = [i for i in range(3, len(vb) - 3) if vb[i] == vb[i - 3:i + 4].min() and vb[i] < 95]
keep = []
for i in mins:
    if not keep or i - keep[-1] > 8: keep.append(i)
for n, i in enumerate(keep, 1):
    ax.annotate(f"{n}  {vb[i]:.0f}", (xb[i], yb[i]), xytext=(8, 8), textcoords='offset points', color=INK, fontsize=11, fontweight='bold')
im = int(np.argmax(vb)); ax.annotate(f"{vb[im]:.0f} km/h", (xb[im], yb[im]), xytext=(10, -14), textcoords='offset points', color=INK, fontsize=11, fontweight='bold')
ax.plot([px - d[1] * 30, px + d[1] * 30], [py + d[0] * 30, py - d[0] * 30], color=YEL, lw=3); ax.annotate('start / finish', (px + d[1] * 30, py - d[0] * 30), xytext=(6, 0), textcoords='offset points', color=MUTED)
ax.set_title(f"Killarney, 14 October 2026: speed around the lap, {len(flying)} flying laps\nnumbers are the slowest speed at each corner on the best lap ({fmt(best['time'])})", loc='left', color=INK, fontsize=13)
fig.savefig(os.path.join(out, 'heatmap.png'), dpi=160, bbox_inches='tight'); plt.close(fig)
# 2. racing lines: every flying lap thin, best lap bold
fig, ax = plt.subplots(figsize=(9, 9)); ax.set_aspect('equal'); ax.axis('off')
for l in flying:
    la, lb = l['a'], l['b']; ax.plot(x[la:lb + 1], y[la:lb + 1], color='#7fb39a', lw=0.9, alpha=0.7)
ax.plot([], [], color='#7fb39a', lw=0.9, alpha=0.7, label='every flying lap')
ax.plot(xb, yb, color=BRG, lw=2.4, label=f"best lap {fmt(best['time'])}")
ax.legend(frameon=False, loc='lower right', labelcolor=INK)
ax.set_title('Racing line, lap by lap: where the lines fan out, the line is not yet consistent', loc='left', color=INK, fontsize=13)
fig.savefig(os.path.join(out, 'lines.png'), dpi=160, bbox_inches='tight'); plt.close(fig)
# 3. lap times: thin bars, direct labels, best in BRG
fig, ax = plt.subplots(figsize=(11, 4.2))
xs = np.arange(len(flying)); times = [l['time'] for l in flying]
cols = [BRG if l is best else '#9ec7b3' for l in flying]
ax.bar(xs, times, width=0.55, color=cols, edgecolor='none')
for i, l in enumerate(flying):
    ax.text(i, l['time'] + 1.5, fmt(l['time'])[:-2], ha='center', va='bottom', color=INK, fontsize=9)
    ax.text(i, 100, f"{l['vmax']:.0f}", ha='center', va='bottom', color='#fafaf7', fontsize=8)
ax.set_xticks(xs); ax.set_xticklabels([f"L{l['n']}\nS{l['stint']}" for l in flying], fontsize=8); ax.set_ylim(95, max(times) + 12)
ax.set_yticks([100, 110, 120, 130, 140, 150]); ax.set_yticklabels([fmt(s)[:-4] for s in [100, 110, 120, 130, 140, 150]])
for sp in ['top', 'right']: ax.spines[sp].set_visible(False)
ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True)
ax.set_title('Lap times (top speed in km/h inside each bar); L = lap on the day, S = stint', loc='left', color=INK, fontsize=13)
fig.savefig(os.path.join(out, 'laptimes.png'), dpi=160, bbox_inches='tight'); plt.close(fig)
# 4. best lap trace: speed against distance
dist = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xb), np.diff(yb)))])
fig, ax1 = plt.subplots(figsize=(11, 4))
ax1.plot(dist, vb, color=BRG, lw=2); ax1.set_ylabel('km/h'); ax1.set_xlabel('metres from the start line')
for n, i in enumerate(keep, 1): ax1.annotate(str(n), (dist[i], vb[i]), xytext=(0, -14), textcoords='offset points', ha='center', color=INK, fontweight='bold')
for sp in ['top', 'right']: ax1.spines[sp].set_visible(False)
ax1.yaxis.grid(True, color=GRID); ax1.set_axisbelow(True)
ax1.set_title(f"Best lap {fmt(best['time'])} (lap {best['n']}): speed around the lap, corners numbered", loc='left', color=INK, fontsize=13)
fig.savefig(os.path.join(out, 'bestlap.png'), dpi=160, bbox_inches='tight'); plt.close(fig)
# 5. tables
with open(os.path.join(out, 'laps.csv'), 'w') as f:
    f.write('lap,stint,time_s,time,top_speed_kmh\n')
    for l in flying: f.write(f"{l['n']},{l['stint']},{l['time']:.3f},{fmt(l['time'])},{l['vmax']:.1f}\n")
with open(os.path.join(out, 'laps.md'), 'w') as f:
    f.write('| Lap | Stint | Time | Top speed |\n|---|---|---|---|\n')
    for l in flying: f.write(f"| {l['n']} | {l['stint']} | {'**' if l is best else ''}{fmt(l['time'])}{'**' if l is best else ''} | {l['vmax']:.0f} km/h |\n")
print(f"{len(flying)} flying laps, best {fmt(best['time'])} on lap {best['n']}, top speed {max(l['vmax'] for l in flying):.0f} km/h, corners found {len(keep)}")
