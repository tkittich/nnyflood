"""R7-27: ฮาร์มอนิกหลายปีพร้อมตัวแก้ปมจันทร์ (กติกา docs/HARMONICS_REFIT_PREREG.md) — ตรวจโครงสร้างและการไม่รั่วไหล ไม่ตรวจว่าผลต้องดีกว่าแบบเดิม"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal6_l3_coastal_harmonics as m  # noqa: E402

S = json.loads((ROOT / "analysis/goal6/l3_coastal_harmonics_summary.json").read_text(encoding="utf-8"))


def test_fit_uses_many_years_and_ends_before_test_window():
    fb = S["fit_basis"]
    assert fb["n_hours_fit"] > 50000 and fb["fit_end"] < "2026-09-20 00:00" and fb["common_sample_all_leads"] is True
    assert len(S["astronomical_harmonics_calibrated"]["constituents"]) == 10


def test_common_sample_same_n_test_all_leads():
    n = {v["n_test"] for v in S["lead_skill_evaluations"].values()}
    assert len(n) == 1
    n2 = {v["n_test"] for v in S["comparison_short_window_4_constituents"]["lead_skill_evaluations"].values()}
    assert n == n2                     # สองตัวทำนายเทียบกันบนตัวอย่างชุดเดียวกัน


def test_nodal_factors_match_rule():
    f, u = m.nodal_fu("M2", np.array([0.0]))
    assert abs(f[0] - (1.0004 - 0.0373 + 0.0002)) < 1e-9 and abs(u[0]) < 1e-12
    f, u = m.nodal_fu("S2", np.array([123.0]))
    assert f[0] == 1.0 and u[0] == 0.0


def test_design_matrix_shape_and_reports_both_predictors():
    import datetime as dt
    X = m._design([dt.datetime(2020, 1, 1) + dt.timedelta(hours=h) for h in range(10)])
    assert X.shape == (10, 21)
    assert set(S["tide_prediction_vs_observed_test_window"]) == {"short_window_4", "multiyear_10"}
