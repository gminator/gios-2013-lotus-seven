"""Render an OBJ (car axes: y up, z forward) from a fixed view: blender --background --python blender_view.py -- in.obj out.png left|right|top|front"""
import bpy, sys, math, random
argv = sys.argv[sys.argv.index('--') + 1:]
obj_path, out_png, view = argv[0], argv[1], argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='Z', up_axis='Y')
scene = bpy.context.scene
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.clip_end = 100
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
# Blender frame after import: car y-up becomes Blender z-up, car z-forward becomes Blender -y? we just place cameras on each axis
views = {
    'left':  ((10, 0, 0.4), (math.radians(90), 0, math.radians(90))),
    'right': ((-10, 0, 0.4), (math.radians(90), 0, math.radians(-90))),
    'top':   ((0, 0, 10), (0, 0, 0)),
    'front': ((0, -10, 0.4), (math.radians(90), 0, 0)),
    'rear':  ((0, 10, 0.4), (math.radians(90), 0, math.radians(180))),
}
cam.location, cam.rotation_euler = views[view]; cam_data.ortho_scale = 3.8
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'OBJECT'
for o in bpy.data.objects:
    if o.type == 'MESH':
        random.seed(o.name); o.color = (0.3 + 0.7 * random.random(), 0.3 + 0.7 * random.random(), 0.3 + 0.7 * random.random(), 1)
scene.render.resolution_x = 1600; scene.render.resolution_y = 900
scene.render.filepath = out_png; bpy.ops.render.render(write_still=True)
print('rendered', out_png)
