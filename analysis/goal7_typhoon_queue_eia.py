"""เป้าหมาย 7 — คิว Typhoon-OCR ของเล่ม EIA 2569 ทั้ง 4 เล่ม ตาม analysis/goal7/ocr_coverage.json (ต้องรัน goal7_ocr_coverage.py ก่อน)

ลำดับ: (1) หน้าสแกน (ข้อความภาษาไทยล้วน — คุณภาพดีและเร็ว) ทุกเล่ม · (2) หน้ารูป/ตารางที่เป็นภาพ (ทำครั้งเดียวจำกัดความยาว — ถ้าถอดไม่ได้ทำเครื่องหมาย needs_visual ไม่แต่งข้อความ)
ผลต่อเล่มที่ data/32_goal7_chaophraya2/typhoon_ocr/eia2569_<เล่ม>/ (pages.jsonl + document.md) · ทำต่อจากที่ค้างได้ (resume) · ใช้ GPU 2 worker พร้อมกัน

รัน: E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_typhoon_queue_eia.py [--workers 2] [--only scan|figure] [--volumes main1,app1]
ผลลัพธ์: data/32_goal7_chaophraya2/typhoon_ocr/eia2569_<เล่ม>/pages.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis.goal7_typhoon_ocr import run_job  # noqa: E402

COVERAGE = ROOT / "analysis/goal7/ocr_coverage.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--only", choices=["scan", "figure"])
    ap.add_argument("--volumes")
    a = ap.parse_args()
    cov = json.loads(COVERAGE.read_text(encoding="utf-8"))["volumes"]
    vols = a.volumes.split(",") if a.volumes else list(cov)
    for kind in ("scan", "figure"):
        if a.only and a.only != kind:
            continue
        for vol in vols:
            pages = cov[vol][f"todo_{kind}"]
            if not pages:
                print(f"[{vol}/{kind}] ไม่มีหน้าค้าง", flush=True)
                continue
            print(f"[{vol}/{kind}] {len(pages)} หน้า", flush=True)
            run_job(ROOT / cov[vol]["pdf"], f"eia2569_{vol}", pages=pages, dpi=150, workers=a.workers, kind=kind)


if __name__ == "__main__":
    main()
