# ทดสอบฟังก์ชันหลักของโปรเจค (รัน: python -m pytest tests/ -q)
#
# ทุกเทสต์ต้อง import ฟังก์ชันจริงจากโปรเจคและ/หรือตรวจ artifact จริง —
# เทสต์ที่เป็นเลขคณิตในตัวมันเองโดยไม่ผูกกับโค้ดโปรเจคจะ "ผ่านเสมอ"
# แม้โค้ดโปรเจคจะพังทั้งหมด จึงห้ามเขียนแบบนั้น:
#   - analysis/rain_window.py                -> หน้าต่างฝนรายวัน + กันข้อมูลอนาคตรั่ว
#   - analysis/rid_cross_section_hydraulics.py -> Manning / geometry / rating / datum
#   - analysis/rid_cross_section_extract.py  -> การอ่านป้ายกำกับไทยในไฟล์สำรวจ
#   - analysis/goal4_model_v1_results.json   -> ข้อสรุปที่เผยแพร่ต้องตรงกับผลจริง
#   - data/16_training_data/power_rain_daily_3pts_2021_2026.csv -> ฝนเหตุการณ์จริง
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))

from rain_window import day_window, windows_for_grid          # noqa: E402
import rid_cross_section_hydraulics as hyd                    # noqa: E402
from rid_cross_section_extract import parse_offset            # noqa: E402


# ---------- rain_window: หน้าต่างฝนรายวัน ----------

def test_day_window_is_a_window_not_a_cumulative_sum():
    """ผลต่างรายวันของหน้าต่างต้องคงที่ (หน้าต่างจริง) ไม่ใช่ cumsum เลื่อน n ช่อง ซึ่งโต quadratic"""
    daily = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    w3 = day_window(daily, 3)
    assert np.allclose(w3, [0.0, 0.0, 1.0, 3.0, 6.0, 9.0, 12.0])
    # หน้าต่างจริง -> ผลต่างคงที่ (= ฝนรายวัน 3) ไม่ใช่บวกเพิ่มขึ้นเรื่อย ๆ
    assert np.allclose(np.diff(w3[3:]), 3.0)
    # ยืนยันว่าต่างจากสูตร cumsum ที่ผิด (ถ้าใครเผลอเขียนแบบนั้น เทสต์นี้จะล้ม)
    c = np.concatenate([[0.0], np.cumsum(daily)])
    buggy = np.array([c[max(0, i - 3)] for i in range(1, len(daily) + 1)])
    assert not np.allclose(w3, buggy)


def test_day_window_uses_no_future_information():
    """ช่อง "เมื่อวาน" ต้องไม่มีฝนของวันนี้ปน (กันข้อมูลอนาคตรั่ว)"""
    daily = np.zeros(10)
    w1 = day_window(daily, 1)
    assert w1[5] == 0.0
    daily[5] = 100.0                      # ฝนตก "วันนี้"
    w1 = day_window(daily, 1)
    assert w1[5] == 0.0                   # วันนี้ยังไม่ถูกนับ
    assert w1[6] == 100.0                 # พรุ่งนี้จึงเห็นเป็น "ฝนเมื่อวาน"


def test_windows_for_grid_aligns_to_yesterday():
    """ทั้งวันมีค่าเท่ากัน และเท่ากับฝนสะสมที่สิ้นสุดเมื่อวาน"""
    grid = [dt.datetime(2026, 9, 1) + dt.timedelta(hours=h) for h in range(72)]
    daily = {"20260901": 10.0, "20260902": 20.0, "20260903": 30.0}
    w = windows_for_grid(daily, grid, (1, 3))
    assert set(w[1][:24]) == {0.0}        # 1 ก.ย. ยังไม่มีเมื่อวาน
    assert set(w[1][24:48]) == {10.0}     # 2 ก.ย. -> ฝน 1 ก.ย.
    assert set(w[1][48:72]) == {20.0}     # 3 ก.ย. -> ฝน 2 ก.ย.
    assert set(w[3][48:72]) == {30.0}     # 3 ก.ย. -> ฝน 1+2 ก.ย. = 30
    # เพิ่มฝน "วันนี้" ต้องไม่เปลี่ยนค่าของวันนี้
    w2 = windows_for_grid({**daily, "20260903": 999.0}, grid, (1, 3))
    assert set(w2[1][48:72]) == {20.0}
    assert set(w2[3][48:72]) == {30.0}


# ---------- rid_cross_section_hydraulics ----------

def test_manning_q_hand_calculated():
    """Q = (1/n)·A·R^(2/3)·√S — เทียบกับค่าคำนวณมือ A=100 · P=40 · n=0.035"""
    q = hyd.manning_q(100.0, 40.0, 0.035)
    assert abs(q - 94.356) < 0.01
    # n สูงขึ้น -> Q ลดลง (ทิศทางต้องถูก)
    assert hyd.manning_q(100.0, 40.0, 0.030) > hyd.manning_q(100.0, 40.0, 0.045)


def test_manning_q_edge_cases():
    """พื้นที่หรือเส้นรอบเปียกเป็น 0 -> ไม่มีอัตราไหล (ห้ามคืน nan/inf)"""
    assert hyd.manning_q(0.0, 10.0, 0.035) == 0.0
    assert hyd.manning_q(10.0, 0.0, 0.035) == 0.0


def test_project_rating_bankfull():
    """rating ของโปรเจค: Q = 242·(h−4.55)^0.66 ; ที่ระดับล้นตลิ่ง 6.86 -> ~420 ม³/วิ"""
    assert abs(hyd.project_rating(6.86) - 420.5) < 1.0
    assert abs(hyd.project_rating(7.64) - 509.6) < 1.0
    assert hyd.project_rating(4.55) == 0.0          # ระดับเริ่มไหล
    assert hyd.project_rating(4.0) == 0.0           # ต่ำกว่านั้นต้องไม่ติดลบ
    assert hyd.project_rating(7.64) > hyd.project_rating(6.86)


def test_geometry_v_channel():
    """ร่องน้ำรูปตัว V (ท้อง 0 · ขอบ 10 ม.รทก. ที่ offset ±10 ม.) ที่ระดับ 5 ม.รทก.
    -> กว้างผิวน้ำ 10 ม. · พื้นที่เปียก = 2·∫₀⁵(5−x)dx = 25 ตร.ม."""
    xs = np.array([-10.0, 0.0, 10.0])
    ys = np.array([10.0, 0.0, 10.0])
    w, a, p = hyd.geometry(xs, ys, 5.0, dx=0.25)
    assert abs(a - 25.0) < 0.5
    assert abs(w - 10.0) < 0.5
    assert p > w                                     # เส้นรอบเปียกต้องมากกว่าความกว้างผิวน้ำ
    # ระดับสูงขึ้น -> กว้างขึ้น/พื้นที่มากขึ้น (monotone)
    w2, a2, _ = hyd.geometry(xs, ys, 8.0, dx=0.25)
    assert a2 > a and w2 > w


def test_geometry_dry_channel():
    """ระดับต่ำกว่าท้องน้ำ -> ไม่มีน้ำเลย"""
    xs = np.array([-10.0, 0.0, 10.0])
    ys = np.array([10.0, 0.0, 10.0])
    w, a, p = hyd.geometry(xs, ys, -1.0)
    assert (w, a) == (0.0, 0.0)


def test_datum_offset_ny7():
    """datum Ny.7: ม.รทก. = เกจ − 1.59 (ค่าคงที่ของโปรเจค)"""
    assert abs(hyd.GAUGE_OFFSET - 1.59) < 1e-9
    assert abs((9.23 - hyd.GAUGE_OFFSET) - 7.64) < 0.01    # น้ำสูงสุดเหตุการณ์
    assert abs((8.45 - hyd.GAUGE_OFFSET) - 6.86) < 0.01    # ระดับล้นตลิ่ง


def test_slope_is_plausible_river_slope():
    """SLOPE ต้องอยู่ในพิสัยความลาดของแม่น้ำจริง (9 ม./28 กม. = 3.2e-4)
    พิสัยนี้จับ typo เช่น 9/2800 (3.2e-3) ได้"""
    assert 1e-4 < hyd.SLOPE < 1e-3


# ---------- rid_cross_section_extract ----------

def test_parse_offset_thai_labels():
    """คอลัมน์สำรวจมีทั้งตัวเลขล้วนและสตริงมีป้ายกำกับไทย"""
    assert parse_offset(23.5) == (23.5, "")
    assert parse_offset(-60.0) == (-60.0, "")
    off, label = parse_offset("23.50 ผิวน้ำซ้าย")
    assert off == 23.5 and label == "ผิวน้ำซ้าย"
    assert parse_offset("-60.00") == (-60.0, "")


def test_parse_offset_without_number():
    """ไม่มีตัวเลข -> offset None (ห้ามคืน 0 ซึ่งจะกลายเป็นจุดปลอมบนภาคตัดขวาง)"""
    off, label = parse_offset("ไม่ระบุ")
    assert off is None and label == "ไม่ระบุ"
    assert parse_offset(None) == (None, "")


# ---------- เอกสารต้องตรงกับ artifact ----------

def test_documented_claims_match_shipped_results():
    """ข้อสรุปที่เผยแพร่ (findings §ผล) ต้องตรงกับ goal4_model_v1_results.json จริง
    เทสต์นี้จะล้มถ้ามีใครรันโมเดลใหม่แล้วตัวเลขเปลี่ยนโดยไม่แก้เอกสาร"""
    res = json.loads((ROOT / "analysis" / "goal4_model_v1_results.json").read_text(encoding="utf-8"))
    # แถว = [ชื่อ, RMSE ทั้งชุด, MAE, RMSE เหตุการณ์, hit, false-alarm]
    ev = {h: {row[0]: row[3] for row in rows} for h, rows in res.items()}
    for h in ("6", "24", "48"):
        assert set(ev[h]) == {"persistence", "linear", "GBDT"}
    # +6 ชม.: สูตรเส้นตรงชนะทั้ง persistence และ GBDT
    assert ev["6"]["linear"] < ev["6"]["persistence"]
    assert ev["6"]["linear"] < ev["6"]["GBDT"]
    # +24 ชม.: persistence ชนะสูตรเส้นตรง — สูตรไม่ได้ชนะทุกระยะ
    assert ev["24"]["persistence"] < ev["24"]["linear"]
    # +48 ชม.: GBDT ชนะ (ทุกโมเดลพังที่ระดับ 1.5 ม.)
    assert ev["48"]["GBDT"] < ev["48"]["linear"]


def test_event_rain_total_matches_documented_value():
    """ฝนสะสม 7 วัน 23–29 ก.ย. 69 (เฉลี่ย 2 เซลล์กริด) ต้องได้ ~248 มม. ตามที่รายงานอ้าง
    และต้องเกินเกณฑ์เฝ้าระวัง 150 มม./7 วัน"""
    p = ROOT / "data" / "16_training_data" / "power_rain_daily_3pts_2021_2026.csv"
    rows = {r[0]: (float(r[1]) + float(r[3])) / 2
            for r in csv.reader(open(p, encoding="utf-8")) if r[0] != "date"}
    days = [f"202609{d:02d}" for d in range(23, 30)]
    assert all(d in rows for d in days), "ข้อมูลฝนช่วงเหตุการณ์หายไป"
    total = sum(rows[d] for d in days)
    assert abs(total - 247.9) < 1.0
    assert total > 150.0


# ---------- s1_change_detect: กฎน้ำท่วม 3 เงื่อนไข + opening (ผลรีวิว GLM GL-03) ----------

def test_s1_flood_rule_conditions_and_opening():
    """กฎ canonical: ΔVH≤−1 & ΔVV≤−2 & VHหลัง≤−18 + opening 3×3 —
    แต่ละเงื่อนไขต้อง gate จริง · พิกเซลโดดเดี่ยวถูก opening กลืน · บล็อก 3×3 รอด ·
    NaN/นอก lowland ไม่นับ (เทสนี้จะจับกรณี F-01 ซ้ำ: สคริปต์ committed ต่างจากกฎที่ตีพิมพ์)"""
    from s1_change_detect import detect
    n = 9
    pre_vh = np.full((n, n), -20.0)
    pre_vv = np.full((n, n), -20.0)
    post_vv = np.full((n, n), -23.0)          # ΔVV = −3 ✓ ทุกจุด
    lowland = np.ones((n, n), bool)
    post_vh = np.full((n, n), -17.5)          # ฐาน: VHหลัง > −18 = ไม่ผ่านเพดาน absolute

    # (ก) เพดาน VH + opening: พิกเซลเดียวที่ผ่านทุกเงื่อนไขแต่โดดเดี่ยว = ถูกกลืน
    lone = post_vh.copy()
    lone[4, 4] = -22.0                        # ΔVH = −2 ✓ · VH = −22 ≤ −18 ✓
    assert detect(pre_vh, lone, pre_vv, post_vv, lowland).sum() == 0

    # (ข) บล็อก 3×3 ที่ผ่านทุกเงื่อนไข = รอดครบ 9 px
    block = post_vh.copy()
    block[3:6, 3:6] = -22.0
    w = detect(pre_vh, block, pre_vv, post_vv, lowland)
    assert w.sum() == 9 and w[3:6, 3:6].all()

    # (ค) ΔVH = −0.5 ไม่ถึงเกณฑ์ (แม้ VH ต่ำ) = ไม่เป็นน้ำ
    dh = pre_vh.copy()
    dh[3:6, 3:6] = -21.5
    assert detect(dh, block, pre_vv, post_vv, lowland).sum() == 0

    # (ง) ΔVV = −1 ไม่ถึงเกณฑ์ = ไม่เป็นน้ำ
    dv = pre_vv.copy()
    dv[3:6, 3:6] = -22.0
    assert detect(pre_vh, block, dv, post_vv, lowland).sum() == 0

    # (จ) นอก lowland = ไม่นับแม้สัญญาณผ่าน
    low2 = lowland.copy()
    low2[3:6, 3:6] = False
    assert detect(pre_vh, block, pre_vv, post_vv, low2).sum() == 0

    # (ฟ) NaN กลางบล็อก = ไม่นับ + opening กัดบล็อกที่มีรูออกทั้งบล็อก
    nanv = post_vv.copy()
    nanv[4, 4] = np.nan
    assert detect(pre_vh, block, pre_vv, nanv, lowland).sum() == 0


# ---------- attribution_share: อินทิกราลราย 15 นาที (ผลรีวิว GLM GL-01) ----------

def test_attribution_integrate_is_15min_and_captures_subhourly_peak():
    """อินทิกราลต้องก้าวราย 15 นาที — รุ่นก่อนแก้ (8 ต.ค. 69) ก้าวรายชั่วโมงทั้งที่ป้ายบอก
    15 นาที ทำให้พีคที่เกิดนาที 15/30/45 หลุดทั้งหมดบนไฮโดรกราฟคม"""
    from attribution_share import integrate
    t0 = dt.datetime(2026, 9, 27, 10)
    series = {}
    for i in range(8):                        # ครอบหน้าต่าง 2 ชม.
        t = t0 + dt.timedelta(minutes=15 * i)
        series[t] = 500.0 if t == t0 + dt.timedelta(minutes=30) else 100.0
    total15, n15 = integrate(series, (t0, t0 + dt.timedelta(hours=2)), step_min=15)
    assert n15 == 8
    # ไรมันน์: (7×100 + 500) ม³/วิ × 900 วิ = 1.08 ล้าน ลบ.ม. — พีคนาที 30 ถูกนับครบ
    assert abs(total15 - 1.08) < 1e-9
    # การก้าวรายชั่วโมง (บั๊กรุ่นเดิม) มองไม่เห็นพีคนาที 30: 2×100×3600 = 0.72 ล้าน ลบ.ม.
    total60, n60 = integrate(series, (t0, t0 + dt.timedelta(hours=2)), step_min=60)
    assert n60 == 2 and abs(total60 - 0.72) < 1e-9
    assert total15 > total60
