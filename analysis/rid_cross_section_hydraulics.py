# ตรวจไขว้รูปตัดขวางจริง (RID) กับ rating curve ของโปรเจค
#   - สร้างฟังก์ชัน ground(x) จากเส้นสำรวจ (interpolate เชิงเส้น)
#   - คำนวณ ความกว้างผิวน้ำ / พื้นที่เปียก / wetted perimeter / R ตามระดับน้ำ
#   - Manning: Q = (1/n) A R^(2/3) S^(1/2)  -> หา n ที่ทำให้ Q ตรงกับค่าที่โปรเจคใช้
# อ้างอิงค่าของโปรเจค: rating Q = 242*(h-4.55)^0.66 (h = ม.รทก.) · datum Ny.7 เกจ = ม.รทก.+1.59
#                      ความลาดท้องน้ำ ~9 ม./28 กม. (terrain_mueang_analysis)
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DER = ROOT / "data" / "19_rid_cross_sections" / "derived"

SLOPE = 9.0 / 28000.0  # m/m จากโปรไฟล์แม่น้ำของโปรเจค
GAUGE_OFFSET = 1.59    # เกจ = ม.รทก. + 1.59


def load(stem):
    pts = []
    with open(DER / f"{stem}_profile.csv", encoding="utf-8") as f:
        next(f)
        for line in f:
            off, elev, _ = line.split(",", 2)
            pts.append((float(off), float(elev)))
    pts.sort()
    return np.array(pts)


def ground_at(xs, ys, x):
    return np.interp(x, xs, ys)


def geometry(xs, ys, stage, dx=0.25):
    """ความกว้างผิวน้ำ/พื้นที่เปียก/เส้นรอบเปียก ที่ระดับน้ำ stage (ม.รทก.)

    ระวัง: perim ห้ามใช้ width + (span) ≈ 2 เท่าของความกว้างผิวน้ำ
    เพราะนับ "ผิวน้ำอิสระ" เป็นขอบเปียกด้วย — มาตรฐาน (และ HEC-RAS) ไม่นับ
    ต้องใช้ความยาวผิวดินที่จมน้ำ + หน้าตัดแนวตั้งสองข้าง
    ถ้านับผิวน้ำ R จะต่ำเกิน ~2 เท่า → Q ต่ำเกิน ~1.63 เท่า → ได้ n ต่ำผิดปกติ
    """
    grid = np.arange(xs.min(), xs.max() + dx, dx)
    g = ground_at(xs, ys, grid)
    depth = np.clip(stage - g, 0.0, None)
    area = float(depth.sum() * dx)
    wet = depth > 0
    width = float(wet.sum() * dx)
    perim = 0.0
    idx = np.where(wet)[0]
    if len(idx):
        for k in range(len(idx) - 1):
            if idx[k + 1] == idx[k] + 1:
                perim += math.hypot(dx, g[idx[k + 1]] - g[idx[k]])
        perim += float(depth[idx[0]] + depth[idx[-1]])   # หน้าตัดแนวตั้งสองข้าง
    return width, area, perim


def manning_q(area, perim, n):
    if area <= 0 or perim <= 0:
        return 0.0
    R = area / perim
    return (1.0 / n) * area * (R ** (2.0 / 3.0)) * (SLOPE ** 0.5)


def project_rating(h_msl):
    """rating curve ของโปรเจค (ใช้เฉพาะช่วง h>4.55)"""
    return 242.0 * max(h_msl - 4.55, 0.0) ** 0.66


def main():
    report = {}
    for stem, peak_msl, peak_gauge in [("Ny.7", 7.64, 9.23), ("Ny.1B", 11.07, 11.0)]:
        pts = load(stem)
        xs, ys = pts[:, 0], pts[:, 1]
        print(f"\n===== {stem} =====")
        print(f"  ช่วงสำรวจ offset {xs.min():g}..{xs.max():g} m · ต่ำสุด {ys.min():.3f} · สูงสุด {ys.max():.3f} ม.รทก.")

        # เส้นระดับตลิ่ง: จุดเปลี่ยนความชัน = ขอบร่องน้ำ (offset 0 และ 100)
        print("  ระดับตามช่วง:")
        for stage in [4.55, 5.0, 6.0, 6.86, 7.64, 8.0, 8.213, 8.919, 9.5]:
            w, a, p = geometry(xs, ys, stage)
            print(f"    stage {stage:5.2f} ม.รทก. (เกจ {stage + GAUGE_OFFSET:5.2f}) | "
                  f"กว้าง {w:6.1f} ม. | พื้นที่ {a:7.1f} ตร.ม. | รอบเปียก {p:6.1f} ม. | "
                  f"Q@n=0.035 {manning_q(a, p, 0.035):7.1f}")

        w, a, p = geometry(xs, ys, peak_msl)
        qp = project_rating(peak_msl)
        print(f"\n  --- ณ ระดับสูงสุดเหตุการณ์ {peak_msl} ม.รทก. (เกจ {peak_gauge}) ---")
        print(f"    กว้างผิวน้ำ {w:.1f} ม. · พื้นที่เปียก {a:.1f} ตร.ม. · รอบเปียก {p:.1f} ม. · R {a/p:.2f} ม.")
        print(f"    Q จาก rating curve ของโปรเจค = {qp:.0f} ม³/วิ")
        for n in (0.030, 0.035, 0.040, 0.045):
            print(f"    Q จาก Manning (n={n}) = {manning_q(a, p, n):7.1f} ม³/วิ")
        # n ที่ทำให้ Manning ตรงกับ rating ของโปรเจค — fit เฉพาะสถานีที่ datum ยืนยันแล้ว
        # GL-08: Ny.1B ยังไม่มี datum ที่ยืนยัน (11.07 ต่อเกจ 11.0 = offset −0.07 ขัด convention
        # +1.59 ของ Ny.7; METHODS §5) → n ที่ fit ได้เดิม (0.0223) ใช้ไม่ได้ จึงไม่ fit
        if stem == "Ny.7":
            lo, hi = 0.015, 0.20
            for _ in range(80):
                mid = (lo + hi) / 2
                if manning_q(a, p, mid) > qp:
                    lo = mid
                else:
                    hi = mid
            print(f"    -> n ที่ทำให้ Manning = rating curve: {lo:.4f}")
            n_fit = round(lo, 4)
        else:
            print("    -> (ข้าม fit n — datum ของสถานียังไม่ยืนยัน รอ FOI สช.9)")
            n_fit = None
        report[stem] = {
            "offset_range_m": [float(xs.min()), float(xs.max())],
            "bed_min_msl": float(ys.min()),
            "crest_max_msl": float(ys.max()),
            "peak_stage_msl": peak_msl,
            "peak_gauge_m": peak_gauge,
            "peak_width_m": round(w, 1),
            "peak_area_m2": round(a, 1),
            "peak_perimeter_m": round(p, 1),
            "peak_hydraulic_radius_m": round(a / p, 2),
            "project_rating_q_cms": round(qp, 1),
            "manning_n_fitted": n_fit,
            "manning_n_note": None if n_fit is not None else "ข้าม — datum สถานียังไม่ยืนยัน (GL-08)",
        }

    out = DER / "cross_section_hydraulics.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
