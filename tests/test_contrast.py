"""ทดสอบคอนทราสต์สี (WCAG 2.x) ของธีมรายงานและพาเลตต์กราฟ

ที่มา: การกลั่นกรองผลรีวิวรอบที่ 4 (GLM F-20 · BP F-13 · SB F-11/F-19) —
กฎ "คำนวณคอนทราสต์ทุกครั้งที่แก้ CSS/กราฟ" เคยไม่มีตัวบังคับอัตโนมัติ ไฟล์นี้เพิ่มด่าน 3 ชั้น:
  1) ชุดโทเคนสีของรายงาน (ไบล์เดอร์นครนายก 2 ตัว + ชุดกลาง goal6_reportlib) ต้องผ่านเกณฑ์
     ตัวอักษร ≥ 4.5 · องค์ประกอบข้อมูล (คู่ chart-bar/chart-accent) ≥ 3.0
  2) พาเลตต์แถบความเสี่ยงของเมทริกซ์น้ำหลากปะทะน้ำหนุน ต้องเป็นสีทึบและผ่าน ≥ 3.0 บนพื้นขาว
  3) สี/คำศัพท์ที่ปลดประจำการ (#78909c · ม.เกจ) ห้ามหลุดกลับเข้าทั้งไฟล์ต้นทางและไฟล์ที่เผยแพร่
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEXT_MIN = 4.5
DATA_MIN = 3.0
DATA_PAIR_NAMES = {"chart-bar", "chart-accent"}


def _srgb_channel(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return 0.2126 * _srgb_channel(r) + 0.7152 * _srgb_channel(g) + 0.0722 * _srgb_channel(b)


def _contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _pairs_from_builder(path: Path) -> list[tuple[str, str, str]]:
    """คู่สีในไบล์เดอร์รายงานรูปแบบ CSS variables: --c-<ชื่อ>: <พื้น>; --c-<ชื่อ>-fg: <ตัวอักษร>"""
    txt = path.read_text(encoding="utf-8")
    pairs = re.findall(
        r"--c-([a-z-]+):\s*(#[0-9a-fA-F]{6});\s*--c-\1-fg:\s*(#[0-9a-fA-F]{6})", txt
    )
    if not pairs and "css_tokens" in txt:
        import sys
        sys.path.insert(0, str(path.parent))
        from goal6_reportlib import css_tokens
        pairs = re.findall(
            r"--c-([a-z-]+):\s*(#[0-9a-fA-F]{6});\s*--c-\1-fg:\s*(#[0-9a-fA-F]{6})", css_tokens()
        )
    return pairs


def _pairs_from_reportlib(path: Path) -> list[tuple[str, str, str]]:
    """คู่สีในชุดกลาง reportlib รูปแบบ COLOR_TOKENS = {'ชื่อ': ('#พื้น', '#ตัวอักษร'), ...}"""
    txt = path.read_text(encoding="utf-8")
    m = re.search(r"COLOR_TOKENS = \{(.*?)\n\}", txt, re.S)
    assert m, f"{path.name}: ไม่พบ COLOR_TOKENS"
    pairs = re.findall(
        r'"([a-z_]+)":\s*\("#([0-9a-fA-F]{6})",\s*"#([0-9a-fA-F]{6})"\)', m.group(1)
    )
    return [(n.replace("_", "-"), bg, fg) for n, bg, fg in pairs]


def test_report_themes_meet_wcag():
    sources: list[tuple[str, list[tuple[str, str, str]]]] = [
        ("report/build_report_html.py", _pairs_from_builder(ROOT / "report/build_report_html.py")),
        ("report/build_expert_report.py", _pairs_from_builder(ROOT / "report/build_expert_report.py")),
        ("report/goal6_reportlib.py", _pairs_from_reportlib(ROOT / "report/goal6_reportlib.py")),
    ]
    total = 0
    for name, pairs in sources:
        assert len(pairs) >= 12, f"{name}: พบชุดคู่สีน้อยผิดปกติ ({len(pairs)})"
        for token, bg, fg in pairs:
            ratio = _contrast(bg, fg)
            need = DATA_MIN if token in DATA_PAIR_NAMES else TEXT_MIN
            assert ratio >= need - 1e-9, (
                f"{name}: คู่ --c-{token} ({fg} บน {bg}) = {ratio:.2f}:1 ต่ำกว่าเกณฑ์ {need}:1"
            )
            total += 1
    assert total >= 40, f"จำนวนคู่สีที่ตรวจรวมน้อยผิดปกติ ({total})"


def test_compound_palette_is_wcag_data_safe():
    txt = (ROOT / "analysis/compound_flood_risk.py").read_text(encoding="utf-8")
    m = re.search(r"colors = \[([^\]]+)\]", txt)
    assert m, "ไม่พบรายการสีของเมทริกซ์ใน analysis/compound_flood_risk.py"
    cols = re.findall(r"#[0-9a-fA-F]{6}", m.group(1))
    assert len(cols) == 4, f"จำนวนสีแถบความเสี่ยงต้องเป็น 4 (พบ {len(cols)})"
    for c in cols:
        ratio = _contrast("#ffffff", c)
        assert ratio >= DATA_MIN - 1e-9, (
            f"สีแถบความเสี่ยง {c} บนพื้นขาว = {ratio:.2f}:1 ต่ำกว่า {DATA_MIN}:1"
        )
    assert "alpha=0.85" not in txt, "แถบความเสี่ยงต้องทึบแสง (alpha=1) เพื่อคงคอนทราสต์บนพื้นแผนที่"


def test_banned_color_and_jargon_variants_absent():
    files = [
        ROOT / "report/build_report_html.py",
        ROOT / "report/build_expert_report.py",
        ROOT / "report/report_assets.py",
        ROOT / "report/น้ำท่วมนครนายก2569_ประชาชน.html",
        ROOT / "report/น้ำท่วมนครนายก2569_วิชาการ.html",
    ]
    for f in files:
        txt = f.read_text(encoding="utf-8")
        assert "#78909c" not in txt, (
            f"{f.name}: สีเทา #78909c (≈3.35:1 — ต่ำกว่าเกณฑ์ตัวอักษร) ต้องไม่หลุดกลับ — ใช้ #5a6b7b"
        )
        assert "ม.เกจ" not in txt, (
            f"{f.name}: คำที่ปลดประจำการ 'ม.เกจ' ต้องเป็น 'ม.ตามมาตรวัด'"
        )
