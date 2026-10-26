"""ตรวจโครงสร้างผลแผนที่น้ำเรดาร์ฉะเชิงเทรา (R7-22 · กติกา docs/S1_CHACHOENGSAO_RECENT_PREREG.md) — ไม่ฝังข้อสรุป"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
R = json.loads((ROOT / "analysis/goal7/s1_chachoengsao_recent.json").read_text(encoding="utf-8"))


def test_every_ok_scene_has_reference_before_event_and_valid_fractions():
    ok = [s for s in R["scenes"] if s["status"] == "ok"]
    assert ok
    for s in ok:
        assert s["reference"] and all(r < "20260924" for r in s["reference"])
        assert 0 <= s["province_coverage_frac"] <= 1
        assert 0 <= s["water_frac_of_covered_province"] <= 1
        assert s["water_km2_in_province"] <= R["province_km2_on_grid"]


def test_province_area_is_province_not_neighbour_union():
    assert 4000 < R["province_km2_on_grid"] < 6000       # จังหวัดเดียว (ชั้น bound รวมเพื่อนบ้านเคยใช้ผิด — ดูข้อ 6 ของกติกา)


def test_relative_orbit_formula_matches_known_pairs():
    import goal7_s1_chachoengsao_recent as m
    a = "S1D_IW_GRDH_1SDV_20260926T230018_20260926T230043_004755_008E7F_8F9B_COG.SAFE"
    b = "S1D_IW_GRDH_1SDV_20260914T230017_20260914T230042_004580_008890_0000_COG.SAFE"
    assert m.rel_orbit(a) == 133
    assert (4755 - 4580) % 175 == 0 and m.rel_orbit(b) == 133   # ห่าง 175 รอบ = วงโคจรเดียวกัน
