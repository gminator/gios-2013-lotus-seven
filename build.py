#!/usr/bin/env python3
"""Assemble the Ghost Seven car for Assetto Corsa from the original Caterham 1700 Super Sprint mod.

    python3 build.py ~/Downloads/bo_caterham_1700-v1.52.7z [out_dir]

Needs bsdtar (macOS/Linux) to unpack the 7z, and Pillow is NOT needed: textures ship pre-built in overlay/.
Produces out_dir/bo_birkin_s3_1700_kent/ and out_dir/bo_birkin_s3_1700_kent.zip.
"""
import os, shutil, subprocess, sys, tempfile, json
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = 'bo_caterham_s7_1700_ss_rhd'
CAR = 'bo_birkin_s3_1700_kent'

def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    archive = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'build'))
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='ghost7_')
    subprocess.run(['bsdtar', '-xf', archive, '-C', tmp], check=True)
    src = os.path.join(tmp, SRC)
    if not os.path.isdir(src):
        sys.exit(f'{SRC} not found in {archive}')
    dst = os.path.join(out, CAR)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    os.chdir(dst)
    # unpacked physics folder replaces the packed one
    for f in ['data.acd', 'donate.url', os.path.join('data1.35', 'respect copyright, donate.url')]:
        if os.path.exists(f): os.remove(f)
    os.rename('data1.35', 'data')
    # rename model, sound bank and every reference to the old folder name
    for f in os.listdir('.'):
        if f.startswith(SRC) and f.endswith('.kn5'):
            os.rename(f, f.replace(SRC, CAR))
    os.rename(os.path.join('sfx', SRC + '.bank'), os.path.join('sfx', CAR + '.bank'))
    for f in [os.path.join('sfx', 'GUIDs.txt'), os.path.join('data', 'lods.ini'), os.path.join('ui', 'cm_paintshop.json')]:
        raw = open(f, 'rb').read().replace(SRC.encode(), CAR.encode())
        open(f, 'wb').write(raw)
    # overlay: physics, ui, skin, extension textures
    ov = os.path.join(HERE, 'overlay')
    for root, _, files in os.walk(ov):
        rel = os.path.relpath(root, ov)
        if rel.split(os.sep)[0] in ('kn5_textures',) or rel == '.':
            continue
        os.makedirs(rel, exist_ok=True)
        for f in files:
            if f in ('ext_config_append.ini',):
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(rel, f))
    with open(os.path.join('extension', 'ext_config.ini'), 'a', newline='') as fh:
        fh.write('\r\n\r\n' + open(os.path.join(ov, 'extension', 'ext_config_append.ini')).read().replace('\n', '\r\n'))
    with open('readme.txt', 'a') as fh:
        fh.write('\n\n' + open(os.path.join(ov, 'readme_append.txt')).read())
    # dash dials (white faces, km/h) patched into the main model
    sys.path.insert(0, os.path.join(HERE, 'tools'))
    import kn5_patch_tex  # noqa: runs on import with argv, so call its function instead
    kn5_patch_tex.patch(CAR + '.kn5', CAR + '.kn5', {'dashboard.dds': os.path.join(ov, 'kn5_textures', 'dashboard.dds')})
    os.chdir(out)
    zp = os.path.join(out, CAR + '.zip')
    if os.path.exists(zp): os.remove(zp)
    subprocess.run(['bsdtar', '-a', '-cf', zp, CAR], check=True)
    shutil.rmtree(tmp)
    print('built', dst)
    print('zip  ', zp, os.path.getsize(zp) // 1024 // 1024, 'MB')

if __name__ == '__main__':
    main()
