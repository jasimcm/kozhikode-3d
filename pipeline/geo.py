"""Shared grid definition: a local metric grid centred on Kozhikode."""
import math

W, S, E, N = 75.735, 11.150, 75.855, 11.300          # detailed 3D area
BW, BS, BE, BN = 75.53, 10.97, 76.06, 11.48          # backdrop (terrain + imagery only)
LON0, LAT0 = (W + E) / 2, (S + N) / 2
MX = 111320.0 * math.cos(math.radians(LAT0))         # metres per degree lon
MY = 110574.0                                        # metres per degree lat

def to_xy(lon, lat):
    """lon/lat -> metres east, metres north of the grid centre."""
    return (lon - LON0) * MX, (lat - LAT0) * MY

def to_ll(x, y):
    return LON0 + x / MX, LAT0 + y / MY

HALF_X = (E - LON0) * MX
HALF_Y = (N - LAT0) * MY
BX0, BY0 = to_xy(BW, BS)
BX1, BY1 = to_xy(BE, BN)
