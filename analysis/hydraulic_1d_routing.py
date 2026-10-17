"""แบบจำลองชลศาสตร์ 1 มิติ แม่น้ำนครนายก (1D Hydrodynamic River Routing)

จำลองการไหลแบบไม่คงที่ (Unsteady 1D Hydraulic Routing) บนช่วงลำน้ำที่มีหน้าตัดสำรวจจริง:
- Ny.1B บ้านเขานางบวช (กม.9.2) — 61 จุดสำรวจ
- Ny.7 ตัวเมืองนครนายก (กม.27.5) — 68 จุดสำรวจ

ขอบเขต: **Ny.1B -> Ny.7 (18.3 กม.) เท่านั้น** · Kgt.30 (กม.54.0) ยังไม่มีเงื่อนไขขอบเขต
ท้ายน้ำที่ใช้งานได้ จึงไม่ถูกใช้ในแบบจำลองนี้ (ห้ามอ้างว่าแบบจำลองครอบคลุม 43 กม.)

รัน: python analysis/hydraulic_1d_routing.py
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]

ROOT = Path(__file__).resolve().parent.parent
DATA_19 = ROOT / "data/19_rid_cross_sections/derived"
DATA_20 = ROOT / "data/20_multistation_levels"
OUT_JSON = ROOT / "analysis/hydraulic_1d_routing_summary.json"
OUT_PNG = ROOT / "report/assets/hydraulic_1d_nakhonnayok_profiles.png"


def load_cross_section(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """โหลดหน้าตัดสำรวจ (offset_m, elev_msl_m)"""
    offsets, elevs = [], []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            offsets.append(float(r["offset_m"]))
            elevs.append(float(r["elev_msl_m"]))
    # เรียงลำดับตาม offset
    idx = np.argsort(offsets)
    return np.array(offsets)[idx], np.array(elevs)[idx]


def compute_hydraulic_geometry(offsets: np.ndarray, elevs: np.ndarray, water_level: float) -> dict:
    """คำนวณพื้นที่หน้าตัด A, เส้นรอบรูปเปียก P, รัศมีชลศาสตร์ R, ความกว้างผิวน้ำ B
    และค่าการนำน้ำสองวิธี

    หน้าตัดจริงเป็น **หน้าตัดประกอบ** (ร่องน้ำลึก + ที่ราบน้ำท่วมถึงกว้างตื้น) การรวม A กับ P
    ทั้งหน้าตัดแล้วใช้ R เดียว (composite) ทำให้ R *ลดลง* เมื่อน้ำล้นขึ้นที่ราบ (P พุ่งจาก
    ~125 เป็น ~224 ม. ขณะที่ A โตช้ากว่า) → สมการ Manning ให้ Q ลดลงเมื่อระดับน้ำสูงขึ้น
    ซึ่งผิดกายภาพ และทำให้ค่า "ความจุตลิ่ง" กลายเป็นจุดสูงสุดของเส้นโค้งที่ไม่เป็นเอกภาพ

    เก็บสองค่าไว้เทียบกัน (ห้ามเลือกเงียบ ๆ):
      - conveyance_composite = A_total * (A/P)^(2/3)   ← วิธีที่ n=0.0437 ถูกสอบเทียบมาด้วย
      - conveyance_divided   = Σ A_i * (A_i/P_i)^(2/3)  ← แบ่งช่อง (vertical slice) เป็นเอกภาพเสมอ
        แต่ให้ค่า Q สูงกว่า ~30% เพราะแต่ละช่องไม่แชร์แรงเสียดทานร่วมกัน

    ค่าเริ่มต้นของ stage_to_discharge คือ composite เพื่อไม่ให้ตัวเลขที่สอบเทียบแล้วขยับ
    โดยไม่มีข้อมูลใหม่ · ค่า divided รายงานเป็นช่วงความไว (sensitivity) ใน summary
    """
    if water_level <= np.min(elevs):
        return {"area": 0.0, "perimeter": 0.0, "radius": 0.0, "width": 0.0,
                "conveyance_composite": 0.0, "conveyance_divided": 0.0}

    area = 0.0
    perimeter = 0.0
    wet_widths = []
    conv_divided = 0.0

    for i in range(len(offsets) - 1):
        x1, x2 = offsets[i], offsets[i + 1]
        y1, y2 = elevs[i], elevs[i + 1]
        dx = x2 - x1
        d1 = water_level - y1
        d2 = water_level - y2

        if d1 <= 0.0 and d2 <= 0.0:
            continue

        if d1 > 0.0 and d2 > 0.0:
            a = 0.5 * (d1 + d2) * dx
            p = math.hypot(dx, y2 - y1)
            w = dx
        else:
            frac = d1 / (d1 - d2)
            xc = x1 + frac * dx
            if d1 > 0.0:
                a = 0.5 * d1 * (xc - x1)
                p = math.hypot(xc - x1, d1)
                w = xc - x1
            else:
                a = 0.5 * d2 * (x2 - xc)
                p = math.hypot(x2 - xc, d2)
                w = x2 - xc

        area += a
        perimeter += p
        wet_widths.append(w)
        if a > 0.0 and p > 0.0:
            conv_divided += a * ((a / p) ** (2.0 / 3.0))

    width = sum(wet_widths)
    radius = (area / perimeter) if perimeter > 0 else 0.0
    conv_composite = area * (radius ** (2.0 / 3.0)) if radius > 0 else 0.0
    return {"area": area, "perimeter": perimeter, "radius": radius, "width": width,
            "conveyance_composite": conv_composite, "conveyance_divided": conv_divided}


def stage_to_discharge(geom: dict, n: float, slope: float, method: str = "composite") -> float:
    """Manning Equation: Q = (1/n) * sqrt(S) * conveyance

    method="composite" (ค่าเริ่มต้น) = A*(A/P)^(2/3) · method="divided" = Σ A_i R_i^(2/3)
    """
    key = "conveyance_divided" if method == "divided" else "conveyance_composite"
    k = geom.get(key, 0.0)
    if k <= 0.0:
        return 0.0
    return (1.0 / n) * k * math.sqrt(slope)


def run_muskingum_cunge_reach(
    inflow_q: np.ndarray,
    dt_sec: float,
    dx_m: float,
    slope: float,
    manning_n: float,
    b_avg: float,
    n_sub: int = 12,
) -> np.ndarray:
    """จำลองการเคลื่อนตัวของมวลน้ำหลากแบบ Muskingum-Cunge 1D Unsteady
    
    แบ่งช่วงย่อย n_sub ช่วง เพื่อให้สอดคล้องกับเกณฑ์เสถียรภาพ Courant:
    dx_sub ≈ c_wave * dt_sec (ป้องกันค่าสัมประสิทธิ์ c1 ติดลบ และขจัด numerical dip)
    """
    dx_sub = dx_m / float(n_sub)
    curr_inflow = inflow_q.copy()

    for _ in range(n_sub):
        n_steps = len(curr_inflow)
        outflow_q = np.zeros(n_steps)
        outflow_q[0] = curr_inflow[0]

        for t in range(n_steps - 1):
            q_ref = max(10.0, 0.5 * (curr_inflow[t] + outflow_q[t]))
            # ความเร็วคลื่น c = dQ/dA ≈ (5/3) * v (Manning)
            y_est = max(0.5, ((manning_n * q_ref) / (b_avg * math.sqrt(slope))) ** 0.6)
            v_est = q_ref / (b_avg * y_est)
            c_wave = (5.0 / 3.0) * v_est  # m/s

            k_sec = dx_sub / max(0.5, c_wave)
            x_param = 0.5 * (1.0 - q_ref / (b_avg * slope * c_wave * dx_sub))
            x_param = max(0.0, min(0.45, x_param))  # เสถียรภาพตัวแปร

            denom = 2.0 * k_sec * (1.0 - x_param) + dt_sec
            c1 = (dt_sec - 2.0 * k_sec * x_param) / denom
            c2 = (dt_sec + 2.0 * k_sec * x_param) / denom
            c3 = (2.0 * k_sec * (1.0 - x_param) - dt_sec) / denom

            q_next = c1 * curr_inflow[t + 1] + c2 * curr_inflow[t] + c3 * outflow_q[t]
            outflow_q[t + 1] = max(0.0, q_next)

        curr_inflow = outflow_q

    return curr_inflow


def main() -> None:
    # 1. โหลดหน้าตัดสำรวจ
    # ขอบเขตแบบจำลอง = Ny.1B -> Ny.7 (18.3 กม.) เท่านั้น · Kgt.30 ยังไม่มีเงื่อนไขขอบเขต
    # ท้ายน้ำที่ใช้งานได้ จึงไม่โหลด (เดิมโหลดแล้วไม่ใช้ — ทำให้เข้าใจผิดว่าเป็น 1D ครบ 43 กม.)
    x_ny1b, z_ny1b = load_cross_section(DATA_19 / "Ny.1B_profile.csv")
    x_ny7, z_ny7 = load_cross_section(DATA_19 / "Ny.7_profile.csv")

    slope_reach1 = 0.00065  # ขุนด่านฯ -> Ny.1B (ลาดชันสูง ใกล้ภูเขา)
    slope_reach2 = 0.00035  # Ny.1B -> Ny.7 (ที่ราบเมือง)
    # Manning n สอบเทียบที่ Ny.7 จากคู่ (Q,H) สังเกต — ใช้ค่าเดียวตลอดช่วง Ny.1B–Ny.7 (ความลาดชันต่างกัน ~2 เท่า)
    # · ยังไม่สอบเทียบแยกหน้าตัด (SB F-15 รีวิวรอบ 4)
    n_channel = 0.0437

    # คำนวณความจุตลิ่ง (Bankfull Capacity) Ny.1B และ Ny.7
    # คำเตือนเรื่องชื่อ (SB F-14 รีวิวรอบ 4): ค่าที่ใช้คือ "สันตลิ่ง/ตอม่อที่สำรวจ" ไม่ใช่คันดินชลประทาน
    # และไม่ใช่ระดับเริ่มท่วมที่ราบ (Ny.7 เริ่มท่วมที่ราบที่ 6.86) · key จึงใช้ bankfull_* และ terrace_onset_* เท่านั้น
    bank_ny1b = 10.60  # ม.รทก.
    geom_bank_ny1b = compute_hydraulic_geometry(x_ny1b, z_ny1b, bank_ny1b)
    q_bank_ny1b = stage_to_discharge(geom_bank_ny1b, n_channel, slope_reach1)

    bank_ny7 = 8.213   # ม.รทก.
    geom_bank_ny7 = compute_hydraulic_geometry(x_ny7, z_ny7, bank_ny7)
    q_bank_ny7 = stage_to_discharge(geom_bank_ny7, n_channel, slope_reach2)

    terrace_ny7 = 6.86
    q_terrace_ny7 = stage_to_discharge(
        compute_hydraulic_geometry(x_ny7, z_ny7, terrace_ny7), n_channel, slope_reach2)

    # 2. โหลดข้อมูลโทรมาตร 15 นาที 20–30 ก.ย. 2569
    # st61 (Ny.1B) และ st62 (Ny.7)
    times, q_obs_ny1b, h_obs_ny1b = [], [], []
    with open(DATA_20 / "st61.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            dt = r["datetime"]
            if "2026-09-24" <= dt <= "2026-09-30":
                times.append(dt)
                q_obs_ny1b.append(float(r["q_cms"]))
                h_obs_ny1b.append(float(r["level_msl_m"]))

    q_obs_ny7, h_obs_ny7 = [], []
    with open(DATA_20 / "st62.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            dt = r["datetime"]
            if "2026-09-24" <= dt <= "2026-09-30":
                q_obs_ny7.append(float(r["q_cms"]))
                h_obs_ny7.append(float(r["level_msl_m"]))

    q_obs_ny1b = np.array(q_obs_ny1b)
    h_obs_ny1b = np.array(h_obs_ny1b)
    q_obs_ny7 = np.array(q_obs_ny7)
    h_obs_ny7 = np.array(h_obs_ny7)

    # 3. รัน 1D Muskingum-Cunge จาก Ny.1B -> Ny.7 (ระยะทาง 18.3 กม.)
    dt_sec = 15.0 * 60.0  # 15 นาที = 900 วินาที
    dx_m = 18300.0        # 18.3 กม.
    b_avg = 0.5 * (geom_bank_ny1b["width"] + geom_bank_ny7["width"])

    # ตรวจค่า X ดิบของ Muskingum–Cunge ก่อนบีบ (SB F-02 รีวิวรอบ 4) — จุดตรวจ 10–1,500 ลบ.ม./วินาที ที่ n_sub=12
    _dx_sub = dx_m / 12.0
    _x_raw = []
    for _q in np.linspace(10.0, 1500.0, 30):
        _q = float(_q)
        _y = max(0.5, ((n_channel * _q) / (b_avg * math.sqrt(slope_reach2))) ** 0.6)
        _c_wave = (5.0 / 3.0) * (_q / (b_avg * _y))
        _x_raw.append(0.5 * (1.0 - _q / (b_avg * slope_reach2 * _c_wave * _dx_sub)))
    x_param_probe = {
        "q_probe_range_cms": [10.0, 1500.0],
        "x_raw_min": round(min(_x_raw), 3),
        "x_raw_max": round(max(_x_raw), 3),
        "negative_share": round(sum(1 for v in _x_raw if v < 0) / len(_x_raw), 3),
    }

    q_sim_ny7 = run_muskingum_cunge_reach(q_obs_ny1b, dt_sec, dx_m, slope_reach2, n_channel, b_avg, n_sub=12)

    # 4. แปลง Q_sim กลับเป็นระดับน้ำ h_sim ที่ Ny.7 ด้วย Rating Curve จากหน้าตัดจริง
    # หน้าตัดประกอบทำให้ q_lookup มีจุดพับ (Q ลดเมื่อระดับน้ำสูงขึ้น) -> np.interp จะให้ผล
    # ไม่มีความหมาย · ใช้เปลือกบน (running maximum) และยืนยันความเป็นเอกภาพก่อน interp
    h_test_levels = np.linspace(np.min(z_ny7) + 0.1, bank_ny7 + 2.0, 200)
    q_lookup = np.array([
        stage_to_discharge(compute_hydraulic_geometry(x_ny7, z_ny7, hl), n_channel, slope_reach2)
        for hl in h_test_levels
    ])
    order = np.argsort(h_test_levels)
    q_raw = q_lookup[order]
    q_env = np.maximum.accumulate(q_raw)
    n_folds = int(np.sum(np.diff(q_raw) < 0))
    if n_folds:
        # หน้าตัดประกอบทำให้ Q(H) ไม่เป็นเอกภาพ · เปลือกบนคืน "ระดับน้ำต่ำสุดที่รับ Q นั้นได้"
        # ซึ่งเป็นสาขาที่ถูกต้องสำหรับ rating · ห้าม interp กับ q_raw ตรง ๆ
        print(f"  หมายเหตุ: rating curve มีจุดพับ {n_folds} จุด — ใช้เปลือกบนในการผกผัน")
    if np.any(np.diff(q_env) < 0):  # ค้ำประกันเชิงโครงสร้าง (ไม่ควรเกิด)
        raise ValueError("เปลือกบนของ rating curve ยังลดลง — ตรรกะผกผันผิด")
    h_sim_ny7 = np.interp(q_sim_ny7, q_env, h_test_levels[order])

    # 4b. ช่วงความไวของ Manning สองวิธี (composite vs divided) — รายงานคู่กันเสมอ
    def rating_sensitivity(x, z, slope, stages):
        out = {}
        for label, lvl in stages.items():
            g = compute_hydraulic_geometry(x, z, lvl)
            out[label] = {
                "stage_msl_m": round(float(lvl), 2),
                "q_composite_cms": round(stage_to_discharge(g, n_channel, slope), 1),
                "q_divided_cms": round(stage_to_discharge(g, n_channel, slope, "divided"), 1),
            }
        return out

    # คำนวณความคลาดเคลื่อน (RMSE) ช่วงน้ำหลาก 26–28 ก.ย.
    mask_event = [("2026-09-26" <= t <= "2026-09-28") for t in times]
    rmse_q_cms = float(np.sqrt(np.mean((q_sim_ny7[mask_event] - q_obs_ny7[mask_event]) ** 2)))
    rmse_h_m = float(np.sqrt(np.mean((h_sim_ny7[mask_event] - h_obs_ny7[mask_event]) ** 2)))
    # แยกองค์ประกอบความคลาดเคลื่อนระดับน้ำ (SB F-24 รีวิวรอบ 4): ความเอนเอียงคงที่ + ส่วนที่เหลือ
    bias_h_m = float(np.mean(h_sim_ny7[mask_event] - h_obs_ny7[mask_event]))

    # 4c. ตารางลู่เข้า (grid convergence) — RMSE ต้องไม่แย่ลงเมื่อแบ่งช่วงย่อยละเอียดขึ้น
    convergence = {}
    for ns in (6, 12, 24, 48):
        qs = run_muskingum_cunge_reach(q_obs_ny1b, dt_sec, dx_m, slope_reach2, n_channel, b_avg, n_sub=ns)
        hs = np.interp(qs, q_env, h_test_levels[order])
        convergence[str(ns)] = {
            "q_peak_cms": round(float(np.max(qs)), 1),
            "rmse_q_cms": round(float(np.sqrt(np.mean((qs[mask_event] - q_obs_ny7[mask_event]) ** 2))), 1),
            "rmse_h_cm": round(float(np.sqrt(np.mean((hs[mask_event] - h_obs_ny7[mask_event]) ** 2))) * 100.0, 1),
        }

    # เวลาเดินทางของยอดคลื่นน้ำ (Peak Wave Travel Time: ร่องน้ำ Ny.1B สู่ Ny.7 18.3 กม.)
    idx_pk_ny1b = int(np.argmax(q_obs_ny1b))
    idx_pk_ny7_sim = int(np.argmax(q_sim_ny7))
    travel_time_hours_sim = (idx_pk_ny7_sim - idx_pk_ny1b) * 0.25

    # เวลาเดินทางสังเกตจากระดับน้ำจริง (Stage Peak Lag: Ny.1B สู่ Ny.7 รวมการหน่วงทุ่ง)
    idx_pk_h_ny1b = int(np.argmax(h_obs_ny1b))
    idx_pk_h_ny7 = int(np.argmax(h_obs_ny7))
    travel_time_stage_obs = (idx_pk_h_ny7 - idx_pk_h_ny1b) * 0.25

    # F-04: ยอดของ q_cms (สถานีรายงานเอง) ไม่ตรงกับยอดของ level_msl_m ที่สถานีเดียวกัน
    # และเหลื่อมคนละทิศ — วัดส่วนเหลื่อมไว้เป็นหลักฐานแทนการรายงาน "เวลาเดินทาง" ที่ผิดความหมาย
    idx_pk_q_ny1b = int(np.argmax(q_obs_ny1b))
    idx_pk_q_ny7 = int(np.argmax(q_obs_ny7))
    q_h_offset_ny1b_h = (idx_pk_h_ny1b - idx_pk_q_ny1b) * 0.25   # + = ยอด Q มาก่อนยอด H
    q_h_offset_ny7_h = (idx_pk_h_ny7 - idx_pk_q_ny7) * 0.25

    # สรุปผล
    summary = {
        "metadata": {
            "title": "แบบจำลองชลศาสตร์ 1 มิติ แม่น้ำนครนายก (1D Hydrodynamic Routing)",
            "reach_ny1b_to_ny7_km": 18.3,
            "model_scope_note": "ครอบคลุม Ny.1B–Ny.7 (18.3 กม.) เท่านั้น — ยังไม่มีเงื่อนไขขอบเขตท้ายน้ำที่ Kgt.30",
            "manning_n": n_channel,
            "manning_n_note": "n สอบเทียบที่ Ny.7 เท่านั้น (คู่ Q,H สังเกต) แล้วใช้ค่าเดียวตลอดช่วง Ny.1B–Ny.7 แม้ความลาดชันต่างกัน · สอบเทียบกับวิธี composite (A_total, P_total) — ยังไม่สอบเทียบใหม่สำหรับวิธี divided และยังไม่สอบเทียบ n แยกหน้าตัด (SB F-15)",
            "muskingum_x_note": "ค่า X ในสูตร x = 0.5·(1 − q/(B·S·c·dx)) · ตรวจเส้น 10–1,500 ลบ.ม./วินาที (n_sub=12) ค่าดิบติดลบทุกจุดที่อัตราไหลช่วงน้ำหลาก (q ≳ 100) → โค้ดบีบเป็น X = 0 โดยปริยาย (เดินเป็นคลื่นแพร่ ไม่ใช่ค่า X ที่สอบเทียบ) · ยังไม่ทดลองแผนผลต่าง–แพร่ที่ลู่เข้า (SB F-02)",
            "x_param_probe": x_param_probe,
            "conveyance_method": "composite",
            "slope_reach1": slope_reach1,
            "slope_reach2": slope_reach2,
            "sim_time_step_min": 15,
            "n_subreaches": 12,
        },
        "ny1b_hydraulics": {
            "station": "Ny.1B (บ้านเขานางบวช)",
            "bankfull_crest_msl_m": bank_ny1b,
            "bankfull_top_width_m": round(geom_bank_ny1b["width"], 1),
            "bankfull_area_m2": round(geom_bank_ny1b["area"], 1),
            "bankfull_capacity_q_cms": round(q_bank_ny1b, 1),
            "peak_stage_msl_m": round(float(np.max(h_obs_ny1b)), 2),
            "peak_q_cms": round(float(np.max(q_obs_ny1b)), 1),
            "peak_above_bankfull_m": round(float(np.max(h_obs_ny1b) - bank_ny1b), 2),
            "rid_declared_braelevel_msl_m": 8.81,
            "note": "bankfull = สันตลิ่ง/ตอม่อที่สำรวจ (10.60) ไม่ใช่คันดินชลประทาน · ระดับตลิ่งที่กรมชลฯ ประกาศ (braelevel 8.81) ต่างจากสันหน้าตัด 1.79 ม. — คนละนิยาม (SB F-14)",
        },
        "ny7_hydraulics": {
            "station": "Ny.7 (สะพานเทศบาลนครนายก)",
            "bankfull_crest_msl_m": round(bank_ny7, 2),
            "terrace_onset_msl_m": terrace_ny7,
            "bankfull_top_width_m": round(geom_bank_ny7["width"], 1),
            "bankfull_area_m2": round(geom_bank_ny7["area"], 1),
            "bankfull_capacity_q_cms": round(q_bank_ny7, 1),
            "terrace_onset_q_cms": round(q_terrace_ny7, 1),
            "peak_stage_msl_m": round(float(np.max(h_obs_ny7)), 2),
            "peak_q_cms": round(float(np.max(q_obs_ny7)), 1),
            "note": "bankfull = สันตลิ่ง/ตอม่อสำรวจ 8.213 · terrace_onset = ระดับเริ่มท่วมที่ราบ 6.86 (คนละนิยาม — SB F-14)",
        },
        "routing_performance": {
            "travel_time_hours_sim": round(travel_time_hours_sim, 2),
            "travel_time_stage_obs": round(travel_time_stage_obs, 2),
            "q_h_peak_offset_ny1b_h": round(q_h_offset_ny1b_h, 2),
            "q_h_peak_offset_ny7_h": round(q_h_offset_ny7_h, 2),
            "travel_time_caveat": (
                "ใช้ยอด *ระดับน้ำ* เป็นหลักเท่านั้น · q_cms เป็นค่าที่สถานีรายงานเอง "
                "ไม่ได้คำนวณจาก level_msl_m ด้วยเส้นความสัมพันธ์เส้นเดียว — ยอด Q เหลื่อมจากยอด H "
                f"ที่ Ny.1B {q_h_offset_ny1b_h:+.2f} ชม. และที่ Ny.7 {q_h_offset_ny7_h:+.2f} ชม. "
                "จึงไม่มี 'เวลาเดินทางที่นับจากยอด Q' รายงานในไฟล์นี้ (ค่าที่เคยรายงานถูกถอนออกแล้ว) "
                "· travel_time_hours_sim เป็น Q→Q ของแบบจำลอง ส่วน travel_time_stage_obs เป็น H→H "
                "ของข้อมูลจริง สองค่านี้จึงเทียบกันตรง ๆ ไม่ได้"
            ),
            "rmse_discharge_cms": round(rmse_q_cms, 2),
            "rmse_stage_cm": round(rmse_h_m * 100.0, 1),
            "stage_bias_cm": round(bias_h_m * 100.0, 1),
            "stage_residual_cm": round(math.sqrt(max(rmse_h_m ** 2 - bias_h_m ** 2, 0.0)) * 100.0, 1),
            "stage_error_note": "RMSE ระดับน้ำแยกเป็นความเอนเอียงคงที่ (bias) + ส่วนที่เหลือ · ส่วนหลักของความคลาดเคลื่อนมาจากเส้นระดับ–ปริมาณน้ำ (rating) ที่ยังไม่สอบเทียบ ไม่ใช่ทักษะการเดินตัวของแบบจำลอง (SB F-24)",
            "q_peak_sim_cms": round(float(np.max(q_sim_ny7)), 1),
            "q_peak_obs_cms": round(float(np.max(q_obs_ny7)), 1),
        },
        "rating_sensitivity": {
            "note": "Manning สองวิธีบนหน้าตัดเดียวกัน · composite = วิธีที่ n ถูกสอบเทียบมาด้วย · divided = แบ่งช่อง (เอกภาพแต่ให้ค่าสูงกว่า ~30%) · ny1b_flat_slope = Ny.1B บนความลาดชันเรียบช่วงท้ายน้ำ (0.00035) — ปลายล่างของช่วงความไม่แน่นอน · ช่วงนี้คือความไม่แน่นอนของ rating (SB F-01)",
            "ny1b": rating_sensitivity(x_ny1b, z_ny1b, slope_reach1,
                                       {"terrace_onset_6.86": 6.86, "bankfull_crest_10.60": 10.60, "peak_11.00": 11.00}),
            "ny1b_flat_slope": rating_sensitivity(x_ny1b, z_ny1b, slope_reach2,
                                                  {"bankfull_crest_10.60": 10.60, "peak_11.00": 11.00}),
            "ny7": rating_sensitivity(x_ny7, z_ny7, slope_reach2,
                                      {"terrace_onset_6.86": 6.86, "peak_7.68": 7.68, "bankfull_crest_8.213": 8.213}),
        },
        "grid_convergence": {
            "note": "RMSE ไม่ลดลงเมื่อแบ่งช่วงย่อยละเอียดขึ้น → ผลที่ n_sub=12 เป็นค่าที่ 'พอดี' ไม่ใช่ค่าที่ลู่เข้า · ห้ามอ้างว่าเป็นคำตอบเชิงกายภาพ",
            "n_sub_6": convergence["6"],
            "n_sub_12": convergence["12"],
            "n_sub_24": convergence["24"],
            "n_sub_48": convergence["48"],
        },
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกผลการวิเคราะห์ชลศาสตร์ 1 มิติ: {OUT_JSON}")

    # 5. สร้างกราฟแสดงผล
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5), dpi=200)

    # รูปตัดขวางเปรียบเทียบ Ny.1B และ Ny.7
    ax1.plot(x_ny1b, z_ny1b, color="#2c3e50", lw=2, label="หน้าตัดลำน้ำ Ny.1B (กม.9.2)")
    ax1.axhline(bank_ny1b, color="#e67e22", ls="--", lw=1.5, label=f"ระดับตลิ่ง Ny.1B (+{bank_ny1b:.2f} ม.รทก.)")
    ax1.axhline(np.max(h_obs_ny1b), color="#c0392b", ls="-", lw=1.5, label=f"ระดับน้ำสูงสุดจริง (+{np.max(h_obs_ny1b):.2f} ม.รทก.)")
    ax1.fill_between(x_ny1b, z_ny1b, np.max(h_obs_ny1b), where=(z_ny1b <= np.max(h_obs_ny1b)), color="#3498db", alpha=0.35)
    ax1.set_title("ก) รูปตัดขวางลำน้ำสำรวจจริง สถานี Ny.1B บ้านเขานางบวช (61 จุดสำรวจ RID SWOC)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("ระยะตามแนวขวางลำน้ำ (เมตร)", fontsize=10)
    ax1.set_ylabel("ระดับความสูง (ม.รทก.)", fontsize=10)
    ax1.grid(True, alpha=0.3, ls=":")
    ax1.legend(loc="upper right", framealpha=0.9)

    # ไฮโดรกราฟการเคลื่อนตัวของน้ำหลาก
    # แปลงเวลาเป็นชั่วโมงนับจาก 24 ก.ย.
    hrs = np.arange(len(times)) * 0.25
    ax2.plot(hrs, q_obs_ny1b, color="#2980b9", lw=1.8, label="อัตราไหล Ny.1B ต้นน้ำ (จริง)")
    ax2.plot(hrs, q_sim_ny7, color="#27ae60", lw=2.0, ls="-", label=f"1D Hydrodynamic Routing ไป Ny.7 (จำลอง: ยอดน้ำหลากหน่วง {travel_time_hours_sim:.1f} ชม.)")
    ax2.plot(hrs, q_obs_ny7, color="#c0392b", lw=1.8, ls="--", label="อัตราไหล Ny.7 ตัวเมือง (วัดจริง)")
    ax2.axhline(q_bank_ny7, color="#d35400", ls=":", lw=1.5, label=f"ความจุลำน้ำ Ny.7 ก่อนล้นตลิ่ง ({q_bank_ny7:.1f} ม³/วิ)")
    ax2.set_title("ข) การเคลื่อนตัวของมวลน้ำหลากตามแนวลำน้ำ: จาก Ny.1B สู่ Ny.7 (18.3 กม.)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("เวลา (ชั่วโมงนับจาก 24 ก.ย. 2569 00:00)", fontsize=10)
    ax2.set_ylabel("อัตราการไหล (ลบ.ม./วินาที)", fontsize=10)
    ax2.grid(True, alpha=0.3, ls=":")
    ax2.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    fig.savefig(OUT_PNG)
    plt.close(fig)
    print(f"บันทึกภาพกราฟชลศาสตร์: {OUT_PNG}")


if __name__ == "__main__":
    main()
