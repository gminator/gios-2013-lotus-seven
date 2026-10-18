# Gio's 2013 Lotus Seven

![The car on the gravel at the top of the pass](photos/hero-gravel.jpg)

A 2013 Birkin S3 Lotus Seven replica, British Racing Green with a yellow nose: Ford Kent crossflow, 711M block bored from 1600 to
1700, gas-flowed head, performance cam, low compression pistons, twin side-draught carbs, wrapped manifolds, 4-speed, live axle, right hand drive,
plated G-SEVEN in the sim. This repo is its twin for Assetto Corsa, built as a re-tune of Ben O'Bro and
JackCY's **Caterham Super7 1700 Super Sprint RHD** mod (v1.52, physics 2.9) from RaceDepartment.

The source tree holds only what was changed or added; `build.py` assembles the full car from the original mod's 7z,
and the releases carry the built zip.

| | |
|---|---|
| ![Chapman's Peak](photos/chapmans-peak.jpg) | ![Sea Point at sunset](photos/cockpit-sea-point.jpg) |

## Download

The built car is attached to the [latest release](https://github.com/gminator/gios-2013-lotus-seven/releases/latest):
download `bo_birkin_s3_1700_kent.zip` and drag it into Content Manager. It installs as its own car and leaves the
stock Caterham alone. That zip contains the base mod's model, sounds and textures by Ben O'Bro and JackCY.

## Build it yourself

```
python3 build.py ~/Downloads/bo_caterham_1700-v1.52.7z
```

Python 3 with numpy, and `bsdtar` (on macOS by default). Output: `build/bo_birkin_s3_1700_kent/` and a zip to drag into Content
Manager.

## What is different from the stock mod

| Area | Change |
|---|---|
| Gearbox | 4-speed, 3.65 / 1.60 / 1.40 / 1.10, final 3.92, open diff (18 Oct 2026, after driving it: 2nd lengthened so it holds through the kink; 3rd went 1.37, 1.30, then a shorter 1.40 because it ran too long down the start straight; 4th shortened from 1.00 to 1.10 because the shift to 4th felt wrong, the revs fell away. His 2nd to 3rd felt realistic) |
| Engine | 711M 1700 Kent, gas-flowed head, performance cam, low compression: about 64 bhp (48 kW) at 5,500 rpm, 95 Nm at 4,250, 6,800 limiter (v7: a peaky cammed Kent, weak below 3,500 rpm, fading fast past 5,500) |
| Mass | 650 kg with driver |
| Rear suspension | Softer springs, less travel before the bump stops (the real car bottoms out) |
| Skin | `00_british_racing_green`: BRG with an aluminium bonnet, yellow grille lip, black 7 grille, silver rims, two side vents on the exhaust side, Union Jack and G. ADONIS on the sides, G-SEVEN plates |
| Exhaust | Remodelled to his: wrapped elbow out of the side panel, long silencer in an expanded-metal guard with three bands, bare tailpipe bending down ahead of the rear wheel (`tools/exhaust_geom.py`, written into the kn5 by the build) |
| Seats and badges | The Caterham seat patch, belt label and Super 7 roundel in the mod's `tex_misc.dds` replaced with LOTUS 7 items in orange stitching |
| Dash and trim | White-faced VDO dials, speedo in km/h (the mod's was MPH), patched into the kn5; wooden dash, flat body-colour rear deck (the canvas tonneau and its press studs removed) with a wooden luggage rack on chrome rails (`tools/rack_geom.py`), polished screen frame and black headlight housings, all as materials and meshes written into the kn5 |

## The engine, so far an estimate

![Estimated dyno](dyno/estimate-2026-10-18-v7.png)

Nobody has put this engine on a dyno yet. The solid curve is the v7 guess, shaped from Giovann's notes on driving the sim
against the real car: the real engine labors in 3rd, picks up speed out of corners more slowly, runs out of breath early (the
sim let him hold 3rd to the end of the start straight, the real car wants 4th well before the line) and scrubs speed fast. It is
a cammed 711M 1700 crossflow with a gas-flowed head and low compression pistons: about 64 bhp (48 kW) at 5,500 rpm and 95 Nm at
4,250, weak below 3,500 rpm and falling away quickly past 5,500. He said he would be shocked to see 60 kW from it and that it could
still be dejuiced another 5 to 10 percent, so v7 is v6 x 0.92 (about 41 kW at the wheels). Drag already matched a Seven (about 0.87 m2,
0.22 g on a lift at speed), so only the engine and the 3rd ratio changed. Earlier versions: v2 (114 bhp) drove far too strong (169 km/h
on the back straight, laps of 1:46 against 131 to 146 km/h and 1:58.6 at Killarney); v3 (91 bhp) and v4 (82 bhp) were flat trims of it,
v5 (78 bhp) the first peaky shape and v6 (70 bhp) a further scale. The Garmin trace implies more pull than v7 gives at 100 to 130 km/h,
so the sim is now much slower than the best real runs there; his feel of the real car outranks the trace. The dashed lines are v6 and v2. The real car gets dyno'd over the coming months; each run goes into `dyno/` and
the curve, limiter and gearing get updated from it. What would also tighten the physics: the real gearbox and diff
ratios, the tyre size, and the compression ratio.

## Track days

- [Killarney, 14 October 2026](trackday/2026-10-14/): first track day, 16 flying laps, best 1:58.6, 146 km/h. Speed heat map, racing lines, lap times and the best-lap trace from the Garmin.

![Killarney heat map](trackday/2026-10-14/heatmap.png)

![Lap times](trackday/2026-10-14/laptimes.png)

## Sim sessions

- [Killarney in the twin, 18 October 2026](trackday/sim-2026-10-18/driving-report.pdf): a one-page report each on downshifts, coasting, steering and gear use, from the recorded telemetry (`tools/sim_report.py`).

## Layout

- `overlay/data/`: the 7 physics files that changed (engine, power curve, drivetrain, car, suspension, setup, AI)
- `overlay/ui/ui_car.json`: name, description, specs and curves
- `overlay/skins/00_british_racing_green/`: the livery
- `overlay/extension/`: wood and flat-normal textures plus the CSP section appended to the mod's `ext_config.ini`
- `overlay/kn5_textures/`: the redrawn dial atlas, exhaust, seat and rack textures, patched into the model by the build
- `dyno/`: engine curves, estimated now, measured later
- `photos/`: the real car
- `tools/`: kn5 parser and rewriter (textures, materials, meshes), texture extract, UV mapper, `data.acd` unpacker, engine curve model, dial redraw, livery painter, exhaust and rack geometry, seat stitching, Blender check renders, track-day charts.
  Those that draw or convert textures need `pip install pillow numpy`; the build itself does not.

## kn5 conventions learned the hard way

- Texture coordinates: the game reads `image_y = 1 + v` (v is stored negative), so row 0 of a texture needs `v = row - 1`.
- Winding: triangles are counter-clockwise about the outward normal; the game culls back faces, so the wrong way round looks see-through.
- Axes in the model: +x is the car's left, +y up, +z forward; node matrices are row-vector (`P = [p, 1] @ M`, translation in the last row).
- In the body texture the top side-panel island is the left side (exhaust), the bottom one the right side; lettering on the top island is laid out rotated 180 degrees.
- Blender's OBJ import counts v from the bottom and its camera is right-handed, so a Blender check render is the game's view flipped; use the web viewer (`tools/kn5_to_obj_full.py` + `tools/blender_glb.py`) instead.

## Credits

Model, textures, sound: Ben O'Bro. Physics research: JackCY (Jaroslav Černý). Thank you both; please support them on
RaceDepartment. The re-tune, livery and dash are Giovann Adonis's, for his own car.

`tools/blender_sprites.py` renders the built car (exported with `tools/kn5_to_obj_full.py`) from a fixed three-quarter top camera at 72 headings on a transparent background, for dashboards and maps: `blender --background --python tools/blender_sprites.py -- car.obj out_dir 72 256 58`.
