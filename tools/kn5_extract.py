import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from kn5 import parse
from PIL import Image
b,ver,T,M,X=parse(sys.argv[1]); out=sys.argv[2]
want=sys.argv[3].split(',')
for t in T:
    if t['name'] in want:
        p=os.path.join(out,t['name']); open(p,'wb').write(b[t['offset']:t['offset']+t['size']])
        try:
            im=Image.open(p); print(t['name'], im.size, im.mode, getattr(im,'pixel_format',''))
            im.convert('RGBA').resize((min(im.size[0],1024),min(im.size[1],1024))).save(p+'.png')
        except Exception as e: print(t['name'],'ERR',e)
