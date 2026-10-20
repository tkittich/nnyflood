"""ชั้นมิตรเอิร์ธรายจังหวัด: เส้นเขตต้องเป็นรวมตำบล (ไม่ใช่กรอบ `bound`) · ผลสรุปสมเหตุสมผล · จังหวัดที่ไม่มี GISTDA ระบุชัด"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
S = ROOT / "analysis/goal7/mitrearth_provinces_summary.json"
pytestmark = pytest.mark.skipif(not S.exists(), reason="ยังไม่ได้รันสคริปต์")


def load():
    return json.loads(S.read_text(encoding="utf-8"))


def test_province_areas_match_known_sizes():
    """พื้นที่จังหวัดจากรวมตำบลต้องใกล้พื้นที่จริง (±10%) — ชั้น bound/pbound ใหญ่กว่า ~2 เท่าและห้ามใช้"""
    known = {"กรุงเทพมหานคร": 1569, "นนทบุรี": 622, "ฉะเชิงเทรา": 5351, "นครนายก": 2122, "พระนครศรีอยุธยา": 2557, "ปทุมธานี": 1526}
    got = {v["name"]: v["province_area_km2"] for v in load()["provinces"].values()}
    for k, a in known.items():
        assert abs(got[k] - a) / a < 0.10, (k, got[k], a)


def test_gistda_years_and_shares_sane():
    for pid, v in load()["provinces"].items():
        g = v.get("gistda")
        if not g:
            continue
        for y, r in g["per_year"].items():
            assert 2005 <= int(y) <= 2011
            assert 0 <= r["share_pct"] <= 100
        assert g["ever_flooded_km2"] <= v["province_area_km2"] * 1.001
        assert g["ever_flooded_km2"] >= max(r["area_km2"] for r in g["per_year"].values()) - 0.1


def test_missing_gistda_provinces_declared():
    s = load()
    assert set(s["gistda_missing_provinces"]) == {"อ่างทอง", "สิงห์บุรี", "สมุทรปราการ", "สมุทรสาคร"}


def test_2026_overlap_fields():
    r = load()["vs_2026"]
    assert r["covered_area_km2"] > 1000
    for k in ("peak_27sep", "oct2_validated"):
        assert 0 <= r[k]["share_flooded_in_any_past_year_pct"] <= 100
