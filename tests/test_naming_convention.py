# ระเบียบชื่อไฟล์ใน analysis/ — ดู AGENTS.md หัวข้อ "การสืบค้นและระเบียบชื่อไฟล์"
#
# กฎ (แก้ 17 ต.ค. 69): ไฟล์ .py ใน analysis/ ต้องเข้าหนึ่งในสองประเภท
#   (ก) สคริปต์ตามเป้าหมาย — ขึ้นต้นด้วย goal<N>_ หรือ common_
#   (ข) โมดูลกลาง (core) ที่ลงทะเบียนใน CORE_MODULES ด้านล่าง
#
# ทำไมมี allowlist แทนการบังคับเปลี่ยนชื่อ: 42 จาก 112 ไฟล์เป็น core ที่เกิดก่อนกฎ
# (common.py, build_canonical_numbers.py, hydraulic_1d_routing.py, ...) การเปลี่ยนชื่อ
# จะทำให้ import พังทั้งคลังและต้องแก้ catalog 97 รายการ โดยไม่ได้ประโยชน์เชิงวิเคราะห์
# allowlist นี้จึงเป็น "ภาพสถาปัตยกรรมจริง" ไม่ใช่ถังขยะ — ไฟล์ใหม่ที่ไม่เข้าสองประเภท
# จะ fail ทันที และการเพิ่ม core ต้องแก้รายการนี้อย่างตั้งใจ
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"

GOAL_PREFIX = re.compile(r"^(goal\d+_|common_)")

CORE_MODULES = frozenset({
    # --- โครงกลาง / canonical / QA ---
    "common.py", "build_canonical_numbers.py", "run_all.py", "verify_data_integrity.py",
    "attribution_share.py", "rain_window.py", "all_stations_network.py",
    "archive_forecasts_daily.py", "thachang_leadtime.py",
    # --- ดาวเทียม S1 / S2 / Landsat ---
    "s1_change_detect.py", "s1_masks.py", "s1_merge_scenes.py", "s1_pairs_animation.py",
    "s1_peak_flood_map.py", "s1_process.py", "s2_truecolor_process.py", "s2_water.py",
    "landsat_water.py", "calibrate_s1_thresholds.py",
    # --- geo-referencing / GISTDA ---
    "georef_corner_match.py", "georef_fit.py", "georef_gistda.py",
    "gistda_georef_compare.py", "gistda_pass_areas.py", "fetch_gistda_flood.py",
    # --- นำเข้าข้อมูล ---
    "fetch_khundan_fullyears.py", "fetch_khundan_training.py",
    "fetch_khundan_training_2021_2022.py", "fetch_khundan_training_2024_2025.py",
    "fetch_multistation_levels.py", "national_pull_waterlevels.py",
    # --- ชลศาสตร์ / แบบจำลอง ---
    "hydraulic_1d_routing.py", "hecras_lite_channel.py", "compound_flood_risk.py",
    "rid_cross_section_extract.py", "rid_cross_section_hydraulics.py",
    "rid_cross_section_plot.py", "rid_cross_section_stage_rating.py",
    # --- สื่อ / อัลบั้ม ---
    "album_append.py", "album_geotag_map.py", "album_scan_batch.py",
    # --- QA เฉพาะกิจ ---
    "qa5_rain_drainage_counterfactual.py",
})


def test_analysis_scripts_follow_naming_rule():
    """ทุกไฟล์ใน analysis/ ต้องขึ้นต้นด้วย goal<N>_/common_ หรืออยู่ใน CORE_MODULES"""
    offenders = [
        p.name for p in sorted(ANALYSIS.glob("*.py"))
        if not (GOAL_PREFIX.match(p.name) or p.name in CORE_MODULES)
    ]
    assert not offenders, (
        "ไฟล์ใน analysis/ ต้องขึ้นต้นด้วย goal<N>_ หรือ common_ "
        f"หรือลงทะเบียนใน CORE_MODULES — พบไฟล์ใหม่ที่ยังไม่เข้าประเภท: {offenders}"
    )


def test_core_modules_allowlist_has_no_ghosts():
    """allowlist ต้องไม่มีชื่อไฟล์ที่ถูกลบ/เปลี่ยนชื่อแล้ว — รายการค้างทำให้กฎอ่อนลงเงียบ ๆ"""
    present = {p.name for p in ANALYSIS.glob("*.py")}
    ghosts = sorted(CORE_MODULES - present)
    assert not ghosts, f"CORE_MODULES อ้างไฟล์ที่ไม่มีอยู่จริง: {ghosts}"


def test_core_modules_are_not_goal_scripts():
    """ไฟล์ที่ขึ้นต้นตามกฎอยู่แล้วไม่ต้องอยู่ใน allowlist — กันการลงทะเบียนซ้ำสองทาง"""
    redundant = sorted(n for n in CORE_MODULES if GOAL_PREFIX.match(n))
    assert not redundant, f"CORE_MODULES ไม่ควรมีไฟล์ที่ขึ้นต้นตามกฎอยู่แล้ว: {redundant}"
