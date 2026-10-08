"""Paired same-orbit change detection for the 3 new dates + stats + frame npys.

Pairs (12-day same orbit) ใช้กฎ canonical ตรงจาก s1_change_detect.detect() — import อย่างเดียว
ไม่พิมพ์ threshold ซ้ำ (กันกฎหลุด sync ตอนคาลิเบรตใหม่ — ผลรีวิว GLM):
  27 Sep 06:00 local (26 Sep 23 UTC a+b) vs 15 Sep 06:00 (14 Sep 23 UTC a+b)  -> frame-2 verdict
  28 Sep 18:19 (S1C)  vs 16 Sep 18:19 (S1C)
  22 Sep 18:20 (a+b)  vs 10 Sep 18:20 (a+b)
"""
import json
from pathlib import Path

import numpy as np
from common import cell_km2
from s1_change_detect import detect

DER = Path(__file__).resolve().parent.parent / "data" / "13_sentinel1_copernicus" / "derived"  # อิง __file__
g = json.load(open(DER / "grid.json"))
RES = g["res"]
nx, ny = g["nx"], g["ny"]
cell = cell_km2(RES)
lowland = np.load(DER / "mask_lowland.npy")
prov = np.load(DER / "mask_province.npy")

def merged(tag_a, tag_b, pol="vh"):
    a = np.load(DER / f"{tag_a}_{pol}_db.npy")
    if tag_b:
        b = np.load(DER / f"{tag_b}_{pol}_db.npy")
        va, vb = np.isfinite(a), np.isfinite(b)
        m = np.where(va, a, b)
        both = va & vb
        # เฉลี่ยในหน่วยกำลัง (linear) — ค่าเฉลี่ยในหน่วย dB ต่ำกว่าค่าจริง (GL-25)
        lin = 10 ** (a[both].astype(np.float64) / 10) + 10 ** (b[both].astype(np.float64) / 10)
        m[both] = (10 * np.log10(lin / 2)).astype(np.float32)
        return m, va | vb
    return a, np.isfinite(a)

PAIRS = [
    ("2026-09-22 18:20", "s1d_20260922_1820_a", "s1d_20260922_1820_b", "s1d_20260910_1820_a", "s1d_20260910_1820_b"),
    ("2026-09-27 06:00", "s1d_20260927_0600_a", "s1d_20260927_0600_b", "s1d_20260915_0600_a", "s1d_20260915_0600_b"),
    ("2026-09-28 18:19", "s1c_20260928_1820", None, "s1c_20260916_1820", None),
]

results = {}
for label, pa, pb, qa, qb in PAIRS:
    vh_post, valid = merged(pa, pb, "vh")
    vh_pre, _ = merged(qa, qb, "vh")
    vv_post, _ = merged(pa, pb, "vv")
    vv_pre, _ = merged(qa, qb, "vv")
    w = detect(vh_pre, vh_post, vv_pre, vv_post, lowland)
    cov = float((valid & prov).sum() / prov.sum() * 100)
    area = float(w.sum() * cell)
    results[label] = {"area_km2": round(area, 1), "coverage_pct": round(cov, 1), "mask": w}
    np.save(DER / f"flood_{label[:10].replace('-', '')}_{label[11:16].replace(':', '')}.npy", w)
    dist = {}
    for f in sorted(DER.glob("mask_district_*.npy")):
        m = np.load(f)
        dist[f.stem.replace("mask_district_", "")] = round(float((w & m).sum() * cell), 1)
    results[label]["districts"] = dist
    print(f"{label}: {area:.1f} km2 | coverage {cov:.0f}% | {dist}")

series = {k: {"area_km2": v["area_km2"], "coverage_pct": v["coverage_pct"], "districts": v["districts"]}
          for k, v in results.items()}
# เขียนสองที่ตรงกัน (เดิมต้องคัดลอกด้วยมือ — GLM GL-25): DER สำหรับสคริปต์ในชุดเดียวกัน,
# analysis/s1_flood_series.json คือตัวที่ build_canonical_numbers.py อ่าน
for dest in (DER / "flood_series_ours.json",
             p := Path(__file__).resolve().parent / "s1_flood_series.json"):
    json.dump(series, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", dest.name)
