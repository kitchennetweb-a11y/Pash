# Tidy the Tripo toy-train cars (image-to-3D from the owner's metal train sheet) for the play-room train set:
# drop stray loose bits, size the cars against each other (engine 1.0 long), origin at the bottom centre, front = +X (glTF +x),
# a steel coupling hook on the engine's back, glossy enamel-on-metal finish. Wheels stay in the mesh: they are plain discs, turning wouldn't show.
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python tools/train_refine_blender.py -- SRC_DIR OUT_DIR [lineup.png]
import bpy, bmesh, sys, os, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]; SRC, OUT = args[0], args[1]
CARS = {'train_engine': 1.02, 'train_wagon_yellow': .9, 'train_wagon_green': .96}  # scale: averaged from the sheet's lengths and heights

def lin(h):
    c = [((h >> s) & 255) / 255 for s in (16, 8, 0)]
    return [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c] + [1]

def tidy(o, keep=.01):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen, islands = set(), []
    for v in bm.verts:  # loose parts by vertex connectivity
        if v.index in seen: continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            a = stack.pop(); isl.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen: seen.add(b.index); stack.append(b)
        islands.append(isl)
    big = max(len(i) for i in islands); drop = [v for i in islands if len(i) < big * keep for v in i]
    bmesh.ops.delete(bm, geom=drop, context='VERTS'); bm.to_mesh(o.data); bm.free()
    return len(islands), len(drop)

def finish(m):  # glossy enamel paint over metal: a bit more shine than Tripo's default
    b = m.node_tree.nodes.get('Principled BSDF')
    if b: b.inputs['Roughness'].default_value = .55; b.inputs['Coat Weight'].default_value = .4; b.inputs['Coat Roughness'].default_value = .2

placed = []
for name, s in CARS.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SRC, name + '.glb'))
    o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    n, d = tidy(o)
    vs = [v.co for v in o.data.vertices]; mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
    o.data.transform(__import__('mathutils').Matrix.Translation(Vector(((mn.x + mx.x) / -2, (mn.y + mx.y) / -2, -mn.z))))
    o.data.transform(__import__('mathutils').Matrix.Scale(s, 4))
    for m in o.data.materials: finish(m)
    L = (mx.x - mn.x) * s; H = (mx.z - mn.z) * s
    if name == 'train_engine':  # a steel coupling hook on the back (-X), at buffer height
        steel = bpy.data.materials.new('coupling_steel'); steel.use_nodes = True; bb = steel.node_tree.nodes['Principled BSDF']
        bb.inputs['Base Color'].default_value = lin(0xb8bcc4); bb.inputs['Metallic'].default_value = 1; bb.inputs['Roughness'].default_value = .25
        bpy.ops.mesh.primitive_cylinder_add(radius=.022, depth=.11, location=(-L / 2 - .045, 0, .2), rotation=(0, math.pi / 2, 0))
        bar = bpy.context.active_object; bar.data.materials.append(steel)
        bpy.ops.mesh.primitive_torus_add(major_radius=.035, minor_radius=.011, location=(-L / 2 - .1, 0, .2), rotation=(math.pi / 2, 0, 0))
        hook = bpy.context.active_object; hook.data.materials.append(steel)
        for x in (bar, hook): x.select_set(True)
        o.select_set(True); bpy.context.view_layer.objects.active = o; bpy.ops.object.join()
    o.name = name
    print(f'{name}: islands {n}, dropped {d} verts, length {L:.3f}, height {H:.3f}, tris {len(o.data.polygons)}')
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + '.glb'), export_format='GLB', export_apply=True, export_yup=True)
    placed.append((name, L))

if len(args) > 2:  # line-up preview: engine in front, wagons behind it
    bpy.ops.wm.read_factory_settings(use_empty=True); x = 0
    for name, L in placed:
        bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, name + '.glb'))
        for ob in bpy.context.selected_objects: ob.location.x += x - L / 2
        x -= L + .12
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1400, 600; sc.render.filepath = args[2]
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.6, .6, .65, 1)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.6; cam.location = (x / 2 + .3, -6, 2.2); cam.rotation_euler = (math.radians(75), 0, 0)
    Ls = bpy.data.objects.new('l', bpy.data.lights.new('l', 'SUN')); Ls.data.energy = 3.5; Ls.rotation_euler = (.8, .2, .5); sc.collection.objects.link(Ls)
    bpy.ops.render.render(write_still=True)
