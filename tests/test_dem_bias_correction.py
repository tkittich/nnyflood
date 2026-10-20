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


def test_leave_one_window_out_improves():
    l = load()["leave_one_window_out"]
    assert l["windows_improved"] >= 0.8 * l["windows_total"] and l["mean_mae_gain_m"] > 0.5


def test_eia_ground_improves_along_canal():
    e = load()["eia_ground_check"]
    assert e["n_lowland_fabdem_lt_15m"] >= 15
    assert e["fabdem_corrected"]["mae_m"] < e["fabdem_raw"]["mae_m"] and e["fabdem_corrected"]["mae_m"] < 0.9
    assert abs(e["fabdem_corrected"]["bias_m"]) < abs(e["fabdem_raw"]["bias_m"])


def test_correct_function_roundtrip():
    import sys
    sys.path.insert(0, str(S.parent.parent))
    import goal7_dem_bias_correction as m
    t = load()["bias_table_by_fabdem_height"]
    out = m.correct(np.array([1.5, 2.5, 4.0]), t)
    assert (out < np.array([1.5, 2.5, 4.0])).all()
