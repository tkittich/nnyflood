"""เป้าหมาย 7 — คิวรวม Typhoon-OCR (เล่ม EIA 2569 ทั้ง 4 เล่ม + ทำซ้ำหน้า echo ของเอกสารอื่น) ตาม analysis/goal7/ocr_coverage.json

คิวเดียวรวมทุกเอกสาร เรียงลำดับ: (1) หน้าสแกนของ EIA (2) หน้ารูป/ตารางที่เป็นภาพของ EIA (3) หน้าค้าง/echo ของเอกสารอื่นใน goal7_batch_ocr_queue.BACKLOG_JOBS
worker 2 ตัวเป็นอิสระต่อกัน — ตัวหนึ่งเสร็จก่อนได้หยิบงานถัดไปทันที ไม่รออีกตัวและไม่รอเปลี่ยนเอกสาร (โหลดโมเดลครั้งเดียวต่อ worker)
OCR อื่น (RapidOCR/Windows OCR/tesseract) เลิกใช้แล้ว (ผู้ใช้ 19 ต.ค. 69) · ต้องรัน goal7_ocr_coverage.py ก่อน · ทำต่อจากที่ค้างได้ (resume)

รัน: E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_typhoon_queue_eia.py [--workers 2] [--only scan|figure|others]
ผลลัพธ์: data/32_goal7_chaophraya2/typhoon_ocr/<ป้ายเอกสาร>/pages.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis.goal7_typhoon_ocr import pending_pages, run_global_queue  # noqa: E402

COVERAGE = ROOT / "analysis/goal7/ocr_coverage.json"
LOW_PRIORITY = {"eia_clarify2_att1", "eia_clarify2_att2"}


def build_tasks(only: str | None) -> list[dict]:
    cov = json.loads(COVERAGE.read_text(encoding="utf-8"))["volumes"]
    tasks: list[dict] = []
    for kind in ("scan", "figure"):
        if only and only != kind:
            continue
        for vol, c in cov.items():
            label = f"eia2569_{vol}"
            for p in pending_pages(label, c[f"todo_{kind}"]):
                tasks.append({"pdf": str(ROOT / c["pdf"]), "label": label, "page": p, "kind": kind})
    if not only or only == "others":
        import pymupdf

        from analysis.goal7_batch_ocr_queue import BACKLOG_JOBS

        for job in sorted(BACKLOG_JOBS, key=lambda j: j["label"] in LOW_PRIORITY):   # เอกสารแนบฉบับชี้แจง (หน้าภาพจำนวนมาก คุณค่าต่อรายงานต่ำ) ทำท้ายสุด
            pdf = Path(job["pdf"])
            if not pdf.exists():
                continue
            n = len(pymupdf.open(pdf))
            pages = job["pages"] or list(range(1, n + 1))
            for p in pending_pages(job["label"], pages):
                tasks.append({"pdf": str(pdf), "label": job["label"], "page": p, "kind": "auto"})
    return tasks


def main() -> None:
    import multiprocessing

    multiprocessing.freeze_support()
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--only", choices=["scan", "figure", "others"])
    a = ap.parse_args()
    tasks = build_tasks(a.only)
    if not tasks:
        print("ไม่มีหน้าค้าง")
        return
    run_global_queue(tasks, workers=a.workers)


if __name__ == "__main__":
    main()
