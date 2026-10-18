"""OBJ+MTL -> GLB: blender --background --python blender_glb.py -- in.obj out.glb"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=argv[0], forward_axis='NEGATIVE_Y', up_axis='Z')   # keep car axes as-is
# car axes are y-up already; glTF is y-up and the exporter converts from Blender z-up, so rotate the scene so Blender z-up == car y-up
import math
for o in bpy.data.objects:
    o.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', export_yup=True, export_apply=True)
print('glb written', argv[1])
