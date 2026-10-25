"""R6-09 (ความไวอายุเศรษฐกิจ 30/50 ปี) และ R6-12 (ที่มาของยอด 87 อาคาร) — ตรวจโครงสร้างและความสอดคล้อง ไม่ตรวจว่าผลต้องออกทางใด"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
C = json.loads((ROOT / "analysis/goal7/canonical.json").read_text(encoding="utf-8"))
LE = C["operational_economics"]["lifecycle_economics"]


def test_life_sensitivity_has_three_rates_and_longer_life_lowers_annual_capital():
    ls = LE["life_sensitivity"]
    assert ls["alt_lifespan_years"] > LE["lifespan_years"] and len(ls["scenarios"]) == 3
    for a, b in zip(ls["scenarios"], LE["discount_scenarios"]):
        assert a["discount_rate_pct"] == b["discount_rate_pct"] and a["crf"] < b["crf"]          # อายุยาวขึ้น → CRF ต่ำลง (คณิตศาสตร์ ไม่ใช่ข้อสรุปงานวิจัย)
        assert abs(a["total_annual_cost_mb"] - (a["annualized_capital_mb"] + LE["opex_annual_mb"])) < 0.15


def test_structure_count_reconciliation_registered_and_catalogue_count_matches_file():
    sc = C["reconciled_parameters"]["structure_count"]
    v = sc["variants"]
    rows = sum(1 for _ in csv.DictReader(open(ROOT / "analysis/goal7/structures_all.csv", encoding="utf-8")))
    assert v["analyst_compilation"]["count"] == sc["canonical_value"] and v["project_catalogue_rows"]["count"] == rows
    assert v["analyst_compilation"]["tier"] == "C"          # ยอด 87 ยังไม่มีแหล่งทางการ
    bn = C["operational_economics"]["cross_drainage_bottlenecks"]
    typed = bn["eia_primary_siphons_and_culverts"] + bn["road_bridges"] + bn["railway_bridge"] + bn["navigation_locks"] + bn["mid_canal_gates"]
    assert typed < bn["total_crossing_structures"]           # แยกประเภทได้ไม่ครบ — ต้องเปิดเผยตามที่ resolution บอก
