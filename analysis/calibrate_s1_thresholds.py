"""ค้น threshold ของกฎ 3 เงื่อนไข โดย maximize F1 เทียบ GISTDA บนฉาก 2 ต.ค. (producer ของ METHODS §6)

นี่คือสคริปต์คาลิเบรตที่เอกสารอ้าง ("ตั้งค่าโดย maximize F1 กับผล GISTDA") — ก่อนหน้านี้
ไม่มีไฟล์จริงใน repo (ผลรีวิว GLM GL-04; ตัวเดิมยุค 5 ต.ค. เป็น inline script VH-only
2 เงื่อนไข ซึ่งให้คนละมาสก์ 564.4 ตร.กม. — ห้ามกลับไปใช้)

ค้นตาราง (DROP_VH, DROP_VV, ABS_VH) บนกริดคร่าว ๆ รอบค่า canonical (1.0, 2.0, −18.0)
แล้วรายงาน top-10 · กฎ canonical อยู่ที่ s1_change_detect.py เสมอ — สคริปต์นี้ใช้ยืนยัน
ที่มาของค่า ไม่ใช่เปลี่ยนค่า (เปลี่ยน threshold = ต้องประกาศ canonical ชุดใหม่ทั้งรายงาน)

ใช้: `python analysis/calibrate_s1_thresholds.py`   # ~1 นาที (504 คู่ threshold × 5.1 ล้าน px)
"""
import json

import numpy as np

from s1_change_detect import (ABS_VH, DER, DROP_VH, DROP_VV, load_gistda_mask,
                              detect, prf)
from common import cell_km2


def main():
    g = json.load(open(DER / "grid.json"))
    CELL = cell_km2(g["res"])
    lowland = np.load(DER / "mask_lowland.npy")
    gis = load_gistda_mask(g)

    pre_vh = np.load(DER / "s1d_20260920_0609_vh_db.npy")
    post_vh = np.load(DER / "s1d_20261002_0609_vh_db.npy")
    pre_vv = np.load(DER / "s1d_20260920_0609_vv_db.npy")
    post_vv = np.load(DER / "s1d_20261002_0609_vv_db.npy")

    grid = [
        (dh, dv, ab)
        for dh in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
        for dv in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)
        for ab in (-24.0, -22.0, -20.0, -19.0, -18.0, -17.0, -16.0, -15.0, -14.0, -13.0)
    ]
    print(f"ค้น {len(grid)} คู่ threshold (canonical = {(DROP_VH, DROP_VV, ABS_VH)})")
    rows = []
    for dh, dv, ab in grid:
        w = detect(pre_vh, post_vh, pre_vv, post_vv, lowland, dh, dv, ab)
        pr, rc, f1 = prf(w, gis)
        rows.append((f1, pr, rc, dh, dv, ab, w.sum() * CELL))
    rows.sort(reverse=True)

    print("\nTop-10 โดย F1:")
    for f1, pr, rc, dh, dv, ab, area in rows[:10]:
        mark = "  ← canonical" if (dh, dv, ab) == (DROP_VH, DROP_VV, ABS_VH) else ""
        print(f"  DROP_VH≤-{dh} ΔVV≤-{dv} VH≤{ab} → F1={f1:.3f} (P={pr:.3f} R={rc:.3f}) น้ำ {area:.1f} ตร.กม.{mark}")

    best = rows[0]
    canon = next(r for r in rows if (r[3], r[4], r[5]) == (DROP_VH, DROP_VV, ABS_VH))
    print(f"\ncanonical F1={canon[0]:.3f} · best ในกริด F1={best[0]:.3f} ที่ {(best[3], best[4], best[5])}")
    if abs(canon[0] - best[0]) < 0.002:
        print("→ canonical อยู่บนพื้น F1 สูงสุดของกริดนี้ (ต่าง < 0.002 = แบน) — ยืนยันที่มาค่า threshold")
    else:
        print(f"⚠️ best ต่างจาก canonical {best[0] - canon[0]:+.4f} — กริดนี้ละเอียดกว่า/ต่างจากการค้นเดิม; "
              "ห้ามเปลี่ยน threshold จากสคริปต์นี้เอง (ดู docstring)")


if __name__ == "__main__":
    main()
