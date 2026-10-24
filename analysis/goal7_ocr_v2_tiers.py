"""สรุปภาพย่อยที่ตัวอ่านหลายตัวอ่านตรงกัน (ระดับสูง) จากขั้นตอน OCR รุ่นที่ 2: ตัวเลขฉันทามติ (พบในตัวอ่านอย่างน้อย 2 ตัว) · ตัวเลขขัดแย้ง · คำบรรยายรูปที่อยู่ใกล้ที่สุดจากผลแยกส่วน
เกณฑ์ระดับสูง (ตั้งก่อนดูผล): มีตัวเลขฉันทามติอย่างน้อย 5 ค่า และตัวเลขขัดแย้งไม่เกิน 25% ของตัวเลขทั้งหมด · ตัวอ่าน = Qwen3-VL-8B · Qwen2.5-VL-7B · Indra OCR
ข้อจำกัด: ฉันทามติไม่ใช่ความถูกต้อง (ตัวอ่านอาจผิดเหมือนกันได้) — ต้องเทียบกับภาพหน้าหรือข้อความรายงานก่อนใช้ · ไม่รวมภาพสีสดที่ข้ามการอ่าน
รัน: python analysis/goal7_ocr_v2_tiers.py
ผลลัพธ์: analysis/goal7/ocr_v2_high_tier.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_ocr_v2 as v2  # noqa: E402  (reuse-first: ตัวดึงตัวเลข · รายชื่อเล่ม · ตัวอ่าน)

OUT = ROOT / "analysis/goal7/ocr_v2_high_tier.json"


def main() -> None:
    rows, low = [], 0
    for vol in v2.VOLS:
        for p in v2.needs_visual_pages(vol):
            d = v2.V2 / vol / f"p{p:04d}"
            if not (d / "crops.json").exists():
                continue
            lay = json.loads((d / "layout.json").read_text(encoding="utf-8"))["blocks"] if (d / "layout.json").exists() else []
            caps = [b for b in lay if "caption" in b["type"] and b.get("text")]
            for c in json.loads((d / "crops.json").read_text(encoding="utf-8")):
                if c["skip_reason"]:
                    continue
                texts = {}
                for name in (v2.READ_MAIN, v2.READ_SECOND, "indra"):
                    f = d / "reads" / f"{c['id']}__{name}.json"
                    if f.exists():
                        texts[name] = json.loads(f.read_text(encoding="utf-8"))["text"]
                sets = {k: v2.numbers_of(v) for k, v in texts.items()}
                if len(sets) < 2:
                    continue
                allv = set().union(*sets.values())
                cons = sorted(v for v in allv if sum(v in s for s in sets.values()) >= 2)
                cont = len(allv) - len(cons)
                if len(cons) >= 5 and cont <= 0.25 * len(allv):
                    cy = (c["bbox"][1] + c["bbox"][3]) / 2
                    cap = min(caps, key=lambda b: abs((b["bbox"][1] + b["bbox"][3]) / 2 - cy), default=None)
                    rows.append({"vol": vol, "page": p, "crop": c["id"], "type": c["type"], "readers": sorted(sets), "consensus_numbers": len(cons), "contested_numbers": cont,
                                 "caption": (cap["text"][:140] if cap else None)})
                elif len(allv) >= 5:
                    low += 1
    OUT.write_text(json.dumps({"note": "ภาพย่อยที่ตัวอ่านอย่างน้อย 2 ตัวอ่านตัวเลขตรงกัน — ฉันทามติไม่ใช่ความถูกต้อง ต้องเทียบภาพหน้า", "high_tier": len(rows), "low_tier_with_5plus_numbers": low, "items": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(rows), "ระดับสูง ·", low, "ระดับต่ำ")
    for r in rows:
        print(r["vol"][-5:], r["page"], r["crop"], r["consensus_numbers"], r["contested_numbers"], (r["caption"] or "")[:70])


if __name__ == "__main__":
    main()
