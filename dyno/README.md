# Dyno

`estimate-2026-10-18` was the first guess (105 bhp at 5,500, 155 Nm at 3,750, 6,500 limiter). `estimate-2026-10-18-v2`
is v2: the 711M block, gas-flowed head and performance cam, about 114 bhp at 5,750 rpm and 156 Nm at 4,250 at the crank, 6,800 rpm
limiter. It drove too strong, so `estimate-2026-10-18-v3` is the current one: v2 trimmed 20 percent, about 91 bhp at 5,750 rpm and
125 Nm at 4,250. `stock-caterham-1700ss-mod` is the mod's own curve. None of these is a measurement. v3 was sized so the
sim does 80 to 130 km/h in about 9 s like the Garmin trace from Killarney on 14 October 2026.

## When the car has been on a dyno

1. Save the run here as `run-YYYY-MM-DD.csv` with columns `rpm,torque_nm,power_bhp` and note in this file whether
   the figures are at the wheels or at the crank, the gear used, and the weather.
2. Put the measured crank torque per 250 rpm into the `crank` table in `tools/engine_model.py` (if the dyno gave
   wheel figures, divide by 0.87 first; the sim applies that loss itself).
3. Run `python3 tools/engine_model.py <built car folder>` to write `power.lut` and the UI curves, copy
   `data/power.lut` and `ui/ui_car.json` into `overlay/`, set the limiter in `overlay/data/engine.ini`, rebuild.
4. Add the new chart next to the old one so the guesses and the measurements sit side by side.
