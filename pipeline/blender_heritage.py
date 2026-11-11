"""Mishkal Mosque (with Kuttichira tank edge) and Tali Temple (with its pond edge), from photo reference on mapped footprints.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_heritage.py -- <out_dir>
Model space: +X east, +Y north, Z up, metres, relative to each origin (local grid metres)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_lib import Model, COL, OUT

COL.update({
    "seagreen": (0x3D, 0xC4, 0xA2), "doorblue": (0x1E, 0x6E, 0xB4), "louvre": (0x58, 0xA6, 0x9A), "louvre2": (0x3E, 0x82, 0x78),
    "stone": (0xC8, 0xC2, 0xB4), "granite": (0x9C, 0x9A, 0x96), "laterite": (0xA8, 0x52, 0x38), "wood": (0x6A, 0x44, 0x2A),
    "gold": (0xD8, 0xA8, 0x3A), "copper": (0x8A, 0x5A, 0x34), "stripe": (0xB2, 0x32, 0x2A), "cobble": (0x9A, 0x92, 0x88),
    "lamp": (0xFF, 0xF1, 0xC4), "iron": (0x2A, 0x2C, 0x2E), "gableblue": (0x2C, 0x6F, 0xC0), "moss": (0x7C, 0x6A, 0x3E),
})

def seg(m, mat, a, b, width, h, z, O):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    m.box(mat, L + width * 0.1, width, h, (a[0] + b[0]) / 2 - O[0], (a[1] + b[1]) / 2 - O[1], z, math.atan2(dy, dx))

def tank_edge(m, ring, O, steps=4):
    """stepped stone ghats running down into a tank, following its mapped outline"""
    cx = sum(p[0] for p in ring) / len(ring); cy = sum(p[1] for p in ring) / len(ring)
    for s in range(steps):
        k = 1 + 0.035 * (steps - s)
        pts = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in ring]
        for a, b in zip(pts, pts[1:] + pts[:1]): seg(m, "stone", a, b, 1.6, 0.35, 0.15 + (steps - s - 1) * -0.0 + (steps - s) * 0.3 - 0.9, O)

def place(name, O, rx, rz, extra=()):
    json.dump({"f": f"models/{name}.glb", "x": O[0], "n": O[1], "deg": 0, "rx": rx, "rz": rz}, open(os.path.join(OUT, name + ".place.json"), "w"))
    for i, e in enumerate(extra): json.dump(e, open(os.path.join(OUT, f"{name}_clear{i}.place.json"), "w"))

def ring_arches(m, w, d, z, n_long, n_short, door_h=3.0):
    """alternating blue arched doors and white blind niches round all four walls"""
    for side, (count, length, fixed, ry) in enumerate([(n_long, w, -d / 2, 0.0), (n_short, d, w / 2, math.pi / 2), (n_long, w, d / 2, math.pi), (n_short, d, -w / 2, -math.pi / 2)]):
        for i in range(count):
            t = -length / 2 + (i + 0.5) * length / count
            x, y = [(t, fixed), (fixed, t), (-t, fixed), (fixed, -t)][side]
            if i % 2 == 0: m.arch(x, y, z, 1.7, door_h, ry, trim="frame", fill="doorblue")
            else: m.arch(x, y, z + 0.5, 1.25, door_h - 1.0, ry, trim="frame", fill="frame")

# ---------------------------------------------------------------- Mishkal Mosque
# Reference: sea-green ground floor on a three-step stone plinth, ringed by white-trimmed arches (blue doors alternating
# with white blind niches); a tiled lean-to roof all round; a timber-railed gallery above; then two set-back storeys of
# blue-green wooden louvres, each under its own tiled roof; hipped tile roof on top. No minarets.
def mishkal(W=29.6, D=24.1):
    O = (-2060.6, 2278.8); m = Model("mishkal")
    for i in range(3): m.box("stone", W + 4.4 - i * 1.3, D + 4.4 - i * 1.3, 0.32, 0, 0, i * 0.32)
    z = 0.96
    m.box("seagreen", W, D, 4.3, 0, 0, z); m.box("frame", W + 0.12, D + 0.12, 0.3, 0, 0, z + 4.0)
    ring_arches(m, W, D, z, 12, 10)
    z1 = z + 4.3
    m.skirt("tile", W - 2.4, D - 2.4, 0, 0, z1 + 1.3, out=3.3, drop=1.6); m.box("frame", W + 2.0, D + 2.0, 0.14, 0, 0, z1 - 0.34)   # lean-to roof + white gutter line
    w2, d2 = W - 2.6, D - 2.6                                                                    # timber gallery storey
    m.box("wood", w2, d2, 3.0, 0, 0, z1 + 1.1)
    for i in range(int(w2 / 1.6) + 1):
        for y in (-d2 / 2 - 0.05, d2 / 2 + 0.05): m.box("timber", 0.14, 0.14, 3.0, -w2 / 2 + i * 1.6, y, z1 + 1.1)
    for i in range(int(d2 / 1.6) + 1):
        for x in (-w2 / 2 - 0.05, w2 / 2 + 0.05): m.box("timber", 0.14, 0.14, 3.0, x, -d2 / 2 + i * 1.6, z1 + 1.1)
    m.box("timber", w2 + 0.3, d2 + 0.3, 0.12, 0, 0, z1 + 2.05)                                    # gallery rail
    z2 = z1 + 4.1
    m.skirt("tile", w2 - 2.0, d2 - 2.0, 0, 0, z2 + 1.2, out=3.0, drop=1.5)
    for k, (inset, h) in enumerate([(5.6, 3.0), (10.4, 2.8)]):                                    # two louvred storeys
        w3, d3 = W - inset, D - inset; zz = z2 + 1.0 + k * 4.0
        m.box("louvre", w3, d3, h, 0, 0, zz)
        for j in range(int(h / 0.3)): m.box("louvre2", w3 + 0.1, d3 + 0.1, 0.06, 0, 0, zz + 0.15 + j * 0.3)
        for i in range(int(w3 / 2.2) + 1):
            for y in (-d3 / 2 - 0.06, d3 / 2 + 0.06): m.box("timber", 0.16, 0.16, h, -w3 / 2 + i * w3 / int(w3 / 2.2), y, zz)
        if k == 0: m.skirt("tile", w3 - 1.8, d3 - 1.8, 0, 0, zz + h + 1.1, out=2.8, drop=1.4)
        else: m.hip("tile", w3 + 3.4, d3 + 3.4, 0, 0, zz + h, 3.4)
    m.box("cobble", 22, D + 14, 0.12, W / 2 + 13, -2, 0)                                          # paved forecourt on the east
    m.box("white", 9, 14, 3.4, W / 2 + 19, 6, 0); m.hip("tile", 10.5, 15.5, W / 2 + 19, 6, 3.4, 2.2)   # ablution block
    tank_edge(m, [(-2118.2, 2225.2), (-2093.2, 2100.5), (-2040.6, 2111.2), (-2066.1, 2234.5)], O)
    m.finish(); place("mishkal", O, 17, 14.5)

# ---------------------------------------------------------------- Tali Temple
# Reference: a walled Kerala cloister (red-and-white striped walls, tiled roofs) round an inner court with a two-tier
# copper-roofed sanctum; on the east a two-tier tiled gateway with a blue-and-white gable, grey stone pillars and a brass
# lamp pillar; the temple pond, stone-stepped, to the north.
def tali(W=46.7, D=40.3):
    O = (-856.0, 2506.8); m = Model("tali"); wing = 6.0
    for cx, cy, w, d in [(0, -D / 2 + wing / 2, W, wing), (0, D / 2 - wing / 2, W, wing), (-W / 2 + wing / 2, 0, wing, D), (W / 2 - wing / 2, 0, wing, D)]:
        m.box("frame", w, d, 3.4, cx, cy, 0.5); m.box("granite", w + 0.4, d + 0.4, 0.5, cx, cy, 0)
        m.hip("tile", w + 2.2, d + 2.2, cx, cy, 3.9, 2.6)
    for i in range(int(W / 1.3)):                                                                 # red stripes on the outer walls
        x = -W / 2 + 0.65 + i * 1.3
        if i % 2 == 0:
            for y in (-D / 2 - 0.03, D / 2 + 0.03): m.box("stripe", 0.65, 0.08, 3.2, x, y, 0.6)
    for i in range(int(D / 1.3)):
        y = -D / 2 + 0.65 + i * 1.3
        if i % 2 == 0:
            for x in (-W / 2 - 0.03, W / 2 + 0.03): m.box("stripe", 0.08, 0.65, 3.2, x, y, 0.6)
    m.box("cobble", W - 2 * wing, D - 2 * wing, 0.15, 0, 0, 0)                                    # inner court
    m.box("granite", 12, 12, 1.0, -3, 0, 0.15); m.box("laterite", 10, 10, 4.2, -3, 0, 1.15)       # sanctum, two tiers
    m.hip("copper", 14.5, 14.5, -3, 0, 5.35, 2.6); m.box("laterite", 6.4, 6.4, 2.4, -3, 0, 7.3)
    m.hip("copper", 9.6, 9.6, -3, 0, 9.7, 4.4); m.cyl("gold", 0.3, 1.6, -3, 0, 14.0, 8, 0.05)
    m.box("granite", 6, 6, 0.8, 8, 0, 0.15)                                                       # pillared hall in front of the sanctum
    for dx in (-2.5, 2.5):
        for dy in (-2.5, 2.5): m.box("wood", 0.4, 0.4, 3.0, 8 + dx, dy, 0.95)
    m.hip("tile", 8.2, 8.2, 8, 0, 3.95, 2.6)
    m.box("laterite", 5, 5, 3.2, -8, 9.5, 0.15); m.hip("copper", 7, 7, -8, 9.5, 3.35, 2.4)       # second, smaller shrine
    gx = W / 2 + 2.0                                                                              # east gateway
    m.box("granite", 9, 12, 0.9, gx, 0, 0)
    for dy in (-4.6, -1.6, 1.6, 4.6): m.box("granite", 0.55, 0.55, 3.6, gx + 3.6, dy, 0.9);
    m.box("frame", 5, 11, 3.6, gx - 1.5, 0, 0.9)
    m.hip("tile", 12.5, 15, gx, 0, 4.5, 2.4); m.box("stripe", 6.5, 9, 2.6, gx - 0.5, 0, 6.2); m.hip("tile", 10, 12.5, gx - 0.5, 0, 8.8, 3.0)
    m.poly("gableblue", [(gx + 6.4, -3.6, 4.6), (gx + 6.4, 3.6, 4.6), (gx + 5.2, 0, 8.4)])       # blue-and-white gable over the door
    m.box("frame", 0.12, 5.2, 0.9, gx + 6.3, 0, 4.7); m.text("stripe", "TALI MAHA KSHETRAM", 0.36, gx + 6.4, 0, 4.98, ry=math.pi / 2)
    m.cyl("gold", 0.22, 6.5, gx + 11, 0, 0, 10, 0.12); m.cyl("gold", 0.7, 0.25, gx + 11, 0, 0, 12)   # brass lamp pillar
    for k in range(5): m.cyl("gold", 0.55 - k * 0.07, 0.08, gx + 11, 0, 1.6 + k * 1.0, 12)
    m.cyl("gold", 0.16, 13.0, W / 2 - wing - 3, 0, 0.15, 8, 0.1)                                  # flagstaff inside the gate
    m.box("frame", 23, 20, 3.6, 44.5, 24, 0.3); m.hip("tile", 25, 22, 44.5, 24, 3.9, 3.0)        # hall north-east of the gate
    pond = [(-884.3, 2663.1), (-882.3, 2561.9), (-809.3, 2563.3), (-811.3, 2664.5)]
    tank_edge(m, pond, O)
    m.box("frame", 30, 7, 5.6, -846 - O[0], 2556.5 - O[1], 0.2); m.hip("tile", 32, 9, -846 - O[0], 2556.5 - O[1], 5.8, 2.4)   # long tiled bath-house on the pond's south bank
    for i in range(10): m.window(-846 - O[0] - 13 + i * 2.9, 2556.5 - O[1] + 3.5, 3.4, 1.0, 1.2, ry=math.pi, shutters=False, frame="wood")
    m.finish(); place("tali", O, 25, 22, extra=[{"x": -811.5, "n": 2530.7, "rx": 13, "rz": 12}, {"x": -843.8, "n": 2540.4, "rx": 17, "rz": 6}])

mishkal(); tali()
