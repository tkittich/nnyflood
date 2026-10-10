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
REPORTS = ["report/ระลอกปลายกย2569_6ลุ่ม.html", "report/ชุดเทียบมาตรฐาน2554.html"]


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
    assert d["c2_attribution"]["scenarios"][-1]["drop_m"] == 2.22
    assert d["pasak_over_years"] == "20/22"


def test_report_html_matches_canonical_flood_and_rain():
    """ตัวเลขหลักใน HTML ต้องตรง canonical (ไม่ใช่แค่ไม่มีค่าเก่า — ค่าใหม่ต้องมีจริง)"""
    d = _load()
    h3 = (ROOT / REPORTS[0]).read_text(encoding="utf-8")
    assert f"{d['flood_peak_km2']['ping_cp']:.0f}" in h3 or "2,264" in h3
    assert f"{d['flood_peak_km2']['bkk_lower_after_sea']:,.0f}" in h3
    assert str(d["rain_national"]["top3_stations_7d"]) in h3
    assert str(d["rain_national"]["top3_cells_7d"]) in h3
    assert str(d["event_stations"]["n_usable_datum"]) in h3
    h4 = (ROOT / REPORTS[1]).read_text(encoding="utf-8")
    assert "20 จาก 22" in h4
    assert str(d["rain_2554_vs_2569"]["top3_cells_54"]) in h4


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
            f"{c2['scenarios'][0]['drop_m']:.2f}–{c2['scenarios'][-1]['drop_m']:.2f}",
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
