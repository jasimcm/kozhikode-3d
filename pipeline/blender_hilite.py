"""HiLITE Mall and HiLITE Business Park (HiLITE City, Thondayad bypass), from satellite + place-photo reference.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_hilite.py -- <out_dir>
Mall model space: +X along the building's long axis, front (bypass side) faces -Y; rotated into place by `deg`.
Business Park model space: +X east, +Y north (outline is the mapped footprint)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_lib import Model, COL, OUT

COL.update({
    "orange": (0xC9, 0x58, 0x36), "orange2": (0xB0, 0x48, 0x2C), "panel": (0xD8, 0xD6, 0xD0), "roofgrey": (0x8C, 0x8E, 0x90),
    "dkglass": (0x1E, 0x2C, 0x38), "screen": (0x2A, 0x4E, 0x9A), "steel": (0x6C, 0x72, 0x78), "hired": (0xD2, 0x2B, 0x2B),
})

def seg(m, mat, a, b, width, h, z):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    m.box(mat, L, width, h, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z, math.atan2(dy, dx))

def extrude(m, mat, ring, z0, z1):
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        m.poly(mat, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)])
    m.poly(mat, [(x, y, z1) for x, y in ring])

def place(name, x, n, deg, rx, rz):
    json.dump({"f": f"models/{name}.glb", "x": x, "n": n, "deg": deg, "rx": rx, "rz": rz}, open(os.path.join(OUT, name + ".place.json"), "w"))

# ---------------------------------------------------------------- HiLITE Mall
# Reference: one very long four-level block (about 230 m) with terracotta-orange and light panel bands, a tall orange
# entrance portal framing dark glass and a big LED screen, a glazed spine roof, and a wider cinema block at the south end.
def mall(L=232.0, D=54.0, H=22.0):
    m = Model("hilitemall")
    m.box("panel", L, D, H, 0, 0, 0); m.box("roofgrey", L - 2, D - 2, 0.6, 0, 0, H)
    for k in range(4):                                                        # orange bands on both long faces
        z = 1.2 + k * 5.2
        for y in (-D / 2 - 0.08, D / 2 + 0.08): m.box("orange" if k % 2 == 0 else "orange2", L * 0.98, 0.25, 2.4, 0, y, z + 2.2)
        for y in (-D / 2 - 0.1, D / 2 + 0.1): m.box("dkglass", L * 0.9, 0.2, 1.5, 0, y, z + 0.4)
    for i in range(22):                                                       # vertical piers
        x = -L / 2 + 5 + i * (L - 10) / 21
        for y in (-D / 2 - 0.2, D / 2 + 0.2): m.box("panel", 0.9, 0.5, H, x, y, 0)
    m.box("dkglass", L * 0.78, 9.0, 2.6, -6, 0, H + 0.6)                      # glazed spine over the atrium
    for i in range(16): m.box("steel", 0.3, 9.6, 2.9, -6 - L * 0.39 + i * L * 0.78 / 15, 0, H + 0.6)
    for x in (-L * 0.28, L * 0.05, L * 0.3): m.box("steel", 9, 7, 3.2, x, D / 2 - 9, H + 0.6)   # plant rooms
    for px in (-L * 0.22, L * 0.2):                                           # two entrance portals on the bypass side
        m.box("orange", 26, 5.0, H + 4, px, -D / 2 - 2.2, 0); m.box("dkglass", 19, 0.4, H - 4.5, px, -D / 2 - 4.8, 0)
        m.box("screen", 14, 0.3, 8.0, px, -D / 2 - 5.05, 8.5); m.box("panel", 22, 6.5, 0.5, px, -D / 2 - 6.5, 5.2)
        m.text("frame", "HiLITE MALL", 2.3, px, -D / 2 - 4.75, H + 0.6)
        for dx in (-9.5, 9.5): m.box("panel", 1.0, 1.0, 5.2, px + dx, -D / 2 - 9, 0)
    cx = -L / 2 + 34                                                          # cinema / anchor block, south end, wider
    m.box("orange2", 70, D + 22, H + 5, cx, -4, 0); m.box("roofgrey", 68, D + 20, 0.6, cx, -4, H + 5)
    m.box("panel", 70.3, 0.3, 4.0, cx, -4 - (D + 22) / 2, H - 2); m.text("frame", "PALAXI CINEMAS", 2.0, cx, -4 - (D + 22) / 2 - 0.2, H - 0.9)
    m.box("roofgrey", L * 0.75, 16, 0.25, 10, -D / 2 - 17, 0)                 # forecourt and drop-off
    m.finish(); place("hilitemall", 4135.0, 2562.0, 77.0, 52, 128)

# ---------------------------------------------------------------- HiLITE Business Park
# Reference: a terracotta-orange crescent office block of about ten floors with continuous dark window bands,
# ending in a round drum tower with the same banding; light roof plant and a sign at the top.
def bpark(floors=10, fh=3.9):
    ring = [(-28, 9), (-42, -38), (-27, -45), (12, -36), (33, -4), (36, 25), (31, 39), (22, 46), (5, 46), (-10, 38)]
    m = Model("hilitebp"); H = floors * fh
    extrude(m, "orange", ring, 0, H)
    cx = sum(p[0] for p in ring) / len(ring); cy = sum(p[1] for p in ring) / len(ring)
    out = [(cx + (x - cx) * 1.012, cy + (y - cy) * 1.012) for x, y in ring]
    for f in range(floors):
        for a, b in zip(out, out[1:] + out[:1]):
            seg(m, "dkglass", a, b, 0.5, 1.7, f * fh + 1.1);
        for a, b in zip(out, out[1:] + out[:1]): seg(m, "orange2", a, b, 0.7, 0.35, f * fh + 3.3)
    dx, dy, r = -33, -41, 15.0                                                # drum tower at the south-west end
    m.cyl("orange", r, H + 5, dx, dy, 0, 40)
    for f in range(floors + 1): m.cyl("dkglass", r + 0.15, 1.7, dx, dy, f * fh + 1.1, 40)
    m.cyl("panel", r + 0.8, 0.6, dx, dy, H + 5, 40); m.cyl("roofgrey", r * 0.5, 2.5, dx, dy, H + 5.6, 20)
    m.box("panel", 14, 10, 3.2, 8, 8, H); m.box("panel", 8, 8, 4.4, 22, 28, H); m.box("roofgrey", 30, 22, 0.4, 0, -12, H)
    m.box("panel", 24, 9, 0.6, 30, -30, 5.0)                                  # entrance canopy on the bypass side
    for ox in (-10, 10): m.box("panel", 0.9, 0.9, 5.0, 30 + ox, -33.5, 0)
    m.text("frame", "HiLITE BUSINESS PARK", 2.2, 35.9, 10, H - 4, ry=math.pi / 2)
    m.box("roofgrey", 60, 50, 0.2, 30, -42, 0)                                # forecourt
    m.finish(); place("hilitebp", 4204.6, 2473.5, 0, 46, 52)

mall(); bpark()
