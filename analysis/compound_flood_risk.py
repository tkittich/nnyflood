#!/usr/bin/env python3
"""analysis/compound_flood_risk.py — แบบจำลองเมทริกซ์ประเมินความเสี่ยงน้ำเหนือหลากปะทะน้ำทะเลหนุน (Compound Flood Risk)

หลักการ:
    วิเคราะห์ปฏิสัมพันธ์ระหว่างสองแรงขับเคลื่อนหลัก (Compound Inundation Drivers) ในลุ่มน้ำเจ้าพระยาตอนล่าง:
    1. ปริมาณน้ำเหนือหลากจากแม่น้ำเจ้าพระยาและป่าสัก (C.13 + S.26 บรรจบที่บางไทร C.29A: 1,500–4,000 ลบ.ม./วินาที)
    2. อิทธิพลขอบเขตทะเลหนุนปากแม่น้ำ (สถานี CPY015 สะพานกรุงเทพ + ปากอ่าวไทย: +1.40 ถึง +2.50 ม.รทก.)
       ผสานแรงต้านคลื่นลมทะเลอ่าวไทยเป็นค่าคงที่ +0.08 ม. (wave setup — ยังไม่ผสานคลื่น SWAN เป็นตัวแปร;
       ข้อมูลคลื่นที่มีเป็นค่าเดียวหลังช่วงทดสอบ ใช้เป็นตัวแปรไม่ได้ — เป็นข้อจำกัดที่เปิดเผยใน metadata)

ผลลัพธ์:
    - analysis/compound_flood_risk_summary.json (ตารางเมทริกซ์และเกณฑ์เตือนภัย)
    - report/assets/compound_flood_risk_matrix.png (แผนภาพความเสี่ยง 2 มิติ)
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "analysis" / "compound_flood_risk_summary.json"
OUT_PNG = ROOT / "report" / "assets" / "compound_flood_risk_matrix.png"

# ตั้งค่าฟอนต์ภาษาไทยตามกติกาของโปรเจกต์
plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]


def calculate_c12_stage(q_bangsai: float, tide_msl: float, wave_setup_m: float = 0.08) -> float:
    """คำนวณระดับน้ำจำลองที่สถานี C.12 สามเสน (ม.รทก.)

    อิงสมการชลศาสตร์ Backwater Curve และผลการสอบเทียบกับข้อมูลโทรมาตรจริง:
    H_C12 = H_tide + wave_setup + c1 * (Q / 1000)^1.28

    สถานะการสอบเทียบ (ตรวจ 17 ต.ค. 69): **ยังไม่สอบเทียบหลายปี** — ไม่มีสคริปต์สอบเทียบ
    และไม่มี artifact ของการ fit ใน repo · c1 และเลขชี้กำลังเป็นค่าประมาณที่ตั้งให้ผ่าน
    จุดตรวจ 2 จุด (2,500 -> ~2.51 · 3,500 -> ~3.04) ซึ่งเป็น "การตรวจความเป็นไปได้"
    ไม่ใช่การถดถอยจากอนุกรมเวลา · ห้ามอ้างว่าสอบเทียบจากปี 2554/2564/2565 จนกว่าจะมี
    `analysis/compound_flood_risk_calibration.py` + artifact
    """
    # จุดตรวจความเป็นไปได้ (ไม่ใช่ชุดสอบเทียบ):
    # เมื่อ Q=2,500 และ Tide=+2.00 ม. -> H_C12 ≈ +2.51 ม.
    # เมื่อ Q=3,500 และ Tide=+2.30 ม. -> H_C12 ≈ +3.04 ม. (เข้าสู่ระดับวิกฤต)
    c1 = 0.132
    head_loss = c1 * ((q_bangsai / 1000.0) ** 1.28)
    stage = tide_msl + wave_setup_m + head_loss
    return round(float(stage), 2)


def main():
    print("=" * 72)
    print("  การประเมินความเสี่ยงน้ำเหนือหลากปะทะน้ำทะเลหนุน (Compound Flood Risk Matrix)")
    print("=" * 72)

    # ช่วงของตัวแปรนำเข้า
    q_range = np.arange(1500, 4250, 250)      # อัตราน้ำหลากบางไทร (ลบ.ม./วินาที)
    tide_range = np.arange(1.40, 2.55, 0.10)  # ระดับน้ำทะเลหนุนปากอ่าว (ม.รทก.)

    matrix = []
    matrix_grid = np.zeros((len(tide_range), len(q_range)))

    for i, t in enumerate(tide_range):
        row = []
        for j, q in enumerate(q_range):
            st = calculate_c12_stage(q, t)
            matrix_grid[i, j] = st
            # จำแนกระดับความเสี่ยง
            # เขียว: ปกติ (< 2.00 ม.)
            # เหลือง: เฝ้าระวัง (2.00 - 2.40 ม.)
            # ส้ม: เตือนภัยเสี่ยงท่วมชุมชนนอกคัน (2.40 - 2.70 ม.)
            # แดง: วิกฤตล้นคันกั้นน้ำ กทม. (> 2.70 ม. สันคันเฉลี่ย 2.80–3.00 ม.)
            if st < 2.00:
                risk = "normal"
            elif st < 2.40:
                risk = "watch"
            elif st < 2.70:
                risk = "warning"
            else:
                risk = "critical"

            row.append({
                "q_bangsai_m3s": int(q),
                "tide_msl_m": round(float(t), 2),
                "c12_stage_msl_m": st,
                "risk_level": risk,
            })
        matrix.append(row)

    # เหตุการณ์สำคัญในประวัติศาสตร์
    historical_benchmarks = [
        {
            "event": "มหาอุทกภัยปี 2554 (จุดสูงสุด ต.ค. 54)",
            "q_bangsai_m3s": 3750,
            "tide_msl_m": 2.35,
            "c12_stage_msl_m": calculate_c12_stage(3750, 2.35),
            "status": "น้ำล้นคันกั้นน้ำหลายจุด ท่วมกรุงเทพฯ ฝั่งตะวันตกและเหนือ",
        },
        {
            "event": "ระลอกปลาย ก.ย. 2569 (เหตุการณ์จริง)",
            "q_bangsai_m3s": 2250,
            "tide_msl_m": 1.91,
            "c12_stage_msl_m": calculate_c12_stage(2250, 1.91),
            "status": "ระดับน้ำสูงสุด 2.36 ม. อยู่ในเกณฑ์เฝ้าระวัง (สูงกว่าค่าโทรมาตรจริง 2.24 ม. อยู่ 12 ซม. = 5% อยู่ในเกณฑ์เดียวกัน; ท่วมเฉพาะชุมชนนอกแนวคันกั้นน้ำ)",
        },
        {
            "event": "กรณีสมมติ: ระลอก 2569 หากเกิดน้ำทะเลหนุนสูงสุด (+2.40 ม.)",
            "q_bangsai_m3s": 2250,
            "tide_msl_m": 2.40,
            "c12_stage_msl_m": calculate_c12_stage(2250, 2.40),
            "status": "เข้าสู่ระดับวิกฤตล้นคันกั้นน้ำ (2.85 ม. เกินคันกั้นน้ำ 2.80 ม.) ต้องเสริมแนวกระสอบทรายทันที",
        },
        {
            "event": "กรณีสมมติ: ผันน้ำด้วยคลองเจ้าพระยา 2 (-600 ลบ.ม./วิ)",
            "q_bangsai_m3s": 1650,
            "tide_msl_m": 2.40,
            "c12_stage_msl_m": calculate_c12_stage(1650, 2.40),
            "status": "ลดระดับน้ำลงเหลือ 2.73 ม. (ต่ำกว่าสันคันกั้นน้ำ 2.80 ม. แต่ยังอยู่ในเกณฑ์วิกฤตที่ต้องเฝ้าระวังใกล้ชิด)",
        },
    ]

    summary_data = {
        "metadata": {
            "title": "เมทริกซ์ประเมินความเสี่ยงน้ำเหนือหลากปะทะน้ำทะเลหนุน (Compound Flood Risk Matrix)",
            "target_location": "แม่น้ำเจ้าพระยาตอนล่าง (สถานี C.12 สามเสน กรุงเทพมหานคร)",
            "floodwall_crest_msl_m": 2.80,
            "watch_threshold_msl_m": 2.00,
            "warning_threshold_msl_m": 2.40,
            "critical_threshold_msl_m": 2.70,
            "calibration_status": "ยังไม่สอบเทียบหลายปี — ค่าสัมประสิทธิ์เป็นการตรวจความเป็นไปได้จาก 2 จุด (ดู docstring)",
            "limitations": [
                "สมการบวกกันตรง ๆ: ∂H_C12/∂H_tide = 1.0 ทุกสภาวะ และไม่มีพจน์ปฏิสัมพันธ์ Q×tide "
                "→ ยังไม่จำลองการหนุนกลับแบบไม่เชิงเส้นจริง (ผลของน้ำหลากกับน้ำทะเลแยกกันบวก ไม่ใช่ทบกัน)",
                "ไม่มีคลื่นลมจริง: wave_setup คงที่ 0.08 ม. ทุกช่วงเวลา (ไม่ผสานคลื่น SWAN เป็นตัวแปร)",
                "อินพุตปี 2554 (Q=3,750 ม³/วิ · Tide=+2.35 ม.) เป็นค่าประมาณ ไม่มีแหล่งอ้างอิงใน repo",
                "อินพุตปี 2569 (Q=2,250 ม³/วิ · Tide=+1.91 ม.) เป็นค่าประมาณจากบริบทเหตุการณ์ — Q ซ้ำกับค่าที่ใช้ในแบบจำลองคลองเจ้าพระยา 2 (ดูช่องว่าง cp2_q_bangsai_2250) และยังไม่ขึ้นทะเบียน canonical (F-08)",
            ],
        },
        "historical_benchmarks": historical_benchmarks,
        "risk_levels_definition": {
            "normal": "ระดับน้ำปลอดภัย (< 2.00 ม.รทก.) การระบายน้ำในท่อเป็นปกติ",
            "watch": "ระดับเฝ้าระวัง (2.00–2.40 ม.รทก.) น้ำเริ่มดันปากท่อระบายน้ำ กทม. ต้องเดินเครื่องสูบ",
            "warning": "ระดับเตือนภัย (2.40–2.70 ม.รทก.) น้ำท่วมชุมชนนอกแนวคันกั้นน้ำ ท่าเรือ ทางเดินริมน้ำ",
            "critical": "ระดับวิกฤต (> 2.70 ม.รทก.) เสี่ยงน้ำล้นสันคันกั้นน้ำ กทม. (2.80–3.00 ม.) และเกิดแนวกระสอบทรายรั่วซึม",
        },
        "matrix_grid": matrix,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกสรุปตัวเลขเมทริกซ์เรียบร้อยแล้ว: {OUT_JSON}")

    # วาดแผนภาพ 2 มิติ (Contour + Heatmap)
    fig, ax = plt.subplots(figsize=(10, 7), dpi=200)

    # ระดับสี: เลือกให้แต่ละแถบผ่านเกณฑ์ WCAG ≥3:1 บนพื้นขาว (เดิม #2ecc71/#f1c40f/#e67e22/#e74c3c
    # ที่ α=0.85 รวมกับพื้นแล้วต่ำกว่าเกณฑ์ — SB F-11) และใช้สีทึบ (alpha=1) เพราะสีคือรหัสความเสี่ยง
    colors = ["#1b7f3b", "#8a6d00", "#b34700", "#a12020"]

    # วาด contourf
    c = ax.contourf(
        q_range, tide_range, matrix_grid,
        levels=[1.4, 2.0, 2.4, 2.7, 3.4],
        colors=colors, alpha=1.0
    )

    # วาดเส้น contour line
    lines = ax.contour(q_range, tide_range, matrix_grid, levels=[2.0, 2.4, 2.7, 2.8], colors="black", linewidths=1.2)
    ax.clabel(lines, inline=True, fontsize=10, fmt="%.2f ม.")

    # พล็อตจุดเปรียบเทียบประวัติศาสตร์
    # ต้องมาจาก historical_benchmarks ตัวเดียวกันกับ JSON เท่านั้น (กันภาพกับตารางไม่ตรงกัน)
    marker_labels = ["2554 (จริง)", "2569 (จริง)", "2569 + น้ำเกิดสูงสุด", "2569 + คลองเจ้าพระยา 2"]
    marker_style = [("red", "s"), ("blue", "o"), ("darkred", "^"), ("green", "D")]
    markers = []
    for bm, label, (col, sym) in zip(historical_benchmarks, marker_labels, marker_style):
        st = calculate_c12_stage(bm["q_bangsai_m3s"], bm["tide_msl_m"])
        assert abs(st - bm["c12_stage_msl_m"]) < 0.005, (
            f"จุดบนภาพ '{label}' ({st} ม.) ไม่ตรงกับตาราง JSON ({bm['c12_stage_msl_m']} ม.)"
        )
        markers.append((label, bm["q_bangsai_m3s"], bm["tide_msl_m"], col, sym, st))

    for label, q, t, col, sym, st in markers:
        ax.scatter(q, t, color=col, marker=sym, s=120, edgecolors="white", linewidths=1.5, zorder=5)
        ax.annotate(f"{label}\n({st:.2f} ม.)", (q + 50, t - 0.02), fontsize=9, fontweight="bold",
                    color="black", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=col, alpha=0.9))

    ax.set_title("เมทริกซ์ประเมินความเสี่ยงน้ำเหนือหลากปะทะน้ำทะเลหนุน (สถานี C.12 สามเสน กทม.)", fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel("อัตราการไหลของน้ำเหนือหลากที่จุดบรรจบบางไทร (ลบ.ม./วินาที)", fontsize=11, labelpad=8)
    ax.set_ylabel("ระดับน้ำทะเลหนุนปากแม่น้ำเจ้าพระยา (ม.รทก.)", fontsize=11, labelpad=8)

    # เพิ่มคำอธิบายระดับความเสี่ยง
    risk_labels = [
        "ปลอดภัย (< 2.00 ม.)",
        "เฝ้าระวัง (2.00–2.40 ม.)",
        "เตือนภัยนอกคัน (2.40–2.70 ม.)",
        "วิกฤตล้นคัน กทม. (> 2.70 ม.)"
    ]
    custom_handles = [plt.Rectangle((0, 0), 1, 1, color=col) for col in colors]
    ax.legend(custom_handles, risk_labels, loc="upper left", framealpha=0.95, title="ระดับความเสี่ยงที่ C.12", fontsize=9)

    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG)
    plt.close(fig)
    print(f"✅ บันทึกแผนภาพเมทริกซ์ความเสี่ยงเรียบร้อยแล้ว: {OUT_PNG}")


if __name__ == "__main__":
    main()
