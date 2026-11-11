"""Kallai River timber yards: the Kallai road bridge + the railway bridge beside it, the open-sided sawmill sheds on
both banks (on their mapped Overture footprints), log stacks on the bank and log rafts at the water's edge.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_kallai.py -- <out_dir>

Model space: metres, +X east, +Y north, Z up. Origin = grid (x=-801.2, n=1410.5), in the river just east of the bridge.
The site is a river valley (banks ~5-10 m above the water in the project's terrain), so the model is meant to be placed
with "drape": true (src/models.js adds max(terrain, y-1.5) to every vertex). Loose things (logs, yard, rafts) are simply
modelled on z=0 and follow the ground. Things that must stay level (bridges, sheds) are built inside `Level(...)`, which
pre-subtracts the terrain height under each vertex so they come out level after draping.
Layout source: Overture water / segments / buildings (data/raw/*.parquet) converted with geo.to_xy; roof colours and
shed positions cross-checked against Google satellite imagery."""
import sys, os, math, json, random
import bmesh
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_lib import Model, COL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OX, OY, FLOOR = -801.2, 1410.5, 0.0          # origin in grid metres; FLOOR = place.json y - 1.5
COL.update({
    "rust": (0x9C, 0x58, 0x38), "rust2": (0x74, 0x44, 0x30), "sheet": (0x8E, 0x80, 0x74), "oldtile": (0x86, 0x4A, 0x36),
    "log": (0x5E, 0x42, 0x2E), "log2": (0x7E, 0x5C, 0x40), "cut": (0xD6, 0xB3, 0x7C), "plank": (0x6A, 0x4E, 0x38),
    "earth": (0x7E, 0x64, 0x4C), "asphalt": (0x3E, 0x3E, 0x42), "stone": (0x77, 0x70, 0x66), "girder": (0x5C, 0x38, 0x2E),
    "steel": (0x4A, 0x48, 0x48), "ballast": (0x6E, 0x6A, 0x66), "lamp": (0xF6, 0xEE, 0xC8),
})

# ---------------------------------------------------------------- shared helpers
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
def gable(m, F, mat, L, W, z, rise, over=0.7, side=0.6, ends=None, patches=None, rnd=None):
    """gabled roof, ridge along u; z = eave height at the wall line"""
    hl, hw = L / 2 + over, W / 2 + side; ze = z - side * rise / (W / 2); zr = z + rise
    for s in (-1, 1):
        m.poly(mat, [F(-hl, s * hw, ze), F(hl, s * hw, ze), F(hl, 0, zr), F(-hl, 0, zr)])
        if patches:
            for k in range(patches[1]):
                u0 = rnd.uniform(-hl, hl - 3); du = rnd.uniform(1.5, 3.0); a = rnd.uniform(0.05, 0.6); b = a + rnd.uniform(0.2, 0.35)
                P = lambda u, t: F(u, s * hw * (1 - t), ze + (zr - ze) * t + 0.05)
                m.poly(patches[0][k % len(patches[0])], [P(u0, a), P(u0 + du, a), P(u0 + du, b), P(u0, b)])
        if ends: m.poly(ends, [F(s * L / 2, -W / 2, z), F(s * L / 2, W / 2, z), F(s * L / 2, 0, zr)])
def log(m, mat, x, y, z, ang, L, r, seg=8, ends=None):
    M = Matrix.Translation((x, y, z)) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")
    bmesh.ops.create_cone(m._bm(mat), cap_ends=True, segments=seg, radius1=r, radius2=r * 0.88, depth=L, matrix=M)
    if ends:
        for s, rr in ((-1, r), (1, r * 0.88)):
            bmesh.ops.create_circle(m._bm(ends), cap_ends=True, segments=seg, radius=rr * 0.86, matrix=M @ Matrix.Translation((0, 0, s * (L / 2 + 0.015))))

def rect_frame(rect):
    (x0, y0), (x1, y1), (x2, y2), _ = rect
    cx, cy = (x0 + x2) / 2, (y0 + y2) / 2
    a, b = (x1 - x0, y1 - y0), (x2 - x1, y2 - y1); la, lb = math.hypot(*a), math.hypot(*b)
    if la >= lb: L, W, ang = la, lb, math.atan2(a[1], a[0])
    else: L, W, ang = lb, la, math.atan2(b[1], b[0])
    return cx, cy, L, W, ang
def base_of(rect, cx, cy):
    return (G(cx, cy) + max(G(x, y) for x, y in rect)) / 2

# ---------------------------------------------------------------- pieces
ROOFS = ["rust", "oldtile", "rust2", "sheet", "rust", "rust2", "oldtile"]
def shed(m, rect, k, bays=1, eave=3.7):
    """open-sided sawmill shed: timber posts, tie beams, low-pitched gabled sheet/tile roof, plank wall at the land end"""
    rnd = random.Random(k * 7 + 3)
    cx, cy, L, W, ang = rect_frame(rect); F = frame(cx, cy, ang)
    end = 1 if abs(F(L / 2, 0)[1]) > abs(F(-L / 2, 0)[1]) else -1            # the end farther from the river is walled
    wb = W / bays
    with Level(m, base_of(rect, cx, cy)):
        m.box("earth", L + 1.4, W + 1.4, 4.0, cx, cy, -3.9, ang)               # earth/laterite plinth (runs down into the bank)
        n = max(2, round(L / 4.6)) + 1
        for i in range(n):
            u = -L / 2 + 0.3 + i * (L - 0.6) / (n - 1)
            for b in range(bays + 1): fbox(m, F, ang, "timber", 0.24, 0.24, eave, u, -W / 2 + 0.25 + b * (W - 0.5) / bays, 0.1)
            fbox(m, F, ang, "timber", 0.16, W - 0.3, 0.2, u, 0, eave - 0.1)   # tie beam
        for b in range(bays):
            vc = -W / 2 + wb * (b + 0.5); Fb = frame(*F(0, vc)[:2], ang); rise = wb * 0.27
            mat = ROOFS[(k + b) % len(ROOFS)]
            gable(m, Fb, mat, L, wb, eave + 0.1, rise, over=0.9, side=0.55 if bays == 1 else 0.12, ends=None,
                  patches=(["rust2", "sheet", "rust"], 3 if L > 14 else 2), rnd=rnd)
            fbox(m, Fb, ang, "rust2", L + 1.8, 0.4, 0.1, 0, 0, eave + 0.1 + rise - 0.03)                        # ridge cap
            m.poly("plank", [Fb(end * L / 2, -wb / 2, eave), Fb(end * L / 2, wb / 2, eave), Fb(end * L / 2, 0, eave + rise)])
            # what is under the roof: a log on the saw carriage, stacks of sawn planks, a couple of logs waiting
            if L > 12:
                fbox(m, Fb, ang, "steel", 4.5, 1.1, 0.7, -end * L * 0.12, 0, 0.1)
                x, y, _ = Fb(-end * L * 0.12, 0); log(m, "log2", x, y, 1.15, ang, 4.2, 0.36, 8, "cut")
            for j in range(2 if L > 14 else 1):
                u = end * (L * 0.2 + j * L * 0.17); v = (wb * 0.22) * (1 if (j + b) % 2 else -1)
                fbox(m, Fb, ang, "cut", 3.6, 1.2, 0.5 + 0.35 * ((j + k) % 3), u, v, 0.1)
            for j in range(2):
                x, y, _ = Fb(-end * (L / 2 - 2.8 - rnd.random()), (j - 0.5) * 1.1 + rnd.uniform(-.3, .3))
                log(m, "log" if j else "log2", x, y, 0.45, ang + rnd.uniform(-.08, .08), rnd.uniform(3.5, 5), 0.34, 8, "cut")
        fbox(m, F, ang, "plank", 0.14, W - 0.3, eave, end * (L / 2 - 0.1), 0, 0.1)                              # plank end wall

def house(m, rect, k):
    cx, cy, L, W, ang = rect_frame(rect); F = frame(cx, cy, ang)
    with Level(m, base_of(rect, cx, cy)):
        m.box(("white", "cream", "grey")[k % 3], L, W, 6.0, cx, cy, -3.0, ang)
        gable(m, F, ("tile", "oldtile", "sheet")[k % 3], L, W, 3.0, W * 0.3, over=0.5, side=0.6, ends="white")

def stack(m, cx, cy, ang, nb=4, L=6.5, r=0.38, seed=0):
    """pyramid of logs on the bank"""
    rnd = random.Random(seed); F = frame(cx, cy, ang)
    for row in range(nb):
        for i in range(nb - row):
            rr = r * rnd.uniform(0.88, 1.08); v = (i - (nb - row - 1) / 2) * 2 * r
            x, y, _ = F(rnd.uniform(-0.5, 0.5), v)
            log(m, "log" if (i + row + seed) % 3 else "log2", x, y, r + row * r * 1.72, ang + rnd.uniform(-0.03, 0.03), L * rnd.uniform(0.85, 1.05), rr, 8, "cut")

def raft(m, cx, cy, ang, n=12, L=6.0, seed=0):
    """logs floating side by side, tethered at the bank"""
    rnd = random.Random(seed + 100); F = frame(cx, cy, ang)
    for i in range(n):
        x, y, _ = F(rnd.uniform(-0.7, 0.7), (i - (n - 1) / 2) * 0.66)
        log(m, "log" if (i + seed) % 4 else "log2", x, y, 0.1, ang + rnd.uniform(-0.035, 0.035), L * rnd.uniform(0.8, 1.1), rnd.uniform(0.27, 0.34), 6)

def interp(pts, x):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1: return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[0][1] if x < pts[0][0] else pts[-1][1]

# ---------------------------------------------------------------- layout data (metres east, north of the origin)
NBANK = [(-86, 0), (-37, 22), (-13, 24), (20, 33), (32, 44), (51, 38), (130, 57)]      # north bank of the river polygon
SBANK = [(-47, -46), (-13, -31), (9, -22), (26, -21), (81, -14), (130, 3)]             # south bank
# Overture building footprints (minimum rotated rectangles) whose centre lies in the removal rectangle (rx=82, rz=92)
SHEDS = [  # (rect, bays)
    ([(34.0, -26.6), (59.5, -73.7), (29.9, -89.7), (4.4, -42.6)], 4),       # big multi-bay mill on the south bank
    ([(13.8, 67.2), (18.5, 46.6), (5.3, 43.6), (0.6, 64.2)], 1),            # row of sheds on the north bank, east of the bridge
    ([(0.6, 64.2), (5.3, 43.6), (-7.0, 40.8), (-11.7, 61.4)], 1),
    ([(65.3, -63.1), (58.4, -67.0), (43.1, -40.3), (49.9, -36.4)], 1),
    ([(34.3, 46.7), (30.4, 66.6), (36.9, 67.9), (40.8, 47.9)], 1),
    ([(20.0, 68.6), (24.9, 47.4), (18.7, 45.9), (13.8, 67.2)], 1),
    ([(25.2, 69.8), (29.9, 49.2), (24.8, 48.1), (20.1, 68.6)], 1),
    ([(-19.7, 41.9), (-23.5, 58.7), (-18.1, 59.9), (-14.3, 43.1)], 1),
    ([(-13.9, 41.3), (-16.6, 53.1), (-10.1, 54.6), (-7.4, 42.8)], 1),
    ([(69.1, 88.4), (74.7, 89.7), (81.0, 62.2), (75.4, 60.9)], 1),          # second cluster further east
    ([(69.9, 85.0), (75.4, 60.9), (70.6, 59.8), (65.1, 83.9)], 1),
    ([(65.6, 81.7), (69.4, 64.9), (63.2, 63.5), (59.4, 80.2)], 1),
    ([(54.5, 77.1), (57.9, 62.3), (50.5, 60.6), (47.1, 75.4)], 1),
    ([(57.9, 62.3), (54.5, 77.1), (59.8, 78.3), (63.2, 63.5)], 1),
    ([(42.9, -24.1), (50.0, -36.4), (43.1, -40.3), (36.1, -28.0)], 1),
]
HOUSES = [
    [(-16.7, 82.8), (-3.1, 84.3), (-1.8, 72.3), (-15.4, 70.8)], [(-22.5, 85.4), (-34.6, 83.0), (-36.5, 92.7), (-24.4, 95.1)],
    [(-46.9, 93.0), (-38.6, 78.8), (-43.3, 76.1), (-51.6, 90.2)], [(-6.3, 38.0), (1.8, 39.9), (3.2, 33.9), (-4.9, 32.0)],
    [(-38.9, 77.6), (-32.1, 81.9), (-29.0, 77.0), (-35.8, 72.7)], [(43.2, 67.6), (41.7, 74.2), (47.1, 75.4), (48.7, 68.8)],
    [(-29.7, 78.2), (-23.7, 80.1), (-22.0, 74.4), (-28.0, 72.6)], [(-7.9, 87.0), (-17.1, 86.0), (-17.5, 89.6), (-8.3, 90.6)],
    [(-31.5, 83.1), (-24.9, 84.8), (-23.7, 80.5), (-30.4, 78.7)], [(-17.1, 73.5), (-20.6, 73.1), (-21.4, 79.5), (-17.8, 79.9)],
]

def road_bridge(m):
    """Kallai Road bridge on the mapped road line: flat concrete girder deck on wall piers, post-and-rail parapets"""
    dx, dy = 0.4408, -0.8976; ang = math.atan2(dy, dx); F = frame(-63.0, 36.0, ang)      # u = metres along the road, southbound
    t0, t1, top = -6.0, 126.0, 7.9; n = 22; seg = (t1 - t0) / n
    with Level(m, 0.0):
        for i in range(n):
            u = t0 + (i + 0.5) * seg
            fbox(m, F, ang, "concrete", seg + 0.02, 11.0, 0.5, u, 0, top - 0.5)
            fbox(m, F, ang, "asphalt", seg + 0.02, 7.6, 0.06, u, 0, top)
            for s in (-1, 1):
                fbox(m, F, ang, "grey", seg + 0.02, 1.5, 0.2, u, s * 4.7, top)                     # footpaths
                for z in (0.55, 1.0): fbox(m, F, ang, "white", seg + 0.02, 0.14, 0.14, u, s * 5.3, top + z)
            for v in (-3.6, 0, 3.6): fbox(m, F, ang, "concrete", seg + 0.02, 0.55, 1.0, u, v, top - 1.5)   # girders
        for i in range(int((t1 - t0) / 3) + 1):
            for s in (-1, 1): fbox(m, F, ang, "white", 0.26, 0.26, 1.2, t0 + i * 3, s * 5.3, top)
        for u in (10, 24, 38, 52, 67, 81, 95, 109):                                              # piers (water between 24 and 81)
            fbox(m, F, ang, "concrete", 1.3, 9.0, 9.0, u, 0, -2.6); fbox(m, F, ang, "concrete", 1.9, 10.6, 0.5, u, 0, top - 2.0)
            for s in (-1, 1): x, y, _ = F(u, s * 4.5); m.cyl("concrete", 0.65, 9.0, x, y, -2.6, 8)
        for u in (t0 + 1, t1 - 1): fbox(m, F, ang, "stone", 2.4, 11.6, 6.0, u, 0, top - 6.5)       # abutments
        for i, u in enumerate((8, 38, 68, 98)):                                                   # street lamps
            s = 1 if i % 2 else -1; x, y, _ = F(u, s * 5.0)
            m.cyl("steel", 0.08, 6.5, x, y, top, 6); fbox(m, F, ang, "steel", 0.1, 1.6, 0.1, u, s * 4.3, top + 6.4)
            fbox(m, F, ang, "lamp", 0.3, 0.7, 0.12, u, s * 3.7, top + 6.3)

def rail_bridge(m):
    """railway bridge immediately west of the road bridge: plate-girder spans on stone piers, two tracks"""
    dx, dy = 0.4177, -0.9097; ang = math.atan2(dy, dx); F = frame(-135.0, 159.0, ang)
    s0, s1, top = 136.0, 268.0, 7.9; n = 22; seg = (s1 - s0) / n
    with Level(m, 0.0):
        for i in range(n):
            u = s0 + (i + 0.5) * seg
            fbox(m, F, ang, "steel", seg + 0.02, 8.8, 0.35, u, 0, top - 0.55)
            for v in (-2.1, 2.1):
                fbox(m, F, ang, "ballast", seg + 0.02, 2.7, 0.14, u, v, top - 0.2)
                for r in (-0.84, 0.84): fbox(m, F, ang, "steel", seg + 0.02, 0.1, 0.14, u, v + r, top - 0.06)
            for s in (-1, 1): fbox(m, F, ang, "girder", seg + 0.02, 0.22, 1.9, u, s * 4.5, top - 1.3)
        for i in range(int((s1 - s0) / 3) + 1):
            for s in (-1, 1): fbox(m, F, ang, "girder", 0.12, 0.42, 1.8, s0 + i * 3, s * 4.5, top - 1.25)   # web stiffeners
        for u in (150, 168, 186, 204, 222, 240, 258):
            fbox(m, F, ang, "stone", 2.2, 9.6, 9.6, u, 0, -2.6); fbox(m, F, ang, "stone", 2.8, 10.4, 0.5, u, 0, top - 1.8)
            for s in (-1, 1): x, y, _ = F(u, s * 4.8); m.cyl("stone", 1.1, 9.6, x, y, -2.6, 6)
        for u in (s0 + 1, s1 - 1): fbox(m, F, ang, "stone", 2.6, 10.4, 6.5, u, 0, top - 7.0)

def kallai():
    m = Model("kallai")
    road_bridge(m); rail_bridge(m)
    for k, (rect, bays) in enumerate(SHEDS): shed(m, rect, k, bays)
    for k, rect in enumerate(HOUSES): house(m, rect, k)
    # trodden-earth timber yard between the sheds and the water (5 m tiles so it follows the bank)
    for x in range(-30, 46, 5):
        y = interp(NBANK, x) + 1.5
        while y < 45.5: m.box("earth", 5.1, 5.1, 0.07, x, y + 2.5, 0.0); y += 5
    for x in range(-24, 41, 5):
        y = interp(SBANK, x) - 1.5; lim = -44 + (x - 4) * 0.55 if x > 4 else -44 - (4 - x) * 0.2
        while y > lim: m.box("earth", 5.1, 5.1, 0.07, x, y - 2.5, 0.0); y -= 5
    # log stacks on the bank, long axis roughly parallel to the water
    for i, (x, y, a, nb) in enumerate([(-27, 31.5, 0.25, 4), (-16, 34.5, 0.2, 3), (9, 37.5, 0.3, 4), (21, 41, 0.5, 3), (45, 44.5, -0.2, 4),
                                       (59, 49, 0.15, 5), (74, 51.5, 0.2, 4), (-4, -34, 0.45, 4), (-21, -43, 0.42, 5), (14, -29.5, 0.1, 3), (68, -24, 0.15, 4)]):
        stack(m, x, y, a, nb, 6.5 if i % 2 else 7.5, seed=i)
    for i, (x, y, a) in enumerate([(-10, 32, 1.2), (30, 47.5, 1.9), (-12, -37, 2.0), (52, 46, 1.4), (2, -30, 1.0)]):   # stray single logs
        log(m, "log2" if i % 2 else "log", x, y, 0.4, a, 6.0, 0.36, 8, "cut")
    # rafts of floating logs along both banks
    for i, (x, off, n) in enumerate([(-30, 7, 12), (-18, 8, 16), (-4, 7, 14), (10, 9, 12), (24, 13, 10), (42, 12, 16), (58, 9, 14), (76, 9, 12), (94, 8, 10)]):
        a = math.atan2(interp(NBANK, x + 5) - interp(NBANK, x - 5), 10) * 0.6
        raft(m, x, interp(NBANK, x) - off - n * 0.33, a, n, 6.5, i)
    for i, (x, off, n) in enumerate([(-22, 7, 12), (-6, 8, 14), (12, 7, 16), (30, 8, 12), (50, 7, 14), (70, 8, 10)]):
        a = math.atan2(interp(SBANK, x + 5) - interp(SBANK, x - 5), 10) * 0.6
        raft(m, x, interp(SBANK, x) + off + n * 0.33, a, n, 6.5, i + 20)
    # a loose drifting raft mid-river and two country boats pulled up at the yard
    raft(m, 28, 8, 0.25, 9, 6.0, 40)
    for x, y, a in ((2, 29.5, 0.3), (36, -17.5, 0.1)):
        F = frame(x, y, a); fbox(m, F, a, "timber", 5.2, 1.1, 0.45, 0, 0, 0.05); fbox(m, F, a, "plank", 4.6, 0.8, 0.1, 0, 0, 0.46)
        for s in (-1, 1): fbox(m, F, a + s * 0.5, "timber", 1.3, 0.5, 0.42, s * 2.9, 0, 0.08)
    m.finish()

kallai()
