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
# ประกาศ canonical ที่ตีพิมพ์ — มาสก์ใหม่ต้องให้ค่าเดิม (ต่าง = หยุด ประกาศ canonical ชุดใหม่ก่อน ห้ามไหลผ่านเงียบ ๆ)
for _k, _exp in (("peak_km2", 452.1), ("oct2_ours_km2", 363.6)):
    assert abs(s1[_k] - _exp) <= 0.05, f"S1 {_k} = {s1[_k]} ≠ canonical {_exp} — มาสก์/กฎเปลี่ยน? ประกาศ canonical ใหม่ก่อน"

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

# ---------- สถานการณ์จำลอง (ลุ่มน้ำนครนายก — ขุนด่านฯ ปล่อยน้ำ/น้ำล้นตลิ่ง) ----------
# ตั้งชื่อ key ระบุโดเมนให้ชัด (รีวิวรอบ 4): คนละความหมายกับ cp2_bypass_counterfactual ของเป้าหมาย 7
cf = jload(ANA / "goal4_counterfactual_summary.json")
khundan_overflow_counterfactual = {
    k: {"overflow_mcm": cf[k]["overflow_mcm"], "hours_above_bankfull": cf[k]["hours_above_bankfull"]}
    for k in ("actual", "R1", "M1", "M2", "M3")
}
khundan_overflow_counterfactual["m4_drain_mcm"] = cf["M4_volume_budget"]["drain_mcm"]
khundan_overflow_counterfactual["m4_peak_drop_m"] = cf["M4_volume_budget"]["peak_drop_m"]

# ---------- โมเดลทำนาย (แถว = [model, RMSE ทั้งช่วง, RMSE wet, RMSE เหตุการณ์, ...]) ----------
v1 = jload(ANA / "goal4_model_v1_results.json")
model_v1 = {}
for h in ("6", "24", "48"):
    rows = {r[0]: r for r in v1[h]}
    model_v1[f"rmse{h}_all_cm"] = rows["linear"][1]
    model_v1[f"rmse{h}_event_cm"] = rows["linear"][3]
    model_v1[f"pers{h}_event_cm"] = rows["persistence"][3]
    model_v1[f"gbdt{h}_event_cm"] = rows["GBDT"][3]
model_v1["train_h"] = v1["samples"]["train_h"]
model_v1["test_h"] = v1["samples"]["test_h"]

bt = jload(ANA / "goal4_model_backtest_long.json")
backtest_beats_persistence_every_season = all(
    f["rmse24_wet"] < f["rmse24_persistence_wet"] for f in bt["folds"].values()
)

# ---------- ระดับน้ำ (recorded constants + ตรวจความสอดคล้อง datum) ----------
levels = {
    "peak_gauge_m": 9.23,        # Ny.7 น้ำสูงสุด 27 ก.ย. 10:00 (โทรมาตร กช.)
    "datum_offset_m": GAUGE_OFFSET,  # เกจ = ม.รทก. + 1.59 (khundan_tele_findings)
    "bankfull_gauge_m": 8.45,    # เริ่มล้นเมือง (เกจ)
    "bankfull_msl_m": 8.21,      # สันตลิ่งจริง (ภาคตัดขวาง data/19)
    "floodplain_onset_msl_m": 6.86,  # ระดับเริ่มท่วมที่ราบ (ม.รทก.)
    # GL-28: 8.45 เกจ ≡ 6.86 ม.รทก. = "เริ่มท่วมที่ราบย่านเมือง" — ต่างจาก bankfull_msl 8.21
    # (สันตลิ่งจริงจากภาคตัดขวาง) · ค่าคงที่ BANKFULL_MSL=6.86 ใน common.py หมายถึงตัว 6.86 ตัวนี้
    "note": "bankfull_gauge 8.45 = ระดับเริ่มท่วมที่ราบย่านเมือง (≡ 6.86 ม.รทก.) · bankfull_msl 8.21 = สันตลิ่งจริง (เกจ 9.80) — คนละความหมาย",
}
assert abs((levels["peak_gauge_m"] - GAUGE_OFFSET) - 7.64) < 0.005
assert abs((levels["bankfull_gauge_m"] - GAUGE_OFFSET) - 6.86) < 0.005

# ---------- ชุด string ที่รายงานแต่ละฉบับต้องมี (ตรวจด้วย exact substring ไม่ใช่ regex —
# regex ที่มีจุดไปแมตช์ base64 ขยะได้) สองฉบับเลือกนำเสนอคนละหน่วยโดยดีไซน์:
# ประชาชนใช้เกจ 9.80/9.23 + RMSE เป็นเมตร (1.09) · วิชาการใช้ ม.รทก. (7.64/8.21) + 11.89 ----------
# ---------- อ่างเก็บน้ำขนาดกลาง 6 แห่ง นครนายก (SWOC RID) ----------
med_dams = jload(ANA / "goal2_nny_medium_dams_summary.json")

# ---------- เขื่อนขุนด่านฯ สถิติ 22 ปีเต็ม 2548–2569 ----------
kd22 = jload(ANA / "goal2_khundan_22y_summary.json")

# ---------- แบบจำลองชลศาสตร์ 1 มิติ (1D Hydrodynamic Routing) ----------
r1d_file = ANA / "hydraulic_1d_routing_summary.json"
r1d = jload(r1d_file) if r1d_file.exists() else {}

# ---------- ภาคตัดขวางสำรวจจริง Ny.1B (RID SWOC Hydro App) ----------
# รีวิวรอบ 4 (Tier-2): ตัวเลขหลัก = ผลสมการ Manning บนภาคตัดขวางสำรวจ 61 จุด (ค่ากลางวิธีรวมหน้าตัด 666.3)
# + ช่วงความไม่แน่นอน 488.9–893.0 (ปลายล่าง = ความลาดชันเรียบของช่วงท้ายน้ำ · ปลายบน = วิธีแบ่งช่อง)
# ยึดระดับ/อัตราไหลสูงสุดกับโทรมาตรจริง (11.00 ม.รทก. / 675.3 ม³/วิ)
# ค่าเก่าตามเส้นระดับ–ปริมาณน้ำเดิม (244.6 · 11.23 · 282.4) ปลดประจำการจากรายงาน — เก็บ note ไว้ในแฟ้มนี้เท่านั้น
ny1b_xs = {
    "survey_points": 61,
    "bed_elevation_msl": 4.10,
    "bank_elevation_msl": r1d["ny1b_hydraulics"]["bankfull_crest_msl_m"],
    "bankfull_q_m3s": r1d["ny1b_hydraulics"]["bankfull_capacity_q_cms"],
    "bankfull_q_low_m3s": r1d["rating_sensitivity"]["ny1b_flat_slope"]["bankfull_crest_10.60"]["q_composite_cms"],
    "bankfull_q_high_m3s": r1d["rating_sensitivity"]["ny1b"]["bankfull_crest_10.60"]["q_divided_cms"],
    "legacy_rating_note": "ค่าเก่า 244.6 ม³/วิ มาจากตารางเส้นระดับ–ปริมาณน้ำ (rating) ประวัติศาสตร์ของกรมชลฯ ไม่ใช่ผลสมการ Manning — เลิกใช้ในรายงานแล้ว (รีวิวรอบ 4)",
    "peak_stage_msl": r1d["ny1b_hydraulics"]["peak_stage_msl_m"],
    "peak_q_m3s": r1d["ny1b_hydraulics"]["peak_q_cms"],
    "overflow_depth_m": r1d["ny1b_hydraulics"]["peak_above_bankfull_m"],
    "overflow_q_m3s": round(r1d["ny1b_hydraulics"]["peak_q_cms"] - r1d["ny1b_hydraulics"]["bankfull_capacity_q_cms"], 1),
}

checks = {
    "public": ["452.1", "363.6", "306.9", "51.5", "12%", "60%", "65 ชม.",
               "9.23", "9.80", "8.45", "6.86", "0.78 ม.", "1.18",
               "1,058–1,416", "242", "26.96", "666.3", "675.3", "488.9", "893.0",
               "10.60", "0.40", "7,811", "38.0"],
    "expert": ["452.1", "363.6", "306.9", "51.5", "12%", "60%", "65 ชม.",
               "9.23", "8.45", "7.64", "6.86", "8.21", "11.89", "117.6",
               "1,058–1,416", "242(h−4.55)", "4.55", "26.96", "666.3", "675.3", "488.9", "893.0",
               "10.60", "0.40", "7,811", "38.0", "4 พฤศจิกายน", "27 กันยายน",
               "617.4", "3.25"],
}

# ค่า/คำที่เลิกใช้ — ห้ามปรากฏใน HTML ที่ build (builders/tests ตรวจ absence — GL-10)
FORBIDDEN = ["เกินเส้นควบคุม 36 วัน", "ต่อเนื่องก่อนพายุ", "เหนือเส้นควบคุมมา 36 วัน", "ไม่ตามเส้นควบคุม", "พิสูจน์ว่า \"ตัวกั้น\"", "ไม่มีหน่วยงานใดเคยเผยแพร่", "1,050", "1,420", "11.95", "44 ซม", "57%", "564.4", "14 passed", "12 ตัวแปร",
             "น้ำสูงสุดสูงสุด", "น้ำสูงสุดสุด", "ทำนายทำนาย", "น้ำน้ำ", "ผู้ว้าฯ",
             "509.3", "436.3", "62.2", "450.5", "364.5", "50.0", "202.3", "104.4", "75.8", "68.1",
             "176.0", "50.5", "≈380–450", "0.732", "0.676", "0.798",
             "13,608", "26.6 ซม", "108.6", "159.5", "120.3", "153.5", "153.8",
             # รีวิวรอบ 4 (Tier-2): ค่า Ny.1B รุ่นเก่าตามเส้น rating เดิม · ค่ามัธยฐานขุนด่านแบบรวมปีเหตุการณ์ · จำนวนวันนับเก่า
             "244.6", "11.23", "282.4", "36.5 วัน", "7,961", "7,945"]

# ค่าที่เลิกใช้แล้ว "ในบริบทหนึ่ง" แต่ยังปรากฏอย่างถูกต้องในอีกบริบท (คนละปริมาณ/คนละโดเมน)
# เหตุผล: FORBIDDEN เป็นรายการแบนราบ การจับแบบ substring ล้วนทำให้ค่าที่บังเอิญซ้ำกับ
#   ตัวเลขของงานอื่นโดนจับผิด (เช่น 11.95% EIRR ของ Goal 7 ไม่ใช่ 11.95 ที่ถอนในงานนครนายก)
# กติกา: ทุกข้อยกเว้นต้องมีเหตุผลเป็นข้อความ (test บังคับ) และต้องเป็น token ที่อยู่ใน
#   FORBIDDEN จริง — ไม่ใช่ช่องทางเลี่ยงการแบนค่าใหม่
FORBIDDEN_EXCEPTIONS = {
    "คลองเจ้าพระยา2_ประชาชน.html": {
        "50.0": "สัดส่วนพื้นที่น้ำท่วมร้อยละ 50.0 ของ อ.องครักษ์ ที่ระดับมัธยฐาน +3.20 ม.รทก. (เป้าหมาย 7) — คนละปริมาณกับ 50.0 ที่ถูกถอนในงานลุ่มน้ำนครนายก",
    },
    "คลองเจ้าพระยา2_วิชาการ.html": {
        "11.95": "EIRR 11.95% ของโครงการคลองเจ้าพระยา 2 (โดเมนเศรษฐศาสตร์) — คนละปริมาณกับ 11.95 ที่ถูกถอนในงานลุ่มน้ำนครนายก",
        "50.0": "สัดส่วนพื้นที่น้ำท่วมร้อยละ 50.0 ของ อ.องครักษ์ ที่ระดับมัธยฐาน +3.20 ม.รทก. (เป้าหมาย 7) — คนละปริมาณกับ 50.0 ที่ถูกถอนในงานลุ่มน้ำนครนายก",
    },
    "ชุดเทียบมาตรฐาน2554.html": {
        "57%": "เปอร์เซ็นต์ตามเส้นกฎเกณฑ์เขื่อนในตารางเทียบ 2554 — คนละปริมาณกับ 57% ที่ถูกถอน (สัดส่วนพื้นที่/ความครอบคลุม)",
    },
}

# ---------- GL-11: ค่าแสดงผลสำหรับ builders (token @@R:ชื่อ@@ — คำนวณจากข้อมูลจริง ไม่ใช่พิมพ์มือ) ----------
peak_m = np.load(DER / "flood_peak_27sep1828.npy")
oct2_m = np.load(DER / "flood_2oct_validated.npy")
dpk, do2 = {}, {}
for f in sorted(DER.glob("mask_district_*.npy")):
    m = np.load(f)
    nm = f.stem.replace("mask_district_", "")
    dpk[nm] = round(float((peak_m & m).sum() * cell), 1)
    do2[nm] = round(float((oct2_m & m).sum() * cell), 1)
K = {"อำเภอองครักษ์": "ong", "อำเภอเมืองนครนายก": "mueang", "อำเภอบ้านนา": "bn", "อำเภอปากพลี": "pk"}
# รีวิว Sonnet 12 ต.ค. 69: เทียบฝนแบบเดียวกับแหล่งเดียวกัน — อันดับ ERA5 ของปี 2569 (ไม่เทียบสถานีกับกริด)
import csv as _csv
_era = [(int(r["year"]), float(r["dam_upper_basin"])) for r in
        _csv.DictReader(open(ANA / "era5_rain_18day_max_by_year.csv", encoding="utf-8-sig"))
        if r["dam_upper_basin"]]
_era_sorted = sorted((v for _, v in _era), reverse=True)
_era26 = next(v for y, v in _era if y == 2026)
_era_rank = _era_sorted.index(_era26) + 1
# ตรวจกฎตัดน้ำ (รีวิว Sonnet M1/R9) — อ่านจาก analysis/goal6/s1_rule_validation.json (ผลิตโดย goal6_s1_rule_validation.py)
_rv = json.loads((ANA / "goal6" / "s1_rule_validation.json").read_text(encoding="utf-8"))["nakhonnayok"]
_pk_rows = [r for r in _rv["sensitivity"] if r["scene"] == "peak_27sep" and r["drop_vh"] == 0.5 and r["drop_vv"] == 1.5]
# ตัวช่วยรูปแบบวันที่ไทยสำหรับ token (SB F-22 · SB F-23)
TH_MONTHS = {1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน", 5: "พฤษภาคม", 6: "มิถุนายน",
             7: "กรกฎาคม", 8: "สิงหาคม", 9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"}


def _th_date(iso: str) -> str:
    """'2026-11-04' -> '4 พฤศจิกายน'"""
    _y, _m, _d = iso.split("-")
    return f"{int(_d)} {TH_MONTHS[int(_m)]}"


_kd_full_years = [str(r["year_be"]) for r in kd22["annual_records"] if r["is_full_100pct"]]

render = {
    "s1_pk_lo": f"{min(r['area_km2'] for r in _pk_rows):.0f}", "s1_pk_hi": f"{max(r['area_km2'] for r in _pk_rows):.0f}",
    "s1_pk_f1": f"{_rv['peak_27sep']['f1']:.2f}",
    "s1_pk_f1ci": f"{_rv['peak_27sep']['f1_ci95'][0]:.2f}–{_rv['peak_27sep']['f1_ci95'][1]:.2f}",
    "s1_pk_dark": f"{_rv['peak_27sep']['share_new_water_already_dark_in_reference']:.0%}",
    "era5_18d_mm": f"{_era26:.0f}", "era5_rank": f"{_era_rank} จาก {len(_era)}",
    "peak": f"{s1['peak_km2']}", "oct2": f"{s1['oct2_ours_km2']}",
    "am27": f"{s1['sep27_am_ours_km2']}",
    **{f"d_{v}": f"{dpk[k]}" for k, v in K.items()},
    **{f"d2_{v}": f"{do2[k]}" for k, v in K.items()},
    "rmse6": f"{model_v1['rmse6_event_cm']:.1f}",
    "rmse24": f"{model_v1['rmse24_event_cm']:.1f}",
    "rmse48": f"{model_v1['rmse48_event_cm']:.1f}",
    "pers24": f"{model_v1['pers24_event_cm']:.1f}",
    "gbdt48": f"{model_v1['gbdt48_event_cm']:.1f}",
    "all24m": f"{model_v1['rmse24_all_cm'] / 100:.2f} ม.",
    "ev24m": f"{model_v1['rmse24_event_cm'] / 100:.2f} ม.",
    "trainh": f"{model_v1['train_h']:,}",
    "pisai": f"≈{round(s1['peak_km2'] * 306.9 / s1['oct2_ours_km2'])}–{pk_short if False else round(s1['peak_km2'])}",
    "med_cap": f"{med_dams['system_totals']['total_medium_capacity_mcm']}",
    "med_pct": f"{med_dams['system_totals']['medium_to_khundan_pct']:.1f}%",
    "med_inflow": f"{med_dams['event_26_29_sep']['total_inflow_mcm']:.2f}",
    "med_outflow": f"{med_dams['event_26_29_sep']['total_outflow_mcm']:.2f}",
    "med_retain": f"{med_dams['event_26_29_sep']['net_retention_mcm']:.2f}",
    "kd22_full_yr": f"{kd22['headline_metrics']['full_capacity_years']} จาก {kd22['metadata']['period_years']} ปี",
    "kd22_full_pct": f"{kd22['headline_metrics']['full_capacity_pct']:.1f}%",
    "kd22_days_early": f"{kd22['headline_metrics']['year_2026_anomaly']['days_earlier_than_median']}",
    "kd22_days": f"{kd22['metadata']['total_days_analyzed']:,}",
    "kd22_med_date": _th_date(kd22["headline_metrics"]["year_2026_anomaly"]["median_peak_date_excl_2026"]),
    "kd22_pk_date": _th_date(kd22["headline_metrics"]["year_2026_anomaly"]["peak_date"]),
    "kd22_full99": f"{kd22['headline_metrics']['full_capacity_thresholds']['pct_99']}",
    "kd22_full98": f"{kd22['headline_metrics']['full_capacity_thresholds']['pct_98']}",
    "kd22_full_years_list": ", ".join(_kd_full_years[:-1]) + f" และ {_kd_full_years[-1]}",
    "ny1b_pts": f"{ny1b_xs['survey_points']}",
    "ny1b_bank_msl": f"{ny1b_xs['bank_elevation_msl']:.2f}",
    "ny1b_q_bankfull": f"{ny1b_xs['bankfull_q_m3s']:.1f}",
    "ny1b_q_low": f"{ny1b_xs['bankfull_q_low_m3s']:.1f}",
    "ny1b_q_high": f"{ny1b_xs['bankfull_q_high_m3s']:.1f}",
    "ny1b_pk_msl": f"{ny1b_xs['peak_stage_msl']:.2f}",
    "ny1b_pk_q": f"{ny1b_xs['peak_q_m3s']:.1f}",
    "ny1b_ov_m": f"{ny1b_xs['overflow_depth_m']:.2f}",
    # F-18: ค่าที่รายงาน 1–2 เคยพิมพ์เป็น literal ใน builder — ผูกกับ canonical แทน
    # (AGENTS.md หลัก 2: builder ห้ามพิมพ์ตัวเลข metric เป็น literal)
    "ny7_peak_g": f"{levels['peak_gauge_m']:.2f}",
    "ny7_peak_msl": f"{levels['peak_gauge_m'] - levels['datum_offset_m']:.2f}",
    "gistda_oct2": f"{gistda['oct2_km2']:.1f}",
    "cf_ov_mcm": f"{khundan_overflow_counterfactual['actual']['overflow_mcm']:.2f}",
    "cf_ov_h": f"{khundan_overflow_counterfactual['actual']['hours_above_bankfull']}",
    "r1d_ny7_q": f"{r1d['ny7_hydraulics']['bankfull_capacity_q_cms']:.1f}",
    "r1d_travel_h": f"{r1d['routing_performance']['travel_time_hours_sim']:.2f}",
}

out = {
    "forbidden": FORBIDDEN,
    "forbidden_exceptions": FORBIDDEN_EXCEPTIONS,
    "render": render,
    "meta": {
        "generated_by": "analysis/build_canonical_numbers.py",
        "note": "ตัวเลข canonical ของโครงการ — builders และ tests อ่านจากไฟล์นี้ ห้ามแก้มือ",
        "sources": {
            "s1": "data/13_sentinel1_copernicus/derived/flood_*.npy + analysis/s1_flood_series.json (กฎคาลิเบรตใหม่ 8 ต.ค. 69: 0.5/1.5/−20 · F1=0.732)",
            "gistda": "analysis/gistda_pass_areas_nn.json",
            "dam_share": "analysis/attribution_share.json (อินทิกราล 15 นาที)",
            "khundan_overflow_counterfactual": "analysis/goal4_counterfactual_summary.json (สถานการณ์น้ำล้นตลิ่งลุ่มนครนายก — คนละโดเมนกับ cp2_bypass_counterfactual ของเป้าหมาย 7)",
            "model_v1": "analysis/goal4_model_v1_results.json",
            "backtest": "analysis/goal4_model_backtest_long.json",
            "levels": "โทรมาตร กช. + ภาคตัดขวาง data/19 (recorded constants)",
            "medium_dams": "analysis/goal2_nny_medium_dams_summary.json (SWOC RID 6 อ่างขนาดกลางนครนายก)",
            "khundan_22y": "analysis/goal2_khundan_22y_summary.json (SWOC RID สถิติ 22 ปี 2548–2569)",
            "ny1b_cross_section": "data/23_rid_swoc/raw/rid_telemetry_cross_sections.json (สำรวจจริง 61 จุด) + analysis/hydraulic_1d_routing_summary.json (ค่าหลัก 666.3 · ช่วง 488.9–893.0 · พีคโทรมาตร 11.00/675.3)",
            "hydraulic_1d_routing": "analysis/hydraulic_1d_routing_summary.json (Saint-Venant kinematic/diffusive wave Ny.1B -> Ny.7)",
        },
    },
    "values": {
        "s1": s1, "gistda": gistda, "dam_share": dam_share,
        "khundan_overflow_counterfactual": khundan_overflow_counterfactual, "model_v1": model_v1,
        "backtest_beats_persistence_every_season": backtest_beats_persistence_every_season,
        "levels": levels,
        "medium_dams": med_dams,
        "khundan_22y": kd22,
        "ny1b_cross_section": ny1b_xs,
        "routing_1d": r1d,
    },
    "checks": checks,
}

dest = ANA / "canonical_numbers.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"saved {dest}")
print(f"  s1 peak {s1['peak_km2']} · 2oct ours {s1['oct2_ours_km2']} · dam share "
      f"{dam_share['p1_pct']}%/{dam_share['p2_pct']}% · event 65 ชม. · RMSE24 "
      f"{model_v1['rmse24_all_cm']}/{model_v1['rmse24_event_cm']} ซม.")
