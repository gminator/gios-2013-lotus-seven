# Ghost Seven

The ghost of Giovann's Seven in Assetto Corsa: a 2013 Birkin S3 Lotus Seven replica, Ford Kent crossflow
1600 bored to 1700, twin side-draughts, 4-speed, live axle, right hand drive, British Racing Green with a
yellow nose. Built as a re-tune of Ben O'Bro and JackCY's **Caterham Super7 1700 Super Sprint RHD** mod
(v1.52, physics 2.9) from RaceDepartment.

This repo holds only what was changed or added. The original mod's model, sounds and textures are not
redistributed here, as its authors ask. `build.py` assembles the full car from their 7z.

## Build

```
python3 build.py ~/Downloads/bo_caterham_1700-v1.52.7z
```

Needs Python 3 and `bsdtar` (on macOS by default). Output: `build/bo_birkin_s3_1700_kent/` and a zip you can
drag into Content Manager. It installs as its own car, `bo_birkin_s3_1700_kent`, and leaves the stock Caterham alone.

## What is different from the stock mod

| Area | Change |
|---|---|
| Gearbox | 4-speed, Ford Type E ratios 3.65 / 1.97 / 1.37 / 1.00, final 3.92, open diff |
| Engine | Low compression 1700 Kent crossflow: about 105 bhp at 5,500 rpm, 155 Nm at 3,750, 6,500 limiter |
| Mass | 650 kg with driver |
| Rear suspension | Softer springs, less travel before the bump stops (the real car bottoms out) |
| Skin | `00_british_racing_green`: bare aluminium body, BRG wings and tub, yellow nose, black 7 grille, CAA 692 564 plates |
| Dash | White-faced VDO dials, speedo in km/h (the mod's was MPH), patched into the kn5; wooden dash via CSP `extension/ext_config.ini` |

Power and gearing are estimates calibrated against the Killarney track day of 14 October 2026 (Garmin GPS:
best lap 1:58.3, 146 km/h, 80 to 130 km/h in about 9 s). A dyno sheet or the real gearbox and diff ratios would
pin them down. Physics ships in a plain `data/` folder, no `data.acd`, so it can be tweaked in place.

## Layout

- `overlay/data/`: the 7 physics files that changed (engine, power curve, drivetrain, car, suspension, setup, AI)
- `overlay/ui/ui_car.json`: name, description, specs and curves
- `overlay/skins/00_british_racing_green/`: the livery
- `overlay/extension/`: wood and flat-normal textures plus the CSP section appended to the mod's `ext_config.ini`
- `overlay/kn5_textures/dashboard.dds`: the redrawn dial atlas, patched into the model by the build
- `tools/`: kn5 parser, texture extract and patch, UV mapper, `data.acd` unpacker, engine curve model, dial redraw

Tools that draw or convert textures need `pip install pillow numpy`; the build itself does not.

## Credits

Model, textures, sound: Ben O'Bro. Physics research: JackCY (Jaroslav Černý). Thank you both; please support
them on RaceDepartment. The re-tune, livery and dash are Giovann Adonis's, for his own car.
