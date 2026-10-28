"""analysis/common_render_status.py — ทะเบียนสถานะการเรนเดอร์ต่อคีย์ของ canonical.json (เป้าหมาย 6 และ 7)

ทำไมต้องมี: รอบรีวิว 8–9 เจอซ้ำว่าผลวิเคราะห์เสร็จและลง canonical แล้ว แต่ไม่ถึงหน้ารายงาน (หรือไม่มีใครรู้ว่าถึงหรือไม่)
— ทะเบียนนี้บังคับให้ทุกคีย์ระดับบนมีสถานะที่ตรวจได้ แล้วให้เทสต์เทียบกับซอร์สตัวสร้างใน report/*.py จริง

สถานะ:
- rendered        ตัวสร้างใน report/ อ่านคีย์นี้ (ระบุไฟล์ใน builders) — ต้องอ่านจริงอย่างน้อยหนึ่งไฟล์
- cross_check_only ตัวสร้างไม่อ่านคีย์นี้ แต่ค่าเดียวกันออกรายงานผ่านเส้นทางอื่น และเทสต์ใช้เทียบ (ต้องมี reason)
- internal_only   ยังไม่ออกรายงานใด (ต้องมี reason) — ตัวสร้างต้องไม่อ่านคีย์นี้ ถ้าเริ่มอ่านต้องเปลี่ยนเป็น rendered
- superseded_by   ถูกคีย์อื่นแทน (ระบุ key ที่ต้องมีอยู่จริงและไม่ใช่ superseded_by/internal_only)
- metadata        คีย์โครงสร้างของ canonical เอง (ไม่ใช่ผลวิเคราะห์)

ไฟล์นี้เป็นแหล่งจริงของทะเบียน — goal6_canonical.py และ goal7_analysis.py แนบสำเนาลง canonical.json ใต้คีย์ render_status
(อย่าแก้ canonical.json ด้วยมือ) · เพิ่มคีย์ใหม่ใน canonical = เพิ่มแถวที่นี่ ไม่งั้นเทส test_render_status ตก
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
STATUSES = ("rendered", "cross_check_only", "internal_only", "superseded_by", "metadata")

GOAL6 = {
    "rain_national": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "rain_2554_vs_2569": {"status": "cross_check_only", "reason": "report4 คำนวณจำนวนจุดวัดอันดับ 1–3 ของปี 2554 จากไฟล์ดิบเอง (goal6_build_report4_draft.py: _t54) — canonical เก็บสำเนาไว้ให้เทส test_goal6_consistency เทียบกับ HTML"},
    "flood_peak_km2": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "flood_peak_meta": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "dam_inflow": {"status": "rendered", "builders": ["goal6_build_report3_draft.py", "goal6_build_report4_draft.py"]},
    "basin_rain": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "exposure": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "s1_landcover": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "s1_rule": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "s1_gistda_crosscheck": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "s1_ref_sensitivity": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "s1_ref_sensitivity_other": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "s1_ref_dates": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "s1_control_rain": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "s1_orbit31_check": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "event_stations": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "l3_best": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "l3_summary": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "c2_attribution": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "bhumibol": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "dams_2554_over_urc_days": {"status": "rendered", "builders": ["goal6_build_report4_draft.py"]},
    "pasak_over_years": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "pasak_over_mid_rain_years": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "estuary_tide": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "estuary_salinity": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "gulf_marine_swan": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "glofas_streamflow": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "gistda_disaster_platform": {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]},
    "national_medium_reservoirs": {"status": "rendered", "builders": ["goal6_build_report3_draft.py", "goal6_build_report4_draft.py"]},
    "pasak_24y_baseline": {"status": "rendered", "builders": ["goal6_build_report3_draft.py", "goal6_build_report4_draft.py"]},
    "pasak_year_counts": {"status": "cross_check_only", "reason": "บัญชีนิยามสี่แบบของ 'ปีที่น้ำเกิน' ป่าสักชลสิทธิ์ (ดู definitions) — รายงาน 3–4 พิมพ์จำนวนผ่าน pasak_over_years และ pasak_24y_baseline; เทสเทียบค่ากับบัญชีนี้"},
    "l3_coastal_coupled": {"status": "rendered", "builders": ["goal6_build_report4_draft.py"]},
    "compound_flood_risk": {"status": "rendered", "builders": ["goal6_build_report4_draft.py"]},
    "l3_coastal_harmonics": {"status": "rendered", "builders": ["goal6_build_report4_draft.py"]},
    "bp_downstream": {"status": "rendered", "builders": ["goal6_bp_downstream.py"]},
    "definitions": {"status": "metadata"},
    "retired": {"status": "metadata"},
}

GOAL7 = {
    "meta": {"status": "metadata"},
    "facts": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_common.py"]},
    "reconciled_parameters": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_policy_brief.py", "goal7_build_public.py"]},
    "canal_volume_check": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "design_segments": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "design_2566": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py"]},
    "dwr_plan": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py"]},
    "eia_land": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "eia_econ": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "eia_social": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py"]},
    "concern_checks": {"status": "rendered", "builders": ["goal7_build_academic.py"]},
    "eia_section": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
    "eia_levels": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
    "eia_profile": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_policy_brief.py", "goal7_build_public.py", "goal7_common.py"]},
    "design_2565": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py"]},
    "design_2565_structs": {"status": "superseded_by", "key": "struct_compare", "reason": "ค่าอาคารตามแบบ 2565 ถูกป้อนเข้า struct_compare (goal7_analysis.py:669–670) ซึ่งตัวสร้างอ่านและพิมพ์แล้ว"},
    "meeting_20260909": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "struct_compare": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py"]},
    "design_2560": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py"]},
    "participation": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "concerns": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py"]},
    "civic_funding": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py"]},
    "design_history": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "eia_versions": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
    "eia_structs": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
    "alignment_qa": {"status": "rendered", "builders": ["goal7_build_academic.py"]},
    "provinces_km": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_common.py"]},
    "structures": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
    "dem": {"status": "rendered", "builders": ["goal7_common.py"]},
    "manning": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_common.py"]},
    "c2": {"status": "rendered", "builders": ["goal7_common.py"]},
    "pasak_dam": {"status": "rendered", "builders": ["goal7_common.py"]},
    "corridor_area": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_common.py"]},
    "flood_band": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_common.py"]},
    "embankment": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
    "basins_2569": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_common.py"]},
    "reading_coverage": {"status": "rendered", "builders": ["goal7_build_academic.py"]},
    "options": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
    "runoff": {"status": "rendered", "builders": ["goal6_reportlib.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "extra_q": {"status": "rendered", "builders": ["goal7_build_public.py"]},
    "new_cases": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
    "ocr_facts": {"status": "rendered", "builders": ["goal7_build_academic.py"]},
    "acid_soil": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_policy_brief.py", "goal7_build_public.py"]},
    "nn_venues_2566": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "nuclear_site": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "bpk_role": {"status": "rendered", "builders": ["goal7_build_academic.py", "goal7_build_public.py"]},
    "golf_case": {"status": "rendered", "builders": ["goal7_build_public.py"]},
    "concern_short": {"status": "rendered", "builders": ["goal7_build_public.py"]},
    "nn_water_users": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "eia_construction": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "ongkharak_flood": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "illustrative_only": {"status": "internal_only", "reason": "ผลจำลองรูปคลื่นสังเคราะห์ (ความจุ 2,600 · dQ/dh 1,100 ไม่มีที่มา) — ตั้งใจไม่ลงรายงาน (รีวิวรอบ 6 A4)"},
    "ayutthaya_dqdh_rating": {"status": "internal_only", "reason": "ตารางสอบเทียบ dQ/dh อยุธยา–บางไทร (272–417) ยังไม่ถูกตัวสร้างเล่มใดอ่าน และยังไม่ได้ใช้แทนค่าสมมติ 1,100 ในการจำลองสวนข้อเท็จจริง (illustrative_only) — การแทนต้องมี docs/*_PREREG.md ก่อนรัน"},
    "ongkharak_2d_depression": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py"]},
    "legal_and_nuclear_assessment": {"status": "internal_only", "reason": "บทวิเคราะห์กฎหมายเวนคืนและศูนย์วิจัยนิวเคลียร์ ยังไม่มีตัวสร้างเล่มใดอ่านคีย์นี้ (ข้อความที่เกี่ยวข้องในรายงานมาจากคีย์ nuclear_site และข้อความพิมพ์เองในตัวสร้าง)"},
    "acid_sulfate_soil_assessment": {"status": "internal_only", "reason": "การประเมินปูนและต้นทุนดินกรดกำมะถัน ยังไม่มีตัวสร้างเล่มใดอ่านคีย์นี้ (รายงานอ่านพื้นที่ดินกรดจากคีย์ acid_soil)"},
    "interbasin_transfer_vectors": {"status": "internal_only", "reason": "เวกเตอร์ผันน้ำข้ามลุ่มรายประตู (ภาพ ณ 9 ต.ค. 69) ยังไม่มีตัวสร้างเล่มใดอ่านคีย์นี้"},
    "dam_to_gulf_corridors": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "bangban_bangsai_case": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_policy_brief.py"]},
    "operational_economics": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_policy_brief.py", "goal7_build_public.py"]},
    "dem_bias_correction": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py"]},
    "dem_waterline_test": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "dem_gistda_waterline_test": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "ongkharak_hydraulic_2d": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "mitrearth_layers": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "mitrearth_road_valley": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "s1_chachoengsao_recent": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "bangpakong_chachoengsao": {"status": "rendered", "builders": ["goal7_blocks.py"]},
    "mitrearth_national": {"status": "rendered", "builders": ["goal7_blocks.py", "goal7_build_academic.py", "goal7_build_public.py", "goal7_common.py"]},
}


REGISTRY = {"goal6": GOAL6, "goal7": GOAL7}


def attach(canonical: dict, goal: str) -> dict:
    """แนบทะเบียนลง canonical (เรียกท้ายตัวผลิต canonical)"""
    canonical["render_status"] = dict(REGISTRY[goal])
    return canonical


def builder_readers(key: str, report_dir: Path = REPORT_DIR) -> list[str]:
    """ชื่อไฟล์ใน report/*.py ที่มีสตริงคีย์เป็นตัวอักษรตรง ('key' หรือ "key")"""
    pat = re.compile("[\"']" + re.escape(key) + "[\"']")
    return sorted(p.name for p in report_dir.glob("*.py") if pat.search(p.read_text(encoding="utf-8")))


def problems(canonical: dict, goal: str, report_dir: Path = REPORT_DIR) -> list[str]:
    """ตรวจทะเบียนเทียบ canonical จริงและซอร์สตัวสร้าง — คืนรายการปัญหา (ว่าง = ผ่าน)"""
    reg = canonical.get("render_status")
    if reg is None:
        return ["canonical ไม่มี render_status — รันตัวผลิต canonical ใหม่"]
    out: list[str] = []
    keys = [k for k in canonical if k != "render_status"]
    for k in keys:
        if k not in reg:
            out.append(f"{k}: ไม่มีสถานะในทะเบียน (เพิ่มใน analysis/common_render_status.py)")
    for k in reg:
        if k not in canonical and k != "render_status":
            out.append(f"{k}: อยู่ในทะเบียนแต่ไม่มีใน canonical")
    for k, r in reg.items():
        st = r.get("status")
        if st not in STATUSES:
            out.append(f"{k}: สถานะ {st!r} ไม่รู้จัก")
            continue
        readers = builder_readers(k, report_dir)
        if st == "rendered":
            declared = r.get("builders") or []
            if not declared:
                out.append(f"{k}: rendered ต้องระบุ builders")
            for b in declared:
                if b not in readers:
                    out.append(f"{k}: ประกาศว่า {b} อ่านคีย์นี้ แต่ไม่พบในซอร์ส")
            if not readers:
                out.append(f"{k}: rendered แต่ไม่มีตัวสร้างใดอ่านคีย์นี้")
        elif st in ("internal_only", "cross_check_only"):
            if not r.get("reason"):
                out.append(f"{k}: {st} ต้องมี reason")
            if readers:
                out.append(f"{k}: {st} แต่ตัวสร้างอ่านอยู่ ({', '.join(readers)}) — เปลี่ยนเป็น rendered")
        elif st == "superseded_by":
            tgt = r.get("key")
            if tgt not in reg:
                out.append(f"{k}: superseded_by คีย์ {tgt!r} ซึ่งไม่อยู่ในทะเบียน")
            elif reg[tgt].get("status") in ("superseded_by", "internal_only"):
                out.append(f"{k}: คีย์ปลายทาง {tgt} มีสถานะ {reg[tgt]['status']} — ต้องเป็นคีย์ที่ออกรายงานจริง")
    return out
