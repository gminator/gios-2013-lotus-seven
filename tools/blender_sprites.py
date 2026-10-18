"""Render a turntable sprite set of the car for dashboards: the car seen from a fixed 3/4 top camera while it turns on the spot,
transparent background, one PNG per heading.
    blender --background --python blender_sprites.py -- car.obj out_dir [frames=72] [size=256] [elevation=58]
Frame i shows the car heading i * 360 / frames degrees counter-clockwise on the screen, 0 = pointing right (east).
Car axes in the OBJ: x left, y up, z forward (see kn5_to_obj_full.py)."""
import bpy, sys, math, os
argv = sys.argv[sys.argv.index('--') + 1:]
obj_path, out_dir = argv[0], argv[1]
N = int(argv[2]) if len(argv) > 2 else 72; SIZE = int(argv[3]) if len(argv) > 3 else 256; EL = float(argv[4]) if len(argv) > 4 else 58.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='NEGATIVE_Y', up_axis='Z')
scene = bpy.context.scene
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes: o.rotation_euler = (math.radians(90), 0, 0)         # car y-up -> Blender z-up; car forward (+z) -> Blender -y
bpy.context.view_layer.update()
# the car's bounding box centre becomes the origin of a turntable empty
import mathutils
lo = mathutils.Vector((1e9, 1e9, 1e9)); hi = mathutils.Vector((-1e9, -1e9, -1e9))
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        lo = mathutils.Vector((min(lo[i], w[i]) for i in range(3))); hi = mathutils.Vector((max(hi[i], w[i]) for i in range(3)))
centre = (lo + hi) / 2
turn = bpy.data.objects.new('turn', None); scene.collection.objects.link(turn); turn.location = (centre.x, centre.y, 0)
bpy.context.view_layer.update()
for o in meshes:
    o.parent = turn; o.matrix_parent_inverse = turn.matrix_world.inverted()
print('car size (m):', round(hi.x - lo.x, 2), round(hi.y - lo.y, 2), round(hi.z - lo.z, 2))
for m in bpy.data.materials:
    if not m.use_nodes: continue
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if not bsdf: continue
    n = m.name.lower()
    if 'parbrise' in n or 'glass' in n or 'dash_dust' in n:
        m.blend_method = 'BLEND'; bsdf.inputs['Alpha'].default_value = 0.08 if 'parbrise' in n else 0.0; bsdf.inputs['Roughness'].default_value = 0.05
    elif 'carpaint' in n or 'brg' in n:
        bsdf.inputs['Roughness'].default_value = 0.25; bsdf.inputs['Specular IOR Level' if 'Specular IOR Level' in bsdf.inputs else 'Specular'].default_value = 0.6
    elif 'alu' in n or 'chrome' in n or 'exhaust' in n or 'alloy' in n:
        bsdf.inputs['Metallic'].default_value = 0.9; bsdf.inputs['Roughness'].default_value = 0.3
    elif 'tyre' in n: bsdf.inputs['Roughness'].default_value = 0.9
    else: bsdf.inputs['Roughness'].default_value = 0.6
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.2; sun.angle = math.radians(6)
so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(40), math.radians(10), math.radians(-30))
for i, (loc, e) in enumerate((((0, -5, 5), 500), ((-5, 3, 4), 250))):
    a = bpy.data.lights.new(f'area{i}', 'AREA'); a.energy = e; a.size = 5
    ao = bpy.data.objects.new(f'area{i}', a); scene.collection.objects.link(ao); ao.location = loc
    c = ao.constraints.new('TRACK_TO'); c.target = turn; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
scene.world = bpy.data.worlds.new('w'); scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.8, 0.8, 0.8, 1); scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 4.6
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
e = math.radians(EL); R = 20.0
cam.location = (centre.x, centre.y - R * math.cos(e), (hi.z - lo.z) / 2 + R * math.sin(e))
tgt = mathutils.Vector((centre.x, centre.y, (hi.z - lo.z) / 2))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
scene.render.resolution_x = SIZE; scene.render.resolution_y = SIZE; scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
views = [i.identifier for i in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items]
scene.view_settings.view_transform = 'Filmic' if 'Filmic' in views else 'AgX'; scene.view_settings.exposure = 0.3
try: scene.eevee.taa_render_samples = 24
except Exception: pass
os.makedirs(out_dir, exist_ok=True)
frames = range(N) if os.environ.get('ONLY') is None else [int(x) for x in os.environ['ONLY'].split(',')]
for i in frames:
    phi = 2 * math.pi * i / N                                    # screen heading, counter-clockwise, 0 = right
    turn.rotation_euler = (0, 0, phi + math.pi / 2)             # unrotated the nose points to -y (down the screen)
    scene.render.filepath = os.path.join(out_dir, f'f{i:02d}.png')
    bpy.ops.render.render(write_still=True)
print('rendered', len(list(frames)), 'sprites to', out_dir)
