"""Build the ORCA low-poly asset pack. Run:
Blender -b --python build_assets.py
Writes orca-assets.blend (next to this file), ../web/public/models/orca-assets.glb and /tmp/orca-assets-preview.png.
Blender is Z-up; the glTF exporter converts to +Y up. Each object is normalised to a largest dimension of 1.0.
Satellite is centred on the origin; ground objects are centred in XY with their base at the origin.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.normpath(os.path.join(HERE, "..", "web", "public", "models", "orca-assets.glb"))
BLEND = os.path.join(HERE, "orca-assets.blend")
PREVIEW = "/tmp/orca-assets-preview.png"

# ---------- scene reset ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)

# ---------- materials (roles) ----------
MATS = {}
COLORS = {"body": (0.72, 0.74, 0.78), "panel": (0.12, 0.22, 0.45),
          "accent": (0.95, 0.55, 0.15), "dark": (0.12, 0.13, 0.15)}
for i, (n, c) in enumerate(COLORS.items()):
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = 0.8
    b.inputs["Metallic"].default_value = 0.0
    for k in ("Emission Strength",):
        if k in b.inputs:
            b.inputs[k].default_value = 0.0
    m.diffuse_color = (*c, 1)
    MATS[n] = (i, m)

# ---------- bmesh builders ----------
class Builder:
    def __init__(self):
        self.bm = bmesh.new()

    def _tag(self, geom, mat):
        for f in [g for g in geom if isinstance(g, bmesh.types.BMFace)]:
            f.material_index = MATS[mat][0]

    def box(self, c, size, mat, rot=None):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        m = Matrix.Translation(Vector(c))
        if rot is not None:
            m = m @ rot.to_4x4()
        m = m @ Matrix.Diagonal((*size, 1.0))
        bmesh.ops.transform(self.bm, matrix=m, verts=r["verts"])
        self._tag(r["verts"][0].link_faces[:] and [f for v in r["verts"] for f in v.link_faces], mat)

    def strut(self, p0, p1, r, mat, seg=4, r2=None):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r,
                                    radius2=r if r2 is None else r2, depth=d.length)
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation((p0 + p1) / 2) @ rot, verts=res["verts"])
        self._tag([f for v in res["verts"] for f in v.link_faces], mat)

    def dish(self, c, direction, R, depth, mat, seg=14, rings=3, t=0.04):
        """Parabolic shell, vertex at c, opening toward direction."""
        bm = self.bm
        rot = Vector(direction).to_track_quat("Z", "Y").to_matrix().to_4x4()
        M = Matrix.Translation(Vector(c)) @ rot
        def surf(off):
            vs = [bm.verts.new(M @ Vector((0, 0, off)))]
            rg = []
            for i in range(1, rings + 1):
                r = R * i / rings
                z = depth * (r / R) ** 2 + off
                ring = [bm.verts.new(M @ Vector((r * math.cos(2 * math.pi * k / seg),
                                                 r * math.sin(2 * math.pi * k / seg), z)))
                        for k in range(seg)]
                rg.append(ring)
            return vs[0], rg
        c0, fr = surf(0.0)
        c1, bk = surf(-t)
        faces = []
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append(bm.faces.new((c0, fr[0][k2], fr[0][k])))
            faces.append(bm.faces.new((c1, bk[0][k], bk[0][k2])))
            for i in range(rings - 1):
                faces.append(bm.faces.new((fr[i][k], fr[i][k2], fr[i + 1][k2], fr[i + 1][k])))
                faces.append(bm.faces.new((bk[i][k], bk[i + 1][k], bk[i + 1][k2], bk[i][k2])))
            faces.append(bm.faces.new((fr[-1][k], fr[-1][k2], bk[-1][k2], bk[-1][k])))
        self._tag(faces, mat)

    def finish(self, name, centre_z):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        cz = (min(zs) + max(zs)) / 2 if centre_z else min(zs)
        dim = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
        s = 1.0 / dim
        for v in bm.verts:
            v.co = Vector(((v.co.x - cx) * s, (v.co.y - cy) * s, (v.co.z - cz) * s))
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for n in ("body", "panel", "accent", "dark"):
            me.materials.append(MATS[n][1])
        for p in me.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob

def tilt(el_deg, az_deg=90.0):
    e, a = math.radians(el_deg), math.radians(az_deg)
    return Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))

# ---------- 1. Satellite ----------
def satellite():
    b = Builder()
    b.box((0, 0, 0), (1.0, 1.0, 1.3), "body")
    b.box((0, 0, 0.66), (1.04, 1.04, 0.08), "dark")       # top deck
    b.box((0, 0, -0.66), (1.04, 1.04, 0.08), "dark")      # nadir deck
    for sgn in (-1, 1):
        b.strut((sgn * 0.5, 0, 0), (sgn * 0.95, 0, 0), 0.06, "dark", seg=6)
        cx = sgn * (0.95 + 1.3)
        b.box((cx, 0, 0), (2.6, 0.04, 1.2), "panel")
        for k in (-0.65, 0.0, 0.65):                       # cell frame bars
            b.box((cx + sgn * k * 1.0, 0, 0), (0.05, 0.07, 1.24), "dark")
        b.box((cx, 0, 0), (2.64, 0.07, 0.05), "dark")
    # big dish on +Y, smaller on -Y, angled slightly down
    d1 = Vector((0, math.cos(math.radians(25)), -math.sin(math.radians(25))))
    p1 = Vector((0, 0.52, 0.1))
    b.dish(p1, d1, 0.6, 0.22, "body", seg=16)
    b.strut(p1 + d1 * 0.0, p1 - Vector((0, 0.2, 0)), 0.04, "dark")
    b.strut(p1 + d1 * 0.5 + Vector((0, 0, 0.0)), p1 + d1 * 0.02, 0.012, "dark", seg=3)
    b.box(p1 + d1 * 0.52, (0.1, 0.1, 0.1), "accent")
    d2 = Vector((0, -math.cos(math.radians(30)), -math.sin(math.radians(30))))
    p2 = Vector((0, -0.52, 0.25))
    b.dish(p2, d2, 0.4, 0.15, "body", seg=14)
    b.box(p2 + d2 * 0.36, (0.07, 0.07, 0.07), "accent")
    b.strut(p2 + d2 * 0.36, p2, 0.012, "dark", seg=3)
    # nadir feed horn
    b.strut((0, 0, -0.7), (0, 0, -1.0), 0.05, "accent", seg=6, r2=0.16)
    b.strut((0.3, 0.3, 0.7), (0.3, 0.3, 1.1), 0.015, "dark", seg=4)
    return b.finish("Satellite", True)

# ---------- 2. GatewayDish ----------
def gateway():
    b = Builder()
    b.strut((0, 0, 0), (0, 0, 0.35), 0.75, "dark", seg=12)
    b.strut((0, 0, 0.35), (0, 0, 1.4), 0.28, "body", seg=8, r2=0.2)
    d = tilt(55, 90)
    c = Vector((0, 0, 1.75))
    b.box(c - d * 0.1, (0.4, 0.4, 0.3), "dark")
    R, dep = 1.6, 0.55
    b.dish(c + Vector((0, 0, 0.25)), d, R, dep, "body", seg=20, rings=4)
    f = R * R / (4 * dep)
    tip = c + Vector((0, 0, 0.25)) + d * f
    rim = lambda a: c + Vector((0, 0, 0.25)) + Vector((1, 0, 0)).__rmul__(1) * 0
    side = d.cross(Vector((0, 0, 1))).normalized()
    up2 = side.cross(d).normalized()
    base = c + Vector((0, 0, 0.25))
    for ang in (0, 120, 240):
        a = math.radians(ang)
        edge = base + (side * math.cos(a) + up2 * math.sin(a)) * R * 0.85 + d * dep * 0.72
        b.strut(edge, tip, 0.03, "dark", seg=4)
    b.strut(tip, tip + d * 0.25, 0.07, "accent", seg=6, r2=0.14)
    # hut
    b.box((3.1, 0, 0.45), (1.8, 1.2, 0.9), "body")
    b.box((3.1, 0, 0.94), (1.9, 1.3, 0.08), "accent")
    b.box((3.1, -0.61, 0.38), (0.4, 0.04, 0.7), "dark")
    b.strut((2.5, 0.0, 0.94), (2.5, 0.0, 1.5), 0.03, "dark", seg=4)
    b.strut((1.6, 0, 0.5), (2.2, 0, 0.5), 0.04, "dark", seg=4)  # feeder duct to dish base
    return b.finish("GatewayDish", False)

# ---------- 3. CellTower ----------
def tower():
    b = Builder()
    H, hw0, hw1, n = 4.4, 0.55, 0.18, 5
    hw = lambda z: hw0 + (hw1 - hw0) * z / H
    corner = lambda z, k: Vector(((1 if k in (0, 3) else -1) * hw(z), (1 if k in (0, 1) else -1) * hw(z), z))
    for k in range(4):
        b.strut(corner(0, k), corner(H, k), 0.04, "body", seg=4)
    zs = [H * i / n for i in range(n + 1)]
    for i, z in enumerate(zs):
        for k in range(4):
            b.strut(corner(z, k), corner(z, (k + 1) % 4), 0.018, "dark", seg=3)
        if i < n:
            for k in range(4):
                a, c2 = (k, (k + 1) % 4)
                if (i + k) % 2:
                    b.strut(corner(zs[i], a), corner(zs[i + 1], c2), 0.016, "dark", seg=3)
                else:
                    b.strut(corner(zs[i], c2), corner(zs[i + 1], a), 0.016, "dark", seg=3)
    b.box((0, 0, 0.0 + 0.04), (1.35, 1.35, 0.08), "dark")   # footing
    b.box((0, 0, H + 0.03), (0.6, 0.6, 0.06), "dark")       # platform
    b.strut((0, 0, H), (0, 0, 5.45), 0.03, "dark", seg=4)
    b.box((0, 0, 5.5), (0.1, 0.1, 0.1), "accent")           # beacon (flat colour)
    for ang in (90, 210, 330):
        a = math.radians(ang)
        rv = Vector((math.cos(a), math.sin(a), 0))
        rot = Matrix.Rotation(a - math.pi / 2, 3, "Z")
        b.box(rv * 0.5 + Vector((0, 0, 4.85)), (0.24, 0.07, 0.8), "panel", rot)
        b.strut(rv * 0.2 + Vector((0, 0, H + 0.05)), rv * 0.47 + Vector((0, 0, 4.6)), 0.015, "dark", seg=3)
        b.strut(rv * 0.2 + Vector((0, 0, H + 0.05)), rv * 0.47 + Vector((0, 0, 5.1)), 0.015, "dark", seg=3)
    # microwave dish on -Y face
    b.strut((0, -0.2, 3.5), (0, -0.46, 3.5), 0.04, "dark", seg=4)
    b.dish(Vector((0, -0.46, 3.5)), Vector((0, -1, 0)), 0.26, 0.09, "body", seg=12, rings=2, t=0.03)
    b.strut((0, -0.55, 3.5), (0, -0.72, 3.5), 0.03, "accent", seg=4)
    return b.finish("CellTower", False)

# ---------- 4. UserTerminal ----------
def terminal():
    b = Builder()
    b.box((0, 0, 0.04), (0.8, 0.8, 0.08), "dark")
    b.strut((0, 0, 0.08), (0, 0, 0.7), 0.05, "body", seg=6)
    d = tilt(50, 90)
    c = Vector((0, 0, 0.8))
    b.box(c - d * 0.04, (0.14, 0.14, 0.14), "dark")
    R, dep = 0.5, 0.16
    b.dish(c, d, R, dep, "body", seg=16, rings=3, t=0.03)
    f = R * R / (4 * dep)
    tip = c + d * f
    side = d.cross(Vector((0, 0, 1))).normalized()
    b.strut(c + side * R * 0.8 + d * dep * 0.64, tip, 0.012, "dark", seg=3)
    b.strut(c - side * R * 0.8 + d * dep * 0.64, tip, 0.012, "dark", seg=3)
    b.box(tip + d * 0.03, (0.07, 0.07, 0.07), "accent")
    b.box((0.85, 0.0, 0.12), (0.42, 0.3, 0.12), "body")      # modem box
    b.box((0.85, -0.151, 0.12), (0.1, 0.01, 0.03), "accent")
    b.strut((0.2, 0, 0.12), (0.64, 0, 0.12), 0.012, "dark", seg=3)
    return b.finish("UserTerminal", False)

objs = [satellite(), gateway(), tower(), terminal()]
for ob in objs:
    ob.location = (0, 0, 0)
    ob.select_set(False)

# ---------- stats ----------
stats = {}
for ob in objs:
    ob.data.calc_loop_triangles()
    stats[ob.name] = (len(ob.data.loop_triangles), tuple(round(x, 3) for x in ob.dimensions))
print("STATS", stats)

# ---------- save + export (no cameras / lights in scene yet) ----------
bpy.ops.object.select_all(action="DESELECT")
for ob in objs:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
os.makedirs(os.path.dirname(GLB), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True, export_yup=True,
                          export_apply=True, export_cameras=False, export_lights=False,
                          export_image_format="NONE", export_draco_mesh_compression_enable=False,
                          export_materials="EXPORT")
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("GLB bytes", os.path.getsize(GLB))

# ---------- preview (not saved to the .blend) ----------
for i, ob in enumerate(objs):
    ob.location = (i * 1.5, 0, 0)
    if i == 0:
        ob.location.z = 0.5
    ob.rotation_euler = (0, 0, math.radians(-25 if i in (1, 3) else 0))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
bpy.context.scene.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = 6.2
cam.location = (2.1 + 2.5, -8, 3.5)
tgt = Vector((2.25, 0, 0.45))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = False
sc.display.render_aa = "8"
sc.render.resolution_x, sc.render.resolution_y = 1800, 560
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.93, 0.94, 0.96)
sc.render.filepath = PREVIEW
bpy.ops.render.render(write_still=True)
print("DONE")
