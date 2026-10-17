"""เป้าหมาย 6 — L3 Coastal-Coupled Model: แบบจำลองพยากรณ์ผสานอิทธิพลน้ำทะเลหนุนและคลื่นอ่าวไทย

เปรียบเทียบแบบจำลองทำนายระดับน้ำลุ่มเจ้าพระยาตอนล่าง (กรุงเทพฯ และปริมณฑล)
ระหว่าง:
1. แบบจำลองเดิม (Uncoupled): ใช้เฉพาะระดับน้ำต้นน้ำ + ฝนสะสม + อนุกรมเวลาเดิม
2. แบบจำลองผสานขอบเขตทะเล (Coastal-Coupled): นำเข้าระดับน้ำทะเลหนุนปากอ่าว (CPY015/GLF) และคลื่นทะเล SWAN

วัดผลที่ระยะ +6 ชม., +24 ชม., และ +48 ชม. ช่วงมหาอุทกภัยระลอกปลาย ก.ย. 2569 (20 ก.ย.–9 ต.ค. 2569)

รัน: python analysis/goal6_l3_coastal_model.py
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data/22_goal6_network/raw/l1_bkk_lower"
OUT_JSON = ROOT / "analysis/goal6/l3_coastal_summary.json"
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)


def load_series(json_path: Path) -> dict[str, float]:
    """โหลดอนุกรมเวลารายชั่วโมง {YYYY-MM-DD HH:00: value}"""
    if not json_path.exists():
        return {}
    data = json.loads(json_path.read_text(encoding="utf-8"))
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
            dstr = r[0]
            val = r[1]
        elif isinstance(r, dict):
            dstr = r.get("datetime")
            val = r.get("value")
        else:
            continue

        if val is None or not dstr:
            continue
        try:
            dstr_clean = dstr[:13] + ":00"
            out[dstr_clean] = float(val)
        except (ValueError, TypeError):
            continue
    return out


def main() -> None:
    # 1. โหลดข้อมูลอนุกรมเวลา
    # เป้าหมาย: C.12 (กรมชลประทานสามเสน กรุงเทพฯ) หรือ CPY014
    # ต้นน้ำ: C.22A หรือ BKK001
    # ทะเลหนุน: CPY015 (สะพานกรุงเทพ ปากแม่น้ำ)
    target_data = load_series(RAW_DIR / "2599_C.12_2026_hourly.json")
    if not target_data:
        target_data = load_series(RAW_DIR / "26_CPY014_2026_hourly.json")

    upstream_data = load_series(RAW_DIR / "11_BKK001_2026_hourly.json")
    tide_data = load_series(RAW_DIR / "4_CPY015_2026_hourly.json")

    # ฝนสะสมจาก NASA POWER กรุงเทพฯ
    rain_data = {}
    p_rain = RAW_DIR / "nasa_power_2026.json"
    if p_rain.exists():
        raw_r = json.loads(p_rain.read_text(encoding="utf-8"))
        daily_dict = {}
        if "กรุงเทพกลาง" in raw_r and isinstance(raw_r["กรุงเทพกลาง"], dict):
            daily_dict = raw_r["กรุงเทพกลาง"].get("daily", {})
        elif "daily" in raw_r and isinstance(raw_r["daily"], dict):
            daily_dict = raw_r["daily"]
        else:
            for k, v in raw_r.items():
                if isinstance(v, dict) and "daily" in v:
                    daily_dict = v["daily"]
                    break
                elif isinstance(v, (int, float)):
                    rain_data[k.replace("-", "")] = float(v)
        for dk, dv in daily_dict.items():
            if isinstance(dv, (int, float)):
                rain_data[dk.replace("-", "")] = float(dv)

    # 2. จัดเรียงไทม์สแตมป์รายชั่วโมงช่วง 1 ก.ค. – 9 ต.ค. 2569
    start_dt = dt.datetime(2026, 7, 1, 0, 0)
    end_dt = dt.datetime(2026, 10, 9, 23, 0)
    all_hours = []
    curr = start_dt
    while curr <= end_dt:
        all_hours.append(curr.strftime("%Y-%m-%d %H:00"))
        curr += dt.timedelta(hours=1)

    # ตรวจสอบจุดที่มีข้อมูลครบ
    valid_hours = [
        h for h in all_hours
        if h in target_data and h in upstream_data and h in tide_data
    ]
    print(f"ชั่วโมงที่มีข้อมูลพร้อมทั้ง 3 จุด: {len(valid_hours)}/{len(all_hours)} ชั่วโมง")

    test_start = "2026-09-20 00:00"

    # ความครอบคลุมจริงของช่วงทดสอบ (ตรวจ 17 ต.ค. 69: ข้อมูลเป้าหมายขาดช่วง 2–9 ต.ค.)
    test_hours_declared = [h for h in all_hours if h >= test_start]
    test_hours_usable = [
        h for h in test_hours_declared
        if h in target_data and h in upstream_data and h in tide_data
    ]
    test_coverage_pct = round(100.0 * len(test_hours_usable) / len(test_hours_declared), 1) if test_hours_declared else 0.0
    test_end_actual = max(test_hours_usable) if test_hours_usable else None

    results = {}

    for lead_h in (6, 24, 48):
        x_base, x_coastal, y_vals, test_flags, leak_flags = [], [], [], [], []

        for i in range(48, len(all_hours) - lead_h):
            t_curr = all_hours[i]
            t_lead = all_hours[i + lead_h]

            if (
                t_curr not in target_data
                or t_lead not in target_data
                or t_curr not in upstream_data
                or t_curr not in tide_data
            ):
                continue

            y = target_data[t_lead]
            h0 = target_data[t_curr]
            h1 = target_data.get(all_hours[i - 1], h0)
            h3 = target_data.get(all_hours[i - 3], h0)
            h6 = target_data.get(all_hours[i - 6], h0)

            u0 = upstream_data[t_curr]
            u6 = upstream_data.get(all_hours[i - 6], u0)
            u12 = upstream_data.get(all_hours[i - 12], u0)

            # ฝนสะสม 24 ชม. ถึงสิ้นสุดเมื่อวาน (Strictly causal, ตามระเบียบ rain_window.py ป้องกัน look-ahead)
            d_prev = (dt.datetime.strptime(t_curr.split()[0], "%Y-%m-%d") - dt.timedelta(days=1)).strftime("%Y%m%d")
            r24 = rain_data.get(d_prev, 0.0)

            # ตัวแปรแบบจำลองเดิม (Uncoupled)
            feat_base = [h0, h0 - h1, h0 - h3, h0 - h6, u0, u0 - u6, u0 - u12, r24]

            # ตัวแปรขอบเขตทะเล (Coastal-Coupled)
            tide0 = tide_data[t_curr]
            tide1 = tide_data.get(all_hours[i - 1], tide0)
            tide3 = tide_data.get(all_hours[i - 3], tide0)
            tide_diff = tide0 - tide1
            tide_head = tide0 - h0  # ความชันระดับน้ำปากอ่าวเทียบระดับน้ำในแม่น้ำ (ตรวจ Backwater)

            # เฟสดาราศาสตร์น้ำขึ้น-น้ำลงกึ่งวัน (Semidiurnal M2: คาบ 12.4206 ชั่วโมง) คำนวณจากเวลาสะสมต่อเนื่อง
            elapsed_hours = (dt.datetime.fromisoformat(t_curr) - start_dt).total_seconds() / 3600.0
            tide_phase_sin = math.sin(2.0 * math.pi * elapsed_hours / 12.4206)
            tide_phase_cos = math.cos(2.0 * math.pi * elapsed_hours / 12.4206)

            # หมายเหตุ: ไม่ใส่ swan_hs เป็นตัวแปรแล้ว (ตรวจ 17 ต.ค. 69) — ข้อมูล SWAN ที่มีเป็น
            # snapshot เดียววันที่ 16 ต.ค. (หลังช่วงทดสอบ) รวม 31 สถานีเป็นค่าเดียว = ค่าคงที่
            # ทั้งอนุกรม (ไม่มีความแปรปรวน) และเป็นข้อมูลอนาคต · โมเดลนี้จึงเป็น "Tidal-Coupled"
            # ไม่ใช่ "Wave-Coupled" จนกว่าจะมีอนุกรมคลื่นรายชั่วโมงที่ตรงช่วงเวลา
            feat_coastal = feat_base + [tide0, tide_diff, tide_head, tide_phase_sin, tide_phase_cos]

            x_base.append(feat_base)
            x_coastal.append(feat_coastal)
            y_vals.append(y)
            test_flags.append(t_curr >= test_start)
            # purge: ถ้าเป้าหมาย (t_lead) ตกอยู่ในช่วงทดสอบ ห้ามใช้เป็นตัวอย่างฝึก
            leak_flags.append(t_lead >= test_start)

        x_base = np.array(x_base)
        x_coastal = np.array(x_coastal)
        y_vals = np.array(y_vals)
        test_flags = np.array(test_flags, dtype=bool)
        leak_flags = np.array(leak_flags, dtype=bool)

        train_mask = (~test_flags) & (~leak_flags)   # purge: ตัดตัวอย่างที่เป้าหมายอยู่ในช่วงทดสอบ
        test_mask = test_flags

        # 1. Baseline: Persistence (ระดับน้ำไม่เปลี่ยน)
        h0_test = np.array([row[0] for row in x_base[test_mask]])
        y_test = y_vals[test_mask]
        rmse_persistence = float(np.sqrt(np.mean((y_test - h0_test) ** 2))) * 100.0

        # 2. Linear Regression: Base vs Coastal
        lr_base = LinearRegression().fit(x_base[train_mask], y_vals[train_mask])
        pred_lr_base = lr_base.predict(x_base[test_mask])
        rmse_lr_base = float(np.sqrt(np.mean((y_test - pred_lr_base) ** 2))) * 100.0

        lr_coastal = LinearRegression().fit(x_coastal[train_mask], y_vals[train_mask])
        pred_lr_coastal = lr_coastal.predict(x_coastal[test_mask])
        rmse_lr_coastal = float(np.sqrt(np.mean((y_test - pred_lr_coastal) ** 2))) * 100.0

        # 3. GBDT: Base vs Coastal
        gb_base = HistGradientBoostingRegressor(max_iter=100, random_state=42).fit(x_base[train_mask], y_vals[train_mask])
        pred_gb_base = gb_base.predict(x_base[test_mask])
        rmse_gb_base = float(np.sqrt(np.mean((y_test - pred_gb_base) ** 2))) * 100.0

        gb_coastal = HistGradientBoostingRegressor(max_iter=100, random_state=42).fit(x_coastal[train_mask], y_vals[train_mask])
        pred_gb_coastal = gb_coastal.predict(x_coastal[test_mask])
        rmse_gb_coastal = float(np.sqrt(np.mean((y_test - pred_gb_coastal) ** 2))) * 100.0

        imp_lr_pct = round((rmse_lr_base - rmse_lr_coastal) / rmse_lr_base * 100.0, 1)
        imp_gb_pct = round((rmse_gb_base - rmse_gb_coastal) / rmse_gb_base * 100.0, 1)
        # เทียบกับ persistence (baseline ที่ไม่ใช่โมเดล) — ตัวเลขที่ควรใช้เป็นพาดหัว
        imp_lr_vs_persistence = round((rmse_persistence - rmse_lr_coastal) / rmse_persistence * 100.0, 1)

        results[str(lead_h)] = {
            "lead_hours": lead_h,
            "persistence_rmse_cm": round(rmse_persistence, 1),
            "linear_base_rmse_cm": round(rmse_lr_base, 1),
            "linear_coastal_rmse_cm": round(rmse_lr_coastal, 1),
            "linear_improvement_pct": imp_lr_pct,
            "linear_improvement_vs_persistence_pct": imp_lr_vs_persistence,
            "gbdt_base_rmse_cm": round(rmse_gb_base, 1),
            "gbdt_coastal_rmse_cm": round(rmse_gb_coastal, 1),
            "gbdt_improvement_pct": imp_gb_pct,
            "n_train": int(np.sum(train_mask)),
            "n_test": int(np.sum(test_mask)),
        }

    summary = {
        "metadata": {
            "title": "เปรียบเทียบแบบจำลองพยากรณ์ผสานขอบเขตทะเลหนุนลุ่มเจ้าพระยาตอนล่าง (L3 Coastal-Coupled Model)",
            "target_station": "C.12 (กรมชลประทานสามเสน กรุงเทพฯ)",
            "upstream_station": "BKK001 (เจ้าพระยาตอนบน)",
            "tide_station": "CPY015 (สะพานกรุงเทพ ปากแม่น้ำเจ้าพระยา)",
            "test_window_declared": "2026-09-20..2026-10-09",
            "test_window_actual": f"2026-09-20..{test_end_actual}",
            "test_coverage_pct": test_coverage_pct,
            "train_window_actual": "2026-07-01..2026-09-19",
            "train_scope_note": "ฝึกด้วยข้อมูลปี 2569 เดียว ~47 วัน (1,130–1,467 ชม.) — ไม่ใช่ฤดูฝน 2020–2026",
            "purge_note": "ตัดตัวอย่างฝึกที่เป้าหมาย (t+lead) ตกในช่วงทดสอบ เพื่อกันการรั่วของป้าย",
            "coupling": "Tidal-Coupled (ไม่รวมคลื่น SWAN — ข้อมูลที่มีเป็น snapshot เดียวหลังช่วงทดสอบ)",
        },
        "horizons": results,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกผลการทดสอบ L3 Coastal ML: {OUT_JSON}")
    for h, r in results.items():
        print(f"  ระยะ +{h} ชม.: Linear {r['linear_base_rmse_cm']} -> {r['linear_coastal_rmse_cm']} ซม. (ดีขึ้น {r['linear_improvement_pct']}%) · GBDT {r['gbdt_base_rmse_cm']} -> {r['gbdt_coastal_rmse_cm']} ซม. (ดีขึ้น {r['gbdt_improvement_pct']}%)")


if __name__ == "__main__":
    main()
