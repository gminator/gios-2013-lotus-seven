"""Driving report from a recorded Assetto Corsa session: one page per thing to work on.
    python3 tools/sim_report.py <telemetry.db> <session_id> <out.pdf>
Needs smooth_engine.py and coach.py from the telemetry project next to telemetry.db (it leaves out replays of earlier laps)."""
import sqlite3, sys, math, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
db, sid, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
con = sqlite3.connect(db)
cols = ['t', 'speed_kmh', 'gas', 'brake', 'clutch', 'rpm', 'steer', 'gear', 'g_horizontal', 'g_frontal', 'lap_count', 'position_normalized', 'slip_ratio_rl', 'slip_ratio_rr', 'x', 'z']
R = np.array(con.execute(f"select {','.join(cols)} from samples where session_id=? order by t", (sid,)).fetchall(), float)
_, u = np.unique(R[:, 0], return_index=True); R = R[u]                       # the recorder stored some stretches twice
# the game's own replay of earlier laps is recorded like driving: find it from repeated lap times and drop it
sys.path.insert(0, str(__import__('pathlib').Path(db).resolve().parent))
from smooth_engine import Engine, COLS as ECOLS
_eng = Engine(); _drop = []
for _r in con.execute(f"select {','.join(ECOLS)} from samples where session_id=? order by t", (sid,)):
    _eng.feed(_r)
    if _eng.replaying: _drop.append(_r[0])
if _eng.replay_runs:
    # rows fed before the replay was recognised (its first lap) belong to the same run: drop from the run's start
    _cut = min(_eng.run_starts[r] for r in _eng.replay_runs)
    R = R[R[:, 0] < _cut]
    print('replay of earlier laps found and left out from', round(_cut), 's on')
C = {n: R[:, i] for i, n in enumerate(cols)}
t, v, gas, brk, rpm, steer, gear = C['t'], C['speed_kmh'], C['gas'], C['brake'], C['rpm'], C['steer'], C['gear']
dt = np.median(np.diff(t))
laps = con.execute("select lap, time_ms from laps where session_id=? and time_ms>0 order by lap", (sid,)).fetchall()
best_lap, best_ms = min(laps[1:] or laps, key=lambda l: l[1])
def fmt(ms): s = ms / 1000; return f"{int(s // 60)}:{s % 60:06.3f}"
# a clean lap for traces: the lap_count block whose duration matches a lap time
blocks = {}
for L in np.unique(C['lap_count']):
    m = C['lap_count'] == L; blocks[L] = (t[m][-1] - t[m][0], m)
clean = min(blocks.items(), key=lambda kv: abs(kv[1][0] - best_ms / 1000))[1][1]
o = np.argsort(C['position_normalized'][clean])
L = {k: C[k][clean][o] for k in cols}
# corners on the clean lap, numbered from the start line
k = 60; vv = L['speed_kmh']; pp = L['position_normalized']
mins = [i for i in range(k, len(vv) - k) if vv[i] == vv[i - k:i + k + 1].min() and vv[i] < 0.9 * vv[max(0, i - 4 * k):i + 4 * k].max()]
corners = []
for i in mins:
    if abs(L['steer'][i]) < 10: continue                       # a lift on a straight, not a corner
    if not corners or pp[i] - pp[corners[-1]] > 0.03: corners.append(i)
# ---- downshifts (through neutral)
FD = 3.916667; RT = 0.292; old = {1: 3.65, 2: 1.97, 3: 1.37, 4: 1.0}; new = {1: 3.65, 2: 1.60, 3: 1.30, 4: 1.0}
def rpm_at(vk, g, ratios): return vk / 3.6 / (2 * math.pi * RT) * 60 * ratios[g] * FD
down = []; lg = li = None
for i in range(len(gear)):
    g = int(gear[i])
    if g < 1: continue
    if lg is not None and g < lg and v[i] > 15 and t[i] - t[li] < 3: down.append((i, lg, g))
    lg, li = g, i
D = []
for i, g0, g1 in down:
    w = slice(max(0, i - int(0.25 / dt)), i + int(0.25 / dt))
    slip = np.abs(np.r_[C['slip_ratio_rl'][i:i + int(0.6 / dt)], C['slip_ratio_rr'][i:i + int(0.6 / dt)]]).max()
    D.append((v[i], g0, g1, brk[w].max(), rpm_at(v[i], g1, old), slip))
D = np.array(D)
coast = (gas < 0.05) & (brk < 0.05) & (v > 40)
INK = '#1f1f1f'; MUTED = '#6f6f6f'; GRID = '#e6e6e2'; BRG = '#0b3d2e'; YEL = '#d9a406'; RED = '#b3261e'; PALE = '#9ec7b3'
plt.rcParams.update({'font.family': 'Helvetica Neue', 'font.size': 10.5, 'axes.edgecolor': GRID, 'axes.labelcolor': MUTED, 'xtick.color': MUTED, 'ytick.color': MUTED, 'figure.facecolor': 'white', 'axes.facecolor': 'white'})
def page(title, kicker):
    f = plt.figure(figsize=(8.27, 11.69))
    f.text(0.07, 0.95, kicker.upper(), color=MUTED, fontsize=9, weight='bold')
    f.text(0.07, 0.915, title, color=INK, fontsize=20, weight='bold')
    f.text(0.07, 0.03, f"Killarney in Assetto Corsa, the Birkin twin, 18 October 2026. Session {sid}, best lap {fmt(best_ms)}. Gearing at the time: 2nd 1.97, 3rd 1.37.", color=MUTED, fontsize=8)
    return f
import textwrap
def body(f, y, lines, size=10.5):
    for para in lines:
        if not para: y -= 0.012; continue
        for ln in textwrap.wrap(para, 92):
            f.text(0.07, y, ln, color=INK, fontsize=size); y -= 0.022
    return y
def clean_ax(ax):
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True)
pdf = PdfPages(out)
# ---------------- page 1: downshifts
f = page('Brake, then downshift', '1 of 4  ·  Downshifts')
n = len(D); braked = np.mean(D[:, 3] > 0.15) * 100; over = int(np.sum(D[:, 4] > 6800)); locked = int(np.sum(D[:, 5] > 0.15))
d32 = D[D[:, 1] == 3]
y = body(f, 0.86, [
    f"What the data says. {n} downshifts. You were on the brake within a quarter second of the shift in {braked:.0f}% of them. {over} of {n} forced the engine above the 6,800 limiter in the new gear, and the rear wheels locked briefly after {locked}. The 3 to 2 changes were done at about {np.median(d32[:,0]):.0f} km/h, which asks 2nd for about {np.median(d32[:,4]):,.0f} rpm. That is the shunt you feel.",
    "",
    "What to do. Brake first, and keep a little brake on through the change. Shift once the speed suits the lower gear, then let the clutch out smoothly. With the new gearing that means 2nd below about 105 km/h and 3rd below about 130. The instructor's 'gear down early' means finish your braking early, not change gear while you are still fast."])
ax = f.add_axes([0.1, 0.36, 0.82, 0.28])
for g0, col, lab in ((4, PALE, '4 to 3'), (3, BRG, '3 to 2'), (2, YEL, '2 to 1')):
    s = D[D[:, 1] == g0]
    if len(s): ax.scatter(s[:, 0], s[:, 4], s=34, color=col, label=lab, edgecolor='white', linewidth=0.6, zorder=3)
ax.axhline(6800, color=RED, lw=1.5); ax.text(0.99, 6800, 'limiter 6,800 rpm  ', color=RED, fontsize=9, ha='right', va='bottom', transform=ax.get_yaxis_transform())
ax.set_xlabel('speed at the downshift, km/h'); ax.set_ylabel('engine speed the new gear asks for, rpm'); clean_ax(ax); ax.legend(frameon=False, loc='upper left')
ax.set_title('Each dot is one downshift. Above the red line, the gear change forces the engine past the limiter.', loc='left', fontsize=10, color=INK)
ax2 = f.add_axes([0.3, 0.08, 0.62, 0.18])
labels = ['braking at the shift', 'over the limiter', 'rear wheels locked']
vals = [braked, over / n * 100, locked / n * 100]
ax2.barh(labels, vals, color=[BRG, RED, RED], height=0.5)
for i_, val in enumerate(vals): ax2.text(val + 1, i_, f"{val:.0f}%", va='center', color=INK)
ax2.set_xlim(0, 100); ax2.invert_yaxis(); clean_ax(ax2); ax2.xaxis.grid(True, color=GRID); ax2.yaxis.grid(False)
ax2.set_title('Share of downshifts. Aim: braking at the shift near 100%, the other two near zero.', loc='left', fontsize=10, color=INK)
pdf.savefig(f); plt.close(f)
# ---------------- page 2: coasting
f = page('Stop coasting', '2 of 4  ·  Braking')
cl = (L['gas'] < 0.05) & (L['brake'] < 0.05) & (L['speed_kmh'] > 40)
y = body(f, 0.86, [
    f"What the data says. {coast.mean()*100:.0f}% of your driving time was spent coasting: off the throttle and off the brake. In a Seven that is lost time, and it is what made the downshifts harsh: the car slows on its own while you wait, then the clutch comes out with nothing settling the car.",
    "",
    "What to do. Every corner is throttle, then brake, then throttle again. Go straight from one pedal to the other. Brake firmly at the start, ease off as you turn in, and pick up the throttle as you unwind the wheel. On the trace below the grey bands are coasting; make them as thin as possible."])
ax = f.add_axes([0.1, 0.4, 0.82, 0.26])
xs = L['position_normalized'] * 100
ax.fill_between(xs, 0, 1, where=cl, color='#d6d6d2', step='mid', label='coasting', transform=ax.get_xaxis_transform())
ax.plot(xs, L['speed_kmh'], color=BRG, lw=1.6)
for n_, i in enumerate(corners, 1): ax.text(xs[i], L['speed_kmh'][i] - 9, str(n_), ha='center', color=INK, weight='bold')
ax.set_ylabel('km/h'); ax.set_xlabel('distance round the lap, %'); clean_ax(ax); ax.legend(frameon=False, loc='lower right')
ax.set_title(f'Best lap {fmt(best_ms)}: speed, with coasting shaded and corners numbered from the start line.', loc='left', fontsize=10, color=INK)
ax2 = f.add_axes([0.1, 0.1, 0.82, 0.24])
ax2.plot(xs, L['gas'] * 100, color=BRG, lw=1.2, label='throttle')
ax2.plot(xs, L['brake'] * 100, color=RED, lw=1.2, label='brake')
ax2.set_ylabel('%'); ax2.set_xlabel('distance round the lap, %'); clean_ax(ax2); ax2.legend(frameon=False, loc='upper right', ncol=2)
ax2.set_title('Throttle and brake. Between the two there should be no gap.', loc='left', fontsize=10, color=INK)
pdf.savefig(f); plt.close(f)
# ---------------- page 3: steering and exits
f = page('Open the wheel, let it run', '3 of 4  ·  Steering')
exit_rows = []
for n_, i in enumerate(corners, 1):
    j = min(len(vv) - 1, np.searchsorted(L['t'], L['t'][i] + 1.0))
    k2 = i
    while k2 < len(vv) - 1 and abs(L['steer'][k2]) > 0.3 * max(abs(L['steer'][i]), 1): k2 += 1
    exit_rows.append((n_, vv[i], abs(L['steer'][i]), abs(L['steer'][j]), L['t'][k2] - L['t'][i], L['gas'][j]))
E = np.array(exit_rows)
y = body(f, 0.86, [
    "What the instructor said. You turn too much; open up the steering wheel and use the car's power to push it out of the turn.",
    "",
    f"What the data says. At the slowest point of each corner you had about {np.median(E[:,2]):.0f} degrees of lock (median). One second later you were still holding about {np.median(E[:,3]):.0f} degrees with {np.median(E[:,5])*100:.0f}% throttle, and it took about {np.median(E[:,4]):.1f} s to unwind most of the lock. In {int(np.sum(E[:,3] > E[:,2]))} of {len(E)} corners you had more lock a second after the apex than at it: you were winding on lock while adding power. That is exactly what the instructor saw.",
    "",
    "What to do. Turn in once, decisively, then from the apex let the wheel come back as the throttle goes on: hands unwind and right foot presses together. If you need more lock to hold the line, you are too fast at the apex."])
ax = f.add_axes([0.1, 0.36, 0.82, 0.24])
ax.plot(xs, np.abs(L['steer']), color=BRG, lw=1.4, label='steering lock, degrees')
ax.plot(xs, L['gas'] * 100, color=YEL, lw=1.2, label='throttle, %')
for n_, i in enumerate(corners, 1): ax.text(xs[i], abs(L['steer'][i]) + 6, str(n_), ha='center', color=INK, weight='bold')
ax.set_xlabel('distance round the lap, %'); clean_ax(ax); ax.legend(frameon=False, loc='upper right')
ax.set_title('Steering and throttle together. On exit the green should fall as the yellow rises.', loc='left', fontsize=10, color=INK)
ax2 = f.add_axes([0.1, 0.08, 0.82, 0.2])
ax2.bar(E[:, 0] - 0.2, E[:, 2], width=0.38, color=PALE, label='lock at the apex')
ax2.bar(E[:, 0] + 0.2, E[:, 3], width=0.38, color=BRG, label='lock 1 s after the apex')
ax2.set_xlabel('corner'); ax2.set_ylabel('degrees'); ax2.set_xticks(E[:, 0]); clean_ax(ax2); ax2.legend(frameon=False, loc='upper right')
ax2.set_title('Per corner. The dark bar should be well below the light one.', loc='left', fontsize=10, color=INK)
pdf.savefig(f); plt.close(f)
# ---------------- page 4: gears
f = page('Gears for this track', '4 of 4  ·  Gear use')
hit = (rpm >= 6650) & (gas > 0.5)
y = body(f, 0.86, [
    f"What the data says. You were on the limiter in 2nd at two places a lap: out of corner 2, the hairpin, by about 105 km/h, and out of corner {len(corners)}, the last slow corner before the main straight, by about 117 km/h.",
    "",
    "What changed. 2nd is now 1.60 (was 1.97) and 3rd 1.30 (was 1.37), so 2nd holds through both exits.",
    "",
    "What to do. Stay in 2nd through those two exits and change up once, cleanly, at about 6,300 rpm. Fewer changes means fewer chances to get a downshift wrong."])
ax = f.add_axes([0.07, 0.33, 0.5, 0.31]); ax.set_aspect('equal'); ax.axis('off')
gcol = {1: '#e0a800', 2: '#2f7a5c', 3: '#7fb39a', 4: '#c9dfd4'}
for g in (1, 2, 3, 4):
    m = L['gear'] == g; ax.scatter(L['x'][m], L['z'][m], s=3, color=gcol[g], label=f'{g}' + ('st' if g == 1 else 'nd' if g == 2 else 'rd' if g == 3 else 'th'))
lim = (L['rpm'] >= 6650) & (L['gas'] > 0.5); ax.scatter(L['x'][lim], L['z'][lim], s=12, color=RED, label='limiter')
for n_, i in enumerate(corners, 1): ax.text(L['x'][i], L['z'][i], f' {n_}', color=INK, weight='bold')
ax.legend(frameon=False, loc='upper left', bbox_to_anchor=(1.02, 0.35), fontsize=9, markerscale=3); ax.set_title('Gear round the lap, limiter in red', loc='left', fontsize=10, color=INK)
ax2 = f.add_axes([0.62, 0.44, 0.33, 0.18]); ax2.axis('off')
circ = 2 * math.pi * RT
rows = [['gear', 'before', 'now']] + [[str(g), f"{6800/(old[g]*FD)*circ*60/1000:.0f}", f"{6800/(new[g]*FD)*circ*60/1000:.0f}"] for g in (1, 2, 3, 4)]
tb = ax2.table(cellText=rows, loc='center', cellLoc='center'); tb.scale(1, 1.8); tb.set_fontsize(11)
for (r, c_), cell in tb.get_celld().items():
    cell.set_edgecolor(GRID)
    if r == 0: cell.set_text_props(weight='bold')
ax2.set_title('km/h at the 6,800 limiter', fontsize=10, color=INK, pad=14)
ax3 = f.add_axes([0.1, 0.09, 0.82, 0.2])
share = [np.mean(gear[v > 5] == g) * 100 for g in (1, 2, 3, 4)]
ax3.bar(['1st', '2nd', '3rd', '4th'], share, color=[gcol[1], gcol[2], gcol[3], gcol[4]])
for i_, sv in enumerate(share): ax3.text(i_, sv + 1, f"{sv:.0f}%", ha='center', color=INK)
clean_ax(ax3); ax3.set_ylabel('% of driving time'); ax3.set_title('Time in each gear this session', loc='left', fontsize=10, color=INK)
pdf.savefig(f); plt.close(f)
pdf.close(); print('report written', out)
