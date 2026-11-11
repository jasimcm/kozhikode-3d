"""Fetch Sentinel-2 cloudless imagery + terrarium elevation tiles and resample to the local grid."""
import io, math, os, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np, requests
from PIL import Image
import geo

RAW = "../data/raw"
CACHE = f"{RAW}/tiles"
os.makedirs(CACHE, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "city-3d-model-builder/1.0"

SAT = {
    "s2016": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg",
    "s2020": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg",
    "s2023": "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2023_3857/default/g/{z}/{y}/{x}.jpg",
}
DEM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def get(url, key):
    p = f"{CACHE}/{key}"
    if os.path.exists(p):
        return open(p, "rb").read()
    for _ in range(4):
        try:
            r = S.get(url, timeout=40)
            if r.status_code == 200:
                open(p, "wb").write(r.content)
                return r.content
        except Exception:
            pass
    raise RuntimeError("failed " + url)

def mosaic(tpl, name, z, w, s, e, n, ext):
    x0, y0 = tile_xy(w, n, z); x1, y1 = tile_xy(e, s, z)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    jobs = [(x, y) for x in range(tx0, tx1 + 1) for y in range(ty0, ty1 + 1)]
    def one(xy):
        x, y = xy
        return xy, Image.open(io.BytesIO(get(tpl.format(z=z, x=x, y=y), f"{name}_{z}_{x}_{y}.{ext}"))).convert("RGB")
    out = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 3), np.uint8)
    with ThreadPoolExecutor(8) as ex:
        for (x, y), im in ex.map(one, jobs):
            out[(y - ty0) * 256:(y - ty0 + 1) * 256, (x - tx0) * 256:(x - tx0 + 1) * 256] = np.asarray(im)
    return out, tx0, ty0

def resample(mos, tx0, ty0, z, x0, y0, x1, y1, W, H, nearest=False):
    """Sample mosaic onto the local metric grid: (x0,y0)=SW corner metres, (x1,y1)=NE; row 0 = north."""
    xs = x0 + (np.arange(W) + 0.5) / W * (x1 - x0)
    ys = y1 - (np.arange(H) + 0.5) / H * (y1 - y0)
    lon = geo.LON0 + xs / geo.MX
    lat = geo.LAT0 + ys / geo.MY
    n = 2 ** z
    px = ((lon + 180) / 360 * n - tx0) * 256 - 0.5
    py = ((1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n - ty0) * 256 - 0.5
    PX, PY = np.meshgrid(px, py)
    PX = np.clip(PX, 0, mos.shape[1] - 1.001); PY = np.clip(PY, 0, mos.shape[0] - 1.001)
    if nearest:
        return mos[np.round(PY).astype(int), np.round(PX).astype(int)]
    ix, iy = PX.astype(int), PY.astype(int)
    fx, fy = (PX - ix)[..., None], (PY - iy)[..., None]
    m = mos.astype(np.float32)
    return (m[iy, ix] * (1 - fx) * (1 - fy) + m[iy, ix + 1] * fx * (1 - fy)
            + m[iy + 1, ix] * (1 - fx) * fy + m[iy + 1, ix + 1] * fx * fy)

def dem_to_m(rgb):
    return rgb[..., 0] * 256.0 + rgb[..., 1] + rgb[..., 2] / 256.0 - 32768.0

if __name__ == "__main__":
    layer = sys.argv[1] if len(sys.argv) > 1 else "s2020"
    hx, hy = geo.HALF_X, geo.HALF_Y
    # core imagery
    m, tx, ty = mosaic(SAT[layer], layer, 14, geo.W, geo.S, geo.E, geo.N, "jpg")
    core = resample(m, tx, ty, 14, -hx, -hy, hx, hy, 2048, int(2048 * hy / hx))
    Image.fromarray(core.astype(np.uint8)).save(f"{RAW}/sat_core_{layer}.png")
    # backdrop imagery
    m, tx, ty = mosaic(SAT[layer], layer, 12, geo.BW, geo.BS, geo.BE, geo.BN, "jpg")
    bw = 1536; bh = int(bw * (geo.BY1 - geo.BY0) / (geo.BX1 - geo.BX0))
    back = resample(m, tx, ty, 12, geo.BX0, geo.BY0, geo.BX1, geo.BY1, bw, bh)
    Image.fromarray(back.astype(np.uint8)).save(f"{RAW}/sat_back_{layer}.png")
    # elevation
    m, tx, ty = mosaic(DEM, "dem", 13, geo.W, geo.S, geo.E, geo.N, "png")
    h = resample(dem_to_m(m.astype(np.float32))[..., None], tx, ty, 13, -hx, -hy, hx, hy, 512, int(512 * hy / hx))[..., 0]
    np.save(f"{RAW}/h_core.npy", h.astype(np.float32))
    m, tx, ty = mosaic(DEM, "dem", 11, geo.BW, geo.BS, geo.BE, geo.BN, "png")
    hb = resample(dem_to_m(m.astype(np.float32))[..., None], tx, ty, 11, geo.BX0, geo.BY0, geo.BX1, geo.BY1, 512, int(512 * bh / bw))[..., 0]
    np.save(f"{RAW}/h_back.npy", hb.astype(np.float32))
    print("core", core.shape, "back", back.shape, "h", h.shape, h.min(), h.max(), "hb", hb.shape, hb.min(), hb.max())
