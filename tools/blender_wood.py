"""Bake a walnut-style wood texture from Blender's procedural nodes: blender --background --python blender_wood.py -- out.png [size]"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]; out = argv[0]; size = int(argv[1]) if len(argv) > 1 else 1024
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=2); plane = bpy.context.object
mat = bpy.data.materials.new('wood'); mat.use_nodes = True; nt = mat.node_tree; nodes = nt.nodes; links = nt.links
for n in list(nodes): nodes.remove(n)
outn = nodes.new('ShaderNodeOutputMaterial'); em = nodes.new('ShaderNodeEmission')
coord = nodes.new('ShaderNodeTexCoord'); mapn = nodes.new('ShaderNodeMapping'); mapn.inputs['Scale'].default_value = (1.0, 6.0, 1.0)
wave = nodes.new('ShaderNodeTexWave'); wave.wave_type = 'BANDS'; wave.bands_direction = 'Y'
wave.inputs['Scale'].default_value = 2.2; wave.inputs['Distortion'].default_value = 16.0; wave.inputs['Detail'].default_value = 14.0; wave.inputs['Detail Scale'].default_value = 1.2; wave.inputs['Detail Roughness'].default_value = 0.75
noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 40.0; noise.inputs['Detail'].default_value = 8.0; noise.inputs['Roughness'].default_value = 0.6
mix = nodes.new('ShaderNodeMix'); mix.data_type = 'FLOAT'; mix.inputs['Factor'].default_value = 0.28
ramp = nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = (0.16, 0.07, 0.03, 1)
cr.elements[1].position = 1.0; cr.elements[1].color = (0.50, 0.26, 0.11, 1)
e = cr.elements.new(0.45); e.color = (0.30, 0.14, 0.06, 1)
e2 = cr.elements.new(0.75); e2.color = (0.42, 0.21, 0.09, 1)
links.new(coord.outputs['UV'], mapn.inputs['Vector']); links.new(mapn.outputs['Vector'], wave.inputs['Vector']); links.new(mapn.outputs['Vector'], noise.inputs['Vector'])
links.new(wave.outputs['Fac'], mix.inputs['A']); links.new(noise.outputs['Fac'], mix.inputs['B']); links.new(mix.outputs['Result'], ramp.inputs['Fac'])
links.new(ramp.outputs['Color'], em.inputs['Color']); links.new(em.outputs['Emission'], outn.inputs['Surface'])
plane.data.materials.append(mat)
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 2.0
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam; cam.location = (0, 0, 5)
scene.render.engine = 'BLENDER_EEVEE' if hasattr(bpy.types, 'SceneEEVEE') and 'BLENDER_EEVEE' in [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
scene.view_settings.view_transform = 'Standard'
scene.render.resolution_x = scene.render.resolution_y = size; scene.render.filepath = out; scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True); print('wood baked', out)
