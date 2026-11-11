"""Wards + locality labels -> ../data/wards.json, ../data/localities.json"""
import json, duckdb, shapely
from shapely.geometry import shape
from shapely import wkb as swkb
import numpy as np, geo
R, OUT = "../data/raw", "../data"
HX, HY = geo.HALF_X, geo.HALF_Y
out = []
for f in json.load(open(f"{R}/wards.geojson"))["features"]:
    g = shape(f["geometry"]); p = f["properties"]
    rings = []
    for poly in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        c = np.asarray(poly.exterior.coords)[:, :2]
        xy = np.stack([(c[:, 0] - geo.LON0) * geo.MX, (c[:, 1] - geo.LAT0) * geo.MY], 1)
        s = shapely.Polygon(xy).simplify(6.0)
        if s.is_empty or s.geom_type != "Polygon": continue
        rings.append([round(float(v), 1) for v in np.asarray(s.exterior.coords).reshape(-1)])
    cx, cy = geo.to_xy(g.representative_point().x, g.representative_point().y)
    if not rings: continue
    out.append({"no": p["ward_no"], "name": p["ward_name"], "c": [round(cx, 1), round(cy, 1)], "r": rings})
json.dump(out, open(f"{OUT}/wards.json", "w"), separators=(",", ":"), ensure_ascii=False)
print("wards", len(out))
con = duckdb.connect()
loc = []
for wkb_, sub, name, common in con.execute(f"select wkb, subtype, name, common from '{R}/division.parquet' where subtype in ('locality','macrohood','neighborhood')").fetchall():
    g = swkb.loads(bytes(wkb_)).centroid
    x, y = geo.to_xy(g.x, g.y)
    if abs(x) > HX or abs(y) > HY or name.startswith("Kozhikode Municipal") or name in ("Kozhikode", "Skyline Meadows", "Markazudaawa", "Malaparamba Housing Colony"): continue
    ml = (json.loads(common) or {}).get("ml") if common else None
    loc.append({"n": name, "ml": ml.replace("‌", "") if ml else None, "x": round(x), "y": round(y), "t": sub})
json.dump(loc, open(f"{OUT}/localities.json", "w"), separators=(",", ":"), ensure_ascii=False)
print("localities", len(loc))
