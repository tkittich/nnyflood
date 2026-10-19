"""เป้าหมาย 7 — วัดความครอบคลุม OCR ของเล่ม EIA 2569 ทั้ง 4 เล่ม (หน้าสแกน/หน้ามีรูปที่เป็นภาพ เทียบกับผล Typhoon-OCR ที่ใช้ได้)

จัดชนิดหน้าด้วย goal7_typhoon_ocr.classify_page: scan (หน้าสแกน) · figure (ข้อความ + ภาพ/รูป/ตารางที่เป็นภาพขนาดใหญ่) · text (ข้อความล้วน — ไม่ต้อง OCR)
สถานะ Typhoon รายหน้า (label eia2569_<main1|main2|app1|app2>): ok (ข้อความใช้ได้) · needs_visual (ถอดไม่ได้/เป็นรูป ต้องอ่านภาพหรือตัดตาราง) · echo (ผลเก่าสะท้อนแม่แบบ) · none
RapidOCR ถือเป็นผลรอง (อ่านไทยได้ไม่ดี — ตัดสินใจ 19 ต.ค. 69 ให้ทำใหม่ด้วย Typhoon ทั้งหมด) จึงไม่นับเป็นครอบคลุม

รัน: python analysis/goal7_ocr_coverage.py
ผลลัพธ์: analysis/goal7/ocr_coverage.json (รวมรายการหน้าที่ต้องทำ todo_scan / todo_figure ต่อเล่ม)
"""
from __future__ import annotations

import json
import sys
import time
import zipfile
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal7_typhoon_ocr import classify_page, is_echo  # noqa: E402  (reuse-first: ตัวจัดชนิดหน้าชุดเดียวกับตัวถอดความ)

ROOT = Path(__file__).resolve().parent.parent
D32 = ROOT / "data/32_goal7_chaophraya2"
ZIP = D32 / "official_eia/256909-65.zip"
EXTRACT = D32 / "official_eia/extracted"
OUT = ROOT / "analysis/goal7/ocr_coverage.json"
VOL = {"สมบูรณ์ เล่ม 1": "main1", "สมบูรณ์ เล่ม 2": "main2", "ภาคผนวก เล่ม 1": "app1", "ภาคผนวก เล่ม 2": "app2"}


def extracted_pdfs() -> dict[str, Path]:
    EXTRACT.mkdir(parents=True, exist_ok=True)
    out = {}
    with zipfile.ZipFile(ZIP) as z:
        for n in z.namelist():
            key = next((v for k, v in VOL.items() if k in n), None)
            if key:
                dst = EXTRACT / f"{key}.pdf"
                if not dst.exists():
                    dst.write_bytes(z.read(n))
                out[key] = dst
    return out


def typhoon_status(label: str) -> dict[int, str]:
    recs: dict[int, dict] = {}
    d = D32 / "typhoon_ocr" / label
    for jl in sorted(d.glob("pages*.jsonl")):
        for ln in jl.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                r = json.loads(ln)
                recs[r["page"]] = r
    st = {}
    for p, r in recs.items():
        meta = r.get("meta") or {}
        if r.get("error"):
            st[p] = "error"
        elif meta.get("needs_visual"):
            st[p] = "needs_visual"
        elif is_echo(r.get("text") or "") or not (r.get("text") or "").strip():
            st[p] = "echo"
        else:
            st[p] = "ok"
    return st


def rapid_pages(label: str) -> set[int]:
    s = set()
    for jl in (D32 / "ocr" / label).glob("pages*.jsonl"):
        for ln in jl.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    s.add(json.loads(ln)["page"])
                except Exception:
                    pass
    return s


def main() -> None:
    pdfs = extracted_pdfs()
    res = {}
    for vol, pdf in pdfs.items():
        doc = fitz.open(pdf)
        classes = {i: classify_page(doc[i - 1]) for i in range(1, len(doc) + 1)}
        ty = typhoon_status(f"eia2569_{vol}")
        rp = rapid_pages(f"eia2569_{'main1' if vol == 'main1' else vol}_imgpages")
        by = {"scan": [], "figure": [], "text": []}
        for p, c in classes.items():
            by[c].append(p)
        todo = {c: [p for p in by[c] if ty.get(p) not in ("ok", "needs_visual")] for c in ("scan", "figure")}
        res[vol] = {
            "pages": len(doc), "pdf": str(pdf.relative_to(ROOT)),
            "classes": {c: len(v) for c, v in by.items()},
            "typhoon": {s: sum(1 for p, x in ty.items() if x == s) for s in ("ok", "needs_visual", "echo", "error")},
            "rapidocr_pages": len(rp),
            "need_ocr_pages": len(by["scan"]) + len(by["figure"]),
            "todo_scan": todo["scan"], "todo_figure": todo["figure"],
        }
        doc.close()
        print(vol, {k: v for k, v in res[vol].items() if k not in ("todo_scan", "todo_figure", "pdf")}, "todo", len(todo["scan"]), len(todo["figure"]))
    OUT.write_text(json.dumps({"generated": time.strftime("%Y-%m-%d"), "volumes": res}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
