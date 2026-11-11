"""Shared helpers for headless Blender model scripts (see blender_models.py for usage).
Run a script with: Blender --background --python <script>.py -- <out_dir>
Model space: X = building length, Y = depth (front faces -Y), Z up, metres, origin at footprint centre on the ground."""
import bpy, bmesh, math, sys, os
from mathutils import Matrix, Vector

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "."
COL = {
    "white": (0xF2, 0xEE, 0xE4), "cream": (0xF1, 0xE4, 0xA6), "grey": (0xB9, 0xB4, 0xAA), "concrete": (0xA6, 0xA3, 0x9C),
    "tile": (0xA4, 0x4E, 0x33), "tile2": (0x8E, 0x40, 0x2B), "timber": (0x3A, 0x2A, 0x20), "glass": (0x20, 0x2A, 0x30),
    "black": (0x1C, 0x1C, 0x1E), "brick": (0x9A, 0x4B, 0x35), "paver": (0x8D, 0x45, 0x30), "blue": (0xCF, 0xE2, 0xEE),
    "red": (0xB5, 0x3A, 0x2E), "sign": (0x7A, 0x3B, 0x2A), "signgrey": (0xC9, 0xCC, 0xD0), "ink": (0x33, 0x3E, 0x52),
    "green": (0x4F, 0x8A, 0x3C), "frame": (0xFA, 0xFA, 0xF6),
}
ROUGH = {"glass": 0.15, "tile": 0.8, "tile2": 0.8}

class Model:
    def __init__(self, name):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.name, self.bm, self.texts = name, {}, []
    def _bm(self, mat):
        return self.bm.setdefault(mat, bmesh.new())
    def box(self, mat, sx, sy, sz, cx, cy, cz, rz=0.0):
        """box of size (sx,sy,sz) centred at (cx,cy) with its base at cz"""
        m = Matrix.Translation((cx, cy, cz + sz / 2)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Diagonal((sx, sy, sz, 1))
        bmesh.ops.create_cube(self._bm(mat), size=1, matrix=m)
    def cyl(self, mat, r, h, cx, cy, cz, seg=12, r2=None):
        m = Matrix.Translation((cx, cy, cz + h / 2))
        bmesh.ops.create_cone(self._bm(mat), cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h, matrix=m)
    def poly(self, mat, pts):
        bm = self._bm(mat); bm.faces.new([bm.verts.new(p) for p in pts])
    def hip(self, mat, w, d, cx, cy, z, rise, soffit="timber"):
        """hipped roof over a w x d rectangle (eaves at z), ridge along the longer side"""
        hw, hd = w / 2, d / 2
        if w >= d: r = [(cx - hw + hd, cy), (cx + hw - hd, cy)]
        else: r = [(cx, cy - hd + hw), (cx, cy + hd - hw)]
        c = [(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)]
        E = [(x, y, z) for x, y in c]; R = [(x, y, z + rise) for x, y in r]
        if w >= d: faces = [[E[0], E[1], R[1], R[0]], [E[2], E[3], R[0], R[1]], [E[1], E[2], R[1]], [E[3], E[0], R[0]]]
        else: faces = [[E[1], E[2], R[1], R[0]], [E[3], E[0], R[0], R[1]], [E[0], E[1], R[0]], [E[2], E[3], R[1]]]
        for f in faces: self.poly(mat, f)
        self.box(soffit, w - 0.05, d - 0.05, 0.12, cx, cy, z - 0.12)
    def skirt(self, mat, w, d, cx, cy, z, out=0.9, drop=0.45):
        """sloping tile band around a w x d block at height z (the tiled sunshade between floors)"""
        hw, hd = w / 2, d / 2
        a = [(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)]
        b = [(cx - hw - out, cy - hd - out), (cx + hw + out, cy - hd - out), (cx + hw + out, cy + hd + out), (cx - hw - out, cy + hd + out)]
        for i in range(4):
            j = (i + 1) % 4
            self.poly(mat, [(*b[i], z - drop), (*b[j], z - drop), (*a[j], z), (*a[i], z)])
    def window(self, cx, cy, cz, w=1.3, h=1.4, ry=0.0, shutters=True, frame="frame"):
        """window on a wall whose outward normal is rotated ry about Z from -Y"""
        R = Matrix.Rotation(ry, 4, "Z")
        def b(mat, sx, sy, sz, ox, oy, oz):
            p = R @ Vector((ox, oy, 0)); self.box(mat, sx, sy, sz, cx + p.x, cy + p.y, cz + oz, ry)
        b(frame, w + 0.16, 0.1, h + 0.16, 0, -0.03, -0.08); b("glass", w, 0.06, h, 0, -0.08, 0)
        b(frame, 0.05, 0.05, h, 0, -0.11, 0); b(frame, w, 0.05, 0.05, 0, -0.11, h * 0.55)
        if shutters:
            for s in (-1, 1): b(frame, 0.5, 0.05, h, s * (w / 2 + 0.3), -0.1, 0)
    def arch(self, cx, cy, cz, w, h, ry=0.0, trim="red", fill="glass"):
        R = Matrix.Rotation(ry, 4, "Z")
        for mat, k, off in ((trim, 1.0, -0.02), (fill, 0.84, -0.06)):
            p = R @ Vector((0, off, 0)); ww = w * k
            self.box(mat, ww, 0.12, h - w / 2, cx + p.x, cy + p.y, cz, ry)
            m = Matrix.Translation((cx + p.x, cy + p.y, cz + h - w / 2)) @ Matrix.Rotation(ry, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")
            bmesh.ops.create_cone(self._bm(mat), cap_ends=True, segments=20, radius1=ww / 2, radius2=ww / 2, depth=0.12, matrix=m)
    def text(self, mat, body, size, cx, cy, cz, ry=0.0):
        self.texts.append((mat, body, size, cx, cy, cz, ry))
    def finish(self):
        objs = []
        for mat, bm in self.bm.items():
            me = bpy.data.meshes.new(mat); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
            ob = bpy.data.objects.new(mat, me); bpy.context.scene.collection.objects.link(ob); ob.data.materials.append(material(mat)); objs.append(ob)
        for mat, body, size, cx, cy, cz, ry in self.texts:
            cu = bpy.data.curves.new("t", "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.extrude = 0.02
            ob = bpy.data.objects.new("t", cu); bpy.context.scene.collection.objects.link(ob)
            ob.rotation_euler = (math.pi / 2, 0, ry); ob.location = (cx, cy, cz); ob.data.materials.append(material(mat))
            bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.convert(target="MESH"); ob.select_set(False); objs.append(ob)
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); objs[0].name = self.name
        os.makedirs(OUT, exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, self.name + ".glb"), export_format="GLB", export_yup=True, export_apply=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, self.name + ".blend"))
        print("exported", self.name, len(objs[0].data.vertices), "verts")

def material(name):
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; r, g, bl = (pow(c / 255, 2.2) for c in COL[name])
    b.inputs["Base Color"].default_value = (r, g, bl, 1); b.inputs["Roughness"].default_value = ROUGH.get(name, 0.85)
    return m

