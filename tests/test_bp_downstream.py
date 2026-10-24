"""ส่วนเพิ่ม 4.7 ของรายงาน 3 (ท้ายน้ำบางปะกง/ฉะเชิงเทรา) — ตัวเลขมาจาก canonical และติดป้ายสถานะ exploratory"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAN = json.loads((ROOT / "analysis/goal6/canonical.json").read_text(encoding="utf-8"))
HTML = (ROOT / "report/ระลอกปลายกย2569.html").read_text(encoding="utf-8")


def test_canonical_block_matches_goal7_source():
    b = CAN["bp_downstream"]
    src = json.loads((ROOT / "analysis/goal7/bangpakong_chachoengsao.json").read_text(encoding="utf-8"))
    assert b["basin"]["area_km2"] == src["basin"]["basin_area_km2"]
    assert b["gauges"]["BPK003"]["latest_m"] == next(s for s in src["gauges"]["stations"] if s["code"] == "BPK003")["latest_m"]
    assert b["terrain"]["variance_explained"]["by_elevation_zone"] > b["terrain"]["variance_explained"]["by_province"]


def test_report3_has_labelled_exploratory_section_with_numbers_from_canonical():
    assert "4.7 ส่วนเพิ่ม: ท้ายน้ำบางปะกง" in HTML
    assert "วิเคราะห์เพิ่มหลังกำหนดคำถามล่วงหน้า" in HTML
    b = CAN["bp_downstream"]
    assert f"{b['basin']['area_km2']:,.0f}" in HTML                        # ขนาดลุ่มที่พิมพ์ต้องตรง canonical
    assert f"{b['gauges']['BPK003']['run_above_bank_days_to_latest']:.0f} วัน" in HTML
