"""C.2 attribution — ผลิตตัวเลขทั้งชุด "เขื่อนผิดหรือฝนผิด" ลง JSON (แทน literal ใน builder)

แก้ตามรีวิว Sift H3/H4/H5 + Gemini F1:
- H3: corr(−0.92)/corr_lag2(0.44) ที่เคยเป็น string ใน builder → คำนวณจริงที่นี่
- H4: ตาราง chain (ปล่อยรวม/P.17/N.67/C.2) → คำนวณจริงจาก c2_sources_volumes.json
- H5/F1: สถานการณ์ปล่อยล่วงหน้าแก้ผิดหน่วย — เดิมลบ "ปริมาตร 4 วัน" ออกจาก "อัตราไหลพีค"
  (ผิดหน่วย: 300 ลลบ.ม. ลบจาก 225 ลลบ.ม./วัน → Q=0 แม่น้ำแห้ง) แก้เป็นลบอัตราเท่านั้น:
  q_new = q_peak − (extra − actual) ต่อวัน · และติดป้ายว่ากรณีไหนอยู่ใน/นอกช่วงคาลิเบรต
- ข้อจำกัด L18 รีวิว Sift: corr เป็นสถิติกำกวม (เขื่อนปล่อยน้อยช่วงพีคเพราะถือน้ำไว้) —
  นับเป็น "หลักฐานสนับสนุน" ไม่ใช่หลักฐานหลัก (หลัก = ปริมาตร 3%)

ผลลัพธ์: analysis/goal6/c2_attribution.json
ทำซ้ำได้ · รัน: python analysis/goal6_c2_attribution.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/22_goal6_network/raw/spike_ping_cp"
OUT = ROOT / "analysis/goal6/c2_attribution.json"


def main() -> None:
    vol = json.loads((SRC / "c2_discharge_daily_sep2026.json").read_text(encoding="utf-8"))
    rel_src = json.loads((SRC / "c2_vs_dam_releases_sep2026.json").read_text(encoding="utf-8"))
    chain = json.loads((SRC / "c2_sources_volumes.json").read_text(encoding="utf-8"))

    dates = sorted(vol["C2_daily_volume_max_mcm"])
    c2v = np.array([vol["C2_daily_volume_max_mcm"][d] for d in dates])
    rel = np.array([(rel_src["bhumibol_released"].get(d) or 0) + (rel_src["sirikit_released"].get(d) or 0) for d in dates])
    inflow = np.array([(rel_src["bhumibol_inflow"].get(d) or 0) + (rel_src["sirikit_inflow"].get(d) or 0) for d in dates])

    # ---- H3: correlations (จากข้อมูลจริง) ----
    lag = 2
    corr_rel = float(np.corrcoef(rel, c2v)[0, 1])
    corr_inflow_lag = float(np.corrcoef(inflow[:-lag], c2v[lag:])[0, 1])

    # ---- สมการระดับ↔ปริมาตร (เหมือนเดิม — ใช้ภายในช่วงคาลิเบรตเท่านั้น) ----
    lv_d = chain  # ระดับ C.2 รายวันจาก c2_sources_4stations (lv จาก daily) — ใช้แฟ้ม 4 จุดแทนเพื่อกันเรียก API
    st4 = json.loads((SRC / "c2_sources_4stations_sep2026.json").read_text(encoding="utf-8"))
    daily = st4["stations"]["C2_kaesai"]["daily"]
    lv = np.array([max(x["lv"] for x in [daily[d]]) for d in dates])

    A = np.vstack([np.ones_like(c2v), c2v]).T
    coef, *_ = np.linalg.lstsq(A, lv, rcond=None)
    pred = A @ coef
    r2 = 1 - ((lv - pred) ** 2).sum() / ((lv - lv.mean()) ** 2).sum()

    # ---- H4: ตาราง chain จากข้อมูลจริง ----
    def ends(key: str) -> dict:
        v = np.array(chain[key])
        i_peak = int(np.argmax(v))
        return {"early_sep_avg": round(float(v[:10].mean()), 1),
                "peak": round(float(v[i_peak]), 1), "peak_date": chain["dates"][i_peak],
                "ratio_peak_vs_early": round(float(v[i_peak] / v[:10].mean()), 1)}

    out = {
        "note": "แก้ตามรีวิว Sift H3/H4/H5 + Gemini F1 — ตัวเลขทุกตัวคำนวณจากข้อมูลจริงใน repo",
        "correlations": {
            "release_vs_c2": round(corr_rel, 3),
            "inflow_lag2_vs_c2": round(corr_inflow_lag, 3),
            "caveat": "corr เป็นสถิติสนับสนุน (เขื่อนปล่อยน้อยช่วงพีคเพราะถือน้ำไว้ — กำกวมเชิงสาเหตุ) "
                      "หลัก = สัดส่วนปริมาตรที่พีค",
        },
        "level_volume_equation": {"a": round(float(coef[0]), 3), "b": round(float(coef[1]), 6),
                                  "r2": round(float(r2), 3),
                                  "calib_range_mcm_day": [round(float(c2v.min()), 1), round(float(c2v.max()), 1)]},
        "chain": {
            "released_total": ends("released_total"),
            "p17_ping_lower": ends("p17"),
            "n67_nan_lower": ends("n67"),
            "c2_total": ends("c2"),
            "release_share_at_peak_pct": round(float(chain["released_total"][chain["dates"].index("2026-10-01")] /
                                                      chain["c2"][chain["dates"].index("2026-10-01")] * 100), 1),
        },
        # ---- H5/F1: สถานการณ์แก้หน่วยแล้ว ----
        "prerelease_scenarios": [],
        "prerelease_note": "แก้ผิดหน่วย (เดิมลบปริมาตร 4 วันออกจากอัตราพีค → Q=0 แม่น้ำแห้ง): "
                           "ตอนนี้ลดอัตราไหลพีคลงเท่ากับส่วนปล่อยส่วนเกินต่อวัน (extra − actual) · "
                           "เฉพาะกรณีที่ Q ใหม่ยังอยู่ในช่วงคาลิเบรตจึงอ่านได้ · "
                           "กรณี Q ต่ำกว่าช่วง = ประมาณเกินขอบ (extrapolation) — ป้ายชัดทุกแถว",
    }
    peak_idx = dates.index("2026-10-01")
    # H1 (รีวิว Sonnet 12 ต.ค.): ปล่อยล่วงหน้าช่วยพีคได้ทางเดียว = เขื่อนปล่อยน้อยลง "ที่เวลาพีค"
    # → เพดานการลดพีคของ C.2 = ปล่อยจริงของ 2 เขื่อน ณ วันพีค (เทียบ 3% ของน้ำผ่าน) ไม่ใช่ส่วนเกินที่ปล่อยก่อนหน้า
    release_at_peak = float(rel[peak_idx])
    max_drop_m = float(coef[1]) * release_at_peak
    out["peak_release_ceiling"] = {
        "release_at_peak_mcm_day": round(release_at_peak, 2),
        "max_drop_m_if_zero_release": round(max_drop_m, 2),
        "note": "เพดานทางทฤษฎี: ถ้าเขื่อนทั้งสองไม่ปล่อยเลยวันพีค (1 ต.ค.) ระดับ C.2 ลดได้อย่างมาก = ความชันสมการ × ปล่อยวันพีค "
                "· สถานการณ์ปล่อยล่วงหน้าที่มี (ลบส่วนเกินออกจากอัตราไหลพีค) ถูกถอน เพราะเกินเพดานนี้ 3.5–9 เท่า "
                "(ปล่อยล่วงหน้าเลื่อนเวลาน้ำ ไม่ได้หักออกจากอัตราไหลวันพีค)",
    }
    out["prerelease_scenarios"] = []
    out["prerelease_note"] = ("ถอนสถานการณ์ 40/60/80/100 (ลบส่วนเกินจากอัตราพีค) — ขัดกับสัดส่วน 3% ของข้อมูลเอง · "
                              "ใช้เพดาน peak_release_ceiling แทน (รายงานรีวิว Sonnet H1)")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"corr: {corr_rel:.3f}/{corr_inflow_lag:.3f} · สมการ {coef[0]:.2f}+{coef[1]:.5f}·Q R²={r2:.3f} "
          f"ช่วงคาลิเบรต {c2v.min():.1f}–{c2v.max():.1f}")
    print(f"เพดานลดพีค: ปล่อยวันพีค {release_at_peak:.2f} → ≤ {max_drop_m:.2f} ม.")
    print(f"เขียนแล้ว: {OUT}")


if __name__ == "__main__":
    main()
