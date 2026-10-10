"""ตรวจกติกาภาษารายงานที่ 3 (ห้ามทับศัพท์) — รันหลังสร้าง แยกจาก builder (กันวนซ้ำ)"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "report/ระลอกปลายกย2569.html"
DRAFT4 = ROOT / "report/ชุดเทียบมาตรฐาน2554.html"

BANNED = ["พีค", "น้ำพีค", "attribution", "คาลิเบรต", "เทมเพลต",
          "rule curve", "rulecurve", "critical", "datum", "baseline",
          "config", "scenario", "workflow", "threshold"]


def test_report3_exists():
    assert DRAFT.exists(), "ร่างรายงานที่ 3 ยังไม่ถูกสร้าง — รัน python report/goal6_build_report3_draft.py ก่อน"


def test_report3_no_banned_terms():
    h = DRAFT.read_text(encoding="utf-8")
    body = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    body = re.sub(r"<code>.*?</code>", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    found = {w: len(re.findall(w, body, flags=re.IGNORECASE)) for w in BANNED}
    hits = {k: v for k, v in found.items() if v}
    assert not hits, f"พบคำทับศัพท์/ศัพท์เทคนิคที่ต้องแทน: {hits} — แก้ใน goal6_build_report3_draft.py"


def test_report4_exists():
    assert DRAFT4.exists(), "ร่างรายงานที่ 4 ยังไม่ถูกสร้าง — รัน python report/goal6_build_report4_draft.py ก่อน"


def test_report4_no_banned_terms():
    h = DRAFT4.read_text(encoding="utf-8")
    body = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    body = re.sub(r"<code>.*?</code>", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    found = {w: len(re.findall(w, body, flags=re.IGNORECASE)) for w in BANNED}
    hits = {k: v for k, v in found.items() if v}
    assert not hits, f"รายงานที่ 4 พบคำทับศัพท์: {hits}"


def test_report4_has_tldr_and_context():
    h = DRAFT4.read_text(encoding="utf-8")
    assert "สรุปสั้น (อ่าน 2 นาที)" in h, "รายงานที่ 4 ต้องมี TLDR"
    assert "บริบทสำหรับผู้อ่านใหม่" in h, "รายงานที่ 4 ต้องมีบริบทสำหรับผู้อ่านใหม่"


def test_report3_has_definitions():
    h = DRAFT.read_text(encoding="utf-8")
    assert "อ่านจบในตัวเอง" in h, "รายงานต้องมีบทนำบอกว่าอ่านจบในตัวเอง"
    assert "เส้นกำกับระดับน้ำ" in h, "รายงานต้องนิยามคำ 'เส้นกำกับระดับน้ำ' (แทน rule curve)"


def test_report3_has_tldr():
    h = DRAFT.read_text(encoding="utf-8")
    assert "สรุปสั้น (อ่าน 2 นาที)" in h, "รายงานต้องมี TLDR อ่าน 2 นาที"


def test_report3_has_context_intro():
    h = DRAFT.read_text(encoding="utf-8")
    assert "บริบทสำหรับผู้อ่านที่ไม่เคยอ่านรายงานนครนายก" in h, "รายงานต้องมีบริบทสำหรับผู้อ่านใหม่"
