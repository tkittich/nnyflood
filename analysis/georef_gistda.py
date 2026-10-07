# Georeference แผนที่ GISTDA "Road Inundated Map" (S__5980182_gistda_28sep02oct.jpg)
#
# วิธี: อ่าน graticule ที่พิมพ์กำกับบนแผนที่โดยตรง (ไม่ใช้ feature matching)
#   แผนที่นี้เป็น plate carree (องศาสี่เหลี่ยม) — px/°lon = px/°lat เกือบเท่ากันเป๊ะ
#   ยืนยัน: 101°0'0"E -> x=3172, 101°20'0"E -> x=5302 (2130 px / 0.33333°)
#           14°20'0"N -> y=1977, 14°0'0"N  -> y=4106 (2129 px / 0.33333°)
#   -> px/°lon = 6390, px/°lat = 6387  (ต่างกัน 0.05% = ไม่มี shear/rotation ที่มีนัย)
#
# ผลลัพธ์: _georef_gistda.json (affine lon,lat -> x,y) + ภาพ validate ทับเส้น OSM
import json
from pathlib import Path

import numpy as np
import cv2

PROJ = Path(__file__).resolve().parent.parent        # อิง __file__ ไม่ใช่ cwd
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"
ROOT = PROJ / "data" / "08_dem_topography" / "satellite_gistda_28sep02oct"
IMGP = str(ROOT / "S__5980182_gistda_28sep02oct.jpg")
OUT_JSON = str(ROOT / "_georef_gistda.json")

# --- GCP: (lon, lat) -> (x, y) อ่านจาก graticule ที่พิมพ์บนแผนที่ ---
GCPS = [
    (101.0,      14.333333, 3172.0, 1977.0),   # 101°0'0"E , 14°20'0"N
    (101.333333, 14.333333, 5302.0, 1977.0),   # 101°20'0"E, 14°20'0"N
    (101.0,      14.0,      3172.0, 4106.0),   # 101°0'0"E , 14°0'0"N
    (101.333333, 14.0,      5302.0, 4106.0),   # 101°20'0"E, 14°0'0"N
]


def fit_affine(gcps):
    """fit x = a*lon + b*lat + c ; y = d*lon + e*lat + f (6 พารามิเตอร์)"""
    A, bx, by = [], [], []
    for lon, lat, x, y in gcps:
        A.append([lon, lat, 1.0])
        bx.append(x)
        by.append(y)
    A = np.array(A)
    cx, *_ = np.linalg.lstsq(A, np.array(bx), rcond=None)
    cy, *_ = np.linalg.lstsq(A, np.array(by), rcond=None)
    return cx, cy


def report(cx, cy, gcps):
    print("affine x = %.6f*lon + %.6f*lat + %.3f" % tuple(cx))
    print("affine y = %.6f*lon + %.6f*lat + %.3f" % tuple(cy))
    print("off-diagonal (shear/rotation):  dx/dlat=%.3f  dy/dlon=%.3f" % (cx[1], cy[0]))
    print("scale: px/deg_lon=%.1f  px/deg_lat=%.1f" % (cx[0], -cy[1]))
    mpp_lon = 111320 * np.cos(np.radians(14.24)) / cx[0]
    mpp_lat = 110574 / (-cy[1])
    print("scale: %.2f m/px (lon)  %.2f m/px (lat)" % (mpp_lon, mpp_lat))
    print("--- residual ที่ GCP ---")
    for lon, lat, x, y in gcps:
        px = cx[0] * lon + cx[1] * lat + cx[2]
        py = cy[0] * lon + cy[1] * lat + cy[2]
        print(f"  ({lon:.5f},{lat:.5f}) -> pred ({px:.1f},{py:.1f}) vs obs ({x:.1f},{y:.1f})  err=({px-x:+.1f},{py-y:+.1f})")
    return mpp_lon, mpp_lat


def to_px(cx, cy, lon, lat):
    return cx[0] * lon + cx[1] * lat + cx[2], cy[0] * lon + cy[1] * lat + cy[2]


def main():
    cx, cy = fit_affine(GCPS)
    mpp_lon, mpp_lat = report(cx, cy, GCPS)

    json.dump({"affine_x": [float(v) for v in cx], "affine_y": [float(v) for v in cy],
               "gcps": GCPS, "m_per_px_lon": float(mpp_lon), "m_per_px_lat": float(mpp_lat),
               "crs_note": "plate carree (square degrees), north-up; lon/lat = WGS84"},
              open(OUT_JSON, "w", encoding="utf-8"), indent=1)
    print("saved", OUT_JSON)

    # --- validate: ทับเส้นขอบเขต OSM บนแผนที่ ---
    im = cv2.imread(IMGP)
    bnd = json.load(open(DER / "osm_nakhonnayok_boundary.json",
                         encoding="utf-8"))["geojson"]
    outer = bnd["coordinates"][0]
    pts = np.array([[int(round(x)), int(round(y))]
                    for x, y in (to_px(cx, cy, lo, la) for lo, la in outer)])
    cv2.polylines(im, [pts], True, (0, 0, 255), 6)

    dst = json.load(open(DER / "osm_nakhonnayok_districts.json",
                         encoding="utf-8"))
    for name, v in dst.items():
        geom = v["geojson"]
        for ring in geom["coordinates"]:
            pts = np.array([[int(round(x)), int(round(y))]
                            for x, y in (to_px(cx, cy, lo, la) for lo, la in ring)])
            cv2.polylines(im, [pts], True, (255, 0, 255), 3)

    cv2.imwrite(str(ROOT / "_validate_georef.png"), im)
    # crop ตัวเมืองไว้ดูใกล้ ๆ
    cv2.imwrite(str(ROOT / "_validate_georef_town.png"), im[1600:3200, 2800:4600])
    print("saved _validate_georef.png / _validate_georef_town.png")


if __name__ == "__main__":
    main()
