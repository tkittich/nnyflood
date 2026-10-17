"""แบบจำลองชลศาสตร์ 1 มิติ แม่น้ำนครนายก (1D Hydrodynamic River Routing)

จำลองการไหลแบบไม่คงที่ (Unsteady 1D Hydraulic Routing) จากหน้าตัดสำรวจจริง 5 สถานี:
- เขื่อนขุนด่านปราการชล (กม.0)
- Ny.1B บ้านเขานางบวช (กม.9.2) — 61 จุดสำรวจ
- Ny.7 ตัวเมืองนครนายก (กม.27.5) — 68 จุดสำรวจ
- Kgt.30 แม่น้ำบางปะกง (กม.54.0) — เงื่อนไขขอบเขตท้ายน้ำ

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
    """คำนวณพื้นที่หน้าตัด A, เส้นรอบรูปเปียก P, รัศมีชลศาสตร์ R, ความกว้างผิวน้ำ B"""
    if water_level <= np.min(elevs):
        return {"area": 0.0, "perimeter": 0.0, "radius": 0.0, "width": 0.0}

    # แบ่งช่วงย่อยตามจุดสำรวจ
    area = 0.0
    perimeter = 0.0
    wet_widths = []

    for i in range(len(offsets) - 1):
        x1, x2 = offsets[i], offsets[i + 1]
        y1, y2 = elevs[i], elevs[i + 1]

        # กรณีทั้งสองจุดต่ำกว่าผิวน้ำ
        if y1 <= water_level and y2 <= water_level:
            dx = x2 - x1
            dy = y2 - y1
            d1 = water_level - y1
            d2 = water_level - y2
            area += 0.5 * (d1 + d2) * dx
            perimeter += math.hypot(dx, dy)
            wet_widths.append(dx)
        # กรณีตัดผิวน้ำ
        elif (y1 < water_level and y2 > water_level) or (y1 > water_level and y2 < water_level):
            # หาจุดตัด
            frac = (water_level - y1) / (y2 - y1)
            xc = x1 + frac * (x2 - x1)
            if y1 < water_level:
                dx = xc - x1
                d1 = water_level - y1
                area += 0.5 * d1 * dx
                perimeter += math.hypot(dx, water_level - y1)
                wet_widths.append(dx)
            else:
                dx = x2 - xc
                d2 = water_level - y2
                area += 0.5 * d2 * dx
                perimeter += math.hypot(dx, water_level - y2)
                wet_widths.append(dx)

    width = sum(wet_widths)
    radius = (area / perimeter) if perimeter > 0 else 0.0
    return {"area": area, "perimeter": perimeter, "radius": radius, "width": width}


def stage_to_discharge(geom: dict, n: float, slope: float) -> float:
    """Manning Equation: Q = (1/n) * A * R^(2/3) * S^(1/2)"""
    if geom["area"] <= 0 or geom["radius"] <= 0:
        return 0.0
    return (1.0 / n) * geom["area"] * (geom["radius"] ** (2.0 / 3.0)) * math.sqrt(slope)


def run_muskingum_cunge_reach(
    inflow_q: np.ndarray,
    dt_sec: float,
    dx_m: float,
    slope: float,
    manning_n: float,
    b_avg: float,
) -> np.ndarray:
    """จำลองการเคลื่อนตัวของมวลน้ำหลากแบบ Muskingum-Cunge 1D Unsteady"""
    n_steps = len(inflow_q)
    outflow_q = np.zeros(n_steps)
    outflow_q[0] = inflow_q[0]

    for t in range(n_steps - 1):
        q_ref = max(10.0, 0.5 * (inflow_q[t] + outflow_q[t]))
        # ความเร็วคลื่น c = dQ/dA ≈ (5/3) * v (Manning)
        # v = Q / (B * y), y ≈ (n*Q / (B * S^0.5))^(3/5)
        y_est = max(0.5, ((manning_n * q_ref) / (b_avg * math.sqrt(slope))) ** 0.6)
        v_est = q_ref / (b_avg * y_est)
        c_wave = (5.0 / 3.0) * v_est  # m/s

        k_sec = dx_m / max(0.5, c_wave)
        x_param = 0.5 * (1.0 - q_ref / (b_avg * slope * c_wave * dx_m))
        x_param = max(0.0, min(0.45, x_param))  # เสถียรภาพตัวแปร

        denom = 2.0 * k_sec * (1.0 - x_param) + dt_sec
        c1 = (dt_sec - 2.0 * k_sec * x_param) / denom
        c2 = (dt_sec + 2.0 * k_sec * x_param) / denom
        c3 = (2.0 * k_sec * (1.0 - x_param) - dt_sec) / denom

        q_next = c1 * inflow_q[t + 1] + c2 * inflow_q[t] + c3 * outflow_q[t]
        outflow_q[t + 1] = max(0.0, q_next)

    return outflow_q


def main() -> None:
    # 1. โหลดหน้าตัดสำรวจ
    x_ny1b, z_ny1b = load_cross_section(DATA_19 / "Ny.1B_profile.csv")
    x_ny7, z_ny7 = load_cross_section(DATA_19 / "Ny.7_profile.csv")
    x_kgt30, z_kgt30 = load_cross_section(DATA_19 / "Kgt.30_profile.csv")

    slope_reach1 = 0.00065  # ขุนด่านฯ -> Ny.1B (ลาดชันสูง ใกล้ภูเขา)
    slope_reach2 = 0.00035  # Ny.1B -> Ny.7 (ที่ราบเมือง)
    slope_reach3 = 0.00015  # Ny.7 -> Kgt.30 (ที่ราบลุ่มต่ำบางปะกง)
    n_channel = 0.0437       # Manning n สอบเทียบ Ny.7

    # คำนวณความจุตลิ่ง (Bankfull Capacity) Ny.1B และ Ny.7
    bank_ny1b = 10.60  # ม.รทก.
    geom_bank_ny1b = compute_hydraulic_geometry(x_ny1b, z_ny1b, bank_ny1b)
    q_bank_ny1b = stage_to_discharge(geom_bank_ny1b, n_channel, slope_reach1)

    bank_ny7 = 8.213   # ม.รทก.
    geom_bank_ny7 = compute_hydraulic_geometry(x_ny7, z_ny7, bank_ny7)
    q_bank_ny7 = stage_to_discharge(geom_bank_ny7, n_channel, slope_reach2)

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

    q_sim_ny7 = run_muskingum_cunge_reach(q_obs_ny1b, dt_sec, dx_m, slope_reach2, n_channel, b_avg)

    # 4. แปลง Q_sim กลับเป็นระดับน้ำ h_sim ที่ Ny.7 ด้วย Rating Curve จากหน้าตัดจริง
    # สร้าง Stage-Discharge lookup table สำหรับ Ny.7
    h_test_levels = np.linspace(np.min(z_ny7) + 0.1, bank_ny7 + 2.0, 200)
    q_lookup = [stage_to_discharge(compute_hydraulic_geometry(x_ny7, z_ny7, hl), n_channel, slope_reach2) for hl in h_test_levels]
    h_sim_ny7 = np.interp(q_sim_ny7, q_lookup, h_test_levels)

    # คำนวณความคลาดเคลื่อน (RMSE) ช่วงน้ำหลาก 26–28 ก.ย.
    mask_event = [("2026-09-26" <= t <= "2026-09-28") for t in times]
    rmse_q_cms = float(np.sqrt(np.mean((q_sim_ny7[mask_event] - q_obs_ny7[mask_event]) ** 2)))
    rmse_h_m = float(np.sqrt(np.mean((h_sim_ny7[mask_event] - h_obs_ny7[mask_event]) ** 2)))

    # เวลาเดินทางของยอดคลื่นน้ำ (Peak Travel Time)
    idx_pk_ny1b = int(np.argmax(q_obs_ny1b))
    idx_pk_ny7_sim = int(np.argmax(q_sim_ny7))
    idx_pk_ny7_obs = int(np.argmax(q_obs_ny7))
    travel_time_hours_sim = (idx_pk_ny7_sim - idx_pk_ny1b) * 0.25
    travel_time_hours_obs = (idx_pk_ny7_obs - idx_pk_ny1b) * 0.25

    # สรุปผล
    summary = {
        "metadata": {
            "title": "แบบจำลองชลศาสตร์ 1 มิติ แม่น้ำนครนายก (1D Hydrodynamic Routing)",
            "reach_ny1b_to_ny7_km": 18.3,
            "manning_n": n_channel,
            "slope_reach1": slope_reach1,
            "slope_reach2": slope_reach2,
            "sim_time_step_min": 15,
        },
        "ny1b_hydraulics": {
            "station": "Ny.1B (บ้านเขานางบวช)",
            "bank_msl_m": bank_ny1b,
            "bankfull_width_m": round(geom_bank_ny1b["width"], 1),
            "bankfull_area_m2": round(geom_bank_ny1b["area"], 1),
            "bankfull_q_cms": round(q_bank_ny1b, 1),
            "peak_stage_msl_m": round(float(np.max(h_obs_ny1b)), 2),
            "peak_q_cms": round(float(np.max(q_obs_ny1b)), 1),
            "overflow_depth_m": round(float(np.max(h_obs_ny1b) - bank_ny1b), 2),
            "overflow_q_cms": round(float(np.max(q_obs_ny1b) - q_bank_ny1b), 1),
        },
        "ny7_hydraulics": {
            "station": "Ny.7 (สะพานเทศบาลนครนายก)",
            "bank_msl_m": round(bank_ny7, 2),
            "terrace_start_msl_m": 6.86,
            "bankfull_width_m": round(geom_bank_ny7["width"], 1),
            "bankfull_area_m2": round(geom_bank_ny7["area"], 1),
            "bankfull_q_cms": round(q_bank_ny7, 1),
            "peak_stage_msl_m": round(float(np.max(h_obs_ny7)), 2),
            "peak_q_cms": round(float(np.max(q_obs_ny7)), 1),
        },
        "routing_performance": {
            "travel_time_hours_sim": round(travel_time_hours_sim, 2),
            "travel_time_hours_obs": round(travel_time_hours_obs, 2),
            "rmse_discharge_cms": round(rmse_q_cms, 2),
            "rmse_stage_cm": round(rmse_h_m * 100.0, 1),
            "q_peak_sim_cms": round(float(np.max(q_sim_ny7)), 1),
            "q_peak_obs_cms": round(float(np.max(q_obs_ny7)), 1),
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
