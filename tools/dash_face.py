import math, sys
from PIL import Image, ImageDraw, ImageFont
src=Image.open('kn5tex/dashboard.dds.png').convert('RGBA'); W,H=src.size; px=src.load()
CREAM=(240,236,224,255); INK=(20,20,22,255)
def fit_circle(pts):
    # algebraic least squares circle fit
    n=len(pts); sx=sum(p[0] for p in pts); sy=sum(p[1] for p in pts)
    sxx=sum(p[0]**2 for p in pts); syy=sum(p[1]**2 for p in pts); sxy=sum(p[0]*p[1] for p in pts)
    sxxx=sum(p[0]**3 for p in pts); syyy=sum(p[1]**3 for p in pts); sxyy=sum(p[0]*p[1]**2 for p in pts); sxxy=sum(p[0]**2*p[1] for p in pts)
    A=[[sxx,sxy,sx],[sxy,syy,sy],[sx,sy,n]]; B=[-(sxxx+sxyy),-(sxxy+syyy),-(sxx+syy)]
    import numpy as np
    a,b,c=np.linalg.solve(np.array(A),np.array(B))
    cx,cy=-a/2,-b/2; r=math.sqrt(cx*cx+cy*cy-c); return cx,cy,r
# speedo: yellow km/h labels
yel=[(x,y) for y in range(60,580) for x in range(530,1024) if (lambda p: p[0]>170 and p[1]>140 and p[2]<110 and p[0]-p[2]>80)(px[x,y])]
cx,cy,rlab=fit_circle(yel); print(f"speedo centre ({cx:.1f},{cy:.1f}) label radius {rlab:.1f}, {len(yel)} yellow px")
# angles of label clusters (compass: 0 = up, clockwise)
def comp(x,y): return (math.degrees(math.atan2(x-cx, -(y-cy))))%360
bins=[0]*360
for x,y in yel: bins[int(comp(x,y))]+=1
groups=[]; cur=[]
for a in list(range(360))+[None]:
    if a is not None and bins[a]>0: cur.append(a)
    else:
        if cur: groups.append(cur); cur=[]
if groups and groups[0][0]==0 and groups[-1][-1]==359: groups[0]=groups[-1]+[g+360 for g in groups[0]]; groups.pop()
means=sorted((sum(bins[g%360]*g for g in grp)/sum(bins[g%360] for g in grp))%360 for grp in groups)
print("label clusters (compass deg):",[round(m) for m in means])
# labels run 20..240 clockwise starting after the gap (rest peg at lower left). Find the gap: biggest angular jump
ms=means[:]; jumps=[((ms[(i+1)%len(ms)]-ms[i])%360,i) for i in range(len(ms))]; gap=max(jumps)[1]
order=ms[gap+1:]+ms[:gap+1]
vals=[20*(i+1) for i in range(len(order))]
th0=sum(((o-1.2*v)%360) for o,v in zip(order,vals))/len(order)
print("fit theta0 (compass angle of 0 km/h):",round(th0,1),"residuals:",[round(((o-1.2*v)%360)-th0,1) for o,v in zip(order,vals)])
json_out=dict(cx=cx,cy=cy,rlab=rlab,th0=th0)
import json; json.dump(json_out,open('skinwork/speedo_geom.json','w'))
# check image: draw my km/h tick positions on the original
chk=src.copy(); d=ImageDraw.Draw(chk)
for v in range(0,250,10):
    t=math.radians(th0+1.2*v); r0=rlab+25; r1=rlab+45 if v%20==0 else rlab+35
    d.line([(cx+r0*math.sin(t),cy-r0*math.cos(t)),(cx+r1*math.sin(t),cy-r1*math.cos(t))],fill=(255,0,0,255),width=3)
d.ellipse([cx-4,cy-4,cx+4,cy+4],fill=(255,0,0,255))
chk.crop((520,50,1024,600)).save('skinwork/speedo_check.png')
