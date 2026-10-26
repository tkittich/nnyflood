"""ตรวจโครงสร้างผลตรวจฉากอ้างอิงเรดาร์ขั้นที่ 2 (docs/S1_REFERENCE_AUDIT_PREREG.md) — ไม่ฝังข้อสรุป"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "analysis/goal6/s1_reference_audit.json").read_text(encoding="utf-8"))
SUM = json.loads((ROOT / "data/22_goal6_network/derived/s1_stage2/summary.json").read_text(encoding="utf-8"))


def test_every_event_reference_group_is_audited():
    """ทุกกลุ่มที่ฉากอ้างอิงถ่ายตั้งแต่ 24 ก.ย. ต้องอยู่ในผลตรวจ (ไม่เลือกบางกลุ่ม)"""
    want = {(b, hh) for b, v in SUM.items() for hh, t in v["tracks"].items()
            if t["reference"].split("_")[4][:8] >= "20260924"}
    got = {(s["basin"], s["hh"]) for s in R["scenes"]}
    assert want == got


def test_published_values_match_stage2_and_labels_follow_rule():
    for b, v in R["per_basin"].items():
        assert v["published_max_km2"] == max(r["water_km2_lowland"] for r in SUM[b]["scenes"])
        if v["published_max_km2"]:
            assert v["material_label"] == (abs(v["change_pct"]) > 10.0)
        assert v["audited_max_km2"] >= 0
