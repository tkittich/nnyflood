"""ทดสอบขอบน้ำเรดาร์เทียบ DEM (goal7_dem_waterline_test) — โครงผลและความสอดคล้องพื้นฐาน"""
import json
from pathlib import Path

R = json.loads((Path(__file__).resolve().parent.parent / "analysis/goal7/dem_waterline_test.json").read_text(encoding="utf-8"))


def test_three_dems_two_dates_with_edges():
    assert set(R["results"]) == {"peak_27sep", "oct2_validated"}
    for d in R["results"].values():
        assert set(d) == {"copernicus_raw", "fabdem_raw", "fabdem_corrected"}
        for r in d.values():
            assert r["edge_pixels"] > 10000 and 0 < r["edge_iqr_over_district_iqr"] < 1.5


def test_corrected_dem_has_tightest_edge_both_dates():
    for d in R["results"].values():
        assert d["fabdem_corrected"]["edge_iqr_over_district_iqr"] == min(r["edge_iqr_over_district_iqr"] for r in d.values())


def test_gistda_yearly_waterline_summary():
    G = json.loads((Path(__file__).resolve().parent.parent / "analysis/goal7/dem_gistda_waterline_test.json").read_text(encoding="utf-8"))
    assert set(G["summary"]) == {"copernicus_raw", "fabdem_raw", "fabdem_corrected"}
    n = {v["years_tested"] for v in G["summary"].values()}
    assert len(n) == 1 and n.pop() >= 5
    assert all(v["flood_km2_in_district"] >= G["min_flood_km2"] for v in G["years"].values())
    assert G["summary"]["copernicus_raw"]["median_edge_level_m"] - G["summary"]["fabdem_corrected"]["median_edge_level_m"] > 1.0
