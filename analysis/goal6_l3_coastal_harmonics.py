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

    # 1. สอบเทียบฮาร์มอนิกดาราศาสตร์บน CPY015 (สะพานกรุงเทพ)
    harmonics_meta, harmonics_fn = fit_astronomical_harmonics(train_dts, train_cpy015)

    # คำนวณค่าระดับน้ำดาราศาสตร์ทำนายล่วงหน้า
    all_tide_astro = harmonics_fn(dt_objs)
    astro_dict = {d.strftime("%Y-%m-%d %H:00"): float(val) for d, val in zip(dt_objs, all_tide_astro)}

    # 2. ทดสอบแบบจำลองพยากรณ์ที่ระยะต่าง ๆ (LEADS)
    lead_evaluations = {}

    for lead in LEADS:
        # เตรียมชุดข้อมูล (tide_astro_lead, bkk001, c12_current) -> c12(t + lead)
        X_train, y_train = [], []
        X_test, y_test = [], []
        y_test_persistence = []
        y_test_astro_baseline = []

        lead_delta = dt.timedelta(hours=lead)
        n_purged = 0

        for d in dt_objs:
            target_dt = d + lead_delta
            target_str = target_dt.strftime("%Y-%m-%d %H:00")
            d_str = d.strftime("%Y-%m-%d %H:00")

            if target_str not in c12_data:
                continue

            c12_curr = c12_data[d_str]
            bkk_curr = bkk001_data[d_str]
            c12_target = c12_data[target_str]

            # ค่าดาราศาสตร์ล่วงหน้าที่ระยะ lead
            astro_target = astro_dict.get(target_str, harmonics_fn([target_dt])[0])
            astro_curr = astro_dict[d_str]

            features = [c12_curr, bkk_curr, astro_target, astro_curr]

            if d < TEST_START_DT:
                if target_dt >= TEST_START_DT:
                    # purge: เป้าหมายทับช่วงทดสอบ — ห้ามใช้ฝึก (แบบเดียวกับ goal6_l3_coastal_model.py)
                    n_purged += 1
                    continue
                X_train.append(features)
                y_train.append(c12_target)
            else:
                X_test.append(features)
                y_test.append(c12_target)
                y_test_persistence.append(c12_curr)
                # ฐานเทียบดาราศาสตร์: h0 + (astro(t+lead) - astro(t))
                y_test_astro_baseline.append(c12_curr + (astro_target - astro_curr))

        # ฟิตโมเดล
        if len(X_train) > 10 and len(X_test) > 5:
            reg = Ridge(alpha=1.0)
            reg.fit(X_train, y_train)
            y_pred = reg.predict(X_test)

            y_t = np.array(y_test)
            y_p = np.array(y_pred)
            y_persist = np.array(y_test_persistence)
            y_astro_base = np.array(y_test_astro_baseline)

            rmse_model = float(np.sqrt(np.mean((y_t - y_p) ** 2)))
            mae_model = float(np.mean(np.abs(y_t - y_p)))
            ss_tot = np.sum((y_t - np.mean(y_t)) ** 2)
            r2_model = float(1.0 - np.sum((y_t - y_p) ** 2) / ss_tot) if ss_tot > 0 else 0.0

            rmse_persist = float(np.sqrt(np.mean((y_t - y_persist) ** 2)))
            rmse_astro_base = float(np.sqrt(np.mean((y_t - y_astro_base) ** 2)))

            skill_vs_persistence_pct = round((1.0 - rmse_model / rmse_persist) * 100.0, 1)
            skill_vs_astro_base_pct = round((1.0 - rmse_model / rmse_astro_base) * 100.0, 1)

            lead_evaluations[f"lead_{lead}h"] = {
                "lead_hours": lead,
                "n_train": len(X_train),
                "n_purged": n_purged,
                "n_test": len(X_test),
                "rmse_model_m": round(rmse_model, 3),
                "mae_model_m": round(mae_model, 3),
                "r2_model": round(r2_model, 3),
                "rmse_persistence_m": round(rmse_persist, 3),
                "rmse_astro_baseline_m": round(rmse_astro_base, 3),
                "skill_gain_vs_persistence_pct": skill_vs_persistence_pct,
                "skill_gain_vs_astro_baseline_pct": skill_vs_astro_base_pct,
            }

    summary = {
        "title": "แบบจำลองพยากรณ์ระดับน้ำเจ้าพระยาตอนล่างผสานฮาร์มอนิกดาราศาสตร์ (Astronomical Harmonics Coupled)",
        "target_station": "C.12 (กรมชลประทานสามเสน กรุงเทพฯ)",
        "downstream_boundary": "CPY015 (สะพานกรุงเทพ)",
        "upstream_boundary": "BKK001 (ปทุมธานี)",
        "test_window": f"{TEST_START} เป็นต้นไป",
        "purge_note": "ตัดแถวฝึกที่เป้าหมายทับช่วงทดสอบ (purge รายระยะ) ก่อนฟิตโมเดลทุกระยะ แบบเดียวกับแบบจำลองปากอ่าว — กันข้อมูลอนาคตรั่วเข้าชุดฝึก (รีวิวรอบ 5: Claude F-11 · DeepSeek F6(b) · Gemini F-12)",
        "astronomical_harmonics_calibrated": harmonics_meta,
        "lead_skill_evaluations": lead_evaluations,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกสรุปผลแบบจำลองฮาร์มอนิกดาราศาสตร์ลง {OUT_JSON.name}")

    # สร้างรายงาน Markdown
    md_lines = [
        "# ผลการประเมินแบบจำลองพยากรณ์ชายฝั่งผสานฮาร์มอนิกดาราศาสตร์ (C.12 สามเสน)",
        "",
        "> นำเข้าคลื่นดาราศาสตร์ 4 องค์ประกอบหลัก (M2, S2, K1, O1) สกัดจากอนุกรมเวลาโทรมาตรสะพานกรุงเทพ (CPY015)",
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
        "3. **ทิศทางการพัฒนา**: ในระยะยาวจำเป็นต้องใช้อนุกรมเวลาระดับน้ำทะเลต่อเนื่องหลายปีเพื่อสกัดองค์ประกอบฮาร์มอนิกที่ครบถ้วน (ตามรายการ ACAD-07) และผสานแบบจำลอง Meteorological Surge เพื่อยกระดับความแม่นยำช่วงน้ำหลากวิกฤต",
        "4. **การป้องกันการรั่วไหลของข้อมูล (Purge)**: ตัดแถวฝึกที่เป้าหมายทับช่วงทดสอบทุกระยะก่อนฟิตโมเดล (แบบเดียวกับแบบจำลองปากอ่าว) — จำนวนแถวที่ตัดรายระยะดูได้จากคอลัมน์ 'ตัดออก (purge)' ข้างบนและช่อง `n_purged` ในไฟล์สรุปผล",
    ])

    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"✅ บันทึกรายงานการวิเคราะห์ลง {OUT_MD.name}")
    return summary


if __name__ == "__main__":
    run_coastal_harmonics_analysis()
