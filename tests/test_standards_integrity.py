"""tests/test_standards_integrity.py — การตรวจจับความสอดคล้องของมาตรฐาน สารบัญ และแผนผังระบบ

ครอบคลุม:
1. ตรวจสอบว่าไฟล์/โฟลเดอร์ทั้งหมดที่ลงทะเบียนใน catalog.py มีอยู่จริงบนดิสก์ (Catalog Drift Guard)
2. ตรวจสอบว่าการ์ดรายงานทุกใบใน index.html มีป้ายกำกับผู้อ่าน (audience) และขอบเขต (scope) ครบถ้วน
3. ตรวจสอบว่ามีลิ้นชักสถาปัตยกรรมข้อมูล (tech-drawer) ใน index.html
4. ตรวจสอบว่าลิงก์ไฟล์โค้ด/รายงาน/canonical ใน docs/PROJECT_MAP.md มีอยู่จริงทุกไฟล์
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import catalog  # noqa: E402


def test_catalog_registered_paths_exist():
    """ไฟล์และโฟลเดอร์ทั้งหมดที่ลงทะเบียนใน catalog.py ต้องมีอยู่จริงบนดิสก์"""
    missing = []
    total = 0

    for p_id, p_info in catalog.PILLARS.items():
        for r in p_info["reports"]:
            total += 2
            if not (ROOT / r["html"]).exists():
                missing.append(f"{r['html']} (html report of {r['name']})")
            if not (ROOT / r["builder"]).exists():
                missing.append(f"{r['builder']} (builder of {r['name']})")

        total += 2
        if not (ROOT / p_info["canonical"]).exists():
            missing.append(f"{p_info['canonical']} (canonical json of pillar {p_id})")
        if not (ROOT / p_info["canonical_builder"]).exists():
            missing.append(f"{p_info['canonical_builder']} (canonical builder of pillar {p_id})")

        for d in p_info["docs"]:
            total += 1
            if not (ROOT / d).exists():
                missing.append(f"{d} (doc of pillar {p_id})")

        for s in p_info["key_scripts"]:
            total += 1
            if not (ROOT / s).exists():
                missing.append(f"{s} (key script of pillar {p_id})")

        for dr in p_info["data_dirs"]:
            total += 1
            if not (ROOT / dr).exists():
                missing.append(f"{dr} (data dir of pillar {p_id})")

    for doc, desc in catalog.CORE_GOVERNANCE:
        total += 1
        if not (ROOT / doc).exists():
            missing.append(f"{doc} (core governance: {desc})")

    assert not missing, f"พบ {len(missing)} จาก {total} รายการใน catalog.py ที่ไม่มีอยู่จริงบนดิสก์:\n" + "\n".join(missing)


def test_index_html_cards_have_required_badges():
    """การ์ดรายงานทุกใบใน index.html ต้องมีป้ายบอกกลุ่มเป้าหมาย (public/academic) และขอบเขต (scope) เสมอ"""
    index_path = ROOT / "index.html"
    assert index_path.exists(), "ต้องมีไฟล์ index.html อยู่ที่ root"
    content = index_path.read_text(encoding="utf-8")

    # ดึงการ์ดรายงานทั้งหมด
    cards = re.findall(r'<a class="card" href="([^"]+)">(.*?)</a>', content, re.DOTALL)
    assert len(cards) >= 6, f"ควรมีการ์ดรายงานอย่างน้อย 6 ฉบับใน index.html (พบ {len(cards)} ฉบับ)"

    errors = []
    for href, card_html in cards:
        # ตรวจป้ายกลุ่มเป้าหมาย (ฉบับประชาชน หรือ ฉบับวิชาการ)
        has_audience = "badge-public" in card_html or "badge-academic" in card_html
        if not has_audience:
            errors.append(f"การ์ด {href}: ขาดป้ายกลุ่มเป้าหมาย (badge-public หรือ badge-academic)")

        # ตรวจป้ายขอบเขตพื้นที่
        has_scope = "badge-scope" in card_html
        if not has_scope:
            errors.append(f"การ์ด {href}: ขาดป้ายขอบเขตพื้นที่ (badge-scope)")

    assert not errors, "พบการ์ดรายงานที่ป้ายกำกับไม่ครบถ้วนใน index.html:\n" + "\n".join(errors)


def test_index_html_has_tech_drawer():
    """index.html ต้องมีลิ้นชักสถาปัตยกรรมข้อมูล (details.tech-drawer)"""
    index_path = ROOT / "index.html"
    content = index_path.read_text(encoding="utf-8")
    assert '<details class="tech-drawer">' in content, "ต้องมี <details class='tech-drawer'> ใน index.html"
    assert "PROJECT_MAP.md" in content, "ลิ้นชักข้อมูลต้องมีลิงก์ไปยัง docs/PROJECT_MAP.md"
    assert "canonical_numbers.json" in content, "ลิ้นชักข้อมูลต้องอ้างอิง canonical numbers"


def test_project_map_registered_files_exist():
    """ไฟล์ที่ระบุในตารางของ docs/PROJECT_MAP.md ต้องมีอยู่จริงบนดิสก์"""
    map_path = ROOT / "docs/PROJECT_MAP.md"
    assert map_path.exists(), "ต้องมีไฟล์ docs/PROJECT_MAP.md"
    content = map_path.read_text(encoding="utf-8")

    # สกัด path ที่อยู่ใน backtick เช่น `report/...`, `analysis/...`, `docs/...`
    matches = re.findall(r'`((?:report|analysis|docs|data|tests)/[a-zA-Z0-9_\-\.\/]+)`', content)
    assert len(matches) > 10, "ควรพบพาธไฟล์ใน docs/PROJECT_MAP.md อย่างน้อย 10 จุด"

    missing = []
    for rel_path in sorted(set(matches)):
        p = ROOT / rel_path
        if not p.exists():
            missing.append(rel_path)

    assert not missing, f"พบไฟล์ที่อ้างใน docs/PROJECT_MAP.md แต่ไม่มีอยู่จริง:\n" + "\n".join(missing)


def test_active_reports_have_provenance_box():
    """รายงานฉบับที่ 3, 4, 7, 8 ต้องมีกล่องประทับประวัติและความโปร่งใส (provenance-box) พร้อมป้ายรับรอง"""
    targets = [
        ROOT / "report/ระลอกปลายกย2569.html",
        ROOT / "report/ชุดเทียบมาตรฐาน2554.html",
        ROOT / "report/คลองเจ้าพระยา2_ประชาชน.html",
        ROOT / "report/คลองเจ้าพระยา2_วิชาการ.html",
    ]
    for path in targets:
        assert path.exists(), f"ไม่พบไฟล์รายงาน {path.name}"
        html = path.read_text(encoding="utf-8")
        assert 'class="provenance-box"' in html, f"{path.name} ขาดกล่อง provenance-box"
        assert "prov-badge-code" in html, f"{path.name} ขาดป้ายรหัสรุ่น Git"
        assert "prov-badge-ok" in html, f"{path.name} ขาดป้ายรับรองคุณภาพ"
        assert "canonical.json" in html, f"{path.name} ขาดการอ้างอิง canonical.json"
        assert "github.com/tkittich/nnyflood" in html, f"{path.name} ขาดลิงก์คลังโค้ดสาธารณะ"


def test_catalog_key_scripts_covered_in_project_map():
    """ทุก key_scripts และ data_dirs ใน catalog.py ต้องได้รับการบันทึกใน docs/PROJECT_MAP.md"""
    map_path = ROOT / "docs/PROJECT_MAP.md"
    assert map_path.exists(), "ต้องมีไฟล์ docs/PROJECT_MAP.md"
    map_text = map_path.read_text(encoding="utf-8")

    missing = []
    for p_id, p_info in catalog.PILLARS.items():
        for s in p_info["key_scripts"]:
            s_name = Path(s).name
            if s_name not in map_text and s not in map_text:
                missing.append(f"เสาที่ {p_id} สคริปต์: {s}")

        for d in p_info["data_dirs"]:
            d_name = Path(d).name
            if d_name not in map_text and d not in map_text:
                missing.append(f"เสาที่ {p_id} โฟลเดอร์ข้อมูล: {d}")

    assert not missing, "พบสคริปต์/โฟลเดอร์ใน catalog.py ที่ยังไม่ถูกบันทึกใน docs/PROJECT_MAP.md:\n" + "\n".join(missing)


