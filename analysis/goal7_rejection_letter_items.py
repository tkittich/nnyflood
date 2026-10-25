"""เป้าหมาย 7 (R7-10) — ถอดโครงหนังสือ สผ. แจ้งผลการพิจารณา EIA 3 รอบ (ทส 1010.6/2233 · ทส 1010.6/18346 · ทส 1009.6/6077) จากผล Typhoon-OCR: เลขที่ · วันที่ · หัวข้อใหญ่ · ข้อย่อย

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
EVID = ROOT / "data/32_goal7_chaophraya2/evidence/letter2233_p1_header.png"
OUT = ROOT / "analysis/goal7/rejection_letter_items.json"
TH = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
SEC = re.compile(r"^(?:#+\s*)?(\d{1,2})\.\s+(\S.*)$")
ITEM = re.compile(r"^(\d{1,2})\)\s+(\S.*)$")
SUB = re.compile(r"^(\d{1,2})\.(\d{1,2})\)\s+(\S.*)$")


ITEM_DOT = re.compile(r"^(?:#+\s*)?(\d{1,2})\.(\d{1,2})\s+(\S.*)$")      # รอบ 2–3: "1.6 …" (ข้อย่อยของหัวข้อ)
OCR_DIR = ROOT / "data/32_goal7_chaophraya2/typhoon_ocr"
LETTERS = {
    1: {"label": "eia_rejection_letter", "no": "ทส 1010.6/2233", "date": "18 ก.พ. 2562", "meeting": "คชก. ครั้งที่ 2/2562 วันที่ 1 ก.พ. 2562", "ref": "กษ 0327/10446 ลงวันที่ 27 พ.ย. 2561",
        "evidence": "data/32_goal7_chaophraya2/evidence/letter2233_p1_header.png", "reading": "ภาพหน้า 1: ที่ ทส ๑๐๑๐.๖/๒๒๓๓ · ๑๘ กุมภาพันธ์ ๒๕๖๒", "pdf_pages": 11, "dot": False},
    2: {"label": "eia_letter_round2", "no": "ทส 1010.6/18346", "date": "25 พ.ย. 2564", "meeting": "คชก. ครั้งที่ 7/2564 วันที่ 28 ต.ค. 2564", "ref": "กษ 0327/7681 ลงวันที่ 20 ก.ย. 2564",
        "evidence": "data/32_goal7_chaophraya2/evidence/letter_round2_p1_header.png", "reading": "ภาพหน้า 1: ที่ ทส ๑๐๑๐.๖/๑๘๓๔๖ · ๒๕ พฤศจิกายน ๒๕๖๔ (มีตราประทับทับวันที่)", "pdf_pages": 11, "dot": True},
    3: {"label": "eia_letter_round3", "no": "ทส 1009.6/6077", "date": "18 มี.ค. 2567", "meeting": "คชก. ครั้งที่ 5/2567 วันที่ 8 มี.ค. 2567", "ref": "กษ 0327/11565 ลงวันที่ 19 ธ.ค. 2566",
        "evidence": "data/32_goal7_chaophraya2/evidence/letter_round3_p1_header.png", "reading": "ภาพหน้า 1: ที่ ทส ๑๐๐๙.๖/๖๐๗๗ · ๑๘ มีนาคม ๒๕๖๗", "pdf_pages": 9, "dot": True},
}


def parse(pages_path: Path, dot: bool = False) -> dict:
    pages = sorted((json.loads(x) for x in pages_path.read_text(encoding="utf-8").splitlines() if x.strip()), key=lambda r: r["page"])

    def split_inline(text: str) -> str:   # หัวข้อที่ OCR ติดกลางบรรทัดในรูป **11. ด้าน…** ให้ขึ้นบรรทัดใหม่เป็นหัวข้อ
        return re.sub(r"\*\*\s*(\d{1,2})\.\s*([^*\n]{3,80})\*\*", r"\n## \1. \2\n", text)
    lines = [(r["page"], ln.strip()) for r in pages for ln in split_inline((r.get("text") or "").translate(TH)).split("\n")]
    secs: dict[int, dict] = {}
    cur = None
    last = None
    has_dot: set[int] = set()
    for pg, s in lines:
        if not s:
            continue
        if dot:
            md = ITEM_DOT.match(s)
            if md and cur is not None and int(md.group(1)) == cur:
                last = {"no": f"{md.group(1)}.{md.group(2)}", "page": pg, "text": md.group(3)}
                secs[cur]["items"].append(last)
                has_dot.add(cur)
                continue
        elif re.match(r"^(#+\s*)?\d{1,2}\.\d", s) and not SUB.match(s):
            continue
        m = SEC.match(s)
        if m and not m.group(2).startswith(("ปรับ", "ให้")) and int(m.group(1)) <= 21 and (s.startswith("#") or "ด้าน" in m.group(2) or m.group(2).startswith(("อื่น", "มาตรการ"))):
            cur = int(m.group(1))
            secs[cur] = {"title": m.group(2)[:90], "page": pg, "items": []}
            last = None
            continue
        if cur is None:
            continue
        m = SUB.match(s) or ITEM.match(s)
        if m:
            if dot and cur in has_dot and last is not None and len(m.groups()) == 2:
                last["text"] += " " + s                                   # ข้อย่อย "1)" ของข้อ "N.M" — รวมเข้าข้อแม่
                continue
            tag = f"{m.group(1)}.{m.group(2)}" if len(m.groups()) == 3 else m.group(1)
            txt = m.group(3) if len(m.groups()) == 3 else m.group(2)
            last = {"no": tag, "page": pg, "text": txt}
            secs[cur]["items"].append(last)
        elif last is not None and not s.startswith(("#", "|")):
            last["text"] += " " + s
    for v in secs.values():
        for it in v["items"]:
            it["text"] = re.sub(r"\s+", " ", it["text"])[:700]
    return secs


def one_round(n: int) -> dict:
    meta = LETTERS[n]
    secs = parse(OCR_DIR / meta["label"] / "pages.jsonl", meta["dot"])
    ev_file = ROOT / meta["evidence"]
    ev = {"file": meta["evidence"], "sha256": hashlib.sha256(ev_file.read_bytes()).hexdigest() if ev_file.exists() else None, "reading": meta["reading"]}
    n_items = sum(len(v["items"]) for v in secs.values())
    recs = [json.loads(x) for x in (OCR_DIR / meta["label"] / "pages.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return {"letter": {"no": meta["no"], "date": meta["date"], "date_evidence": ev, "meeting": meta["meeting"], "ref": meta["ref"], "pages": meta["pdf_pages"]},
            "ocr": {"pages": len(recs), "pages_truncated": sum(1 for r in recs if (r.get("meta") or {}).get("truncated"))},
            "counts": {"sections_detected": len(secs), "items_detected_total": n_items}, "sections": {str(k): v for k, v in sorted(secs.items())}}


_NAME_RX = re.compile(r"(?:นางสาว|นาง|นาย)(?!ก\s)\s*[ก-๙]+\s+[ก-๙]+")
_GARBLED_NAMES = ("ประวี ชุมมาลา", "ปรเนร ชุมมาเกิด")      # ลายเซ็นผู้ลงนามที่โปรแกรมอ่านเพี้ยนจนไม่มีคำนำหน้า


def redact_names(s: str) -> str:
    """ปกปิดชื่อบุคคลธรรมดา (ผู้ลงนามในหนังสือ) — เก็บตำแหน่งไว้ · รีวิวรอบ 7 (ข้อมูลส่วนบุคคลเกินจำเป็นในไฟล์ที่ติดตามใน git)"""
    for g in _GARBLED_NAMES:
        s = s.replace(g, "[ชื่อผู้ลงนามถูกปกปิด]")
    return _NAME_RX.sub("[ชื่อผู้ลงนามถูกปกปิด]", s)


def main() -> None:
    r1 = one_round(1)
    r1["counts"].update({"section_1_items_detected": len(r1["sections"].get("1", {}).get("items", [])), "section_1_items_in_letter": 16,
                         "note": "หัวข้อใหญ่มีเลข 1–21 · ข้อย่อยนับด้วยโปรแกรมจากข้อความถอด (ประมาณ)"})
    r1["rounds"] = {"2": one_round(2), "3": one_round(3)}
    OUT.write_text(redact_names(json.dumps(r1, ensure_ascii=False, indent=1)), encoding="utf-8")
    print("round1", r1["counts"], "trunc", r1["ocr"])
    for k, v in r1["rounds"].items():
        print("round" + k, v["letter"]["no"], v["letter"]["date"], v["counts"], v["ocr"])


if __name__ == "__main__":
    main()
