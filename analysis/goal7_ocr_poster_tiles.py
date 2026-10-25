"""ถอดความบอร์ดนิทรรศการขนาดยักษ์ (หน้าเดียวสูงหลายเมตร) ด้วย Typhoon-OCR แบบแบ่งแถบแนวนอนซ้อนเหลื่อม แล้วเขียนทับหน้าที่ล้มเหลวด้วยหน่วยความจำการ์ดจอไม่พอ
ที่มา: R7-13 — คิวเดิมเรนเดอร์ทั้งหน้าที่ 120 จุดต่อนิ้ว ได้ภาพกว้างหมื่นพิกเซล ขอหน่วยความจำ 15.7 GiB จนล้มทั้ง 11 หน้า (ph2_public_board2 7 หน้า · ph2_subgroup1_board 4 หน้า)
วิธี: เรนเดอร์ให้กว้าง ~1,700 พิกเซล แล้วตัดเป็นแถบสูง ~2,200 พิกเซล ซ้อนกัน 15% · ถอดทีละแถบด้วยคำสั่งสั้นเดิม · รวมข้อความตามลำดับบนลงล่าง พร้อมเครื่องหมายแถบ
ข้อจำกัด: ผลเป็นร่าง — ข้อความที่ถูกตัดกลางบรรทัดตรงรอยต่ออาจซ้ำหรือขาด · รูปและแผนที่ในบอร์ดไม่ถูกอ่านเป็นตัวเลข · ใช้ค้นหาข้อความเท่านั้น
รัน: E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_ocr_poster_tiles.py [--labels ph2_public_board2,ph2_subgroup1_board]
ผลลัพธ์: data/32_goal7_chaophraya2/typhoon_ocr/<ป้าย>/pages.jsonl (เขียนทับหน้าที่ล้มเหลว) + document.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))

TARGET_W = 1700
TILE_H = 2200
OVERLAP = 0.15


def tiles_of(img):
    h = img.height
    step = int(TILE_H * (1 - OVERLAP))
    y, out = 0, []
    while y < h:
        y1 = min(h, y + TILE_H)
        out.append((y, y1, img.crop((0, y, img.width, y1))))
        if y1 >= h:
            break
        y += step
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="ph2_public_board2,ph2_subgroup1_board")
    args = ap.parse_args()
    import fitz
    import goal7_batch_ocr_queue as q
    import goal7_typhoon_ocr as t
    from PIL import Image

    jobs = {j["label"]: j for j in q.BACKLOG_JOBS}
    processor, model = t.init_engine()
    for label in [s.strip() for s in args.labels.split(",") if s.strip()]:
        job = jobs[label]
        doc = fitz.open(job["pdf"])
        target = t.OUT_DIR / label
        jl = target / "pages.jsonl"
        recs = {}
        if jl.exists():
            for ln in jl.read_text(encoding="utf-8").splitlines():
                if ln.strip():
                    r = json.loads(ln)
                    recs[int(r["page"])] = r
        for pno in range(1, len(doc) + 1):
            if pno in recs and not recs[pno].get("error"):
                continue
            t0 = time.time()
            page = doc[pno - 1]
            dpi = max(20, int(TARGET_W / (page.rect.width / 72.0)))
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            parts = []
            for i, (y0, y1, tile) in enumerate(tiles_of(img), 1):
                txt = t._generate(tile, t.SHORT_PROMPT, processor, model, "cuda:0", max_new_tokens=2048, max_time=240.0)
                parts.append(f"<!-- แถบ {i} (แถว {y0}–{y1} จาก {img.height}) -->\n{txt.strip()}")
            recs[pno] = {"page": pno, "text": "\n\n".join(parts), "sec": round(time.time() - t0, 2), "worker": "tiles", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "note": f"แบ่ง {len(parts)} แถบ · {img.width}x{img.height} px"}
            print(label, "หน้า", pno, "แถบ", len(parts), f"{recs[pno]['sec']} วินาที", flush=True)
            with jl.open("w", encoding="utf-8") as f:
                for r in sorted(recs.values(), key=lambda x: int(x["page"])):
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        t.finalize_label(label)
    print("เสร็จ")


if __name__ == "__main__":
    main()
