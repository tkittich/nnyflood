"""**เลิกใช้แล้ว (19 ต.ค. 2569 — ผู้ใช้ตัดสิน): RapidOCR อ่านไทยไม่ดี ให้ใช้ analysis/goal7_typhoon_ocr.py / goal7_typhoon_queue_eia.py แทน**

เป้าหมาย 7 — OCR ภาษาไทยสำหรับเอกสารภาพสแกน (หนังสือมาตรการ · หน้าภาพของ EIA 2569 · เอกสารระยะที่ 1–2)

เครื่องมือ: RapidOCR (PP-OCRv5 รุ่นภาษาไทย `th_PP-OCRv5_rec_mobile` · onnxruntime CPU) — ทดสอบ 16 ต.ค. 69 บนหน้า 2/54 ของหนังสือมาตรการ:
อ่านไทยได้เกือบทั้งหน้า (ผิดเล็กน้อย เช่น "กรมซลประทาน" · หัวคอลัมน์บางช่องหลุด) → ใช้ **อ่านหาข้อมูล** ไม่ใช่ถอดความอ้างอิงตรง ๆ —
ข้อความที่จะอ้างในรายงานต้องเปิดดูภาพหน้าตรวจซ้ำ (บันทึกหน้าไว้ใน ocr/<label>/pages.jsonl)

รันด้วย venv ภายนอก repo (ไม่ปักใน requirements.txt — ใช้ครั้งเดียว): E:/theera/ocr_env/Scripts/python.exe analysis/goal7_ocr.py <spec.json>
spec.json: [{"label": "...", "pdf": "path", "pages": [1,2,...] | null}]  (null = ทุกหน้า) · เขียน/ต่อได้ (resume) ที่
data/32_goal7_chaophraya2/ocr/<label>/pages.jsonl  — ข้ามหน้าที่ทำแล้ว
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import fitz
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/32_goal7_chaophraya2/ocr"
DPI = 200


def engine():
    from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR
    return RapidOCR(params={"Rec.lang_type": LangRec.TH, "Rec.ocr_version": OCRVersion.PPOCRV5, "Rec.model_type": ModelType.MOBILE,
                            "Global.log_level": "warning"})


def page_image(doc, i: int, dpi: int = DPI) -> np.ndarray:
    pix = doc[i].get_pixmap(dpi=dpi, colorspace=fitz.csRGB)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)


def run(spec: list[dict]) -> None:
    eng = engine()
    for job in spec:
        label, pdf = job["label"], Path(job["pdf"])
        d = fitz.open(pdf)
        pages = job.get("pages") or list(range(1, len(d) + 1))
        out_dir = OUT / label
        out_dir.mkdir(parents=True, exist_ok=True)
        jl = out_dir / "pages.jsonl"
        done = set()
        if jl.exists():
            keep = [ln for ln in jl.read_text(encoding="utf-8").splitlines() if ln.strip() and "\"error\"" not in ln]  # หน้าที่ผิดพลาดทำซ้ำ
            jl.write_text(chr(10).join(keep) + (chr(10) if keep else ""), encoding="utf-8")
            for ln in keep:
                done.add(json.loads(ln)["page"])
        todo = [p for p in pages if p not in done]
        print(f"[{label}] {len(todo)} หน้าที่ต้องทำ (เสร็จแล้ว {len(done)}) · {pdf.name}", flush=True)
        t0 = time.time()
        with jl.open("a", encoding="utf-8") as f:
            for n, p in enumerate(todo, 1):
                try:
                    try:
                        r = eng(page_image(d, p - 1))
                    except Exception as e0:  # noqa: BLE001 — ภาพใหญ่เกิน (กระดานโปสเตอร์) ลองความละเอียดต่ำลง
                        if "large" not in str(e0):
                            raise
                        r = eng(page_image(d, p - 1, dpi=80))
                    boxes, txts, scores = r.boxes, r.txts or (), r.scores or ()
                    lines = []
                    for b, t, s in zip(boxes if boxes is not None else [], txts, scores):
                        xs = [pt[0] for pt in b]
                        ys = [pt[1] for pt in b]
                        lines.append([int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)), t, round(float(s), 3)])
                    lines.sort(key=lambda x: (round(x[1] / 25), x[0]))
                    rec = {"page": p, "n_lines": len(lines), "mean_conf": round(float(np.mean([x[5] for x in lines])), 3) if lines else None,
                           "text": "\n".join(x[4] for x in lines), "lines": lines}
                except Exception as e:  # noqa: BLE001 — หน้าเสียไม่หยุดทั้งงาน
                    rec = {"page": p, "error": str(e)[:200], "text": "", "lines": []}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                if n % 10 == 0:
                    print(f"  [{label}] {n}/{len(todo)} · {(time.time() - t0) / n:.1f} วินาที/หน้า", flush=True)
        # รวมเป็นข้อความเดียวต่อเอกสาร (เรียงหน้า)
        recs = sorted((json.loads(x) for x in jl.read_text(encoding="utf-8").splitlines() if x.strip()), key=lambda r: r["page"])
        (out_dir / "text.txt").write_text("\n".join(f"\n===== หน้า {r['page']} =====\n{r['text']}" for r in recs), encoding="utf-8")
        print(f"[{label}] เสร็จ {len(recs)} หน้า", flush=True)


if __name__ == "__main__":
    run(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
