"""Turn raw Overture / Sentinel / DEM downloads into compact web assets in ../data/."""
import json, math, struct, sys, hashlib
import numpy as np, duckdb, shapely
from shapely import wkb as swkb
from shapely.geometry import box
from PIL import Image, ImageDraw, ImageFilter
import geo

Image.MAX_IMAGE_PIXELS = None
RAW, OUT = "../data/raw", "../data"
HX, HY = geo.HALF_X, geo.HALF_Y
BBOX = box(geo.W, geo.S, geo.E, geo.N)
con = duckdb.connect()
LAYER = "s2020"
CHUNK = 1024.0
NCX, NCY = math.ceil(2 * HX / CHUNK), math.ceil(2 * HY / CHUNK)
Q = 0.05  # metres per int16 unit

def rows(name, cols, where="1=1"):
    return con.execute(f"select {cols} from '{RAW}/{name}.parquet' where {where}").fetchall()

def xy(coords):
    a = np.asarray(coords, dtype=np.float64)[:, :2]
    return np.stack([(a[:, 0] - geo.LON0) * geo.MX, (a[:, 1] - geo.LAT0) * geo.MY], 1)

def polys(g):
    if g.geom_type == "Polygon": return [g]
    if g.geom_type == "MultiPolygon": return list(g.geoms)
    if g.geom_type == "GeometryCollection": return [p for x in g.geoms for p in polys(x)]
    return []

def lines(g):
    if g.geom_type == "LineString": return [g]
    if g.geom_type == "MultiLineString": return list(g.geoms)
    return []

def h01(s, salt=0):
    return (int(hashlib.md5(f"{s}{salt}".encode()).hexdigest()[:8], 16) % 100000) / 100000.0

# ---------------------------------------------------------------- rasters
MW = 4096; MH = int(round(MW * HY / HX)); SS = 2
RW, RH = MW * SS, MH * SS
def pix(p, w=RW, h=RH):
    return [((x + HX) / (2 * HX) * w, (HY - y) / (2 * HY) * h) for x, y in p]
MPP = 2 * HX / RW

sat = np.asarray(Image.open(f"{RAW}/sat_core_{LAYER}.png").convert("RGB")).astype(np.float32)
hcore = np.load(f"{RAW}/h_core.npy")
hback = np.load(f"{RAW}/h_back.npy")

def sample(grid, x, y):
    """bilinear sample of a core-extent raster (row 0 = north) at local metres."""
    H, W = grid.shape[:2]
    fx = np.clip((x + HX) / (2 * HX) * W - 0.5, 0, W - 1.001)
    fy = np.clip((HY - y) / (2 * HY) * H - 0.5, 0, H - 1.001)
    ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - ix, fy - iy
    if grid.ndim == 3: tx, ty = tx[..., None], ty[..., None]
    return (grid[iy, ix] * (1 - tx) * (1 - ty) + grid[iy, ix + 1] * tx * (1 - ty)
            + grid[iy + 1, ix] * (1 - tx) * ty + grid[iy + 1, ix + 1] * tx * ty)

print("water…", flush=True)
water = Image.new("L", (RW, RH), 0); dw = ImageDraw.Draw(water)
nsea = 0
for wkb_, sub, cls in rows("water", "wkb, subtype, class"):
    g = swkb.loads(bytes(wkb_))
    if not g.intersects(BBOX): continue
    g = g.intersection(BBOX.buffer(0.01)) if g.geom_type in ("Polygon", "MultiPolygon") else g
    for p in polys(g):
        if sub == "human_made": continue
        if sub in ("ocean",): nsea += 1
        dw.polygon(pix(xy(p.exterior.coords)), fill=255)
        for r in p.interiors: dw.polygon(pix(xy(r.coords)), fill=0)
    for l in lines(g):
        wd = {"river": 14, "canal": 6, "stream": 3}.get(sub, 3)
        if cls in ("drain", "ditch"): wd = 2
        dw.line(pix(xy(l.coords)), fill=255, width=max(1, round(wd / MPP)), joint="curve")
print("  ocean polygons drawn:", nsea, "water coverage", np.asarray(water).mean() / 255)

print("roads…", flush=True)
road = Image.new("L", (RW, RH), 0); dr = ImageDraw.Draw(road)
rail = Image.new("L", (RW, RH), 0); dl = ImageDraw.Draw(rail)
WIDTH = {"motorway": 16, "trunk": 14, "primary": 12, "secondary": 9.5, "tertiary": 7.5, "residential": 5,
         "unclassified": 5, "unknown": 4.5, "living_street": 4, "service": 3.5, "pedestrian": 4, "track": 3}
major = []
for wkb_, sub, cls, name in rows("segments", "wkb, subtype, class, name"):
    g = swkb.loads(bytes(wkb_))
    for l in lines(g):
        p = xy(l.coords)
        if sub == "rail":
            dl.line(pix(p), fill=255, width=max(1, round(3.2 / MPP)), joint="curve")
        elif sub == "road" and cls in WIDTH:
            wd = WIDTH[cls]
            dr.line(pix(p), fill=255, width=max(1, round(wd / MPP)), joint="curve")
            if cls in ("trunk", "primary", "secondary", "tertiary"):
                s = shapely.LineString(p).simplify(2.0)
                c = np.asarray(s.coords)
                if (np.abs(c[:, 0]) < HX).any() and (np.abs(c[:, 1]) < HY).any():
                    major.append({"c": {"trunk": 0, "primary": 1, "secondary": 2, "tertiary": 3}[cls],
                                  "p": [round(float(v), 1) for v in c.reshape(-1)]})
json.dump(major, open(f"{OUT}/roads.json", "w"), separators=(",", ":"))
print("  major roads", len(major))

# ---------------------------------------------------------------- buildings
print("buildings…", flush=True)
bmask = Image.new("L", (MW, MH), 0); db = ImageDraw.Draw(bmask)
CX0, CY0 = 75.7830, 11.2560
ccx, ccy = geo.to_xy(CX0, CY0)
chunks = {}
nb = nv = 0; src = {"mapped": 0, "est": 0}
for bid, wkb_, height, floors, cls, name in rows("buildings", "id, wkb, height, num_floors, class, name"):
    g = swkb.loads(bytes(wkb_))
    for p in polys(g):
        c = xy(p.exterior.coords)
        poly = shapely.Polygon(c)
        if not poly.is_valid: poly = poly.buffer(0)
        if poly.is_empty or poly.geom_type != "Polygon": continue
        poly = poly.simplify(0.45)
        a = poly.area
        if a < 9: continue
        cen = poly.centroid
        if abs(cen.x) > HX or abs(cen.y) > HY: continue
        ring = np.asarray(shapely.geometry.polygon.orient(poly, 1.0).exterior.coords)[:-1]
        if len(ring) < 3: continue
        if len(ring) > 250: ring = ring[:: math.ceil(len(ring) / 250)]
        r1, r2, r3 = h01(bid), h01(bid, 1), h01(bid, 2)
        core = math.exp(-math.hypot(cen.x - ccx, cen.y - ccy) / 1600.0)
        mapped = True
        if height and height > 2: hgt = float(height)
        elif floors and floors > 0: hgt = floors * 3.1 + 0.8
        else:
            mapped = False
            if a < 60: fl = 1
            elif a < 200: fl = 1 + (r1 < 0.28 + 0.3 * core)
            elif a < 500: fl = 1 + (r1 < 0.55) + (r2 < 0.5 * core)
            elif a < 1500:
                fl = 2 + int(r1 * 2) + int(r2 * 3 * core)
                if r3 < 0.012 + 0.03 * core and 4 * math.pi * a / (poly.length ** 2) > 0.55: fl = 7 + int(r1 * 6)
            else: fl = 1 + int(r1 * 2.5) + (r2 < core)
            hgt = fl * 2.9 + 0.3 + r3 * 0.5
        src["mapped" if mapped else "est"] += 1
        hgt = min(hgt, 127.0)
        # roof style: 1 = pitched tile (small 4-corner houses), 2 = sheet metal (big sheds), 0 = flat concrete
        style = 0
        if len(ring) <= 10 and a < 480 and hgt < 9.5 and r2 < 0.78 - 0.25 * core: style = 1
        elif a > 900 and hgt < 11 and r3 < 0.65: style = 2
        s = sample(sat, np.array([cen.x]), np.array([cen.y]))[0]
        if style == 1:
            pal = np.array([[176, 92, 62], [160, 80, 56], [188, 108, 74], [128, 84, 68], [112, 100, 94], [146, 70, 50]][int(r1 * 6)]) + (r3 - 0.5) * 22
        elif style == 2: pal = np.array([[86, 118, 156], [132, 140, 146], [112, 92, 78], [96, 128, 150], [150, 150, 146]][int(r1 * 5)])
        else: pal = np.array([[150, 148, 142], [128, 126, 122], [168, 162, 150], [112, 112, 114], [140, 124, 110], [182, 178, 168]][int(r1 * 6)])
        col = np.clip(0.3 * np.clip(s * 1.5 + 18, 0, 255) + 0.7 * pal, 0, 255).astype(np.uint8)
        base = float(sample(hcore, np.array([cen.x]), np.array([cen.y]))[0])
        ci, cj = int((cen.x + HX) // CHUNK), int((cen.y + HY) // CHUNK)
        ch = chunks.setdefault((ci, cj), {"n": [], "h": [], "f": [], "b": [], "c": [], "v": []})
        ox, oy = -HX + (ci + 0.5) * CHUNK, -HY + (cj + 0.5) * CHUNK
        ch["n"].append(len(ring)); ch["h"].append(int(round(hgt * 2))); ch["f"].append(style | (int(r3 * 31) << 3))
        ch["b"].append(int(round(max(base, 0.3) * 10))); ch["c"].append(col)
        ch["v"].append(np.clip(np.round((ring - [ox, oy]) / Q), -32767, 32767).astype(np.int16))
        db.polygon(pix(ring, MW, MH), fill=255)
        nb += 1; nv += len(ring)
print("  buildings", nb, "verts", nv, src)

blob = bytearray(); man = []
for (ci, cj), ch in sorted(chunks.items()):
    n = len(ch["n"]); v = np.concatenate(ch["v"])
    off = len(blob)
    blob += np.asarray(ch["n"], np.uint8).tobytes() + np.asarray(ch["h"], np.uint8).tobytes()
    blob += np.asarray(ch["f"], np.uint8).tobytes() + np.asarray(ch["c"], np.uint8).tobytes()
    blob += np.asarray(ch["b"], np.int16).tobytes() + v.tobytes()
    man.append({"i": ci, "j": cj, "n": n, "v": len(v), "o": off})
open(f"{OUT}/buildings.bin", "wb").write(blob)

# ---------------------------------------------------------------- masks + trees
print("masks…", flush=True)
water_s = water.resize((MW, MH), Image.LANCZOS)
road_s = road.resize((MW, MH), Image.LANCZOS)
rail_s = rail.resize((MW, MH), Image.LANCZOS)
ao = bmask.filter(ImageFilter.GaussianBlur(2.2))
satL = Image.fromarray(sat.astype(np.uint8)).resize((MW, MH), Image.BICUBIC)
sa = np.asarray(satL).astype(np.float32)
r, g, b = sa[..., 0], sa[..., 1], sa[..., 2]
veg = np.clip((g - np.maximum(r, b) * 0.97) / 14.0, 0, 1) * np.clip((150 - (r + g + b) / 3) / 60, 0, 1)
veg = np.asarray(Image.fromarray((veg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
wa = np.asarray(water_s).astype(np.float32) / 255
veg = veg * (1 - np.clip(wa * 3, 0, 1))
Image.merge("RGB", [road_s, water_s, Image.fromarray((veg * 255).astype(np.uint8))]).save(f"{OUT}/masks.jpg", quality=90)
Image.merge("RGB", [rail_s, ao, Image.new("L", (MW, MH), 0)]).save(f"{OUT}/masks2.jpg", quality=88)

print("trees…", flush=True)
rng = np.random.default_rng(7)
block = (np.asarray(bmask.filter(ImageFilter.MaxFilter(3))) > 0) | (np.asarray(road_s) > 60) | (wa > 0.15) | (np.asarray(rail_s) > 60)
NT = 1_400_000
tx = rng.uniform(-HX, HX, NT); ty = rng.uniform(-HY, HY, NT)
px = np.clip(((tx + HX) / (2 * HX) * MW).astype(int), 0, MW - 1); py = np.clip(((HY - ty) / (2 * HY) * MH).astype(int), 0, MH - 1)
keep = (~block[py, px]) & (rng.uniform(0, 1, NT) < veg[py, px] * 0.9 + 0.02)
tx, ty = tx[keep], ty[keep]
tsize = rng.uniform(0, 1, len(tx)); tkind = (rng.uniform(0, 1, len(tx)) < 0.5).astype(np.uint8)
tci = ((tx + HX) // CHUNK).astype(int); tcj = ((ty + HY) // CHUNK).astype(int)
tblob = bytearray(); tman = []
for ci in range(NCX):
    for cj in range(NCY):
        m = (tci == ci) & (tcj == cj); n = int(m.sum())
        if not n: continue
        ox, oy = -HX + (ci + 0.5) * CHUNK, -HY + (cj + 0.5) * CHUNK
        v = np.stack([np.round((tx[m] - ox) / Q), np.round((ty[m] - oy) / Q)], 1).astype(np.int16)
        tman.append({"i": ci, "j": cj, "n": n, "o": len(tblob)})
        tblob += v.tobytes() + (tsize[m] * 255).astype(np.uint8).tobytes() + tkind[m].tobytes()
open(f"{OUT}/trees.bin", "wb").write(tblob)
print("  trees", len(tx))

# ---------------------------------------------------------------- terrain + imagery
print("terrain…", flush=True)
def hgrid(h, w, hh):
    im = Image.fromarray(h.astype(np.float32), "F").resize((w, hh), Image.BILINEAR)
    return np.asarray(im)
GW, GH = 257, int(round(256 * HY / HX)) + 1
hc = hgrid(hcore, GW, GH).copy()
wsm = np.asarray(water_s.resize((GW, GH), Image.BILINEAR)).astype(np.float32) / 255
hc = np.where(wsm > 0.5, np.minimum(hc, 0.0), np.maximum(hc, 0.4))
hc = np.clip(hc, -20, 3000)
np.round((hc + 100) * 10).astype(np.uint16).tofile(f"{OUT}/height_core.bin")
BW_, BH_ = 257, 251
hb = hgrid(hback, BW_, BH_)
np.round((np.clip(hb, -90, 3000) + 100) * 10).astype(np.uint16).tofile(f"{OUT}/height_back.bin")
Image.fromarray(sat.astype(np.uint8)).save(f"{OUT}/sat_core.jpg", quality=88)
sb = Image.open(f"{RAW}/sat_back_{LAYER}.png").convert("RGB")
# backdrop sea mask in alpha-free form: store as separate small png
seab = (hgrid(hback, 512, 498) < -0.3).astype(np.uint8) * 255
Image.fromarray(seab).filter(ImageFilter.GaussianBlur(1.2)).save(f"{OUT}/sea_back.png")
sb.save(f"{OUT}/sat_back.jpg", quality=86)

manifest = {
    "center": [geo.LON0, geo.LAT0], "mx": geo.MX, "my": geo.MY, "halfX": HX, "halfY": HY,
    "back": [geo.BX0, geo.BY0, geo.BX1, geo.BY1], "chunk": CHUNK, "ncx": NCX, "ncy": NCY, "q": Q,
    "grid": [GW, GH], "gridBack": [BW_, BH_], "buildings": nb, "heightSrc": src,
    "bChunks": man, "tChunks": tman, "trees": int(len(tx)), "release": "2026-10-21.0",
}
json.dump(manifest, open(f"{OUT}/manifest.json", "w"), separators=(",", ":"))
print("done", {k: manifest[k] for k in ("buildings", "trees", "ncx", "ncy", "grid")})
