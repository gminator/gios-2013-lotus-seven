"""Draw dyno/ curves: python3 tools/dyno_chart.py out.png title label=file.csv[:style] ...   style = solid|dash
CSV columns: rpm,torque_nm_crank,power_bhp_crank"""
import sys, csv
from PIL import Image, ImageDraw, ImageFont
out, title = sys.argv[1], sys.argv[2]
series = []
for arg in sys.argv[3:]:
    label, rest = arg.split('=', 1); path, _, style = rest.partition(':')
    rows = [r for r in csv.DictReader(open(path))]
    series.append((label, [(float(r['rpm']), float(r['torque_nm_crank']), float(r['power_bhp_crank'])) for r in rows], style or 'solid'))
W, H = 1400, 800; L, R_, T, B = 110, 110, 70, 90
im = Image.new('RGB', (W, H), (250, 250, 247)); d = ImageDraw.Draw(im)
F = lambda s: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', s)
Fn = lambda s: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', s)
x0, x1, y0, y1 = L, W - R_, T, H - B
rmin, rmax, tmax, pmax = 1000, 7500, 200, 160
X = lambda r: x0 + (r - rmin) / (rmax - rmin) * (x1 - x0)
YT = lambda t: y1 - t / tmax * (y1 - y0); YP = lambda p: y1 - p / pmax * (y1 - y0)
for r in range(1000, 7501, 500):
    d.line([(X(r), y0), (X(r), y1)], fill=(225, 225, 220)); d.text((X(r), y1 + 12), str(r), font=Fn(20), fill=(90, 90, 90), anchor='mt')
for t in range(0, 201, 25):
    d.line([(x0, YT(t)), (x1, YT(t))], fill=(232, 232, 228)); d.text((x0 - 12, YT(t)), str(t), font=Fn(20), fill=(90, 90, 90), anchor='rm')
for p in range(0, 161, 20):
    d.text((x1 + 12, YP(p)), str(p), font=Fn(20), fill=(90, 90, 90), anchor='lm')
d.rectangle([x0, y0, x1, y1], outline=(120, 120, 120), width=2)
def line(pts, col, w, dash):
    for a, b in zip(pts, pts[1:]):
        if dash:
            for k in range(0, 6, 2):
                d.line([(a[0] + (b[0] - a[0]) * k / 6, a[1] + (b[1] - a[1]) * k / 6), (a[0] + (b[0] - a[0]) * (k + 1) / 6, a[1] + (b[1] - a[1]) * (k + 1) / 6)], fill=col, width=w)
        else:
            d.line([a, b], fill=col, width=w)
palette = [((11, 61, 46), (226, 170, 9)), ((90, 130, 110), (235, 205, 120)), ((170, 170, 170), (170, 170, 170))]
lx, ly = x0 + 30, y0 + 25
for i, (label, pts, style) in enumerate(series):
    ct, cp = palette[min(i, 2)]; dash = style == 'dash'; w = 7 if i == 0 else 4
    pts = [p for p in pts if rmin <= p[0] <= rmax]
    line([(X(r), YT(t)) for r, t, p in pts], ct, w, dash); line([(X(r), YP(p)) for r, t, p in pts], cp, w, dash)
    pk = max(pts, key=lambda p: p[2]); tq = max(pts, key=lambda p: p[1])
    line([(lx, ly), (lx + 60, ly)], ct, 6, dash); d.text((lx + 75, ly), f"{label}: {pk[2]:.0f} bhp at {pk[0]:.0f}, {tq[1]:.0f} Nm at {tq[0]:.0f}", font=Fn(22), fill=(40, 40, 40), anchor='lm'); ly += 34
d.text((W // 2, 22), title, font=F(30), fill=(30, 30, 30), anchor='mt')
d.text((x0, y0 - 28), "Nm", font=Fn(20), fill=(90, 90, 90), anchor='lb'); d.text((x1, y0 - 28), "bhp", font=Fn(20), fill=(90, 90, 90), anchor='rb')
d.text((W // 2, H - 30), "rpm", font=Fn(20), fill=(90, 90, 90), anchor='mm')
im.save(out); print('wrote', out)
