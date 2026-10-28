#!/usr/bin/env python3
"""analysis/goal7_acid_sulfate_soil_analysis.py — การประเมินปริมาณดินกรดกำมะถันและไพไรต์ตามแนวขุดคลองเจ้าพระยา 2

วิเคราะห์เชิงปริมาณ:
1. การกระจายตัวของชุดดินกรดกำมะถัน (ชุดดินองครักษ์ Ok, รังสิต Rs, บางน้ำเปรี้ยว Bp)
2. ปริมาณดินขุดผ่านชั้นไพไรต์ (Pyrite FeS2) และศักย์การเกิดกรดกำมะถัน (Potential Sulfuric Acid Generation)
3. ปริมาณปูนขาว/ปูนมาร์ล (CaCO3) ที่ต้องใช้ปรับสภาพและต้นทุนการบำบัด
4. มาตรการควบคุมสิ่งแวดล้อมทางวิศวกรรม (Submergence Capping, Neutralization Ponds)

ช่องว่างที่เกี่ยวข้อง (ยังเปิด — สคริปต์นี้ให้เพียงสถานการณ์สมมติ ไม่ใช่ผลวัด):
- acid_sulfur_content: ปริมาณกำมะถัน/ศักย์กรดของชั้นดินที่จะขุด
- acid_measures: มาตรการจัดการดินกรดกำมะถันระหว่างขุด กองดิน และการใช้ดินถม

รัน: python analysis/goal7_acid_sulfate_soil_analysis.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_FILE = ROOT / "analysis/goal7/canonical.json"
GAPS_FILE = ROOT / "analysis/goal7/gaps.json"
OUT_JSON = ROOT / "analysis/goal7/acid_sulfate_soil_summary.json"


def analyze_acid_sulfate_soils():
    # โหลด canonical
    canonical = {}
    if CANONICAL_FILE.exists():
        canonical = json.loads(CANONICAL_FILE.read_text(encoding="utf-8"))

    as_data = canonical.get("acid_soil", {})

    # การกระจายตัวเชิงพื้นที่
    distribution = {
        "ok_canal_rai": as_data.get("ok_rai_canal", 1768),
        "ok_500m_buffer_rai": as_data.get("ok_500m_rai", 8322),
        "total_acid_soil_rai": as_data.get("acid_rai_all", 8089),
        "total_alignment_soil_rai": as_data.get("soil_rai_all", 14964),
        "acid_share_pct": as_data.get("acid_share_all", 54.1),
        "km_spans": {
            "km23_110": {
                "acid_pct": as_data.get("acid_share_km23_110", 67.0),
                "dominant_series": ["Ok (องครักษ์)", "Rs (รังสิต)", "Bp (บางน้ำเปรี้ยว)"],
            },
            "km110_135": {
                "acid_pct": as_data.get("acid_share_km110_135", 48.3),
                "dominant_series": ["Bp (บางน้ำเปรี้ยว)", "Bk (บางกอก)"],
            },
        },
    }

    # ปริมาตรดินขุดและการเกิดกรด
    excavation_mcm_design = as_data.get("excavation_acid_mcm", {}).get("design", 16.1)
    excavation_mcm_deep = as_data.get("excavation_acid_mcm", {}).get("deep", 72.5)

    bulk_density = as_data.get("assumptions", {}).get("bulk_density_t_m3", 1.4)
    caco3_factor = as_data.get("assumptions", {}).get("caco3_kg_per_t_per_pct_s", 31.25)
    safety_factor = as_data.get("assumptions", {}).get("safety", 1.5)

    scenarios = {}
    for s_pct in [0.2, 0.5, 1.0]:
        mass_t_design = excavation_mcm_design * 1e6 * bulk_density
        mass_t_deep = excavation_mcm_deep * 1e6 * bulk_density

        caco3_req_t_design = (mass_t_design * s_pct * caco3_factor * safety_factor) / 1000.0
        caco3_req_t_deep = (mass_t_deep * s_pct * caco3_factor * safety_factor) / 1000.0

        scenarios[f"s_{s_pct}pct"] = {
            "sulfur_pct": s_pct,
            "design_cut": {
                "volume_mcm": excavation_mcm_design,
                "lime_caco3_mt": round(caco3_req_t_design / 1e6, 2),
                "cost_mb_min": round((caco3_req_t_design * 1000) / 1e6, 1),
                "cost_mb_max": round((caco3_req_t_design * 1500) / 1e6, 1),
            },
            "deep_cut": {
                "volume_mcm": excavation_mcm_deep,
                "lime_caco3_mt": round(caco3_req_t_deep / 1e6, 2),
                "cost_mb_min": round((caco3_req_t_deep * 1000) / 1e6, 1),
                "cost_mb_max": round((caco3_req_t_deep * 1500) / 1e6, 1),
            },
        }

    summary = {
        "title": "ตารางปูนปรับสภาพดินกรดกำมะถันตามสถานการณ์สมมติ โครงการคลองเจ้าพระยา 2 (ซ้ำกับคีย์ acid_soil ที่รายงานใช้อยู่)",
        "status": "superseded_by_acid_soil",
        "note": "ค่ากำมะถันร้อยละ 0.2/0.5/1.0 เป็นสถานการณ์สมมติ ไม่ใช่ค่าที่วัด · ราคาปูนไม่มีแหล่งอ้างอิง · ผลที่เผยแพร่ในรายงานอยู่ที่คีย์ acid_soil (blocks.tbl_acid_soil) — ไฟล์นี้เก็บไว้เพื่อตรวจย้อนเท่านั้น",
        "spatial_distribution": distribution,
        "stoichiometric_scenarios": scenarios,
        "analyst_proposals_unpublished": "แนวปฏิบัติทั่วไปที่ผู้วิเคราะห์ร่างไว้ (ปิดคลุมด้วยน้ำ · วางดินเปรี้ยวเป็นแกนคันดิน · บ่อพักปรับสภาพน้ำ · ตรวจวัด pH) ตัวเลขเฉพาะ เช่น ระยะบ่อพักและอัตราปูนมาร์ล ไม่มีแหล่งอ้างอิง จึงไม่ลงรายงานและไม่ถือเป็นมาตรการของโครงการ",
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกสรุปการประเมินดินกรดกำมะถันลง {OUT_JSON.name}")

    # อัปเดตลง canonical.json
    if CANONICAL_FILE.exists():
        cdata = json.loads(CANONICAL_FILE.read_text(encoding="utf-8"))
        cdata["acid_sulfate_soil_assessment"] = summary
        CANONICAL_FILE.write_text(json.dumps(cdata, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"✅ อัปเดต canonical.json เรียบร้อย")

    # ไม่ปิดช่องว่าง acid_sulfur_content / acid_measures: ยังไม่มีผลวัดกำมะถันและไม่มีมาตรการของโครงการ (28 ต.ค. 69)
    if GAPS_FILE.exists():
        gdata = json.loads(GAPS_FILE.read_text(encoding="utf-8"))
        for gap in gdata.get("gaps", []):
            if gap["id"] in ("acid_sulfur_content", "acid_measures"):
                gap["status"] = "open"
                gap.pop("evidence", None)
        with open(GAPS_FILE, "w", encoding="utf-8", newline=chr(10)) as f:
            json.dump(gdata, f, ensure_ascii=False, indent=2)
        print("✅ คง acid_sulfur_content และ acid_measures เป็นช่องว่างที่เปิดอยู่ ใน gaps.json")

    return summary


if __name__ == "__main__":
    analyze_acid_sulfate_soils()
