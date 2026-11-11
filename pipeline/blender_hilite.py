"""HiLITE Mall and HiLITE Business Park (HiLITE City, Thondayad bypass), from satellite + place-photo reference.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_hilite.py -- <out_dir>
Mall model space: +X along the building's long axis, front (bypass side) faces -Y; rotated into place by `deg`.
Business Park model space: +X east, +Y north (outline is the mapped footprint)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_lib import Model, COL, OUT

COL.update({
    "orange": (0xC9, 0x58, 0x36), "orange2": (0xB0, 0x48, 0x2C), "panel": (0xD8, 0xD6, 0xD0), "roofgrey": (0x8C, 0x8E, 0x90),
    "dkglass": (0x1E, 0x2C, 0x38), "lawn": (0x5E, 0x9E, 0x42), "screen": (0x2A, 0x4E, 0x9A), "steel": (0x6C, 0x72, 0x78), "hired": (0xD2, 0x2B, 0x2B),
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
# Reference (satellite): two interlocking curved blocks forming an S. Phase 1 is a terracotta-orange crescent wrapping
# the west side of a round entrance plaza; Tower 2 is a second curved block wrapping the north-east side of a round
# plaza to its south-west. Both have continuous dark window bands; place photos show roughly ten and twelve floors.
def arc_block(m, cx, cy, r_in, r_out, a0, a1, floors, fh, wall, band, step=6.0):
    H = floors * fh; n = max(2, int(round((a1 - a0) / step))); da = math.radians((a1 - a0) / n); rm = (r_in + r_out) / 2
    for i in range(n):
        a = math.radians(a0) + (i + 0.5) * da; ca, sa = math.cos(a), math.sin(a)
        m.box(wall, 2 * r_out * math.tan(da / 2) + 0.05, r_out - r_in, H, cx + ca * rm, cy + sa * rm, 0, a + math.pi / 2)
        for f in range(floors):
            m.box("dkglass", 2 * (r_out + 0.2) * math.tan(da / 2), 0.4, 1.7, cx + ca * (r_out + 0.05), cy + sa * (r_out + 0.05), f * fh + 1.1, a + math.pi / 2)
            m.box("dkglass", 2 * (r_in - 0.2) * math.tan(da / 2), 0.4, 1.7, cx + ca * (r_in - 0.05), cy + sa * (r_in - 0.05), f * fh + 1.1, a + math.pi / 2)
            m.box(band, 2 * (r_out + 0.4) * math.tan(da / 2), 0.5, 0.35, cx + ca * (r_out + 0.15), cy + sa * (r_out + 0.15), f * fh + 3.3, a + math.pi / 2)
        m.box("roofgrey", 2 * rm * math.tan(da / 2), (r_out - r_in) - 1.2, 0.5, cx + ca * rm, cy + sa * rm, H, a + math.pi / 2)
    for a_end in (a0, a1):                                                   # blank end walls
        a = math.radians(a_end); m.box(band, r_out - r_in + 0.6, 0.6, H + 0.5, cx + math.cos(a) * rm, cy + math.sin(a) * rm, 0, a)
    return H

def bpark():
    m = Model("hilitebp")
    A = (14.0, 22.0); B = (-18.0, -22.0)                                     # plaza centres, metres from the footprint centroid
    HA = arc_block(m, *A, 15.0, 26.5, 95, 265, 10, 3.9, "orange", "orange2")      # phase 1: crescent on the west of plaza A
    HB = arc_block(m, *B, 14.0, 26.0, -35, 120, 12, 3.9, "panel", "steel")         # tower 2: curved block on the north-east of plaza B
    for (cx, cy), col in ((A, "panel"), (B, "panel")):                        # round plazas
        m.cyl("roofgrey", 14.2, 0.3, cx, cy, 0, 40); m.cyl(col, 9.0, 0.34, cx, cy, 0, 32); m.cyl("lawn" if "lawn" in COL else "roofgrey", 3.0, 0.5, cx, cy, 0, 16)
    m.cyl("orange", 6.5, HA + 5, A[0] - 20.5, A[1] - 0.5, 0, 28)              # lift/stair drum on the crescent's outer face
    for f in range(11): m.cyl("dkglass", 6.65, 1.5, A[0] - 20.5, A[1] - 0.5, f * 3.9 + 1.2, 28)
    m.cyl("panel", 7.2, 0.5, A[0] - 20.5, A[1] - 0.5, HA + 5, 28)
    m.box("panel", 16, 8, 0.6, A[0] + 19, A[1], 5.0)                          # entrance canopy on the plaza's open (east) side
    for oy in (-3, 3): m.box("panel", 0.8, 0.8, 5.0, A[0] + 25, A[1] + oy, 0)
    m.text("frame", "HiLITE BUSINESS PARK", 1.9, A[0] - 4, A[1] + 26.9, HA - 4, ry=math.pi)
    m.text("frame", "TOWER 2", 2.0, B[0] + 20, B[1] + 17.6, HB - 4, ry=math.radians(220))
    m.finish(); place("hilitebp", 4204.6, 2473.5, 0, 46, 52)

mall(); bpark()
