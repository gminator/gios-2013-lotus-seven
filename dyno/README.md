# Dyno

`estimate-2026-10-18` is the starting guess, not a measurement: a low compression 1700 Kent crossflow on twin
side-draughts, about 105 bhp at 5,500 rpm and 155 Nm at 3,750 at the crank, 6,500 rpm limiter. It was sized so the
sim does 80 to 130 km/h in 8 to 10 s like the Garmin trace from Killarney on 14 October 2026.

## When the car has been on a dyno

1. Save the run here as `run-YYYY-MM-DD.csv` with columns `rpm,torque_nm,power_bhp` and note in this file whether
   the figures are at the wheels or at the crank, the gear used, and the weather.
2. Put the measured crank torque per 250 rpm into the `crank` table in `tools/engine_model.py` (if the dyno gave
   wheel figures, divide by 0.87 first; the sim applies that loss itself).
3. Run `python3 tools/engine_model.py <built car folder>` to write `power.lut` and the UI curves, copy
   `data/power.lut` and `ui/ui_car.json` into `overlay/`, set the limiter in `overlay/data/engine.ini`, rebuild.
4. Add the new chart next to the old one so the guesses and the measurements sit side by side.
