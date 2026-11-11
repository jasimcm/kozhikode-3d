# Kozhikode 3D

A 3D model of Kozhikode (Calicut), Kerala, built from open map data. Live at https://kozhikode-3d.vercel.app

- Buildings, roads, rail, water and places: Overture Maps Foundation (includes OpenStreetMap contributors, ODbL)
- Terrain: Mapzen / AWS Terrain Tiles
- Ground imagery: Sentinel-2 cloudless 2020 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2020), CC BY-NC-SA 4.0 (non-commercial)
- Ward boundaries: Delimitation Commission, Kerala / Information Kerala Mission (K-SMART ward map); no formal open licence
- Landmark models: built in Blender from photo reference (`pipeline/blender_*.py`), stylised

Building heights are mostly estimated from footprint size, not measured.

## Run locally

    python3 serve.py 5183

then open http://localhost:5183

## Rebuild data

Scripts are in `pipeline/` (`fetch_overture.py`, `fetch_tiles.py`, `build.py`, `roads.py`, `extras.py`, `merge_models.py`). They need Python with duckdb, shapely, numpy, pillow and requests.
