"""ตรวจโครงสร้างผลเทียบพื้นที่น้ำเรดาร์กับ GISTDA 30 วัน (docs/S1_GISTDA_CROSSCHECK_PREREG.md) — ไม่ฝังข้อสรุป"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
X = json.loads((ROOT / "analysis/goal6/s1_gistda_crosscheck.json").read_text(encoding="utf-8"))["basins"]
CAN = json.loads((ROOT / "analysis/goal6/canonical.json").read_text(encoding="utf-8"))


def test_metrics_are_valid_fractions_and_domain_share_consistent():
    for b, v in X.items():
        if v["status"] != "ok":
            continue
        for k in ("A_peak_scene", "B_union_all_scenes"):
            m = v[k]
            for key in ("precision", "recall", "f1", "share_of_radar_in_domain"):
                assert 0 <= m[key] <= 1.0001, (b, k, key)
            assert m["radar_km2"] <= m["radar_total_km2_whole_grid"] + 0.1
            assert m["label_low_precision"] == (m["precision"] < 0.50)


def test_union_covers_at_least_peak_scene():
    for b, v in X.items():
        if v["status"] == "ok":
            assert v["B_union_all_scenes"]["radar_total_km2_whole_grid"] >= v["A_peak_scene"]["radar_total_km2_whole_grid"] - 0.1


def test_canonical_ranges_follow_json():
    c = CAN["s1_gistda_crosscheck"]
    ok = [v for v in X.values() if v["status"] == "ok"]
    assert c["n_basins"] == len(ok)
    assert c["B_precision_range"] == [min(v["B_union_all_scenes"]["precision"] for v in ok), max(v["B_union_all_scenes"]["precision"] for v in ok)]
