import math, json
from PIL import Image, ImageDraw, ImageFont
import numpy as np
src=Image.open('kn5tex/dashboard.dds.png').convert('RGBA')
CREAM=(240,236,224,255); INK=(22,22,24,255)
FB='/System/Library/Fonts/Supplemental/Arial Bold.ttf'; FN='/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf'
def fit_circle(pts):
    pts=np.array(pts,dtype=float); x,y=pts[:,0],pts[:,1]
    A=np.c_[x,y,np.ones(len(x))]; b=-(x*x+y*y); a,bb,c=np.linalg.lstsq(A,b,rcond=None)[0]
    cx,cy=-a/2,-bb/2; return cx,cy,math.sqrt(cx*cx+cy*cy-c)
arr=np.array(src).astype(int)
def invert_face(img, cx, cy, r):
    a=np.array(img).astype(int); H,W=a.shape[:2]
    yy,xx=np.mgrid[0:H,0:W]; m=(xx-cx)**2+(yy-cy)**2<=r*r
    rgb=a[...,:3]; L=rgb.mean(axis=2); sat=rgb.max(axis=2)-rgb.min(axis=2)
    mono=m&(sat<45)
    t=np.clip(L/255.0,0,1)[...,None]           # 0 dark .. 1 light
    newc=np.array(INK[:3])*t+np.array(CREAM[:3])*(1-t)   # dark -> cream, light -> ink
    a[...,:3]=np.where(mono[...,None],newc,rgb)
    return Image.fromarray(a.astype(np.uint8))
# --- tacho: fit centre from white ticks
wh=[(x,y) for y in range(60,580) for x in range(10,520) if arr[y,x,0]>215 and arr[y,x,1]>215 and arr[y,x,2]>215]
tcx,tcy,tr=260,314,250
out=invert_face(src,tcx,tcy,tr)
# --- small gauges: invert each dial region (centres from bright pixels)
for (x0,x1) in [(0,340),(340,680),(680,1024)]:
    pts=[(x,y) for y in range(600,930) for x in range(x0,x1) if arr[y,x,:3].min()>200]
    cx,cy,r=fit_circle(pts); print(f"small gauge centre ({cx:.0f},{cy:.0f}) r {r:.0f}")
    out=invert_face(out,cx,cy,min(r+70,165))
# --- speedo: redraw in km/h
g=json.load(open('skinwork/speedo_geom.json')); cx,cy,rlab=g['cx'],g['cy'],g['rlab']; th0=205.0
R=238
d=ImageDraw.Draw(out)
d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=CREAM)
fnum=ImageFont.truetype(FB,36); fsm=ImageFont.truetype(FB,30); fvdo=ImageFont.truetype(FN,26)
for v in range(0,241,10):
    t=math.radians(th0+1.2*v)
    major=(v%20==0)
    r0=R-8; r1=R-(36 if major else 22)
    d.line([(cx+r0*math.sin(t),cy-r0*math.cos(t)),(cx+r1*math.sin(t),cy-r1*math.cos(t))],fill=INK,width=7 if major else 4)
    if major and v>=20:
        rn=185
        d.text((cx+rn*math.sin(t),cy-rn*math.cos(t)),str(v),font=fnum,fill=INK,anchor='mm')
d.text((cx,cy+145),"km/h",font=fsm,fill=INK,anchor='mm')
d.text((cx,cy+200),"VDO",font=fvdo,fill=INK,anchor='mm')
d.ellipse([cx-22,cy-22,cx+22,cy+22],fill=INK)
# needle colour swatch: white -> deep red so needles show on cream faces
d.rectangle([45,40,95,85],fill=(185,22,22,255))
# rest peg (black dot) just before 20
t=math.radians(th0+1.2*5); pr=R-60
d.ellipse([cx+pr*math.sin(t)-6,cy-pr*math.cos(t)-6,cx+pr*math.sin(t)+6,cy-pr*math.cos(t)+6],fill=INK)
# odometer windows copied from the original face
for box in [(650,203,890,252),(672,381,862,432)]:
    out.paste(src.crop(box),box[:2])
    d.rectangle(box,outline=INK,width=3)
out.save('skinwork/dashboard.png')
out.crop((0,40,1024,600)).save('skinwork/dash_check_top.png')
out.crop((0,580,1024,1024)).save('skinwork/dash_check_bottom.png')
print('dash atlas drawn')
