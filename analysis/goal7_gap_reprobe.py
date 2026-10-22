"""ค้นคำสำคัญของช่องว่างที่ยังเปิดซ้ำบนผลถอดสองชุด (Typhoon · Indra OCR) และชั้นข้อความ PDF — ดูว่า Indra พบหน้าที่ Typhoon ไม่พบหรือไม่ (ข้อความ "ไม่พบ" ในรายงานพึ่งคุณภาพ OCR)
ตั้งไว้ก่อนดูผล: คำค้นมาจาก analysis/goal7/ocr_findings.json (ชุดคำเดิมรายหัวข้อ) · นับ "หน้า" ที่พบ แยกตามแหล่ง · หน้าที่ Indra พบแต่ Typhoon ไม่พบ = เบาะแสใหม่ ต้องเปิดภาพหน้าตรวจก่อนอ้าง
ข้อจำกัด: ค้นแบบตรงตัวอักษร (ตัดวรรณยุกต์ทั้งสองฝั่ง) — คำที่ OCR ถอดเพี้ยนจะไม่พบ · ไม่ได้ตัดสินว่าช่องว่างปิดแล้ว (ต้องอ่านหน้าจริง)
รัน: python analysis/goal7_gap_reprobe.py   (ต้องทำดัชนีค้นหาใหม่หลัง Indra อ่านครบ: python tools/mini_fts.py --reindex)
ผลลัพธ์: analysis/goal7/gap_reprobe.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.mini_fts import search  # noqa: E402  (reuse-first: ดัชนีค้นข้อความเต็มของโครงการ)

SRC = ROOT / "analysis/goal7/ocr_findings.json"
OUT = ROOT / "analysis/goal7/gap_reprobe.json"
CATS = ("ocr_typhoon", "ocr_indra", "eia_text")


def main() -> None:
    topics = json.loads(SRC.read_text(encoding="utf-8"))["summary"]
    res = {}
    for topic, terms in topics.items():
        row = {}
        for term in terms:
            hits = {c: set() for c in CATS}
            for r in search(term, limit=3000):
                if r["category"] in hits:
                    hits[r["category"]].add(r["path"])
            ty, ind, tx = (len(hits[c]) for c in CATS)
            only_indra = sorted(hits["ocr_indra"] - {p.replace("typhoon_ocr", "indra_ocr") for p in hits["ocr_typhoon"]})
            row[term] = {"typhoon": ty, "indra": ind, "text_layer": tx, "pages_indra_not_typhoon": len(only_indra), "sample": only_indra[:5]}
        res[topic] = row
    OUT.write_text(json.dumps({"note": "จำนวนหน้าที่พบคำค้น แยกตามแหล่ง — เบาะแสเท่านั้น ต้องเปิดภาพหน้าตรวจก่อนอ้าง", "topics": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    for t, row in res.items():
        print(t, {k: (v["typhoon"], v["indra"], v["text_layer"], v["pages_indra_not_typhoon"]) for k, v in row.items()})


if __name__ == "__main__":
    main()
