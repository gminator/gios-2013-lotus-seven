import sys, os, struct, colorsys
sys.path.insert(0, os.path.dirname(__file__))
from kn5 import parse
from PIL import Image, ImageDraw
b,ver,T,M,X=parse(sys.argv[1]); out=sys.argv[2]; mats=sys.argv[3].split(',')
S=1024
im=Image.new('RGB',(S,S),(0,0,0)); d=ImageDraw.Draw(im)
names=[x for x in X if M[x['mat']]['name'] in mats and not x.get('skinned')]
legend=[]
for k,x in enumerate(names):
    col=tuple(int(c*255) for c in colorsys.hsv_to_rgb((k*0.618)%1,0.8,1.0))
    uv=[struct.unpack_from('<2f',b,x['voff']+i*44+24) for i in range(x['nv'])]
    idx=struct.unpack_from(f"<{x['ni']}H",b,x['ioff'])
    for t in range(0,x['ni'],3):
        pts=[(uv[idx[t+j]][0]*S, -uv[idx[t+j]][1]*S) for j in range(3)]
        d.polygon(pts, fill=col, outline=col)
    legend.append((x['name'],col,x['nv']))
im.save(out)
for n,c,nv in legend: print(f"{n:35s} rgb{c} nv={nv}")
