"""OBJ+MTL -> GLB: blender --background --python blender_glb.py -- in.obj out.glb [max_texture_px]
Textures are shrunk to max_texture_px (default 1024) and stored as JPEG (the exporter keeps PNG where an image needs transparency), so the file stays small enough for a dashboard."""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=argv[0], forward_axis='NEGATIVE_Y', up_axis='Z')   # keep car axes as-is
# car axes are y-up already; glTF is y-up and the exporter converts from Blender z-up, so rotate the scene so Blender z-up == car y-up
import math
for o in bpy.data.objects:
    o.rotation_euler = (math.radians(90), 0, 0)
MAXPX = int(argv[2]) if len(argv) > 2 else 1024
for img in bpy.data.images:
    if img.size[0] > MAXPX or img.size[1] > MAXPX:
        k = MAXPX / max(img.size[0], img.size[1]); img.scale(max(1, int(img.size[0] * k)), max(1, int(img.size[1] * k)))
bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', export_yup=True, export_apply=True, export_image_format='JPEG', export_jpeg_quality=78)
print('glb written', argv[1])
