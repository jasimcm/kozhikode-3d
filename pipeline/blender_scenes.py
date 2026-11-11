"""Kozhikode Beach front, Mananchira Square and SM Street: street-level detail laid out on mapped geometry.
Layout comes from Overture (pond outline, maidan outline, road centre-lines); look comes from satellite/photo reference.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_scenes.py -- <out_dir>
Model space: +X east, +Y north, Z up, metres, relative to each scene's origin (local grid metres given below)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_lib import Model, COL, OUT

COL.update({
    "stone": (0xC8, 0xC2, 0xB4), "granite": (0x9C, 0x9A, 0x96), "laterite": (0xA8, 0x52, 0x38), "lawn": (0x5E, 0x9E, 0x42),
    "lamp": (0xFF, 0xF1, 0xC4), "iron": (0x2A, 0x2C, 0x2E), "wood": (0x7A, 0x52, 0x30), "cobble": (0x8C, 0x7F, 0x74),
    "aw1": (0xD9, 0x4F, 0x3B), "aw2": (0x2F, 0x7F, 0xB8), "aw3": (0xE9, 0xB0, 0x3C), "aw4": (0x3F, 0x9A, 0x6A), "aw5": (0xF2, 0xEE, 0xE4),
    "bronze": (0x6B, 0x4E, 0x2E), "gate": (0x2F, 0x6B, 0x4A), "sand": (0xD9, 0xC4, 0x96),
})
AW = ["aw1", "aw2", "aw3", "aw4", "aw5"]

def seg(m, mat, a, b, width, h, z=0.0, o=(0, 0)):
    """box running from a to b (local grid metres), given width and height"""
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    m.box(mat, L + width * 0.1, width, h, (a[0] + b[0]) / 2 - o[0], (a[1] + b[1]) / 2 - o[1], z, math.atan2(dy, dx))

def along(line, step, offset=0.0):
    """points every `step` metres along a polyline, shifted `offset` to the left of travel; yields (x, y, heading)"""
    carry = 0.0
    for a, b in zip(line, line[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; d = carry
        while d < L:
            yield a[0] + ux * d - uy * offset, a[1] + uy * d + ux * offset, math.atan2(dy, dx)
            d += step
        carry = d - L

def lamp(m, x, y, h=5.0, arms=1):
    m.cyl("iron", 0.07, h, x, y, 0, 6); m.cyl("iron", 0.16, 0.5, x, y, 0, 6)
    if arms == 2:
        for s in (-1, 1): m.box("iron", 0.9, 0.05, 0.05, x + s * 0.45, y, h - 0.3); m.cyl("lamp", 0.2, 0.32, x + s * 0.85, y, h - 0.25, 8)
    m.cyl("lamp", 0.24, 0.38, x, y, h, 8)

def place(name, origin, rx=1, rz=1):
    json.dump({"f": f"models/{name}.glb", "x": origin[0], "n": origin[1], "deg": 0, "rx": rx, "rz": rz},
              open(os.path.join(OUT, name + ".place.json"), "w"))

# ---------------------------------------------------------------- Mananchira
def mananchira():
    O = (-1636.5, 3264.4)
    pond = [(-1711.1, 3326.1), (-1689.5, 3184.7), (-1562.3, 3203.7), (-1583.3, 3343.0)]
    maidan = [(-1545.7, 3218.6), (-1522.8, 3099.6), (-1464.4, 3107.9), (-1439.7, 3133.6), (-1446.1, 3189.1), (-1483.5, 3227.9)]
    m = Model("mananchira"); rel = lambda p: (p[0] - O[0], p[1] - O[1])
    ring = pond + [pond[0]]
    for a, b in zip(ring, ring[1:]):
        seg(m, "laterite", a, b, 0.9, 1.0, 0, O); seg(m, "stone", a, b, 1.1, 0.14, 1.0, O)       # laterite parapet + coping
        seg(m, "frame", a, b, 0.12, 0.5, 1.14, O)                                               # white rail
    out = [(-1717.5, 3331.5), (-1695.0, 3178.5), (-1556.0, 3199.0), (-1578.0, 3349.0)]            # paved walk around the tank
    for a, b in zip(out + [out[0]], (out + [out[0]])[1:]): seg(m, "granite", a, b, 6.0, 0.25, 0, O)
    for x, y, _ in along(out + [out[0]], 13.0): lamp(m, x - O[0], y - O[1], 4.6, 2)
    for i in range(5): seg(m, "stone", (-1563.5 + i * 0.6, 3250), (-1578.5 + i * 0.6, 3310), 1.2, 0.9 - i * 0.2, 0, O)  # bathing steps, east side
    # maidan: lawn, fence, lamps, stage, fountain, gate
    m.poly("lawn", [(*rel(p), 0.35) for p in maidan]); m.poly("lawn", [(*rel(p), 0.0) for p in reversed(maidan)])
    mr = maidan + [maidan[0]]
    for a, b in zip(mr, mr[1:]):
        seg(m, "stone", a, b, 0.5, 0.6, 0, O); seg(m, "gate", a, b, 0.08, 1.1, 0.6, O)
    for x, y, _ in along(mr, 16.0): lamp(m, x - O[0], y - O[1], 5.0, 2)
    sx, sy = -1500 - O[0], 3125 - O[1]                                                           # open-air stage, south end
    m.box("stone", 16, 10, 1.0, sx, sy, 0.3); m.box("white", 16, 0.5, 5, sx, sy - 4.7, 1.3)
    for dx in (-7.5, 7.5): m.box("white", 0.6, 0.6, 5, sx + dx, sy + 4.5, 1.3)
    m.hip("tile", 18.5, 12.5, sx, sy, 6.3, 2.4)
    fx, fy = -1490 - O[0], 3172 - O[1]                                                           # musical fountain basin
    m.cyl("stone", 9, 0.6, fx, fy, 0.35, 28); m.cyl("glass", 8.3, 0.5, fx, fy, 0.5, 28); m.cyl("stone", 1.2, 1.4, fx, fy, 0.5, 12)
    gx, gy = -1448 - O[0], 3160 - O[1]                                                           # tiled entrance gateway facing the junction
    for dy in (-3.2, 3.2): m.box("laterite", 1.3, 1.3, 4.0, gx, gy + dy, 0)
    m.box("wood", 1.6, 8.2, 0.4, gx, gy, 4.0); m.hip("tile", 4.2, 10.5, gx, gy, 4.4, 1.9)
    for i, (px, py) in enumerate([(-1528, 3185), (-1475, 3205), (-1462, 3125)]):                 # statues on pedestals
        m.box("stone", 1.6, 1.6, 2.2, px - O[0], py - O[1], 0.35); m.cyl("bronze", 0.45, 1.9, px - O[0], py - O[1], 2.55, 8, 0.3)
    for i in range(14):                                                                          # benches along the tank's east walk
        x, y = -1553 - i * 1.55, 3206 + i * 10.2; m.box("wood", 0.6, 2.0, 0.45, x - O[0], y - O[1], 0.25)
    m.finish(); place("mananchira", O)

# ---------------------------------------------------------------- SM Street
def smstreet():
    O = (-1466.0, 2860.0)
    line = [(-1477, 3082), (-1468, 3014), (-1466, 2854), (-1458, 2740), (-1461, 2637)]
    m = Model("smstreet")
    for a, b in zip(line, line[1:]):
        seg(m, "cobble", a, b, 7.4, 0.22, 0, O); seg(m, "granite", a, b, 1.2, 0.24, 0, O)        # cobbled walking street, centre drain line
    for i, (x, y, h) in enumerate(along(line, 5.2, 0)):                                          # awnings + signboards on both sides
        for s in (-1, 1):
            nx, ny = -math.sin(h) * s, math.cos(h) * s
            k = (i * 3 + (2 if s > 0 else 0)) % 5
            if (i + (s > 0)) % 7 == 3: continue
            cx, cy = x + nx * 4.6 - O[0], y + ny * 4.6 - O[1]
            m.box(AW[k], 4.6, 1.9, 0.12, cx, cy, 2.9, h); m.box(AW[(k + 2) % 5], 4.4, 0.15, 0.9, x + nx * 5.5 - O[0], y + ny * 5.5 - O[1], 3.3, h)
            if i % 2 == 0: m.box("wood", 3.4, 0.9, 0.9, x + nx * 4.4 - O[0], y + ny * 4.4 - O[1], 0.22, h)    # display tables (halwa, chips)
    for x, y, h in along(line, 22.0, 0): lamp(m, x - O[0], y - O[1], 4.4, 2)
    gx, gy = -1476.5 - O[0], 3079 - O[1]                                                         # entrance gateway at the Mananchira end
    for dx in (-4.6, 4.6):
        m.box("laterite", 1.2, 1.2, 5.6, gx + dx, gy, 0); m.box("stone", 1.5, 1.5, 0.3, gx + dx, gy, 5.6); m.cyl("lamp", 0.3, 0.45, gx + dx, gy, 5.9, 8)
    m.box("gate", 10.4, 0.5, 1.3, gx, gy, 4.7); m.box("stone", 10.8, 0.7, 0.2, gx, gy, 6.0)
    m.text("white", "S.M. STREET", 0.75, gx, gy + 0.27, 5.05, ry=math.pi); m.text("white", "S.M. STREET", 0.75, gx, gy - 0.27, 5.05)
    px, py = gx + 7.5, gy + 4                                                                    # S.K. Pottekkatt statue by the entrance
    m.box("granite", 2.2, 2.2, 2.4, px, py, 0); m.cyl("bronze", 0.5, 1.5, px, py, 2.4, 10, 0.34); m.cyl("bronze", 0.3, 0.42, px, py, 3.9, 10)
    ex, ey = -1461 - O[0], 2640 - O[1]                                                           # plain arch at the southern end
    for dx in (-4.2, 4.2): m.box("laterite", 1.0, 1.0, 4.6, ex + dx, ey, 0)
    m.box("gate", 9.4, 0.4, 0.9, ex, ey, 4.0)
    m.finish(); place("smstreet", O)

# ---------------------------------------------------------------- Kozhikode Beach
def beach():
    O = (-2800.0, 3600.0)
    road = [(-2742, 3411), (-2768, 3527), (-2802, 3639), (-2815, 3712), (-2841, 3789)]           # Beach Road, seaward carriageway (south to north)
    m = Model("beach")
    prom = [(x, y) for x, y, _ in along(road, 30.0, 17.0)]                                       # promenade 17 m seaward of the road
    for a, b in zip(prom, prom[1:]): seg(m, "granite", a, b, 13.0, 1.3, -0.7, O); seg(m, "stone", a, b, 2.0, 1.34, -0.7, O)
    sea_edge = [(x, y) for x, y, _ in along(road, 30.0, 24.2)]
    for a, b in zip(sea_edge, sea_edge[1:]): seg(m, "stone", a, b, 0.5, 0.7, 0.6, O)            # sea wall / seat wall
    for x, y, _ in along(road, 18.0, 11.5): lamp(m, x - O[0], y - O[1], 6.0, 2)
    for i, (x, y, h) in enumerate(along(road, 14.0, 21.5)):                                      # benches facing the sea
        m.box("wood", 2.2, 0.55, 0.45, x - O[0], y - O[1], 0.6, h); m.box("wood", 2.2, 0.1, 0.5, x - O[0] + math.sin(h) * 0.25, y - O[1] - math.cos(h) * 0.25, 1.0, h)
    for i, (x, y, h) in enumerate(along(road[:3], 5.4, 8.5)):                                    # food-street stalls, southern stretch
        if i > 26 or i % 9 == 8: continue
        cx, cy = x - O[0], y - O[1]
        m.box("white", 3.6, 2.6, 2.3, cx, cy, 0.3, h); m.box(AW[i % 5], 4.6, 3.6, 0.12, cx, cy, 2.75, h)
        m.box(AW[(i + 2) % 5], 3.6, 0.1, 0.7, cx - math.sin(h) * -1.35, cy + math.cos(h) * -1.35, 2.9, h)
    fx, fy = -2833 - O[0], 3673 - O[1]                                                           # Freedom Square: laterite stage walls + stepped seating
    for t in range(4):
        r = 9 + t * 2.4
        for k in range(-7, 8):
            a = math.radians(180 + k * 11); m.box("laterite", 2 * r * math.sin(math.radians(5.6)) + 0.15, 1.2, 0.5 + t * 0.45, fx + math.cos(a) * r, fy + math.sin(a) * r, 0.5, a + math.pi / 2)
    for k in range(-5, 6):
        a = math.radians(k * 12); r = 11.0
        if k in (-1, 0, 1):
            m.box("laterite", 2.4, 1.0, 1.4, fx + math.cos(a) * r, fy + math.sin(a) * r, 4.6, a + math.pi / 2)   # lintel over the central opening
        else:
            m.box("laterite", 2.4, 1.0, 6.0 - abs(k) * 0.5, fx + math.cos(a) * r, fy + math.sin(a) * r, 0.5, a + math.pi / 2)
    m.cyl("stone", 8.0, 0.5, fx, fy, 0.3, 28)
    for i in range(3):                                                                           # shade pavilions on the sand
        x, y = [(-2835, 3560), (-2828, 3610), (-2852, 3740)][i]
        for dx in (-3, 3):
            for dy in (-3, 3): m.cyl("wood", 0.12, 3.0, x - O[0] + dx, y - O[1] + dy, 0.2, 6)
        m.hip("tile", 8.5, 8.5, x - O[0], y - O[1], 3.2, 2.2)
    m.finish(); place("beach", O)

mananchira(); smstreet(); beach()
