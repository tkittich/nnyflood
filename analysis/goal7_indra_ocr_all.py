"""Indra OCR (CPU) อ่านทุกหน้าที่ Typhoon เคยอ่านไว้ แล้วเก็บเป็นชุดผลถอดคู่ขนาน (ข้อความ · บล็อกพร้อมป้าย/กรอบ · ค่าความมั่นใจรายบรรทัด) ใช้เป็นด่านแรก/ตัวเทียบกับ Typhoon
ผลวัดบนเฉลยชั้นข้อความ PDF: Indra คล้ายเฉลยเฉลี่ย 0.94 เทียบ Typhoon 0.85 (analysis/goal7/ocr_accuracy_vs_textlayer.json) — จึงเก็บผลไว้ให้ค้นหาและเทียบ ไม่ลบผล Typhoon
ข้อจำกัด: บังคับอ่านด้วยภาพ (ไม่ใช้ชั้นข้อความ PDF) ที่ 200 dpi · หน้าภาพวาด/แผนที่ได้ข้อความป้ายเป็นชิ้น ๆ ไม่ใช่ตาราง · ใบอนุญาตน้ำหนัก OpenRAIL-M แก้ไข
รัน: E:/theera/indra_env/Scripts/python.exe analysis/goal7_indra_ocr_all.py [--labels a,b]
ผลลัพธ์: data/32_goal7_chaophraya2/indra_ocr/<ชื่อ>/pages.jsonl (disk-only)
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_indra_vs_typhoon as ivt  # noqa: E402  (reuse-first: แผนที่ชื่อเอกสาร→PDF)

OUT = ROOT / "data/32_goal7_chaophraya2/indra_ocr"


def main() -> None:
    import cv2
    import indra_ocr
    import numpy as np
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="")
    a = ap.parse_args()
    pm = ivt.pdf_map()
    labels = [x for x in a.labels.split(",") if x] or sorted(p.parent.name for p in ivt.OCR.glob("*/pages.jsonl") if p.parent.name in pm)
    conv = indra_ocr.load(threads=4)
    for lb in labels:
        d = OUT / lb
        d.mkdir(parents=True, exist_ok=True)
        f = d / "pages.jsonl"
        done = {json.loads(x)["page"] for x in f.read_text(encoding="utf-8").splitlines() if x.strip()} if f.exists() else set()
        pages = [json.loads(x)["page"] for x in (ivt.OCR / lb / "pages.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        todo = [p for p in pages if p not in done]
        if not todo:
            continue
        doc = pymupdf.open(pm[lb])
        t0 = time.time()
        with f.open("a", encoding="utf-8") as fh:
            for p in todo:
                try:
                    pix = doc[p - 1].get_pixmap(dpi=200)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if pix.n >= 3 else img[:, :, 0]
                    pg = conv.ocr(gray)
                    confs = [float(getattr(ln, "conf", 0.0) or 0.0) for ln in pg.lines]
                    row = {"page": p, "text": pg.text, "rotation": getattr(pg, "rotation", None), "n_lines": len(pg.lines),
                           "mean_conf": round(sum(confs) / len(confs), 3) if confs else None, "share_low_conf": round(sum(c < 0.6 for c in confs) / len(confs), 3) if confs else None,
                           "blocks": [{"type": b["label"], "bbox": [round(float(v), 1) for v in b["bbox"]]} for b in pg.blocks], "engine": "indra-ocr"}
                except Exception as e:   # noqa: BLE001
                    row = {"page": p, "error": f"{type(e).__name__}: {str(e)[:120]}", "engine": "indra-ocr"}
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(lb, len(todo), "หน้า", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
