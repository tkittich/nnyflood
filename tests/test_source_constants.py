"""รอบ 6: ค่าคงที่นำเข้าของเป้าหมาย 7 ต้องมีแหล่งอ้างอิงและผ่านการตรวจ — ไม่พิมพ์ตัวเลขซ้ำในสคริปต์"""
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_source_constants as sc  # noqa: E402

VER = ROOT / "analysis/goal7/source_constants_verification.json"
ALLOWED_FAILED = {"s26_flood_season_max_mcm"}   # ไม่พบ 5,830 ในหน้าที่ระบุ — บันทึกเป็นยังไม่ยืนยัน ไม่ถูกใช้ในรายงาน
ALLOWED_CONFLICT: set[str] = set()              # ตัดสินแล้ว 19 ต.ค. 69: opex = 264.80 (ตรวจแล้ว); 519 ตรวจไม่ได้ เก็บเป็น clarify2_opex_annual_mb


def test_every_constant_has_source_method_and_verification_plan():
    for cid in sc.all_ids():
        r = sc.record(cid)
        assert r["method"] in sc.METHODS, cid
        assert r["source"].get("doc"), f"{cid}: ต้องระบุเอกสารต้นทาง"
        if r["method"] in ("text_layer", "visual_reading"):
            assert r["verify"], f"{cid}: ค่าที่อ้างจากเอกสารต้องมีวิธีตรวจ"
            assert r["source"].get("pdf_page"), f"{cid}: ต้องระบุหน้า"


def test_verification_file_is_current_and_clean():
    ver = json.loads(VER.read_text(encoding="utf-8"))
    assert ver["constants_sha256"] == hashlib.sha256(sc.PATH.read_bytes()).hexdigest(), "รัน python analysis/goal7_verify_constants.py ใหม่"
    res = ver["results"]
    assert set(res) == set(sc.all_ids())
    failed = {k for k, v in res.items() if v["status"] == "failed"}
    assert failed <= ALLOWED_FAILED, f"ตรวจไม่ผ่าน: {sorted(failed - ALLOWED_FAILED)}"
    conflict = {k for k, v in res.items() if v["status"] == "conflict"}
    assert conflict == ALLOWED_CONFLICT, conflict
    assert res["clarify2_opex_annual_mb"]["status"] == "unverified"


def test_cross_section_identities_hold():
    b, d, z1 = sc.value("eia_bed_width_m"), sc.value("eia_depth_m"), sc.value("eia_z_inner")
    assert abs(d * (b + z1 * d) - sc.value("eia_area_m2")) < 0.5
    assert abs(b + 2 * d * math.sqrt(1 + z1 * z1) - sc.value("eia_wetted_perimeter_m")) < 0.05
    assert abs(sc.value("eia_area_m2") * sc.value("eia_velocity_ms") - sc.value("eia_table_q_m3s")) < 0.5   # Q = A·V


def test_scripts_do_not_reintroduce_literals_for_registered_constants():
    ops = (ROOT / "analysis/goal7_operational_economics.py").read_text(encoding="utf-8")
    for lit in ("519.0", "264.8", "160046.0", "1970.0", "= 0.07", "135_900.0"):
        assert lit not in ops, f"goal7_operational_economics.py: พิมพ์ {lit} ตรง — ใช้ K('<id>')"
    ga = (ROOT / "analysis/goal7_analysis.py").read_text(encoding="utf-8")
    assert "EIA_SECTION = {" in ga and '_K("eia_area_m2")' in ga
