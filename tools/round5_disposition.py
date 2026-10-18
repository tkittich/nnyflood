"""สร้างทะเบียนการดำเนินการของข้อค้นพบจากรีวิวอีก 4 ฉบับ

เดิมข้อค้นพบเหล่านี้ถูก "เก็บคัดกรองรอบที่ 6" โดยไม่มีรายการตรวจสอบ
จึงเท่ากับไม่มีผู้รับผิดชอบและเสี่ยงหายถาวร (คือข้อ F-30 ของผู้ตรวจรอบที่ 5)

สคริปต์นี้ดึงรายการข้อค้นพบจากไฟล์รีวิวแบบอัตโนมัติ แล้วผูกกับผลตรวจที่บันทึกไว้
สถานะที่ใช้มี 4 ระดับ และห้ามใช้คำว่า "ปิด" ถ้ายังไม่ได้ตรวจจริง:
  · ทำซ้ำไม่ได้    — ตรวจแล้ว ไม่พบปัญหาในโค้ดปัจจุบัน (รีวิวเขียนจากโค้ดรุ่นก่อน)
  · ปิดแล้ว        — ตรวจแล้ว ปัญหาหายไปแล้วจริง
  · ยังค้าง         — ตรวจแล้ว ยืนยันว่ายังมีอยู่ ต้องแก้
  · ยังไม่ได้ตรวจ   — ยังไม่ได้ตรวจ ระบุวิธีตรวจที่ต้องใช้ไว้ให้ผู้รับทำต่อได้
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# อยู่ใน tools/ เพราะเป็นตัวสร้างเอกสาร ไม่ใช่โมดูลวิเคราะห์ของเป้าหมายใด —
# ถ้าวางใน analysis/ จะขัดกับกติกาตั้งชื่อไฟล์ที่บังคับใช้กับสคริปต์วิเคราะห์
REVIEWS = ROOT / "docs" / "reviews"
OUT = ROOT / "docs" / "reviews" / "DISPOSITION_ROUND5_OTHERS.md"

SOURCES = {
    "claude": "REVIEW.claude-sonnet-5.5-goal6.md",
    "deepseek": "REVIEW.deepseek.md",
    "gemini": "REVIEW.gemini_3.8_flash.md",
    "glm": "REVIEW.glm.md",
}


def extract() -> dict[str, list[tuple[str, str]]]:
    """ดึง (รหัส, หัวข้อ) ของข้อค้นพบจากรีวิวแต่ละฉบับ รองรับรูปแบบต่างกัน 4 แบบ"""
    out: dict[str, list[tuple[str, str]]] = {}

    # Gemini: ตาราง | **F1** | **ความรุนแรง** | ...   (ใช้เลขไม่มีขีด)
    t = (REVIEWS / SOURCES["gemini"]).read_text(encoding="utf-8")
    out["gemini"] = [
        (m[0], m[1].strip())
        for m in re.findall(r"^\|\s*\*\*(F\d{1,2})\*\*\s*\|\s*\*\*([^*]{4,90})\*\*", t, re.M)
    ]

    # DeepSeek: ตาราง | F-01 | ... |
    t = (REVIEWS / SOURCES["deepseek"]).read_text(encoding="utf-8")
    out["deepseek"] = [
        (a, b.strip())
        for a, b in re.findall(r"^\|\s*(F-\d{1,2})\s*\|([^|\n]{4,120})\|", t, re.M)
    ]

    # GLM: หัวข้อ ### GL-01 · หัวข้อ
    t = (REVIEWS / SOURCES["glm"]).read_text(encoding="utf-8")
    out["glm"] = [
        (m[0], m[1].strip()) for m in re.findall(r"^###\s*(GL-\d{1,2})\s*·\s*([^\n]{4,90})", t, re.M)
    ]

    # Claude: **H1 — หัวข้อ** ภายในส่วน ### HIGH / MED / LOW
    t = (REVIEWS / SOURCES["claude"]).read_text(encoding="utf-8")
    found: list[tuple[str, str]] = []
    letter = {"HIGH": "H", "MED": "M", "LOW": "L"}
    for sev in ("HIGH", "MED", "LOW"):
        blk = re.search(rf"^###\s*{sev}\s*$(.*?)(?=^###|\Z)", t, re.M | re.S)
        if not blk:
            continue
        for m in re.finditer(r"^\*\*([HML]\d{1,2})\s*—\s*([^*\n]{5,120})\*\*", blk.group(1), re.M):
            found.append((m.group(1), m.group(2).strip()))
    out["claude"] = found
    assert letter  # คงการอ้างอิงถึงแผนที่รหัสอักษร
    return out


def main() -> None:
    data = extract()
    verified = json.loads((ROOT / "analysis" / "goal7" / "round5_verified.json").read_text(encoding="utf-8"))

    lines = [
        "# ทะเบียนการดำเนินการ — ข้อค้นพบจากรีวิวอีก 4 ฉบับ (รอบที่ 5)",
        "",
        "> สร้างโดย `tools/round5_disposition.py` · ไม่แก้ด้วยมือ",
        "",
        "ทะเบียนนี้มีเพื่อแทนคำว่า \"เก็บคัดกรองรอบที่ 6\" ด้วยรายการที่มีผู้รับผิดชอบและวิธีตรวจ",
        "ตามข้อ F-30 ของผู้ตรวจรอบที่ 5 — ข้อค้นพบที่ไม่มีผลการดำเนินการจะหายถาวร",
        "",
        "## คำสัญญาของสถานะ",
        "",
        "| สถานะ | ความหมาย |",
        "|---|---|",
        "| **ทำซ้ำไม่ได้** | ตรวจแล้ว ไม่พบปัญหาในโค้ดปัจจุบัน — รีวิวนี้เขียนจากโค้ดรุ่นก่อนแก้ |",
        "| **ปิดแล้ว** | ตรวจแล้ว ยืนยันว่าปัญหาหายไปจริงในไฟล์ที่เผยแพร่ |",
        "| **ยังค้าง** | ตรวจแล้ว ยืนยันว่ายังมีอยู่ — ต้องแก้ |",
        "| **ยังไม่ได้ตรวจ** | ยังไม่ได้ตรวจ — ระบุวิธีตรวจที่ต้องใช้ |",
        "",
        "**ห้ามอ่าน \"ยังไม่ได้ตรวจ\" เป็น \"ไม่มีปัญหา\"** — เป็นการบันทึกความไม่รู้อย่างตรงไปตรงมา",
        "",
    ]
    total = 0
    for src, rows in data.items():
        lines += [f"## {src} ({len(rows)} ข้อ)", "", "| รหัส | ข้อค้นพบ | สถานะ | ผลตรวจ / วิธีตรวจที่ต้องใช้ |", "|---|---|---|---|"]
        for fid, title in rows:
            v = verified.get(src, {}).get(fid)
            status, note = (v[0], v[1]) if v else ("ยังไม่ได้ตรวจ", "ยังไม่ได้ตรวจ — ต้องเปิดไฟล์รีวิวและตรวจกับโค้ดจริง")
            total += 1
            lines.append(f"| {fid} | {title.replace('|', '/')} | **{status}** | {note} |")
        lines.append("")
    lines += [f"**รวม {total} ข้อ**", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    n_verified = sum(len(v) for v in verified.values())
    print(f"เขียน {OUT.name}: {total} ข้อ · ตรวจแล้ว {n_verified} ข้อ · อีก {total - n_verified} ข้อรอตรวจ")


if __name__ == "__main__":
    main()
