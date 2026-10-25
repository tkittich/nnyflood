"""แบบจำลองชลศาสตร์ 2 มิติองครักษ์ — โครงผลและกติกาที่ตั้งไว้ก่อนดูผล (ไม่ใช้ GPU)"""
import json
from pathlib import Path

R = json.loads((Path(__file__).resolve().parent.parent / "analysis/goal7/ongkharak_hydraulic_2d.json").read_text(encoding="utf-8"))


def test_grid_and_rules_recorded():
    assert set(R["dems"]) == {"fabdem_corrected", "fabdem_stepped", "fabdem_raw", "copernicus_raw"}
    for v in R["dems"].values():
        assert len(v["runs"]) == 6
        b = v["best_by_27sep"]
        best = max(v["runs"], key=lambda r: r["peak_27sep"]["iou"])
        assert b["iou_27sep"] == best["peak_27sep"]["iou"]          # เลือกด้วย 27 ก.ย. เท่านั้น
        assert b["iou_2oct_not_refit"] == best["oct2_validated"]["iou"]


def test_mass_balance_not_absurd():
    for v in R["dems"].values():
        for r in v["runs"]:
            assert 0 < r["final_stored_mcm"] <= r["inflow_mcm"] + 10      # น้ำที่เก็บไม่เกินน้ำเข้ารวมน้ำเริ่มต้นในร่อง


def test_water_budget_closes_every_run():
    """R7-28 (กติกา docs/HYDRAULIC2D_RERUN_PREREG.md §2): บัญชีน้ำปิดรอบทุกการรัน — ถ้าเกินร้อยละ 5 ต้องติดป้ายในรายงาน (ที่นี่ตรวจว่าไม่เกิน)"""
    for v in R["dems"].values():
        for r in v["runs"]:
            b = r["budget"]
            assert abs(b["closure_error_pct_of_input"]) < 5.0, b
            assert b["final_mcm"] >= 0 and b["edge_outflow_mcm"] >= 0

