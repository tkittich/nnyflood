"""เทสรายงาน 1–2 (ฉบับประชาชน/วิชาการ) — รวมเข้าขอบเขตรีวิวเดียวกับรายงาน 3–4 (12 ต.ค. 69)

เดิมกติกาภาษา/ความเป็นกลาง/ภาพ บังคับเฉพาะรายงาน 3–4 · รายงาน 1–2 ผ่านเทสตัวเลข canonical อย่างเดียว
"""
from __future__ import annotations

import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "report"))
from goal6_reportlib import find_banned_reader_terms  # noqa: E402

R12 = [ROOT / "report/น้ำท่วมนครนายก2569_ประชาชน.html", ROOT / "report/น้ำท่วมนครนายก2569_วิชาการ.html"]
# วลีที่ถูกถอน (เกินหลักฐาน/ตัวเลขผิดนิยาม) — ห้ามกลับมา
RETIRED_PHRASES = [
    "ไม่มีหน่วยงานใดเคยเผยแพร่",
    "พิสูจน์ว่า \"ตัวกั้น\"",
    "ไม่ตามเส้นควบคุม",
    "ต่อเนื่องก่อนพายุ",
    "เต็มเกินเส้นควบคุม 36 วัน",
    "ฝนทั้งเดือน ต.ค.ของกรุงเทพฯ ปกติ ~200",
    "สปิลเวย์",
    "สูงกว่าค่ามากสุดในรอบ 26 ปี",
    "สูงกว่าค่าสูงสุดเทียบเคียงได้ในข้อมูลย้อนหลัง 26 ปี",
]


def test_reports12_exist_and_no_banned_terms():
    for f in R12:
        h = f.read_text(encoding="utf-8")
        assert find_banned_reader_terms(h) == [], f"{f.name}: คำต้องห้ามตกค้าง {find_banned_reader_terms(h)}"


def test_reports12_no_retired_phrases():
    for f in R12:
        h = f.read_text(encoding="utf-8")
        for p in RETIRED_PHRASES:
            assert p not in h, f"{f.name}: วลีที่ถอนแล้วกลับมา: {p!r}"


def test_reports12_embedded_images_valid():
    for f in R12:
        h = f.read_text(encoding="utf-8")
        imgs = re.findall(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/=]+)", h)
        assert imgs, f.name
        for kind, b in imgs:
            raw = base64.b64decode(b)
            assert raw[:8] == b"\x89PNG\r\n\x1a\n" if kind == "png" else raw[:2] == b"\xff\xd8", f.name


def test_reports12_builders_have_no_metric_literals():
    """F-18: builder รายงาน 1–2 ห้ามพิมพ์ตัวเลข metric เป็น literal — ต้องมาจาก @@R: เท่านั้น

    กติกา AGENTS.md หลัก 2 (เดิมบังคับเฉพาะเป้าหมาย 6) — ตัวเลขที่ขยับตามการ rerun
    ต้องผูกกับ analysis/canonical_numbers.json ไม่ใช่พิมพ์มือในเทมเพลต
    """
    import json
    canon = json.loads((ROOT / "analysis/canonical_numbers.json").read_text(encoding="utf-8"))
    render = canon["render"]
    builders = [ROOT / "report/build_report_html.py", ROOT / "report/build_expert_report.py"]
    literals = {
        "ny7_peak_g": render["ny7_peak_g"],
        "ny7_peak_msl": render["ny7_peak_msl"],
        "gistda_oct2": render["gistda_oct2"],
        "cf_ov_mcm": render["cf_ov_mcm"],
    }
    for b in builders:
        src = b.read_text(encoding="utf-8")
        for key, val in literals.items():
            assert val not in src, (
                f"{b.name}: ตัวเลข metric {val!r} ({key}) ถูกพิมพ์เป็น literal — ใช้ @@R:{key}@@ แทน")
        # 65 เปล่า ๆ ชนกับปี พ.ศ. (2564/65/67/68) จึงตรวจเฉพาะรูปที่ใช้จริงในข้อความ
        assert f"{render['cf_ov_h']} ชม." not in src, (
            f"{b.name}: '65 ชม.' ถูกพิมพ์เป็น literal — ใช้ @@R:cf_ov_h@@ ชม. แทน")


def test_token_contract_is_two_way():
    """สัญญา token สองทาง: ใช้แล้วต้องมี · มีแล้วต้องใช้

    - builder ใช้ @@R:key@@ แต่ canonical ไม่มี key → build พัง (ดักได้ก่อน build)
    - canonical มี key แต่ไม่มี builder ไหนใช้ → token ตาย (ลบทิ้ง หรือผูกให้ใช้จริง)

    ไม่มี allowlist โดยเจตนา: token ใหม่ต้องมาพร้อมการใช้ใน commit เดียวกัน
    """
    import json
    canon = json.loads((ROOT / "analysis/canonical_numbers.json").read_text(encoding="utf-8"))
    render = set(canon["render"])
    builders = [ROOT / "report/build_report_html.py", ROOT / "report/build_expert_report.py"]
    used: set[str] = set()
    for b in builders:
        used |= set(re.findall(r"@@R:([A-Za-z0-9_]+)@@", b.read_text(encoding="utf-8")))
    assert not (used - render), (
        f"builder ใช้ token ที่ไม่มีใน canonical render: {sorted(used - render)}")
    assert not (render - used), (
        f"canonical render มี token ที่ไม่มี builder ใช้ (token ตาย): {sorted(render - used)}")


def test_urc_streak_matches_data():
    """29 วันจนถึงน้ำสูงสุด 27 ก.ย. (36 วันถึง 4 ต.ค.) — คำนวณสดจาก CSV ไม่ใช่ตัวเลขพิมพ์"""
    import csv
    import datetime as dt
    rows = {r["date"]: r for r in csv.DictReader(
        open(ROOT / "analysis/dam_khun_dan_daily_2013_2026.csv", encoding="utf-8-sig"))}
    def over(d):
        r = rows.get(d.isoformat())
        return bool(r and r["storage_mcm"] and r["upper_rule_curve_mcm"]
                    and float(r["storage_mcm"]) > float(r["upper_rule_curve_mcm"]))
    peak = dt.date(2026, 9, 27)
    s = peak
    while over(s - dt.timedelta(1)):
        s -= dt.timedelta(1)
    e = peak
    while over(e + dt.timedelta(1)):
        e += dt.timedelta(1)
    assert (peak - s).days + 1 == 29 and s == dt.date(2026, 8, 30)
    assert (e - s).days + 1 == 36
    h = R12[0].read_text(encoding="utf-8")
    assert "29 วัน" in h and "รวม 36 วัน" in h
