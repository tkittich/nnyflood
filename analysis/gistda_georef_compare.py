# เทียบพื้นที่น้ำท่วม: แผนที่ GISTDA (georeferenced) vs Sentinel-1 ของเรา
#
# ใช้ _georef_gistda.json (affine lon,lat -> px ที่ได้จาก graticule) สุ่มสีน้ำท่วม
# จากแผนที่ GISTDA ลงบน grid เดียวกับ S1 (data/13/derived/grid.json) แล้วคิด IoU/F1
#
# ความหมายของสีบนแผนที่ GISTDA (สุ่มจาก swatch/พื้นที่จริง):
#   น้ำท่วม  = ฟ้าสด (vivid cyan)  B-R > 150   -> ใช้เป็นชั้น "flood"
#   ชั้นฟ้าอ่อน (B-R 60..150) อยู่นอกจังหวัดเกือบทั้งหมด (26 km^2) = คนละชั้น ไม่นับ
import json
from pathlib import Path

import numpy as np
import cv2

# อิง __file__ ไม่ใช่ cwd — รันจากโฟลเดอร์ไหนก็ได้ (ตาม convention สคริปต์อื่นใน analysis/)
PROJ = Path(__file__).resolve().parent.parent
ROOT = PROJ / "data" / "08_dem_topography" / "satellite_gistda_28sep02oct"
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"
IMGP = ROOT / "S__5980182_gistda_28sep02oct.jpg"


def gistda_flood_on_grid():
    """คืน bool array (ny,nx) ว่าช่อง grid ไหนเป็นน้ำท่วมตามแผนที่ GISTDA"""
    g = json.load(open(DER / "grid.json", encoding="utf-8"))
    p = json.load(open(ROOT / "_georef_gistda.json", encoding="utf-8"))
    cx, cy = p["affine_x"], p["affine_y"]
    nx, ny = g["nx"], g["ny"]
    x0, x1, y0, y1 = g["x0"], g["x1"], g["y0"], g["y1"]

    im = cv2.imread(IMGP)
    H, W = im.shape[:2]
    B = im[..., 0].astype(np.int16)
    R = im[..., 2].astype(np.int16)
    vivid = (B - R > 150) & (B > 200)          # ชั้นน้ำท่วม

    lon = x0 + (np.arange(nx) + 0.5) * (x1 - x0) / nx
    lat = y1 - (np.arange(ny) + 0.5) * (y1 - y0) / ny
    px = np.clip(np.rint(cx[0] * lon + cx[2]).astype(np.int64), 0, W - 1)
    py = np.clip(np.rint(cy[1] * lat + cy[2]).astype(np.int64), 0, H - 1)
    out = vivid[np.ix_(py, px)]                 # (ny,nx)
    inside = ((cx[0] * lon + cx[2]) >= 1602) & ((cx[0] * lon + cx[2]) <= 7419)
    out &= inside[None, :]
    return out


def confusion(a, b, mask):
    a = a & mask
    b = b & mask
    tp = int((a & b).sum())
    fp = int((a & ~b).sum())
    fn = int((~a & b).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 0.0
    return tp, fp, fn, prec, rec, f1, iou


def main():
    g = json.load(open(f"{DER}/grid.json", encoding="utf-8"))
    nx, ny = g["nx"], g["ny"]
    lat_mid = 14.24
    cell = (g["res"] * 111320 * np.cos(np.radians(lat_mid))) * (g["res"] * 110574)
    prov = np.load(f"{DER}/mask_province.npy")

    gflood = gistda_flood_on_grid()
    print(f"GISTDA flood px = {int(gflood.sum())} -> {gflood.sum()*cell/1e6:.1f} km^2 (ทั้งแผนที่)")
    print(f"   ในจังหวัด = {(gflood&prov).sum()*cell/1e6:.1f} km^2")

    for name, f in [("S1 2 ต.ค.", "flood_2oct_validated.npy"),
                    ("S1 peak 27 ก.ย.", "flood_peak_27sep1828.npy")]:
        ours = np.load(f"{DER}/{f}")
        tp, fp, fn, pr, rc, f1, iou = confusion(ours, gflood, prov)
        print(f"\n{name} (ในจังหวัด) vs GISTDA:")
        print(f"  ของเรา = {ours[prov].sum()*cell/1e6:.1f} km^2 | GISTDA = {(gflood&prov).sum()*cell/1e6:.1f} km^2")
        print(f"  TP={tp*cell/1e6:.1f}  FP={fp*cell/1e6:.1f}  FN={fn*cell/1e6:.1f} km^2")
        print(f"  precision={pr:.3f} recall={rc:.3f} F1={f1:.3f} IoU={iou:.3f}")

    np.save(f"{ROOT}/gistda_flood_mask_grid.npy", gflood)
    print(f"\nsaved {ROOT}/gistda_flood_mask_grid.npy")

    # --- แผนภาพความสอดคล้อง TP/FP/FN ---
    ours = np.load(f"{DER}/flood_2oct_validated.npy") & prov
    gg = gflood & prov
    ny, nx = ours.shape
    img = np.full((ny, nx, 3), 255, np.uint8)
    img[ours & ~gg] = (255, 0, 0)      # น้ำเงิน = ของเราอย่างเดียว (FP)
    img[~ours & gg] = (0, 0, 255)      # แดง = GISTDA อย่างเดียว (FN)
    img[ours & gg] = (0, 170, 0)       # เขียว = ตรงกัน (TP)
    img[~prov] = (235, 235, 235)
    ys, xs = np.where(prov)
    crop = img[ys.min():ys.max(), xs.min():xs.max()]
    cv2.imwrite(f"{ROOT}/_compare_s1_vs_gistda.png", crop)
    print(f"saved {ROOT}/_compare_s1_vs_gistda.png (เขียว=ตรงกัน น้ำเงิน=เราเท่านั้น แดง=GISTDA เท่านั้น)")


if __name__ == "__main__":
    main()
