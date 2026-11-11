"""All roads + rail as simplified polylines in local metres -> ../data/roads.json"""
import json, duckdb, shapely, numpy as np
from shapely import wkb as swkb
import geo
R, OUT = "../data/raw", "../data"
HX, HY = geo.HALF_X, geo.HALF_Y
WIDTH = {"motorway": 16, "trunk": 14, "primary": 12, "secondary": 9.5, "tertiary": 7.5, "residential": 5,
         "unclassified": 5, "unknown": 4.5, "living_street": 4, "service": 3.5, "pedestrian": 4, "track": 3, "path": 2, "footway": 2}
CLS = {"motorway": 0, "trunk": 0, "primary": 1, "secondary": 2, "tertiary": 3}
out = []
for wkb_, sub, cls in duckdb.connect().execute(f"select wkb, subtype, class from '{R}/segments.parquet'").fetchall():
    g = swkb.loads(bytes(wkb_))
    for l in (g.geoms if g.geom_type == "MultiLineString" else [g]):
        if l.geom_type != "LineString": continue
        if sub == "rail": c, w = 9, 3.4
        elif sub == "road" and cls in WIDTH: c, w = CLS.get(cls, 5 if WIDTH[cls] <= 2 else 4), WIDTH[cls]
        else: continue
        a = np.asarray(l.coords)[:, :2]
        p = np.stack([(a[:, 0] - geo.LON0) * geo.MX, (a[:, 1] - geo.LAT0) * geo.MY], 1)
        if not ((np.abs(p[:, 0]) < HX + 50) & (np.abs(p[:, 1]) < HY + 50)).any(): continue
        s = np.asarray(shapely.LineString(p).simplify(0.8).coords)
        out.append({"c": c, "w": w, "p": [round(float(v), 1) for v in s.reshape(-1)]})
json.dump(out, open(f"{OUT}/roads.json", "w"), separators=(",", ":"))
print(len(out), "lines")
