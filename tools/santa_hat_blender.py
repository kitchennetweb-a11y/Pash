# Googoo's Santa hat: red, soft and floppy (the tip droops to one side), a fluffy cream band, a pom-pom (its own node "pompom", the game wobbles it).
# Y-up in the game, band centre at the origin, about 0.5 across like the witch hat's crown.
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python tools/santa_hat_blender.py -- models/santa_hat.glb [preview.png]
import bpy, bmesh, math, sys
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)

def lin(h):
    c = [((h >> s) & 255) / 255 for s in (16, 8, 0)]
    return [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c] + [1]
def mat(name, hexcol, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(hexcol); b.inputs['Roughness'].default_value = rough
    return m
RED, FUR = mat('hat_red', 0xd42a2a, .75), mat('hat_fur', 0xf4ecdc, .95)

def obj(name, bm, m):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    return o
SEG = 48
def ring(bm, r, z, off=(0, 0)):
    return [bm.verts.new((off[0] + r * math.cos(a), off[1] + r * math.sin(a), z)) for a in (math.tau * i / SEG for i in range(SEG))]
def bridge(bm, a, b):
    for i in range(SEG): bm.faces.new((a[i], a[(i + 1) % SEG], b[(i + 1) % SEG], b[i]))

# floppy cone: up, then the top half bends over to the side and down
bm = bmesh.new(); N = 30; rings = []; x, z, dl = 0., .05, .78 / 30
for i in range(N + 1):
    t = i / N; r = .235 * (1 - t) ** .9 + .035
    a = max(0, t - .3) / .7; ang = a ** 1.6 * 2.3  # tilt from upright grows along the hat: past level, so the tip droops
    rings.append(ring(bm, r, z, (x, 0))); tipx, tipz = x, z
    x += math.sin(ang) * dl; z += math.cos(ang) * dl
for a, b in zip(rings, rings[1:]): bridge(bm, a, b)
cap = bm.verts.new((tipx, 0, tipz + .005))
for i in range(SEG): bm.faces.new((rings[-1][i], rings[-1][(i + 1) % SEG], cap))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); obj('cone', bm, RED)

# fluffy band: a fat torus with a slightly bumpy surface
bm = bmesh.new(); R0, r0, S2 = .25, .065, 20; rs = []
for i in range(SEG):
    u = math.tau * i / SEG; c, s = math.cos(u), math.sin(u)
    rs.append([bm.verts.new(((R0 + (r0 + .006 * math.sin(7 * u + 3 * v)) * math.cos(v)) * c, (R0 + (r0 + .006 * math.sin(7 * u + 3 * v)) * math.cos(v)) * s, .05 + r0 * math.sin(v))) for v in (math.tau * k / S2 for k in range(S2))])
for i in range(SEG):
    a, b = rs[i], rs[(i + 1) % SEG]
    for k in range(S2): bm.faces.new((a[k], b[k], b[(k + 1) % S2], a[(k + 1) % S2]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); obj('band', bm, FUR)

# pom-pom at the tip
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=.075)
pp = obj('pompom', bm, FUR); pp.location = (tipx + .03, 0, tipz - .05)

bpy.ops.export_scene.gltf(filepath=args[0], export_format='GLB', export_apply=True, export_yup=True)
print('exported', args[0])
if len(args) > 1:
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 600; sc.render.filepath = args[1]
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .5, .55, 1)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.location = (.3, -2.0, .55); cam.rotation_euler = (math.radians(82), 0, math.radians(8))
    L = bpy.data.objects.new('l', bpy.data.lights.new('l', 'SUN')); L.data.energy = 4; L.rotation_euler = (.6, .3, .4); bpy.context.collection.objects.link(L)
    bpy.ops.render.render(write_still=True)
