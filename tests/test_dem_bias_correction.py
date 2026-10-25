"""การปรับความสูง FABDEM ด้วย DEMPro 5 ม.: ต้องดีขึ้นนอกตัวอย่าง (ตัดทีละหน้าต่าง) และกับเส้นดิน EIA ตลอดแนวคลอง"""
import json
from pathlib import Path

import numpy as np
import pytest

S = Path(__file__).resolve().parent.parent / "analysis/goal7/dem_bias_correction.json"
pytestmark = pytest.mark.skipif(not S.exists(), reason="ยังไม่ได้รันสคริปต์")


def load():
    return json.loads(S.read_text(encoding="utf-8"))


def test_enough_windows_and_table():
    d = load()
    assert d["windows_used"] >= 15 and d["pooled_points"] > 50000
    t = d["bias_table_by_fabdem_height"]
    assert t["1..2"]["fabdem_minus_dempro_median_m"] > 0.8 and t["2..3"]["fabdem_minus_dempro_median_m"] > t["1..2"]["fabdem_minus_dempro_median_m"]


def test_leave_one_window_out_reported_not_prejudged():
    """B1 รีวิวรอบ 7: เทสต์ไม่กำหนดว่าผลต้องดีขึ้น (กันกดดันให้ผลออกทางใดทางหนึ่ง) — ตรวจเพียงว่าค่าที่ต้องรายงานครบและเป็นตัวเลข"""
    l = load()["leave_one_window_out"]
    assert l["windows_total"] >= 15 and 0 <= l["windows_improved"] <= l["windows_total"]
    lo, hi = l["corrected_mae_range_m"]
    assert 0 <= lo <= hi and l["corrected_sd_range_m"][1] >= l["corrected_sd_range_m"][0] >= 0
    assert set(l["stepped"]) == {"mean_mae_gain_m", "windows_improved"}


def test_eia_ground_check_has_all_surfaces():
    e = load()["eia_ground_check"]
    assert e["n_lowland_fabdem_lt_15m"] >= 15
    for k in ("fabdem_raw", "fabdem_stepped", "fabdem_corrected", "copernicus_raw"):
        assert isinstance(e[k]["mae_m"], float) and isinstance(e[k]["bias_m"], float)


def test_monotone_correction_is_continuous_and_nondecreasing():
    """เงื่อนไขของกติกาที่ตั้งก่อนดูผล (docs/DEM_CORRECTION_PREREG.md §1.5): ไม่มีรอยกระโดดเกิน 0.05 ม. และไม่ลดลงตามความสูงดิบ"""
    import sys
    sys.path.insert(0, str(S.parent.parent))
    import goal7_dem_bias_correction as m
    mc = load()["monotone_correction"]
    assert mc["max_step_m"] <= 0.05
    g = np.arange(-5.0, 40.0, 0.01)
    y = m.correct_monotone(g, mc["knots"])
    assert (np.diff(y) >= 0).all() and np.abs(np.diff(y)).max() <= 0.05
    assert mc["max_step_stepped_table_m"] > 1.0        # ตารางเดิมเป็นขั้นบันไดจริง (เก็บไว้เป็นชุดความไว)
    assert m.correct_monotone(np.array([35.0]), mc["knots"])[0] == 35.0     # สูงกว่า 30 ม. ไม่ปรับ


def test_isotonic_pav_pools_violations():
    import sys
    sys.path.insert(0, str(S.parent.parent))
    import goal7_dem_bias_correction as m
    assert m._pav([1.0, 3.0, 2.0, 4.0], [1, 1, 1, 1]) == [1.0, 2.5, 2.5, 4.0]


def test_correct_function_roundtrip():
    import sys
    sys.path.insert(0, str(S.parent.parent))
    import goal7_dem_bias_correction as m
    t = load()["bias_table_by_fabdem_height"]
    out = m.correct(np.array([1.5, 2.5, 4.0]), t)
    assert (out < np.array([1.5, 2.5, 4.0])).all()
