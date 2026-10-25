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
OUT_PNG_ANCH = ROOT / "report" / "assets" / "compound_flood_risk_matrix_anchored.png"
C1 = 0.132       # สัมประสิทธิ์เดิม ไม่แตะต้อง (ยังไม่สอบเทียบหลายปี)
EXP = 1.28

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
    head_loss = C1 * ((q_bangsai / 1000.0) ** EXP)
    stage = tide_msl + wave_setup_m + head_loss
    return round(float(stage), 2)


def risk_of(st: float) -> str:
    """เกณฑ์ระดับความเสี่ยงที่ C.12 (เท่ากับที่ใช้ในเมทริกซ์เดิม)"""
    return "normal" if st < 2.00 else "watch" if st < 2.40 else "warning" if st < 2.70 else "critical"


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
            "event": "มหาอุทกภัยปี 2554 (จุดสูงสุด ต.ค. 54) — ข้อมูลนำเข้าเป็นค่าประมาณ ไม่มีแหล่งอ้างอิง ระดับน้ำในตารางเป็นผลสมการ",
            "q_bangsai_m3s": 3750,
            "tide_msl_m": 2.35,
            "c12_stage_msl_m": calculate_c12_stage(3750, 2.35),
            "status": "น้ำล้นคันกั้นน้ำหลายจุด ท่วมกรุงเทพฯ ฝั่งตะวันตกและเหนือ",
        },
        {
            "event": "ระลอกปลาย ก.ย. 2569 (เหตุการณ์จริง · ระดับน้ำในตารางเป็นผลสมการ ค่าโทรมาตรจริง 2.24 ม.)",
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

    # รีวิวรอบ 6 (C1): ความไวต่ออัตราส่งผ่านน้ำหนุนที่วัดได้ (analysis/goal6_tide_gain_regression.py)
    # ยึดกับระดับ C.12 ที่วัดจริง (ไม่ใช้สมการ) แล้วบวกส่วนต่างน้ำหนุน × อัตราส่งผ่าน
    tide_gain_evidence = None
    _tg = ROOT / "analysis/goal6/tide_gain_regression.json"
    if _tg.exists():
        _g = json.loads(_tg.read_text(encoding="utf-8"))
        _gs = [_g["headline"]["gain"], _g["tidal_band_pre_event"]["gain"], _g["tidal_band_event"]["gain"]]
        _obs_stage = 2.24   # ค่าโทรมาตรจริงสูงสุด C.12 (ต.ค. 2569) ในช่วงข้อมูลชุดเดียวกัน
        _obs_tide = historical_benchmarks[1]["tide_msl_m"]
        _t_hyp = historical_benchmarks[2]["tide_msl_m"]
        tide_gain_evidence = {
            "source": "analysis/goal6/tide_gain_regression.json",
            "gain_headline": _g["headline"]["gain"],
            "gain_ci95": _g["headline"]["gain_ci95"],
            "gain_range_across_periods": [round(min(_gs), 3), round(max(_gs), 3)],
            "formula_gain": 1.0,
            "anchor_observed_stage_m": _obs_stage,
            "scenario_tide_msl_m": _t_hyp,
            "stage_if_measured_gain_m": {
                "low": round(_obs_stage + min(_gs) * (_t_hyp - _obs_tide), 2),
                "high": round(_obs_stage + max(_gs) * (_t_hyp - _obs_tide), 2),
            },
            "stage_formula_gain_m": historical_benchmarks[2]["c12_stage_msl_m"],
            "note": "ยึดระดับที่วัดจริง 2.24 ม. แล้วเพิ่มตามส่วนต่างน้ำหนุน × อัตราส่งผ่านที่วัดได้ — เป็นความไว ไม่ใช่การพยากรณ์ · ฤดูเดียว",
        }

    # R7-26 (กติกา docs/COMPOUND_ANCHORED_PREREG.md ตั้งก่อนดูผล): แบบยึดค่าที่วัด + อัตราส่งผ่านน้ำหนุนที่วัดได้ — วางเทียบแบบเดิม ไม่แทน
    matrix_anchored = None
    if tide_gain_evidence:
        g_c = tide_gain_evidence["gain_headline"]
        g_lo, g_hi = tide_gain_evidence["gain_range_across_periods"]
        bm0 = historical_benchmarks[1]
        h0, t0, q0 = tide_gain_evidence["anchor_observed_stage_m"], bm0["tide_msl_m"], bm0["q_bangsai_m3s"]
        r0 = (q0 / 1000.0) ** EXP

        def anch(q, tt, g):
            return round(h0 + g * (tt - t0) + C1 * (((q / 1000.0) ** EXP) - r0), 2)
        grid, counts = [], {"original": {}, "anchored_central": {}, "anchored_gain_low": {}, "anchored_gain_high": {}}
        changed, diffs = 0, []
        for i, tt in enumerate(tide_range):
            row = []
            for j, q in enumerate(q_range):
                sc, sl, sh = anch(q, tt, g_c), anch(q, tt, g_lo), anch(q, tt, g_hi)
                orig = matrix[i][j]
                rk = risk_of(sc)
                row.append({"q_bangsai_m3s": int(q), "tide_msl_m": round(float(tt), 2), "c12_stage_msl_m": sc, "stage_gain_low_m": sl, "stage_gain_high_m": sh, "risk_level": rk})
                for key, lv in (("original", orig["risk_level"]), ("anchored_central", rk), ("anchored_gain_low", risk_of(sl)), ("anchored_gain_high", risk_of(sh))):
                    counts[key][lv] = counts[key].get(lv, 0) + 1
                changed += int(rk != orig["risk_level"])
                diffs.append(round(sc - orig["c12_stage_msl_m"], 2))
            grid.append(row)
        matrix_anchored = {
            "rule": "docs/COMPOUND_ANCHORED_PREREG.md (ตั้งก่อนดูผล 26 ต.ค. 69)",
            "formula": "H = H_วัด + g × (น้ำหนุน − น้ำหนุน_วัด) + c1 × [(Q/1000)^1.28 − (Q_วัด/1000)^1.28]",
            "anchor": {"stage_msl_m": h0, "tide_msl_m": t0, "q_bangsai_m3s": q0},
            "gain": {"central": g_c, "low": g_lo, "high": g_hi},
            "n_cells": len(q_range) * len(tide_range),
            "band_counts": counts,
            "cells_changed_band_vs_original": changed,
            "stage_diff_vs_original_m": {"min": min(diffs), "max": max(diffs)},
            "grid": grid,
        }

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
                "สมการบวกกันตรง ๆ: ∂H_C12/∂H_tide = 1.0 ทุกสภาวะ (ข้อมูลฤดู 2569 ถดถอยได้ต่ำกว่า 1 ดู tide_gain_evidence) และไม่มีพจน์ปฏิสัมพันธ์ Q×tide "
                "→ ยังไม่จำลองการหนุนกลับแบบไม่เชิงเส้นจริง (ผลของน้ำหลากกับน้ำทะเลแยกกันบวก ไม่ใช่ทบกัน)",
                "ไม่มีคลื่นลมจริง: wave_setup คงที่ 0.08 ม. ทุกช่วงเวลา (ไม่ผสานคลื่น SWAN เป็นตัวแปร)",
                "อินพุตปี 2554 (Q=3,750 ม³/วิ · Tide=+2.35 ม.) เป็นค่าประมาณ ไม่มีแหล่งอ้างอิงใน repo",
                "อินพุตปี 2569 (Q=2,250 ม³/วิ · Tide=+1.91 ม.) เป็นค่าประมาณจากบริบทเหตุการณ์ — Q ซ้ำกับค่าที่ใช้ในแบบจำลองคลองเจ้าพระยา 2 (ที่มาของ Q นี้ยังไม่มีบันทึกอ้างอิงในโครงการ) และยังไม่ขึ้นทะเบียน canonical (F-08)",
            ],
        },
        "historical_benchmarks": historical_benchmarks,
        "tide_gain_evidence": tide_gain_evidence,
        "matrix_anchored": matrix_anchored,
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
    marker_labels = ["2554 (ประมาณ)", "2569 (จริง)", "2569 + น้ำเกิดสูงสุด", "2569 + คลองเจ้าพระยา 2"]
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

    if matrix_anchored:
        ag = np.array([[c["c12_stage_msl_m"] for c in row] for row in matrix_anchored["grid"]])
        fig2, ax2 = plt.subplots(figsize=(10, 7), dpi=200)
        ax2.contourf(q_range, tide_range, ag, levels=[1.0, 2.0, 2.4, 2.7, 3.4], colors=colors, alpha=1.0)
        ln2 = ax2.contour(q_range, tide_range, ag, levels=[2.0, 2.4, 2.7, 2.8], colors="black", linewidths=1.2)
        ax2.clabel(ln2, inline=True, fontsize=10, fmt="%.2f ม.")
        a = matrix_anchored["anchor"]
        ax2.scatter(a["q_bangsai_m3s"], a["tide_msl_m"], color="blue", marker="o", s=120, edgecolors="white", linewidths=1.5, zorder=5)
        ax2.annotate(f"จุดยึด 2569 (วัดจริง {a['stage_msl_m']:.2f} ม.)", (a["q_bangsai_m3s"] + 50, a["tide_msl_m"] - 0.02), fontsize=9, fontweight="bold",
                     color="black", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="blue", alpha=0.9))
        ax2.set_title("เมทริกซ์แบบยึดค่าที่วัดจริงและอัตราส่งผ่านน้ำหนุนที่วัดได้ (สถานี C.12 สามเสน กทม.)", fontsize=12, fontweight="bold", pad=12)
        ax2.set_xlabel("อัตราการไหลของน้ำเหนือหลากที่จุดบรรจบบางไทร (ลบ.ม./วินาที)", fontsize=11, labelpad=8)
        ax2.set_ylabel("ระดับน้ำทะเลหนุนปากแม่น้ำเจ้าพระยา (ม.รทก.)", fontsize=11, labelpad=8)
        ax2.legend(custom_handles, risk_labels, loc="upper left", framealpha=0.95, title="ระดับความเสี่ยงที่ C.12", fontsize=9)
        ax2.grid(True, linestyle="--", alpha=0.4)
        fig2.tight_layout()
        fig2.savefig(OUT_PNG_ANCH)
        plt.close(fig2)
        print(f"✅ บันทึกแผนภาพเมทริกซ์แบบยึดค่าที่วัด: {OUT_PNG_ANCH}")


if __name__ == "__main__":
    main()
