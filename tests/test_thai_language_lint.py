"""การตรวจภาษาไทยเชิงระบบ (Linter & Regression Guard) — รันใน pytest หลังสร้างเสร็จ
ครอบคลุม:
1. ทะเบียนคำผิดที่เคยพบ (Typo Registry: แป้นพิมพ์เกษมณี / คำพ้องเสียง / ทับศัพท์)
2. ป้องกันคำซ้อน/คำชนจากการ replace (Collision & Stutter Scanner: ระบบระบบ, แสงอาทิตย์เซลล์ ฯลฯ)
3. ตรวจสอบความถูกต้องของตารางคำศัพท์ PLAIN_TH (เรียงตามความยาว และคำประสมต้องมาก่อนคำเดี่ยว)
4. ตรวจสอบความสอดคล้องของตัวเลข/สารบัญข้ามเอกสาร (Cross-doc consistency: README, index.html, HANDOFF)
5. ตรวจคำต้องห้ามครอบคลุมรายงานทั้ง 6 ฉบับ
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "report"))
from goal6_reportlib import _text_segments  # noqa: E402
from goal7_common import PLAIN_TH  # noqa: E402

ALL_REPORTS = [
    ROOT / "report/น้ำท่วมนครนายก2569_ประชาชน.html",
    ROOT / "report/น้ำท่วมนครนายก2569_วิชาการ.html",
    ROOT / "report/ระลอกปลายกย2569.html",
    ROOT / "report/ชุดเทียบมาตรฐาน2554.html",
    ROOT / "report/คลองเจ้าพระยา2_ประชาชน.html",
    ROOT / "report/คลองเจ้าพระยา2_วิชาการ.html",
    ROOT / "report/สมุดปกขาว_เจ้าพระยา2.html",
]

DOC_FILES = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "HANDOFF.md",
    *sorted((ROOT / "docs").glob("*.md")),
]

BUILDER_SCRIPTS = sorted((ROOT / "report").glob("*.py"))

KNOWN_TYPOS = [
    "ล้าสมณี",   # ผิดจาก ล้าสมัย
    "ต้นฉบูล",   # ผิดจาก ต้นฉบับ
    "จุเล็ก",    # ผิดจาก จุดเล็ก
    "ดาวเทียบ",  # ผิดจาก ดาวเทียม
    "สมมุติ",   # มาตรฐานราชบัณฑิตยสภาคือ สมมติ
    "โปรเจค",   # ควรใช้ โปรเจกต์ หรือ โครงการ/งานวิเคราะห์
    "เวิร์กโฟลว์", # ควรใช้ ขั้นตอนการทำงาน
    "ดาต้าเซ็ต",  # ควรใช้ ชุดข้อมูล
    "เมตริก",    # ควรใช้ ตัวชี้วัด
]

COLLISION_PATTERNS = [
    (r"ระบบระบบ", "การซ้อนคำนำหน้า (ระบบ + ระบบ...)"),
    (r"แสงอาทิตย์เซลล์", "คำประสมแตกจากการแทนที่ผิดลำดับ (ควรเป็น เซลล์แสงอาทิตย์/แผงเซลล์แสงอาทิตย์)"),
    (r"(?:น้ำท่วม|ท่วม)น้ำสูงสุด", "การแทนที่ 'พีค' โดยไม่ดูบริบทคำหน้า"),
    (r"วันจุดสูงสุด", "การแทนที่ 'วันพีค' ผิดบริบท (ควรเป็น วันที่น้ำสูงสุด หรือ วันที่ระดับน้ำขึ้นสูงสุด)"),
    (r"ที่ที่\s+ที่", "คำว่า 'ที่' ติดกัน 3 ครั้ง"),
    (r"และและ", "คำเชื่อมซ้ำซ้อน"),
]

BANNED_JARGON = [
    "พีค", "น้ำพีค", "attribution", "คาลิเบรต", "เทมเพลต",
    "rule curve", "rulecurve", "critical", "datum", "baseline",
    "threshold",
]


def _reader_text(html: str) -> str:
    """ดึงเฉพาะข้อความสำหรับผู้อ่าน ไม่เอาโค้ด/สไตล์/สคริปต์/แท็ก/base64"""
    out = []
    for is_text, chunk in _text_segments(html):
        if is_text and "base64," not in chunk:
            out.append(chunk)
    return " ".join(out)


def test_plain_th_integrity():
    """ตาราง PLAIN_TH ต้องเรียงลำดับจากยาวไปสั้น และคำประสมต้องมาก่อนคำเดี่ยวเสมอ"""
    keys = [k for k, _ in PLAIN_TH]
    sorted_keys = sorted(keys, key=len, reverse=True)
    assert keys == sorted_keys, "PLAIN_TH ต้องเรียงลำดับความยาวของคำค้นจากมากไปน้อยเสมอ"

    for i, k1 in enumerate(keys):
        for j, k2 in enumerate(keys):
            if k1 != k2 and k2 in k1:
                assert i < j, f"คำประสม {k1!r} ต้องปรากฏก่อนคำเดี่ยว {k2!r} ใน PLAIN_TH"


def test_known_typo_registry():
    """ต้องไม่พบคำผิดที่บันทึกไว้ใน Typo Registry ในเอกสาร Markdown, HTML รายงาน และ Builder"""
    targets = DOC_FILES + ALL_REPORTS + BUILDER_SCRIPTS
    errors = []

    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            text = _reader_text(text)
        elif path.suffix == ".py":
            # ในไฟล์ทดสอบนี้เองจะมีคำผิดอยู่ใน KNOWN_TYPOS ให้ข้ามไฟล์นี้
            if path.name == "test_thai_language_lint.py":
                continue

        for typo in KNOWN_TYPOS:
            # ข้ามกรณีที่อยู่ในคอมเมนต์ตัวอย่าง หรือใน gap id
            matches = list(re.finditer(re.escape(typo), text))
            if matches:
                errors.append(f"{path.name}: พบคำผิด {typo!r} ({len(matches)} จุด)")

    assert not errors, "พบคำผิดใน Typo Registry:\n" + "\n".join(errors)


def test_no_collision_or_stuttering():
    """ต้องไม่พบคำซ้อน/คำชนที่เกิดจากการ replace ข้อความผิดวิธี"""
    targets = DOC_FILES + ALL_REPORTS
    errors = []

    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            text = _reader_text(text)

        for pat, desc in COLLISION_PATTERNS:
            matches = list(re.finditer(pat, text))
            if matches:
                errors.append(f"{path.name}: พบรูปแบบคำชน {pat!r} ({desc}) จำนวน {len(matches)} จุด")

    assert not errors, "พบคำชน/คำซ้ำจากการแทนที่:\n" + "\n".join(errors)


def test_cross_doc_qa_count_consistency():
    """จำนวนข้อ ถาม–ตอบ รายงานที่ 7 (23 ข้อ) และ รายงานที่ 1 (15 ข้อ) ต้องสอดคล้องกันทุกเอกสาร"""
    # รายงานที่ 7 (คลองเจ้าพระยา 2): 23 ข้อ ต้องตรงกันทั้ง README.md, index.html, HANDOFF.md
    c7_counts = {}
    for doc in [ROOT / "README.md", ROOT / "index.html", ROOT / "HANDOFF.md"]:
        text = doc.read_text(encoding="utf-8")
        if doc.name == "README.md":
            m = re.search(r"รายงานที่ 7.*?ถาม[–-]ตอบ\s*(\d+)\s*ข้อ", text)
        else:
            m = re.search(r"คลองเจ้าพระยา2_ประชาชน.*?ถาม[–-]ตอบ\s*(\d+)\s*ข้อ", text, re.S)
        assert m is not None, f"ไม่พบ 'ถาม–ตอบ X ข้อ' ของรายงานคลองเจ้าพระยา 2 ใน {doc.name}"
        c7_counts[doc.name] = int(m.group(1))

    assert c7_counts == {"README.md": 23, "index.html": 23, "HANDOFF.md": 23}, f"จำนวนข้อถาม-ตอบรายงาน 7 ไม่ตรงกัน: {c7_counts}"

    # รายงานที่ 1 (นครนายก ประชาชน): 15 ข้อ ต้องตรงกันระหว่าง README.md และ index.html
    r1_counts = {}
    for doc in [ROOT / "README.md", ROOT / "index.html"]:
        text = doc.read_text(encoding="utf-8")
        m = re.search(r"(?:รายงานที่ 1|ลุ่มน้ำนครนายก|เล่าเหตุการณ์ตามลำดับเวลา).*?ถาม[–-]ตอบ\s*(\d+)\s*ข้อ", text, re.S)
        assert m is not None, f"ไม่พบ 'ถาม–ตอบ X ข้อ' ของรายงาน 1 ใน {doc.name}"
        r1_counts[doc.name] = int(m.group(1))

    assert r1_counts == {"README.md": 15, "index.html": 15}, f"จำนวนข้อถาม-ตอบรายงาน 1 ไม่ตรงกัน: {r1_counts}"


@pytest.mark.parametrize("report_path", ALL_REPORTS, ids=[p.stem for p in ALL_REPORTS])
def test_all_reports_no_banned_jargon(report_path):
    """รายงานทุกฉบับต้องไม่มีคำทับศัพท์/ศัพท์เทคนิคต้องห้ามในเนื้อความผู้อ่าน"""
    assert report_path.exists(), f"ยังไม่ได้สร้างรายงาน {report_path.name}"
    reader_content = _reader_text(report_path.read_text(encoding="utf-8"))

    found = {}
    for term in BANNED_JARGON:
        count = len(re.findall(re.escape(term), reader_content, flags=re.IGNORECASE))
        if count:
            found[term] = count

    assert not found, f"{report_path.name}: พบคำต้องห้ามตกค้างในเนื้อความ: {found}"
