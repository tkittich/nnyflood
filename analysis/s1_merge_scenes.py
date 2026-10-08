"""โมเสก 2 slice ของฉาก S1 ที่ทับกัน → ไฟล์ `*_full_*` ที่ s1_change_detect.py ใช้

นี่คือ **producer** ของ npy ขาดหายใน repo (ผลรีวิว GLM GL-04) — กฎที่ตรวจสอบแล้ว
(8 ต.ค. 69 เทียบ byte-identical กับไฟล์เดิมทั้ง 2 วัน × 2 โพลาไรซ์, diff = 0.0):

    full = where(isfinite(หลัก), หลัก, รอง)      # หลัก = slice a (หรือไฟล์ไม่มีตัวอักษรของ 27/9)
    full_valid = isfinite(full)                   # พิกเซลที่มีข้อมูลจริง

slice `a`/`b` คือผล geocode ราย slice จาก s1_process.py (วงโคจรเดียวกันถูกตัดเป็น
2 slice เมื่อกรอบจังหวัดกิน 2 ฉากย่อยใน burst เดียว)

ใช้: `python analysis/s1_merge_scenes.py`          # สร้าง/ทับ *_full_* ทั้ง 2 วัน
     `python analysis/s1_merge_scenes.py --verify` # สร้างแล้ว assert ตรงไฟล์ที่มีอยู่ (regression)
"""
import sys
from pathlib import Path

import numpy as np

PROJ = Path(__file__).resolve().parent.parent
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"

# (ชื่อไฟล์ full, slice หลัก, slice รอง)
PAIRS = [
    ("s1d_20260915_1828_full", "s1d_20260915_1828_a", "s1d_20260915_1828_b"),
    ("s1d_20260927_1828_full", "s1d_20260927_1828", "s1d_20260927_1828_b"),
]
POLS = ("vh", "vv")


def merge(primary, secondary):
    """full = หลักที่ finite ไม่เช่นนั้นใช้รอง · valid = isfinite(full)"""
    full = np.where(np.isfinite(primary), primary, secondary)
    return full, np.isfinite(full)


def main():
    verify = "--verify" in sys.argv
    for base, prim, sec in PAIRS:
        for pol in POLS:
            p = np.load(DER / f"{prim}_{pol}_db.npy")
            s = np.load(DER / f"{sec}_{pol}_db.npy")
            full, valid = merge(p, s)
            out = DER / f"{base}_{pol}_db.npy"
            if verify and out.exists():
                old = np.load(out)
                om = np.isfinite(old)
                nm = np.isfinite(full)
                same_nan = np.array_equal(om, nm)
                maxdiff = float(np.nanmax(np.abs(np.where(om, old, np.nan) - np.where(nm, full, np.nan)))) if same_nan else float("inf")
                assert same_nan and maxdiff == 0.0, f"{out.name}: ต่างจากไฟล์เดิม (nan-match={same_nan}, maxdiff={maxdiff})"
            np.save(out, full)
            np.save(DER / f"{base}_valid.npy", valid)
            print(f"{base}_{pol}: full={int(np.isfinite(full).sum())} px · valid={int(valid.sum())} px ✓")
    if verify:
        print("verify: ทุกไฟล์ตรงของเดิม byte-level (array-equal)")


if __name__ == "__main__":
    main()
