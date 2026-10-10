"""เป้าหมาย 6 — mask ทะเลบท กทม.: ตัดนอกตลิ่งน้ำขึ้นลงออกจากมาสก์น้ำ S1 ของ bkk_lower

วิธี (pre-register): ทะเล = เซลล์ที่ **ค่า VH ต่ำถาวรทุกฉากทุกวง** (น้ำเกลือไม่มีทางแห้งในหน้าต่าง
1 ก.ค.–9 ต.ค. 69) — VH ≤ −20 dB ใน ≥90% ของฉากที่ครอบจุดนั้น = น้ำถาวร · ตัดออกจาก "น้ำใหม่" ของ stage-2
+ M13 (รีวิว 10 ต.ค.): ใช้**น้ำถาวรสถิติเท่านั้น** — ตัด DEM<1.2 ม. ออก (GLO-30 ±2–4 ม.
ไม่ใช่แนวชายฝั่ง · เดิม OR กินที่ลุ่มต่ำมีคนอยู่ทั้งแถบ → ผิดจาก docstring AND)

ผลลัพธ์: data/22_goal6_network/derived/s1_stage2/bkk_lower/mask_sea.npy +
analysis/goal6/bkk_lower/l2_sea_adjust.json + MD สรุปตัวเลขก่อน/หลัง
รัน: python analysis/goal6_bkk_sea_mask.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
STAGE2 = ROOT / "data/22_goal6_network/derived/s1_stage2"
OUT_JSON = ROOT / "analysis/goal6/bkk_lower/l2_sea_adjust.json"

bid = "bkk_lower"
g = json.loads((STAGE1 / f"grid_{bid}.json").read_text(encoding="utf-8"))
x0, y0, x1, y1, nx, ny = g["x0"], g["y0"], g["x1"], g["y1"], g["nx"], g["ny"]

# 1) สถิติน้ำถาวร: นับจำนวนฉากที่ VH ≤ −20 ต่อเซลล์
vh_files = sorted((STAGE1 / bid).glob("*_vh_db.npy"))
lowland = np.load(STAGE1 / f"mask_lowland_{bid}.npy")
wet_count = np.zeros((ny, nx), np.float32)
covered = np.zeros((ny, nx), np.float32)
for f in vh_files:
    v = np.load(f)
    c = np.isfinite(v)
    covered += c
    wet_count += ((v <= -20.0) & c).astype(np.float32)
wet_frac = np.where(covered > 0, wet_count / np.maximum(covered, 1), np.nan)
permanent_water = np.where(covered >= 3, wet_frac >= 0.9, False)  # ครอบ ≥3 ฉาก (bkk_lower มี 4 ฉาก) และเปียก ≥90%

# 2) เกณฑ์พิกัด/DEM — M13 (รีวิว Sift/Gemini): เดิม OR DEM<1.2 ม. กินที่ลุ่มต่ำที่อยู่อาศัยทั้งแถบ
# (ผิดกับ docstring ที่เขียน AND) · แก้เป็น**น้ำถาวรสถิติเท่านั้น** (ป้องกันอ่านเป็นตัวเลขต่ำเทียม)
# — DEM<1.2 ไม่ใช่แนวชายฝั่ง (GLO-30 คลาดเคลื่อน ±2–4 ม.) จึงไม่ใช้
sea_mask = permanent_water & lowland
np.save(STAGE2 / bid / "mask_sea.npy", sea_mask)

# 3) ปรับตัวเลข stage-2 ก่อน/หลัง
summary = json.loads((STAGE2 / "summary.json").read_text(encoding="utf-8"))
rows = []
for rec in summary[bid]["scenes"]:
    if rec["reference"] == rec["scene"]:
        continue
    w = np.load(STAGE2 / bid / f"{rec['scene']}_water.npy")
    before = w.sum() * 0.0009
    after = (w & ~sea_mask).sum() * 0.0009
    rows.append({"scene": rec["scene"], "before_km2": round(before, 1), "after_km2": round(after, 1),
                 "sea_removed_km2": round(before - after, 1)})
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
peak = max(rows, key=lambda r: r["after_km2"])
out = {"method": "น้ำถาวรสถิติเท่านั้น (VH≤−20 ≥90% ของฉากที่ครอบ, ครอบ ≥3 ฉาก) — ใน lowland (M13: ตัด DEM<1.2 ออก)",
       "sea_cells_km2": round(float(sea_mask.sum()) * 0.0009, 1),
       "scene_adjust": rows, "peak_after_km2": peak["after_km2"], "peak_scene": peak["scene"]}
OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

md = ["# mask ทะเล บท กทม. — ปรับตัวเลขน้ำท่วม", "",
      f"> วิธี: {out['method']} · พื้นที่ถูกตีความเป็นทะเล: **{out['sea_cells_km2']} ตร.กม.**", "",
      "| ฉาก | ก่อน (ตร.กม.) | หลังตัดทะเล | ต่าง |", "|---|---|---|---|"]
for r in sorted(rows, key=lambda x: x["scene"]):
    md.append(f"| {r['scene'][12:40]} | {r['before_km2']} | {r['after_km2']} | {r['sea_removed_km2']} |")
md += ["", f"**พีคหลังตัดทะเล: {peak['after_km2']} ตร.กม.** ({peak['scene'][12:40]})", ""]
(ROOT / "analysis/goal6/bkk_lower/l2_sea_adjust.md").write_text("\n".join(md), encoding="utf-8")
print(f"ทะเล {out['sea_cells_km2']} ตร.กม. · พีคก่อน {max(r['before_km2'] for r in rows)} → หลัง {peak['after_km2']} ตร.กม.")
