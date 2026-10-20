"""ชุดมิตรเอิร์ธระดับประเทศ: ผลตรวจความครบ · สถานี กช. มีพิกัด Ny.* · จุดตัดถนน/หมู่บ้านใกล้แนวคลองสมเหตุสมผล"""
import json
from pathlib import Path

import pytest

R = Path(__file__).resolve().parent.parent
S = R / "analysis/goal7/mitrearth_thailand_summary.json"
pytestmark = pytest.mark.skipif(not S.exists(), reason="ยังไม่ได้รันสคริปต์")


def load():
    return json.loads(S.read_text(encoding="utf-8"))


def test_pack_completeness_recorded():
    c = load()["completeness"]
    assert c["files"] == 8086
    assert c["shapefile_sets_complete"] >= 170 and c["shapefile_sets_incomplete"] <= 20   # ฉบับสมบูรณ์ (R7-19 ปิดแล้ว): ขาดเล็กน้อยเฉพาะชั้นนอกขอบเขตโครงการ


def test_rid_stations_include_ny_with_coordinates():
    s = load()["rid_hydro_stations"]
    assert s["total_stations"] == 551 and "Ny.1B" in s["ny_stations"]
    rows = (R / s["csv"]).read_text(encoding="utf-8").splitlines()
    assert rows[0].startswith("code,lon,lat") and len(rows) - 1 == s["in_study_area"]


def test_corridor_layers_sane():
    d = load()
    assert d["stream_road_crossings"]["total_points_nationwide"] == 9431 and d["stream_road_crossings"]["within_3km_of_canal"] > 5
    v = d["villages_regional_flood"]
    assert v["villages_nationwide"] > 80000
    near = v["near_canal"]["กม.23–134"]
    assert near["within_1km"] <= near["within_2km"] <= near["within_5km"]
