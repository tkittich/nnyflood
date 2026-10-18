"""สร้างทะเบียนการดำเนินการของข้อค้นพบจากรีวิวอิสระรอบที่ 5 (อีก 4 ฉบับ)

เดิมข้อค้นพบเหล่านี้ถูก "เก็บคัดกรองรอบที่ 6" โดยไม่มีรายการตรวจสอบ
จึงเท่ากับไม่มีผู้รับผิดชอบและเสี่ยงหายถาวร (คือข้อ F-30 ของผู้ตรวจรอบที่ 5)

สคริปต์นี้ดึงรายการข้อค้นพบจากไฟล์รีวิวรอบที่ 5 ที่ root ของ repo โดยตรง
แล้วผูกกับผลตรวจที่บันทึกไว้ใน analysis/goal7/round5_verified.json
ก่อนสร้าง docs/reviews/DISPOSITION_ROUND5_OTHERS.md

ประวัติการแก้ (18 ต.ค. 2569): รุ่นแรกของสคริปต์ชี้ไปไฟล์รีวิวรุ่นเก่า 4 ฉบับ
ใน docs/reviews/ (REVIEW.deepseek.md ฯลฯ) ทำให้ทะเบียนทั้งฉบับอ้างข้อค้นพบ
คนละชุดกับรีวิวรอบที่ 5 ที่ส่งจริง — แก้ให้ชี้ไฟล์จริงและดึงตารางตามรูปแบบของแต่ละฉบับ

สถานะที่ใช้มี 6 ระดับ และห้ามใช้คำว่า "ปิด" ถ้ายังไม่ได้ตรวจจริง:
  · ทำซ้ำไม่ได้    — ตรวจแล้ว ไม่พบปัญหาในโค้ด/ผลลัพธ์ปัจจุบัน (รวมรายการตรวจด้านบวก)
  · ปิดแล้ว        — ตรวจแล้ว ปัญหาหายไปจริง
  · ปิดบางส่วน     — แก้บางส่วน หมายเหตุระบุส่วนที่เหลือและที่พักงาน
  · ยังค้าง        — ตรวจแล้ว ยังมีอยู่ครบ ยังไม่ได้แก้
  · ผักผ่อน        — พักตามข้อจำกัดข้อมูล/วิธีวิทยา (ต้องมีรหัส B-xx/R6-xx ในทะเบียน)
  · ยังไม่ได้ตรวจ   — ยังไม่ได้ตรวจ ระบุวิธีตรวจให้ผู้สานงานต่อ

ไฟล์ผลลัพธ์ถูกสแกนโดย tests/test_thai_language_lint.py — ห้ามแก้ด้วยมือ
ให้แก้ที่ analysis/goal7/round5_verified.json แล้วรันสคริปต์นี้ใหม่
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# อยู่ใน tools/ เพราะเป็นตัวสร้างเอกสาร ไม่ใช่โมดูลวิเคราะห์ของเป้าหมายใด —
# ถ้าวางใน analysis/ จะขัดกับกติกาตั้งชื่อไฟล์ที่บังคับใช้กับสคริปต์วิเคราะห์
OUT = ROOT / "docs" / "reviews" / "DISPOSITION_ROUND5_OTHERS.md"
VERIFIED = ROOT / "analysis" / "goal7" / "round5_verified.json"

SOURCES = {
    "claude": {"file": "REVIEW.Claude-Sonnet-5.5.md", "label": "Claude Sonnet 5.5", "expect": 20},
    "deepseek": {"file": "REVIEW.deepseek-v4.1-flash-free.md", "label": "DeepSeek V4.1 Flash", "expect": 8},
    "gemini": {"file": "REVIEW.Gemini-3.8-Flash.md", "label": "Gemini 3.8 Flash", "expect": 17},
    "glm": {"file": "REVIEW.GLM-5.3-Flash-Free.md", "label": "GLM 5.3 Flash", "expect": 15},
}

STATUS_ORDER = ("ปิดแล้ว", "ปิดบางส่วน", "ผักผ่อน", "ยังค้าง", "ทำซ้ำไม่ได้", "ยังไม่ได้ตรวจ")

STATUS_MEANING = {
    "ทำซ้ำไม่ได้": "ตรวจแล้ว ไม่พบปัญหาในโค้ด/ผลลัพธ์ปัจจุบัน (รวมรายการตรวจด้านบวก)",
    "ปิดแล้ว": "ตรวจแล้ว ปัญหาหายไปจริง",
    "ปิดบางส่วน": "แก้บางส่วน — หมายเหตุระบุส่วนที่เหลือและที่พักงาน",
    "ยังค้าง": "ตรวจแล้ว ยังมีอยู่ครบ ยังไม่ได้แก้",
    "ผักผ่อน": "พักตามข้อจำกัดข้อมูล/วิธีวิทยา — ต้องมีรหัสในทะเบียน B-xx/R6-xx",
    "ยังไม่ได้ตรวจ": "ยังไม่ได้ตรวจ — ระบุวิธีตรวจให้ผู้สานงานต่อ",
}

ROW_RX = re.compile(r"^\|\s*\*{0,2}(F-?\d{1,2})\*{0,2}\s*\|")


def _normalize_code(code: str) -> str:
    """F1 -> F-1 สำหรับฉบับ DeepSeek; ฉบับอื่นเป็น F-01 อยู่แล้ว"""
    if code.startswith("F-"):
        return code
    return "F-" + code[1:]


def _clean_cell(text: str) -> str:
    text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    text = text.replace("|", "\\|")
    if len(text) > 200:
        text = text[:199].rstrip() + "…"
    return text


def _table_findings(text: str) -> dict[str, str]:
    """ดึงตารางข้อค้นพบ: คอลัมน์รหัส, ระดับ, เป้าหมาย, ข้อค้นพบ (คือคอลัมน์ที่ 4)"""
    found: dict[str, str] = {}
    for line in text.splitlines():
        m = ROW_RX.match(line)
        if not m:
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 4:
            continue
        code = _normalize_code(m.group(1))
        if code not in found:
            found[code] = _clean_cell(cols[3])
    return found


def extract_findings(src: str, text: str) -> dict[str, str]:
    found = _table_findings(text)
    if src == "claude":
        # F-20 อยู่ในหัวข้อย่อยเชิงลึก (ด้านกฎหมาย) ไม่ได้อยู่ในตารางข้อค้นพบ
        found.setdefault("F-20", "Legal framing (deep dive): ข้อความเจตนาหน่วยงานในโค้ดเขื่อนป่าสัก + พาดหัว '38 วันต่อปี'")
    return found


def _sort_key(code: str) -> int:
    return int(code.split("-")[1])


def main() -> None:
    verified = json.loads(VERIFIED.read_text(encoding="utf-8"))
    all_findings: dict[str, dict[str, str]] = {}
    expected_total = 0
    for src, meta in SOURCES.items():
        text = (ROOT / meta["file"]).read_text(encoding="utf-8")
        found = extract_findings(src, text)
        if len(found) != meta["expect"]:
            raise SystemExit(
                f"❌ {meta['file']}: พบ {len(found)} ข้อค้นพบ แต่คาด {meta['expect']} — "
                "ตรวจรูปแบบตารางของฉบับรีวิวก่อน (อย่าปล่อยให้ทะเบียนขาดข้อ)"
            )
        all_findings[src] = found
        expected_total += len(found)

    missing = [
        f"{src}:{code}"
        for src, findings in all_findings.items()
        for code in findings
        if code not in verified.get(src, {})
    ]
    if missing:
        raise SystemExit("❌ ขาดสถานะผลตรวจใน round5_verified.json: " + ", ".join(missing))

    counts = {s: 0 for s in STATUS_ORDER}
    for src, findings in all_findings.items():
        for code in findings:
            st = verified[src][code]["status"]
            if st not in counts:
                raise SystemExit(f"❌ สถานะไม่รู้จัก '{st}' ที่ {src}:{code}")
            counts[st] += 1

    def cell(src: str, code: str) -> tuple[str, str, str]:
        entry = verified[src][code]
        return code, all_findings[src][code], entry["status"], entry["note"]

    lines: list[str] = [
        "# ทะเบียนการดำเนินการ: ข้อค้นพบจากรีวิวอิสระรอบที่ 5 — 4 ฉบับ (Claude · DeepSeek · Gemini · GLM)",
        "",
        "> สร้างอัตโนมัติโดย `python tools/round5_disposition.py` — **ห้ามแก้ไฟล์นี้ด้วยมือ** "
        "(ให้แก้ `analysis/goal7/round5_verified.json` แล้วรันสคริปต์ใหม่)",
        "> ต้นทาง (ไฟล์ที่ root ของ repo): "
        + " · ".join(f"`{m['file']}` ({m['expect']} ข้อ)" for m in SOURCES.values()),
        "> ฉบับ Space Bunny (37 ข้อ) ผู้ตรวจรอบที่ 5 สรุปทะเบียนเองไว้ที่ "
        "`docs/reviews/TRIAGE_ROUND5_2026-10-18.md` หัวข้อ 6",
        "> ข้อคงค้างทุกรายการมีรหัสติดตาม R6-xx / B-xx ใน `docs/OFFLINE_DATA_BACKLOG.md` หัวข้อ 6",
        "",
        "**นิยามสถานะ** (ตรวจเทียบโค้ด/ผลลัพธ์จริงเป็นรายข้อ — ห้ามใช้คำว่า \"ปิด\" ถ้ายังไม่ได้ตรวจ):",
        "",
        "| สถานะ | ความหมาย |",
        "|---|---|",
    ]
    for s in STATUS_ORDER:
        lines.append(f"| {s} | {STATUS_MEANING[s]} |")

    total = expected_total
    summary = " · ".join(f"{s} {counts[s]}" for s in STATUS_ORDER)
    lines.extend(["", f"**สรุปจาก {total} ข้อ**: {summary}", ""])

    for src, meta in SOURCES.items():
        findings = sorted(all_findings[src].keys(), key=_sort_key)
        lines.extend(
            [
                f"## {meta['label']} ({len(findings)} ข้อ)",
                "",
                "| รหัส | ข้อค้นพบ (ถ้อยคำจากฉบับรีวิว) | สถานะ | หมายเหตุ/หลักฐานการตรวจ |",
                "|---|---|---|---|",
            ]
        )
        for code in findings:
            c, title, st, note = cell(src, code)
            lines.append(f"| {c} | {title} | **{st}** | {note} |")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "### บันทึกการแก้ไขตัวสร้าง (18 ต.ค. 2569)",
            "",
            "- รุ่นแรกของตัวสร้างชี้ `SOURCES` ไปไฟล์รีวิวรุ่นเก่าใน `docs/reviews/` "
            "(`REVIEW.claude-sonnet-5.5-goal6.md`, `REVIEW.deepseek.md`, `REVIEW.gemini_3.8_flash.md`, `REVIEW.glm.md`) "
            "ทำให้ทะเบียนที่เผยแพร่ก่อนหน้านี้อ้างข้อค้นพบคนละชุดกับรีวิวรอบที่ 5 ที่ส่งจริง "
            "(75 รายการจากฉบับเก่า และส่วนใหญ่ยังขึ้นว่า \"ยังไม่ได้ตรวจ\")",
            "- รอบนี้ชี้ไฟล์จริงที่ root ตามรายการข้างต้น และตรวจสถานะใหม่ครบทุกรายการเทียบโค้ด/ผลลัพธ์ ณ วันที่สร้าง",
            "- ตัวเลขยอดรายฉบับถูกบังคับด้วย `expect` ต่อไฟล์ — ถ้ารูปแบบตารางรีวิวเปลี่ยนจนดึงได้ไม่ครบ สคริปต์จะหยุดทันที",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ เขียนทะเบียนลง {OUT.relative_to(ROOT)}")
    print(f"   รวม {total} ข้อ — " + " · ".join(f"{s}: {counts[s]}" for s in STATUS_ORDER))


if __name__ == "__main__":
    main()
