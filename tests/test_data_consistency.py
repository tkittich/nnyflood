"""tests/test_data_consistency.py — การตรวจสอบความสม่ำเสมอของข้อมูลและสัญญาตัวเลขทั้งคลัง (Unified Data Consistency Gate)

ครอบคลุม:
1. การห้ามปรากฏของตัวเลขและข้อความที่ถูกแทนที่/ปลดประจำการแล้ว (Global Retired Ledger) ทั่วทุกรายงานและเอกสาร
2. การตรวจสอบโครงสร้างระงับข้อขัดแย้งหลายแหล่งข้อมูล (Truth Discovery & Reconciliation Schema) ใน canonical.json
3. การป้องกันพฤติกรรม Defensive Gap (การอ้างว่าไม่มีที่มาเพื่อแก้ตัวแทนการสืบค้น หรือการคำนวณลอย ๆ)
4. การตรวจสอบสัญญาความสอดคล้องระหว่างภาพประกอบและคำบรรยายใต้ภาพ (Asset-Caption Integrity)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

# รายงานผลลัพธ์ทั้งหมด
REPORT_FILES = sorted((ROOT / "report").glob("*.html"))

# เอกสารเผยแพร่และคู่มือหลัก
DOC_FILES = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "HANDOFF.md",
    *sorted((ROOT / "docs").glob("*.md")),
]

# สคริปต์ตัวสร้างรายงาน
BUILDER_FILES = sorted((ROOT / "report").glob("*.py"))

# บัญชีคำ/ตัวเลขที่ปลดประจำการส่วนกลาง (Global Retired Ledger)
GLOBAL_RETIRED_PATTERNS = [
    ("ความกว้างท้องคลองนี้ยังไม่มีที่มาอ้างอิง", "ข้อความแก้ตัวลอย — ท้องคลองมีระบุใน EIA 54.5 ม. และแบบร่าง 51.0 ม."),
    ("ปริมาตรรวม 55.4 ล้าน ลบ.ม. ที่ใช้ข้างต้น ไม่มีที่มาอ้างอิง", "ข้อความแก้ตัวลอย — ตัวเลข 55.4 มาจากเอกสารเก่าที่คำนวณผิด"),
    ("ความจุเก็บกัก 55.4", "ตัวเลขเก่าที่คำนวณผิด (EIA ระบุ 68.5 ล้าน ลบ.ม. รวม และ 52.3 ล้าน ลบ.ม. ใช้งาน)"),
    ("ท้องคลองกว้าง 48.0", "ตัวเลขผิดที่เลิกใช้ (EIA ระบุ 54.5 ม.)"),
    ("48.0 ม. (ลาดข้าง", "ตัวเลขผิดที่เลิกใช้"),
    ("แผนที่ตำแหน่งอาคารบังคับน้ำ สถานีโทรมาตร และจุดตัดทางน้ำสำคัญตามแนวคลอง", "คำบรรยายสัญญาเกินจริง — ในแผนที่ไม่มีสถานีโทรมาตร"),
    ("81.3 ตร.กม.", "พื้นที่น้ำท่วมเก่าที่ยังไม่ได้คำนวณจริง"),
    ("18 ก.พ. 2562", "วันที่หนังสือราชการที่คลาดเคลื่อน (ของจริงคือ 14 ก.พ. 2562)"),
    ("21.0 ลลบ.ม.", "ความจุเก็บกักน้ำตายที่คำนวณผิดหลักเรขาคณิต (ของจริงคือ 13.9–14.4 ลลบ.ม.)"),
]


def test_global_retired_ledger_absent_in_all_reports():
    """ตัวเลขและข้อความที่ปลดประจำการต้องไม่ปรากฏในรายงาน HTML ทุกฉบับ"""
    failures = []
    for r_path in REPORT_FILES:
        txt = r_path.read_text(encoding="utf-8")
        # ตัดภาพ base64 ออกเพื่อป้องกัน false positive
        clean_txt = re.sub(r"data:[a-zA-Z0-9/+-]+;base64,[A-Za-z0-9+/=]+", "", txt)
        for pattern, reason in GLOBAL_RETIRED_PATTERNS:
            if pattern in clean_txt:
                failures.append(f"{r_path.name}: พบข้อความปลดประจำการ '{pattern}' ({reason})")

    assert not failures, f"พบข้อความที่เลิกใช้ค้างในรายงาน ({len(failures)} จุด):\n" + "\n".join(failures)


def test_global_retired_ledger_absent_in_all_docs():
    """ตัวเลขและข้อความที่ปลดประจำการต้องไม่ปรากฏในเอกสารทางการ (docs/*.md, README, HANDOFF)
    ยกเว้นเอกสารว่าด้วยการจัดการความสอดคล้อง (DATA_CONSISTENCY_WORKFLOW.md) หรือผลรีวิวอิสระที่จดประวัติไว้
    """
    failures = []
    exempt_docs = {
        "DATA_CONSISTENCY_WORKFLOW.md",
        "READER_CHANGELOG.md",
    }
    for d_path in DOC_FILES:
        if d_path.name in exempt_docs:
            continue
        txt = d_path.read_text(encoding="utf-8")
        for pattern, reason in GLOBAL_RETIRED_PATTERNS:
            if pattern in txt:
                failures.append(f"{d_path.relative_to(ROOT)}: พบข้อความปลดประจำการ '{pattern}' ({reason})")

    assert not failures, f"พบข้อความที่เลิกใช้ค้างในเอกสาร ({len(failures)} จุด):\n" + "\n".join(failures)


def test_no_defensive_unreferenced_claims_in_reports():
    """ห้ามใช้ข้อความแก้ตัวแบบ defensive gap ('ไม่มีที่มาอ้างอิงในคลังข้อมูล') ในรายงานสาธารณะ
    หากตัวเลขใดไม่มีที่มา ต้องไม่นำมาคำนวณ หรือต้องบันทึกเป็น FOI gap อย่างเป็นทางการใน gaps.json
    """
    forbidden_defensive_phrases = [
        "ไม่มีที่มาอ้างอิงในคลังข้อมูล",
        "ยังไม่มีที่มาอ้างอิง",
        "ไม่พบที่มาอ้างอิงในระบบ",
    ]
    failures = []
    for r_path in REPORT_FILES:
        txt = r_path.read_text(encoding="utf-8")
        clean_txt = re.sub(r"data:[a-zA-Z0-9/+-]+;base64,[A-Za-z0-9+/=]+", "", txt)
        for phrase in forbidden_defensive_phrases:
            if phrase in clean_txt:
                failures.append(f"{r_path.name}: มีข้อความ defensive gap: '{phrase}'")

    assert not failures, f"พบข้อความแก้ตัวลอยในรายงาน:\n" + "\n".join(failures)


def test_canonical_reconciliation_schema_valid():
    """โครงสร้าง reconciled_parameters ใน canonical.json ต้องปฏิบัติตามมาตรฐาน Truth Discovery"""
    goal7_can = ROOT / "analysis/goal7/canonical.json"
    if not goal7_can.exists():
        pytest.skip("goal7 canonical.json not found")

    data = json.loads(goal7_can.read_text(encoding="utf-8"))
    assert "reconciled_parameters" in data, "goal7 canonical.json ขาด reconciled_parameters"
    rp = data["reconciled_parameters"]

    for param_name, param_info in rp.items():
        assert "resolution" in param_info, f"{param_name}: ขาดเหตุผลการระงับข้อขัดแย้ง (resolution)"
        assert "variants" in param_info, f"{param_name}: ขาดรายการตัวเลขต่างแหล่ง (variants)"
        assert isinstance(param_info["variants"], (dict, list)), f"{param_name}: variants ต้องเป็น dict หรือ list"
        assert len(param_info["variants"]) >= 2, f"{param_name}: variants ต้องมีอย่างน้อย 2 แหล่งเพื่อเทียบเคียง"

        # ตรวจสอบว่าทุก variant มี source หรือ reason (กรณี retired)
        variants_iterable = param_info["variants"].values() if isinstance(param_info["variants"], dict) else param_info["variants"]
        for var in variants_iterable:
            assert "source" in var or "reason" in var, f"{param_name}: variant ต้องระบุ source หรือ reason"
            assert any(isinstance(v, (int, float)) for v in var.values()), (
                f"{param_name}: variant ต้องมีค่าตัวเลขอย่างน้อยหนึ่งค่า"
            )


def test_asset_caption_truthfulness_contract():
    """คำบรรยายใต้ภาพต้องไม่สัญญาชั้นข้อมูลที่แผนที่ไม่ได้แสดง"""
    # ตรวจสอบแผนที่แนวคลองเจ้าพระยา 2 ในรายงานฉบับประชาชนและวิชาการ
    cp2_public = ROOT / "report/คลองเจ้าพระยา2_ประชาชน.html"
    cp2_academic = ROOT / "report/คลองเจ้าพระยา2_วิชาการ.html"
    for r_path in (cp2_public, cp2_academic):
        if not r_path.exists():
            continue
        txt = r_path.read_text(encoding="utf-8")
        # ห้ามมีคำสัญญาว่าแผนที่มี 'สถานีโทรมาตร' หากไม่มีจุดสถานีโทรมาตรบนแผนที่จริง
        assert "แผนที่ตำแหน่งอาคารบังคับน้ำ สถานีโทรมาตร" not in txt, (
            f"{r_path.name}: ผิดสัญญา Asset-Caption — คำบรรยายสัญญาสถานีโทรมาตรที่ไม่มีในภาพ"
        )


def test_pillar1_canonical_inward_contracts():
    """สัญญาข้อมูลขาเข้าเสาที่ 1 (นครนายก) ต้องผ่านเกณฑ์ความสมเหตุสมผลทางชลศาสตร์"""
    can_path = ROOT / "analysis/canonical_numbers.json"
    assert can_path.exists(), "ไม่พบ analysis/canonical_numbers.json"
    data = json.loads(can_path.read_text(encoding="utf-8"))["values"]

    # 1. สัญญาสัดส่วนสาเหตุและสมดุลมวลน้ำ (Attribution Mass Balance)
    ds = data["dam_share"]
    assert round(ds["p1_pct"]) == 12, "สัดส่วนเขื่อน P1 ต้องเป็น 12%"
    assert round(100.0 - ds["p1_pct"]) == 88, "สัดส่วนฝน P1 ต้องเป็น 88%"
    assert round(ds["p2_pct"]) == 60, "สัดส่วนเขื่อน P2 ต้องเป็น 60%"
    assert round(100.0 - ds["p2_pct"]) == 40, "สัดส่วนฝน P2 ต้องเป็น 40%"

    # 2. สัญญาระดับน้ำและค่าอ้างอิงความสูง (Water Level & Datum Consistency)
    lv = data["levels"]
    assert lv["peak_gauge_m"] > lv["bankfull_gauge_m"], "ระดับน้ำสูงสุดต้องสูงกว่าระดับเริ่มล้นตลิ่ง"
    assert abs(lv["peak_gauge_m"] - lv["datum_offset_m"] - 7.64) < 0.01, "ระดับ ม.รทก. ต้องตรงเกจหัก datum"

    # 3. สัญญาชลศาสตร์ Ny.1B (1D Hydraulics Monotonicity)
    xs = data["ny1b_cross_section"]
    assert xs["bankfull_q_low_m3s"] < xs["bankfull_q_m3s"] < xs["bankfull_q_high_m3s"], (
        "ช่วงความไม่แน่นอนของอัตราไหลต้องเรียงจากต่ำไปสูง"
    )


def test_pillar2_canonical_inward_contracts():
    """สัญญาข้อมูลขาเข้าเสาที่ 2 (6 ลุ่มน้ำและ 24 เขื่อน) ต้องผ่านเกณฑ์สถิติและการหน่วงน้ำ"""
    can_path = ROOT / "analysis/goal6/canonical.json"
    assert can_path.exists(), "ไม่พบ analysis/goal6/canonical.json"
    data = json.loads(can_path.read_text(encoding="utf-8"))

    # 1. สัญญาฝน (Rain Bounds)
    rn = data["rain_national"]
    assert rn["top3_stations_7d"] <= rn["n_stations"], "สถานีฝน top 3 ต้องไม่เกินจำนวนทั้งหมด"
    assert rn["top3_cells_7d"] <= rn["n_cells"], "ช่องกริดฝน top 3 ต้องไม่เกินจำนวนทั้งหมด"

    # 2. สัญญาเขื่อนป่าสักชลสิทธิ์ 24 ปี (Pasak Surcharge Contracts)
    ps = data["pasak_24y_baseline"]
    assert ps["over_normal_years"] <= ps["years_analyzed"], "ปีที่เกินปกติป่าสักต้องไม่เกินปีที่วิเคราะห์"
    assert ps["over_1000mcm_years"] <= ps["over_normal_years"], (
        "ปีที่แตะ 1,000 ล้าน ลบ.ม. ต้องเป็นสับเซตของปีที่เกินระดับปกติ"
    )
    assert ps["record_peak_mcm"] >= ps["y2569_peak_mcm"], "สถิติน้ำสูงสุดตลอดกาลต้องไม่ต่ำกว่าน้ำสูงสุดปี 2569"

    # 3. สัญญาโทรมาตรปากแม่น้ำและคุณภาพน้ำ (Estuary & Salinity Contracts)
    et = data["estuary_tide"]
    assert et["c12_peak_m"] > et["c12_trough_min_m"], "ระดับน้ำขึ้นสูงสุดต้องสูงกว่าระดับน้ำลงต่ำสุด"
    es = data["estuary_salinity"]
    assert es["samlae_salinity_min_gl"] <= es["samlae_salinity_max_gl"] <= es["samlae_warning_threshold_gl"], (
        "ความเค็มสำแลต้องอยู่ในช่วงปกติและไม่เกินเกณฑ์เตือนภัย"
    )


def test_pillar3_canonical_inward_contracts():
    """สัญญาข้อมูลขาเข้าเสาที่ 3 (คลองเจ้าพระยา 2) ต้องผ่านเกณฑ์เรขาคณิตและความจุเก็บกัก"""
    can_path = ROOT / "analysis/goal7/canonical.json"
    assert can_path.exists(), "ไม่พบ analysis/goal7/canonical.json"
    data = json.loads(can_path.read_text(encoding="utf-8"))

    rp = data["reconciled_parameters"]
    # 1. สัญญาความกว้างท้องคลอง (Geometric Trapezoidal Derivation)
    assert rp["canal_bed_width"]["canonical_value_m"] == 54.5, "ท้องคลองต้องเป็น 54.5 ม. ตามหน้าตัด EIA"

    # 2. สัญญาความจุเก็บกัก (Total = Active + Dead)
    cs = rp["canal_storage"]
    assert cs["canonical_total_mcm"] == round(cs["canonical_active_mcm"] + cs["canonical_dead_mcm"], 1), (
        "ความจุรวมต้องเท่ากับความจุใช้การบวกความจุก้นคลอง"
    )


def test_figure_asset_caption_contract_raises_on_unrendered_promise(tmp_path):
    """ฟังก์ชัน figure() ต้อง raise ValueError ทันทีหากคำบรรยายสัญญาชั้นข้อมูลที่ภาพไม่ได้ประกาศ"""
    sys.path.insert(0, str(ROOT / "report"))
    from goal6_reportlib import figure
    dummy_img = tmp_path / "dummy.png"
    dummy_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

    # สัญญา 'สถานีโทรมาตร' โดยไม่มี layers ต้องล้ม
    with pytest.raises(ValueError, match="Asset-Caption Breach"):
        figure(dummy_img, "แผนที่ตำแหน่งอาคารบังคับน้ำ สถานีโทรมาตร และจุดตัด")

    # ประกาศ layers=['telemetry'] ต้องผ่าน
    html = figure(dummy_img, "แผนที่ตำแหน่งอาคารบังคับน้ำ สถานีโทรมาตร และจุดตัด", layers=["telemetry"])
    assert "data:image/png;base64" in html


