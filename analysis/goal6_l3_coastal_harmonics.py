#!/usr/bin/env python3
"""analysis/goal6_l3_coastal_harmonics.py — แบบจำลองพยากรณ์ระดับน้ำเจ้าพระยาตอนล่างผสานฮาร์มอนิกน้ำขึ้น-น้ำลงดาราศาสตร์ (Astronomical Tidal Harmonics Model)

ขยายขีดความสามารถของแบบจำลอง L3 Coastal-Coupled:
1. สกัดฮาร์มอนิกน้ำขึ้น-น้ำลงดาราศาสตร์ 4 องค์ประกอบหลัก (M2, S2, K1, O1)
2. สร้างตัวทำนายระดับน้ำทะเลล่วงหน้าดาราศาสตร์ (Astronomical Tide Predictor) ที่ไม่ต้องพึ่งพาข้อมูลตรวจวัดจริงในอนาคต
3. ประเมินทักษะการพยากรณ์ระดับน้ำสถานี C.12 กรมชลประทานสามเสน ที่ระยะ +6 ชม., +12 ชม., +24 ชม., และ +48 ชม.
4. เปรียบเทียบความแม่นยำ (RMSE, MAE, R²) กับเกณฑ์อ้างอิงเดิม (Persistence Baseline)
5. ตัดแถวฝึกที่เป้าหมายทับช่วงทดสอบ (purge รายระยะ) กันการรั่วไหลของข้อมูลอนาคต แบบเดียวกับ goal6_l3_coastal_model.py (รีวิวรอบ 5: Claude F-11 · DeepSeek F6(b) · Gemini F-12)

รัน: python analysis/goal6_l3_coastal_harmonics.py
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge

ROOT = Path(__file__).resolve().parent.parent
RAW_L1 = ROOT / "data/22_goal6_network/raw/l1_bkk_lower"
RAW_TIDES = ROOT / "data/22_goal6_network/raw/estuary_tides"
OUT_JSON = ROOT / "analysis/goal6/l3_coastal_harmonics_summary.json"
OUT_MD = ROOT / "analysis/goal6/l3_coastal_harmonics_findings.md"
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

# องค์ประกอบฮาร์มอนิกดาราศาสตร์หลัก (คาบเวลาเป็นชั่วโมง)
HARMONIC_CONSTITUENTS = {
    "M2": {"name": "ดวงจันทร์กึ่งรายวันหลัก (Principal lunar semidiurnal)", "period_h": 12.4206012},
    "S2": {"name": "ดวงอาทิตย์กึ่งรายวันหลัก (Principal solar semidiurnal)", "period_h": 12.0000000},
    "K1": {"name": "ดวงจันทร์-ดวงอาทิตย์รายวัน (Lunar diurnal)", "period_h": 23.9344721},
    "O1": {"name": "ดวงจันทร์รายวันหลัก (Principal lunar diurnal)", "period_h": 25.8193417},
}

LEADS = [6, 12, 24, 48]
TEST_START = "2026-09-20 00:00"
TEST_START_DT = dt.datetime.strptime(TEST_START, "%Y-%m-%d %H:00")


def load_hourly(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "graph_data" in data:
            items = data["graph_data"]
        elif "data" in data and isinstance(data["data"], dict) and "graph_data" in data["data"]:
            items = data["data"]["graph_data"]
        elif "data" in data and isinstance(data["data"], list):
            items = data["data"]

    out = {}
    for r in items:
        if isinstance(r, (list, tuple)) and len(r) >= 2:
            t, v = r[0], r[1]
        elif isinstance(r, dict):
            t, v = r.get("datetime"), r.get("value")
        else:
            continue
    # กฎเวลา (กำหนดก่อนรันใหม่ 25 ต.ค. 69 ตามรีวิวรอบ 7 B2): ใช้เฉพาะบันทึกที่ลงเวลา "นาทีที่ 00" ของแต่ละชั่วโมง
    # (เดิมตัด [:13]+":00" แล้วเขียนทับ ทำให้ซีรีส์ 10 นาทีของ CPY015 เหลือค่านาทีที่ 50 ซึ่งคลาดจากเวลาที่ระบุ 50 นาที)
    # ชั่วโมงที่ไม่มีบันทึกนาทีที่ 00 = ขาดค่า (ไม่เฉลี่ย ไม่ใช้ค่านาทีอื่นแทน)
        if v is not None and t and t[14:16] == "00":
            try:
                dt_str = t[:13] + ":00"
                out[dt_str] = float(v)
            except (ValueError, TypeError):
                continue
    return out


def fit_astronomical_harmonics(times: list[dt.datetime], values: list[float]):
    """สกัดฮาร์มอนิก 4 องค์ประกอบ: h(t) = S0 + sum [A_k cos(w_k t) + B_k sin(w_k t)]"""
    t0 = times[0]
    t_hours = np.array([(t - t0).total_seconds() / 3600.0 for t in times])

    X = np.ones((len(times), 1 + 2 * len(HARMONIC_CONSTITUENTS)))
    col = 1
    const_keys = list(HARMONIC_CONSTITUENTS.keys())
    for k in const_keys:
        T = HARMONIC_CONSTITUENTS[k]["period_h"]
        w = 2.0 * math.pi / T
        X[:, col] = np.cos(w * t_hours)
        X[:, col + 1] = np.sin(w * t_hours)
        col += 2

    y = np.array(values)
    model = Ridge(alpha=1e-3, fit_intercept=False)
    model.fit(X, y)

    coefs = model.coef_
    intercept = coefs[0]
    harmonic_results = {"S0": round(float(intercept), 4), "constituents": {}}

    col = 1
    for k in const_keys:
        a = float(coefs[col])
        b = float(coefs[col + 1])
        amp = math.sqrt(a * a + b * b)
        phase_rad = math.atan2(-b, a)  # A cos(wt) + B sin(wt) = Amp cos(wt - phase)
        phase_deg = (math.degrees(phase_rad)) % 360.0
        harmonic_results["constituents"][k] = {
            "name": HARMONIC_CONSTITUENTS[k]["name"],
            "period_hours": HARMONIC_CONSTITUENTS[k]["period_h"],
            "amplitude_m": round(amp, 4),
            "phase_degrees": round(phase_deg, 2),
            "a_cos": round(a, 4),
            "b_sin": round(b, 4),
        }
        col += 2

    def predict_harmonics(query_times: list[dt.datetime]) -> np.ndarray:
        qh = np.array([(t - t0).total_seconds() / 3600.0 for t in query_times])
        pred = np.full(len(query_times), intercept)
        col_idx = 1
        for k in const_keys:
            T = HARMONIC_CONSTITUENTS[k]["period_h"]
            w = 2.0 * math.pi / T
            pred += coefs[col_idx] * np.cos(w * qh) + coefs[col_idx + 1] * np.sin(w * qh)
            col_idx += 2
        return pred

    return harmonic_results, predict_harmonics


# ---------- ฮาร์มอนิกหลายปี + ตัวแก้ปมจันทร์ (R7-27 · กติกา docs/HARMONICS_REFIT_PREREG.md ตั้งก่อนดูผล) ----------
EPOCH_FIT = dt.datetime(2000, 1, 1, 0, 0)       # จุดอ้างอิงเฟส (ชั่วโมงนับจากนี้)
EPOCH_J2000_NOON = dt.datetime(2000, 1, 1, 12, 0)
MULTI = {
    "M2": 12.4206012, "S2": 12.0, "N2": 12.65834751, "K2": 11.96723606,
    "K1": 23.9344721, "O1": 25.8193417, "P1": 24.06588766, "Q1": 26.8683566,
    "Sa": 365.2422 * 24.0, "Ssa": 182.6211 * 24.0,
}
MULTI_NAMES = {
    "M2": "ดวงจันทร์กึ่งรายวันหลัก", "S2": "ดวงอาทิตย์กึ่งรายวันหลัก", "N2": "ดวงจันทร์วงรีกึ่งรายวัน", "K2": "จันทร์-อาทิตย์กึ่งรายวัน",
    "K1": "จันทร์-อาทิตย์รายวัน", "O1": "ดวงจันทร์รายวันหลัก", "P1": "ดวงอาทิตย์รายวัน", "Q1": "ดวงจันทร์วงรีรายวัน",
    "Sa": "ฤดูกาลรายปี", "Ssa": "ฤดูกาลครึ่งปี",
}


def nodal_fu(name: str, n_deg: np.ndarray):
    """ตัวคูณแอมพลิจูด f และการเลื่อนเฟส u (องศา) ตามสูตรประมาณของ Schureman — ตรงตามเอกสารกติกา §2"""
    n = np.radians(n_deg)
    c1, c2, s1, s2 = np.cos(n), np.cos(2 * n), np.sin(n), np.sin(2 * n)
    if name in ("M2", "N2"):
        return 1.0004 - 0.0373 * c1 + 0.0002 * c2, -2.14 * s1
    if name == "K1":
        return 1.006 + 0.115 * c1 - 0.0088 * c2, -8.86 * s1 + 0.68 * s2
    if name in ("O1", "Q1"):
        return 1.0089 + 0.1871 * c1 - 0.0147 * c2, 10.80 * s1 - 1.34 * s2
    if name == "K2":
        return 1.0241 + 0.2863 * c1 + 0.0083 * c2, -17.74 * s1 + 0.68 * s2
    one = np.ones_like(n_deg)
    return one, 0.0 * one


def _design(times: list):
    th = np.array([(x - EPOCH_FIT).total_seconds() / 3600.0 for x in times])
    dd = np.array([(x - EPOCH_J2000_NOON).total_seconds() / 86400.0 for x in times])
    n_deg = 125.0445 - 0.0529539 * dd
    cols = [np.ones(len(times))]
    for k, per in MULTI.items():
        f, u = nodal_fu(k, n_deg)
        arg = 2.0 * np.pi / per * th + np.radians(u)
        cols += [f * np.cos(arg), f * np.sin(arg)]
    return np.column_stack(cols)


def load_multiyear_cpy015() -> dict:
    """CPY015 หลายปี (2555–2568) ใช้เฉพาะบันทึกนาทีที่ 00 — กติกา §1"""
    out = {}
    for f in sorted(RAW_TIDES.glob("*_4_CPY015_annual.json")):
        out.update(load_hourly(f))
    return out


def fit_multiyear_harmonics(times: list, values: list):
    X = _design(times)
    y = np.array(values)
    coefs, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = {"S0": round(float(coefs[0]), 4), "constituents": {}}
    for i, k in enumerate(MULTI):
        a, b = float(coefs[1 + 2 * i]), float(coefs[2 + 2 * i])
        res["constituents"][k] = {"name": MULTI_NAMES[k], "period_hours": round(MULTI[k], 4), "amplitude_m": round(math.hypot(a, b), 4),
                                  "phase_degrees": round(math.degrees(math.atan2(-b, a)) % 360.0, 2), "a_cos": round(a, 4), "b_sin": round(b, 4)}
    res["s2_over_m2"] = round(res["constituents"]["S2"]["amplitude_m"] / res["constituents"]["M2"]["amplitude_m"], 3)

    def predict(query: list) -> np.ndarray:
        return _design(query) @ coefs
    return res, predict


def evaluate_leads(dt_objs, c12_data, bkk001_data, astro_fn, common):
    """ขั้นตอนประเมินเดิม (คุณลักษณะ/ริดจ์/ตัดแถวฝึกที่ทับช่วงทดสอบ) บนชุดตัวอย่างร่วมทุกระยะ"""
    all_tide = astro_fn(dt_objs)
    astro_dict = {d.strftime("%Y-%m-%d %H:00"): float(v) for d, v in zip(dt_objs, all_tide)}
    out = {}
    for lead in LEADS:
        X_train, y_train, X_test, y_test, y_persist, y_base = [], [], [], [], [], []
        lead_delta = dt.timedelta(hours=lead)
        n_purged = 0
        for d in dt_objs:
            if d not in common:
                continue
            target_dt = d + lead_delta
            target_str = target_dt.strftime("%Y-%m-%d %H:00")
            d_str = d.strftime("%Y-%m-%d %H:00")
            c12_curr, bkk_curr, c12_target = c12_data[d_str], bkk001_data[d_str], c12_data[target_str]
            astro_target = astro_dict.get(target_str)
            if astro_target is None:
                astro_target = float(astro_fn([target_dt])[0])
            astro_curr = astro_dict[d_str]
            feats = [c12_curr, bkk_curr, astro_target, astro_curr]
            if d < TEST_START_DT:
                if target_dt >= TEST_START_DT:
                    n_purged += 1
                    continue
                X_train.append(feats)
                y_train.append(c12_target)
            else:
                X_test.append(feats)
                y_test.append(c12_target)
                y_persist.append(c12_curr)
                y_base.append(c12_curr + (astro_target - astro_curr))
        if len(X_train) > 10 and len(X_test) > 5:
            reg = Ridge(alpha=1.0)
            reg.fit(X_train, y_train)
            y_t, y_p = np.array(y_test), np.array(reg.predict(X_test))
            rm = float(np.sqrt(np.mean((y_t - y_p) ** 2)))
            ss_tot = np.sum((y_t - np.mean(y_t)) ** 2)
            rp = float(np.sqrt(np.mean((y_t - np.array(y_persist)) ** 2)))
            rb = float(np.sqrt(np.mean((y_t - np.array(y_base)) ** 2)))
            out[f"lead_{lead}h"] = {
                "lead_hours": lead, "n_train": len(X_train), "n_purged": n_purged, "n_test": len(X_test),
                "rmse_model_m": round(rm, 3), "mae_model_m": round(float(np.mean(np.abs(y_t - y_p))), 3),
                "r2_model": round(float(1.0 - np.sum((y_t - y_p) ** 2) / ss_tot) if ss_tot > 0 else 0.0, 3),
                "rmse_persistence_m": round(rp, 3), "rmse_astro_baseline_m": round(rb, 3),
                "skill_gain_vs_persistence_pct": round((1.0 - rm / rp) * 100.0, 1), "skill_gain_vs_astro_baseline_pct": round((1.0 - rm / rb) * 100.0, 1),
            }
    return out


def tide_prediction_rmse(astro_fn, cpy015_data, test_times):
    ts = [d for d in test_times if d.strftime("%Y-%m-%d %H:00") in cpy015_data]
    obs = np.array([cpy015_data[d.strftime("%Y-%m-%d %H:00")] for d in ts])
    pred = astro_fn(ts)
    return {"n": len(ts), "rmse_m": round(float(np.sqrt(np.mean((obs - pred) ** 2))), 3), "bias_m": round(float(np.mean(pred - obs)), 3)}


def run_coastal_harmonics_analysis():
    # โหลดอนุกรมเป้าหมาย C.12 และขอบเขตท้ายน้ำ CPY015 สะพานกรุงเทพ
    c12_data = load_hourly(RAW_L1 / "2599_C.12_2026_hourly.json")
    cpy015_data = load_hourly(RAW_L1 / "4_CPY015_2026_hourly.json")
    bkk001_data = load_hourly(RAW_L1 / "11_BKK001_2026_hourly.json")

    # เทียบช่วงเวลา
    all_dts = sorted(set(c12_data.keys()) & set(cpy015_data.keys()) & set(bkk001_data.keys()))
    dt_objs = [dt.datetime.strptime(s, "%Y-%m-%d %H:00") for s in all_dts]

    # แบ่งชุดฝึกสอน (ก่อน 20 ก.ย.) และชุดทดสอบ (20 ก.ย. เป็นต้นไป)
    train_mask = [d < TEST_START_DT for d in dt_objs]
    test_mask = [not m for m in train_mask]

    train_dts = [d for d, m in zip(dt_objs, train_mask) if m]
    train_cpy015 = [cpy015_data[d.strftime("%Y-%m-%d %H:00")] for d, m in zip(dt_objs, train_mask) if m]

    test_dts = [d for d, m in zip(dt_objs, test_mask) if m]

    # ชุดตัวอย่างร่วมทุกระยะ: เวลาที่มีเป้าหมายครบ +6/+12/+24/+48 ชม. (กติกา §3)
    common = {d for d in dt_objs if all((d + dt.timedelta(hours=h)).strftime("%Y-%m-%d %H:00") in c12_data for h in LEADS)}

    # (ก) ฮาร์มอนิกเดิม 4 องค์ประกอบ จาก CPY015 ปี 2569 ก่อนช่วงทดสอบ
    harm_short, fn_short = fit_astronomical_harmonics(train_dts, train_cpy015)
    # (ข) ฮาร์มอนิกหลายปี 10 องค์ประกอบพร้อมตัวแก้ปมจันทร์ (ใช้เป็นตัวทำนายหลักในรายงาน)
    multi = {k: v for k, v in load_multiyear_cpy015().items() if dt.datetime.strptime(k, "%Y-%m-%d %H:00") < TEST_START_DT}
    multi.update({k: v for k, v in cpy015_data.items() if dt.datetime.strptime(k, "%Y-%m-%d %H:00") < TEST_START_DT})
    m_times = [dt.datetime.strptime(k, "%Y-%m-%d %H:00") for k in sorted(multi)]
    m_vals = [multi[k] for k in sorted(multi)]
    harmonics_meta, harmonics_fn = fit_multiyear_harmonics(m_times, m_vals)
    yearly = {}
    for k, v in multi.items():
        yearly.setdefault(k[:4], []).append(v)
    yearly_means = {y: {"mean_m": round(float(np.mean(v)), 3), "n_hours": len(v)} for y, v in sorted(yearly.items())}

    lead_evaluations = evaluate_leads(dt_objs, c12_data, bkk001_data, harmonics_fn, common)
    lead_short = evaluate_leads(dt_objs, c12_data, bkk001_data, fn_short, common)
    test_times = [d for d in dt_objs if d >= TEST_START_DT]
    # ตรวจตัวทำนายน้ำขึ้นน้ำลงโดยตรงบน CPY015 ช่วงทดสอบ (ไม่ผ่านแบบจำลองถดถอย)
    tp_short = tide_prediction_rmse(fn_short, cpy015_data, test_times)
    tp_multi = tide_prediction_rmse(harmonics_fn, cpy015_data, test_times)

    summary = {
        "title": "แบบจำลองพยากรณ์ระดับน้ำเจ้าพระยาตอนล่างผสานฮาร์มอนิกดาราศาสตร์ (Astronomical Harmonics Coupled)",
        "target_station": "C.12 (กรมชลประทานสามเสน กรุงเทพฯ)",
        "downstream_boundary": "CPY015 (สะพานกรุงเทพ)",
        "upstream_boundary": "BKK001 (ปทุมธานี)",
        "test_window": f"{TEST_START} เป็นต้นไป",
        "purge_note": "ตัดแถวฝึกที่เป้าหมายทับช่วงทดสอบ (purge รายระยะ) ก่อนฟิตโมเดลทุกระยะ แบบเดียวกับแบบจำลองปากอ่าว — กันข้อมูลอนาคตรั่วเข้าชุดฝึก (รีวิวรอบ 5: Claude F-11 · DeepSeek F6(b) · Gemini F-12)",
        "astronomical_harmonics_calibrated": harmonics_meta,
        "lead_skill_evaluations": lead_evaluations,
        "fit_basis": {"rule": "docs/HARMONICS_REFIT_PREREG.md (ตั้งก่อนดูผล 25 ต.ค. 69)", "model": "ฮาร์มอนิกหลายปี 10 องค์ประกอบพร้อมตัวแก้ปมจันทร์ (ข)", "n_hours_fit": len(m_vals), "fit_end": m_times[-1].strftime("%Y-%m-%d %H:00"),
                      "years": f"{m_times[0].year + 543}–{m_times[-1].year + 543}", "common_sample_all_leads": True, "yearly_means": yearly_means},
        "comparison_short_window_4_constituents": {"note": "ฮาร์มอนิกเดิม 4 องค์ประกอบจากข้อมูลปี 2569 ก่อนช่วงทดสอบ (ก) ผ่านขั้นตอนประเมินเดียวกัน",
                                                   "astronomical_harmonics_calibrated": harm_short, "lead_skill_evaluations": lead_short},
        "tide_prediction_vs_observed_test_window": {"short_window_4": tp_short, "multiyear_10": tp_multi},
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกสรุปผลแบบจำลองฮาร์มอนิกดาราศาสตร์ลง {OUT_JSON.name}")

    # สร้างรายงาน Markdown
    md_lines = [
        "# ผลการประเมินแบบจำลองพยากรณ์ชายฝั่งผสานฮาร์มอนิกดาราศาสตร์ (C.12 สามเสน)",
        "",
        f"> นำเข้าคลื่นดาราศาสตร์ 10 องค์ประกอบพร้อมตัวแก้ปมจันทร์ สกัดจากอนุกรมเวลาโทรมาตรสะพานกรุงเทพ (CPY015) หลายปี ({m_times[0].year + 543}–{m_times[-1].year + 543}) ตามกติกา docs/HARMONICS_REFIT_PREREG.md · ฟิตก่อน 20 ก.ย. 2569 เท่านั้น · เทียบกับแบบ 4 องค์ประกอบเดิมในไฟล์สรุป",
        "",
        "## 1. คุณลักษณะฮาร์มอนิกน้ำขึ้น-น้ำลงดาราศาสตร์ที่สกัดได้",
        "",
        "| รหัส | ชนิดคลื่นดาราศาสตร์ | คาบเวลา (ชม.) | แอมพลิจูด (ม.) | มุมเฟส (องศา) |",
        "|---|---|---:|---:|---:|",
    ]

    for k, v in harmonics_meta["constituents"].items():
        md_lines.append(f"| `{k}` | {v['name']} | {v['period_hours']:.2f} | {v['amplitude_m']:.4f} | {v['phase_degrees']:.1f}° |")

    md_lines.extend([
        "",
        "## 2. ทักษะการพยากรณ์ล่วงหน้ารายระยะ (Lead-time Skill Comparison)",
        "",
        "| ระยะพยากรณ์ | จำนวนตัวอย่างทดสอบ | ตัดออก (purge) | RMSE โมเดล (ม.) | MAE (ม.) | R² | RMSE ค่าเดิมคงที่ (ม.) | ทักษะดีขึ้นเทียบค่าเดิม (%) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])

    for k, le in lead_evaluations.items():
        md_lines.append(
            f"| **+{le['lead_hours']} ชั่วโมง** | {le['n_test']} | {le['n_purged']} | {le['rmse_model_m']:.3f} | {le['mae_model_m']:.3f} | {le['r2_model']:.3f} | {le['rmse_persistence_m']:.3f} | **{le['skill_gain_vs_persistence_pct']:+.1f}%** |"
        )

    _gains_sorted = sorted((v["lead_hours"], v["skill_gain_vs_persistence_pct"]) for v in lead_evaluations.values())
    _gain_txt = " · ".join(f"+{h:g} ชม. {g:+.1f}%" for h, g in _gains_sorted)
    _neg_txt = ", ".join(f"+{h:g} ชม." for h, g in _gains_sorted if g < 0) or "ไม่มี"

    md_lines.extend([
        "",
        "## 3. สรุปผลและข้อจำกัดของแบบจำลองฮาร์มอนิก",
        "1. **ไม่ต้องพึ่งพาข้อมูลน้ำทะเลหนุนในอนาคต**: การใช้ฮาร์มอนิกดาราศาสตร์ (Astronomical Harmonics) ทำให้โมเดลสามารถพยากรณ์ไปข้างหน้าได้โดยอาศัยเฉพาะข้อมูลดาราศาสตร์",
        f"2. **ประสิทธิภาพเทียบกับฐานเทียบเดิม (Persistence Baseline)**: ทักษะเทียบฐานเทียบเดิมรายระยะ — {_gain_txt} — ระยะที่ค่าติดลบ ({_neg_txt}) เกิดจากยังขาดการรวมพจน์อิทธิพลลมมรสุม/ความกดอากาศ (Surge) และความไม่แน่นอนของอัตราการปล่อยน้ำหลากต้นน้ำ",
        "3. **ทิศทางการพัฒนา**: ในระยะยาวจำเป็นต้องใช้อนุกรมเวลาระดับน้ำทะเลต่อเนื่องหลายปีเพื่อสกัดองค์ประกอบฮาร์มอนิกที่ครบถ้วน (ตามรายการ ACAD-07 — ฟิตหลายปีทำแล้วในรอบนี้ แต่ CPY015 เป็นสถานีในแม่น้ำ ค่าเฉลี่ยรายปีลอยได้ 0.2–0.7 ม.) และผสานแบบจำลอง Meteorological Surge เพื่อยกระดับความแม่นยำช่วงน้ำหลากวิกฤต",
        "4. **การป้องกันการรั่วไหลของข้อมูล (Purge)**: ตัดแถวฝึกที่เป้าหมายทับช่วงทดสอบทุกระยะก่อนฟิตโมเดล (แบบเดียวกับแบบจำลองปากอ่าว) — จำนวนแถวที่ตัดรายระยะดูได้จากคอลัมน์ 'ตัดออก (purge)' ข้างบนและช่อง `n_purged` ในไฟล์สรุปผล",
    ])

    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"✅ บันทึกรายงานการวิเคราะห์ลง {OUT_MD.name}")
    return summary


if __name__ == "__main__":
    run_coastal_harmonics_analysis()
