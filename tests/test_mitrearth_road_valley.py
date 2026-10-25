"""R7-14: จุดถนนตัดร่องน้ำในอำเภอองครักษ์ — ตรวจโครงสร้างและความสอดคล้อง ไม่ตรวจว่าผลต้องออกทางใด"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "analysis/goal7/mitrearth_road_valley.json").read_text(encoding="utf-8"))
C = json.loads((ROOT / "analysis/goal7/canonical.json").read_text(encoding="utf-8"))


def test_counts_consistent_and_subsets_nested():
    o, h = R["in_ongkharak"], R["in_ongkharak_highway_305"]
    assert 0 < h["n"] <= o["n"] <= R["province_valley_x_road_points"]
    for blk in (o, h):
        assert blk["fabdem_raw"]["n"] == blk["n"] == blk["fabdem_corrected"]["n"]
        assert 0 <= blk["below_observed_stage_raw"] <= blk["n"] and 0 <= blk["below_observed_stage_corrected"] <= blk["n"]
        assert blk["fabdem_corrected"]["median_m"] < blk["fabdem_raw"]["median_m"]       # ตารางปรับลดความสูงในช่วงนี้ (ตรวจโครงสร้าง ไม่ใช่ข้อสรุป)


def test_caveat_states_bare_earth_not_road_surface_and_gap_stays_open():
    assert "ไม่ใช่ระดับผิวถนน" in R["caveat"]
    gaps = {g["id"]: g for g in json.loads((ROOT / "analysis/goal7/gaps.json").read_text(encoding="utf-8"))["gaps"]}
    assert gaps["route305_crown_elevation"]["status"] == "open"


def test_layers_summary_in_canonical_and_rendered_in_academic_report():
    assert "mitrearth_road_valley" in C and "mitrearth_layers" in C
    html = (ROOT / "report/คลองเจ้าพระยา2_วิชาการ.html").read_text(encoding="utf-8")
    assert "จุดที่ถนนตัดร่องน้ำ" in html and "เส้นชั้น 1 ม." in html and "พื้นที่น้ำท่วมรายปีของ GISTDA" in html
