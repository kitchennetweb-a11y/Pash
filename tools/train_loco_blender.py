# Split Sketchfab "Locomotive" by yanix (CC-BY, sketchfab.com/3d-models/locomotive-d89f7d5a37ef43119e7b6c37b41c69cb) into two cars for the
# play-room train set: the locomotive and its tender, each with its origin at the bottom centre, front = +X (glTF +x).
# The spoked wheels stay separate nodes named wheel_* with their origin on the axle, so the game can turn them.
#   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python tools/train_loco_blender.py -- locomotive.glb OUT_DIR [preview.png]
import bpy, sys, os, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; SRC, OUT = a[0], a[1]
SPLIT_X = -1.9  # between the engine's cab and the tender

def load():
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=SRC)
    for o in list(bpy.context.scene.objects):  # bake the empties' transforms into the meshes, drop the empties
        if o.type == 'MESH': mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in list(bpy.context.scene.objects):
        if o.type != 'MESH': bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def bbox(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]; return Vector([min(w[i] for w in ws) for i in range(3)]), Vector([max(w[i] for w in ws) for i in range(3)])

def is_wheel(o):
    mn, mx = bbox(o); d = mx - mn
    return d.z > .6 and abs(d.x - d.z) < .18 * d.z and d.y < .35

for car, keep in (('train_loco', lambda x: x > SPLIT_X), ('train_tender', lambda x: x <= SPLIT_X)):
    load()
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objs:
        mn, mx = bbox(o)
        if not keep((mn.x + mx.x) / 2): bpy.data.objects.remove(o)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    mn = Vector([min(bbox(o)[0][i] for o in objs) for i in range(3)]); mx = Vector([max(bbox(o)[1][i] for o in objs) for i in range(3)])
    shift = Matrix.Translation(Vector(((mn.x + mx.x) / -2, (mn.y + mx.y) / -2, -mn.z)))
    wheels, body = [], []
    for o in objs:
        o.data.transform(shift)
        (wheels if is_wheel(o) else body).append(o)
    for i, w in enumerate(wheels):  # origin on the axle
        wmn, wmx = bbox(w); c = (wmn + wmx) / 2; w.data.transform(Matrix.Translation(-c)); w.location = c; w.name = f'wheel_{i}'
    bpy.ops.object.select_all(action='DESELECT')
    for o in body: o.select_set(True)
    bpy.context.view_layer.objects.active = body[0]; bpy.ops.object.join(); body[0].name = car
    bpy.ops.object.select_all(action='SELECT')
    print(f'{car}: length {mx.x - mn.x:.2f} width {mx.y - mn.y:.2f} height {mx.z - mn.z:.2f}, wheels {len(wheels)}, body tris {len(body[0].data.polygons)}')
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, car + '.glb'), export_format='GLB', export_yup=True, export_image_format='JPEG', export_image_quality=82)
