"""R7-08: ทะเบียนตัวตนของปริมาณ — โครงสร้างครบ, ชี้ canonical ได้, ค่าคงที่ต้นทางไม่ขัด canonical, การโต้แย้งส่งต่อ"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import quantity_registry as qr  # noqa: E402


def _reg():
    return json.loads(qr.REG.read_text(encoding="utf-8"))["quantities"]


def test_registry_passes_all_checks():
    errs, _ = qr.check()
    assert not errs, errs


def test_disputed_propagates_to_dependents():
    _, eff = qr.check()
    assert eff["canal_storage_total"] == ["canal_storage_total"]
    assert "canal_storage_total" in eff["canal_storage_active"]
    assert eff["canal_bed_width"] == []


def test_conflicting_source_constant_is_flagged():
    reg = copy.deepcopy(_reg())
    for q in reg:
        if q["id"] == "opex_annual":
            q["source_constant"] = "clarify2_opex_annual_mb"   # 519 ไม่ใช่ค่ามาตรฐาน แต่อยู่ใน variants → ต้องไม่ขัด
    errs, _ = qr.check(reg)
    assert not [e for e in errs if "opex_annual" in e]
    for q in reg:
        if q["id"] == "canal_bed_width":
            q["source_constant"] = "capex_mb"                 # ค่าไม่เกี่ยวกัน → ต้องถูกจับ
    errs, _ = qr.check(reg)
    assert any("canal_bed_width" in e for e in errs)


def test_cycle_and_missing_dependency_detected():
    reg = copy.deepcopy(_reg())
    for q in reg:
        if q["id"] == "canal_bed_width":
            q["depends_on"] = ["canal_storage_total"]
    errs, _ = qr.check(reg)
    assert any("วน" in e for e in errs)
    reg = copy.deepcopy(_reg())
    reg[0]["depends_on"] = ["ไม่มีตัวนี้"]
    errs, _ = qr.check(reg)
    assert any("ไม่มีในทะเบียน" in e for e in errs)


def test_every_reconciled_parameter_registered():
    canon = json.loads(qr.CANON.read_text(encoding="utf-8"))
    reg = _reg()
    refs = {q["canonical_ref"].split(".")[1] for q in reg if q.get("canonical_ref")}
    assert set(canon["reconciled_parameters"]) <= refs
