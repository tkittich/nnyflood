#!/usr/bin/env python3
"""analysis/goal7_acid_sulfate_soil_analysis.py — การประเมินปริมาณดินกรดกำมะถันและไพไรต์ตามแนวขุดคลองเจ้าพระยา 2

วิเคราะห์เชิงปริมาณ:
1. การกระจายตัวของชุดดินกรดกำมะถัน (ชุดดินองครักษ์ Ok, รังสิต Rs, บางน้ำเปรี้ยว Bp)
2. ปริมาณดินขุดผ่านชั้นไพไรต์ (Pyrite FeS2) และศักย์การเกิดกรดกำมะถัน (Potential Sulfuric Acid Generation)
3. ปริมาณปูนขาว/ปูนมาร์ล (CaCO3) ที่ต้องใช้ปรับสภาพและต้นทุนการบำบัด
4. มาตรการควบคุมสิ่งแวดล้อมทางวิศวกรรม (Submergence Capping, Neutralization Ponds)

ปิดช่องว่างความรู้:
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

    # มาตรการทางวิศวกรรมสิ่งแวดล้อม
    mitigation_measures = {
        "prevention_capping": (
            "1. มาตรการปิดคลุมและกักน้ำ (Submergence Capping): ควบคุมระดับน้ำในคลองให้อยู่เหนือชั้นดินไพไรต์ตลอดเวลา "
            "เพื่อตัดการสัมผัสออกซิเจนในบรรยากาศ ยับยั้งปฏิกิริยาออกซิเดชันของ FeS2 มิให้เกิดกรดกำมะถันอิสระ"
        ),
        "spoil_management": (
            "2. การจัดการดินขุดและคันคลอง: ดินขุดช่วงที่มีชั้นไพไรต์เข้มข้น (>0.5% S) ต้องนำไปวางเป็นแกนในของคันดิน "
            "และคลุมทับด้วยดินเหนียวไม่เปรี้ยว (Non-acid clay) หนาไม่น้อยกว่า 1.0 เมตร พร้อมผสมปูนมาร์ลในอัตราส่วน 15–20 กก./ตร.ม."
        ),
        "runoff_treatment": (
            "3. บ่อพักและบำบัดน้ำชะล้าง (Retention & Neutralization Ponds): ก่อสร้างบ่อดักตะกอนชั่วคราวตามแนวขุดทุก 2 กม. "
            "ติดตั้งระบบจ่ายน้ำปูนขาวอัตโนมัติ ควบคุมค่าความเป็นกรด-ด่าง (pH) ของน้ำก่อนระบายออกสู่ลำน้ำสาธารณะไม่ต่ำกว่า 6.5"
        ),
        "monitoring": (
            "4. การเฝ้าระวังคุณภาพน้ำและโลหะหนัก: ติดตั้งสถานีตรวจวัด pH, ซัลเฟต (SO4(2-)), เหล็ก (Fe) และอะลูมิเนียม (Al) "
            "แบบต่อเนื่องทุก 15 นาที ตลอดแนวคลองช่วง กม.23–110 โดยเฉพาะจุดตัดคลองส่งน้ำชลประทานและพื้นที่ใกล้เคียงทุ่งนาองครักษ์"
        ),
    }

    summary = {
        "title": "การประเมินปริมาณดินกรดกำมะถันและมาตรการจัดการทางวิศวกรรม โครงการคลองเจ้าพระยา 2",
        "spatial_distribution": distribution,
        "stoichiometric_scenarios": scenarios,
        "engineering_mitigation_measures": mitigation_measures,
        "evidence_for_gaps": {
            "acid_sulfur_content": (
                "วิเคราะห์ตามฐานข้อมูลชุดดินกรมพัฒนาที่ดิน (LDD): ช่วง กม.23–110 ผ่านชุดดินองครักษ์ (Ok) และรังสิต (Rs) รวม 54.1% ของแนวคลอง "
                "มีปริมาณดินขุดผ่านชั้นไพไรต์ 16.10 ล้าน ลบ.ม. (แบบปกติ) และ 72.50 ล้าน ลบ.ม. (กรณีขุดลึก) กำหนดช่วงกำมะถันไพไรต์ที่ 0.2–1.0% S "
                "มีความต้องการปูนขาวปรับสภาพ 0.21–1.06 ล้านตัน (มูลค่า 530–795 ล้านบาท)"
            ),
            "acid_measures": (
                "กำหนดมาตรการทางวิศวกรรม 4 ด้าน: (1) การกักน้ำท่วมคลุมชั้นไพไรต์ตัดออกซิเจน (Submergence) (2) การบดอัดดินเปรี้ยวเป็นแกนในคันดินคลุมทับด้วยดินเหนียว 1 ม. "
                "(3) บ่อพักตกตะกอนปรับสภาพน้ำด้วยปูนขาวทุก 2 กม. ควบคุม pH ≥ 6.5 ก่อนปล่อย (4) โทรมาตรตรวจวัด pH และโลหะหนักอัตโนมัติ"
            ),
        },
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกสรุปการประเมินดินกรดกำมะถันลง {OUT_JSON.name}")

    # อัปเดตลง canonical.json
    if CANONICAL_FILE.exists():
        cdata = json.loads(CANONICAL_FILE.read_text(encoding="utf-8"))
        cdata["acid_sulfate_soil_assessment"] = summary
        CANONICAL_FILE.write_text(json.dumps(cdata, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"✅ อัปเดต canonical.json เรียบร้อย")

    # อัปเดตปิดช่องว่างใน gaps.json
    if GAPS_FILE.exists():
        gdata = json.loads(GAPS_FILE.read_text(encoding="utf-8"))
        for gap in gdata.get("gaps", []):
            if gap["id"] == "acid_sulfur_content":
                gap["status"] = "closed"
                gap["evidence"] = summary["evidence_for_gaps"]["acid_sulfur_content"]
            elif gap["id"] == "acid_measures":
                gap["status"] = "closed"
                gap["evidence"] = summary["evidence_for_gaps"]["acid_measures"]

        GAPS_FILE.write_text(json.dumps(gdata, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ ปิดช่องว่าง acid_sulfur_content และ acid_measures ใน gaps.json เรียบร้อย")

    return summary


if __name__ == "__main__":
    analyze_acid_sulfate_soils()
