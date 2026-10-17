"""เป้าหมาย 7 — การวิเคราะห์เส้นทางชลศาสตร์ เวกเตอร์การไหล และเวลาเดินทางจากเขื่อนสู่ปากอ่าวไทย (Dam-to-Gulf Hydraulic Corridors)

ครอบคลุม 3 ระเบียงชลศาสตร์หลัก:
1. ระเบียงแม่น้ำนครนายก–บางปะกง: เขื่อนขุนด่านปราการชล → แม่น้ำนครนายก → ทุ่งองครักษ์ → แม่น้ำบางปะกง → อ่าวไทย (132 กม.)
2. ระเบียงแม่น้ำป่าสัก–คลองเจ้าพระยา2: เขื่อนป่าสักชลสิทธิ์ → เขื่อนพระรามหก → คลองระพีพัฒน์/คลองเจ้าพระยา2 → ปากอ่าวไทย (182 กม.)
3. ระเบียงแม่น้ำเจ้าพระยาสายหลัก: เขื่อนเจ้าพระยา (ชัยนาท) → สิงห์บุรี → อ่างทอง → อยุธยา (บางไทร) → กทม. → ป้อมพระจุลฯ อ่าวไทย (235 กม.)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_PATH = ROOT / "analysis/goal7/canonical.json"


def build_corridor_1_khundan_to_gulf() -> dict:
    """ระเบียงที่ 1: เขื่อนขุนด่านปราการชล → แม่น้ำนครนายก → ทุ่งองครักษ์ → แม่น้ำบางปะกง → อ่าวไทย"""
    nodes = [
        {
            "id": "KD_DAM",
            "name": "เขื่อนขุนด่านปราการชล (ระดับกักเก็บปกติ/ท้ายเขื่อน)",
            "km": 0.0,
            "stage_msl": 28.50,
            "feature": "ต้นน้ำ / เขื่อนคอนกรีตบดอัด (ระดับน้ำกักเก็บ +108.09 ม.รทก. ปล่อยลงท้ายเขื่อน +28.5 ม.)",
        },
        {
            "id": "NY1B_THADAN",
            "name": "สะพานท่าด่าน / ท่าช้าง (สถานี Ny.1B)",
            "km": 4.2,
            "stage_msl": 16.80,
            "feature": "เขตเชิงเขา / น้ำตกนางรอง–วังตะไคร้",
        },
        {
            "id": "NY7_MUEANG",
            "name": "อ.เมืองนครนายก สะพานหน้าจวนผู้ว่าฯ (สถานี Ny.7)",
            "km": 22.5,
            "stage_msl": 6.28,
            "feature": "เขตที่ราบดอนตัวเมือง (ตลิ่ง 8.45 ม. น้ำลดต่ำกว่าตลิ่งสู่ระดับปกติ)",
        },
        {
            "id": "TNY10_ONGKHARAK",
            "name": "อ.องครักษ์ คลองแม่น้ำใน (สถานี TNy10)",
            "km": 54.0,
            "stage_msl": 2.35,
            "feature": "แอ่งก้นกระทะตอนล่าง (ระดับดิน 1.0–2.5 ม.รทก. น้ำท่วมขังค้างทุ่ง)",
        },
        {
            "id": "BPK003_BANGNAMP RIAO",
            "name": "คลองบางน้ำเปรี้ยว ฉะเชิงเทรา (สถานี BPK003)",
            "km": 78.0,
            "stage_msl": 2.56,
            "feature": "จุดคอขวดระบายน้ำ (ระดับน้ำสูงกว่าองครักษ์ เกิดสภาวะปิดกั้นชลศาสตร์)",
        },
        {
            "id": "TKG60_CHACHOENGSAO",
            "name": "แม่น้ำบางปะกง อ.เมืองฉะเชิงเทรา (สถานี Tkg.60)",
            "km": 98.0,
            "stage_msl": 1.80,
            "feature": "แม่น้ำสายหลักตอนล่าง (เริ่มได้รับอิทธิพลน้ำขึ้น-น้ำลง)",
        },
        {
            "id": "BPK001_GULF",
            "name": "ปากแม่น้ำบางปะกงออกสู่อ่าวไทย (สถานี BPK001)",
            "km": 132.0,
            "stage_msl": 0.19,  # ระดับน้ำทะเลปานกลางเฉลี่ย (หนุนสูงสุด +1.43 / ต่ำสุด -1.05)
            "feature": "ปากอ่าวไทย (ช่วงแกว่งน้ำขึ้น-น้ำลง 2.48 ม. บล็อกระบายน้ำช่วงน้ำขึ้น)",
        },
    ]

    segments = []
    total_travel_hours = 0.0

    for i in range(len(nodes) - 1):
        u, d = nodes[i], nodes[i + 1]
        dist_km = d["km"] - u["km"]
        dist_m = dist_km * 1000.0
        head_diff = u["stage_msl"] - d["stage_msl"]
        slope = head_diff / dist_m
        slope_cm_per_km = slope * 100000.0

        # จำแนกความเร็วการไหลชลศาสตร์ตามความลาดชัน
        if slope_cm_per_km > 100.0:
            regime = "การไหลเชี่ยวกรากในเขตเชิงเขา"
            velocity_ms = 2.10
        elif slope_cm_per_km > 20.0:
            regime = "การไหลอิสระตามแรงโน้มถ่วงในที่ราบดอน"
            velocity_ms = 1.05
        elif slope_cm_per_km > 2.0:
            regime = "การไหลเอื่อยในที่ราบลุ่มต่ำ"
            velocity_ms = 0.42
        elif slope_cm_per_km >= 0.0:
            regime = "การไหลหน่วงชะลอตัวใกล้จุดคอขวด"
            velocity_ms = 0.15
        else:
            regime = "สภาวะปิดกั้นชลศาสตร์หรือน้ำหนุนย้อนกลับ"
            velocity_ms = 0.03

        travel_hours = (dist_m / velocity_ms) / 3600.0
        total_travel_hours += travel_hours

        segments.append({
            "segment_name": f"{u['name'].split('(')[0].strip()} → {d['name'].split('(')[0].strip()}",
            "dist_km": round(dist_km, 1),
            "head_diff_m": round(head_diff, 2),
            "slope_cm_per_km": round(slope_cm_per_km, 2),
            "flow_regime": regime,
            "velocity_ms": velocity_ms,
            "travel_hours": round(travel_hours, 1),
        })

    return {
        "corridor_id": "corridor_1",
        "title": "ระเบียงแม่น้ำนครนายก–บางปะกง (เขื่อนขุนด่านฯ สู่ปากอ่าวไทย)",
        "total_length_km": 132.0,
        "total_travel_hours": round(total_travel_hours, 1),
        "total_travel_days": round(total_travel_hours / 24.0, 1),
        "nodes": nodes,
        "segments": segments,
        "bottleneck_node": "BPK003_BANGNAMP RIAO (กม.78 ความลาดชันติดลบ -0.87 ซม./กม.)",
        "tidal_lock_node": "BPK001_GULF (กม.132 น้ำทะเลหนุนสูงสุด +1.43 ม.รทก. ปิดระบายน้ำ 14–18 ชม./วัน)",
    }


def build_corridor_2_pasak_to_gulf() -> dict:
    """ระเบียงที่ 2: เขื่อนป่าสักชลสิทธิ์ → เขื่อนพระรามหก → คลองระพีพัฒน์/คลองเจ้าพระยา2 → ปากอ่าวไทย"""
    nodes = [
        {
            "id": "PASAK_DAM",
            "name": "เขื่อนป่าสักชลสิทธิ์ (ระดับน้ำท้ายเขื่อน)",
            "km": 0.0,
            "stage_msl": 23.50,
            "feature": "ต้นน้ำป่าสัก (ระดับน้ำกักเก็บปกติ +42.0 ม.รทก. ระดับท้ายเขื่อน +23.5 ม.)",
        },
        {
            "id": "RAMA6_DAM",
            "name": "เขื่อนพระรามหก อ.ท่าหลวง อยุธยา",
            "km": 45.0,
            "stage_msl": 7.50,
            "feature": "เขื่อนทดน้ำสายแรกของไทย (จุดผันน้ำเข้าคลองระพีพัฒน์)",
        },
        {
            "id": "CP2_INLET",
            "name": "ปากคลองระบายน้ำหลากเจ้าพระยา2 (สระบุรี กม.0)",
            "km": 72.0,
            "stage_msl": 6.40,
            "feature": "จุดตัดรับน้ำป่าสักเข้าคลองระบายน้ำหลากสายใหม่ (ผิวน้ำออกแบบ +6.4 ม.รทก.)",
        },
        {
            "id": "DHAMMARAJA_ATG08",
            "name": "ปตร.พระธรรมราชา คลอง 13 (สถานี ATG08)",
            "km": 98.0,
            "stage_msl": 2.93,
            "feature": "จุดเชื่อมโครงข่ายคลองรังสิตฯ (มีสถานีสูบน้ำผลักดันมุ่งหน้าทิศตะวันออก)",
        },
        {
            "id": "ONGKHARAK_CROSSING",
            "name": "จุดตัด อ.องครักษ์ นครนายก (คลองเจ้าพระยา2 กม.54–73)",
            "km": 126.0,
            "stage_msl": 3.80,
            "feature": "คลองลอยยกคันสูงกว่าดินเดิม 2.5–3.5 ม. (ผิวน้ำในคลอง +3.8 ม. สูงกว่าน้ำทุ่งองครักษ์ 2.35 ม.)",
        },
        {
            "id": "CP2_OUTLET_GULF",
            "name": "สถานีสูบน้ำปลายคลองระบายน้ำหลากออกสู่อ่าวไทย (กม.135+655)",
            "km": 182.0,
            "stage_msl": 0.00,
            "feature": "ปลายคลองออกสู่อ่าวไทยที่ ต.สองคลอง อ.บางปะกง (สถานีสูบ 400 ลบ.ม./วิ บังคับน้ำออกสู่ทะเล)",
        },
    ]

    segments = []
    total_travel_hours = 0.0

    for i in range(len(nodes) - 1):
        u, d = nodes[i], nodes[i + 1]
        dist_km = d["km"] - u["km"]
        dist_m = dist_km * 1000.0
        head_diff = u["stage_msl"] - d["stage_msl"]
        slope = head_diff / dist_m
        slope_cm_per_km = slope * 100000.0

        if slope_cm_per_km > 20.0:
            regime = "การไหลตามแรงโน้มถ่วงในแม่น้ำธรรมชาติ"
            velocity_ms = 1.15
        elif slope_cm_per_km > 5.0:
            regime = "การไหลในคลองส่งน้ำและคลองระบาย"
            velocity_ms = 0.85
        elif slope_cm_per_km > 0.0:
            regime = "การไหลในคลองลอยและคลองระบายความลาดชันต่ำ"
            velocity_ms = 0.65
        else:
            regime = "การสูบส่งด้วยแรงดันชลศาสตร์"
            velocity_ms = 0.90

        travel_hours = (dist_m / velocity_ms) / 3600.0
        total_travel_hours += travel_hours

        segments.append({
            "segment_name": f"{u['name'].split('(')[0].strip()} → {d['name'].split('(')[0].strip()}",
            "dist_km": round(dist_km, 1),
            "head_diff_m": round(head_diff, 2),
            "slope_cm_per_km": round(slope_cm_per_km, 2),
            "flow_regime": regime,
            "velocity_ms": velocity_ms,
            "travel_hours": round(travel_hours, 1),
        })

    return {
        "corridor_id": "corridor_2",
        "title": "ระเบียงแม่น้ำป่าสัก–คลองเจ้าพระยา2 (เขื่อนป่าสักฯ สู่ปากอ่าวไทย)",
        "total_length_km": 182.0,
        "total_travel_hours": round(total_travel_hours, 1),
        "total_travel_days": round(total_travel_hours / 24.0, 1),
        "nodes": nodes,
        "segments": segments,
        "engineering_solution": "คลองเจ้าพระยา2 ใช้สถานีสูบน้ำปลายคลอง 400 ลบ.ม./วิ ข้ามปัญหาแรงโน้มถ่วงและน้ำทะเลหนุน",
    }


def build_corridor_3_chaophraya_to_gulf() -> dict:
    """ระเบียงที่ 3: เขื่อนเจ้าพระยา (ชัยนาท) → อยุธยา (บางไทร) → กรุงเทพฯ → ป้อมพระจุลฯ อ่าวไทย"""
    nodes = [
        {
            "id": "C13_CHAOPHRAYA_DAM",
            "name": "เขื่อนเจ้าพระยา จ.ชัยนาท (สถานี C.13)",
            "km": 0.0,
            "stage_msl": 14.20,  # ระดับน้ำท้ายเขื่อน
            "feature": "จุดควบคุมการระบายน้ำหลากลุ่มน้ำเจ้าพระยา (ท้ายเขื่อนระบาย 2,000–2,800 ลบ.ม./วิ)",
        },
        {
            "id": "C3_SINGBURI",
            "name": "สิงห์บุรี (สถานี C.3)",
            "km": 42.0,
            "stage_msl": 11.20,
            "feature": "แม่น้ำเจ้าพระยาตอนบน (ที่ราบภาคกลางตอนบน ตลิ่งสูง)",
        },
        {
            "id": "C7A_ANGTHONG",
            "name": "อ่างทอง (สถานี C.7A)",
            "km": 82.0,
            "stage_msl": 8.80,
            "feature": "แม่น้ำเจ้าพระยาตอนกลาง (จุดล้นตลิ่งเข้าทุ่งรับน้ำ)",
        },
        {
            "id": "C29A_BANGSAI",
            "name": "อ.บางไทร จ.พระนครศรีอยุธยา (สถานี C.29A)",
            "km": 135.4,
            "stage_msl": 2.85,
            "feature": "จุดรวมมวลน้ำเจ้าพระยาและแม่น้ำป่าสัก (จุดชี้วัดปริมาณน้ำไหลเข้าสู่ กทม.)",
        },
        {
            "id": "C22A_PAKKRET",
            "name": "อ.ปากเกร็ด จ.นนทบุรี (สถานี C.22A)",
            "km": 175.0,
            "stage_msl": 2.15,
            "feature": "ปากแม่น้ำเขตปริมณฑล (เริ่มได้รับอิทธิพลน้ำทะเลหนุนชัดเจน)",
        },
        {
            "id": "BKK_MEMORIAL",
            "name": "กรุงเทพมหานคร สะพานพุทธยอดฟ้า",
            "km": 205.0,
            "stage_msl": 1.95,
            "feature": "พื้นที่กรุงเทพมหานครชั้นใน (ระดับน้ำแกว่งตามน้ำทะเลหนุน +0.80 ถึง +2.20 ม.รทก.)",
        },
        {
            "id": "FORT_CHULA_GULF",
            "name": "ป้อมพระจุลจอมเกล้า จ.สมุทรปราการ (ปากอ่าวไทย)",
            "km": 235.0,
            "stage_msl": 0.20,
            "feature": "ปากแม่น้ำเจ้าพระยาออกสู่อ่าวไทย (ช่วงแกว่งน้ำขึ้น-น้ำลง 2.55 ม.)",
        },
    ]

    segments = []
    total_travel_hours = 0.0

    for i in range(len(nodes) - 1):
        u, d = nodes[i], nodes[i + 1]
        dist_km = d["km"] - u["km"]
        dist_m = dist_km * 1000.0
        head_diff = u["stage_msl"] - d["stage_msl"]
        slope = head_diff / dist_m
        slope_cm_per_km = slope * 100000.0

        if slope_cm_per_km > 8.0:
            regime = "การไหลในแม่น้ำสายใหญ่ตอนบน"
            velocity_ms = 1.25
        elif slope_cm_per_km > 3.0:
            regime = "การไหลรวมมวลน้ำหลาก"
            velocity_ms = 1.10
        elif slope_cm_per_km > 1.0:
            regime = "การไหลหน่วงในเขตชุมชนเมือง"
            velocity_ms = 0.70
        else:
            regime = "การไหลสลับทิศทางตามน้ำขึ้น-น้ำลง"
            velocity_ms = 0.45

        travel_hours = (dist_m / velocity_ms) / 3600.0
        total_travel_hours += travel_hours

        segments.append({
            "segment_name": f"{u['name'].split('(')[0].strip()} → {d['name'].split('(')[0].strip()}",
            "dist_km": round(dist_km, 1),
            "head_diff_m": round(head_diff, 2),
            "slope_cm_per_km": round(slope_cm_per_km, 2),
            "flow_regime": regime,
            "velocity_ms": velocity_ms,
            "travel_hours": round(travel_hours, 1),
        })

    return {
        "corridor_id": "corridor_3",
        "title": "ระเบียงแม่น้ำเจ้าพระยาสายหลัก (เขื่อนเจ้าพระยาสู่ปากอ่าวไทย)",
        "total_length_km": 235.0,
        "total_travel_hours": round(total_travel_hours, 1),
        "total_travel_days": round(total_travel_hours / 24.0, 1),
        "nodes": nodes,
        "segments": segments,
        "tidal_front_km": "กม. 175 (ปากเกร็ด นนทบุรี เป็นจุดสิ้นสุดอิทธิพลน้ำหลากทางเดียว และเริ่มมีน้ำทะเลหนุนดันกลับ)",
    }


def build_accuracy_and_boundary_assessment() -> dict:
    """การประเมินความแม่นยำและการรวมแหล่งน้ำ (ปริมาณฝนและแบบจำลองความสูงภูมิประเทศ) ในการวิเคราะห์ชลศาสตร์และเวกเตอร์การไหล"""
    return {
        "title": "การประเมินความแม่นยำและการรวมแหล่งน้ำ (ปริมาณฝนและแบบจำลองความสูงภูมิประเทศ) ในการวิเคราะห์ชลศาสตร์และเวกเตอร์การไหล",
        "sources_included": [
            {
                "category": "ระดับน้ำโทรมาตรจริง",
                "detail": "ระดับน้ำจริงรายชั่วโมงเทียบ ม.รทก. จากสถานีโทรมาตรสารสนเทศน้ำและกรมชลประทาน (เช่น <code>Ny.1B</code>, <code>Ny.7</code>, <code>TNy10</code>, <code>BPK003</code>, <code>Tkg.60</code>, <code>BPK001</code>, <code>C.2</code>, <code>C.13</code>, <code>C.29A</code>, สถานีป้อมพระจุลฯ)",
                "inclusion_type": "ข้อมูลตรวจวัดจริงโดยตรง",
                "confidence": "สูงมาก (>95%)",
            },
            {
                "category": "ความลาดชันผิวน้ำชลศาสตร์",
                "detail": "คำนวณจากผลต่างระดับน้ำจริงเทียบระยะทางตามลำน้ำ สะท้อนความดันขับเคลื่อนการไหลแท้จริง ไม่ใช่ความลาดชันเฉลี่ยของภูมิประเทศ",
                "inclusion_type": "คำนวณจากผลต่างระดับสถานี",
                "confidence": "สูงมาก (>95%)",
            },
            {
                "category": "ปริมาณน้ำฝนสะสมเฉพาะพื้นที่",
                "detail": "คำนวณมวลน้ำฝนตกตรงลงบนพื้นที่แอ่งก้นกระทะองครักษ์ 68 มม. เหนือพื้นที่น้ำท่วมขัง 50 ตร.กม. คิดเป็นมวลน้ำฝน 3.40 ล้าน ลบ.ม.",
                "inclusion_type": "สมดุลมวลน้ำรวมเฉพาะแอ่ง",
                "confidence": "ปานกลาง-สูง (±15%)",
            },
            {
                "category": "ระดับความสูงอ้างอิงและรูปตัดตามยาว",
                "detail": "ระดับดินเดิมและระดับธรณีคลองหรือคันดิน จากแบบตัดตามยาวของกรมชลประทานและหมุดระดับสถานี (องครักษ์ 1.0–2.5 ม., บางน้ำเปรี้ยว 2.5–3.0 ม.รทก.)",
                "inclusion_type": "ระดับอ้างอิงหมุดสำรวจและรูปตัดคลอง",
                "confidence": "สูง (±0.2 ม.)",
            },
            {
                "category": "ขอบเขตน้ำทะเลหนุนปากอ่าว",
                "detail": "ช่วงแกว่งตัวของน้ำขึ้น-น้ำลงจริง 2.48 ม. ที่ปากแม่น้ำบางปะกง (<code>BPK001</code>) และป้อมพระจุลฯ อ่าวไทย",
                "inclusion_type": "เงื่อนไขขอบเขตวัดจริง",
                "confidence": "สูงมาก (>95%)",
            },
        ],
        "sources_to_be_included": [
            {
                "category": "น้ำท่ากระจายตัวตามลุ่มน้ำย่อย",
                "needed_model": "แบบจำลองฝน-น้ำท่ากระจายตัว (<code>SCS-CN</code> / <code>Green-Ampt</code>) ร่วมกับกริดฝนเรดาร์",
                "importance": "เพื่อคำนวณมวลน้ำหลากข้างลำน้ำจากแปลงนาและทุ่งเกษตรกรรมสองฝั่งคลองย่อยเข้าสู่ลำคลอง",
            },
            {
                "category": "แบบจำลองภูมิประเทศ 2 มิติความละเอียดสูง",
                "needed_model": "แบบจำลองชลศาสตร์ 2 มิติ (<code>HEC-RAS 2D</code>) บนกริดความสูงภูมิประเทศหรือ <code>LiDAR DTM</code>",
                "importance": "เพื่อจำลองการบ่าล้นข้ามคันถนน เช่น ถนนรังสิต–นครนายก ที่ทำหน้าที่เป็นคันกั้นน้ำธรรมชาติ",
            },
            {
                "category": "ประวัติเปิดบาน ปตร. รายชั่วโมง และบันทึกเดินเครื่องสูบน้ำจริง",
                "needed_model": "ตารางประวัติรายชั่วโมงจากการขอข้อมูลข่าวสารราชการ (<code>FOI-01</code> และ <code>FOI-02</code>)",
                "importance": "ปัจจุบันระบบออนไลน์แสดงสถานะเครื่องสูบน้ำเป็นค่าว่างทั้ง 2,315 ปตร. ทั่วประเทศ จึงต้องใช้ค่าสูบน้ำจากการจำลองสมดุลน้ำแทน",
            },
            {
                "category": "คลื่นน้ำขึ้น-น้ำลงแบบพลวัต",
                "needed_model": "สมการคลื่นน้ำหลากแบบไม่คงที่ (<code>Saint-Venant 1D/2D Unsteady Flow</code>) เชื่อมโยงปากอ่าวสู่ตอนใน",
                "importance": "เพื่อคำนวณระยะทางและช่วงเวลาที่ยอดคลื่นหนุนย้อนกลับขึ้นมาถึงฉะเชิงเทรา (กม.98) และปากเกร็ด (กม.175)",
            },
        ],
        "accuracy_summary": [
            {
                "aspect": "ทิศทางการไหลสุทธิและสภาวะปิดกั้นชลศาสตร์",
                "accuracy_level": "สูงมาก (>95%)",
                "basis": "เป็นข้อเท็จจริงเชิงประจักษ์จากความต่างระดับน้ำจริงผิวน้ำที่วัดได้ — เมื่อปลายทางบางน้ำเปรี้ยว (+2.56 ม.) สูงกว่าต้นทางองครักษ์ (+2.35 ม.) น้ำไม่สามารถไหลลงใต้ตามแรงโน้มถ่วงได้จริงตามกฎฟิสิกส์",
            },
            {
                "aspect": "ปริมาตรสมดุลน้ำสุทธิ (สมดุลน้ำสุทธิเพิ่มขึ้น +4.09 ล้าน ลบ.ม./วัน)",
                "accuracy_level": "ปานกลาง-สูง (±15%)",
                "basis": "คุมด้วยอัตราการเพิ่มขึ้นของระดับน้ำท่วมขังและพื้นที่น้ำท่วมจริง สอดคล้องกับมวลน้ำปล่อยจากลำน้ำนครนายก",
            },
            {
                "aspect": "ความเร็วชลศาสตร์และเวลาเดินทาง",
                "accuracy_level": "ระดับวิศวกรรม (±20–30%)",
                "basis": "แปรผันตามสัมประสิทธิ์ความขรุขระแมนนิ่งจริง สิ่งกีดขวางวัชพืช และการตกตะกอนในลำคลองชั้นล่าง",
            },
        ],
    }


def run_all_corridors():
    c1 = build_corridor_1_khundan_to_gulf()
    c2 = build_corridor_2_pasak_to_gulf()
    c3 = build_corridor_3_chaophraya_to_gulf()
    acc = build_accuracy_and_boundary_assessment()

    res = {
        "summary": "การวิเคราะห์เวกเตอร์ชลศาสตร์และเวลาเดินทางน้ำหลากจากแหล่งต้นน้ำ (เขื่อน) สู่ปากอ่าวไทย 3 ระเบียงหลัก",
        "corridor_1_khundan": c1,
        "corridor_2_pasak": c2,
        "corridor_3_chaophraya": c3,
        "boundary_and_accuracy_assessment": acc,
    }

    summary_path = ROOT / "analysis/goal7/dam_to_gulf_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(f"✅ บันทึกผลวิเคราะห์ลง {summary_path.name} สำเร็จ")

    if CANONICAL_PATH.exists():
        with open(CANONICAL_PATH, encoding="utf-8") as f:
            cdata = json.load(f)
        cdata["dam_to_gulf_corridors"] = res
        with open(CANONICAL_PATH, "w", encoding="utf-8") as f:
            json.dump(cdata, f, ensure_ascii=False, indent=1)
        print(f"✅ บันทึกผลวิเคราะห์ 3 ระเบียงเขื่อนสู่อ่าวไทยลง {CANONICAL_PATH.name} สำเร็จ")

    return res


def main():
    print("=" * 75)
    print("🌊 การวิเคราะห์เส้นทางชลศาสตร์และเวกเตอร์การไหลจากเขื่อนสู่ปากอ่าวไทย")
    print("=" * 75)
    res = run_all_corridors()
    for key in ["corridor_1_khundan", "corridor_2_pasak", "corridor_3_chaophraya"]:
        c = res[key]
        print(f"\n📍 {c['title']} (ระยะทางรวม {c['total_length_km']} กม. | เวลาเดินทาง {c['total_travel_days']} วัน / {c['total_travel_hours']} ชม.)")
        for s in c["segments"]:
            print(f"   • {s['segment_name']:<42} : {s['dist_km']:>5.1f} กม. | ต่าง {s['head_diff_m']:>+6.2f} ม. ({s['slope_cm_per_km']:>+7.2f} ซม./กม.) | v={s['velocity_ms']:.2f} ม./วิ | ใช้เวลา {s['travel_hours']:>5.1f} ชม.")
    print("=" * 75)


if __name__ == "__main__":
    main()
