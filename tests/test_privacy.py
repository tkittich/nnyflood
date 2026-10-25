"""เทสความเป็นส่วนตัว (PDPA) — กันเบอร์โทร/ลิงก์โปรไฟล์ส่วนบุคคลกลับเข้า git

เพิ่ม 12 ต.ค. 69 หลังรีวิวภายนอกพบเบอร์โทรประชาชนในไฟล์ดิบโซเชียลที่ track (P1) —
สแกนเฉพาะไฟล์ข้อความที่ git track (ไม่รวมอนุกรมตัวเลขขนาดใหญ่ที่เลขสุ่มพ้องกับรูปเบอร์ได้)
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHONE = re.compile(r"(?<![\d.\-a-fA-F])0[689]\d[- ]?\d{3}[- ]?\d{4}(?![\d.])")
PROFILE = re.compile(r"facebook\.com/(?:profile\.php\?id=\d+|people/)")
LANDLINE = re.compile(r"(?<![\d.\-])0(?:2[- ]\d{3}[- ]\d{4}|[3-7]\d[- ]\d{3}[- ]\d{3,4})(?![\d.])")      # เบอร์บ้าน/สำนักงานที่มีขีดหรือเว้นวรรค
ID13 = re.compile(r"(?<![\d.])[1-8]\d{12}(?![\d.])")
TEXT_EXT = {".md", ".csv", ".txt", ".html", ".py", ".json", ".geojson", ".jsonl", ".tsv", ".xml", ".htm", ".yml", ".yaml"}      # รีวิวรอบ 7 R7-30: เพิ่มไฟล์ข้อมูลโครงสร้าง
ID_EXT = {".md", ".csv", ".txt", ".py"}      # เลขบัตรประชาชน 13 หลักตรวจเฉพาะข้อความ (ไฟล์ข้อมูลตัวเลข/แฮชมีเลข 13 หลักพ้องรหัสตรวจบ่อย)
MAX_BYTES = 20_000_000
# ไฟล์ที่อ้างรูปแบบเหล่านี้เพื่ออธิบายกติกา/รีวิว (ไม่ใช่ข้อมูลบุคคล)
ALLOW = {"tests/test_privacy.py", "docs/LEGAL_REVIEW.md",
         # ลิงก์โปรไฟล์ของเพจทางการเขื่อนขุนด่านฯ (องค์กร ไม่ใช่บุคคลธรรมดา)
         "data/01_rid_khun_dan/manifest.md", "data/01_rid_khun_dan/fb_page/manifest.md"}
ALLOW_PREFIX = ("docs/reviews/",)


def _has_valid_id13(txt: str) -> bool:
    for m in ID13.finditer(txt):
        d = [int(c) for c in m.group(0)]
        if (11 - sum(d[i] * (13 - i) for i in range(12)) % 11) % 10 == d[12]:
            return True
    return False


def test_scanner_patterns_catch_known_shapes():
    assert PHONE.search("โทร 081-234-5678") and LANDLINE.search("โทร 02-123-4567") and LANDLINE.search("038 123 456")
    assert _has_valid_id13("เลขบัตร 1101700207030") and not _has_valid_id13("เลขสุ่ม 1101700207031")
    assert not LANDLINE.search("พิกัด 14.2358 101.1234 ปี 2569-10-25")


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
    return [p for p in out.stdout.splitlines() if p]


def test_no_phone_numbers_or_profile_links_in_tracked_text():
    bad = []
    for rel in _tracked():
        p = Path(rel)
        if p.suffix.lower() not in TEXT_EXT or p.name.startswith("_hashes") or rel in ALLOW or rel.startswith(ALLOW_PREFIX):
            continue
        f = ROOT / rel
        if not f.exists() or f.stat().st_size > MAX_BYTES:
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if PHONE.search(txt) or PROFILE.search(txt) or LANDLINE.search(txt) or (p.suffix.lower() in ID_EXT and _has_valid_id13(txt)):
            bad.append(rel)
    assert not bad, f"พบเบอร์โทร/ลิงก์โปรไฟล์ส่วนบุคคลในไฟล์ที่ track: {bad}"


def test_raw_social_dirs_not_tracked():
    banned = ("data/06_citizen_social/raw/", "data/01_rid_khun_dan/fb_page/raw/",
              "data/01_rid_khun_dan/fb_page/screenshots/", "data/01_rid_khun_dan/instagram/raw/")
    hits = [p for p in _tracked() if p.startswith(banned)]
    assert not hits, f"ไฟล์ดิบโซเชียลต้องไม่เข้า git: {hits[:5]}"
