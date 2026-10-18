"""tests/test_legal_compliance.py — ชุดตรวจความสอดคล้องทางกฎหมายอัตโนมัติ (Legal Compliance & PDPA Guard)

ครอบคลุม:
1. พ.ร.บ. ว่าด้วยการกระทำความผิดเกี่ยวกับคอมพิวเตอร์ พ.ศ. 2560 (มาตรา 14):
   - ตรวจสอบว่ารายงานทุกฉบับมีข้อสงวนสิทธิ์และคำเตือนเรื่องข้อจำกัดของแบบจำลอง (Modeling Uncertainty Disclaimer)
   - ป้องกันการนำเสนอผลจำลองสมมติโดยไม่ติดป้ายกำกับ (Scenario / Simulation Labeling)
2. กฎหมายหมิ่นประมาท (ประมวลกฎหมายอาญา มาตรา 326–333 และมาตรา 329(3)):
   - สแกนหาคำชี้หน้า/กล่าวหาทุจริตส่วนบุคคล (Defamation & Tone Guard)
   - บังคับการวิพากษ์วิจารณ์เชิงระบบ (Systemic Criticism) ไม่พาดพิงบุคคลธรรมดา
3. พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562 (PDPA):
   - สแกนหาเลขบัตรประชาชน 13 หลัก, เลขโฉนดที่ดิน, เบอร์โทรศัพท์, และอีเมลส่วนบุคคล
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

# รายงาน HTML ทั้งหมดที่เผยแพร่สู่สาธารณะ
PUBLISHED_REPORTS = [
    ROOT / "report/น้ำท่วมนครนายก2569_ประชาชน.html",
    ROOT / "report/น้ำท่วมนครนายก2569_วิชาการ.html",
    ROOT / "report/ระลอกปลายกย2569.html",
    ROOT / "report/ชุดเทียบมาตรฐาน2554.html",
    ROOT / "report/คลองเจ้าพระยา2_ประชาชน.html",
    ROOT / "report/คลองเจ้าพระยา2_วิชาการ.html",
    ROOT / "report/สมุดปกขาว_เจ้าพระยา2.html",
]

# คำสุ่มเสี่ยงหมิ่นประมาท / ถ้อยคำกล่าวหาอาญาส่วนบุคคลที่ห้ามใช้ในรายงาน
BANNED_DEFAMATION_TERMS = [
    "โกง",
    "ทุจริต",
    "ฮั้วประมูล",
    "กินหัวคิว",
    "เจตนาทำลาย",
    "ยักยอก",
    "ต้มตุ๋น",
]

# รูปแบบข้อมูลส่วนบุคคล (PDPA)
THAI_CITIZEN_ID = re.compile(r"(?<![\d])\b[1-8]\d{12}\b(?![\d])")
THAI_CITIZEN_ID_HYPHEN = re.compile(r"\b[1-8]-\d{4}-\d{5}-\d{2}-\d\b")
LAND_TITLE_DEED = re.compile(r"โฉนดที่ดินเลขที่\s*\d+")
PHONE_NUMBER = re.compile(r"(?<![\d.\-a-fA-F])0[689]\d[- ]?\d{3}[- ]?\d{4}(?![\d.])")

ALLOW_LEGAL_DOCS = {
    "docs/LEGAL_REVIEW.md",
    "tests/test_legal_compliance.py",
    "tests/test_privacy.py",
}


def _is_valid_thai_citizen_id(s: str) -> bool:
    clean = s.replace("-", "").strip()
    if len(clean) != 13 or not clean.isdigit():
        return False
    digits = [int(c) for c in clean]
    total = sum(digits[i] * (13 - i) for i in range(12))
    check = (11 - (total % 11)) % 10
    return check == digits[12]


def _get_tracked_text_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    valid_exts = {".md", ".html", ".py", ".csv", ".txt", ".json"}
    files = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("data/01_rid_khun_dan/raw/") or "manifest" in line:
            continue
        p = Path(line)
        if p.suffix.lower() in valid_exts:
            files.append(line)
    return files


def test_all_published_reports_have_disclaimer_stack():
    """รายงานทุกฉบับต้องมีกล่องคำเตือนและข้อสงวนสิทธิ์ 3 ชั้น (3-Tier Disclaimer Stack)"""
    missing = []
    for rpath in PUBLISHED_REPORTS:
        if not rpath.exists():
            continue
        content = rpath.read_text(encoding="utf-8")

        # ตรวจสอบว่ามีองค์ประกอบสำคัญครบทั้ง 4 ด้าน
        has_disclaimer = "ข้อสงวนสิทธิ์" in content or "คำเตือน" in content
        has_penal_code = "329(3)" in content or "สุจริต" in content
        has_cca = "คอมพิวเตอร์" in content
        has_peer_review = "Issue" in content or "รับฟังความคิดเห็น" in content or "ตรวจสอบ" in content

        if not (has_disclaimer and has_penal_code and has_cca and has_peer_review):
            missing.append(
                f"{rpath.name}: ขาดองค์ประกอบข้อสงวนสิทธิ์ "
                f"(disclaimer={has_disclaimer}, penal_code={has_penal_code}, cca={has_cca}, peer_review={has_peer_review})"
            )

    assert not missing, "พบรายงานที่ยังขาดข้อสงวนสิทธิ์ทางกฎหมาย 3 ชั้น:\n" + "\n".join(missing)


def test_no_defamatory_terms_in_reports():
    """รายงานและเอกสารสาธารณะต้องไม่มีถ้อยคำปรักปรำหรือกล่าวหาเรื่องทุจริตส่วนตัว"""
    errors = []
    for rpath in PUBLISHED_REPORTS:
        if not rpath.exists():
            continue
        content = rpath.read_text(encoding="utf-8")
        # ตัดแท็กสคริปต์และสไตล์
        clean_text = re.sub(r"<(script|style).*?</\1>", " ", content, flags=re.DOTALL)
        clean_text = re.sub(r"<[^>]+>", " ", clean_text)

        for term in BANNED_DEFAMATION_TERMS:
            if term in clean_text:
                errors.append(f"{rpath.name}: พบคำสุ่มเสี่ยงหมิ่นประมาท '{term}'")

    assert not errors, "พบคำสุ่มเสี่ยงหมิ่นประมาทในรายงาน ต้องเปลี่ยนเป็นข้อความเชิงระบบ:\n" + "\n".join(errors)


def test_enhanced_pdpa_no_citizen_identities():
    """ต้องไม่มีเลขบัตรประชาชน 13 หลัก, เลขโฉนดที่ดิน, หรือเบอร์โทรประชาชนในไฟล์ที่ track ใน git"""
    violations = []
    tracked = _get_tracked_text_files()

    for rel_path in tracked:
        if rel_path in ALLOW_LEGAL_DOCS or rel_path.startswith("docs/reviews/"):
            continue
        fpath = ROOT / rel_path
        if not fpath.exists() or fpath.stat().st_size > 10_000_000:
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # ตรวจสอบเลขโฉนด
        if LAND_TITLE_DEED.search(text):
            violations.append(f"{rel_path}: พบเลขโฉนดที่ดิน")

        # ตรวจสอบเลขโทรศัพท์ส่วนบุคคล
        if PHONE_NUMBER.search(text):
            violations.append(f"{rel_path}: พบเบอร์โทรศัพท์ส่วนบุคคล")

        # ตรวจสอบเลขบัตรประชาชน 13 หลัก (ทั้งแบบมีขีดและไม่มีขีด)
        if not rel_path.startswith("data/") and fpath.suffix.lower() in {".md", ".html", ".py", ".txt"}:
            if THAI_CITIZEN_ID_HYPHEN.search(text):
                violations.append(f"{rel_path}: พบเลขบัตรประชาชน 13 หลัก (รูปแบบมีขีด)")
            for m in THAI_CITIZEN_ID.finditer(text):
                if _is_valid_thai_citizen_id(m.group(0)):
                    violations.append(f"{rel_path}: พบเลขบัตรประชาชน 13 หลักที่ถูกต้องตามอัลกอริทึม")
                    break

    assert not violations, "พบข้อมูลส่วนบุคคลตาม PDPA ในคลังโค้ด:\n" + "\n".join(violations)


def test_scenario_simulations_have_explicit_markers():
    """การจำลองตัวเลขสมมติ (Simulation/Scenario) ต้องมีคำกำกับว่าเป็นแบบจำลองเสมอ กันความเข้าใจผิดเรื่องข้อมูลเท็จ"""
    brief_path = ROOT / "report/สมุดปกขาว_เจ้าพระยา2.html"
    if brief_path.exists():
        content = brief_path.read_text(encoding="utf-8")
        # ในสมุดปกขาวมีการคำนวณฉากทัศน์งบบานปลาย 1.9–2.1 แสนล้าน ต้องมีคำว่าแบบจำลองหรือฉากทัศน์
        if "2.14" in content or "1.93" in content:
            assert ("แบบจำลอง" in content or "ฉากทัศน์" in content), (
                "การแสดงตัวเลขฉากทัศน์งบประมาณต้องมีคำว่า 'แบบจำลอง' หรือ 'ฉากทัศน์' กำกับเสมอ"
            )


def test_legal_review_documentation_exists():
    """ต้องมีเอกสาร docs/LEGAL_REVIEW.md และบรรจุหลักการฎีกา พ.ร.บ.คอมฯ ม.14 ครบถ้วน"""
    lpath = ROOT / "docs/LEGAL_REVIEW.md"
    assert lpath.exists(), "ต้องมีเอกสาร docs/LEGAL_REVIEW.md"
    text = lpath.read_text(encoding="utf-8")
    assert "2778/2561" in text, "LEGAL_REVIEW.md ต้องอ้างอิงคำพิพากษาศาลฎีกาที่ 2778/2561"
    assert "6794/2561" in text, "LEGAL_REVIEW.md ต้องอ้างอิงคำพิพากษาศาลฎีกาที่ 6794/2561"
    assert "329(3)" in text, "LEGAL_REVIEW.md ต้องระบุฐานการคุ้มครองตาม ป.อาญา ม.329(3)"
