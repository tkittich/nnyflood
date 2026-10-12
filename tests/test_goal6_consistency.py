"""เทสความสม่ำเสมอเป้าหมาย 6 — ตัวเลขในรายงาน/เอกสารต้องตรง canonical.json

สัญญา: ตัวเลขที่ปลดประจำการ (retired) ห้ามปรากฏในรายงาน/HANDOFF/GOAL6_PLAN/START_HERE
· ตัวเลขหลักต้องปรากฏใน canonical.json (ผลิตโดย analysis/goal6_canonical.py — ห้ามมือเขียน)

นี่คือชั้นที่รายงาน 1–2 มีอยู่แล้ว (test_artifacts ผูก canonical_numbers.json) — ต่อยอดให้เป้าหมาย 6
(ต้นทุนความไม่สม่ำเสมอที่เจอจริง: รีวิว 3 รอบเจอตัวเลขเก่าค้าง 8+ จุด)
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / "analysis/goal6/canonical.json"

DOCS = ["HANDOFF.md", "docs/GOAL6_PLAN.md", "START_HERE.md"]
REPORTS = ["report/ระลอกปลายกย2569.html", "report/ชุดเทียบมาตรฐาน2554.html"]


def _load() -> dict:
    return json.loads(CANON.read_text(encoding="utf-8"))


def test_canonical_exists_and_generated():
    d = _load()
    assert "rain_national" in d and "flood_peak_km2" in d and "retired" in d
    # canonical ต้องผลิตสดเทียบไฟล์ต้นทาง — ถ้าไม่รัน script แล้ว stale ให้ fail
    import subprocess, sys
    r = subprocess.run([sys.executable, str(ROOT / "analysis/goal6_canonical.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    fresh = _load()
    assert fresh["rain_national"] == d["rain_national"], "canonical.json ล้าสมณี — รัน analysis/goal6_canonical.py ใหม่"


def test_retired_numbers_absent():
    d = _load()
    surfaces = DOCS + REPORTS
    for retired, why in d["retired"]["retired_values"].items():
        for f in surfaces:
            p = ROOT / f
            if not p.exists():
                continue
            txt = p.read_text(encoding="utf-8")
            assert retired not in txt, f"{f}: พบตัวเลข/ข้อความที่ปลดประจำการแล้ว: {retired!r} ({why})"


def test_headline_numbers_present_in_canonical():
    """ตัวเลขหลักที่รายงานอ้าง ต้องตรง canonical (แหล่งเดียว)"""
    d = _load()
    rn = d["rain_national"]
    assert (rn["top3_stations_7d"], rn["n_stations"]) == (67, 199)
    assert rn["top3_cells_7d"] == 32
    assert d["flood_peak_km2"]["ping_cp"] == 2263.6
    assert d["flood_peak_km2"]["bkk_lower_after_sea"] == 1104.0
    es = d["event_stations"]
    assert (es["n_over_crit"], es["n_wave_peak"], es["n_pre_wave_peak"]) == (25, 17, 8)
    assert es["n_usable_datum"] == 6
    assert "C.2" in es["suspect_codes"]
    # H1 (Sonnet): เพดานลดพีค = ปล่อยวันพีค × ความชัน — ต้องไม่เกินเพดาน และไม่เกิน 3% ของน้ำผ่านพีค
    c2 = d["c2_attribution"]
    assert c2["max_drop_m_if_zero_release"] <= 0.3, "สถานการณ์ปล่อยล่วงหน้าเกินเพดาน (ปล่อยวันพีค 3% ของน้ำผ่าน)"
    assert c2["release_at_peak_mcm_day"] / 225.5 < 0.05
    assert "scenarios" not in c2, "สถานการณ์ลบส่วนเกินถูกถอนแล้ว (รีวิว Sonnet H1)"
    assert d["pasak_over_years"] == "20/22"
    tide = d["estuary_tide"]
    assert tide["cpy015_peak_m"] == 1.91
    assert tide["c12_peak_m"] == 2.24


def test_report_html_matches_canonical_flood_and_rain():
    """ตัวเลขหลักใน HTML ต้องตรง canonical (ไม่ใช่แค่ไม่มีค่าเก่า — ค่าใหม่ต้องมีจริง)"""
    d = _load()
    h3 = (ROOT / REPORTS[0]).read_text(encoding="utf-8")
    assert f"{d['flood_peak_km2']['ping_cp']:.0f}" in h3 or "2,264" in h3
    assert f"{d['flood_peak_km2']['bkk_lower_after_sea']:,.0f}" in h3
    assert str(d["rain_national"]["top3_stations_7d"]) in h3
    assert str(d["rain_national"]["top3_cells_7d"]) in h3
    assert str(d["event_stations"]["n_usable_datum"]) in h3
    assert f"{d['estuary_tide']['cpy015_peak_m']:.2f}" in h3
    assert f"{d['estuary_tide']['c12_peak_m']:.2f}" in h3
    # H6 (Sonnet): ห้ามอ้างจำนวน/สถานะประตูระบายที่ไม่มีข้อมูล
    for bad in ("ปิดบานเพื่อป้องกันน้ำเค็ม", "พึ่งพาระบบเครื่องสูบน้ำแบบบังคับระบาย 100%", "ถูกปิดกั้นโดยสิ้นเชิง"):
        assert bad not in h3, f"ข้อความเกินหลักฐาน (ไม่มีข้อมูลบานประตู): {bad}"
    assert "1–2 ม. ที่ C.2" not in h3 and "ได้ราว 2 ม." not in h3
    h4 = (ROOT / REPORTS[1]).read_text(encoding="utf-8")
    assert "20 จาก 22" in h4
    assert str(d["rain_2554_vs_2569"]["top3_cells_54"]) in h4
    # H1 (รีวิว GLM): ตารางอันดับกลางต้องตรง canonical (มัธยฐานมาตรฐาน)
    # A2: ตารางฝนเฉลี่ยลุ่ม — เลขฝนรวมฤดู/อันดับของทุกลุ่มต้องตรง canonical
    br = d["basin_rain"]["basins"]
    for b in ("ping_cp", "pasak", "bp_prach", "maeklong", "thachin", "nakhonnayok"):
        m = br[b]["season_total"]
        assert f"{m['v2554']:.0f} · อันดับ {m['rank2554']}" in h4, f"ฝนรวมฤดู 2554 {b} ไม่ตรง canonical"
        assert f"{m['v2569']:.0f} · อันดับ {m['rank2569']}" in h4, f"ฝนรวมฤดู 2569 {b} ไม่ตรง canonical"
    assert "ไม่ใช่ปีแล้ง" in h3 and "อันดับกลาง 39" not in h3


def test_builder_source_has_no_metric_literals():
    """กติกา builder ห้ามพิมพ์ตัวเลขหลัก — สแกนหา literal ที่เคยก่อปัญหา (H3/H4/H7/M8)"""
    import re
    banned_literals = [
        "1.7", "7.37", "17 จาก 22", "224.34", "0.92", "0.44",
        "ป่าสัก 241", "164 วัน", "127 วัน",  # เลขวันเกิน 2554 ต้องมาจาก dam_history_all
    ]
    for b in ("report/goal6_build_report3_draft.py", "report/goal6_build_report4_draft.py"):
        txt = (ROOT / b).read_text(encoding="utf-8")
        # 224.34/241/164/127 อนุญาตใน comment/docstring เท่านั้น — ตัดบรรทัด comment ออก
        code_lines = [ln for ln in txt.splitlines() if not ln.strip().startswith("#")]
        code = "\n".join(code_lines)
        for lit in ("224.34", "241 วัน", "164 วัน", "127 วัน"):
            assert lit not in code, f"{b}: ตัวเลข hardcode {lit!r} — อ่านจาก dam_history_all.json"
    # corr ต้องมาจาก c2_attribution.json — builder ห้ามมี "−0.92" ลอย ๆ
    t3 = (ROOT / "report/goal6_build_report3_draft.py").read_text(encoding="utf-8")
    code3 = "\n".join(ln for ln in t3.splitlines() if not ln.strip().startswith("#"))
    assert "−0.92)" not in code3.replace("(−0.92)", "") or "_corr_rel" in code3


def test_docs_carry_current_anchor_values():
    """เอกสารสถานะ (HANDOFF/PLAN) พิมพ์ตัวเลขขยับได้ = ต้องเป็นค่าปัจจุบันจาก canonical
    (กันแก้สคริปต์แล้วลืมเอกสาร — บั๊กที่รีวิวเจอซ้ำ 3 รอบ)"""
    d = _load()
    rn, es, c2 = d["rain_national"], d["event_stations"], d["c2_attribution"]
    anchors = {
        "HANDOFF.md": [
            f"{rn['top3_stations_7d']}/{rn['n_stations']}",
            f"{d['flood_peak_km2']['ping_cp']:,.0f}",
            f"{d['flood_peak_km2']['bkk_lower_after_sea']:,.0f}",
            f"{c2['max_drop_m_if_zero_release']:.2f}",
        ],
        "docs/GOAL6_PLAN.md": [
            f"{d['flood_peak_km2']['ping_cp']:,.0f}",
            f"{d['flood_peak_km2']['bkk_lower_after_sea']:,.0f}",
        ],
    }
    for f, needles in anchors.items():
        txt = (ROOT / f).read_text(encoding="utf-8")
        for n in needles:
            assert n in txt, f"{f}: ตัวเลขไม่ตรง canonical (คาด {n!r}) — รัน goal6_build_all.py แล้วอัปเดตเอกสาร"


def test_all_embedded_images_valid():
    """ทุกภาพ base64 ในรายงานต้องถอดรหัสเป็น PNG สมบูรณ์
    (เจอจริง 11 ต.ค.: thai() แทนคำต้องห้ามที่บังเอิญอยู่ใน base64 → ภาพเสีย 2/6 แผนที่)"""
    import base64, re
    for f in REPORTS:
        h = (ROOT / f).read_text(encoding="utf-8")
        imgs = re.findall(r"<img src='data:image/png;base64,([^']*)'", h)
        assert imgs, f"{f}: ไม่มีภาพเลย"
        for i, b64 in enumerate(imgs):
            raw = base64.b64decode(b64, validate=True)
            assert raw[:8] == b"\x89PNG\r\n\x1a\n", f"{f} img{i}: ไม่ใช่ PNG"
            assert b"IEND" in raw, f"{f} img{i}: PNG ไม่สมบูรณ์ (ไม่มี IEND)"


# ---- ค่าคงที่เชิงสถิติจากรีวิว Sonnet 12 ต.ค. 69 (กันผิดซ้ำ — เทสเดิมแค่ยืนยันค่า ไม่ตรวจความถูกต้อง) ----

def test_dam_storage_column_uses_event_window():
    """H3: 'เก็บสูงสุด 2569' ต้องเป็นสูงสุดในหน้าต่าง ก.ย.–ต.ค. เดียวกับ days_over_urc_sep_oct
    ไม่ใช่สูงสุดทั้งปีปฏิทิน (ยกยอดจากปีก่อน) · และตรงกับ screen (แหล่งต่างสคริปต์) ภายใน 1%"""
    dh = json.loads((ROOT / "analysis/goal6/dam_history_all.json").read_text(encoding="utf-8"))["dams"]
    sc = {d["name"]: d for d in json.loads(
        (ROOT / "analysis/goal6_screen_2026_summary.json").read_text(encoding="utf-8"))["dams"]}
    bad = []
    for name, rec in dh.items():
        y = next((r for r in rec.get("years", []) if r["year"] == 2026), None)
        if not y or y.get("max_storage_sep_oct") is None:
            continue
        win = y["storage_sep_oct"]
        assert max(win.values()) == y["max_storage_sep_oct"]
        assert all("09-01" <= d[5:10] <= "10-09" for d in win)
        ref = sc.get(name, {}).get("sep_oct_max_storage")
        if ref and abs(y["max_storage_sep_oct"] - ref) / ref > 0.01:
            bad.append((name, y["max_storage_sep_oct"], ref))
    assert not bad, f"ค่า 2569 ในหน้าต่างไม่ตรง screen: {bad}"


def test_l3_skill_vs_persistence_present_and_report_not_overclaiming():
    """H5: ทุก RMSE ต้องมีค่าเดิมคงที่คู่กัน · ห้ามคำว่า 'พิสูจน์ว่า' กับพยากรณ์"""
    d = _load()
    for b, v in d["l3_best"].items():
        for h in ("h6", "h24", "h48"):
            assert "persistence_cm" in v[h] and "skill_vs_persistence" in v[h], (b, h)
    assert d["l3_summary"]["n_basins"] == 6
    h3 = (ROOT / REPORTS[0]).read_text(encoding="utf-8")
    assert "พิสูจน์ว่า การพยากรณ์" not in h3 and "คลาดเคลื่อนทุกโมเดล" not in h3
    assert "ทำนายได้แม่น" not in h3


def test_flood_area_printed_with_coverage_and_thai_time():
    """H2/P3: พื้นที่น้ำท่วมต้องมีสัดส่วนที่ฉากครอบ + เวลาไทย · ห้ามเรียก 'จุดสูงสุด 1 ต.ค.' ลอย ๆ"""
    d = _load()
    fm = d["flood_peak_meta"]
    assert set(fm) >= {"pasak", "maeklong", "bp_prach", "thachin", "ping_cp", "bkk_lower"}
    for b, m in fm.items():
        assert 0 < m["coverage"] <= 1 and m["ict"] > m["utc"]
    h3 = (ROOT / REPORTS[0]).read_text(encoding="utf-8")
    assert "เวลาไทย" in h3 and "จุดสูงสุด) —" not in h3
    assert "1 ต.ค. 2569 จุดสูงสุด" not in h3


def test_rain_2554_md_rank_denominator_is_years():
    """M4: อันดับต่อปี (≤46) ห้ามพิมพ์เป็น '/199'"""
    md = (ROOT / "analysis/goal6/rain_rarity_2554.md").read_text(encoding="utf-8")
    assert "/199 |" not in md


def test_s1_rule_validation_wired_into_report():
    """M1/R9: ผลตรวจกฎตัดน้ำต้องเข้ารายงาน 3 (ข้อจำกัด (7)) · พื้นที่ฉากท่วมต้องมีช่วงตามเกณฑ์ · ห้าม 'ตรงกัน 72.7%'"""
    d = _load()
    r = d["s1_rule"]
    assert 0.5 < r["oct2"]["f1"] < 0.9 and r["oct2"]["f1_ci95"][0] < r["oct2"]["f1"] < r["oct2"]["f1_ci95"][1]
    lo, hi = r["peak_27sep"]["area_range_abs_pm2db"]
    assert lo < r["peak_27sep"]["area_km2"] < hi, "ค่ากลางต้องอยู่ในช่วงที่เลื่อนเกณฑ์ ±2 dB"
    assert set(r["basin_dark_share"]) >= {"pasak", "maeklong", "bp_prach", "thachin", "ping_cp", "bkk_lower"}
    h3 = (ROOT / REPORTS[0]).read_text(encoding="utf-8")
    assert "ความแม่นของกฎตัดน้ำ" in h3 and "ตรงกัน 72.7%" not in h3
    h1 = (ROOT / "report/น้ำท่วมนครนายก2569_ประชาชน.html").read_text(encoding="utf-8")
    assert "อ่านเป็นช่วง ไม่ใช่ตัวเลขเดียว" in h1 and 'จึงเป็น "ขอบล่าง"' not in h1
