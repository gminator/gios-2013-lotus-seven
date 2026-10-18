import struct, sys, os, json
class R:
    def __init__(s,b): s.b=b; s.p=0
    def i(s): v=struct.unpack_from('<i',s.b,s.p)[0]; s.p+=4; return v
    def u16(s): v=struct.unpack_from('<H',s.b,s.p)[0]; s.p+=2; return v
    def f(s): v=struct.unpack_from('<f',s.b,s.p)[0]; s.p+=4; return v
    def by(s): v=s.b[s.p]; s.p+=1; return v
    def s(s): n=s.i(); v=s.b[s.p:s.p+n].decode('latin-1'); s.p+=n; return v
    def raw(s,n): v=s.b[s.p:s.p+n]; s.p+=n; return v
def parse(path):
    b=open(path,'rb').read(); r=R(b)
    assert r.raw(6)==b'sc6969'
    ver=r.i()
    if ver>5: r.i()
    textures=[]
    for _ in range(r.i()):
        active=r.i(); name=r.s(); n=r.i(); off=r.p; data=r.raw(n)
        textures.append(dict(name=name,active=active,offset=off,size=n))
    materials=[]
    for _ in range(r.i()):
        m=dict(name=r.s(),shader=r.s(),blend=r.by(),atest=r.by(),depth=r.i(),props={},tex={})
        for _ in range(r.i()):
            pn=r.s(); val=r.f(); r.raw(8+12+16); m['props'][pn]=val
        for _ in range(r.i()):
            tn=r.s(); slot=r.i(); texname=r.s(); m['tex'][tn]=texname
        materials.append(m)
    meshes=[]
    def node(depth, parent):
        t=r.i(); name=r.s(); nch=r.i(); act=r.by()
        if t==1:
            r.raw(64)
        elif t==2:
            r.by(); r.by(); r.by()
            nv=r.i(); voff=r.p; r.raw(nv*44)
            ni=r.i(); ioff=r.p; r.raw(ni*2)
            mat=r.i(); layer=r.i(); r.f(); r.f(); r.raw(16); r.by()
            meshes.append(dict(name=name,parent=parent,nv=nv,voff=voff,ni=ni,ioff=ioff,mat=mat))
        elif t==3:
            r.by(); r.by(); r.by()
            for _ in range(r.i()): r.s(); r.raw(64)
            nv=r.i(); voff=r.p; r.raw(nv*76)
            ni=r.i(); ioff=r.p; r.raw(ni*2)
            mat=r.i(); layer=r.i(); r.f(); r.f()
            meshes.append(dict(name=name,parent=parent,nv=nv,voff=voff,ni=ni,ioff=ioff,mat=mat,skinned=True))
        for _ in range(nch): node(depth+1,name)
    node(0,None)
    return b,ver,textures,materials,meshes
if __name__=='__main__':
    b,ver,T,M,X=parse(sys.argv[1])
    print("version",ver,"textures",len(T),"materials",len(M),"meshes",len(X))
    for t in T: print(f"  TEX {t['name']:40s} {t['size']:>9d} B")
    for i,m in enumerate(M): print(f"  MAT {i:3d} {m['name']:30s} {m['shader']:28s} tex={m['tex']}")
    for x in X: print(f"  MESH {x['name']:40s} parent={x['parent']!s:30s} nv={x['nv']:6d} mat={M[x['mat']]['name']}")
