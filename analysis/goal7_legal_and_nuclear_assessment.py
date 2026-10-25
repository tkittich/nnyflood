#!/usr/bin/env python3
"""analysis/goal7_legal_and_nuclear_assessment.py — การวิเคราะห์ข้อกฎหมายเวนคืนที่ดินเพื่อพาณิชย์ และการประเมินความปลอดภัยศูนย์วิจัยนิวเคลียร์องครักษ์

ปิดช่องว่างความรู้:
1. expropriation_commercial_use: กฎหมายว่าด้วยการเวนคืนที่ดินเพื่อพาณิชย์ (พ.ร.บ.เวนคืนฯ 2562 และรัฐธรรมนูญ 2560)
2. nuclear_site_flood_design: การวิเคราะห์ระดับความปลอดภัยทางน้ำของศูนย์วิจัยนิวเคลียร์องครักษ์ (สทน.) คลอง 14

รัน: python analysis/goal7_legal_and_nuclear_assessment.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAPS_FILE = ROOT / "analysis/goal7/gaps.json"
CANONICAL_FILE = ROOT / "analysis/goal7/canonical.json"
OUT_JSON = ROOT / "analysis/goal7/legal_and_nuclear_summary.json"


def run_assessment():
    # 1. การวิเคราะห์ข้อกฎหมายเวนคืนที่ดิน
    expropriation_analysis = {
        "topic": "การนำที่ดินเวนคืนส่วนเหลือไปพัฒนาเชิงพาณิชย์หรือขายต่อเพื่อหาเงินสร้างคลอง",
        "governing_laws": [
            "รัฐธรรมนูญแห่งราชอาณาจักรไทย พุทธศักราช 2560 มาตรา 37 วรรคสาม",
            "พระราชบัญญัติว่าด้วยการเวนคืนและการได้มาซึ่งอสังหาริมทรัพย์ พ.ศ. 2562 มาตรา 4, มาตรา 34, มาตรา 35, และมาตรา 36",
        ],
        "legal_principles": {
            "section_4": "การเวนคืนอสังหาริมทรัพย์จะกระทำได้ก็แต่โดยอาศัยอำนาจตามบทบัญญัติแห่งกฎหมาย เฉพาะเพื่อการอันเป็นสาธารณูปโภค การอันจำเป็นในการป้องกันประเทศ การได้มาซึ่งทรัพยากรธรรมชาติ หรือเพื่อประโยชน์สาธารณะอย่างอื่น",
            "section_34": "อสังหาริมทรัพย์ที่ได้มาจากการเวนคืน ต้องนำไปใช้ตามวัตถุประสงค์แห่งการเวนคืนนั้น ห้ามมิให้นำไปใช้เพื่อประโยชน์อื่นอันมิใช่วัตถุประสงค์แห่งการเวนคืน",
            "section_35": "ถ้าอสังหาริมทรัพย์ที่ได้มาจากการเวนคืนมิได้นำไปใช้เพื่อประโยชน์ตามวัตถุประสงค์แห่งการเวนคืนภายในระยะเวลาที่กำหนด (5 ปี) หรือเหลือจากการใช้ประโยชน์ ให้หน่วยงานของรัฐต้องเสนอขายคืนให้แก่เจ้าของเดิมหรือทายาทก่อน",
        },
        "legal_conclusion": (
            "กรมชลประทานหรือหน่วยงานของรัฐไม่สามารถนำที่ดินที่ได้มาจากการเวนคืนโครงการคลองเจ้าพระยา 2 "
            "ไปพัฒนาเชิงพาณิชย์ ขายต่อ หรือจัดสรรแสวงหากำไรเพื่อนำเงินมาชดเชยค่าก่อสร้างได้โดยชอบด้วยกฎหมาย "
            "การกระทำดังกล่าวขัดต่อมาตรา 34 ของ พ.ร.บ.เวนคืนฯ 2562 อย่างชัดเจน และหากมีที่ดินส่วนเหลือจากการขุดคลองและคันดิน "
            "กฎหมายตามมาตรา 35 บังคับให้ต้องเสนอขายคืนแก่เจ้าของเดิมตามสิทธิก่อนเสมอ"
        ),
        "gap_id": "expropriation_commercial_use",
        "action": "close",
    }

    # 2. การประเมินความปลอดภัยศูนย์วิจัยนิวเคลียร์องครักษ์ (สทน. องครักษ์)
    nuclear_safety_analysis = {
        "facility_name": "ศูนย์วิจัยนิวเคลียร์องครักษ์ สถาบันเทคโนโลยีนิวเคลียร์แห่งชาติ (องค์การมหาชน) - สทน.",
        "coordinates": {"lat": 14.1221, "lon": 101.0275, "location": "หมู่ 7 ต.ทรายมูล อ.องครักษ์ จ.นครนายก"},
        "spatial_relationship_to_cp2": {
            "distance_to_canal_km": 5.78,
            "relative_direction": "ตั้งอยู่ทางทิศตะวันออกของแนวคลองเจ้าพระยา 2 (ตรงกับคลอง กม.57)",
        },
        "elevation_and_flood_benchmarks": {
            "natural_ground_msl_m": 2.79,   # ระดับดินเดิมของแนวคลอง กม.57 (ไม่ใช่ระดับที่ตั้งศูนย์ — ระดับพื้นอาคารและน้ำท่วมออกแบบของศูนย์ยังไม่พบ)
            "cp2_design_crest_msl_m": 6.09,
            "cp2_design_water_level_msl_m": 4.59,
        },
        "safety_assessment": (
            "ยังไม่พบระดับพื้นอาคารเก็บกากกัมมันตรังสี ระดับน้ำท่วมออกแบบ และแผนฉุกเฉินน้ำท่วมของศูนย์ในเอกสารที่รวบรวมไว้ จึงประเมินความปลอดภัยของอาคารจากน้ำท่วมไม่ได้ (ต้องขอข้อมูลจาก สทน./ปส.) · "
            "สิ่งที่คำนวณได้คือ คลองเจ้าพระยา 2 มีระดับผิวน้ำออกแบบ (+4.59 ม.) และสันคัน (+6.09 ม.) สูงกว่าระดับดินเดิมมาก หากเกิดกรณีคันดินชำรุด "
            "หรือการระบายน้ำด้านข้างกีดขวางการไหลหลาก จะต้องมีระบบเฝ้าระวังทางชลศาสตร์ที่กำหนดไว้ในแผนบริหารจัดการเหตุฉุกเฉินทางนิวเคลียร์และรังสี"
        ),
        "gap_id": "nuclear_site_flood_design",
        "action": "keep_open",
    }

    summary = {
        "title": "การวิเคราะห์ข้อกฎหมายเวนคืนที่ดินเพื่อพาณิชย์ และการประเมินความปลอดภัยศูนย์วิจัยนิวเคลียร์องครักษ์",
        "expropriation_legal_analysis": expropriation_analysis,
        "nuclear_facility_safety_analysis": nuclear_safety_analysis,
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกสรุปผลวิเคราะห์กฎหมายและความปลอดภัยนิวเคลียร์ลง {OUT_JSON.name} เรียบร้อย")

    # อัปเดตลง canonical.json
    if CANONICAL_FILE.exists():
        with open(CANONICAL_FILE, encoding="utf-8") as f:
            cdata = json.load(f)
        cdata["legal_and_nuclear_assessment"] = summary
        with open(CANONICAL_FILE, "w", encoding="utf-8") as f:
            json.dump(cdata, f, ensure_ascii=False, indent=1)
        print(f"✅ อัปเดต canonical.json เรียบร้อย")

    # อัปเดตปิดช่องว่างใน gaps.json
    if GAPS_FILE.exists():
        with open(GAPS_FILE, encoding="utf-8") as f:
            gdata = json.load(f)

        for gap in gdata.get("gaps", []):
            if gap["id"] == "expropriation_commercial_use":
                gap["status"] = "closed"
                gap["evidence"] = (
                    "พ.ร.บ.ว่าด้วยการเวนคืนและการได้มาซึ่งอสังหาริมทรัพย์ พ.ศ. 2562 ม.4 และ ม.34 กำหนดชัดเจนว่าต้องใช้ตามวัตถุประสงค์แห่งการเวนคืนเท่านั้น "
                    "ห้ามนำไปใช้เพื่อประโยชน์อื่น และ ม.35 บังคับให้ต้องเสนอขายคืนเจ้าของเดิมหากเหลือใช้ประโยชน์ ไม่สามารถนำไปพัฒนาเชิงพาณิชย์ได้"
                )
            elif gap["id"] == "nuclear_site_flood_design":
                # เปิดช่องว่างคืน (รีวิวรอบ 7): ค่า +4.50/+3.15 ม. ไม่มีแหล่ง จึงใช้ปิดช่องว่างไม่ได้ — ระยะ 5.78 กม. เป็นผลวัดจากพิกัดผู้ใช้ ไม่ใช่หลักฐานด้านน้ำท่วม
                gap["status"] = "open"
                gap.pop("evidence", None)

        with open(GAPS_FILE, "w", encoding="utf-8", newline="
") as f:
            json.dump(gdata, f, ensure_ascii=False, indent=2)
        print("✅ ปิดช่องว่าง expropriation_commercial_use · คง nuclear_site_flood_design เป็นช่องว่างที่เปิดอยู่ ใน gaps.json")

    return summary


if __name__ == "__main__":
    run_assessment()
