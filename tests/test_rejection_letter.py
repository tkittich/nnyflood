"""R7-10: โครงหนังสือ สผ. ทส 1010.6/2233 (ถอดด้วย Typhoon-OCR) — วันที่ตรงภาพต้นฉบับ · หัวข้อ 21 · ข้ออ้างอิงในรายงานมีอยู่จริงในต้นฉบับ"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = json.loads((ROOT / "analysis/goal7/rejection_letter_items.json").read_text(encoding="utf-8"))
OE = json.loads((ROOT / "analysis/goal7/operational_economics_summary.json").read_text(encoding="utf-8"))


def test_letter_date_matches_image_evidence():
    assert ITEMS["letter"]["date"] == "18 ก.พ. 2562"
    ev = ITEMS["letter"]["date_evidence"]
    f = ROOT / ev["file"]
    assert f.exists() and hashlib.sha256(f.read_bytes()).hexdigest() == ev["sha256"]
    assert "18 ก.พ. 2562" in OE["eia_rejection_history"][0]["official_letter"]


def test_letter_has_21_sections_and_section_1_has_16():
    assert ITEMS["counts"]["sections_detected"] == 21
    assert ITEMS["counts"]["section_1_items_in_letter"] == 16
    assert ITEMS["counts"]["items_detected_total"] >= 100


def test_round1_rows_cite_existing_letter_items():
    """ทุกแถวรอบ 1 ต้องอ้าง 'หัวข้อ N ข้อ M' ที่มีในต้นฉบับ (ข้อ 10 ของหัวข้อ 1 หายจากข้อความถอด — ยกเว้นไว้ชัดเจน)"""
    secs = ITEMS["sections"]
    rows = OE["eia_rejection_history"][0]["key_objections"]
    assert rows
    for r in rows:
        refs = re.findall(r"หัวข้อ (\d+) ข้อ ([\d.]+)(?:–([\d.]+))?", r["section"])
        assert refs, f"เลขข้ออ้างอิงไม่อยู่ในรูปแบบ 'หัวข้อ N ข้อ M': {r['section']}"
        for sec, a, b in refs:
            for no in (a, b):
                if not no:
                    continue
                have = {i["no"] for i in secs[sec]["items"]}
                assert no in have or no.split(".")[0] in have, f"{r['section']}: ไม่พบข้อ {no} ในหัวข้อ {sec} ของต้นฉบับ"


def _round_check(n, no, date):
    rd = ITEMS["rounds"][str(n)]
    assert rd["letter"]["no"] == no and rd["letter"]["date"] == date
    assert rd["ocr"]["pages_truncated"] == 0
    ev = rd["letter"]["date_evidence"]
    f = ROOT / ev["file"]
    assert f.exists() and hashlib.sha256(f.read_bytes()).hexdigest() == ev["sha256"]
    h = OE["eia_rejection_history"][n - 1]
    assert no in h["official_letter"] and date in h["official_letter"]
    for r in h["key_objections"]:
        refs = re.findall(r"หัวข้อ (\d+) ข้อ ([\d.]+)", r["section"])
        assert refs, r["section"]
        for sec, a in refs:
            assert a in {i["no"] for i in rd["sections"][sec]["items"]}, r["section"]


def test_round2_letter_and_rows():
    _round_check(2, "ทส 1010.6/18346", "25 พ.ย. 2564")


def test_round3_letter_and_rows():
    _round_check(3, "ทส 1009.6/6077", "18 มี.ค. 2567")
