"""ตรวจโครงสร้างผลความไวต่อวันของฉากอ้างอิง (docs/S1_PASS_MOSAIC_PREREG.md §3) และหน่วยรอบถ่ายของขั้นที่ 2 — ไม่ฝังข้อสรุป"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUM = json.loads((ROOT / "data/22_goal6_network/derived/s1_stage2/summary.json").read_text(encoding="utf-8"))
RS_FILES = sorted((ROOT / "analysis/goal6").glob("s1_ref_sensitivity*.json"))     # ลุ่มตั้งต้น + ลุ่มอื่นที่ทดสอบ


def test_stage2_unit_is_pass_with_slices_and_max_extent():
    for b, v in SUM.items():
        keys = [(r["track"], r["scene"][17:25]) for r in v["scenes"]]
        assert len(keys) == len(set(keys)), b                      # หนึ่งรอบถ่ายต่อวงต่อวัน
        for r in v["scenes"]:
            assert r["slices"] and r["scene"] == r["slices"][0] and r["n_slices"] == len(r["slices"])
            assert 0 <= r["coverage"] <= 1
        nonref = [r for r in v["scenes"] if r["reference"] != r["scene"]]
        assert v["max_extent"]["n_passes"] == len(nonref)
        assert v["max_extent"]["km2_lowland"] >= max(r["water_km2_lowland"] for r in nonref) - 0.1   # รวมทุกวันไม่น้อยกว่าวันเดียว
        assert 0 <= v["max_extent"]["covered_lowland_frac"] <= 1


def test_sensitivity_summary_consistent_if_present():
    for f in RS_FILES:
        d = json.loads(f.read_text(encoding="utf-8"))
        s = d["summary"]
        ev = [x for x in d["passes"] if x.get("role") == "event_or_after"]
        assert s["n_event_passes"] == len(ev), f.name
        assert s["peak_primary_km2"] == max(x["primary_km2"] for x in ev), f.name
        assert s["peak_alt_ref_km2"] == max(x["alt_ref_km2"] for x in ev), f.name
        assert s["label_sensitive_to_reference"] == (abs(s["peak_change_pct"]) > 10.0), f.name
        assert s["basin"] in SUM, f.name
