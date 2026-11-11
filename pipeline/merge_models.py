"""Collect models/*.place.json into models/manifest.json, adding a ground height where a scene needs one."""
import json, glob, os, numpy as np
M = json.load(open("../data/manifest.json")); GW, GH = M["grid"]; HX, HY = M["halfX"], M["halfY"]
H = np.fromfile("../data/height_core.bin", np.uint16).reshape(GH, GW) / 10 - 100
def h(x, n):
    u = (x + HX) / (2 * HX) * (GW - 1); v = (HY - n) / (2 * HY) * (GH - 1)
    return float(H[int(round(min(max(v, 0), GH - 1))), int(round(min(max(u, 0), GW - 1)))])
GROUND = {  # points (local metres east, north) whose median ground height the scene should sit on
    "mananchira": [(-1717, 3331), (-1695, 3178), (-1556, 3199), (-1578, 3349), (-1500, 3160)],
    "smstreet": [(-1477, 3082), (-1468, 3014), (-1466, 2854), (-1458, 2740), (-1461, 2637)],
    "beach": [(-2760, 3420), (-2785, 3527), (-2818, 3639), (-2832, 3712)],
    "mishkal": [(-2075, 2279), (-2046, 2279), (-2060, 2292), (-2060, 2266)],
    "tali": [(-880, 2507), (-832, 2507), (-856, 2527), (-856, 2487)],
}
out = [{"f": "models/tinkerspace.glb", "x": 5376.0, "n": 5897.0, "deg": 0, "rx": 14, "rz": 17},
       {"f": "models/ipm.glb", "x": 5396.5, "n": 5816.7, "deg": 2.1, "rx": 20, "rz": 9.5}]
for f in sorted(glob.glob("../models/*.place.json")):
    p = json.load(open(f)); name = os.path.basename(f).split(".")[0]
    if name in GROUND: p["y"] = round(float(np.median([h(*q) for q in GROUND[name]])), 2); p["drape"] = name in ("mananchira", "smstreet", "beach"); print(name, [round(h(*q), 1) for q in GROUND[name]], "->", p["y"])
    out.append(p)
json.dump(out, open("../models/manifest.json", "w"), indent=1); print(len(out), "models")
