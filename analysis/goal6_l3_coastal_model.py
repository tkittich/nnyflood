"""เป้าหมาย 6 — L3 Coastal-Coupled Model: แบบจำลองพยากรณ์ผสานอิทธิพลน้ำทะเลหนุน (ไม่รวมคลื่นลม)

เปรียบเทียบแบบจำลองทำนายระดับน้ำลุ่มเจ้าพระยาตอนล่าง (กรุงเทพฯ และปริมณฑล)
ระหว่าง:
1. แบบจำลองเดิม (Uncoupled): ใช้เฉพาะระดับน้ำต้นน้ำ + ฝนวันก่อนหน้า + อนุกรมเวลาเดิม
2. แบบจำลองผสานขอบเขตทะเล (Coastal-Coupled): นำเข้าระดับน้ำทะเลหนุนปากอ่าว (CPY015 สะพานกรุงเทพ) เท่านั้น
   — ไม่รวมคลื่นลม SWAN (ข้อมูลคลื่นที่มีเป็นค่าเดียวหลังช่วงทดสอบ ใช้เป็นตัวแปรไม่ได้; ดูข้อจำกัดในไฟล์สรุป)

วัดผลที่ระยะ +6 ชม., +24 ชม., และ +48 ชม. ช่วงมหาอุทกภัยระลอกปลาย ก.ย. 2569 (20 ก.ย.–9 ต.ค. 2569)

รีวิวรอบ 4 (17 ต.ค. 69) — ปรับปรุงตามข้อพบ:
  · ถอดตัวแปร tide_head (tide0 − h0) ที่ซ้ำเชิงเส้นสนิทกับ h0 และ tide0 (BP F-03) + ตรวจอันดับเมทริกซ์ยืนยัน
  · ฐานเทียบเพิ่ม "ค่าเดิมคงที่แบบรู้ทะเล" h0 + (tide(t+lead) − tide(t)) — ฐานที่เป็นธรรมกับโมเดลผสานทะเล (BP F-04 · GLM F-08)
  · ทุกระยะใช้ชุดตัวอย่างชุดเดียวกัน (บังคับให้มีข้อมูลปลายทางและน้ำขึ้น–น้ำลงครบทุกระยะ) — n_test เท่ากัน (BP F-04)
  · ช่วงความเชื่อมั่น 95% (bootstrap) ของส่วนต่าง vs ฐานเทียบทั้งสองแบบ — กันนำเดลต้าลบเล็ก ๆ ไปเทียบเชิงกำลัง (GLM F-08)
  · นับจำนวนจุดที่ต้องเติมค่า (lag ขาด, ฝนขาด) + ระบุสาเหตุที่ช่วงทดสอบสั้น: อนุกรม BKK001 สิ้นสุด 2 ต.ค. (SB F-17/F-18)

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

LEADS = (6, 24, 48)
TEST_START = "2026-09-20 00:00"


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


def rmse_cm(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y - p) ** 2))) * 100.0


def bootstrap_ci_pct(y: np.ndarray, p_base: np.ndarray, p_new: np.ndarray,
                     n_boot: int = 2000, seed: int = 7) -> list[float]:
    """ช่วงความเชื่อมั่น 95% (percentile bootstrap) ของส่วนต่าง RMSE เป็น % ของฐานเทียบ"""
    rng = np.random.default_rng(seed)
    n = len(y)
    d = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        rb = math.sqrt(np.mean((y[idx] - p_base[idx]) ** 2))
        rn = math.sqrt(np.mean((y[idx] - p_new[idx]) ** 2))
        d[b] = (rb - rn) / rb * 100.0
    return [round(float(np.percentile(d, 2.5)), 1), round(float(np.percentile(d, 97.5)), 1)]


def main() -> None:
    # 1. โหลดข้อมูลอนุกรมเวลา
    # เป้าหมาย: C.12 (กรมชลประทานสามเสน กรุงเทพฯ) หรือ CPY014
    # ต้นน้ำ: BKK001 (ฝั่งเจ้าพระยาตอนบน)
    # ทะเลหนุน: CPY015 (สะพานกรุงเทพ ปากแม่น้ำ)
    target_data = load_series(RAW_DIR / "2599_C.12_2026_hourly.json")
    if not target_data:
        target_data = load_series(RAW_DIR / "26_CPY014_2026_hourly.json")

    upstream_data = load_series(RAW_DIR / "11_BKK001_2026_hourly.json")
    tide_data = load_series(RAW_DIR / "4_CPY015_2026_hourly.json")

    # ฝนจาก NASA POWER กรุงเทพฯ (รายวัน — ใช้ "วันก่อนหน้า", ไม่ใช่ 24 ชม.ย้อนหลัง: SB F-17)
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

    # 3. ประกอบ "ชุดตัวอย่างร่วมทุกระยะ" (BP F-04): บังคับให้มีข้อมูล
    #    - จุดนำเข้าที่ t: เป้าหมาย + ต้นน้ำ + น้ำขึ้นน้ำลง
    #    - ปลายทางที่ t+6/t+24/t+48: เป้าหมาย + น้ำขึ้นน้ำลง (สำหรับฐานเทียบแบบรู้ทะเล)
    imp = {"h1": 0, "h3": 0, "h6": 0, "u6": 0, "u12": 0, "tide1": 0, "rain_zero": 0}
    rows = []
    for i in range(48, len(all_hours) - max(LEADS)):
        t_curr = all_hours[i]
        if (t_curr not in target_data) or (t_curr not in upstream_data) or (t_curr not in tide_data):
            continue
        leads_ts = [all_hours[i + h] for h in LEADS]
        if not all((lt in target_data and lt in tide_data) for lt in leads_ts):
            continue

        h0 = target_data[t_curr]
        h1 = target_data.get(all_hours[i - 1])
        if h1 is None:
            imp["h1"] += 1
            h1 = h0
        h3 = target_data.get(all_hours[i - 3])
        if h3 is None:
            imp["h3"] += 1
            h3 = h0
        h6 = target_data.get(all_hours[i - 6])
        if h6 is None:
            imp["h6"] += 1
            h6 = h0

        u0 = upstream_data[t_curr]
        u6 = upstream_data.get(all_hours[i - 6])
        if u6 is None:
            imp["u6"] += 1
            u6 = u0
        u12 = upstream_data.get(all_hours[i - 12])
        if u12 is None:
            imp["u12"] += 1
            u12 = u0

        d_prev = (dt.datetime.strptime(t_curr.split()[0], "%Y-%m-%d") - dt.timedelta(days=1)).strftime("%Y%m%d")
        r_prev = rain_data.get(d_prev)
        if r_prev is None:
            imp["rain_zero"] += 1
            r_prev = 0.0

        # เฟสดาราศาสตร์น้ำขึ้น-น้ำลงกึ่งวัน (Semidiurnal M2: คาบ 12.4206 ชั่วโมง) คำนวณจากเวลาสะสมต่อเนื่อง
        elapsed_hours = (dt.datetime.fromisoformat(t_curr) - start_dt).total_seconds() / 3600.0
        tide_phase_sin = math.sin(2.0 * math.pi * elapsed_hours / 12.4206)
        tide_phase_cos = math.cos(2.0 * math.pi * elapsed_hours / 12.4206)

        tide0 = tide_data[t_curr]
        tide1 = tide_data.get(all_hours[i - 1])
        if tide1 is None:
            imp["tide1"] += 1
            tide1 = tide0

        # ตัวแปรแบบจำลองเดิม (Uncoupled)
        feat_base = [h0, h0 - h1, h0 - h3, h0 - h6, u0, u0 - u6, u0 - u12, r_prev]
        # ตัวแปรขอบเขตทะเล (Coastal-Coupled) — ไม่มี tide_head (ซ้ำเชิงเส้นสนิทกับ h0+tide0: BP F-03)
        # หมายเหตุ: SWAN ไม่ใช่ตัวแปร (ค่าเดียวหลังช่วงทดสอบ) — โมเดลนี้จึงเป็น "Tidal-Coupled"
        feat_coastal = feat_base + [tide0, tide0 - tide1, tide_phase_sin, tide_phase_cos]

        rows.append({
            "t": t_curr,
            "leads_ts": leads_ts,
            "y": [target_data[lt] for lt in leads_ts],
            "tide_leads": [tide_data[lt] for lt in leads_ts],
            "tide0": tide0,
            "h0": h0,
            "xb": feat_base,
            "xc": feat_coastal,
            "test": t_curr >= TEST_START,
        })

    Xb = np.array([r["xb"] for r in rows], dtype=float)
    Xc = np.array([r["xc"] for r in rows], dtype=float)
    Y = np.array([r["y"] for r in rows], dtype=float)
    TIDE_LEADS = np.array([r["tide_leads"] for r in rows], dtype=float)
    TIDE0 = np.array([r["tide0"] for r in rows], dtype=float)
    H0 = np.array([r["h0"] for r in rows], dtype=float)
    test_mask = np.array([r["test"] for r in rows], dtype=bool)
    leak = np.array([[lt >= TEST_START for lt in r["leads_ts"]] for r in rows], dtype=bool)

    # ความครอบคลุมจริงของช่วงทดสอบ + สาเหตุที่สั้น (SB F-18: ระบุชื่อสถานีที่ทำให้จบ)
    test_hours_declared = [h for h in all_hours if h >= TEST_START]
    n_usable_test = int(test_mask.sum())
    test_coverage_pct = round(100.0 * n_usable_test / len(test_hours_declared), 1) if test_hours_declared else 0.0
    test_end_actual = max(r["t"] for r in rows if r["test"]) if n_usable_test else None
    # เพดานจาก BKK001 อย่างเดียว (ก่อนคิดช่องว่างของจุดอื่น) — แสดงที่มาของความครอบคลุมให้ตรง (SB F-18)
    up_end = max(upstream_data) if upstream_data else None
    cap_up = [h for h in test_hours_declared if up_end is None or h <= up_end] if test_hours_declared else []
    cap_up_pct = round(100.0 * len(cap_up) / len(test_hours_declared), 1) if test_hours_declared else 0.0

    series_end = {
        "target_C12": max(target_data) if target_data else None,
        "upstream_BKK001": max(upstream_data) if upstream_data else None,
        "tide_CPY015": max(tide_data) if tide_data else None,
    }

    rank_full = int(np.linalg.matrix_rank(Xc))
    rank_note = (
        "อันดับเมทริกซ์เต็ม (ไม่มีความซ้ำเชิงเส้น) — ถอด tide_head ออกแล้ว (BP F-03)"
        if rank_full == Xc.shape[1]
        else f"พบความซ้ำเชิงเส้นคงเหลือ: อันดับ {rank_full} < จำนวนคอลัมน์ {Xc.shape[1]}"
    )

    results = {}
    for k, lead_h in enumerate(LEADS):
        y = Y[:, k]
        train_mask = (~test_mask) & (~leak[:, k])   # purge: เป้าหมายระยะนี้ตกในช่วงทดสอบ = ห้ามฝึก
        y_train, y_test = y[train_mask], y[test_mask]

        h0_test = H0[test_mask]
        tide_leads_test = TIDE_LEADS[test_mask, k]
        tide0_test = TIDE0[test_mask]

        # ฐานเทียบ 1: ค่าเดิมคงที่ (ระดับน้ำไม่เปลี่ยน)
        pred_pers = h0_test
        rmse_persistence = rmse_cm(y_test, pred_pers)

        # ฐานเทียบ 2: ค่าเดิมคงที่แบบรู้ทะเล h0 + (tide(t+lead) − tide(t)) — ฐานที่เป็นธรรมขึ้น (BP F-04 · GLM F-08)
        pred_pers_tide = h0_test + (tide_leads_test - tide0_test)
        rmse_persistence_tide = rmse_cm(y_test, pred_pers_tide)

        # โมเดล: linear/GBDT × base/coastal
        lr_base = LinearRegression().fit(Xb[train_mask], y_train)
        pred_lr_base = lr_base.predict(Xb[test_mask])
        rmse_lr_base = rmse_cm(y_test, pred_lr_base)

        lr_coastal = LinearRegression().fit(Xc[train_mask], y_train)
        pred_lr_coastal = lr_coastal.predict(Xc[test_mask])
        rmse_lr_coastal = rmse_cm(y_test, pred_lr_coastal)

        gb_base = HistGradientBoostingRegressor(max_iter=100, random_state=42).fit(Xb[train_mask], y_train)
        pred_gb_base = gb_base.predict(Xb[test_mask])
        rmse_gb_base = rmse_cm(y_test, pred_gb_base)

        gb_coastal = HistGradientBoostingRegressor(max_iter=100, random_state=42).fit(Xc[train_mask], y_train)
        pred_gb_coastal = gb_coastal.predict(Xc[test_mask])
        rmse_gb_coastal = rmse_cm(y_test, pred_gb_coastal)

        imp_lr_pct = round((rmse_lr_base - rmse_lr_coastal) / rmse_lr_base * 100.0, 1)
        imp_gb_pct = round((rmse_gb_base - rmse_gb_coastal) / rmse_gb_base * 100.0, 1)
        imp_lr_vs_persistence = round((rmse_persistence - rmse_lr_coastal) / rmse_persistence * 100.0, 1)
        imp_lr_vs_tide = round((rmse_persistence_tide - rmse_lr_coastal) / rmse_persistence_tide * 100.0, 1)
        ci_vs_persistence = bootstrap_ci_pct(y_test, pred_pers, pred_lr_coastal)
        ci_vs_tide = bootstrap_ci_pct(y_test, pred_pers_tide, pred_lr_coastal)

        results[str(lead_h)] = {
            "lead_hours": lead_h,
            "persistence_rmse_cm": round(rmse_persistence, 1),
            "persistence_tide_rmse_cm": round(rmse_persistence_tide, 1),
            "linear_base_rmse_cm": round(rmse_lr_base, 1),
            "linear_coastal_rmse_cm": round(rmse_lr_coastal, 1),
            "linear_improvement_pct": imp_lr_pct,
            "linear_improvement_vs_persistence_pct": imp_lr_vs_persistence,
            "linear_improvement_vs_persistence_ci95_pct": ci_vs_persistence,
            "linear_improvement_vs_tide_persistence_pct": imp_lr_vs_tide,
            "linear_improvement_vs_tide_persistence_ci95_pct": ci_vs_tide,
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
            "series_end": series_end,
            "truncation_cause": (
                "ช่วงทดสอบสิ้นสุด (test_window_actual) เพราะอนุกรม BKK001 (ต้นน้ำ) สิ้นสุดก่อน C.12 และ CPY015 "
                "— ไม่ใช่ 'ข้อมูลเป้าหมายขาดช่วง 2–9 ต.ค.' (SB F-18) · ส่วนความครอบคลุมที่หายไปเกินเพดาน BKK001 "
                "มาจากชั่วโมงข้อมูลขาดของจุดเป้าหมาย/น้ำขึ้น–น้ำลง (ดู test_coverage_breakdown)"
            ),
            "test_coverage_breakdown": {
                "declared_hours": len(test_hours_declared),
                "cap_hours_if_BKK001_complete": len(cap_up),
                "cap_pct_if_BKK001_complete": cap_up_pct,
                "usable_hours": n_usable_test,
                "usable_pct": test_coverage_pct,
                "note": (
                    "เพดาน = ชั่วโมงตั้งแต่ 20 ก.ย. ถึงเวลาสิ้นสุดของ BKK001 (ถ้าจุดอื่นไม่ขาด) · "
                    "ค่าจริงต่ำกว่าเพราะชั่วโมงข้อมูลขาดในชุดเป้าหมาย/น้ำขึ้น–น้ำลงเมื่อบังคับครบทุกระยะ"
                ),
            },
            "train_window_actual": "2026-07-01..2026-09-19",
            "train_scope_note": (
                "ฝึกด้วยข้อมูลปี 2569 เดียว ~47 วัน — ไม่ใช่ฤดูฝน 2020–2026 · ยังไม่ fit หลายฤดู "
                "(ต้องรอข้อมูลฤดูถัดไป; GLM F-08 · SB F-16) จึงเป็น 'การพยากรณ์ในช่วงเหตุการณ์เดียว' ไม่ใช่การทดสอบวางนัยทั่วไป"
            ),
            "purge_note": (
                "ตัดตัวอย่างฝึกเมื่อ 'เป้าหมายของระยะนั้น' (t+lead) ตกในช่วงทดสอบ — n_train ต่างกันเล็กน้อยตามระยะ "
                "โดยออกแบบ (n_test เท่ากันทุกระยะ)"
            ),
            "common_sample_note": (
                "ทุกระยะใช้ชุดตัวอย่างชุดเดียวกัน (บังคับให้มีข้อมูลปลายทางและน้ำขึ้น–น้ำลงครบทั้ง +6/+24/+48 ชม.) "
                "— เทียบข้ามระยะได้ตรง (BP F-04)"
            ),
            "coupling": "Tidal-Coupled (ไม่รวมคลื่น SWAN — ข้อมูลที่มีเป็น snapshot เดียวหลังช่วงทดสอบ)",
            "feature_rank_check": {"n_features": int(Xc.shape[1]), "rank": rank_full, "note": rank_note},
            "imputation_counters": {
                **imp,
                "n_samples_all": len(rows),
                "note": (
                    "จำนวนตัวอย่างที่ต้องเติมค่าแทนจุดข้อมูลขาด: lag ระดับน้ำ (แทนด้วย h0), lag ต้นน้ำ (แทน u0), "
                    "น้ำขึ้น–น้ำลง lag 1 ชม. (แทน tide0), ฝนวันก่อนหน้า (แทน 0) — เปิดเผยก่อนตีความ (GLM F-07 · SB F-17)"
                ),
            },
            "rain_note": (
                "R24 = ผลรวมฝนรายวัน NASA POWER จุดกรุงเทพกลาง ของ 'วันก่อนหน้า' (ไม่ใช่ 24 ชม.ย้อนหลัง) · "
                "ข้อมูลฝนต้นทางเป็นรายวัน จึงสร้างหน้าต่าง 24 ชม. ย้อนหลังจริงไม่ได้ — ระบุเป็นข้อจำกัด (SB F-17) · "
                "จุดเดียว ไม่ใช่ฝนเฉลี่ยพื้นที่ · วันที่ฝนขาดนับเป็น 0 ตามจำนวนใน imputation_counters"
            ),
            "persistence_note": (
                "ฐานเทียบสองแบบ: ค่าเดิมคงที่ (ระดับน้ำไม่เปลี่ยน) และค่าเดิมคงที่แบบรู้ทะเล "
                "h0 + (tide(t+lead) − tide(t)) — ตัวหลังเป็นฐานที่เป็นธรรมกับโมเดลผสานทะเล (BP F-04 · GLM F-08)"
            ),
            "statistical_power_note": (
                "ช่วงความเชื่อมั่น 95% จาก bootstrap บนชุดทดสอบเดียว (2,000 ครั้ง, seed คงที่) — "
                "ส่วนต่างที่ช่วงคร่อมศูนย์ = 'ยังสรุปทิศทางไม่ได้' ห้ามนำไปเทียบเชิงกำลังกับส่วนต่างช่วงแคบ "
                "โดยเฉพาะ +24/+48 ชม. (GLM F-08)"
            ),
        },
        "horizons": results,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกผลการทดสอบ L3 Coastal ML: {OUT_JSON}")
    print(f"  ชุดตัวอย่างร่วมทุกระยะ: {len(rows)} แถว · ทดสอบได้ {n_usable_test} ชม. ({test_coverage_pct}% ของช่วงประกาศ)")
    print(f"  อนุกรมสิ้นสุด: C.12 {series_end['target_C12']} · BKK001 {series_end['upstream_BKK001']} · CPY015 {series_end['tide_CPY015']}")
    print(f"  อันดับเมทริกซ์ผสานทะเล: {rank_full}/{Xc.shape[1]}")
    for h, r in results.items():
        print(f"  ระยะ +{h} ชม.: linear {r['linear_base_rmse_cm']} -> {r['linear_coastal_rmse_cm']} ซม. "
              f"(ดีขึ้น {r['linear_improvement_pct']}%) · vs ค่าเดิมคงที่ธรรมดา {r['linear_improvement_vs_persistence_pct']}% "
              f"{r['linear_improvement_vs_persistence_ci95_pct']} · vs รู้ทะเล {r['linear_improvement_vs_tide_persistence_pct']}% "
              f"{r['linear_improvement_vs_tide_persistence_ci95_pct']} · GBDT {r['gbdt_base_rmse_cm']} -> {r['gbdt_coastal_rmse_cm']} ซม.")


if __name__ == "__main__":
    main()
