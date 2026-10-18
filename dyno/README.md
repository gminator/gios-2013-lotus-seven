# Dyno

`estimate-2026-10-18` was the first guess (105 bhp at 5,500, 155 Nm at 3,750, 6,500 limiter). `estimate-2026-10-18-v2`
is v2: the 711M block, gas-flowed head and performance cam, about 114 bhp at 5,750 rpm and 156 Nm at 4,250 at the crank, 6,800 rpm
limiter. It drove far too strong. `estimate-2026-10-18-v3` and `-v4` are v2 trimmed 20 and 28 percent (91 and 82 bhp). `-v5` is the first peaky cammed Kent (78 bhp), `-v6` is v5 scaled
by 0.90 (70 bhp). `estimate-2026-10-18-v7` is the current one: v6 scaled by another 0.92, about 64 bhp (48 kW) at 5,500 rpm and 95 Nm at 4,250,
weak below 3,500 rpm and falling away past 5,500, shaped from Giovann's notes on the real car. `stock-caterham-1700ss-mod` is the mod's own
curve. None of these is a measurement. The model puts v7 at about 18 s for 80 to 130 km/h, much slower than the real Garmin runs from Killarney on
14 October 2026 (9.4 to 11.8 s); his feel of the real car outranks the trace.

## When the car has been on a dyno

1. Save the run here as `run-YYYY-MM-DD.csv` with columns `rpm,torque_nm,power_bhp` and note in this file whether
   the figures are at the wheels or at the crank, the gear used, and the weather.
2. Put the measured crank torque per 250 rpm into the `crank` table in `tools/engine_model.py` (if the dyno gave
   wheel figures, divide by 0.87 first; the sim applies that loss itself).
3. Run `python3 tools/engine_model.py <built car folder>` to write `power.lut` and the UI curves, copy
   `data/power.lut` and `ui/ui_car.json` into `overlay/`, set the limiter in `overlay/data/engine.ini`, rebuild.
4. Add the new chart next to the old one so the guesses and the measurements sit side by side.
