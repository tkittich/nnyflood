#!/usr/bin/env python3
"""catalog.py — เครื่องมือสืบค้นสารบัญข้อมูล โค้ด ตัวเลข และเอกสารของโปรเจกต์ (Zero-dependency CLI)

การใช้งาน:
    python catalog.py                     # ดูภาพรวมทั้ง 3 เสาหลัก รายงาน และไฟล์สำคัญ
    python catalog.py find <คำค้น>         # ค้นหาคำสำคัญในตัวเลข canonical, สเปก, และชื่อไฟล์
    python catalog.py goal <1..7>         # ดูไฟล์ที่เกี่ยวข้องกับเป้าหมายที่ระบุ
    python catalog.py check               # ตรวจสอบว่าไฟล์และโฟลเดอร์ทั้งหมดในสารบัญมีอยู่จริง
"""
from __future__ import annotations

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
            "analysis/goal5_policy_proposals.md",
        ],
        "key_scripts": [
            "analysis/attribution_share.py",
            "analysis/s1_peak_flood_map.py",
            "analysis/goal4_model_v1.py",
            "analysis/goal2_nny_medium_dams.py",
            "analysis/goal2_khundan_22y_baseline.py",
            "analysis/common_fetch_rid_swoc.py",
            "analysis/rid_cross_section_stage_rating.py",
        ],
        "data_dirs": [
            "data/01_rid_khun_dan",
            "data/02_thaiwater",
            "data/13_sentinel1_copernicus",
            "data/23_rid_swoc",
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
        ],
        "canonical": "analysis/goal7/canonical.json",
        "canonical_builder": "analysis/goal7_analysis.py",
        "docs": [
            "docs/GOAL7_PLAN.md",
            "docs/GOAL7_FOI_REQUESTS.md",
        ],
        "key_scripts": [
            "report/goal7_build_all.py",
            "analysis/goal7_analysis.py",
            "analysis/goal7_eia_structs.py",
            "analysis/goal7_waterchart_overlay.py",
            "analysis/goal7_gaps_check.py",
        ],
        "data_dirs": [
            "data/32_goal7_chaophraya2",
            "data/manual",
        ],
    },
}

CORE_GOVERNANCE = [
    ("AGENTS.md", "กติกาบังคับสำหรับ AI session (หลักฐาน, กฎหมาย, ตัวเลข, ภาษา, และ git)"),
    ("docs/REPORT_CONVENTIONS.md", "ข้อตกลงการทำรายงาน: เอ็นจิน key+โทเคน, ธีม WCAG, สรีรศาสตร์สายตา, และป้ายหน้ารวม"),
    ("docs/PROJECT_MAP.md", "แผนที่นำทางและแคตตาล็อกระบบฉบับเต็ม (Topic Discovery Matrix)"),
    ("docs/LEGAL_REVIEW.md", "แนวปฏิบัติทางกฎหมาย: การหมิ่นประมาท (เน้นระบบ ไม่เน้นตัวบุคคล) และ PDPA"),
    ("docs/DATA_SOURCES.md", "บัญชีแหล่งข้อมูล วิธีเชื่อมต่อ API Thaiwater, CDSE, Copernicus DEM"),
    ("tests/test_thai_language_lint.py", "ระบบทดสอบและตรวจจับภาษาไทยอัตโนมัติ (Typo Registry, คำชน, คำทับศัพท์)"),
]


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
    print("   • คำสั่งรันเทสต์ครบชุด: python -m pytest tests/ (114 ผ่าน)")
    print("   • คำสั่งตรวจข้อมูลดิบ : python analysis/verify_data_integrity.py --quick")
    print("=" * 76)


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


def cmd_find(query: str):
    print_banner()
    print(f"🔍 ผลการค้นหาสำหรับ: '{query}'\n")
    found_any = False

    # 1. ค้นหาในชื่อไฟล์
    matched_files = []
    for sub in ["analysis", "docs", "report", "tests"]:
        p = ROOT / sub
        if p.exists():
            for f in p.glob("**/*"):
                if f.is_file() and query.lower() in f.name.lower():
                    matched_files.append(f.relative_to(ROOT))

    if matched_files:
        found_any = True
        print(f"📁 ชื่อไฟล์ที่ตรงกัน ({len(matched_files)} ไฟล์):")
        for f in matched_files[:15]:
            print(f"   • {f}")
        if len(matched_files) > 15:
            print(f"     ... และอีก {len(matched_files) - 15} ไฟล์")
        print()

    # 2. ค้นหาใน Canonical JSONs
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
            matches = _search_json_keys(cdata, query)
            if matches:
                found_any = True
                print(f"🔢 ตัวเลขและคีย์ใน {label} ({cpath.relative_to(ROOT)}):")
                for k, v in matches[:8]:
                    print(f"   • {k}: {v}")
                if len(matches) > 8:
                    print(f"     ... พบทั้งหมด {len(matches)} จุดในไฟล์นี้")
                print()
        except Exception:
            pass

    # 3. ค้นหาในหัวข้อ Markdown (docs/)
    matched_docs = []
    for doc in sorted((ROOT / "docs").glob("*.md")) + [ROOT / "START_HERE.md", ROOT / "README.md", ROOT / "AGENTS.md"]:
        if not doc.exists():
            continue
        try:
            lines = doc.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines, 1):
                if line.startswith("#") and query.lower() in line.lower():
                    matched_docs.append((doc.relative_to(ROOT), i, line.strip()))
        except Exception:
            pass

    if matched_docs:
        found_any = True
        print(f"📄 หัวข้อในเอกสารที่ตรงกัน ({len(matched_docs)} จุด):")
        for doc_rel, line_no, text in matched_docs[:10]:
            print(f"   • {doc_rel}:{line_no} — {text}")
        print()

    if not found_any:
        print(f"❌ ไม่พบผลลัพธ์ที่ตรงกับ '{query}'")
        print("💡 ลองค้นหาด้วยคำที่กว้างขึ้น เช่น 'เขื่อน', 'ฝน', 'คัน', 's1', 'model' หรือ 'rule curve'")
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
    else:
        # ถ้าพิมพ์คำค้นเดี่ยว ๆ เช่น python catalog.py คันคลอง
        cmd_find(" ".join(args))


if __name__ == "__main__":
    main()
