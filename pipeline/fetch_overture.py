"""Download Overture Maps data for the Kozhikode bbox into data/raw/*.parquet."""
import sys, time, json, urllib.request
import duckdb

W, S, E, N = 75.735, 11.150, 75.855, 11.300
OUT = "../data/raw"

def latest_release():
    try:
        with urllib.request.urlopen("https://stac.overturemaps.org/catalog.json", timeout=30) as r:
            cat = json.load(r)
        if cat.get("latest"):
            return cat["latest"]
        rels = sorted(l["href"].strip("./").split("/")[0] for l in cat["links"] if l.get("rel") == "child")
        return rels[-1]
    except Exception as e:
        print("stac failed", e)
        return "2026-10-21.0"

REL = sys.argv[1] if len(sys.argv) > 1 else latest_release()
print("release", REL, flush=True)
BASE = f"s3://overturemaps-us-west-2/release/{REL}"

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")

BBOX = f"bbox.xmin <= {E} AND bbox.xmax >= {W} AND bbox.ymin <= {N} AND bbox.ymax >= {S}"

JOBS = {
    "buildings": ("theme=buildings/type=building",
        "id, ST_AsWKB(geometry) AS wkb, height, num_floors, class, subtype, roof_shape, names.primary AS name"),
    "segments": ("theme=transportation/type=segment",
        "id, ST_AsWKB(geometry) AS wkb, subtype, class, names.primary AS name"),
    "water": ("theme=base/type=water",
        "id, ST_AsWKB(geometry) AS wkb, subtype, class, names.primary AS name"),
    "land": ("theme=base/type=land",
        "id, ST_AsWKB(geometry) AS wkb, subtype, class, names.primary AS name"),
    "land_use": ("theme=base/type=land_use",
        "id, ST_AsWKB(geometry) AS wkb, subtype, class, names.primary AS name"),
    "land_cover": ("theme=base/type=land_cover",
        "id, ST_AsWKB(geometry) AS wkb, subtype, cartography.min_zoom AS min_zoom, cartography.max_zoom AS max_zoom"),
    "division_area": ("theme=divisions/type=division_area",
        "id, ST_AsWKB(geometry) AS wkb, subtype, class, names.primary AS name, to_json(names.common) AS common, admin_level"),
    "division": ("theme=divisions/type=division",
        "id, ST_AsWKB(geometry) AS wkb, subtype, class, names.primary AS name, to_json(names.common) AS common, population"),
    "places": ("theme=places/type=place",
        "id, ST_AsWKB(geometry) AS wkb, names.primary AS name, to_json(names.common) AS common, confidence"),
}

only = sys.argv[2:] or list(JOBS)
for name in only:
    path, cols = JOBS[name]
    t = time.time()
    try:
        con.execute(f"""COPY (SELECT {cols} FROM read_parquet('{BASE}/{path}/*', hive_partitioning=1)
                        WHERE {BBOX}) TO '{OUT}/{name}.parquet' (FORMAT parquet)""")
        n = con.execute(f"SELECT count(*) FROM '{OUT}/{name}.parquet'").fetchone()[0]
        print(f"{name}: {n} rows in {time.time()-t:.0f}s", flush=True)
    except Exception as e:
        print(f"{name}: FAILED {str(e)[:400]}", flush=True)
