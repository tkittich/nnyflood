"""R7-26: เมทริกซ์น้ำท่วมซ้อนแบบยึดค่าที่วัด (กติกา docs/COMPOUND_ANCHORED_PREREG.md) — ตรวจโครงสร้างและความสอดคล้อง ไม่ตรวจว่าผลต้องออกทางใด"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import compound_flood_risk as m  # noqa: E402

S = json.loads((ROOT / "analysis/compound_flood_risk_summary.json").read_text(encoding="utf-8"))
A = S["matrix_anchored"]


def test_original_matrix_untouched_by_the_new_variant():
    assert m.calculate_c12_stage(2250, 1.91) == 2.36          # ค่าที่รายงานเดิม (สมการไม่เปลี่ยน)
    assert all(c["c12_stage_msl_m"] == m.calculate_c12_stage(c["q_bangsai_m3s"], c["tide_msl_m"]) for row in S["matrix_grid"] for c in row)


def test_anchored_reproduces_observed_stage_at_the_anchor_and_bands_sum():
    a = A["anchor"]
    cell = next(c for row in A["grid"] for c in row if c["q_bangsai_m3s"] == a["q_bangsai_m3s"] and abs(c["tide_msl_m"] - a["tide_msl_m"]) < 0.051)
    assert abs(cell["c12_stage_msl_m"] - a["stage_msl_m"]) <= 0.1      # ช่องกริดที่ใกล้จุดยึดที่สุด (น้ำหนุนกริดห่างจากจุดยึดไม่เกิน 0.05 ม. × อัตราส่ง)
    for key, cnt in A["band_counts"].items():
        assert sum(cnt.values()) == A["n_cells"], key


def test_gain_band_ordered_and_stage_never_above_original():
    g = A["gain"]
    assert g["low"] < g["central"] < g["high"] < 1.0                   # อัตราส่งที่วัดได้ต่ำกว่า 1.0 ของสมการเดิม
    assert A["stage_diff_vs_original_m"]["max"] <= 0.0 + 1e-9
    for row in A["grid"]:
        for c in row:
            assert c["stage_gain_low_m"] <= c["stage_gain_high_m"] or c["tide_msl_m"] < A["anchor"]["tide_msl_m"]


def test_risk_function_matches_thresholds():
    assert [m.risk_of(x) for x in (1.99, 2.00, 2.39, 2.40, 2.69, 2.70)] == ["normal", "watch", "watch", "warning", "warning", "critical"]
