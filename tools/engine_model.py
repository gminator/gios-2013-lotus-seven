"""v7, 18 Oct 2026 (night): the v6 curve scaled by another 0.92 and a shorter 3rd (1.40), see crank below. v2: 711M block, gas-flowed head, performance cam, low compression pistons, twin side-draughts.
Generate power.lut (wheel torque, 13% loss like the original) + ui curves for the Birkin Kent 1700,
and sanity-check acceleration against the stock Caterham, calibrated on the sim telemetry."""
import json, math, sys
car=sys.argv[1]
# crank torque curve (Nm) for a low-compression 1700 Kent crossflow on twin 40 DCOEs, ~105 bhp @ 5500
crank={1000:104,1250:114,1500:123,1750:130,2000:136,2250:140,2500:143,2750:145,3000:147,3250:149,3500:151,3750:153,4000:155,4250:156,4500:156,4750:155,5000:153,5250:150,5500:146,5750:141,6000:134,6250:126,6500:116,6750:104,7000:90}
# v7: he said it could still be dejuiced another 5 to 10 percent and that 3rd was still too long on the start straight, so v7 is
# v6 x 0.92 (about 64 bhp, 48 kW at the crank) with 3rd shortened from 1.30 to 1.40 so it tops out near 130 km/h at 6,500 rpm (about 110 km/h at 5,500).
# v6: he said he would be shocked to see 60 kW from this car, and v5 peaked at 58 kW at the crank, so v6 is v5 x 0.90: about
# 52 kW (70 bhp) at the crank, about 45 kW at the wheels.
# v5: his notes after driving v4: the real car labors in 3rd (weak below about 3,500 rpm), picks up speed out of corners
# slower, runs out of breath early (he holds 3rd to the end of the start straight in the sim, the real car wants 4th long
# before the line) and scrubs speed fast. Drag already matches a Seven (about 0.87 m2 CdA, 0.22 g on a lift at speed), so only the
# engine changes: a cammed Kent that is peaky, about 64 bhp at 5,500 rpm, 95 Nm at 4,250, falling away fast past 5,500.
crank = {1000:50,1250:54,1500:59,1750:63,2000:67,2250:71,2500:76,2750:81,3000:86,3250:87,3500:90,3750:92,4000:94,4250:95,4500:95,4750:93,5000:90,5250:87,5500:84,5750:79,6000:72,6250:64,6500:55,6750:46,7000:38}
LOSS=0.87
lut=[(0,0),(250,0),(500,0),(750,0)]+[(r,round(t*LOSS,1)) for r,t in sorted(crank.items())]+[(r,0) for r in range(7250,10001,250)]
open(f'{car}/data/power.lut','w').write('\n'.join(f'{r}|{t}' for r,t in lut)+'\n')
hp=lambda r,t: t*r*2*math.pi/60/745.7
pk=max(crank.items(), key=lambda kv: hp(*kv)); tq=max(crank.items(), key=lambda kv: kv[1])
print(f"crank: {hp(*pk):.0f} bhp @ {pk[0]} rpm, {tq[1]} Nm @ {tq[0]} rpm; wheel peak {max(t for r,t in lut)} Nm")
ui=json.load(open(f'{car}/ui/ui_car.json'))
ui.update({
 "name":"Birkin S3 1700 Kent (Giovann)","brand":"Birkin","class":"street","country":"South Africa","year":2013,"version":"1.52-giovann",
 "author":"Ben O'Bro & JackCY (mod); Birkin re-tune for Giovann Adonis",
 "description":"A 2013 Birkin S3 Lotus Seven replica, British Racing Green, as it stands in October 2026: Ford Kent crossflow 1600 bored to 1700, low compression pistons, twin side-draught carbs, wrapped exhaust manifolds, 4-speed Ford gearbox, live axle, open differential, right hand drive.<br><br>Re-tuned from the Caterham 1700 Super Sprint RHD mod. Engine: Ford 711M block bored to 1700, gas-flowed head, performance cam, low compression pistons, twin side-draughts. Assumptions (no dyno sheet yet): about 70 bhp (52 kW) at 5,400 rpm and 103 Nm at 4,250 rpm at the crank, a peaky cammed Kent that labors below 3,500 rpm and falls away fast past 5,500, 6,800 rpm limiter, gear ratios 3.65 / 1.60 / 1.40 / 1.00 with the 3.92 final drive, 650 kg with driver, rear springs softened with less bump travel because the real car bottoms out at the rear at Killarney. Model, sound, tyres and brakes are the original mod's.<br><br>Real car reference: Killarney 14 Oct 2026, best lap 1:58.3, top speed 146 km/h on a 140 limit, 80 to 130 km/h in about 9 s.",
 "specs":{"bhp":"64bhp/5500rpm","torque":"95Nm/4250rpm","weight":"650 kg","topspeed":"141km/h","acceleration":"13.6s 0-100km/h","pwratio":"10.2 kg/hp"},
 "tags":["rwd","street","lightweight","trackday","manual","South Africa","birkin","kent","rhd","4speed"],
 "powerCurve":[[float(r),round(hp(r,t),1)] for r,t in sorted(crank.items())],
 "torqueCurve":[[float(r),float(t)] for r,t in sorted(crank.items())]})
json.dump(ui,open(f'{car}/ui/ui_car.json','w'),indent=2,ensure_ascii=False)
import os
if os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','dyno')):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','dyno','estimate-2026-10-18-v7.csv'),'w') as f:
        f.write('rpm,torque_nm_crank,power_bhp_crank\n')
        for r,t in sorted(crank.items()): f.write(f'{r},{t},{hp(r,t):.1f}\n')
# ---- longitudinal sanity model, calibrated so the STOCK car reproduces the sim telemetry (1.44 m/s2 @110 in 4th, 2.33 @100 in 3rd)
R=0.292; rho=1.2; CdA=0.868
stock={r:t for r,t in [tuple(map(float,l.split('|'))) for l in open(f'{car}/../../mod/bo_caterham_s7_1700_ss_rhd/data1.35/power.lut')]}
def interp(c,r):
    ks=sorted(c); 
    if r<=ks[0]: return c[ks[0]]
    for a,b in zip(ks,ks[1:]):
        if a<=r<=b: return c[a]+(c[b]-c[a])*(r-a)/(b-a)
    return 0
def accel(curve,mass,ratio,v,k):
    rpm=max(950, v/(2*math.pi*R)*60*ratio)
    F=interp(curve,rpm)*ratio/R
    return k*(F-0.5*rho*CdA*v*v-150)/mass
# calibrate k on stock car
k=1.0
for _ in range(50):
    a1=accel(stock,615+60,3.916667*1.0,110/3.6,k); a2=accel(stock,615+60,3.916667*1.258065,100/3.6,k)
    k*= (1.44/a1+2.33/a2)/2
print(f"calibration factor {k:.2f} (model vs sim)")
new={r:t for r,t in lut}
def t80_130(curve,mass,ratios,shift_rpm):
    v=80/3.6; t=0; g=0
    # pick lowest gear that keeps rpm under shift_rpm at 80
    while v/(2*math.pi*R)*60*ratios[g]>shift_rpm: g+=1
    while v<130/3.6:
        rpm=v/(2*math.pi*R)*60*ratios[g]
        if rpm>shift_rpm and g<len(ratios)-1: g+=1; t+=0.3; continue
        a=accel(curve,mass,ratios[g],v,k); v+=a*0.05; t+=0.05
    return t
fd=3.916667
print(f"stock Caterham 80-130: 3rd only {t80_130(stock,675,[1.258065*fd],9000):.1f}s, 4th only {t80_130(stock,675,[fd],9000):.1f}s")
rat=[3.65*fd,1.60*fd,1.40*fd,fd]
print(f"Birkin model 80-130: best shift {min((round(t80_130(new,710,rat,sh),1),sh) for sh in (5200,5500,5800,6200,6500))} (s, rpm)  shifting at 6200 {t80_130(new,710,rat,6500):.1f}s, 4th only {t80_130(new,710,[fd],9000):.1f}s   (real Garmin best 9.0s, typical 10-12s)")
# top speed in 4th
v=30
while accel(new,710,fd,v,k)>0 and v<80: v+=0.1
print(f"Birkin model top speed ~{v*3.6:.0f} km/h at {v/(2*math.pi*R)*60*fd:.0f} rpm; gear speeds at 6500: "+", ".join(f"{6500/60*2*math.pi*R/r*3.6:.0f}" for r in rat))
# 0-100
v=0.5; t=0; g=0
while v<100/3.6 and t<30:
    rpm=v/(2*math.pi*R)*60*rat[g]
    if rpm>6200 and g<3: g+=1; t+=0.3; continue
    a=min(accel(new,710,rat[g],v,k),7.0); v+=a*0.05; t+=0.05
print(f"Birkin model 0-100 ~{t:.1f}s")
