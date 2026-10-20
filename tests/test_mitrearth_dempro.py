"""DEMPro 5 ม. ของมิตรเอิร์ธ: ความละเอียด/ขอบเขตตรงที่บันทึก · ส่วนต่างเทียบ FABDEM เป็นระบบ (ต่ำกว่า ~2 ม.) · ไม่ครอบองครักษ์"""
import json
from pathlib import Path

import pytest

S = Path(__file__).resolve().parent.parent / "analysis/goal7/mitrearth_dempro_summary.json"
pytestmark = pytest.mark.skipif(not S.exists(), reason="ยังไม่ได้รันสคริปต์")


def test_dempro_is_five_metre_and_covers_central_province():
    g = json.loads(S.read_text(encoding="utf-8"))["grids"]
    assert 4.5 < g["dempro_5m"]["cell_m"] < 5.6 and 30 < g["dem30m"]["cell_m"] < 32
    b = g["dempro_5m"]["bounds"]
    assert 101.1 < b[0] < 101.15 and 101.29 < b[2] < 101.32 and 14.1 < b[1] < 14.13 and 14.28 < b[3] < 14.3
    assert g["dempro_5m"]["nodata_cells"] <= 5


def test_dempro_lower_than_fabdem_systematically():
    d = json.loads(S.read_text(encoding="utf-8"))["difference_lowland_fabdem_lt_15m"]["dempro_minus_fabdem"]
    assert -3.0 < d["mean_m"] < -1.5 and d["sd_m"] < 1.2 and d["n"] > 100000


def test_window_does_not_cover_ongkharak():
    assert json.loads(S.read_text(encoding="utf-8"))["window"]["overlap_with_ongkharak_km2"] == 0.0


def test_bucket_level_shifts_with_dem_source():
    r = json.loads(S.read_text(encoding="utf-8"))["bucket_fit_vs_sar_2026"]
    for k in ("peak_27sep", "oct2_validated"):
        shift = r["fabdem"][k]["effective_level_m"] - r["dempro_5m_averaged_to_30m"][k]["effective_level_m"]
        assert 1.5 < shift < 3.0
