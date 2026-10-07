# ปรับ affine georeference ของแผนที่ GISTDA สำเร็จรูป ให้เส้นขอบจังหวัด OSM ทับเส้นประดำ
# เร็ว: distance transform คำนวณครั้งเดียว + ตรวจจับเส้นด้วย morphology (แยกจากข้อความ)
import json
from pathlib import Path

import numpy as np
import cv2
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent.parent   # อิง __file__ ไม่ใช่ cwd
im = cv2.imread(str(ROOT / "data" / "08_dem_topography" / "satellite_gistda_28sep02oct"
                   / "S__5980182_gistda_28sep02oct.jpg"))
x0, x1, y0, y1 = 1610, 7500, 410, 4600
sub = im[y0:y1, x0:x1]
b, g, r = sub[..., 0].astype(int), sub[..., 1].astype(int), sub[..., 2].astype(int)
dark = ((b < 110) & (g < 110) & (r < 110)).astype(np.uint8)
k_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
k_h = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
lines = cv2.morphologyEx(dark, cv2.MORPH_OPEN, k_v) | cv2.morphologyEx(dark, cv2.MORPH_OPEN, k_h)
dist = cv2.distanceTransform((lines == 0).astype(np.uint8), cv2.DIST_L2, 3).astype(np.float32)
print("เส้นพิกเซล:", int(lines.sum()))

bnd = json.load(open(ROOT / "data" / "13_sentinel1_copernicus" / "derived" / "osm_nakhonnayok_boundary.json", encoding="utf-8"))["geojson"]
ring = np.array(bnd["coordinates"][0] if bnd["type"] == "Polygon" else bnd["coordinates"][0][0])
lon0, lat0 = 101.0, 14.33333

def loss(p):
    sx, sy, tx, ty = p
    px = tx + (ring[:, 0] - lon0) * sx
    py = ty - (ring[:, 1] - lat0) * sy
    ok = (px >= 0) & (px < sub.shape[1]) & (py >= 0) & (py < sub.shape[0])
    if ok.sum() < 100:
        return 1e9
    return float(dist[py[ok].astype(int), px[ok].astype(int)].mean())

p0 = np.array([8550.0, 3540.0, 2455.0 - 1610.0, 1440.0 - 410.0])   # tx,ty เทียบ sub
print("loss เริ่ม:", round(loss(p0), 2), "px")
res = minimize(loss, p0, method="Powell",
               options={"maxiter": 400, "xtol": 0.3, "ftol": 0.01})
best = res.x
print("loss fit:", round(res.fun, 2), "px | params:", [round(v, 1) for v in best])
sx, sy, tx, ty = best
print(f"สเกล: {111320/sx:.2f} ม./px lon · {110574/sy:.2f} ม./px lat")
print(f"anchor: lon 101.0 -> x {tx + x0:.0f} | lat 14.33333 -> y {ty + y0:.0f}")
np.save(ROOT / "data" / "08_dem_topography" / "satellite_gistda_28sep02oct" / "_georef_params.npy", np.array([sx, sy, tx + x0, ty + y0]))
print("saved params (เทียบ full-image coords)")
