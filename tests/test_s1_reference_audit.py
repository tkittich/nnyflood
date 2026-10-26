"""ตรวจโครงสร้างผลตรวจฉากอ้างอิงเรดาร์ขั้นที่ 2 (docs/S1_REFERENCE_AUDIT_PREREG.md) — ผลวินิจฉัย ณ ก่อนเปลี่ยนวิธี ไม่ฝังข้อสรุป"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "analysis/goal6/s1_reference_audit.json").read_text(encoding="utf-8"))
SUM = json.loads((ROOT / "data/22_goal6_network/derived/s1_stage2/summary.json").read_text(encoding="utf-8"))


def test_audit_labels_follow_rule_and_values_consistent():
    assert R["scenes"] and all(s["status"] == "ok" for s in R["scenes"])
    for b, v in R["per_basin"].items():
        if v["published_max_km2"]:
            assert v["material_label"] == (abs(v["change_pct"]) > 10.0)
            assert abs(v["change_pct"] - 100 * (v["audited_max_km2"] - v["published_max_km2"]) / v["published_max_km2"]) < 0.11
        assert v["audited_max_km2"] >= 0


def test_stage2_now_pairs_by_relative_orbit_with_pre_event_reference():
    """หลังเปลี่ยนวิธี (27 ต.ค. 69): ทุกฉากมีฉากอ้างอิงก่อน 24 ก.ย. ของวงโคจรสัมพัทธ์เดียวกัน และไม่มีฉากค้างไม่มีคู่"""
    import sys
    sys.path.insert(0, str(ROOT / "analysis"))
    from s1_orbit import EVENT_START, rel_orbit, start_of
    for b, v in SUM.items():
        assert v["unpaired"] == [], b
        for r in v["scenes"]:
            assert all(start_of(x) < EVENT_START for x in r["reference_all"])
            assert all(rel_orbit(x) == rel_orbit(r["scene"]) for x in r["reference_all"])
            if r["reference"] == r["scene"]:
                assert r["water_km2_lowland"] == 0.0 and r["scene"] in r["reference_all"]
