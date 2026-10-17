# ตรวจ artifact หัวใจของรายงาน — กัน "ตัวเลขในเอกสาร" กับ "ไฟล์ผลจริง" แยกจากกัน
# (ครอบคลุมช่องที่ test_core.py ยังไม่ครอบ: สถานการณ์บริหาร · backtest หลายฤดู · สัดส่วนเขื่อน/ฝน)
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(rel):
    return json.load(open(ROOT / rel, encoding="utf-8"))


def test_counterfactual_headline_rows():
    """ตารางสถานการณ์บริหารที่รายงานอ้าง: จริง 11.9/65 · R1=M1 5.39/18 · M2=M3 0.83 (8/9 ชม.)"""
    j = _load("analysis/goal4_counterfactual_summary.json")
    assert abs(j["actual"]["overflow_mcm"] - 11.89) < 0.2 and j["actual"]["hours_above_bankfull"] == 65
    for k in ("R1", "M1"):
        assert abs(j[k]["overflow_mcm"] - 5.39) < 0.2 and j[k]["hours_above_bankfull"] == 18, k
    for k, h in (("M2", 8), ("M3", 9)):
        assert abs(j[k]["overflow_mcm"] - 0.83) < 0.1 and j[k]["hours_above_bankfull"] == h, k


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


# ---------- GL-10: ค่า/คำที่เลิกใช้ต้องไม่กลับมาบนพื้นผิวที่เผยแพร่ทุกชิ้น ----------
_NUMERIC = re.compile(r"[\d,]+(?:\.\d+)?%?")


def _num_pattern(token):
    """ขอบเขตของ token ที่เป็นตัวเลขล้วน — กัน 62.2 ไปจับใน 162.2

    lookbehind กันการเป็นส่วนท้ายของเลขอื่น (162.2, 11,050) · lookahead กันการเป็น
    ส่วนต้นของทศนิยมอื่น (62.25) แต่ปล่อยให้มีเครื่องหมายวรรคตอนต่อท้ายได้ (1,050,)
    token ที่ลงท้ายด้วย % ไม่ต้องมี lookahead เพราะ % ทำหน้าที่ปิดตัวเลขเอง
    """
    post = r"(?!\d)" if token[-1].isdigit() else ""
    return r"(?<![\d.,])" + re.escape(token) + post


def _hits(tokens, html):
    out = []
    for t in tokens:
        if _NUMERIC.fullmatch(t):
            if re.search(_num_pattern(t), html):
                out.append(t)
        elif t in html:
            out.append(t)
    return out


def test_no_retired_values_in_published_surfaces():
    """ค่า/คำที่เลิกใช้ (canonical_numbers.json:forbidden) ห้ามปรากฏใน HTML ที่เผยแพร่ทุกไฟล์

    ประวัติ: เวอร์ชันก่อนหน้าอ่าน `_load(...)["checks"].get("forbidden")` ซึ่งคืน [] เสมอ
    → การตรวจนี้ไม่เคยทำงานเลย (42 รายการ ไม่ถูกตรวจสักครั้ง) และไม่เคยครอบ Goal 6/7
    ตอนนี้ตรวจทั้ง 6 ไฟล์ โดยมีข้อยกเว้นที่ต้องระบุเหตุผล (forbidden_exceptions)
    """
    canon = _load("analysis/canonical_numbers.json")
    forbidden = canon["forbidden"]
    exceptions = canon.get("forbidden_exceptions", {})
    surfaces = sorted(p.name for p in (ROOT / "report").glob("*.html"))
    assert len(surfaces) >= 6, f"พบ HTML ที่เผยแพร่น้อยกว่าที่ควร: {surfaces}"

    offenders = {}
    for name in surfaces:
        allowed = exceptions.get(name, {})
        html = (ROOT / "report" / name).read_text(encoding="utf-8")
        hits = [t for t in _hits(forbidden, html) if t not in allowed]
        if hits:
            offenders[name] = hits
    assert not offenders, f"พบค่า/คำที่เลิกใช้บนพื้นผิวที่เผยแพร่: {offenders}"


def test_forbidden_exceptions_are_auditable():
    """ข้อยกเว้นต้องมีเหตุผล · ต้องอ้าง token ที่อยู่ใน forbidden จริง · ต้องยังจำเป็น

    กันไม่ให้ forbidden_exceptions กลายเป็นช่องเลี่ยงการแบนค่าใหม่ และกันข้อยกเว้นค้าง
    ที่ token หายไปจากไฟล์แล้ว (จะทำให้การตรวจอ่อนลงโดยไม่มีใครรู้)
    """
    canon = _load("analysis/canonical_numbers.json")
    forbidden = set(canon["forbidden"])
    for name, mapping in canon.get("forbidden_exceptions", {}).items():
        path = ROOT / "report" / name
        assert path.exists(), f"ข้อยกเว้นอ้างไฟล์ที่ไม่มีอยู่: {name}"
        html = path.read_text(encoding="utf-8")
        for token, reason in mapping.items():
            assert token in forbidden, f"{name}: ข้อยกเว้น {token} ไม่ได้อยู่ใน forbidden"
            assert isinstance(reason, str) and len(reason.strip()) >= 20, \
                f"{name}: {token} ต้องมีเหตุผลประกอบ"
            assert token in html, \
                f"{name}: ข้อยกเว้น {token} ค้างอยู่ (ไม่พบในไฟล์แล้ว) — ลบออกจาก canonical"


def test_routing_summary_naming_and_scope_notes():
    """รีวิวรอบ 4 (SB F-14/F-15/F-02/F-24): ชื่อ key ต้องเป็น bankfull_* + มีหมายเหตุขอบเขตครบ

    - ห้ามเหลือ levee_crest_* (สันสำรวจไม่ใช่คันดิน — ตั้งชื่อเดิมทำให้อ่านผิดความหมาย)
    - ต้องมีหมายเหตุ: n สอบเทียบที่ Ny.7 แห่งเดียว · ค่า X ถูกบีบเป็น 0 · bias แยกจาก RMSE
    """
    j = _load("analysis/hydraulic_1d_routing_summary.json")
    for blk in ("ny1b_hydraulics", "ny7_hydraulics"):
        assert not any(k.startswith("levee_crest") or k == "peak_above_levee_m"
                       for k in j[blk]), f"{blk}: ยังมีชื่อชุด levee_crest_*"
    assert "bankfull_capacity_q_cms" in j["ny1b_hydraulics"]
    assert "Ny.7" in j["metadata"]["manning_n_note"]
    assert "X = 0" in j["metadata"]["muskingum_x_note"]
    assert "ny1b_flat_slope" in j["rating_sensitivity"]
    perf = j["routing_performance"]
    assert "stage_bias_cm" in perf and "stage_residual_cm" in perf
