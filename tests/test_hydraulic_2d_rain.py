"""แบบจำลองชลศาสตร์ 2 มิติองครักษ์โหมดฝน — โครงผล กติกาเลือกค่า และความสอดคล้องกับ canonical (ไม่ใช้ GPU)"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = json.loads((ROOT / "analysis/goal7/ongkharak_hydraulic_2d_rain_all.json").read_text(encoding="utf-8"))
C = json.loads((ROOT / "analysis/goal7/canonical.json").read_text(encoding="utf-8"))["ongkharak_hydraulic_2d"]


def test_two_rounds_combined_and_best_chosen_by_27sep_only():
    assert set(A["dems"]) == {"fabdem_corrected", "fabdem_stepped", "fabdem_raw", "copernicus_raw"}
    for v in A["dems"].values():
        assert len(v["runs"]) == 10
        best = max(v["runs"], key=lambda r: r["peak_27sep"]["iou"])
        assert (v["best_by_27sep"]["f_mmh"], v["best_by_27sep"]["k_per_day"]) == (best["f_mmh"], best["k_per_day"])
        assert v["best_by_27sep"]["iou_2oct_not_refit"] == best["oct2_validated"]["iou"]


def test_canonical_matches_results_without_prejudging_conclusions():
    """รีวิวรอบ 7: ไม่ฝังข้อสรุปในเทสต์ (เช่น ฝนต้องชนะ หรือค่าดีสุดต้องอยู่ขอบกริด) — รายงานคำนวณข้อความเหล่านี้จากข้อมูล"""
    for d, r in C["rain_best"].items():
        assert r["peak_27sep"]["iou"] == A["dems"][d]["best_by_27sep"]["iou_27sep"]
        assert abs(r["budget"]["closure_error_pct_of_input"]) < 5.0
    for d, rows in C["qsens"].items():
        assert [x["q_scale"] for x in rows] == [0.8, 1.2]


def test_report_edge_statement_follows_data():
    """ข้อความ 'ขอบกริด' ในรายงานต้องตรงข้อมูล: พิมพ์เมื่อค่าดีสุดของทุกพื้นผิวอยู่ขอบกริดเท่านั้น"""
    import sys
    sys.path.insert(0, str(ROOT / "report"))
    import goal7_blocks as blk
    edge = all(v["best_by_27sep"]["f_mmh"] == min(r["f_mmh"] for r in v["runs"]) and v["best_by_27sep"]["k_per_day"] == min(r["k_per_day"] for r in v["runs"]) for v in A["dems"].values())
    txt = blk.prose_hydraulic_2d()
    assert ("ขอบของกริดที่ลอง" in txt) == edge
