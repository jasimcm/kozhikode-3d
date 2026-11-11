"""Government Cyberpark Kozhikode - the "Sahya" IT building. Massing from the mapped (Overture) footprint; facade from
place photos: blue-grey ribbed metal cladding that wraps over curved eaves, ribbon glazing with white sun-fins on the
long sides, mostly blank end walls, an upper-floor wing carried on tall yellow columns over the entrance, roof sign.
Built axis-aligned, then turned -1.7 deg to match the footprint. Exported origin = centre of the footprint bounding
box: grid (4577.4 E, 3224.4 N). Metres, Z up, +X east, +Y north.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_cyberpark.py -- <out_dir>"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Matrix
from bl_lib import Model, COL

COL.update({"clad": (0x84, 0x9B, 0xAE), "clad2": (0x9F, 0xB1, 0xBF), "bglass": (0x35, 0x62, 0x8C), "fin": (0xF3, 0xF4, 0xF2),
            "cyellow": (0xE6, 0xB4, 0x3C), "dark": (0x2C, 0x31, 0x38), "solar": (0x1C, 0x2A, 0x48), "croof": (0x8E, 0x93, 0x96),
            "cyblue": (0x1E, 0x6C, 0xB4), "cygreen": (0x3C, 0xA0, 0x68)})

# 'Sahya - Cyberpark' footprint, metres from geo.to_xy(75.83693, 11.25413), CCW from the north-west corner
RING = [(-35.2, 39.6), (-37.7, -45.0), (33.1, -47.1), (35.8, 48.6), (7.6, 49.4), (7.7, 53.5), (-2.9, 53.8), (-3.4, 38.7)]
TILT = math.atan2(-2.1, 70.8)                      # direction of the south wall
SHIFT = (1.0, -3.4)                                # footprint bbox centre -> origin
FH, NF = 4.2, 5                                    # storey height, storeys (G+4)

def barrel(m, mat, xa, xb, ya, yb, eave, r, z0=0.0, seg=5):
    """block spanning xa..xb, ya..yb whose long (Y) eaves curve over into the roof - the wrapped metal cladding"""
    prof = [(xa, z0), (xb, z0)]
    prof += [(xb - r + r * math.cos(t), eave + r * math.sin(t)) for t in (i * math.pi / 2 / seg for i in range(seg + 1))]
    prof += [(xa + r - r * math.sin(t), eave + r * math.cos(t)) for t in (i * math.pi / 2 / seg for i in range(seg + 1))]
    bm = m._bm(mat); a = [bm.verts.new((x, ya, z)) for x, z in prof]; b = [bm.verts.new((x, yb, z)) for x, z in prof]
    for i in range(len(prof)):
        j = (i + 1) % len(prof); bm.faces.new([a[i], a[j], b[j], b[i]])
    bm.faces.new(a[::-1]); bm.faces.new(b)

def ribbons(m, cx, cy, L, ry, f0=0, f1=NF, piers=True):
    """ribbon glazing + white sun-fins on a wall centred at (cx, cy), length L, outward normal rotated ry from -Y"""
    c, s = math.cos(ry), math.sin(ry); nx, ny = s, -c
    for f in range(f0, f1):
        m.box("bglass", L - 2.4, 0.2, 2.1, cx + nx * 0.03, cy + ny * 0.03, f * FH + 1.2, ry)
        m.box("fin", L - 1.2, 0.7, 0.18, cx + nx * 0.35, cy + ny * 0.35, f * FH + 3.5, ry)
    if piers:
        k = max(2, round(L / 8.4))
        for i in range(1, k):
            t = (i / k - 0.5) * L
            m.box("clad", 0.8, 0.5, (f1 - f0) * FH - 0.6, cx + c * t + nx * 0.2, cy + s * t + ny * 0.2, f0 * FH + 0.4, ry)

def cyberpark():
    m = Model("cyberpark")
    ct, st = math.cos(-TILT), math.sin(-TILT)
    A = [(x * ct - y * st, x * st + y * ct) for x, y in RING]                       # footprint, axis-aligned
    W, E = (A[0][0] + A[1][0]) / 2, (A[2][0] + A[3][0]) / 2
    S, NW, NE = (A[1][1] + A[2][1]) / 2, (A[0][1] + A[7][1]) / 2, (A[3][1] + A[4][1]) / 2
    BX0, BX1, BT = (A[6][0] + A[7][0]) / 2, (A[4][0] + A[5][0]) / 2, (A[5][1] + A[6][1]) / 2   # entrance projection
    H, EAVE, R, WW = NF * FH, NF * FH - 1.4, 1.9, 20.0                              # 21 m to the roof, wing width
    cx = (W + E) / 2

    # two long N-S office wings with wrapped roofs
    for xa, xb, yn, out in ((W, W + WW, NW, math.pi * 1.5), (E - WW, E, NE, math.pi / 2)):
        barrel(m, "clad", xa, xb, S, yn, EAVE, R)
        for y in (S + 0.9, yn - 1.4): barrel(m, "dark", xa - 0.22, xb + 0.22, y, y + 0.5, EAVE, R + 0.22, z0=0.3)   # steel ribs at the ends
        xo = xa if out > math.pi else xb
        ribbons(m, xo, (S + yn) / 2, yn - S - 5, out)                               # outer long facade
        xi = xb if out > math.pi else xa
        ribbons(m, xi, (S + 16 + yn) / 2, yn - S - 20, out + math.pi, 4, 5, piers=False)   # top floor, above the atrium block
        for y, ry in ((yn, math.pi), (S, 0.0)):                                     # end walls: blank cladding, recessed strip, stair slit
            sg = 1 if ry else -1
            m.box("dark", WW * 0.72, 0.2, 1.5, (xa + xb) / 2, y + sg * 0.04, H - 5.6, ry)
            m.box("bglass", 1.6, 0.2, H - 9.5, (xa + xb) / 2 - sg * WW * 0.3, y + sg * 0.04, 1.5, ry)
            m.box("fin", WW * 0.72, 0.5, 0.15, (xa + xb) / 2, y + sg * 0.25, H - 4.0, ry)
    # lower atrium block between the wings (4 floors), glazed north front, skylight
    HC = 4 * FH; cw = E - W - 2 * WW
    m.box("clad2", cw, NW - S, HC, cx, (S + NW) / 2, 0); m.box("croof", cw, NW - S, 0.15, cx, (S + NW) / 2, HC)
    m.box("clad2", E - WW - BX1, NE - NW, HC, (BX1 + E - WW) / 2, (NW + NE) / 2, 0); m.box("croof", E - WW - BX1, NE - NW, 0.15, (BX1 + E - WW) / 2, (NW + NE) / 2, HC)
    m.box("bglass", BX0 - (W + WW) - 0.6, 0.25, HC - 1.0, (W + WW + BX0) / 2, NW + 0.05, 0.5)        # curtain wall left of the entrance
    m.box("bglass", E - WW - BX1 - 0.6, 0.25, HC - 1.0, (BX1 + E - WW) / 2, NE + 0.05, 0.5)          # ... and right
    for f in range(1, 4):
        m.box("fin", BX0 - (W + WW), 0.5, 0.16, (W + WW + BX0) / 2, NW + 0.25, f * FH)
        m.box("fin", E - WW - BX1, 0.5, 0.16, (BX1 + E - WW) / 2, NE + 0.25, f * FH)
    m.box("bglass", cw * 0.5, 44, 2.2, cx, (S + NW) / 2 + 2, HC)                    # atrium skylight
    for i in range(6): m.box("fin", cw * 0.5 + 0.3, 0.3, 2.35, cx, (S + NW) / 2 - 20 + i * 8.8, HC)
    m.box("fin", 9, 14, H + 4.5, cx - cw / 2 + 5.5, NW - 16, 0)                     # lift / stair core rising above the roof
    m.box("croof", 9.5, 14.5, 0.2, cx - cw / 2 + 5.5, NW - 16, H + 4.5)
    # south cross-bar, full height, solar panels on the roof
    m.box("clad", cw, 16, H, cx, S + 8, 0); m.box("croof", cw + 0.4, 16.4, 0.15, cx, S + 8, H)
    ribbons(m, cx, S, cw - 1, 0.0)
    for j in range(3):
        for i in range(4): m.box("solar", cw / 4 - 1.2, 3.6, 0.12, cx - cw / 2 + (i + 0.5) * cw / 4, S + 3.2 + j * 4.8, H + 0.35)
    for xa in (W, E - WW):                                                          # solar arrays on the wing roofs
        for i in range(7): m.box("solar", WW - 7, 7.5, 0.12, xa + WW / 2, S + 22 + i * 9.2, EAVE + R + 0.05)
    # entrance: upper floors of a short wing carried over the drop-off on tall yellow columns
    z1 = 2 * FH; bw = BX1 - BX0
    barrel(m, "clad", BX0, BX1, NW - 1, BT, EAVE - 2.2, 1.5, z0=z1)
    m.box("cyellow", bw + 3.0, BT - NW + 2.4, 0.6, (BX0 + BX1) / 2, (NW + BT) / 2 + 0.6, z1 - 0.6)
    for x in (BX0 + 0.3, BX1 - 0.3):
        for y in (BT + 0.6, (NW + BT) / 2 + 0.6): m.cyl("cyellow", 0.5, z1 - 0.6, x, y, 0, 14)
    for f in range(2, 4):
        m.box("bglass", bw - 2.2, 0.2, 2.1, (BX0 + BX1) / 2, BT + 0.03, f * FH + 1.2, math.pi)
        m.box("fin", bw - 0.8, 0.6, 0.18, (BX0 + BX1) / 2, BT + 0.3, f * FH + 3.5, math.pi)
        for x, ry in ((BX0, math.pi * 1.5), (BX1, math.pi / 2)):
            m.box("bglass", 0.2, BT - NW - 2, 2.1, x + (0.03 if ry < 2 else -0.03), (NW + BT) / 2, f * FH + 1.2)
    m.box("dark", bw - 1.5, 0.3, 4.2, (BX0 + BX1) / 2, NW + 0.1, 0.2)               # lobby doors under the canopy
    m.box("fin", 9.0, 0.2, 1.3, (BX0 + BX1) / 2, BT + 1.95, z1 - 0.95, math.pi)     # name board on the canopy edge
    m.text("cyblue", "SAHYA", 0.9, (BX0 + BX1) / 2, BT + 2.1, z1 - 0.7, math.pi)
    # 'cyberpark' roof sign on a steel lattice, facing the approach road (north)
    zs = EAVE - 2.2 + 1.5; sx = (BX0 + BX1) / 2; sy = BT - 1.5
    for i in range(6): m.box("dark", 0.12, 0.12, 4.6, sx - 5.5 + i * 2.2, sy - 0.3, zs)
    for z in (0.6, 2.4, 4.2): m.box("dark", 11.4, 0.1, 0.1, sx, sy - 0.3, zs + z)
    m.text("cyblue", "cyber", 2.6, sx + 3.0, sy, zs + 1.3, math.pi); m.text("cygreen", "park", 2.6, sx - 3.6, sy, zs + 1.3, math.pi)

    T = Matrix.Translation((SHIFT[0], SHIFT[1], 0)) @ Matrix.Rotation(TILT, 4, "Z")  # turn to the real bearing, recentre
    for bm in m.bm.values():
        for v in bm.verts: v.co = T @ v.co
    ct, st = math.cos(TILT), math.sin(TILT)
    m.texts = [(mat, body, size, x * ct - y * st + SHIFT[0], x * st + y * ct + SHIFT[1], z, ry + TILT) for mat, body, size, x, y, z, ry in m.texts]
    m.finish()

cyberpark()
