"""แบบจำลองชลศาสตร์ 2 มิติองครักษ์โหมดฝน — โครงผล กติกาเลือกค่า และความสอดคล้องกับ canonical (ไม่ใช้ GPU)"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = json.loads((ROOT / "analysis/goal7/ongkharak_hydraulic_2d_rain_all.json").read_text(encoding="utf-8"))
C = json.loads((ROOT / "analysis/goal7/canonical.json").read_text(encoding="utf-8"))["ongkharak_hydraulic_2d"]


def test_two_rounds_combined_and_best_chosen_by_27sep_only():
    assert set(A["dems"]) == {"fabdem_corrected", "fabdem_raw", "copernicus_raw"}
    for v in A["dems"].values():
        assert len(v["runs"]) == 10
        best = max(v["runs"], key=lambda r: r["peak_27sep"]["iou"])
        assert (v["best_by_27sep"]["f_mmh"], v["best_by_27sep"]["k_per_day"]) == (best["f_mmh"], best["k_per_day"])
        assert v["best_by_27sep"]["iou_2oct_not_refit"] == best["oct2_validated"]["iou"]


def test_rain_beats_no_rain_by_far_and_canonical_matches():
    for d, r in C["rain_best"].items():
        assert r["peak_27sep"]["iou"] > 10 * max(C["q_only_max_iou"][d]["iou_27sep"], 0.01)
        assert r["peak_27sep"]["iou"] == A["dems"][d]["best_by_27sep"]["iou_27sep"]


def test_best_params_at_grid_edge_is_recorded_honestly():
    """ค่าดีสุดอยู่ขอบกริด (ซึมต่ำสุด ระบายช้าสุด) — ข้อความในรายงานต้องบอกเรื่องนี้ ไม่อ้างว่าระบุค่าได้"""
    for v in A["dems"].values():
        f_all = {r["f_mmh"] for r in v["runs"]}
        k_all = {r["k_per_day"] for r in v["runs"]}
        assert v["best_by_27sep"]["f_mmh"] == min(f_all) and v["best_by_27sep"]["k_per_day"] == min(k_all)
