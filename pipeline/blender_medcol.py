"""Government Medical College, Kozhikode: the radial hospital block, the casualty block, the college quadrangle with
its clock tower, and the small buildings between them. Massing is extruded from the mapped (Overture) footprints.
Modelled around geo.to_xy(75.83703, 11.27251) (centre of the hospital footprint), then shifted so the exported origin is
the centre of the placement rectangle: grid (4581.3 E, 5314.9 N). Metres, Z up, +X east, +Y north.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_medcol.py -- <out_dir>"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
from mathutils import Matrix, Vector
from mathutils.geometry import tessellate_polygon
from bl_lib import Model, COL

COL.update({"mcream": (0xEE, 0xE4, 0xC6), "mgreen": (0x5B, 0x98, 0x68), "mroof": (0x86, 0x84, 0x7E), "mwhite": (0xF6, 0xF3, 0xEA)})

# (kind, mapped area m2, exterior ring CCW, [hole rings]) in local metres; every mapped building whose centre lies in
# the placement rectangle (x -105..89, y -112..235), simplified to 0.5-0.8 m.
BLD = [
    ('other', 756, [(-61.3, 8.9), (-49.0, 9.2), (-49.6, 28.6), (-47.5, 28.7), (-47.6, 33.2), (-49.7, 33.1), (-50.8, 69.8), (-63.1, 69.5)], []),
    ('other', 274, [(-28.8, 26.7), (-29.2, 42.7), (-37.6, 42.5), (-37.7, 46.1), (-44.8, 45.9), (-44.7, 40.1), (-47.8, 40.0), (-47.6, 30.4), (-37.3, 30.7), (-37.1, 26.5)], []),
    ('other', 140, [(-24.1, 32.6), (-13.1, 33.0), (-13.6, 45.7), (-24.6, 45.3)], []),
    ('hosp', 22132, [(-31.5, 1.2), (-36.3, -2.0), (-58.3, -3.3), (-58.2, -6.9), (-74.4, -7.9), (-74.6, 2.0), (-78.3, 1.9), (-79.8, 46.3), (-131.2, 45.1), (-131.3, 34.6), (-94.3, 35.5), (-93.9, 23.9), (-119.9, 23.2), (-119.9, 9.2), (-98.1, 10.2), (-97.9, 13.2), (-93.6, 13.2), (-93.0, 0.9), (-97.7, 1.3), (-95.8, -61.4), (-57.1, -61.0), (-42.7, -40.1), (-38.7, -39.9), (-38.2, -50.8), (-23.1, -50.1), (-23.3, -45.1), (-10.0, -36.7), (-5.3, -44.0), (-23.8, -55.8), (-26.0, -52.3), (-33.3, -57.0), (-31.5, -59.8), (-33.4, -61.0), (-26.1, -72.4), (-3.2, -57.8), (-2.9, -62.3), (6.1, -61.8), (6.3, -64.2), (-14.6, -65.4), (-13.9, -77.5), (7.1, -76.3), (7.3, -79.6), (1.3, -80.0), (1.7, -86.3), (-28.1, -72.0), (-33.3, -82.7), (-3.6, -97.1), (-5.4, -100.6), (-5.9, -107.0), (7.3, -108.1), (14.1, -96.6), (13.1, -96.0), (14.3, -94.0), (11.2, -92.2), (12.0, -90.8), (14.5, -90.7), (15.1, -107.2), (20.6, -107.0), (20.0, -90.0), (23.1, -89.9), (24.4, -92.0), (21.6, -93.7), (23.2, -96.2), (22.2, -96.8), (25.6, -102.3), (26.7, -101.6), (27.7, -103.1), (28.3, -111.5), (34.6, -111.0), (34.0, -103.1), (40.8, -102.6), (40.3, -94.8), (65.2, -79.8), (58.7, -69.2), (32.0, -85.3), (31.2, -73.5), (43.9, -72.6), (43.2, -61.7), (25.9, -62.9), (25.7, -59.8), (38.4, -59.0), (39.0, -57.7), (56.9, -66.1), (58.0, -63.9), (60.9, -65.3), (64.6, -57.7), (62.0, -56.5), (63.7, -53.1), (58.0, -50.4), (56.5, -53.5), (36.1, -43.7), (38.1, -39.5), (48.4, -44.5), (51.5, -38.2), (75.9, -49.9), (76.9, -71.1), (88.2, -70.6), (82.2, 62.5), (68.1, 61.9), (70.6, 5.1), (76.2, 5.4), (76.8, -7.3), (53.5, -26.0), (38.0, -27.5), (37.7, -24.8), (65.9, -8.6), (59.1, 3.2), (56.0, 1.4), (54.5, 4.1), (48.6, 0.6), (49.7, -1.2), (29.9, -12.6), (29.8, -4.8), (23.3, -4.9), (23.2, -1.9), (18.5, -2.0), (18.4, 7.9), (25.7, 17.4), (56.5, 3.5), (64.1, 20.2), (36.4, 32.7), (38.7, 37.8), (34.0, 39.9), (33.9, 44.2), (7.5, 43.2), (7.2, 49.7), (38.2, 50.9), (38.8, 41.9), (58.8, 41.2), (57.2, 78.9), (73.9, 80.0), (72.8, 97.3), (30.9, 95.4), (30.3, 107.3), (0.2, 105.7), (0.5, 95.4), (-44.4, 93.9), (-43.8, 52.1), (1.7, 53.4), (2.0, 44.1), (-9.8, 43.6), (-9.3, 32.4), (-37.9, 15.7), (-30.5, 3.1), (-3.0, 19.1), (-1.0, 10.4), (11.4, 10.4), (11.3, -2.8), (5.0, -2.8), (5.0, -5.5), (-1.1, -5.5), (-1.1, -13.7)], []),
    ('other', 132, [(61.4, -106.8), (70.7, -106.4), (70.1, -92.2), (60.8, -92.6)], []),
    ('other', 711, [(75.7, -81.9), (70.1, -82.1), (71.6, -114.2), (91.4, -113.2), (89.6, -75.8), (75.4, -76.5)], []),
    ('other', 26, [(59.1, -95.5), (59.4, -88.9), (55.4, -88.7), (55.2, -95.4)], []),
    ('other', 64, [(70.7, 66.0), (70.6, 70.2), (68.4, 70.1), (68.2, 75.1), (62.3, 75.0), (62.6, 65.7)], []),
    ('other', 84, [(74.8, 161.6), (80.5, 161.8), (80.0, 176.6), (74.3, 176.4)], []),
    ('other', 25, [(77.3, 175.6), (77.7, 180.5), (72.6, 180.8), (72.2, 176.0)], []),
    ('college', 7506, [(40.3, 114.6), (57.3, 115.8), (57.6, 102.3), (72.6, 102.6), (68.2, 233.8), (51.8, 233.5), (51.8, 219.2), (-64.1, 215.3), (-63.5, 198.5), (-34.0, 198.8), (-31.8, 132.6), (-56.1, 130.9), (-54.9, 112.7), (-48.2, 113.1), (-47.8, 107.6), (-35.3, 108.3), (-35.3, 112.8), (-29.4, 113.3), (-28.8, 108.9), (-22.8, 109.3), (-22.8, 113.0), (-7.1, 113.3), (-7.0, 110.3), (5.4, 111.2), (5.3, 114.1), (28.7, 115.3), (28.8, 111.4), (40.1, 111.6)], [[(-15.1, 192.1), (-21.1, 192.0), (-21.3, 202.0), (45.6, 203.4), (45.7, 197.6), (50.3, 197.7), (50.7, 178.4), (46.4, 178.3), (46.8, 156.9), (51.0, 157.0), (51.5, 137.1), (46.4, 136.9), (46.5, 131.5), (-20.9, 130.0), (-21.1, 137.9), (-14.2, 138.0), (-14.7, 159.6), (-21.0, 159.5), (-21.3, 171.3), (-14.7, 171.4)]]),
    ('other', 48, [(-48.1, 51.3), (-43.8, 51.4), (-44.2, 62.6), (-48.5, 62.5)], []),
    ('other', 48, [(-42.9, 94.3), (-43.2, 101.5), (-49.8, 101.3), (-49.6, 94.1)], []),
    ('other', 252, [(-58.2, 165.9), (-40.4, 166.6), (-41.0, 181.9), (-43.7, 181.8), (-43.7, 179.8), (-55.1, 179.3), (-55.2, 182.0), (-58.8, 181.9)], []),
    ('other', 383, [(-57.3, 143.7), (-39.5, 144.4), (-40.3, 165.9), (-58.2, 165.2)], []),
    ('other', 35, [(-101.7, 24.0), (-95.7, 24.2), (-95.9, 29.9), (-102.0, 29.7)], []),
    ('other', 38, [(-101.8, -36.7), (-98.0, -36.3), (-99.1, -26.7), (-103.0, -27.1)], []),
    ('other', 68, [(-70.2, -0.3), (-66.6, -0.2), (-66.4, -4.0), (-58.4, -3.7), (-58.7, 3.3), (-70.3, 2.9)], []),
    ('cas', 1429, [(-53.4, -63.3), (-79.7, -63.3), (-79.7, -93.2), (-35.6, -93.2), (-35.6, -57.2), (-53.4, -57.2)], []),
]

def solid(m, mat, rings, z0, z1, top=True):
    """prism of a polygon-with-holes between z0 and z1 (closed; top=False leaves it open under a roof slab)"""
    bm = m._bm(mat); lo, hi = [], []
    for ring in rings:
        a = [bm.verts.new((x, y, z0)) for x, y in ring]; b = [bm.verts.new((x, y, z1)) for x, y in ring]
        for i in range(len(ring)):
            j = (i + 1) % len(ring); bm.faces.new([a[i], a[j], b[j], b[i]])
        lo += a; hi += b
    for t in tessellate_polygon([[Vector((x, y, 0)) for x, y in r] for r in rings]):
        bm.faces.new([lo[i] for i in reversed(t)])
        if top: bm.faces.new([hi[i] for i in t])

def edges(ring, minlen=0.0):
    """(mid x, mid y, length, direction angle, outward normal x, y) for each edge of a CCW exterior / CW hole ring"""
    for i in range(len(ring)):
        (x0, y0), (x1, y1) = ring[i], ring[(i + 1) % len(ring)]
        dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy)
        if L >= minlen: yield (x0 + x1) / 2, (y0 + y1) / 2, L, math.atan2(dy, dx), dy / L, -dx / L

def facade(m, rings, floors, fh, fins=None, shade="mgreen"):
    """per wall: one window band + one green sunshade per floor, and full-height piers on the long walls"""
    for ring in rings:
        for mx, my, L, ang, nx, ny in edges(ring, 3.5):
            for f in range(floors):
                m.box("glass", L - 1.4, 0.16, 1.45, mx + nx * 0.02, my + ny * 0.02, f * fh + 1.05, ang)
                if L >= 6: m.box(shade, L - 0.3, 0.6, 0.12, mx + nx * 0.3, my + ny * 0.3, f * fh + 2.75, ang)
            if fins and L >= 12:
                k = max(2, round(L / 6.5)); ux, uy = math.cos(ang), math.sin(ang)
                for i in range(1, k):
                    t = (i / k - 0.5) * L
                    m.box(fins, 0.55, 0.36, floors * fh + 0.3, mx + ux * t + nx * 0.14, my + uy * t + ny * 0.14, 0, ang)

def disc(m, mat, r, cx, cy, cz, ry):
    """vertical disc (clock face) whose outward normal is rotated ry about Z from -Y"""
    M = Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(ry, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")
    bmesh.ops.create_cone(m._bm(mat), cap_ends=True, segments=20, radius1=r, radius2=r, depth=0.2, matrix=M)

def hiproof(m, mat, w, d, cx, cy, z, rise):
    """closed hipped roof over a w x d rectangle (w >= d), ridge along X"""
    bm = m._bm(mat); hw, hd = w / 2, d / 2
    e = [bm.verts.new((cx + sx * hw, cy + sy * hd, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    r = [bm.verts.new((cx - hw + hd, cy, z + rise)), bm.verts.new((cx + hw - hd, cy, z + rise))]
    for f in ([e[0], e[1], r[1], r[0]], [e[2], e[3], r[0], r[1]], [e[1], e[2], r[1]], [e[3], e[0], r[0]], [e[3], e[2], e[1], e[0]]): bm.faces.new(f)

def facing(nx, ny):
    """text / box rotation for a wall with outward normal (nx, ny)"""
    return math.atan2(ny, nx) + math.pi / 2

def medcol():
    m = Model("medcol")
    for kind, area, ext, holes in BLD:
        if kind == "other" and abs(sum(p[0] for p in ext) / len(ext) - 77) < 4 and abs(sum(p[1] for p in ext) / len(ext) - 172) < 10:
            continue                                                                # mapped porch structures of the college: modelled by hand below
        rings = [ext] + holes
        if kind == "hosp": floors, fh, wall, fins = 4, 3.6, "mcream", "mwhite"      # main hospital: G+3
        elif kind == "college": floors, fh, wall, fins = 3, 4.0, "mcream", "mgreen"  # college quadrangle: G+2, tall storeys
        elif kind == "cas": floors, fh, wall, fins = 3, 3.6, "mwhite", None
        else: floors, fh, wall, fins = (3 if area > 500 else 2 if area > 120 else 1), 3.3, "mcream", None
        top = floors * fh + 0.9
        solid(m, wall, rings, 0, top, top=False); solid(m, "mroof", rings, top, top + 0.15)
        facade(m, rings, floors, fh, fins)
        if kind == "hosp":                                                          # sign on the longest wall (east front, entrance road)
            mx, my, L, ang, nx, ny = max(edges(ext), key=lambda e: e[2])
            m.box("mgreen", 46, 0.2, 3.0, mx + nx * 0.1, my + ny * 0.1, top - 1.0, ang)
            m.text("mwhite", "GOVT. MEDICAL COLLEGE HOSPITAL", 2.0, mx + nx * 0.25, my + ny * 0.25, top - 0.3, facing(nx, ny))
        if kind == "cas":
            mx, my, L, ang, nx, ny = min(edges(ext, 20), key=lambda e: e[1])        # south wall
            m.box("red", 20, 0.2, 2.2, mx + nx * 0.1, my + ny * 0.1, top - 2.6, ang)
            m.text("mwhite", "CASUALTY", 1.5, mx + nx * 0.25, my + ny * 0.25, top - 2.1, facing(nx, ny))
            m.box("mwhite", 14, 7, 0.35, mx + nx * 3.5, my + ny * 3.5, 4.2, ang)     # ambulance porch
            for sx in (-6, 6): m.box("mwhite", 0.5, 0.5, 4.2, mx + sx * math.cos(ang) + nx * 6.4, my + sx * math.sin(ang) + ny * 6.4, 0, ang)

    # hospital roof furniture: stair heads / water tanks over the hub and along the east bar; a tiled roof on the north block
    for x, y, w, d, h in ((4, -20, 9, 9, 3.2), (-70, -30, 6, 8, 2.8), (80, -30, 5, 12, 2.8), (76, 40, 5, 10, 2.8), (-20, 75, 8, 6, 2.8), (50, 88, 6, 8, 2.8)):
        m.box("mcream", w, d, h, x, y, 15.4); m.box("mroof", w + 0.6, d + 0.6, 0.15, x, y, 15.4 + h)
    hiproof(m, "tile", 30, 15, 28, 61, 15.5, 3.0); hiproof(m, "tile", 16, 15, 65.5, 88.5, 15.5, 2.8)

    # college clock tower over the main entrance, centre of the east front facing Medical College Entrance Road
    # (art-deco: cream shaft, green fins, stepped top). Built in a frame whose front is -Y, then turned to face east.
    a = math.pi / 2 + 0.0335; R = Matrix.Rotation(a, 3, "Z"); tx, ty = 65.4, 168.0
    def P(ox, oy):
        v = R @ Vector((ox, oy, 0)); return tx + v.x, ty + v.y
    m.box("mcream", 26, 13, 17.5, *P(0, 2.5), 0, a)                                 # raised centre block either side of the tower
    m.box("mroof", 26.4, 13.4, 0.15, *P(0, 2.5), 17.5, a)
    m.box("mcream", 10.5, 10.5, 30, tx, ty, 0, a)                                   # shaft
    m.box("mwhite", 11.3, 11.3, 0.5, tx, ty, 30, a)
    m.box("mcream", 8.6, 8.6, 6.5, tx, ty, 30.5, a)                                 # clock stage
    m.box("mwhite", 9.4, 9.4, 0.45, tx, ty, 37, a)
    m.box("mcream", 6.0, 6.0, 2.6, tx, ty, 37.45, a); m.box("mgreen", 6.6, 6.6, 0.3, tx, ty, 40.05, a)
    m.box("mcream", 3.2, 3.2, 1.8, tx, ty, 40.35, a); m.cyl("mwhite", 0.12, 5, tx, ty, 42.15, 6)
    for k in range(4):                                                              # four faces: fins, long window slots, clock
        ry = a + k * math.pi / 2; Q = Matrix.Rotation(ry, 3, "Z")
        def F(ox, oy):
            v = Q @ Vector((ox, oy, 0)); return tx + v.x, ty + v.y
        for ox in (-3.6, -1.2, 1.2, 3.6): m.box("mgreen", 0.5, 0.5, 23, *F(ox, -5.4), 6.5, ry)
        for ox in (-2.4, 0, 2.4): m.box("glass", 1.5, 0.2, 21, *F(ox, -5.27), 7.5, ry)
        disc(m, "mwhite", 2.7, *F(0, -4.36), 33.9, ry); disc(m, "black", 0.3, *F(0, -4.5), 33.9, ry)
        m.box("black", 0.16, 0.1, 2.1, *F(0, -4.5), 33.9, ry); m.box("black", 1.5, 0.1, 0.16, *F(0.75, -4.5), 33.82, ry)
        for ox in (-3.8, 3.8): m.box("mgreen", 0.45, 0.45, 6.5, *F(ox, -4.2), 30.5, ry)
    m.box("mwhite", 16, 7, 0.45, *P(0, -8.0), 5.2, a)                               # porte-cochere in front of the tower
    for ox in (-7, -2.4, 2.4, 7): m.box("mwhite", 0.6, 0.6, 5.2, *P(ox, -10.8), 0, a)
    m.box("mgreen", 16.2, 0.25, 1.5, *P(0, -11.45), 5.65, a)
    m.text("mwhite", "GOVERNMENT MEDICAL COLLEGE", 0.8, *P(0, -11.6), 6.35, a)
    m.text("mwhite", "KOZHIKODE", 0.5, *P(0, -11.6), 5.75, a)
    for bm in m.bm.values():                                                        # origin -> centre of the placement rectangle
        for v in bm.verts: v.co.x += SHIFT[0]; v.co.y += SHIFT[1]
    m.texts = [(mat, body, size, cx + SHIFT[0], cy + SHIFT[1], cz, ry) for mat, body, size, cx, cy, cz, ry in m.texts]
    m.finish()

SHIFT = (8.0, -61.5)
medcol()
