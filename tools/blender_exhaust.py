"""Build Giovann's side exhaust in car space (x left, y up, z forward; metres) and export it as OBJ with UVs.
    blender --background --python blender_exhaust.py -- out.obj
UV layout (texture 1024x1024): rows of 256 px: 0 steel, 1 wrapped elbow, 2 mesh guard (alpha holes), 3 black bands/end caps."""
import bpy, bmesh, sys, math
from mathutils import Vector
out_obj = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
X = 0.47          # side of the car the exhaust is on (same sign as the mod's exhaust)
def tube(name, pts, radius, row, segs=20, closed_ends=False):
    """polyline pts (list of Vector) swept into a tube; UV u along length, v within the texture row"""
    bm = bmesh.new(); rings = []
    # smooth the polyline a little with Catmull-Rom style subdivision
    def resample(p, n=3):
        q = [p[0]]
        for a, b in zip(p, p[1:]):
            for k in range(1, n + 1): q.append(a.lerp(b, k / n))
        return q
    pts = resample(pts)
    # tangents and a parallel-transported frame
    tans = [(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(len(pts))]
    up = Vector((0, 1, 0)) if abs(tans[0].dot(Vector((0, 1, 0)))) < 0.9 else Vector((1, 0, 0))
    n0 = (up - tans[0] * up.dot(tans[0])).normalized()
    normals = [n0]
    for i in range(1, len(pts)):
        n = normals[-1] - tans[i] * normals[-1].dot(tans[i]); normals.append(n.normalized())
    L = sum((b - a).length for a, b in zip(pts, pts[1:])); s = 0
    uv_layer = bm.loops.layers.uv.new()
    for i, p in enumerate(pts):
        if i: s += (pts[i] - pts[i - 1]).length
        n = normals[i]; bnorm = tans[i].cross(n)
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            v = bm.verts.new(p + (n * math.cos(a) + bnorm * math.sin(a)) * radius); ring.append(v)
        rings.append((ring, s / L))
    faces = []
    for (r0, u0), (r1, u1) in zip(rings, rings[1:]):
        for k in range(segs):
            f = bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k])); faces.append((f, u0, u1, k))
    for f, u0, u1, k in faces:
        for loop in f.loops:
            is_r1 = loop.vert in [r for r, _ in rings[1:]][0] if False else None
        # assign uv by matching vertex to ring
        for loop in f.loops:
            vert = loop.vert
            for ring, u in rings:
                if vert in ring:
                    kk = ring.index(vert); vv = kk / segs
                    # avoid seam wrap: faces with k == segs-1 use vv=1 for index 0
                    if k == segs - 1 and kk == 0: vv = 1.0
                    loop[uv_layer].uv = (u, (row + 0.08 + vv * 0.84) / 4)
                    break
    if closed_ends:
        for ring, u in (rings[0], rings[-1]):
            f = bm.faces.new(ring)
            for loop in f.loops: loop[uv_layer].uv = (u, (3 + 0.5) / 4)
    for f in bm.faces: f.smooth = True
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob
V = Vector
# elbow: comes out of the hole in the side panel (x 0.46, y 0.29, z 0.98), curls down and back into the silencer front
tube('elbow', [V((X - 0.03, 0.29, 0.985)), V((X + 0.03, 0.29, 0.985)), V((X + 0.085, 0.27, 0.975)), V((X + 0.11, 0.235, 0.94)), V((X + 0.115, 0.215, 0.90)), V((X + 0.115, 0.215, 0.86))], 0.034, 1)
# silencer body with end caps, and the mesh guard around it (bands drawn in the texture)
tube('silencer', [V((X + 0.115, 0.215, 0.86)), V((X + 0.115, 0.215, -0.42))], 0.062, 0, closed_ends=True)
tube('guard', [V((X + 0.115, 0.215, 0.84)), V((X + 0.115, 0.215, -0.40))], 0.082, 2, segs=24)
for z in (0.84, 0.30, -0.10, -0.40):   # black guard bands as short wider rings
    tube(f'band_{z}', [V((X + 0.115, 0.215, z + 0.012)), V((X + 0.115, 0.215, z - 0.012))], 0.086, 3, segs=24)
# tailpipe: out of the silencer rear, then a 90 degree bend down and slightly outward, ending in front of the rear wheel
tube('tail', [V((X + 0.115, 0.215, -0.42)), V((X + 0.115, 0.215, -0.50)), V((X + 0.12, 0.205, -0.54)), V((X + 0.125, 0.18, -0.565)), V((X + 0.13, 0.145, -0.575)), V((X + 0.13, 0.10, -0.575))], 0.03, 0)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.obj_export(filepath=out_obj, forward_axis='Z', up_axis='Y', export_materials=False, export_uv=True, export_normals=True)
print('exported', out_obj, 'objects', len(bpy.data.objects))
