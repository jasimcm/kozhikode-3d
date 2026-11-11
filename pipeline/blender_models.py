"""TinkerSpace Calicut + Institute of Palliative Medicine, modelled from photo reference.
Run: /Applications/Blender.app/Contents/MacOS/Blender --background --python blender_models.py -- <out_dir>"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bl_lib import Model, COL

# ---------------------------------------------------------------- TinkerSpace Calicut
# Reference: long two-storey block. Open, pillared ground floor with a through passage; white first floor behind a
# deep verandah with slim white posts and a black railing; one broad low-pitched hipped tile roof with wide eaves;
# a grey rendered wall and a red-paver ramp running along the front.
def tinkerspace(L=22.0, D=9.0):
    m = Model("tinkerspace")
    f1, f2, top = 3.3, 3.55, 6.6                       # first-floor slab underside / top, eave height
    m.box("concrete", L, D, f2 - f1, 0, 0, f1)          # first-floor slab
    for i in range(11):                                 # ground-floor pillars
        x = -L / 2 + 1 + i * (L - 2) / 10
        for y in (-D / 2 + 0.6, D / 2 - 0.6): m.box("concrete", 0.4, 0.4, f1, x, y, 0)
    m.box("white", L * 0.55, D - 4, f1, L * 0.2, 0.6, 0)         # enclosed ground-floor rooms (right of the passage)
    m.box("brick", 1.2, 1.2, f1, -L * 0.08, -D / 2 + 0.7, 0)     # brick pier beside the passage
    m.box("white", L - 3, D - 5.2, top - f2, 0, 1.2, f2)         # first-floor rooms, set back behind the verandah
    for i in range(12):                                          # slim verandah posts on both long sides
        x = -L / 2 + 0.8 + i * (L - 1.6) / 11
        for y in (-D / 2 + 0.35, D / 2 - 0.35): m.cyl("white", 0.09, top - f2, x, y, f2, 8)
    for i in range(7):                                           # dark doors and windows along the front wall
        x = -L / 2 + 4 + i * (L - 8) / 6
        if i % 3 == 0: m.box("black", 1.5, 0.1, 2.2, x, -D / 2 + 3.75, f2)
        else: m.window(x, -D / 2 + 3.8, f2 + 1.0, 1.4, 1.1, shutters=False, frame="black")
    rl, x0 = L * 0.3, -L / 2                                     # black railing along the open balcony at the left end
    m.box("black", rl, 0.05, 0.05, x0 + rl / 2, -D / 2 + 0.1, f2 + 1.0); m.box("black", rl, 0.05, 0.05, x0 + rl / 2, -D / 2 + 0.1, f2 + 0.15)
    for i in range(int(rl / 0.3) + 1): m.box("black", 0.03, 0.03, 0.9, x0 + i * 0.3, -D / 2 + 0.1, f2 + 0.12)
    m.box("black", 0.05, 3.4, 0.05, x0 + 0.05, -D / 2 + 1.8, f2 + 1.0)
    m.box("sign", 4.2, 0.08, 1.1, x0 + rl * 0.55, -D / 2 + 0.03, f2 + 0.05)
    m.text("white", "TINKERSPACE", 0.42, x0 + rl * 0.55, -D / 2 - 0.02, f2 + 0.68); m.text("white", "CALICUT", 0.36, x0 + rl * 0.55 + 0.9, -D / 2 - 0.02, f2 + 0.22)
    m.hip("tile", L + 3.6, D + 3.6, 0, 0, top, 2.5)              # broad hipped roof, wide eaves
    for i in range(1, 40):                                       # tile courses read as faint darker lines
        t = i / 40; m.box("tile2", (L + 3.6) * (1 - t * 0.62), 0.04, 0.03, 0, -(D + 3.6) / 2 * (1 - t), top + 2.5 * t + 0.01)
        m.box("tile2", (L + 3.6) * (1 - t * 0.62), 0.04, 0.03, 0, (D + 3.6) / 2 * (1 - t), top + 2.5 * t + 0.01)
    m.box("grey", L * 0.62, 0.35, 3.5, L * 0.19, -D / 2 - 1.2, 0)  # grey rendered wall along the ramp
    m.box("paver", L * 0.62, 4.5, 0.12, L * 0.19, -D / 2 - 3.8, 0) # ramp / paved approach
    m.box("paver", 5.0, D + 6, 0.1, -L * 0.2, -2, 0)               # passage paving through the building
    for i in range(9): m.cyl("green", 0.7 + (i % 3) * 0.2, 0.9, L * 0.19 - L * 0.28 + i * L * 0.07, -D / 2 - 1.8, 0, 7, 0.2)
    m.finish()

# ---------------------------------------------------------------- Institute of Palliative Medicine
# Reference: two-storey L-shaped block, pale yellow below and white above, a tiled sunshade band between the floors,
# hipped tile roofs, white windows with open shutters; a single-storey pale-blue entrance porch with red-trimmed arches.
def ipm(L=36.0, D=16.0):
    m = Model("ipm")
    h1, h2 = 3.3, 3.2
    wings = [(L * 0.62, 9.0, L * 0.19, D / 2 - 4.5), (10.0, D, -L * 0.03 - 1.0, 0)]   # long rear wing, projecting front wing
    for w, d, cx, cy in wings:
        m.box("cream", w, d, h1, cx, cy, 0); m.box("white", w, d, h2, cx, cy, h1)
        m.skirt("tile", w, d, cx, cy, h1 + 0.25); m.hip("tile", w + 1.6, d + 1.6, cx, cy, h1 + h2, 2.3 if w > d else 2.6)
    w, d, cx, cy = wings[0]                                       # windows on the long wing front
    for i in range(6):
        x = cx - w / 2 + 3.2 + i * (w - 5) / 5.5
        if x > wings[1][2] + 5.6:
            m.window(x, cy - d / 2, 1.0); m.window(x, cy - d / 2, h1 + 1.0)
    w2, d2, cx2, cy2 = wings[1]                                   # windows on the projecting wing: front and right side
    for x in (cx2 - 2.4, cx2 + 2.4):
        m.window(x, cy2 - d2 / 2, 1.0); m.window(x, cy2 - d2 / 2, h1 + 1.0)
    for y in (cy2 - 4.5, cy2 - 1.2):
        m.window(cx2 + w2 / 2, y, 1.0, ry=math.pi / 2); m.window(cx2 + w2 / 2, y, h1 + 1.0, ry=math.pi / 2)
    m.text("ink", "INSTITUTE OF PALLIATIVE MEDICINE", 0.42, cx2, cy2 - d2 / 2 - 0.03, h1 + 2.55)
    m.text("ink", "KOZHIKODE", 0.26, cx2, cy2 - d2 / 2 - 0.03, h1 + 2.15)
    pw, pd, px, py = 11.0, 8.0, -L / 2 + 5.5, -D / 2 + 5.0         # entrance porch, left
    m.box("blue", pw, pd, 3.1, px, py, 0); m.hip("tile", pw + 1.8, pd + 1.8, px, py, 3.1, 2.2)
    for x in (px - 3.4, px, px + 3.4): m.arch(x, py - pd / 2, 0, 2.3, 2.7)
    for y in (py - 2, py + 1.5): m.arch(px + pw / 2, y, 0, 2.0, 2.6, ry=math.pi / 2)
    m.box("tile", 6.0, 5.0, 0.01, px + 9.5, py - 1, 0)
    lw, lx, ly = 13.0, L * 0.19, -D / 2 + 1.5                      # lawn + free-standing sign in front of the long wing
    m.box("green", lw + 6, 5.5, 0.15, lx, ly, 0)
    for s in (-1, 1): m.cyl("black", 0.05, 2.2, lx + s * 2.4, ly, 0, 6)
    m.box("signgrey", 5.2, 0.08, 1.0, lx, ly, 1.4); m.text("ink", "INSTITUTE OF PALLIATIVE MEDICINE", 0.23, lx, ly - 0.06, 1.85)
    for i in range(8): m.cyl("green", 0.5 + (i % 2) * 0.2, 0.8, lx - 6 + i * 1.8, cy - d / 2 - 0.8, 0.1, 7, 0.15)
    m.finish()

tinkerspace(); ipm()
