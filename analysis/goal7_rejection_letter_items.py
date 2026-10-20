"""เป้าหมาย 7 (R7-10) — ถอดโครงหนังสือ สผ. ที่ ทส 1010.6/2233 (แจ้งผลการพิจารณา EIA รอบ 1) จากผล Typhoon-OCR: เลขที่ · วันที่ · หัวข้อใหญ่ · ข้อย่อย

ทำไมต้องมี: รายงานเคยอ้าง "ลงวันที่ 14 ก.พ. 2562" และ "16 ข้อ" จากการคัดมือ — ตรวจกับต้นฉบับ (ภาพหน้า 1) ได้วันที่ 18 ก.พ. 2562 · หนังสือมี 21 หัวข้อใหญ่ และ 16 ข้อเป็นของ "หัวข้อที่ 1 ด้านภาพรวมฯ" เท่านั้น
ข้อควรระวัง: OCR ใช้เลขไทย (แปลงเป็นเลขอารบิกแล้ว) · หัวข้อ 10–15 ไม่ถูกจับเป็นหัวข้อ (นับรวมในหัวข้อ 9) · ข้อ 1) ข้อ 10 หายจากการถอด (ข้อความติดกับข้อ 9) · ตัวนับเป็นการประมาณ ไม่ใช่การนับของ สผ.
แหล่ง: data/32_goal7_chaophraya2/typhoon_ocr/eia_rejection_letter/pages.jsonl (จากไฟล์ data/manual/…/EIA/1. แจ้งมติไม่เห็นชอบ EIA ทางระบายน้ำหลาก.pdf 11 หน้า)
หลักฐานวันที่: ภาพหน้า 1 ตรวจด้วยตา "๑๘ กุมภาพันธ์ ๒๕๖๒" (data/32_goal7_chaophraya2/evidence/letter2233_p1_header.png มีแฮช)
รัน: python analysis/goal7_rejection_letter_items.py
ผลลัพธ์: analysis/goal7/rejection_letter_items.json
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data/32_goal7_chaophraya2/typhoon_ocr/eia_rejection_letter/pages.jsonl"
EVID = ROOT / "data/32_goal7_chaophraya2/evidence/letter2233_p1_header.png"
OUT = ROOT / "analysis/goal7/rejection_letter_items.json"
TH = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
SEC = re.compile(r"^(?:#+\s*)?(\d{1,2})\.\s+(\S.*)$")
ITEM = re.compile(r"^(\d{1,2})\)\s+(\S.*)$")
SUB = re.compile(r"^(\d{1,2})\.(\d{1,2})\)\s+(\S.*)$")


def parse() -> dict:
    pages = sorted((json.loads(x) for x in PAGES.read_text(encoding="utf-8").splitlines() if x.strip()), key=lambda r: r["page"])
    def split_inline(text: str) -> str:   # หัวข้อที่ OCR ติดกลางบรรทัดในรูป **11. ด้าน…** ให้ขึ้นบรรทัดใหม่เป็นหัวข้อ
        return re.sub(r"\*\*\s*(\d{1,2})\.\s*([^*\n]{3,80})\*\*", r"\n## \1. \2\n", text)
    lines = [(r["page"], ln.strip()) for r in pages for ln in split_inline((r.get("text") or "").translate(TH)).split("\n")]
    secs: dict[int, dict] = {}
    cur = None
    last = None
    for pg, s in lines:
        if not s:
            continue
        if re.match(r"^(#+\s*)?\d{1,2}\.\d", s) and not SUB.match(s):
            continue
        m = SEC.match(s)
        if m and not m.group(2).startswith(("ปรับ", "ให้")) and int(m.group(1)) <= 21 and (s.startswith("#") or "ด้าน" in m.group(2) or m.group(2).startswith("อื่น")):
            cur = int(m.group(1))
            secs[cur] = {"title": m.group(2)[:90], "page": pg, "items": []}
            last = None
            continue
        if cur is None:
            continue
        m = SUB.match(s) or ITEM.match(s)
        if m:
            tag = f"{m.group(1)}.{m.group(2)}" if len(m.groups()) == 3 else m.group(1)
            txt = m.group(3) if len(m.groups()) == 3 else m.group(2)
            last = {"no": tag, "page": pg, "text": txt}
            secs[cur]["items"].append(last)
        elif last is not None and not s.startswith(("#", "|")):
            last["text"] += " " + s
    for v in secs.values():
        for it in v["items"]:
            it["text"] = re.sub(r"\s+", " ", it["text"])[:300]
    return secs


def main() -> None:
    secs = parse()
    ev = {"file": str(EVID.relative_to(ROOT)), "sha256": hashlib.sha256(EVID.read_bytes()).hexdigest() if EVID.exists() else None,
          "reading": "ภาพหน้า 1: ที่ ทส ๑๐๑๐.๖/๒๒๓๓ · ๑๘ กุมภาพันธ์ ๒๕๖๒"}
    n_items = sum(len(v["items"]) for v in secs.values())
    out = {"letter": {"no": "ทส 1010.6/2233", "date": "18 ก.พ. 2562", "date_evidence": ev, "meeting": "คชก. ครั้งที่ 2/2562 วันที่ 1 ก.พ. 2562", "pages": 11},
           "counts": {"sections_detected": len(secs), "section_1_items_detected": len(secs.get(1, {}).get("items", [])), "section_1_items_in_letter": 16, "items_detected_total": n_items,
                      "note": "หัวข้อใหญ่มีเลข 1–21 · ข้อย่อยนับด้วยโปรแกรมจากข้อความถอด (ประมาณ) · ข้อ 1) ข้อ 10 หายจากการถอด"},
           "sections": {str(k): v for k, v in sorted(secs.items())}}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(out["counts"])


if __name__ == "__main__":
    main()
