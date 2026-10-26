"""ตรวจโครงสร้างผลวัดระยะตามลำน้ำ Ny.1B–Ny.7 (R7-23 · กติกา docs/REACH_LENGTH_PREREG.md)
เทสต์ไม่ฝังข้อสรุป: ตรวจรูปแบบ ช่วงค่า และความสอดคล้องกับกติกาเท่านั้น"""
import json
from pathlib import Path

R = json.loads((Path(__file__).resolve().parent.parent / "analysis/goal7/reach_length.json").read_text(encoding="utf-8"))
CANON = json.loads((Path(__file__).resolve().parent.parent / "analysis/canonical_numbers.json").read_text(encoding="utf-8"))


def test_all_preregistered_cases_reported():
    cases = {(c["hy_use_only_1"], c["tol_m"]) for c in R["cases"]}
    assert cases == {(u, t) for u in (False, True) for t in (10.0, 30.0, 100.0)}


def test_path_not_shorter_than_straight_line():
    for c in R["cases"]:
        if c["path_km"] is not None:
            assert c["path_km"] >= c["straight_km"]
            assert abs(c["sinuosity"] - c["path_km"] / c["straight_km"]) < 0.01


def test_decision_follows_preregistered_20pct_rule():
    if R["measurable"]:
        assert R["consistent_within_20pct"] == (abs(R["diff_vs_used_pct"]) <= 20.0)
        lo, hi = R["range_km"]
        assert lo <= R["central_km"] <= hi


def test_report_tokens_match_json():
    r = CANON["render"]
    assert r["reach_used_km"] == f"{R['used_reach_km']:.1f}"
    if R["measurable"]:
        assert r["reach_meas_km"] == f"{R['central_km']:.1f}"
        assert r["reach_diff_pct"] == f"{abs(R['diff_vs_used_pct']):.0f}"
