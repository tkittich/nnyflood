"""ทดสอบการประมวลผลชั้นข้อมูลมิตรเอิร์ธ (goal7_mitrearth_layers): การลงตารางกริดรูปมีรู และความสมเหตุสมผลของผลสรุป"""
import json
import sys
from pathlib import Path

import pytest
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_mitrearth_layers as m  # noqa: E402

SUMMARY = ROOT / "analysis/goal7/mitrearth_layers_summary.json"


def test_rasterize_hole_not_counted():
    x0, y1, res = m.GRID["x0"], m.GRID["y1"], m.GRID["res"]
    outer = [(x0 + 10 * res, y1 - 10 * res), (x0 + 30 * res, y1 - 10 * res), (x0 + 30 * res, y1 - 30 * res), (x0 + 10 * res, y1 - 30 * res)]
    hole = [(x0 + 15 * res, y1 - 15 * res), (x0 + 25 * res, y1 - 15 * res), (x0 + 25 * res, y1 - 25 * res), (x0 + 15 * res, y1 - 25 * res)]
    a = m.rasterize([Polygon(outer, [hole])])
    assert a.sum() == 20 * 20 - 10 * 10


def test_rasterize_overlap_counted_once():
    x0, y1, res = m.GRID["x0"], m.GRID["y1"], m.GRID["res"]
    sq = [(x0, y1), (x0 + 10 * res, y1), (x0 + 10 * res, y1 - 10 * res), (x0, y1 - 10 * res)]
    assert m.rasterize([Polygon(sq), Polygon(sq)]).sum() == 100


@pytest.mark.skipif(not SUMMARY.exists(), reason="ยังไม่ได้รันสคริปต์")
def test_summary_sanity():
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    a = s["a_gistda_flood_footprints"]
    assert set(a["per_year"]) == {"2005", "2006", "2008", "2010", "2011"}
    for v in a["per_year"].values():
        assert 0 <= v["share_of_province_pct"] <= 100
        assert 0 <= v["vs_2026_oct2_validated"]["iou"] <= 1
    for r in a["recurrence_of_2026_footprint_pct"].values():
        assert abs(sum(r["by_number_of_past_flood_years"].values()) - 100) < 0.5
    assert s["b_subbasin_vs_eia"]["eia_pk_at_4_km2"] == pytest.approx(330.0, abs=0.1)
    c = s["c_contour_1m_vs_dem"]
    assert c["window_set_gis_file"]["n_points_sampled_in_province"] > 1000 and c["province_set_4_contour_line"]["n_points_sampled_in_province"] > 1000
    # เส้นชั้น 1 ม. สร้างจาก DEM ของมิตรเอิร์ธเอง: ชุดหน้าต่าง ← DEMPro 5 ม. · ชุดทั้งจังหวัด ← DEM 30 ม. (ส่วนต่างเฉลี่ย ~0)
    assert c["conclusion"]["window_set_derived_from"] == "dempro_5m" and c["conclusion"]["province_set_derived_from"] == "mitrearth_dem30m"
    assert abs(c["window_set_gis_file"]["dem_minus_contour"]["dempro_5m"]["bias_m"]) < 0.2 and c["window_set_gis_file"]["dem_minus_contour"]["dempro_5m"]["mae_m"] < 0.5
    assert c["province_set_4_contour_line"]["dem_minus_contour"]["mitrearth_dem30m"]["mae_m"] < 1.0
