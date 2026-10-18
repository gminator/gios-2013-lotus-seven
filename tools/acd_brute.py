import sys, os, struct
acd, outdir = sys.argv[1], sys.argv[2]
data=open(acd,'rb').read()
pos=8 if struct.unpack_from('<i',data,0)[0] < 0 else 0
files=[]
while pos < len(data):
    n=struct.unpack_from('<I',data,pos)[0]; pos+=4
    name=data[pos:pos+n].decode('latin-1'); pos+=n
    size=struct.unpack_from('<I',data,pos)[0]; pos+=4
    raw=bytes(data[pos+i*4] for i in range(size)); pos+=size*4
    files.append((name,raw))
# brute force key string (ASCII digits and '-') of length L
ok=set(range(0x20,0x7f))|{9,10,13}
best=None
for L in range(15,32):
    key=[]
    good=True
    for j in range(L):
        cands=[]
        for k in list(range(48,58))+[45]:
            if all(((b-k)&0xff) in ok for name,raw in files if name.endswith(('.ini','.lut')) for b in raw[j::L][:400]):
                cands.append(k)
        if len(cands)!=1: good=False; break
        key.append(cands[0])
    if good:
        best=bytes(key); break
if not best: print("no key found"); sys.exit(1)
print("key", best.decode(), "len", len(best))
os.makedirs(outdir,exist_ok=True)
for name,raw in files:
    out=bytes((raw[i]-best[i%len(best)])&0xff for i in range(len(raw)))
    open(os.path.join(outdir,name),'wb').write(out)
print("unpacked", len(files), "files")
