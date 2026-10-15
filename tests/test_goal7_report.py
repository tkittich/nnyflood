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
