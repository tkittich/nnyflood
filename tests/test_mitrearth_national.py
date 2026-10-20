"""ชุดมิตรเอิร์ธฉบับสมบูรณ์: น้ำท่วม GISTDA 15 ปีตลอดแนวคลอง · ระดับน้ำทะเลสูงขึ้น · DEMPro 5 ม. เทียบเส้นดินธรรมชาติ EIA"""
import json
from pathlib import Path

import pytest

S = Path(__file__).resolve().parent.parent / "analysis/goal7/mitrearth_national_summary.json"
pytestmark = pytest.mark.skipif(not S.exists(), reason="ยังไม่ได้รันสคริปต์")


def load():
    return json.loads(S.read_text(encoding="utf-8"))


def test_inventory_counts():
    inv = load()["inventory"]
    assert inv["provinces"] == 77 and inv["with_dempro_5m"] >= 70 and 35 <= inv["with_gistda_flood"] <= 45


def test_corridor_flood_frequency_sane():
    f = load()["gistda_corridor_2005_2019"]
    assert len(f["by_year_km2"]) == 15 and 700 < f["corridor_km2"] < 900
    r = f["by_reach"]
    # ช่วงลอยกลางทุ่ง (กม.23–134) ท่วมบ่อยกว่าช่วงปากอ่าว (กม.134–135.9)
    assert r["กม.23–134"]["ever_flooded_pct"] > r["กม.134–135.9"]["ever_flooded_pct"]
    for v in r.values():
        assert 0 <= v["flooded_6plus_years_pct"] <= v["flooded_3plus_years_pct"] <= v["ever_flooded_pct"] <= 100
    assert f["by_year_km2"]["2011"] > 100 and f["by_year_km2"]["2006"] > 100     # ปีใหญ่ ๆ ต้องเห็นในทางเดินรอบแนวคลอง


def test_2026_vs_15_years():
    v = load()["gistda_vs_2026_nakhon_nayok"]
    for k in ("peak_27sep", "oct2_validated"):
        assert 0 <= v[k]["share_flooded_6plus_past_years_pct"] <= v[k]["share_flooded_in_any_past_year_pct"] <= 100
        assert abs(sum(v[k]["by_number_of_past_years_pct"].values()) - 100) < 0.6


def test_slr_monotone():
    s = load()["sea_level_rise_vs_canal"]
    km = [s[k]["axis_km_inside"] for k in sorted(s, key=int)]
    assert km == sorted(km) and km[-1] > 130


def test_dempro_closest_to_eia_ground():
    d = load()["dempro_vs_eia_ground"]
    assert len(d) >= 2
    for name, v in d.items():
        m = v["dem_minus_eia_ground"]
        assert m["dempro"]["mae_m"] < 0.7, name
        assert m["dempro"]["mae_m"] < m["fabdem"]["mae_m"] and m["dempro"]["mae_m"] < m["glo30"]["mae_m"], name
