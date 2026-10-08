# ตรวจ artifact หัวใจของรายงาน — กัน "ตัวเลขในเอกสาร" กับ "ไฟล์ผลจริง" แยกจากกัน
# (ครอบคลุมช่องที่ test_core.py ยังไม่ครอบ: สถานการณ์บริหาร · backtest หลายฤดู · สัดส่วนเขื่อน/ฝน)
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(rel):
    return json.load(open(ROOT / rel, encoding="utf-8"))


def test_counterfactual_headline_rows():
    """ตารางสถานการณ์บริหารที่รายงานอ้าง: จริง 11.9/65 · R1=M1 5.39/18 · M2=M3 0.83 (8/9 ชม.)"""
    j = _load("analysis/goal4_counterfactual_summary.json")
    assert abs(j["actual"][0] - 11.89) < 0.2 and j["actual"][1] == 65
    for k in ("R1", "M1"):
        assert abs(j[k][0] - 5.39) < 0.2 and j[k][1] == 18, k
    for k, h in (("M2", 8), ("M3", 9)):
        assert abs(j[k][0] - 0.83) < 0.1 and j[k][1] == h, k


def test_counterfactual_m4_volume_budget():
    """M4: ระบายก่อนน้ำสูงสุด 5.2 ลลบ.ม. → น้ำสูงสุดลด ~1 ซม. บนที่ราบ / ~52 ซม. ในกรอบลำน้ำ (corridor 9.94 ตร.กม. จาก hecras_lite หลังแก้ lon-scale)"""
    j = _load("analysis/goal4_counterfactual_summary.json")["M4_volume_budget"]
    assert abs(j["drain_mcm"] - 5.18) < 0.1
    assert abs(j["peak_drop_m"] - 0.01) < 0.005
    assert abs(j["corridor_drop_m"] - 0.52) < 0.02


def test_backtest_model_beats_persistence_every_season():
    """สูตรชนะ persistence ทุกฤดู (ฤดูน้ำหลาก) — รวมโฟลด์เหตุการณ์ 2569"""
    j = _load("analysis/goal4_model_backtest_long.json")["folds"]
    assert set(j) == {"2021", "2022", "2024", "2025", "2026"}
    for y, f in j.items():
        assert f["rmse24_wet"] < f["rmse24_persistence_wet"], y


def test_attribution_shares_match_headline():
    """สัดส่วนเขื่อน/ฝน: P1 ~12% · P2 ~60% (±2 จุด) — ตัวเลขที่ README/รายงานอ้าง (อินทิกราล 15 นาที รุ่นแก้ GL-01)"""
    j = _load("analysis/attribution_share.json")["windows"]
    p1 = j["P1_onset"]
    p2 = j["P2_sustained"]
    assert 10 <= p1["dam_share_measured_pct"] <= 14
    assert 55 <= p2["dam_share_measured_pct"] <= 63
    # ตัวเลขปริมาตรที่รายงานวิชาการ §4B อ้าง
    assert 38 <= p1["total_measured_mcm"] <= 40
    assert 68 <= p2["total_measured_mcm"] <= 71.5


def test_reports_contain_canonical_numbers():
    """HTML ที่ commit อยู่ต้องมีตัวเลข canonical ครบตาม analysis/canonical_numbers.json
    — กันกรณีรันวิเคราะห์ใหม่แล้วลืม build รายงาน (builders ตรวจตอน build ด้วย นี่คือชั้นที่ 2)"""
    canon = _load("analysis/canonical_numbers.json")["checks"]
    for fname, key in (
        ("น้ำท่วมนครนายก2569_ประชาชน.html", "public"),
        ("น้ำท่วมนครนายก2569_วิชาการ.html", "expert"),
    ):
        html = (ROOT / "report" / fname).read_text(encoding="utf-8")
        missing = [s for s in canon[key] if s not in html]
        assert not missing, f"{fname} ขาดตัวเลข canonical: {missing}"
        # ชั้นกลับ: ค่า/คำที่เลิกใช้ห้ามกลับเข้ามา (GL-10 — จับ "ค่าเก่าค้างคู่ค่าใหม่")
        present = [t for t in canon.get("forbidden", []) if t in html]
        assert not present, f"{fname} มีค่า/คำที่เลิกใช้: {present}"
