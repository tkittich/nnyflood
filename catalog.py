#!/usr/bin/env python3
"""catalog.py — เครื่องมือสืบค้นสารบัญข้อมูล โค้ด ตัวเลข และเอกสารของโปรเจกต์ (Zero-dependency CLI)

การใช้งาน:
    python catalog.py                     # ดูภาพรวมทั้ง 3 เสาหลัก รายงาน และไฟล์สำคัญ
    python catalog.py find <คำค้น>         # ค้นหาคำสำคัญในตัวเลข canonical, สเปก, และชื่อไฟล์
    python catalog.py goal <1..7>         # ดูไฟล์ที่เกี่ยวข้องกับเป้าหมายที่ระบุ
    python catalog.py check               # ตรวจสอบว่าไฟล์และโฟลเดอร์ทั้งหมดในสารบัญมีอยู่จริง
    python catalog.py audit               # ตรวจย้อนกลับ: เอกสารบนดิสก์ที่ยังไม่ลงทะเบียน (กัน N-04)
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PILLARS = {
    "1": {
        "title": "เสาที่ 1: ลุ่มน้ำนครนายก (เป้าหมาย 1–5)",
        "scope": "วิเคราะห์เหตุการณ์ 26–29 ก.ย. 2569: ฝนตกหนัก vs เขื่อนขุนด่านฯ, ไฮโดรกราฟ, Sentinel-1, แบบจำลองทำนายระดับน้ำ (Model v1)",
        "reports": [
            {
                "id": "1",
                "name": "รายงานที่ 1 — ฉบับประชาชน (อ่านง่าย)",
                "html": "report/น้ำท่วมนครนายก2569_ประชาชน.html",
                "builder": "report/build_report_html.py",
            },
            {
                "id": "2",
                "name": "รายงานที่ 2 — ฉบับวิชาการ (ตรวจสอบย้อนกลับได้ทุกตัวเลข)",
                "html": "report/น้ำท่วมนครนายก2569_วิชาการ.html",
                "builder": "report/build_expert_report.py",
            },
        ],
        "canonical": "analysis/canonical_numbers.json",
        "canonical_builder": "analysis/build_canonical_numbers.py",
        "docs": [
            "docs/METHODS.md",
            "docs/DATA_DICTIONARY.md",
            "docs/ANALYSIS_PLAN.md",
            "docs/RID_SWOC_GUIDE.md",
            "docs/THAIWATER_API_GUIDE.md",
            "docs/ESTUARY_AND_WEATHER_GUIDE.md",
            "analysis/goal5_policy_proposals.md",
        ],
        "key_scripts": [
            "analysis/attribution_share.py",
            "analysis/s1_peak_flood_map.py",
            "analysis/goal4_model_v1.py",
            "analysis/goal2_nny_medium_dams.py",
            "analysis/goal2_khundan_22y_baseline.py",
            "analysis/common_fetch_rid_swoc.py",
            "analysis/common_fetch_water_quality.py",
            "analysis/common_fetch_gulf_marine.py",
            "analysis/common_fetch_rain_stations.py",
            "analysis/common_fetch_weather_forecasts.py",
            "analysis/rid_cross_section_stage_rating.py",
            "analysis/hydraulic_1d_routing.py",
        ],
        "data_dirs": [
            "data/01_rid_khun_dan",
            "data/02_thaiwater",
            "data/13_sentinel1_copernicus",
            "data/23_rid_swoc",
            "data/24_estuary_waterquality",
            "data/25_gulf_marine_tides",
            "data/26_national_rainfall_stations",
            "data/27_weather_flood_forecasts",
        ],
    },
    "2": {
        "title": "เสาที่ 2: 6 ลุ่มน้ำทั่วประเทศ & ชุดเทียบมาตรฐานปี 2554 (เป้าหมาย 6)",
        "scope": "ขยายสู่ 6 ลุ่มน้ำทั่วประเทศ, พฤติกรรม 24 เขื่อนใหญ่ (กฟผ. vs ชลประทาน), สถิติฝน 46 ปี, ชุดเทียบมาตรฐานปี 2554 vs 2569",
        "reports": [
            {
                "id": "3",
                "name": "รายงานที่ 3 — ระลอกปลาย ก.ย. 2569: 6 ลุ่มน้ำทั่วประเทศ",
                "html": "report/ระลอกปลายกย2569.html",
                "builder": "report/goal6_build_report3_draft.py",
            },
            {
                "id": "4",
                "name": "รายงานที่ 4 — ชุดเทียบมาตรฐาน: เขื่อนทั่วประเทศ 2554 vs 2569",
                "html": "report/ชุดเทียบมาตรฐาน2554.html",
                "builder": "report/goal6_build_report4_draft.py",
            },
        ],
        "canonical": "analysis/goal6/canonical.json",
        "canonical_builder": "analysis/goal6_canonical.py",
        "docs": [
            "docs/GOAL6_PLAN.md",
            "docs/GOAL6_HYDRO2D_PLAN.md",
            "docs/GOAL6_PUBLIC_RELEASE_REVIEW.md",
            "docs/REMOTE_SENSING_APIS.md",
        ],
        "key_scripts": [
            "analysis/goal6_build_all.py",
            "analysis/goal6_dam_history_all.py",
            "analysis/goal6_pasak_24y_baseline.py",
            "analysis/goal6_national_medium_reservoirs.py",
            "analysis/goal6_basin_rain.py",
            "analysis/goal6_rain_rarity.py",
            "analysis/goal6_s1_landcover.py",
            "analysis/goal6_s1_rule_validation.py",
            "analysis/goal6_fetch_gistda_flood.py",
            "analysis/goal6_l3_coastal_model.py",
            "analysis/compound_flood_risk.py",
            "analysis/goal6_tide_gain_regression.py",
            "tools/number_inventory.py",
            "tools/doctor.py",
            "tools/registry.json",
        ],
        "data_dirs": [
            "data/12_gistda_flood",
            "data/22_goal6_network",
            "data/31_external_landcover",
        ],
    },
    "3": {
        "title": "เสาที่ 3: โครงการคลองเจ้าพระยา 2 (เป้าหมาย 7)",
        "scope": "คลองระบายน้ำหลากชัยนาท–ป่าสัก–อ่าวไทย (111 กม.), คันคลอง 3.2–4.8 ม., ไซฟอนตัดคลองเดิม 34 จุด, อาคารบังคับน้ำ 99 แห่ง, ผังน้ำ สทนช., ถาม–ตอบ 23 ข้อ",
        "reports": [
            {
                "id": "7",
                "name": "รายงานที่ 7 — คลองเจ้าพระยา 2 ฉบับประชาชน",
                "html": "report/คลองเจ้าพระยา2_ประชาชน.html",
                "builder": "report/goal7_build_public.py",
            },
            {
                "id": "8",
                "name": "รายงานที่ 8 — คลองเจ้าพระยา 2 ฉบับวิชาการ",
                "html": "report/คลองเจ้าพระยา2_วิชาการ.html",
                "builder": "report/goal7_build_academic.py",
            },
            {
                "id": "pb",
                "name": "สมุดปกขาวเชิงนโยบาย — บทเรียนจากบางบาล–บางไทร สู่ความเสี่ยงเมกะโปรเจกต์เจ้าพระยา 2",
                "html": "report/สมุดปกขาว_เจ้าพระยา2.html",
                "builder": "report/goal7_build_policy_brief.py",
            },
        ],
        "canonical": "analysis/goal7/canonical.json",
        "canonical_builder": "analysis/goal7_analysis.py",
        "docs": [
            "docs/GOAL7_PLAN.md",
            "docs/GOAL7_FOI_REQUESTS.md",
            "docs/BANGBAN_BANGSAI_COMPARISON.md",
            "docs/GOAL7_POLICY_BRIEF.md",
        ],
        "key_scripts": [
            "report/goal7_build_all.py",
            "report/goal7_build_policy_brief.py",
            "analysis/goal7_analysis.py",
            "analysis/goal7_eia_structs.py",
            "analysis/goal7_waterchart_overlay.py",
            "analysis/goal7_gaps_check.py",
            "analysis/goal7_counterfactual_simulation.py",
            "analysis/goal7_dam_to_gulf_hydraulics.py",
            "analysis/goal7_bangban_bangsai_comparison.py",
            "analysis/goal7_operational_economics.py",
            "analysis/goal7_batch_ocr_queue.py",
        ],
        "data_dirs": [
            "data/32_goal7_chaophraya2",
            "data/manual",
        ],
    },
}

def _registry_core_docs() -> list[tuple[str, str]]:
    """เอกสารแกนจากทะเบียน tools/registry.json (แหล่งความจริงเดียว — รอบ 6) · ฟิลด์ core=true + desc"""
    try:
        reg = json.loads((ROOT / "tools" / "registry.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [(d["path"], d.get("desc") or d.get("title", "")) for d in reg.get("docs", []) if d.get("core")]


# รายการที่ไม่ใช่เอกสารในทะเบียน (เครื่องมือ/เทสต์/บันทึกรีวิวใน docs/reviews/) — เอกสารแกนอื่นมาจาก registry.json
CORE_EXTRA = [
    ("tools/verify_all.py", "เครื่องมือตรวจความสมบูรณ์และมาตรฐานแบบครบวงจร (catalog, SHA-256, pytest)"),
    ("tests/test_thai_language_lint.py", "ระบบทดสอบและตรวจจับภาษาไทยอัตโนมัติ (Typo Registry, คำชน, คำทับศัพท์)"),
    ("docs/reviews/AUDIT_REDTEAM_2026-10-17.md", "รายงานผลการตรวจสอบอิสระโดย Red-Team รอบที่ 1 (Peer Review ฉบับเต็ม 3 เสาหลัก)"),
    ("docs/reviews/AUDIT_ROUND2_2026-10-17.md", "รายงานผลการตรวจสอบอิสระโดย Red-Team รอบที่ 2 (Delta Review & New Findings)"),
    ("docs/reviews/TRIAGE_ROUND5_2026-10-18.md", "การกลั่นกรองผลรีวิวอิสระรอบที่ 5 และแผนปฏิบัติการปรับปรุงระบบ"),
]

CORE_GOVERNANCE = _registry_core_docs() + CORE_EXTRA


def print_banner():
    print("=" * 76)
    print("  nnyflood — เครื่องมือค้นหาและสารบัญระบบ (Knowledge Atlas & Catalog)")
    print("=" * 76)


def cmd_overview():
    print_banner()
    print("💡 การสืบค้นรวดเร็ว: python catalog.py find <คำค้น>  |  python catalog.py goal <1..7>")
    print("-" * 76)

    for p_id, p_info in PILLARS.items():
        print(f"\n📌 {p_info['title']}")
        print(f"   ขอบเขต: {p_info['scope']}")
        print(f"   ตัวเลขทางการ: {p_info['canonical']}")
        print("   รายงานส่งมอบ:")
        for r in p_info["reports"]:
            exists = "✓" if (ROOT / r["html"]).exists() else "✗"
            print(f"     [{exists}] {r['name']}")
            print(f"         HTML   : {r['html']}")
            print(f"         Builder: {r['builder']}")

    print("\n" + "-" * 76)
    print("📋 กติกากลางและเอกสารมาตรฐาน (Governance & Standards):")
    for doc, desc in CORE_GOVERNANCE:
        exists = "✓" if (ROOT / doc).exists() else "✗"
        print(f"   [{exists}] {doc:<32} : {desc}")

    print("\n🧪 สถานะการทดสอบระบบ:")
    print("   • คำสั่งรันเทสต์ครบชุด: python -m pytest tests/ (จำนวนที่ผ่านแสดงท้ายการรัน — ไม่ hardcode ที่นี่)")
    print("   • คำสั่งตรวจข้อมูลดิบ : python analysis/verify_data_integrity.py --quick")
    print("=" * 76)


SYNONYMS: dict[str, list[str]] = {
    "ปตร": ["ปตร", "ประตูระบายน้ำ", "watergate", "sluice"],
    "ประตูระบายน้ำ": ["ปตร", "ประตูระบายน้ำ", "watergate", "sluice"],
    "สูบ": ["สูบ", "ปั๊ม", "pump", "สถานีสูบ", "เครื่องสูบ"],
    "ปั๊ม": ["สูบ", "ปั๊ม", "pump", "สถานีสูบ", "เครื่องสูบ"],
    "dem": ["dem", "fabdem", "dempro", "waterline", "ขอบน้ำ", "แบบจำลองความสูง", "goal7_dem_waterline_test", "goal7_indra_probe", "goal7_gap_reprobe", "goal7_indra_ocr_all", "goal7_ocr_accuracy_vs_textlayer", "goal7_indra_vs_typhoon", "goal7_indra_text_eval", "indra", "goal7_ocr_v2", "goal7_ongkharak_hydraulic_2d", "goal7_ocr_v2_tiers", "ocr v2", "goal7_layout_compare", "layout", "goal7_bangpakong_chachoengsao", "บางปะกง", "ฉะเชิงเทรา ท่วมนาน", "goal7_dem_gistda_waterline_test", "gistda", "goal7_dem_bias_correction"],
    "องครักษ์": ["องครักษ์", "ongkharak", "tny10", "tny9", "ny.7", "nyk000"],
    "รังสิต": ["รังสิต", "rangsit", "atg101", "bkk014", "bkk015", "คลอง 13", "พระธรรมราชา", "หกวา"],
    "ขุนด่าน": ["ขุนด่าน", "khun dan", "ท่าด่าน"],
    "บางปะกง": ["บางปะกง", "bang pakong", "bpk001", "bpk003", "tkgt58", "tkgt60"],
    "บางน้ำเปรี้ยว": ["บางน้ำเปรี้ยว", "bpk003", "bkk016", "bang nam priao"],
    "คลองหกวา": ["คลองหกวา", "หกวา", "bkk014", "bkk015"],
    "เจ้าพระยา 2": ["เจ้าพระยา 2", "cp2", "ชัยนาท-ป่าสัก", "คลองระบายน้ำหลาก"],
    "rule curve": ["rule curve", "เส้นกำกับ", "urc", "lrc"],
    "eia": ["eia", "รายงานผลกระทบสิ่งแวดล้อม", "eia_structs"],
    "สทนช": ["สทนช", "onwr", "ผังน้ำ"],
    "ชลประทาน": ["ชลประทาน", "rid", "swoc"],
    "ดาวเทียม": ["ดาวเทียม", "satellite", "sentinel", "s1", "gistda"],
    "แบบจำลอง": ["แบบจำลอง", "model", "routing", "counterfactual", "hydraulic"],
}


def _expand_query(query: str) -> list[str]:
    q_clean = query.strip().lower()
    terms = [q_clean]
    for syn_key, syn_list in SYNONYMS.items():
        if syn_key.lower() in q_clean or q_clean in syn_key.lower():
            for s in syn_list:
                s_lower = s.lower()
                if s_lower not in terms:
                    terms.append(s_lower)
    return terms


def _search_json_keys(data, query: str, prefix="") -> list[tuple[str, str]]:
    results = []
    q_lower = query.lower()
    if isinstance(data, dict):
        for k, v in data.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if q_lower in str(k).lower():
                val_snippet = str(v)[:80].replace("\n", " ")
                results.append((full_key, val_snippet))
            results.extend(_search_json_keys(v, query, full_key))
    elif isinstance(data, list):
        for i, item in enumerate(data[:30]):
            full_key = f"{prefix}[{i}]"
            if isinstance(item, (dict, list)):
                results.extend(_search_json_keys(item, query, full_key))
            elif q_lower in str(item).lower():
                results.append((full_key, str(item)[:80]))
    elif isinstance(data, str) and q_lower in data.lower():
        if prefix and len(data) < 200:
            results.append((prefix, data[:80].replace("\n", " ")))
    return results


def _search_code_ast(terms: list[str]) -> list[tuple[str, int, str, str]]:
    """ค้นหาชื่อโมดูล, docstring, ฟังก์ชัน และคลาสใน analysis/, report/, tools/ ด้วย AST"""
    results = []
    for sub in ["analysis", "report", "tools"]:
        sub_path = ROOT / sub
        if not sub_path.exists():
            continue
        for p in sorted(sub_path.glob("**/*.py")):
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                content_lower = content.lower()
                if not any(t in content_lower for t in terms):
                    continue
                tree = ast.parse(content, filename=str(p))
                mod_doc = ast.get_docstring(tree) or ""
                rel_path = p.relative_to(ROOT).as_posix()

                if any(t in mod_doc.lower() for t in terms):
                    first_line = mod_doc.strip().splitlines()[0] if mod_doc.strip() else ""
                    results.append((rel_path, 1, "module", first_line[:100]))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        kind = "class" if isinstance(node, ast.ClassDef) else "def"
                        fn_doc = ast.get_docstring(node) or ""
                        name_match = any(t in node.name.lower() for t in terms)
                        doc_match = any(t in fn_doc.lower() for t in terms)
                        if name_match:
                            desc = f"{node.name}()" if kind == "def" else node.name
                            if fn_doc:
                                desc += f" — {fn_doc.strip().splitlines()[0][:70]}"
                            results.append((rel_path, node.lineno, kind, desc))
                        elif doc_match:
                            doc_first = fn_doc.strip().splitlines()[0][:70]
                            results.append((rel_path, node.lineno, kind, f"{node.name}(): {doc_first}"))
            except Exception:
                pass
    return results


def _search_data_manifests(terms: list[str]) -> list[tuple[str, str, list[str]]]:
    """ค้นหาข้อมูลใน data/**/manifest.md ครอบคลุมคลังข้อมูล 200GB โดยไม่ต้องอ่านไฟล์ไบนารีขนาดใหญ่"""
    results = []
    data_dir = ROOT / "data"
    if not data_dir.exists():
        return results

    for p in sorted(data_dir.glob("**/manifest.md")):
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            content_lower = content.lower()
            if not any(t in content_lower for t in terms):
                continue
            lines = content.splitlines()
            title = lines[0].lstrip("#").strip() if lines else p.parent.name
            matched_lines = []
            for i, line in enumerate(lines, 1):
                line_lower = line.lower()
                if any(t in line_lower for t in terms) and not line.startswith("#"):
                    clean = line.strip().lstrip("-* ").replace("`", "")
                    if clean and len(clean) > 3:
                        matched_lines.append(f"L{i}: {clean[:90]}")
                        if len(matched_lines) >= 3:
                            break
            rel_dir = p.parent.relative_to(ROOT).as_posix()
            results.append((rel_dir, title, matched_lines))
        except Exception:
            pass
    return results


def _search_telemetry_stations(terms: list[str]) -> list[tuple[str, str, str]]:
    """ค้นหาสถานีโทรมาตรและประตูระบายน้ำจากฐานข้อมูล ThaiWater"""
    results = []
    seen = set()

    # 1. ฐานข้อมูลประตูระบายน้ำพร้อมค่าปัจจุบัน
    wg_file = ROOT / "data/02_thaiwater/raw/2026-10-09_watergate_load.json"
    if wg_file.exists():
        try:
            with open(wg_file, encoding="utf-8") as f:
                d = json.load(f)
            for item in d.get("watergate_data", {}).get("data", []):
                st = item.get("station", {})
                name_th = (st.get("tele_station_name") or {}).get("th", "")
                code = st.get("tele_station_oldcode") or ""
                check_str = f"{code} {name_th}".lower()
                if any(t in check_str for t in terms):
                    if code and code not in seen:
                        seen.add(code)
                        win = item.get("watergate_in")
                        wout = item.get("watergate_out")
                        details = f"ระดับน้ำ เหนือ: {win} / ท้าย: {wout} ม.รทก."
                        full_name = name_th if (name_th.startswith("ปตร") or name_th.startswith("ประตู")) else f"ปตร.{name_th}"
                        results.append((code, full_name, details))
        except Exception:
            pass

    # 2. ฐานข้อมูลสถานีโทรมาตรทั่วประเทศ 11,483 จุด
    st_file = ROOT / "data/02_thaiwater/raw/station_all.json"
    if st_file.exists():
        try:
            with open(st_file, encoding="utf-8") as f:
                d = json.load(f)
            for item in d.get("data", []):
                code = item.get("station_old_code") or ""
                name_th = (item.get("station_name") or {}).get("th", "")
                prov = (item.get("province_name") or {}).get("th", "")
                amphoe = (item.get("amphoe_name") or {}).get("th", "")
                lat = item.get("station_lat")
                lon = item.get("station_long")
                check_str = f"{code} {name_th} {prov} {amphoe}".lower()
                if any(t in check_str for t in terms):
                    if code and code not in seen:
                        seen.add(code)
                        loc_str = f"อ.{amphoe} จ.{prov}" if amphoe and prov else (prov or "")
                        results.append((code, f"{name_th} ({loc_str})", f"พิกัด: {lat}, {lon}"))
                        if len(results) >= 15:
                            break
        except Exception:
            pass

    return results


def cmd_find(query: str):
    print_banner()
    terms = _expand_query(query)
    term_str = f"'{query}'"
    if len(terms) > 1:
        term_str += f" (ขยายคำพ้อง: {', '.join(terms[1:5])})"
    print(f"🔍 ผลการค้นหาสำหรับ: {term_str}\n")
    found_any = False

    # 1. ค้นหาในชื่อไฟล์
    matched_files = []
    for sub in ["analysis", "docs", "report", "tests"]:
        p = ROOT / sub
        if p.exists():
            for f in p.glob("**/*"):
                if f.is_file() and any(t in f.name.lower() for t in terms):
                    matched_files.append(f.relative_to(ROOT))

    if matched_files:
        found_any = True
        print(f"📁 ชื่อไฟล์ที่ตรงกัน ({len(matched_files)} ไฟล์):")
        for f in matched_files[:12]:
            print(f"   • {f}")
        if len(matched_files) > 12:
            print(f"     ... และอีก {len(matched_files) - 12} ไฟล์")
        print()

    # 2. ค้นหาในโค้ด (AST: Module docstring, Class, Function)
    code_matches = _search_code_ast(terms)
    if code_matches:
        found_any = True
        print(f"💻 ฟังก์ชัน คลาส และสคริปต์วิเคราะห์ ({len(code_matches)} จุด):")
        for fpath, lno, kind, desc in code_matches[:12]:
            print(f"   • {fpath}:{lno} [{kind}] {desc}")
        if len(code_matches) > 12:
            print(f"     ... และอีก {len(code_matches) - 12} รายการ")
        print()

    # 3. ค้นหาในสารบัญข้อมูลดิบ 200GB (Data Manifests)
    manifest_matches = _search_data_manifests(terms)
    if manifest_matches:
        found_any = True
        print(f"📦 ข้อมูลดิบและเมทาดาตาใน data/ ({len(manifest_matches)} โฟลเดอร์):")
        for fdir, title, snippets in manifest_matches[:8]:
            print(f"   • {fdir} — {title}")
            for s in snippets[:2]:
                print(f"       ↳ {s}")
        if len(manifest_matches) > 8:
            print(f"     ... และอีก {len(manifest_matches) - 8} โฟลเดอร์")
        print()

    # 4. ค้นหาใน Canonical JSONs และทะเบียนช่องว่าง
    canonical_files = [
        ("เป้าหมาย 1–5", ROOT / "analysis/canonical_numbers.json"),
        ("เป้าหมาย 6", ROOT / "analysis/goal6/canonical.json"),
        ("เป้าหมาย 7", ROOT / "analysis/goal7/canonical.json"),
        ("ทะเบียนช่องว่างเป้าหมาย 7", ROOT / "analysis/goal7/gaps.json"),
    ]

    for label, cpath in canonical_files:
        if not cpath.exists():
            continue
        try:
            with open(cpath, encoding="utf-8") as f:
                cdata = json.load(f)
            matches = []
            for t in terms:
                matches.extend(_search_json_keys(cdata, t))
            unique_matches = []
            seen_keys = set()
            for k, v in matches:
                if k not in seen_keys:
                    seen_keys.add(k)
                    unique_matches.append((k, v))
            if unique_matches:
                found_any = True
                print(f"🔢 ตัวเลขและคีย์ใน {label} ({cpath.relative_to(ROOT)}):")
                for k, v in unique_matches[:6]:
                    print(f"   • {k}: {v}")
                if len(unique_matches) > 6:
                    print(f"     ... พบทั้งหมด {len(unique_matches)} จุดในไฟล์นี้")
                print()
        except Exception:
            pass

    # 5. ค้นหาในหัวข้อ Markdown (docs/)
    matched_docs = []
    for doc in sorted((ROOT / "docs").glob("*.md")) + [ROOT / "START_HERE.md", ROOT / "README.md", ROOT / "AGENTS.md"]:
        if not doc.exists():
            continue
        try:
            lines = doc.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines, 1):
                if line.startswith("#") and any(t in line.lower() for t in terms):
                    matched_docs.append((doc.relative_to(ROOT), i, line.strip()))
        except Exception:
            pass

    if matched_docs:
        found_any = True
        print(f"📄 หัวข้อในเอกสารที่ตรงกัน ({len(matched_docs)} จุด):")
        for doc_rel, line_no, text in matched_docs[:8]:
            print(f"   • {doc_rel}:{line_no} — {text}")
        if len(matched_docs) > 8:
            print(f"     ... และอีก {len(matched_docs) - 8} จุด")
        print()

    # 6. ค้นหาเนื้อหาเต็มเชิงลึก (Mini-FTS Full-Text Search)
    try:
        from tools.mini_fts import search as fts_search
        fts_res = fts_search(query, limit=5)
        if fts_res:
            found_any = True
            print(f"📖 ข้อความในเอกสารและการวิเคราะห์ (Mini-FTS {len(fts_res)} รายการ):")
            for r in fts_res:
                print(f"   • [{r['category'].upper()}] {r['title']} ({r['path']})")
                print(f"       ↳ {r['snippet']}")
            print()
    except Exception:
        pass

    # 7. ค้นหาสถานีโทรมาตรและประตูระบายน้ำ
    tele_matches = _search_telemetry_stations(terms)
    if tele_matches:
        found_any = True
        print(f"📡 สถานีโทรมาตรและประตูน้ำ ({len(tele_matches)} จุด):")
        for code, name, detail in tele_matches[:10]:
            print(f"   • [{code}] {name} — {detail}")
        if len(tele_matches) > 10:
            print(f"     ... และอีก {len(tele_matches) - 10} สถานี")
        print()

    if not found_any:
        print(f"❌ ไม่พบผลลัพธ์ที่ตรงกับ '{query}'")
        print("💡 ลองค้นหาด้วยคำที่กว้างขึ้น เช่น 'เขื่อน', 'ฝน', 'ปตร', 'สูบ', 'องครักษ์', 's1', 'model'")
    print("=" * 76)


def cmd_goal(goal_num: str):
    print_banner()
    # แมปหมายเลขเป้าหมายเข้ากับเสาหลัก
    pillar_key = None
    if goal_num in ["1", "2", "3", "4", "5"]:
        pillar_key = "1"
    elif goal_num == "6":
        pillar_key = "2"
    elif goal_num == "7":
        pillar_key = "3"

    if not pillar_key:
        print(f"❌ ไม่พบเป้าหมาย '{goal_num}' (กรุณาระบุเลข 1 ถึง 7)")
        return

    p = PILLARS[pillar_key]
    print(f"🎯 เป้าหมายที่ {goal_num} — อยู่ภายใต้: {p['title']}")
    print(f"   ขอบเขต: {p['scope']}")
    print(f"\n📊 รายงาน HTML:")
    for r in p["reports"]:
        exists = "✓" if (ROOT / r["html"]).exists() else "✗"
        print(f"   [{exists}] {r['name']}")
        print(f"       HTML   : {r['html']}")
        print(f"       Builder: {r['builder']}")

    print(f"\n🔢 ตัวเลขทางการ (Canonical):")
    print(f"   • ไฟล์ : {p['canonical']}")
    print(f"   • สร้าง: {p['canonical_builder']}")

    print(f"\n📑 สเปกและเอกสารประกอบ (Docs):")
    for doc in p["docs"]:
        exists = "✓" if (ROOT / doc).exists() else "✗"
        print(f"   [{exists}] {doc}")

    print(f"\n💻 สคริปต์วิเคราะห์หัวใจ (Key Scripts):")
    for s in p["key_scripts"]:
        exists = "✓" if (ROOT / s).exists() else "✗"
        print(f"   [{exists}] {s}")

    print(f"\n📁 โฟลเดอร์ข้อมูลดิบ (Data Dirs):")
    for d in p["data_dirs"]:
        exists = "✓" if (ROOT / d).exists() else "✗"
        print(f"   [{exists}] {d}")

    print("=" * 76)


def registered_paths() -> set[str]:
    """ทุกพาธที่ลงทะเบียนในสารบัญ — ใช้ตรวจย้อนกลับ (ไฟล์บนดิสก์ที่ยังไม่ลงทะเบียน)"""
    reg: set[str] = set()
    for p in PILLARS.values():
        for r in p["reports"]:
            reg.add(r["html"])
            reg.add(r["builder"])
        reg.add(p["canonical"])
        reg.add(p["canonical_builder"])
        reg.update(p["docs"])
        reg.update(p["key_scripts"])
        reg.update(p["data_dirs"])
    reg.update(doc for doc, _ in CORE_GOVERNANCE)
    return reg


# พื้นผิวเอกสารที่ "ต้องลงทะเบียนครบ" — ไฟล์ใหม่ที่ถูกวางที่ root หรือ docs/ คือที่มาของ N-04
# (เจอจริง: รีวิว/รายงานตรวจสอบถูกวางที่ root แล้วไม่มีใครลงทะเบียน 2 รอบติด)
DOC_SURFACES = ("*.md", "docs/*.md")

# ผลงานรีวิวอิสระจาก session ภายนอก — HANDOFF §งานถัดไปสั่งให้บันทึกไว้ที่ root
# เป็นรูปแบบชั่วคราว ไม่ต้องลงทะเบียนในสารบัญ (ดู unregistered_docs())
#
# ระวัง: repo นี้ใช้ชื่อจริงสองแบนเท่ากัน — `REVIEW.<model>.md` (จุด) แต่
# `TRIAGE_ROUND5_2026-10-18.md` (ขีดล่าง) · รอบแก้แรกใช้ glob `TRIAGE.*.md` ซึ่งไม่จับไฟล์จริง
# ทำให้ส่วนนี้เป็นโค้ดตาย — ตัวตรวจจะล้มซ้ำทุกรอบที่เขียนไฟล์คัดกรองใหม่ไว้ที่ root
# จึงต้องยกเว้นทั้งจุดและขีดล่าง (เจอจริง 18 ต.ค. 69)
#
# คำนวณเป็นฟังก์ชันที่เรียกทุกครั้ง ไม่เก็บเป็นค่าคงที่ระดับโมดูล เพราะค่าคงที่ที่
# อ่านดิสก์ตอน import จะไม่เห็นไฟล์ที่ถูกสร้างหรือลบหลังจากนั้น (เจอจริงระหว่างเทสต์)
_REVIEW_ARTIFACT_RX = re.compile(r"(?:REVIEW|TRIAGE|DISPOSITION)[._].+\.md$")


def review_artifacts() -> frozenset[str]:
    """พาธที่สัมพัทธ์ของไฟล์ที่ตกร่างรีวิวอิสระ/ไฟล์คัดกรอง ซึ่งไม่ต้องลงทะเบียนในสารบัญ

    ครอบคลุมทั้งที่ root ตามที่ HANDOFF สั่ง และใน docs/reviews/ ซึ่งเป็นที่เก็บจริงของฉบับเก่า
    """
    names = frozenset(
        p.name for p in ROOT.glob("*.md") if _REVIEW_ARTIFACT_RX.match(p.name)
    )
    rel = frozenset(
        f"docs/reviews/{p.name}"
        for p in (ROOT / "docs" / "reviews").glob("*.md")
        if _REVIEW_ARTIFACT_RX.match(p.name)
    )
    return names | rel


def unregistered_docs() -> list[str]:
    """ไฟล์เอกสารบนดิสก์ที่ยังไม่ลงทะเบียนในสารบัญ (เรียงตามพาธ)

    ยกเว้นไฟล์ผลการรีวิวอิสระที่วางไว้ที่ root ตามคำสั่งใน HANDOFF §งานถัดไป
    (`REVIEW.<model>.md` / `TRIAGE.*.md`) — เป็นผลงานของ session ภายนอก ไม่ใช่เอกสาร
    ที่ต้องบำรุงรักษาในระบบ การบังคับให้ลงทะเบียนรายไฟล์ทำให้คำสั่งที่ถูกต้อง
    (เขียนรีวิวลง root) ทำให้ `catalog audit` ล้มทุกรอบ — ดู REVIEW.space-bunny-free.md F-36
    """
    reg = registered_paths()
    found: set[str] = set()
    for pat in DOC_SURFACES:
        for p in ROOT.glob(pat):
            found.add(p.relative_to(ROOT).as_posix())
    return sorted(found - reg - review_artifacts())


def cmd_audit() -> int:
    """ตรวจย้อนกลับ: cmd_check ตรวจ 'ลงทะเบียน→มีจริง' แต่จับไฟล์ที่ไม่มีใครลงทะเบียนไม่ได้"""
    print_banner()
    print("🔍 ตรวจย้อนกลับ: เอกสารบนดิสก์ที่ยังไม่ลงทะเบียนในสารบัญ (root *.md + docs/*.md)...\n")
    un = unregistered_docs()
    if un:
        print(f"⚠️ พบ {len(un)} ไฟล์ที่ยังไม่ลงทะเบียน — เพิ่มใน CORE_GOVERNANCE หรือย้ายออกจากพื้นที่:")
        for u in un:
            print(f"   ❌ {u}")
        print("=" * 76)
        return 1
    total = sum(len(list(ROOT.glob(p))) for p in DOC_SURFACES)
    print(f"✅ เอกสารทุกไฟล์ลงทะเบียนครบ ({total} ไฟล์จาก {' + '.join(DOC_SURFACES)})")
    print("=" * 76)
    return 0


def cmd_check():
    print_banner()
    print("🧪 กำลังตรวจสอบความมีอยู่จริงของไฟล์และโฟลเดอร์ทั้งหมดในสารบัญ...\n")
    missing = []
    total = 0

    for p in PILLARS.values():
        for r in p["reports"]:
            total += 2
            if not (ROOT / r["html"]).exists():
                missing.append(r["html"])
            if not (ROOT / r["builder"]).exists():
                missing.append(r["builder"])
        total += 2
        if not (ROOT / p["canonical"]).exists():
            missing.append(p["canonical"])
        if not (ROOT / p["canonical_builder"]).exists():
            missing.append(p["canonical_builder"])
        for d in p["docs"] + p["key_scripts"] + p["data_dirs"]:
            total += 1
            if not (ROOT / d).exists():
                missing.append(d)

    for doc, _ in CORE_GOVERNANCE:
        total += 1
        if not (ROOT / doc).exists():
            missing.append(doc)

    if missing:
        print(f"⚠️ พบ {len(missing)} จาก {total} รายการที่ไม่มีอยู่จริงบนดิสก์:")
        for m in missing:
            print(f"   ❌ {m}")
    else:
        print(f"✅ ผ่านการตรวจสอบสมบูรณ์! ไฟล์และโฟลเดอร์ทั้งหมด {total} รายการมีอยู่จริงบนดิสก์")
    print("=" * 76)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ["-h", "--help", "overview"]:
        cmd_overview()
    elif args[0] in ["find", "search"] and len(args) > 1:
        cmd_find(" ".join(args[1:]))
    elif args[0] in ["goal", "target"] and len(args) > 1:
        cmd_goal(args[1])
    elif args[0] in ["check", "verify", "test"]:
        cmd_check()
    elif args[0] in ["audit", "reverse"]:
        sys.exit(cmd_audit())
    else:
        # ถ้าพิมพ์คำค้นเดี่ยว ๆ เช่น python catalog.py คันคลอง
        cmd_find(" ".join(args))


if __name__ == "__main__":
    main()
