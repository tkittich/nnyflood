"""รวมตัวเลข canonical ของโครงการจากผลวิเคราะห์ทุกตัว -> analysis/canonical_numbers.json

ทำไมต้องมี: รายงาน HTML ทั้งสองฉบับพิมพ์ตัวเลขเป็นโพรซใน template (hardcode) —
ถ้ารันสคริปต์วิเคราะห์ใหม่แล้วผลเปลี่ยน ไม่มีอะไรบังคับให้รายงานตาม ไฟล์นี้จึงเป็น
"สัญญา" ระหว่างฝั่งวิเคราะห์กับฝั่งรายงาน:

1. สคริปต์นี้ อ่านผลจริงจาก JSON/มาสก์ ของทุกสคริปต์วิเคราะห์ -> เขียน canonical_numbers.json
2. build_report_html.py / build_expert_report.py โหลดไฟล์นี้แล้ว **ตรวจว่า HTML ที่ได้
   มีตัวเลขชุดตรวจครบ** — ขาดตัวไหน = build ล้มทันทีด้วยข้อความบอกจุดแก้
3. tests/test_artifacts.py::test_reports_contain_canonical_numbers ตรวจซ้ำกับ HTML
   ที่ commit อยู่ — กันกรณีลืม build ใหม่หลังแก้วิเคราะห์

รันเมื่อไหร่: หลังรันสคริปต์วิเคราะห์ที่เปลี่ยนผล แล้ว build รายงานใหม่ตาม
    python analysis/build_canonical_numbers.py
    python report/build_report_html.py && python report/build_expert_report.py

หมายเหตุ: ตัวเลข "ระดับน้ำ" (9.23/8.45/7.64/6.86/8.21) เป็นค่าที่บันทึกจากการวัด/
สำรวจ (โทรมาตร กช. + ภาคตัดขวาง data/19) ไม่ใช่ค่าที่คำนวณใหม่ได้จาก JSON —
เก็บเป็น recorded constants พร้อมแหล่งอ้างอิง และตรวจความสอดคล้องภายใน
(เกจ − datum = ม.รทก.) ทุกครั้งที่รัน
"""
import json
import sys
from pathlib import Path

import numpy as np

PROJ = Path(__file__).resolve().parent.parent
ANA = PROJ / "analysis"
DER = PROJ / "data" / "13_sentinel1_copernicus" / "derived"

sys.path.insert(0, str(ANA))
from rid_cross_section_hydraulics import GAUGE_OFFSET  # noqa: E402


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ---------- S1: คำนวณพื้นที่จากมาสก์จริง (แหล่งเดียวกับ s1_change_detect.py) ----------
g = jload(DER / "grid.json")
cell = g["res"] * 111.32 * g["res"] * 111.32 * np.cos(np.radians(14.2))
s1 = {
    "peak_km2": round(float(np.load(DER / "flood_peak_27sep1828.npy").sum() * cell), 1),
    "oct2_ours_km2": round(float(np.load(DER / "flood_2oct_validated.npy").sum() * cell), 1),
}
series = jload(ANA / "s1_flood_series.json")
s1["sep27_am_ours_km2"] = series["2026-09-27 06:00"]["area_km2"]
s1["sep27_am_coverage_pct"] = series["2026-09-27 06:00"]["coverage_pct"]

gis = jload(ANA / "gistda_pass_areas_nn.json")
gistda = {
    "sep24_km2": gis["rd2_20260924_1815"],
    "sep27_am_km2": gis["S1D_20260927_0601"],
    "oct2_km2": gis["S1D_20261002_0609"],
}

# ---------- สัดส่วนเขื่อน/ฝน (อินทิกราล 15 นาที) ----------
att = jload(ANA / "attribution_share.json")
w = att["windows"]
dam_share = {
    "p1_pct": w["P1_onset"]["dam_share_measured_pct"],
    "p2_pct": w["P2_sustained"]["dam_share_measured_pct"],
    "p1_total_mcm": w["P1_onset"]["total_measured_mcm"],
    "p2_total_mcm": w["P2_sustained"]["total_measured_mcm"],
    "p2_dam_mcm": w["P2_sustained"]["dam_release_mcm"],
}

# ---------- สถานการณ์จำลอง ----------
cf = jload(ANA / "goal4_counterfactual_summary.json")
counterfactual = {
    k: {"overflow_mcm": cf[k][0], "hours_above_bankfull": cf[k][1]}
    for k in ("actual", "R1", "M1", "M2", "M3")
}
counterfactual["m4_drain_mcm"] = cf["M4_volume_budget"]["drain_mcm"]
counterfactual["m4_peak_drop_m"] = cf["M4_volume_budget"]["peak_drop_m"]

# ---------- โมเดลทำนาย (แถว = [model, RMSE ทั้งช่วง, RMSE wet, RMSE เหตุการณ์, ...]) ----------
v1 = jload(ANA / "goal4_model_v1_results.json")
model_v1 = {}
for h in ("6", "24", "48"):
    row = {r[0]: r for r in v1[h]}["linear"]
    model_v1[f"rmse{h}_all_cm"] = row[1]
    model_v1[f"rmse{h}_event_cm"] = row[3]

bt = jload(ANA / "goal4_model_backtest_long.json")
backtest_beats_persistence_every_season = all(
    f["rmse24_wet"] < f["rmse24_persistence_wet"] for f in bt["folds"].values()
)

# ---------- ระดับน้ำ (recorded constants + ตรวจความสอดคล้อง datum) ----------
levels = {
    "peak_gauge_m": 9.23,        # Ny.7 พีค 27 ก.ย. 10:00 (โทรมาตร กช.)
    "datum_offset_m": GAUGE_OFFSET,  # เกจ = ม.รทก. + 1.59 (khundan_tele_findings)
    "bankfull_gauge_m": 8.45,    # เริ่มล้นเมือง (เกจ)
    "bankfull_msl_m": 8.21,      # สันตลิ่งจริง (ภาคตัดขวาง data/19)
    "floodplain_onset_msl_m": 6.86,  # ระดับเริ่มท่วมที่ราบ (ม.รทก.)
}
assert abs((levels["peak_gauge_m"] - GAUGE_OFFSET) - 7.64) < 0.005
assert abs((levels["bankfull_gauge_m"] - GAUGE_OFFSET) - 6.86) < 0.005

# ---------- ชุด string ที่รายงานแต่ละฉบับต้องมี (ตรวจด้วย exact substring ไม่ใช่ regex —
# regex ที่มีจุดไปแมตช์ base64 ขยะได้) สองฉบับเลือกนำเสนอคนละหน่วยโดยดีไซน์:
# ประชาชนใช้เกจ 9.80/9.23 + RMSE เป็นเมตร (1.09) · วิชาการใช้ ม.รทก. (7.64/8.21) + 11.89 ----------
checks = {
    "public": ["509.3", "436.3", "306.9", "62.2", "12%", "59%", "65 ชม.",
               "9.23", "8.45", "6.86", "0.75 ม.", "1.09"],
    "expert": ["509.3", "436.3", "306.9", "62.2", "12%", "59%", "65 ชม.",
               "9.23", "8.45", "7.64", "6.86", "8.21", "11.89", "108.6"],
}

out = {
    "meta": {
        "generated_by": "analysis/build_canonical_numbers.py",
        "note": "ตัวเลข canonical ของโครงการ — builders และ tests อ่านจากไฟล์นี้ ห้ามแก้มือ",
        "sources": {
            "s1": "data/13_sentinel1_copernicus/derived/flood_*.npy + analysis/s1_flood_series.json",
            "gistda": "analysis/gistda_pass_areas_nn.json",
            "dam_share": "analysis/attribution_share.json (อินทิกราล 15 นาที)",
            "counterfactual": "analysis/goal4_counterfactual_summary.json",
            "model_v1": "analysis/goal4_model_v1_results.json",
            "backtest": "analysis/goal4_model_backtest_long.json",
            "levels": "โทรมาตร กช. + ภาคตัดขวาง data/19 (recorded constants)",
        },
    },
    "values": {
        "s1": s1, "gistda": gistda, "dam_share": dam_share,
        "counterfactual": counterfactual, "model_v1": model_v1,
        "backtest_beats_persistence_every_season": backtest_beats_persistence_every_season,
        "levels": levels,
    },
    "checks": checks,
}

dest = ANA / "canonical_numbers.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"saved {dest}")
print(f"  s1 peak {s1['peak_km2']} · 2oct ours {s1['oct2_ours_km2']} · dam share "
      f"{dam_share['p1_pct']}%/{dam_share['p2_pct']}% · event 65 ชม. · RMSE24 "
      f"{model_v1['rmse24_all_cm']}/{model_v1['rmse24_event_cm']} ซม.")
