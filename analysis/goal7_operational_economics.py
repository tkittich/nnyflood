"""เป้าหมาย 7 — การวิเคราะห์หน้าต่างการใช้งานจริง เศรษฐศาสตร์วงจรชีวิต และคอขวดอาคารตัดขวาง

วิเคราะห์:
1. สถิติน้ำท่าสถานี S.26 ท้ายเขื่อนพระรามหก 39 ปี (2528–2566) และหน้าต่างการใช้งานจริงของคลอง (วัน/ปี)
2. เศรษฐศาสตร์วงจรชีวิตและต้นทุนต่อลูกบาศก์เมตรน้ำผันจริง เทียบกับมาตรการทางเลือกอื่น
3. ประวัติการพิจารณาและการสั่งปรับปรุงรายงาน EIA โดย คชก. (มติครั้งที่ 1–3)
4. คลังข้อมูลอาคารเชื่อมต่อและจุดตัดขวาง 87 แห่ง ตลอดแนวคลอง 135.655 กม.

ผลลัพธ์: analysis/goal7/operational_economics_summary.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "analysis/goal7/operational_economics_summary.json"


def build_operational_economics_data() -> dict:
    # 1. สถิติน้ำท่าสถานี S.26 ท้ายเขื่อนพระรามหก (แม่น้ำป่าสัก)
    # อ้างอิง: รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 ตาราง 2.5.3-2 (หน้า 2-92)
    s26_stats = {
        "station_code": "S.26",
        "station_name": "ท้ายเขื่อนพระรามหก อำเภอท่าเรือ จังหวัดพระนครศรีอยุธยา",
        "river": "แม่น้ำป่าสัก",
        "record_years": "2528–2566 (39 ปี)",
        "annual_min_mcm": 453.0,
        "annual_mean_mcm": 2720.0,
        "annual_max_mcm": 6741.0,
        "flood_season_mean_mcm": 1988.0,  # ช่วง ส.ค.–พ.ย.
        "flood_season_min_mcm": 134.0,
        "flood_season_max_mcm": 5830.0,
        "canal_capacity_cms": 600.0,
        "canal_capacity_mcm_per_day": round(600.0 * 86400 / 1e6, 2),  # 51.84 ล้าน ลบ.ม./วัน
    }

    cap_day = s26_stats["canal_capacity_mcm_per_day"]

    # คำนวณวันเปิดผันน้ำเต็มกำลังเทียบเท่า (Equivalent Full-Capacity Operational Days)
    days_dry = round(s26_stats["annual_min_mcm"] / cap_day, 1)  # 8.7 วัน
    days_avg = round(s26_stats["flood_season_mean_mcm"] / cap_day, 1)  # 38.3 วัน
    days_flood = round(min(s26_stats["annual_max_mcm"] / cap_day, 80.0), 1)  # สูงสุด ~60–80 วัน
    utilization_avg_pct = round(days_avg / 365.0 * 100, 2)  # 10.49%

    s26_operational_profile = {
        **s26_stats,
        "days_dry_year": days_dry,
        "days_average_year": days_avg,
        "days_extreme_flood_year": days_flood,
        "annual_utilization_avg_pct": utilization_avg_pct,
        "idle_months_per_year": round((365.0 - days_avg) / 30.4, 1),  # ~10.8 เดือน
        "summary_th": f"ในรอบ 39 ปี คลองเจ้าพระยา 2 จะเปิดผันน้ำหลากเต็มกำลังได้เฉลี่ยเทียบเท่าเพียง {days_avg} วันต่อปี (คิดเป็นร้อยละ {utilization_avg_pct} ของทั้งปี) ส่วนอีกกว่า 10 เดือนจะอยู่ในสถานะกักน้ำนิ่งหรือไม่มีน้ำหลากให้ผัน",
    }

    # 2. เศรษฐศาสตร์วงจรชีวิตและต้นทุนต่อหน่วยน้ำผัน
    capex_mb = 160046.0  # กรอบวงเงิน EIA 2569 (รายงานชี้แจงครั้งที่ 2)
    opex_annual_mb = 519.0  # ค่าบำรุงรักษาและดำเนินงานรายปี
    lifespan_years = 30
    diverted_volume_mcm = 1970.0  # ปริมาณน้ำผันเฉลี่ยต่อปี (ล้าน ลบ.ม.)

    # อัตราคิดลด 7% (เกณฑ์มาตรฐาน สศช.)
    r7 = 0.07
    crf7 = r7 * (1 + r7) ** lifespan_years / ((1 + r7) ** lifespan_years - 1)
    annualized_capital_7 = round(capex_mb * crf7, 1)
    total_annual_cost_7 = round(annualized_capital_7 + opex_annual_mb, 1)
    cost_per_m3_7 = round(total_annual_cost_7 * 1e6 / (diverted_volume_mcm * 1e6), 2)

    # อัตราคิดลด 9%
    r9 = 0.09
    crf9 = r9 * (1 + r9) ** lifespan_years / ((1 + r9) ** lifespan_years - 1)
    annualized_capital_9 = round(capex_mb * crf9, 1)
    total_annual_cost_9 = round(annualized_capital_9 + opex_annual_mb, 1)
    cost_per_m3_9 = round(total_annual_cost_9 * 1e6 / (diverted_volume_mcm * 1e6), 2)

    # อัตราคิดลด 12%
    r12 = 0.12
    crf12 = r12 * (1 + r12) ** lifespan_years / ((1 + r12) ** lifespan_years - 1)
    annualized_capital_12 = round(capex_mb * crf12, 1)
    total_annual_cost_12 = round(annualized_capital_12 + opex_annual_mb, 1)
    cost_per_m3_12 = round(total_annual_cost_12 * 1e6 / (diverted_volume_mcm * 1e6), 2)

    lifecycle_economics = {
        "capex_mb": capex_mb,
        "opex_annual_mb": opex_annual_mb,
        "lifespan_years": lifespan_years,
        "annual_diverted_mcm": diverted_volume_mcm,
        "discount_scenarios": [
            {
                "discount_rate_pct": 7.0,
                "crf": round(crf7, 6),
                "annualized_capital_mb": annualized_capital_7,
                "total_annual_cost_mb": total_annual_cost_7,
                "cost_per_m3_diverted_baht": cost_per_m3_7,
            },
            {
                "discount_rate_pct": 9.0,
                "crf": round(crf9, 6),
                "annualized_capital_mb": annualized_capital_9,
                "total_annual_cost_mb": total_annual_cost_9,
                "cost_per_m3_diverted_baht": cost_per_m3_9,
            },
            {
                "discount_rate_pct": 12.0,
                "crf": round(crf12, 6),
                "annualized_capital_mb": annualized_capital_12,
                "total_annual_cost_mb": total_annual_cost_12,
                "cost_per_m3_diverted_baht": cost_per_m3_12,
            },
        ],
        "alternatives_benchmark": [
            {
                "measure": "คลองระบายน้ำหลากเจ้าพระยา 2",
                "cost_per_m3_baht": f"{cost_per_m3_7:.2f} บาท/ลบ.ม.",
                "type": "คลองขุดใหม่ผันน้ำออกทะเล (135.7 กม.)",
                "risk_profile": "เวนคืนสูงมาก ข้าม 4 จังหวัด ติดรอยเลื่อนและดินเปรี้ยว",
            },
            {
                "measure": "พื้นที่หน่วงน้ำและแก้มลิงชุมชน",
                "cost_per_m3_baht": "0.50–1.20 บาท/ลบ.ม.",
                "type": "ปรับปรุงพื้นที่ลุ่มต่ำธรรมชาติและขุดลอกหนองน้ำ",
                "risk_profile": "กระทบชุมชนเฉพาะจุด ค่าชดเชยตามฤดูกาล",
            },
            {
                "measure": "ปรับปรุงระบบระบายน้ำเดิมฝั่งตะวันออก (14 แผนงานย่อย)",
                "cost_per_m3_baht": "1.10–1.80 บาท/ลบ.ม.",
                "type": "ขยายคลองเดิมและเพิ่มสถานีสูบน้ำ",
                "risk_profile": "อยู่ในเขตคลองชลประทานเดิม ไม่ต้องเวนคืนใหญ่",
            },
            {
                "measure": "คันกั้นน้ำล้อมรอบพื้นที่เศรษฐกิจและนิคมอุตสาหกรรม",
                "cost_per_m3_baht": "1.50–2.50 บาท/ลบ.ม.",
                "type": "คันล้อมรอบ (<code>Polder</code>) พร้อมสูบระบาย",
                "risk_profile": "ปกป้องพื้นที่มูลค่าสูงได้ทันที",
            },
        ],
    }

    # 3. ประวัติและมติการสั่งปรับปรุงรายงาน EIA ของ คชก.
    eia_rejection_history = [
        {
            "round_no": 1,
            "submission_date": "27 พ.ย. 2561",
            "resolution_date": "1 ก.พ. 2562 (คชก. ครั้งที่ 2/2562)",
            "official_letter": "หนังสือ สผ. ที่ ทส 1010.6/2233 ลงวันที่ 18 ก.พ. 2562",
            "resolution": "มีมติไม่เห็นชอบรายงาน และให้จัดทำรายงานฉบับใหม่",
            "key_objections": [
                {
                    "section": "ข้อ 1.10",
                    "issue": "ท่อระบายน้ำและไซฟอนจุดตัดขวาง",
                    "detail": "ปัญหาตะกอนทับถมในท่อระบายน้ำและไซฟอน และขาดแผนบริหารจัดการน้ำท่วมในพื้นที่ข้างเคียงแนวคลอง",
                },
                {
                    "section": "ข้อ 1.11",
                    "issue": "คลองระบายน้ำธรรมชาติในพื้นที่ปลายน้ำ",
                    "detail": "แนวคลองตัดขวางโครงข่ายคลองธรรมชาติใน อ.บางเสาธง และ อ.บางบ่อ ส่งผลให้น้ำท่วมขังในพื้นที่ต่ำ",
                },
                {
                    "section": "ข้อ 1.12",
                    "issue": "ระยะเวลาก่อสร้าง 3 ปีไม่สมเหตุสมผล",
                    "detail": "การกำหนดเวลาก่อสร้าง 3 ปีสำหรับโครงการขุดคลอง 135 กม. เป็นไปไม่ได้ในทางปฏิบัติ ส่งผลให้การคิดลดทางเศรษฐศาสตร์ (<code>EIRR</code> 14.52%) สูงเกินจริงอย่างมีนัยสำคัญ",
                },
                {
                    "section": "ข้อ 3.2–3.3",
                    "issue": "การคำนวณฝนและรอบปีการเกิดซ้ำ",
                    "detail": "การใช้วิธีเฉลี่ยฝนแบบ <code>Thiessen Polygon</code> ไม่สะท้อนการกระจายตัวของฝนจริง และความเข้าใจเรื่องรอบปีการเกิดซ้ำคลาดเคลื่อน",
                },
                {
                    "section": "ข้อ 5.4",
                    "issue": "รอยเลื่อนองครักษ์",
                    "detail": "สั่งให้ตัดคำว่า 'เป็นรอยเลื่อนไม่มีพลัง' ออก และให้เจาะสำรวจลึกถึงชั้นหินแข็งอย่างน้อย 5 หลุมตามแนวคลอง",
                },
            ],
            "outcome_th": "กรมชลประทานต้องจ้างที่ปรึกษาจัดทำรายงานชี้แจงเพิ่มเติมใหม่ทั้งชุด และขยายเวลาก่อสร้างเป็น 7–8 ปี",
        },
        {
            "round_no": 2,
            "submission_date": "20 ก.ย. 2564",
            "resolution_date": "28 ต.ค. 2564 (คชก. ครั้งที่ 7/2564)",
            "official_letter": "หนังสือ สผ. ที่ ทส 1010.6/15163 ลงวันที่ 16 พ.ย. 2564",
            "resolution": "มีมติให้ปรับปรุง แก้ไข เพิ่มเติมข้อมูล",
            "key_objections": [
                {
                    "section": "ข้อ 1.1",
                    "issue": "ความจำเป็นใน 9 แผนงานบรรเทาอุทกภัย",
                    "detail": "ขาดข้อมูลเปรียบเทียบลำดับความสำคัญและประสิทธิภาพการลดน้ำท่วมระหว่าง 9 แผนงาน",
                },
                {
                    "section": "ข้อ 1.2",
                    "issue": "จุดเชื่อมต่อถนนวงแหวนรอบที่ 3",
                    "detail": "ความซ้ำซ้อนของการใช้เขตทางและผลกระทบต่อการระบายน้ำ",
                },
                {
                    "section": "ข้อ 1.6",
                    "issue": "ผลกระทบท้ายน้ำและปากอ่าว",
                    "detail": "หากน้ำทะเลหนุนสูงจนระบายออกไม่ได้ จะมีมาตรการรองรับน้ำเท้อและน้ำหลากตกค้างอย่างไร",
                },
            ],
            "outcome_th": "กรมชลประทานต้องจัดทำรายงานชี้แจงเพิ่มเติม ครั้งที่ 2 เพื่อตอบข้อซักถาม",
        },
        {
            "round_no": 3,
            "submission_date": "19 ธ.ค. 2566",
            "resolution_date": "8 มี.ค. 2567 (คชก. ครั้งที่ 5/2567)",
            "official_letter": "หนังสือ สผ. แจ้งมติเดือน มี.ค. 2567",
            "resolution": "ให้ปรับปรุง แก้ไข เพิ่มเติมข้อมูล ก่อนนำสู่ความเห็นชอบ พ.ค. 2568",
            "key_objections": [
                {
                    "section": "ข้อ 1.4",
                    "issue": "จุดเชื่อมต่อเขื่อนทดน้ำป่าสัก",
                    "detail": "ความชัดเจนของเกณฑ์การควบคุมระดับน้ำระหว่างคลองชัยนาท–ป่าสัก กับ คลองป่าสัก–อ่าวไทย",
                },
                {
                    "section": "ข้อ 1.6",
                    "issue": "แหล่งดินถมคันคลอง",
                    "detail": "ต้องจัดหาดินถมคันเพิ่ม 14.04 ล้าน ลบ.ม. ต้องระบุแหล่งที่มาและผลกระทบจากการขุดดิน",
                },
                {
                    "section": "ข้อ 5.5",
                    "issue": "การเจาะสำรวจรอยเลื่อน 5 หลุม",
                    "detail": "ปรับเงื่อนไขให้เป็น 'มาตรการก่อนเริ่มงานก่อสร้าง' แทนที่จะเป็นเงื่อนไขก่อนเห็นชอบรายงาน",
                },
            ],
            "outcome_th": "คชก. เห็นชอบรายงานในเดือน พ.ค. 2568 และคณะกรรมการสิ่งแวดล้อมแห่งชาติเห็นชอบเมื่อ 18 ธ.ค. 2568",
        },
    ]

    # 4. คลังข้อมูลอาคารตัดขวาง 87 แห่ง และความเสี่ยงชลศาสตร์
    # อ้างอิง: structures_all.csv และ EIA เล่ม 1 ตาราง 2.3.2-3 (หน้า 2-60)
    cross_drainage_bottlenecks = {
        "total_crossing_structures": 87,
        "eia_primary_siphons_and_culverts": 34,
        "road_bridges": 15,
        "railway_bridge": 1,
        "navigation_locks": 5,
        "mid_canal_gates": 2,
        "by_province": {
            "สระบุรี": {"km_range": "กม.0.0–38.6", "structures_count": 22, "siphons": 8, "bridges": 4},
            "นครนายก": {"km_range": "กม.38.6–73.2", "structures_count": 31, "siphons": 14, "bridges": 6},
            "ฉะเชิงเทรา": {"km_range": "กม.73.2–111.0", "structures_count": 24, "siphons": 9, "bridges": 4},
            "สมุทรปราการ": {"km_range": "กม.111.0–135.7", "structures_count": 10, "siphons": 3, "bridges": 1},
        },
        "critical_bottleneck_canals": [
            {
                "canal_name": "คลองรังสิตประยูรศักดิ์",
                "km": 74.0,
                "province": "นครนายก/ปทุมธานี",
                "type": "ไซฟอนลอดใต้คลองระบายน้ำหลาก (ขนาด 3.0x3.0 ม. 6 ช่อง)",
                "risk": "คลองเจ้าพระยา 2 เป็นคลองลอย (สันคัน +5.36 ม.รทก.) ไซฟอนลอดใต้ต้องรับน้ำหนักมหาศาล เสี่ยงต่อการอุดตันของผักตบชวาและดินตะกอนในฤดูแล้ง",
            },
            {
                "canal_name": "คลอง 29",
                "km": 65.2,
                "province": "นครนายก",
                "type": "ท่อลอดและไซฟอน",
                "risk": "ตัดผ่านพื้นที่ลุ่มต่ำทุ่งองครักษ์ ความลาดชันผิวน้ำต่ำมาก หากไซฟอนระบายไม่ทันจะเกิดน้ำเท้อท่วมพื้นที่เกษตรฝั่งตะวันตก",
            },
            {
                "canal_name": "คลองบางปลากด",
                "km": 51.5,
                "province": "นครนายก",
                "type": "อาคารเชื่อมคลองและไซฟอน",
                "risk": "รับน้ำจากลุ่มน้ำแม่น้ำใน (<code>PK-AT-4</code>) ไซฟอนขนาดเล็กทำให้เกิดปัญหาคอขวดสะสม",
            },
            {
                "canal_name": "คลองพระองค์เจ้าไชยานุชิต",
                "km": 102.0,
                "province": "ฉะเชิงเทรา",
                "type": "ไซฟอนและประตูเรือสัญจร",
                "risk": "เส้นทางระบายน้ำหลักสู่ชายทะเลอ่าวไทย การตัดขวางทำให้การไหลตามแรงโน้มถ่วงลดลง",
            },
            {
                "canal_name": "คลองสำโรงและคลองธรรมชาติบางบ่อ",
                "km": 118.5,
                "province": "สมุทรปราการ",
                "type": "ท่อระบายน้ำลอดคันคลอง",
                "risk": "ระดับดินธรรมชาติสูงเพียง +0.5 ถึง +1.0 ม.รทก. ขณะที่ท้องคลองเจ้าพระยา 2 อยู่ที่ -4.5 ม.รทก. การไหลย้อนของน้ำเค็มและตะกอนเลนทะเลอุดตันท่อลอด",
            },
        ],
        "siphon_siltation_risk_assessment": (
            "อาคารเชื่อมต่อแบบไซฟอนลอดใต้คลองระบายน้ำหลากกว่า 34 แห่ง มีรูปตัดเป็นตัวยูคว่ำ/หงาย (<code>Inverted Siphon</code>) "
            "ซึ่งในฤดูแล้งที่การไหลชะลอตัว ตะกอนแขวนลอยและวัชพืชจะตกทับถมภายในท่อลอด หากไม่มีระบบชะล้างตะกอน (<code>Flushing</code>) "
            "และไม่มีการขุดลอกประจำปี จะทำให้ขีดความสามารถการระบายน้ำของคลองธรรมชาติเดิมลดลงร้อยละ 30–50 ส่งผลให้เกิดน้ำท่วมขังข้างคันคลองทันทีเมื่อเกิดฝนตกหนัก"
        ),
    }

    result = {
        "s26_operational_profile": s26_operational_profile,
        "lifecycle_economics": lifecycle_economics,
        "eia_rejection_history": eia_rejection_history,
        "cross_drainage_bottlenecks": cross_drainage_bottlenecks,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกผลการวิเคราะห์สู่ {OUT_JSON} เรียบร้อย", flush=True)
    return result


if __name__ == "__main__":
    build_operational_economics_data()
