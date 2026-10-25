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


def test_goal7_mark_colours_meet_wcag_data_floor():
    """สีเส้น/พื้นที่ในภาพเป้าหมาย 7 (แผนที่และภาพจำลอง) ต้องผ่านเกณฑ์ข้อมูล 3:1 บนพื้นขาว

    เดิมไม่มีตัวตรวจครอบคลุมไฟล์เหล่านี้เลย — `test_report_themes_meet_wcag` อ่านเฉพาะ
    คู่สีแบบมีป้ายกำกับ (--c-<ชื่อ>) จาก 3 ไฟล์ จึงไม่จับสีที่เขียนตรง ๆ ในโค้ดวาดภาพ
    (แก้จากข้อค้นพบรอบที่ 5: #a89e94 2.63:1, #9ccfe0 1.69:1, #d9bf86 1.79:1, …)
    """
    files = [
        ROOT / "report/goal7_common.py",
        ROOT / "report/report_assets.py",
        ROOT / "report/goal7_blocks.py",
        ROOT / "report/goal7_build_policy_brief.py",
        ROOT / "report/goal7_engine.py",
        ROOT / "report/goal7_build_public.py",
        ROOT / "report/goal7_build_academic.py",
    ]
    # สีที่ไม่ใช่องค์แสดงข้อมูล — พื้นหลัง/เส้นขอบ/ข้อความกำกับ พร้อมเหตุผลที่ยกเว้น:
    # · พื้นผืนผ้าและเส้นหนา/ข้อความกำกับของธีม ไม่ใช่ข้อมูลที่ต้องอ่านค่า
    # · #c9d3c0 / #efe7d8 — เติมสีหน้าตัดคัน/ท้องคลอง มีเส้นขอบ ec=INK ล้อมรอบ
    #   รูปร่างจึงถูกนำโดยเส้น ไม่ใช่สีเติม (รอบที่ 5: พบแต่ไม่แก้ เพราะเป็นสีโครงสร้างที่ออกแบบไว้)
    # · #dbe9f6 — axvspan กำกับช่วงกม. ที่มีชื่อในคำบรรยายภาพ อยู่ชั้นใต้ข้อมูลทั้งหมด
    # · _ELEV_COLORS — พื้นหลังแถบระดับความสูงลำดับชั้น (zorder=0) แต่ละชั้นมี **ป้ายข้อความกำกับ
    #   ในคำอธิบาย (_ELEV_LABELS) และมีเส้น/สถานีทับอยู่ข้างบน ความหมายจึงมาจากป้าย ไม่ใช่สีเติม
    #   **เป็นข้อยกเว้นที่ตัดสินใจเชิงออกแบบ — ถ้าจะยกเลิกต้องปรับชุดสีทั้ง 9 ชั้นพร้อมกัน
    #   ไม่ใช่ทำทีละสี เพราะการเข้มทีละชั้นทำให้ชั้นที่ติดกันแยกกันไม่ออก (เหลือ 1.00:1)**
    # · #f0f9ff / #bae6fd — พื้นหลังและเส้นขอบของกรอบข้อมูล (info-box) ไม่ใช่องค์แสดงข้อมูล
    #   (ข้อความในกรอบใช้สีตัวอักษรธีมซึ่งตรวจคอนทราสต์แยกแล้ว)
    # · #cbd5e1 — เส้นขอบการ์ด/ตัวจำลอง interactive (ขอบตกแต่งของส่วนประกอบ ไม่ใช่ข้อมูล)
    # · #fffbeb / #fcd34d — พื้นหลังและเส้นขอบของกรอบเตือนเรื่องข้อขัดแย้งของตัวเลข
    #   ไม่ใช่องค์แสดงข้อมูล ข้อความในกรอบสืบทอดสีตัวอักษรธีม (เข้ม) บนพื้นอ่อน
    #   จึงอ่านได้ — ยกเว้นคู่เดียวกับกรอบข้อมูลสีฟ้า #f0f9ff/#bae6fd ข้างบน
    # · #b9c6d2 / #dbe3ea — เส้นขอบกล่องพับ (details.qd) ในเอ็นจินรายงาน 7–8 ไม่ใช่องค์แสดงข้อมูล (เพิ่มเมื่อขยายขอบเขตตรวจรอบ 7)
    NON_DATA = {
        "#b9c6d2", "#dbe3ea", "#f6f9fc",      # #f6f9fc = พื้นกล่องถาม–ตอบของรายงาน 7 (ข้อความในกล่องใช้สีธีม · .src #5a6b7b บนพื้นนี้ ≈ 5.2:1)
        "#ffffff", "#000000", "#f8fafc", "#f6f9fb", "#eef2f5", "#eef2f6", "#e2e8f0",
        "#888888", "#dddddd", "#cccccc", "#0f2233", "#153a5e", "#28425c", "#2a4d73",
        "#c9d3dc", "#efe7d8", "#dbe9f6", "#f0f9ff", "#bae6fd", "#cbd5e1",
        "#e6f0e0", "#d6e8c8", "#e9efc6", "#f3ecb8", "#ecdba0",
        "#fffbeb", "#fcd34d",
    }
    checked = 0
    for f in files:
        txt = f.read_text(encoding="utf-8")
        cols = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}", txt)}
        offenders = sorted(c for c in cols if c not in NON_DATA and _contrast("#ffffff", c) < DATA_MIN - 1e-9)
        assert not offenders, (
            f"{f.name}: สีที่คอนทราสต์บนพื้นขาวต่ำกว่า {DATA_MIN}:1 — {offenders}"
        )
        checked += len(cols - NON_DATA)
    assert checked >= 20, f"จำนวนสีที่ตรวจรวมน้อยผิดปกติ ({checked}) — นิยามสีอาจถูกย้ายไปไฟล์อื่น"


def test_dark_panel_text_meets_wcag_on_its_real_background():
    """ข้อความบนแผงพื้นเข้มของรายงาน 1–2 ต้องผ่านเกณฑ์ตัวอักษรบนพื้นที่ใช้จริง

    ตัวตรวจเดิมของเป้าหมาย 7 ตรวจสีทุกตัวบนพื้นขาว ซึ่งให้ผลผิดกับข้อความบนแผงเข้ม
    (`.anim-wrap` ใช้พื้น #0f2233) — #9fb8cc บนพื้นขาวได้ 2.06:1 แต่บนพื้นจริงได้ 7.87:1
    จึงต้องตรวจคู่สีกับพื้นที่ใช้จริง ไม่ใช่เดาเป็นพื้นขาว (เจอจริง 18 ต.ค. 69)
    """
    PANEL_BG = {
        # ตัวเลขกำกับของตัวควบคุมเวลาในภาพจำลองสถานการณ์
        "report/build_report_html.py": [
            (".anim-dates", "#9fb8cc", "#0f2233", 4.5),
            (".anim-bar", "#cfe2f3", "#0f2233", 4.5),
            (".anim-label", "#ffffff", "#0f2233", 4.5),
        ],
    }
    checked = 0
    for rel, pairs in PANEL_BG.items():
        txt = (ROOT / rel).read_text(encoding="utf-8")
        for selector, fg, bg, need in pairs:
            assert selector in txt, f"{rel}: ไม่พบตัวเลือก {selector} — สีอาจถูกย้าย"
            # ยืนยันว่าพื้นเข้มที่ใช้เป็นพื้นหลังจริงยังอยู่ในไฟล์
            assert bg in txt, f"{rel}: ไม่พบพื้นหลังแผง {bg} อีกแล้ว"
            assert fg in txt, f"{rel}: ไม่พบสีตัวอักษร {fg} ของ {selector} อีกแล้ว"
            ratio = _contrast(fg, bg)
            assert ratio >= need - 1e-9, (
                f"{rel} {selector}: {fg} บน {bg} = {ratio:.2f}:1 ต่ำกว่า {need}:1"
            )
            checked += 1
    assert checked >= 3, f"จำนวนคู่สีบนแผงเข้มที่ตรวจน้อยผิดปกติ ({checked})"


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
