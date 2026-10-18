"""Render camera shots of a textured OBJ car (car axes x left, y up, z forward) with EEVEE.
    blender --background --python blender_shots.py -- car.obj out_dir shots.json [fps] [width] [height]
shots.json: [{"name":..., "frames":N, "from":[cx,cy,cz,r,az0,el0,fov], "to":[... same ...]}]
  cx,cy,cz = look-at point in car coords; r = distance; az = azimuth deg (0 = from the front, 90 = from the car's left);
  el = elevation deg; fov in deg. Values interpolate linearly from 'from' to 'to'."""
import bpy, sys, json, math, os
argv = sys.argv[sys.argv.index('--') + 1:]
obj_path, out_dir, shots_path = argv[0], argv[1], argv[2]
fps = int(argv[3]) if len(argv) > 3 else 24; W = int(argv[4]) if len(argv) > 4 else 1280; H = int(argv[5]) if len(argv) > 5 else 720
shots = json.load(open(shots_path))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='NEGATIVE_Y', up_axis='Z')   # keep as-is: Blender(x,y,z) = car(x,y,z)
scene = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH': o.rotation_euler = (math.radians(90), 0, 0)   # car y-up -> Blender z-up; car z (forward) -> Blender -y
def B(p):  # car coords -> Blender coords after that rotation
    return (p[0], -p[2], p[1])
# materials: glass transparent, a touch of gloss everywhere
for m in bpy.data.materials:
    if not m.use_nodes: continue
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if not bsdf: continue
    n = m.name.lower()
    if 'parbrise' in n or 'glass' in n or 'dash_dust' in n:
        m.blend_method = 'BLEND'; bsdf.inputs['Alpha'].default_value = 0.08 if 'parbrise' in n else 0.0
        bsdf.inputs['Roughness'].default_value = 0.05
    elif 'carpaint' in n or 'brg' in n:
        bsdf.inputs['Roughness'].default_value = 0.25; bsdf.inputs['Specular IOR Level' if 'Specular IOR Level' in bsdf.inputs else 'Specular'].default_value = 0.6
    elif 'alu' in n or 'chrome' in n or 'exhaust' in n or 'alloy' in n:
        bsdf.inputs['Metallic'].default_value = 0.9; bsdf.inputs['Roughness'].default_value = 0.3
    elif 'tyre' in n:
        bsdf.inputs['Roughness'].default_value = 0.9
    else:
        bsdf.inputs['Roughness'].default_value = 0.6
# ground
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); ground = bpy.context.object
gm = bpy.data.materials.new('ground'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.82, 0.82, 0.80, 1); gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
ground.data.materials.append(gm)
# lights
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0; sun.angle = math.radians(4)
so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(15), math.radians(-35))
for i, (loc, e) in enumerate((((4, -3, 3), 600), ((-4, 3, 3), 400), ((0, 5, 2.5), 300))):
    a = bpy.data.lights.new(f'area{i}', 'AREA'); a.energy = e; a.size = 4
    ao = bpy.data.objects.new(f'area{i}', a); scene.collection.objects.link(ao); ao.location = loc
    c = ao.constraints.new('TRACK_TO'); c.target = ground; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.75, 0.74, 1); scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
# camera
cam_data = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x = W; scene.render.resolution_y = H; scene.render.fps = fps
scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'Filmic' if 'Filmic' in [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items] else 'AgX'
scene.view_settings.exposure = 0.3
try: scene.eevee.taa_render_samples = 16
except Exception: pass
import mathutils
def place(p):
    cx, cy, cz, r, az, el, fov = p
    a, e = math.radians(az), math.radians(el)
    # azimuth 0 = in front of the nose (car +z), 90 = car's left (+x)
    off = (r * math.cos(e) * math.sin(a), r * math.sin(e), r * math.cos(e) * math.cos(a))
    eye = (cx + off[0], cy + off[1], cz + off[2])
    cam.location = B(eye); tgt = mathutils.Vector(B((cx, cy, cz)))
    d = tgt - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam_data.angle = math.radians(fov)
frame = 0
os.makedirs(out_dir, exist_ok=True)
for s in shots:
    n = s['frames']; f0, f1 = s['from'], s.get('to', s['from'])
    for i in range(n):
        t = i / max(1, n - 1); t = t * t * (3 - 2 * t)      # ease in-out
        place([a + (b - a) * t for a, b in zip(f0, f1)])
        scene.render.filepath = os.path.join(out_dir, f"{s['name']}_{i:04d}.png")
        bpy.ops.render.render(write_still=True); frame += 1
print('rendered', frame, 'frames to', out_dir)
