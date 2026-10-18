#!/usr/bin/env python3
"""Assemble the Ghost Seven car for Assetto Corsa from the original Caterham 1700 Super Sprint mod.

    python3 build.py ~/Downloads/bo_caterham_1700-v1.52.7z [out_dir]

Needs bsdtar (macOS/Linux) to unpack the 7z and numpy (for the exhaust geometry); textures ship pre-built in overlay/.
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
    kn5_patch_tex.patch(CAR + '.kn5', CAR + '.kn5', {'dashboard.dds': os.path.join(ov, 'kn5_textures', 'dashboard.dds'),
                                                     'tex_misc.dds': os.path.join(ov, 'kn5_textures', 'tex_misc.dds'),
                                                     'body.dds': os.path.join(ov, 'kn5_textures', 'body.dds'),                   # the mod's painted exhaust port removed
                                                     'body_base_map.dds': os.path.join(ov, 'kn5_textures', 'body_base_map.dds')})  # and from its shading map          # SQP harness pads, Lotus 7 wheel badges
    # wooden dash, black headlamp housings, polished screen frame, deck, exhaust, rack: new materials and meshes written into the model
    from kn5_mod import Kn5Mod
    import numpy as np, exhaust_geom
    from kn5 import parse as _parse
    _b, _v, _T, _M, _X = _parse(CAR + '.kn5')
    k = Kn5Mod(CAR + '.kn5')
    ext = os.path.join(ov, 'extension')
    k.add_texture('gio_wood.dds', os.path.join(ext, 'dash_wood.dds'))
    k.add_texture('gio_black.dds', os.path.join(ext, 'black_matte.dds'))
    k.add_texture('gio_alu.dds', os.path.join(ext, 'alu_polished.dds'))
    k.add_texture('gio_brg.dds', os.path.join(ext, 'brg_paint.dds'))
    base = {'ksEmissive': 0, 'ksAlphaRef': 0}
    k.add_material('gio_wood', 'ksPerPixel', dict(ksAmbient=0.5, ksDiffuse=0.6, ksSpecular=0.3, ksSpecularEXP=40, **base), {'txDiffuse': 'gio_wood.dds'})
    k.add_material('gio_lamp_black', 'ksPerPixel', dict(ksAmbient=0.4, ksDiffuse=0.5, ksSpecular=0.5, ksSpecularEXP=30, **base), {'txDiffuse': 'gio_black.dds'})
    k.add_material('gio_alu_polished', 'ksPerPixelReflection', dict(ksAmbient=0.5, ksDiffuse=0.5, ksSpecular=1.2, ksSpecularEXP=60, fresnelC=0.3, fresnelEXP=2, fresnelMaxLevel=0.6, **base), {'txDiffuse': 'gio_alu.dds'})
    k.add_material('gio_brg_paint', 'ksPerPixelReflection', dict(ksAmbient=0.45, ksDiffuse=0.5, ksSpecular=0.5, ksSpecularEXP=120, fresnelC=0.3, fresnelEXP=3, fresnelMaxLevel=0.12, **base), {'txDiffuse': 'gio_brg.dds'})
    for m in ['dashboard_lp_SUB0', 'dashboard001_SUB0']: k.set_mesh_material(m, 'gio_wood')
    # the rear deck: a flat body-colour panel instead of the canvas tonneau, press studs hidden
    import rack_geom as _rg
    bc = [m for m in _X if m['name'] == 'boot_cover'][0]
    import struct as _st
    BV = np.array([_st.unpack_from('<11f', _b, bc['voff'] + i * 44) for i in range(bc['nv'])], dtype=np.float32)
    BI = np.frombuffer(_b, dtype='<u2', count=bc['ni'], offset=bc['ioff']).copy()
    Pw = np.c_[BV[:, :3], np.ones(len(BV))] @ bc['world']
    Pw[:, 1] = 0.645 + 0.25 * (Pw[:, 1] - 0.645)             # take the dome out of the tonneau: a near-flat deck on the tub's own outline
    BV[:, :3] = (Pw[:, :3] - bc['world'][3, :3]) @ np.linalg.inv(bc['world'][:3, :3])
    Nw = BV[:, 3:6] @ bc['world'][:3, :3]; tri = BI.reshape(-1, 3)
    keep = Nw[tri, 1].mean(axis=1) > 0.6                   # drop the cover's rolled edge (side-facing faces); keep the top surface
    BI = tri[keep].reshape(-1).astype(np.uint16)
    k.replace_mesh('boot_cover', BV, BI, material='gio_brg_paint')
    bp = [m for m in _X if m['name'] == 'button_press_boot'][0]
    k.replace_mesh('button_press_boot', np.zeros((3, 11), dtype=np.float32), np.array([0, 1, 2], dtype=np.uint16))
    for m in ['mainlight', 'mainlight01']: k.set_mesh_material(m, 'gio_lamp_black')
    k.set_mesh_material('parbrise_chassis_SUB0', 'gio_alu_polished')
    # his side exhaust: elbow out of the panel, long silencer in a mesh guard, tailpipe bending down ahead of the rear wheel
    ex = [m for m in _X if m['name'] == 'exhaust'][0]
    V, I = exhaust_geom.build(); V = exhaust_geom.to_local(V, ex['world'])
    k.add_texture('gio_exhaust.dds', os.path.join(ov, 'kn5_textures', 'gio_exhaust.dds'))
    k.add_material('gio_exhaust', 'ksPerPixel', dict(ksAmbient=0.45, ksDiffuse=0.55, ksSpecular=0.9, ksSpecularEXP=35, ksEmissive=0, ksAlphaRef=0), {'txDiffuse': 'gio_exhaust.dds'})
    k.replace_mesh('exhaust', V, I, material='gio_exhaust')
    # the mod's exhaust bracket node carries the wooden luggage rack instead
    import rack_geom
    att = [m for m in _X if m['name'] == 'exhaust_attach'][0]
    RV, RI = rack_geom.build(); RV = exhaust_geom.to_local(RV, att['world'])
    k.add_texture('gio_rack.dds', os.path.join(ov, 'kn5_textures', 'gio_rack.dds'))
    k.add_material('gio_rack', 'ksPerPixel', dict(ksAmbient=0.5, ksDiffuse=0.55, ksSpecular=0.6, ksSpecularEXP=40, ksEmissive=0, ksAlphaRef=0), {'txDiffuse': 'gio_rack.dds'})
    k.replace_mesh('exhaust_attach', RV, RI, material='gio_rack')
    # bonnet: bare polished aluminium, almost chrome. Own material with the skin's bonnet colour as diffuse and the mod's maps for shading
    k.add_texture('gio_body_skin.dds', os.path.join(ov, 'skins', '00_british_racing_green', 'body_metal_detail.dds'))
    k.add_material('gio_alu_bonnet', 'ksPerPixelMultiMap', dict(ksAmbient=0.45, ksDiffuse=0.35, ksSpecular=2.2, ksSpecularEXP=160, ksEmissive=0, ksAlphaRef=0,
                   fresnelC=0.75, fresnelEXP=1.5, fresnelMaxLevel=0.95, useDetail=0, detailUVMultiplier=1, sunSpecular=40, sunSpecularEXP=3000),
                   {'txDiffuse': 'gio_body_skin.dds', 'txNormal': 'empty_nrm.dds', 'txMaps': 'body_base_map.dds', 'txDetail': 'NULL.dds'})
    k.set_mesh_material('capot new', 'gio_alu_bonnet')
    # seats: LOTUS over 7 stitched on the seat backs (own texture patch per seat)
    import seats
    seats.apply(k, _b, _X, ov)
    # his harness has no cross pad: remove the mod's pad (the narrow label strip of tex_misc) from the belt meshes; the strap tags (big patch) stay
    k.hide_where('tex_misc', lambda x, y, z: 0.56 < y < 0.95 and abs(abs(x) - 0.265) < 0.11 and -1.0 < z < -0.5)   # harness cross pads and the pads behind the headrests live in the misc-badges mesh
    k.hide_where('belt_text', lambda x, y, z: z < -0.65)
    # side mirrors up to the top corners of the screen pillars, as on his car (the centre mirror is already on the top rail)
    for m in ['mirror_side', 'mirror_side_glass', 'mirror_side_handle_SUB0', 'mirror_side_handle_SUB1',
              'mirror_sideL', 'mirror_side_glassL', 'mirror_side_handleL_SUB0', 'mirror_side_handleL_SUB1']:
        k.translate_mesh(m, 0.0, 0.21, -0.03)    # harness tags on and behind the seat backs go; only the two on the shoulder straps in front stay
    k.save(CAR + '.kn5')
    os.chdir(out)
    zp = os.path.join(out, CAR + '.zip')
    if os.path.exists(zp): os.remove(zp)
    subprocess.run(['bsdtar', '-a', '-cf', zp, CAR], check=True)
    shutil.rmtree(tmp)
    print('built', dst)
    print('zip  ', zp, os.path.getsize(zp) // 1024 // 1024, 'MB')

if __name__ == '__main__':
    main()
