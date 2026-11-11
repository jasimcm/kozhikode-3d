"""Sarovaram Bio Park: tiled entrance gateway (padippura) at the canal footbridge, paved paths on their mapped lines,
timber boardwalk over the Kalipoika wetland water, tiled pavilions, a boat jetty with pedal boats, an open-air theatre.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_sarovaram.py -- <out_dir>

Model space: metres, +X east, +Y north, Z up. Origin = grid (x=-91.7, n=4822.1) = lon 75.79416, lat 11.26861.
The park spreads over ~330 x 280 m of uneven ground, so it is meant to be placed with "drape": true (src/models.js adds
max(terrain, y-1.5) to every vertex): paths, boardwalk and lamps are modelled on z=0 in short pieces and follow the
ground; buildings are built inside `Level(...)`, which pre-subtracts the terrain under each vertex so they stay level.
Layout source: Overture water / path segments (data/raw/*.parquet) via geo.to_xy. Positions of the theatre, pavilions
and the boardwalk route are placed by judgement (the real ones are hidden under tree canopy in satellite imagery)."""
import sys, os, math, json
import bpy, bmesh
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_lib import Model, COL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OX, OY, FLOOR = -91.7, 4822.1, 0.0
COL.update({
    "deck": (0x8A, 0x62, 0x40), "deck2": (0x6E, 0x4C, 0x32), "earth": (0x8C, 0x70, 0x54), "stone": (0x86, 0x80, 0x76),
    "laterite": (0x9A, 0x5A, 0x40), "lamp": (0xF6, 0xEE, 0xC8), "steel": (0x3A, 0x40, 0x3C), "boat1": (0xE0, 0xB0, 0x30),
    "boat2": (0x2E, 0x7C, 0xB8), "boat3": (0xD8, 0x50, 0x40), "brass": (0xB8, 0x90, 0x40), "board": (0x2E, 0x5A, 0x3A),
})

def terrain():
    try:
        import numpy as np
        M = json.load(open(os.path.join(ROOT, "data", "manifest.json"))); GW, GH = M["grid"]; HX, HY = M["halfX"], M["halfY"]
        H = np.fromfile(os.path.join(ROOT, "data", "height_core.bin"), np.uint16).reshape(GH, GW) / 10 - 100
    except Exception as e:
        print("no terrain, assuming flat:", e); return lambda x, y: FLOOR
    def g(x, y):   # same bilinear lookup as Terrain.heightAt in src/city.js, clamped like the drape code
        u = (x + OX + HX) / (2 * HX) * (GW - 1); v = (HY - (y + OY)) / (2 * HY) * (GH - 1)
        i, j = int(u), int(v); fu, fv = u - i, v - j
        t = (H[j, i] * (1 - fu) + H[j, i + 1] * fu) * (1 - fv) + (H[j + 1, i] * (1 - fu) + H[j + 1, i + 1] * fu) * fv
        return max(float(t), FLOOR)
    return g
G = terrain()

class Level:
    """geometry built inside is given in absolute heights above `base`; the ground under each vertex is subtracted"""
    def __init__(self, m, base): self.m, self.base = m, base
    def __enter__(self): self.n = {k: len(b.verts) for k, b in self.m.bm.items()}; return self
    def __exit__(self, *a):
        for k, b in self.m.bm.items():
            b.verts.ensure_lookup_table()
            for i in range(self.n.get(k, 0), len(b.verts)):
                v = b.verts[i]; v.co.z += self.base - G(v.co.x, v.co.y)

def frame(cx, cy, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return lambda u, v, z=0.0: (cx + u * ca - v * sa, cy + u * sa + v * ca, z)
def fbox(m, F, ang, mat, su, sv, sz, u, v, z):
    x, y, _ = F(u, v); m.box(mat, su, sv, sz, x, y, z, ang)
def gable(m, F, mat, L, W, z, rise, over=0.7, side=0.6, ends=None):
    """gabled roof, ridge along u; z = eave height at the wall line"""
    hl, hw = L / 2 + over, W / 2 + side; ze = z - side * rise / (W / 2); zr = z + rise
    for s in (-1, 1):
        m.poly(mat, [F(-hl, s * hw, ze), F(hl, s * hw, ze), F(hl, 0, zr), F(-hl, 0, zr)])
        if ends: m.poly(ends, [F(s * L / 2, -W / 2, z), F(s * L / 2, W / 2, z), F(s * L / 2, 0, zr)])
def pyramid(m, F, mat, n, r, z, rise, r_top=0.0, rot=0.0):
    """n-sided tiled roof: eave radius r at height z, up to r_top at z+rise"""
    P = lambda rr, k, zz: F(rr * math.cos(rot + 2 * math.pi * k / n), rr * math.sin(rot + 2 * math.pi * k / n), zz)
    for k in range(n):
        if r_top > 0.01: m.poly(mat, [P(r, k, z), P(r, k + 1, z), P(r_top, k + 1, z + rise), P(r_top, k, z + rise)])
        else: m.poly(mat, [P(r, k, z), P(r, k + 1, z), F(0, 0, z + rise)])
def text(m, mat, body, size, x, y, z, rz):
    """text as mesh inside the model's bmesh (so Level applies to it); faces the -Y direction rotated by rz"""
    cu = bpy.data.curves.new("t", "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.extrude = 0.03; cu.resolution_u = 2
    ob = bpy.data.objects.new("t", cu); bpy.context.scene.collection.objects.link(ob)
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    me.transform(Matrix.Translation((x, y, z)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X"))
    m._bm(mat).from_mesh(me); bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)

def walk(pts, step):
    """yield (x, y, angle, length) pieces of at most `step` metres along a polyline"""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0); n = max(1, math.ceil(L / step)); a = math.atan2(y1 - y0, x1 - x0)
        for i in range(n):
            t = (i + 0.5) / n; yield x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, a, L / n
def ribbon(m, mat, pts, w, h=0.08, z=0.0, step=5.0, edge=None):
    for x, y, a, L in walk(pts, step):
        m.box(mat, L + 0.6, w, h, x, y, z, a)
        if edge:
            F = frame(x, y, a)
            for s in (-1, 1): fbox(m, F, a, edge, L + 0.6, 0.18, h + 0.05, 0, s * (w / 2 + 0.05), z)
def lamp(m, x, y):
    m.cyl("steel", 0.07, 3.6, x, y, 0, 6); m.box("lamp", 0.34, 0.34, 0.4, x, y, 3.6); m.box("steel", 0.5, 0.5, 0.06, x, y, 4.0)
def bench(m, x, y, a):
    F = frame(x, y, a); fbox(m, F, a, "deck", 1.8, 0.5, 0.08, 0, 0, 0.42); fbox(m, F, a, "deck", 1.8, 0.08, 0.45, 0, 0.25, 0.5)
    for s in (-1, 1): fbox(m, F, a, "stone", 0.12, 0.5, 0.42, s * 0.75, 0, 0)

# ---------------------------------------------------------------- pieces
def gateway(m, x, y, a):
    """padippura: laterite plinth blocks either side of the way, timber posts, a broad hipped tile roof with a raised
    gabled upper tier over the opening; the path runs through along local v"""
    F = frame(x, y, a)
    with Level(m, G(x, y) + 0.1):
        for s in (-1, 1):
            fbox(m, F, a, "laterite", 3.6, 4.4, 1.3, s * 4.2, 0, -1.2)                    # raised seats (thinna)
            fbox(m, F, a, "white", 3.2, 0.3, 2.6, s * 4.2, 1.6, 0.1)                       # back wall
            for u in (2.55, 5.85):
                for v in (-1.9, 1.9): fbox(m, F, a, "timber", 0.26, 0.26, 3.3, s * u, v, 0.1)
            fbox(m, F, a, "timber", 3.6, 0.14, 0.14, s * 4.2, -1.9, 0.75)                  # charupadi rail
        fbox(m, F, a, "paver", 4.9, 6.0, 0.6, 0, 0, -0.5)                                 # threshold paving
        fbox(m, F, a, "timber", 12.2, 4.3, 0.22, 0, 0, 3.3)                               # wall plate
        hw, hd, ze, zt = 7.6, 3.6, 2.9, 4.7; tw, td = 3.4, 1.0                             # lower hipped skirt
        c = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]; t = [(-tw, -td), (tw, -td), (tw, td), (-tw, td)]
        for i in range(4):
            j = (i + 1) % 4; m.poly("tile", [F(*c[i], ze), F(*c[j], ze), F(*t[j], zt), F(*t[i], zt)])
        fbox(m, F, a, "white", 6.6, 1.9, 0.9, 0, 0, zt - 0.1)                              # upper-tier drum
        gable(m, frame(x, y, a), "tile", 6.8, 2.0, zt + 0.75, 1.5, over=0.9, side=1.0, ends="timber")
        fbox(m, F, a, "tile2", 8.8, 0.3, 0.14, 0, 0, zt + 2.2)
        for s in (-1, 1): xx, yy, _ = F(s * 3.6, 0); m.cyl("brass", 0.12, 0.7, xx, yy, zt + 2.3, 6, 0.02)   # finials
        fbox(m, F, a, "board", 5.6, 0.12, 0.8, 0, -2.25, 2.35)                             # name board over the opening
        xx, yy, _ = F(0, -2.34); text(m, "white", "SAROVARAM BIO PARK", 0.42, xx, yy, 2.6, a)

def pavilion(m, x, y, n=8, r=3.0, a=0.0, plinth=0.5, two_tier=True):
    """open tiled pavilion: stone plinth, timber posts with a seat rail, wide-eaved tile roof and finial"""
    F = frame(x, y, a); rot = math.pi / n
    with Level(m, G(x, y) + plinth):
        m.cyl("stone", r + 0.5, 3.0, x, y, -3.0, n * 2 if n > 4 else 4)
        if n == 4: pass
        for k in range(n):
            ang = rot + 2 * math.pi * k / n; px, py, _ = F(r * math.cos(ang), r * math.sin(ang))
            m.box("timber", 0.22, 0.22, 2.7, px, py, 0, a + ang)
            a2 = rot + 2 * math.pi * (k + 1) / n; qx, qy, _ = F(r * math.cos(a2), r * math.sin(a2))
            if k != 0: m.box("timber", math.hypot(qx - px, qy - py), 0.3, 0.1, (px + qx) / 2, (py + qy) / 2, 0.5, math.atan2(qy - py, qx - px))
            m.box("timber", math.hypot(qx - px, qy - py), 0.16, 0.2, (px + qx) / 2, (py + qy) / 2, 2.6, math.atan2(qy - py, qx - px))
        if two_tier:
            pyramid(m, F, "tile", n, r + 1.3, 2.35, 1.35, r * 0.5, rot); pyramid(m, F, "timber", n, r * 0.5, 3.7, 0.45, r * 0.5, rot)
            pyramid(m, F, "tile", n, r * 0.5 + 0.55, 4.0, 1.3, 0, rot); top = 5.3
        else: pyramid(m, F, "tile", n, r + 1.3, 2.35, 2.2, 0, rot); top = 4.55
        m.cyl("brass", 0.13, 0.7, x, y, top - 0.05, 6, 0.02)

def boardwalk(m, pts, w=2.4, h=1.0, rail=True):
    """timber deck on piles with post-and-rail handrails, in 3 m pieces so it follows the ground / water"""
    for i, (x, y, a, L) in enumerate(walk(pts, 3.0)):
        F = frame(x, y, a)
        m.box("deck" if i % 2 else "deck2", L + 0.35, w, 0.14, x, y, h, a)
        for s in (-1, 1):
            px, py, _ = F(0, s * (w / 2 - 0.15)); m.cyl("timber", 0.11, h + 1.2, px, py, -1.2, 6)
            if rail:
                fbox(m, F, a, "timber", 0.1, 0.1, 1.0, 0, s * (w / 2 - 0.06), h + 0.14)
                for z in (0.55, 1.0): fbox(m, F, a, "deck2", L + 0.35, 0.07, 0.09, 0, s * (w / 2 - 0.06), h + 0.14 + z)

def footbridge(m, p0, p1, w=3.2):
    """entrance bridge over the Conolly canal: level concrete deck, white balustrade, two piers"""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); a = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); F = frame(*p0, a)
    top = max(G(*p0), G(*p1)) + 0.5; n = math.ceil(L / 4)
    with Level(m, 0.0):
        for i in range(n):
            u = (i + 0.5) * L / n
            fbox(m, F, a, "concrete", L / n + 0.02, w, 0.4, u, 0, top - 0.4); fbox(m, F, a, "paver", L / n + 0.02, w - 0.5, 0.05, u, 0, top)
            for s in (-1, 1):
                for z in (0.5, 0.95): fbox(m, F, a, "white", L / n + 0.02, 0.12, 0.12, u, s * (w / 2 - 0.1), top + z)
        for i in range(int(L / 2) + 1):
            for s in (-1, 1): fbox(m, F, a, "white", 0.2, 0.2, 1.1, i * 2.0, s * (w / 2 - 0.1), top)
        for u in (L * 0.3, L * 0.7): fbox(m, F, a, "concrete", 0.7, w - 0.4, top + 2.2, u, 0, -2.6)

def theatre(m, x, y, a, r0=7.0, tiers=6):
    """open-air theatre: semicircular laterite seating tiers stepping up around a paved floor and a low stage"""
    F = frame(x, y, a); base = G(x, y) + 0.1; n = 14
    with Level(m, base):
        m.cyl("paver", r0, 3.0, x, y, -2.9, 20)                                            # orchestra floor
        for t in range(tiers):
            r = r0 + 0.5 + t * 1.1
            for k in range(n):
                ang = math.pi * (k + 0.5) / n; px, py, _ = F(r * math.cos(ang), r * math.sin(ang))
                m.box("laterite" if t % 2 else "stone", r * math.pi / n + 0.25, 1.12, 3.0 + 0.42 * (t + 1), px, py, -2.9, a + ang + math.pi / 2)
        fbox(m, F, a, "stone", 13.0, 6.0, 3.7, 0, -4.2, -2.9)                              # stage platform
        fbox(m, F, a, "white", 13.0, 0.35, 3.4, 0, -7.0, 0.8)                              # backdrop wall
        for s in (-1, 1):
            fbox(m, F, a, "white", 0.35, 2.4, 3.4, s * 6.3, -5.9, 0.8)
            for v in (-1.6,): fbox(m, F, a, "timber", 0.24, 0.24, 3.2, s * 6.2, v, 0.8)
        hw, v0, v1, ze, zr = 7.4, -7.8, -0.9, 4.0, 5.3                                     # lean-to tile roof over the stage
        m.poly("tile", [F(-hw, v1, ze), F(hw, v1, ze), F(hw, v0, zr), F(-hw, v0, zr)]); fbox(m, F, a, "timber", 14.0, 0.2, 0.2, 0, -1.6, 3.95)

def jetty(m, x, y, a):
    """boat jetty: tiled boathouse/ticket pavilion on the shore, timber pier out over the pond with a T-head, pedal boats"""
    F = frame(x, y, a)                                                                     # local u = out over the water
    with Level(m, G(*F(-6, 0)[:2]) + 0.4):
        cx, cy, _ = F(-6, 0); Fb = frame(cx, cy, a + math.pi / 2)
        m.box("stone", 9.0, 6.0, 3.0, cx, cy, -3.0, a + math.pi / 2)
        for u in (-4, -1.4, 1.4, 4):
            for v in (-2.5, 2.5): fbox(m, Fb, a + math.pi / 2, "timber", 0.24, 0.24, 2.9, u, v, 0)
        fbox(m, Fb, a + math.pi / 2, "white", 3.0, 2.6, 2.6, -2.6, 1.0, 0)                 # ticket room
        gable(m, Fb, "tile", 8.6, 5.4, 2.9, 1.7, over=1.0, side=1.0, ends="timber")
        fbox(m, Fb, a + math.pi / 2, "tile2", 10.8, 0.3, 0.14, 0, 0, 4.6)
    p = lambda u, v: F(u, v)[:2]
    boardwalk(m, [p(-1.5, 0), p(16, 0)], 2.6, 0.7); boardwalk(m, [p(17, -7), p(17, 7)], 3.0, 0.7, rail=False)
    for i, (u, v, r) in enumerate([(20.3, -5, 0.2), (20.5, -1.5, -0.15), (20.2, 2.2, 0.1), (20.6, 5.6, 0.3), (12, 3.4, 1.5), (9, -3.4, 1.7)]):
        bx, by = p(u, v); c = ("boat1", "boat2", "boat3")[i % 3]; Fb = frame(bx, by, a + r)
        fbox(m, Fb, a + r, c, 2.4, 1.5, 0.45, 0, 0, 0.0); fbox(m, Fb, a + r, "white", 1.2, 1.3, 0.3, -0.3, 0, 0.45)
        fbox(m, Fb, a + r, c, 1.5, 1.6, 0.06, -0.2, 0, 1.45)
        for s in (-1, 1): fbox(m, Fb, a + r, "steel", 0.05, 0.05, 1.0, 0.45, s * 0.7, 0.45); fbox(m, Fb, a + r, "steel", 0.05, 0.05, 1.0, -0.9, s * 0.7, 0.45)

# ---------------------------------------------------------------- layout (metres east, north of the origin)
BRIDGE = [(-389, 13), (-364, 33.5)]                                                       # mapped path crossing the canal
MAIN = [(-338, 13), (-110, -169), (-71, -148)]                                            # mapped path along the canal bank
INNER = [(-338, 13), (-331, 17), (-306, 10), (-257, -38), (-189, -92), (-194, -103)]
LOOP = [(-340, 52), (-316, 86), (-282, 118), (-248, 137), (-236, 150), (-239, 187), (-150, 232), (-141, 217), (-72, 172), (-57, 152), (-52, 118),
        (-58, 107), (-58, 93), (-53, 85), (-60, 72), (-72, 70), (-78, 63), (-115, 63), (-173, 77), (-186, 76), (-217, 90), (-220, 116), (-236, 129), (-242, 143)]
LINK1 = [(-364, 33.5), (-342, 12), (-338, 13)]                                            # mapped: bridge end to the main path
LINK2 = [(-338, 13), (-342, 30), (-340, 52)]                                              # guess: entrance to the loop trail
LINK3 = [(-150, -137), (-118, -108), (-88, -88), (-64, -79)]                              # guess: main path to the boardwalk
WALK = [(-64, -79), (-51, -72), (-48, -55), (-41, -35), (-58, -10), (-72, 12), (-45, 21), (-36, 19)]   # over the west arm of the wetland to the island
LINK4 = [(-36, 19), (-27, 13)]

def sarovaram():
    m = Model("sarovaram")
    footbridge(m, *BRIDGE)
    a = math.atan2(BRIDGE[1][1] - BRIDGE[0][1], BRIDGE[1][0] - BRIDGE[0][0])
    gateway(m, -360.5, 36.4, a + math.pi / 2)                                             # just inside the bridge, astride the way
    for x in range(-362, -333, 5):                                                        # paved forecourt
        for y in range(8, 34, 5): m.box("paver", 5.1, 5.1, 0.07, x, y, 0.0)
    with Level(m, G(-347, 36) + 0.2):                                                     # ticket counter beside the forecourt
        m.box("white", 5.0, 3.6, 5.6, -347, 36, -3.0, a); gable(m, frame(-347, 36, a), "tile", 5.0, 3.6, 2.6, 1.3, ends="white")
        fbox(m, frame(-347, 36, a), a, "glass", 2.2, 0.1, 1.0, 0, -1.83, 1.1)
    ribbon(m, "paver", LINK1, 3.4, edge="stone"); ribbon(m, "paver", MAIN, 3.2, edge="stone"); ribbon(m, "paver", INNER, 2.4, edge="stone")
    ribbon(m, "earth", LOOP, 1.8); ribbon(m, "earth", LINK2, 1.8); ribbon(m, "paver", LINK3, 2.2, edge="stone"); ribbon(m, "earth", LINK4, 2.0)
    ribbon(m, "paver", [(-257, -38), (-243, -22)], 2.4, edge="stone")                     # spur to the theatre
    for i, (x, y, an, L) in enumerate(walk(MAIN, 26.0)):                                  # lamps and benches along the canal walk
        F = frame(x, y, an); lamp(m, *F(0, 2.3 if i % 2 else -2.3)[:2])
        if i % 2 == 0: bx, by, _ = F(6, 2.4); bench(m, bx, by, an)
    for i, (x, y, an, L) in enumerate(walk(INNER[2:5], 30.0)): lamp(m, *frame(x, y, an)(0, 1.9)[:2])
    theatre(m, -232, -9, math.atan2(-22 + 9, -243 + 232) + math.pi / 2 + math.pi)          # stage on the far side from the spur
    boardwalk(m, WALK)
    with Level(m, G(-41, -35) + 1.0):                                                     # viewing deck half way along the boardwalk
        m.cyl("deck", 4.6, 0.16, -35.5, -33, 0.0, 8)
        for k in range(8): an = math.pi / 8 + k * math.pi / 4; m.cyl("timber", 0.12, 3.0, -35.5 + 4.2 * math.cos(an), -33 + 4.2 * math.sin(an), -3.0, 6)
    pavilion(m, -35.5, -33, 8, 3.2, plinth=1.16, two_tier=True)
    pavilion(m, -22, 9, 8, 3.4)                                                           # on the island
    pavilion(m, -226, -84, 4, 2.6, a=math.atan2(-182, 228), two_tier=False)               # beside the canal walk
    pavilion(m, -116, 57, 6, 2.8, two_tier=False)                                         # on the loop trail
    pavilion(m, -300, -4, 4, 2.4, a=0.6, two_tier=False)
    sh = math.atan2(56, 97)                                                               # pond shore direction at the path end
    jetty(m, -66, -153.5, sh - math.pi / 2)
    ribbon(m, "paver", [(-71, -148), (-73, -147.5)], 3.2)
    m.finish()

sarovaram()
