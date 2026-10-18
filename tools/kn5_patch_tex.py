"""Replace embedded textures in a kn5: python3 kn5_patch_tex.py in.kn5 out.kn5 name=file ...
kn5 has no offset table, so the texture block is rebuilt and the rest of the file is copied."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kn5 import parse

def patch(src, dst, repl):
    b, ver, T, M, X = parse(src)
    first = T[0]['offset'] - 4 - len(T[0]['name']) - 4 - 4      # back over size, name, name length, active flag
    last_end = T[-1]['offset'] + T[-1]['size']
    out = bytearray(b[:first])
    for t in T:
        data = b[t['offset']:t['offset'] + t['size']]
        if t['name'] in repl:
            data = open(repl[t['name']], 'rb').read()
            print(f"replaced {t['name']}: {t['size']} -> {len(data)} B")
        nm = t['name'].encode('latin-1')
        out += struct.pack('<I', t['active']) + struct.pack('<I', len(nm)) + nm + struct.pack('<I', len(data)) + data
    out += b[last_end:]
    open(dst, 'wb').write(out)
    b2, ver2, T2, M2, X2 = parse(dst)
    assert len(T2) == len(T) and len(M2) == len(M) and len(X2) == len(X), 're-parse mismatch'
    print('ok', dst, len(out), 'bytes; meshes', len(X2))

if __name__ == '__main__':
    patch(sys.argv[1], sys.argv[2], dict(p.split('=', 1) for p in sys.argv[3:]))
