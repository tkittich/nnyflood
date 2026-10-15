"""ตรวจรายงานที่ 5 (คลองเจ้าพระยา2) ทั้ง 2 ฉบับ — รันหลังสร้าง แยกจาก builder (กันวนซ้ำ)
โครงเดียวกับ test_report3_language: TLDR · บริบท · อ่านจบในตัวเอง · ห้ามทับศัพท์ · ภาพประกอบ · ตัวเลขตรง canonical"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "report/คลองเจ้าพระยา2_ประชาชน.html"
ACADEMIC = ROOT / "report/คลองเจ้าพระยา2_วิชาการ.html"
CAN = ROOT / "analysis/goal7/canonical.json"
BOTH = [PUBLIC, ACADEMIC]
BANNED = ["พีค", "น้ำพีค", "attribution", "คาลิเบรต", "เทมเพลต", "rule curve", "rulecurve",
          "critical", "datum", "baseline", "config", "scenario", "workflow", "threshold"]


def _body(p):
    h = p.read_text(encoding="utf-8")
    b = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    b = re.sub(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]+", " ", b)
    b = re.sub(r"<code>.*?</code>", " ", b, flags=re.S)
    return h, re.sub(r"<[^>]+>", " ", b)


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_exists(p):
    assert p.exists(), f"ยังไม่ได้สร้าง {p.name} — รัน report/goal7_build_public.py / goal7_build_academic.py"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_no_banned_terms(p):
    _, b = _body(p)
    hits = {w: len(re.findall(w, b, flags=re.I)) for w in BANNED}
    hits = {k: v for k, v in hits.items() if v}
    assert not hits, f"พบคำทับศัพท์: {hits}"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_structure(p):
    h, _ = _body(p)
    assert "สรุปสั้น (อ่าน 2 นาที)" in h
    assert "บริบทสำหรับผู้อ่านใหม่" in h
    assert "อ่านจบในตัวเอง" in h
    assert h.count("<figure>") >= 4, "ต้องมีภาพประกอบอย่างน้อย 4 ภาพ"


def test_public_has_qa():
    h, _ = _body(PUBLIC)
    assert "ถาม 1" in h and "ถาม 6" in h, "ฉบับประชาชนต้องมีหัวข้อถาม–ตอบ"


def test_academic_has_method_and_appendix():
    h, _ = _body(ACADEMIC)
    for w in ("ข้อมูลและวิธีการ", "ภาคผนวก ก.", "ภาคผนวก ข.", "ภาคผนวก ค.", "คำถามที่ลงทะเบียนไว้ก่อนดูผล"):
        assert w in h, f"ฉบับวิชาการต้องมี: {w}"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_numbers_match_canonical(p):
    c = json.loads(CAN.read_text(encoding="utf-8"))
    _, b = _body(p)
    nn = c["structures"]["nakhonnayok"]
    assert f"{nn['n_siphon']}" in b
    assert f"{c['c2']['years']['2026']['peak_daily_m3s']:,}" in b
    assert f"{c['corridor_area']['rai']['mixed']:,}" in b
    assert f"{c['structures']['n_total']}" in b


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_alignment_caveat_and_tiers(p):
    _, b = _body(p)
    assert "ไม่ใช่แนวทางการ" in b or "ไม่ใช่ข้อมูลทางการ" in b, "ต้องระบุว่าแนวคลองไม่เป็นทางการ"
    assert "ชั้น A" in b and "ชั้น B" in b


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_concerns_listed_as_claims_not_facts(p):
    c = json.loads(CAN.read_text(encoding="utf-8"))
    _, b = _body(p)
    assert len(c["concerns"]) == 13
    assert "ผู้ยื่นระบุ" in b, "ข้อห่วงกังวลต้องระบุเป็นข้อความของผู้ยื่น ไม่ใช่ข้อเท็จจริง"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_no_person_blaming(p):
    _, b = _body(p)
    for w in ("ทุจริต", "ผลาญงบ", "ผิดพลาดโดยเจตนา", "ต้องรับผิดชอบ"):
        assert w not in b


QA = ROOT / "report/คลองเจ้าพระยา2_ถามตอบสั้น.html"


def test_qa_exists_and_structure():
    assert QA.exists(), "ยังไม่ได้สร้างฉบับถาม–ตอบสั้น — รัน report/goal7_build_qa.py"
    h, b = _body(QA)
    assert "สรุปสั้น (อ่าน 2 นาที)" in h and "บริบทสำหรับผู้อ่านใหม่" in h and "อ่านจบในตัวเอง" in h
    assert h.count("<figure>") >= 2
    assert h.count("class='qa'") >= 10, "ต้องมีคำถามอย่างน้อย 10 ข้อ"
    for w in ("รู้แล้ว", "ยังไม่รู้", "ขอได้จาก"):
        assert w in b
    hits = {w: len(re.findall(w, b, flags=re.I)) for w in BANNED}
    assert not {k: v for k, v in hits.items() if v}, "พบคำทับศัพท์"


def test_qa_numbers_match_canonical():
    c = json.loads(CAN.read_text(encoding="utf-8"))
    _, b = _body(QA)
    nn = next(r for r in c["eia_land"]["rows"] if r["province"] == "นครนายก")
    assert f"{nn['rai']:,}" in b and f"{nn['owners']:,}" in b
    assert str(c["eia_econ"]["earlier_2560"]["bcr"]) in b
    assert "ไม่ใช่แนวทางการ" in b


# ---- เพิ่ม 15 ต.ค. 69: ความสูงคันตามข้อมูล · ภาพประกอบ · คำถามเพิ่ม · กฎหมาย/PDPA ----
QA_FILE = ROOT / "report/คลองเจ้าพระยา2_ถามตอบสั้น.html"


def test_embankment_uses_documented_heights_only():
    c = json.loads(CAN.read_text(encoding="utf-8"))
    ids = [x["id"] for x in c["embankment"]["cases"]]
    assert ids == ["eia_lo", "eia_hi"], "ต้องใช้เฉพาะความสูงคันตามรูปตัดตามยาว (ไม่มีกรณีสมมติ 6/7 ม.)"
    top = max(x["crest_above_ground_m"] for x in c["embankment"]["cases"])
    assert top <= 4.8
    for p in (PUBLIC, ACADEMIC, QA_FILE):
        _, b = _body(p)
        assert "คันสูง 6 หรือ 7" not in b and "สมมติคันสูง 6" not in b


def test_new_figures_and_questions():
    pub = PUBLIC.read_text(encoding="utf-8")
    aca = ACADEMIC.read_text(encoding="utf-8")
    qa = QA_FILE.read_text(encoding="utf-8")
    assert pub.count("<figure>") >= 9 and aca.count("<figure>") >= 10 and qa.count("<figure>") >= 5
    assert qa.count("class='qa'") >= 24, "ถาม–ตอบต้องมีอย่างน้อย 24 ข้อ (เพิ่มประตู/รอยเลื่อน/ทางเลือก/การดูแล/ข้อเสนอ)"
    for w in ("ประตูจะเปิด–ปิดอย่างไร", "รอยเลื่อนองครักษ์", "ทางเลือกอื่น", "ใครดูแลคันและท่อ", "ก่อนกันยายน 2569", "ใช้เวลานานเท่าไร", "ข้ามคลองได้ที่ไหน", "คุ้มค่าก่อสร้าง", "หอย"):
        assert w in qa


@pytest.mark.parametrize("p", [PUBLIC, ACADEMIC, QA_FILE], ids=["ประชาชน", "วิชาการ", "ถามตอบ"])
def test_legal_pdpa_no_persons_no_blame(p):
    """กฎหมายหมิ่นประมาท + PDPA (docs/LEGAL_REVIEW.md §4): ไม่มีชื่อบุคคลธรรมดา/เบอร์/ลิงก์โปรไฟล์ · ไม่ตั้งกรอบหาคนผิด"""
    _, b = _body(p)
    assert not re.search(r"(?<![ก-๙])(?:นางสาว|นาย|นาง)(?!ก|อำเภอ)[ก-๙]{2,}\s+[ก-๙]{2,}", b), "พบชื่อบุคคลธรรมดา"
    assert not re.search(r"0\d{1,2}[- ]?\d{3}[- ]?\d{4}", b), "พบเบอร์โทร"
    for w in ("ทุจริต", "โกง", "เจตนา", "ละเลย", "หลอกลวง", "ใครผิด", "ใครรับผิด", "ผลประโยชน์ทับซ้อน"):
        assert w not in b, f"พบถ้อยคำกล่าวหา: {w}"


def test_profile_from_drawing_consistent():
    """รูปตัดตามยาว (รูปที่ 2.3.2-9): ค่าที่อ่านต้องสอดคล้องกับค่าที่รายงานระบุ (สันคันสูงสุดเหนือพื้น 4.8 ม. · ระดับน้ำเหนือพื้น 1.0–3.3 ม.)"""
    c = json.loads(CAN.read_text(encoding="utf-8"))
    nn = c["eia_profile"]["nn_reach"]
    assert abs(nn["crest_above_ground_max_m"] - 4.8) <= 0.1
    assert 1.0 <= nn["water_above_ground_min_m"] and nn["water_above_ground_max_m"] <= 3.4
    rows = {r["km"]: r for r in c["eia_profile"]["rows"]}
    # ค่ากำกับบนรูป: กม.75 สันคัน +5.36 น้ำ +3.86
    assert abs(rows[75]["crest_m"] - 5.36) <= 0.02 and abs(rows[75]["water_m"] - 3.86) <= 0.02
    assert c["eia_profile"]["connecting_canal"]["km"] == [39.8, 51.5]


def test_options_screening_present_and_labeled():
    c = json.loads(CAN.read_text(encoding="utf-8"))
    o = c["options"]
    assert [w["water_above_ground_m"] for w in o["wide_canal"]] == [3.3, 2.0, 1.0, 0.0]
    assert o["wide_canal"][0]["land_vs_now_pct"] == 0 and abs(o["wide_canal"][0]["bottom_m"] - 51) <= 2, "ฐานเทียบต้องตรงหน้าตัดตามรายงาน"
    assert len(c["basins_2569"]["rows"]) == 17
    _, b = _body(ACADEMIC)
    assert "ข้อเสนอของผู้จัดทำ" in b and "ไม่ใช่ข้อมูลทางการ" in b
    _, b2 = _body(PUBLIC)
    assert "ข้อเสนอของผู้จัดทำ" in b2
