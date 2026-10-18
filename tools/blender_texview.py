"""Render OBJ files with one texture applied (UV check): blender --background --python blender_texview.py -- mesh.obj texture.png out.png front|left|right|top|rear [ortho_scale]"""
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
obj_path, tex_path, out_png, view = argv[0], argv[1], argv[2], argv[3]; scale = float(argv[4]) if len(argv) > 4 else 1.2
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='NEGATIVE_Y', up_axis='Z')
img = bpy.data.images.load(tex_path)
mat = bpy.data.materials.new('tex'); mat.use_nodes = True; nt = mat.node_tree
texn = nt.nodes.new('ShaderNodeTexImage'); texn.image = img
nt.links.new(texn.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in objs:
    o.data.materials.clear(); o.data.materials.append(mat)
# centre the camera on the meshes
import mathutils
pts = [o.matrix_world @ mathutils.Vector(c) for o in objs for c in o.bound_box]
c = sum(pts, mathutils.Vector()) / len(pts)
scene = bpy.context.scene
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = scale; cam_data.clip_end = 100
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
views = {'front': ((0, 0, 10), (0, 0, 0)), 'rear': ((0, 0, -10), (0, math.radians(180), 0)), 'left': ((10, 0, 0), (0, math.radians(90), 0)), 'right': ((-10, 0, 0), (0, math.radians(-90), 0)), 'top': ((0, 10, 0), (math.radians(-90), 0, 0))}
loc, rot = views[view]; cam.location = (c.x + loc[0], c.y + loc[1], c.z + loc[2]); cam.rotation_euler = rot
scene.render.engine = 'BLENDER_WORKBENCH'; scene.display.shading.light = 'FLAT'; scene.display.shading.color_type = 'TEXTURE'
scene.render.resolution_x = 1400; scene.render.resolution_y = 900; scene.render.filepath = out_png
bpy.ops.render.render(write_still=True); print('rendered', out_png)
