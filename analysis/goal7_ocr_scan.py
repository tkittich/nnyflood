"""เป้าหมาย 7 — ค้นคำสำคัญข้ามข้อความ OCR + ชั้นข้อความของ EIA 2569 ทั้ง 4 เล่ม → analysis/goal7/ocr_findings.json

ใช้ตรวจว่าช่องว่างความรู้ (analysis/goal7/gaps.json) ปิดได้หรือไม่ · ผลเป็น "ตัวชี้หน้า" ไม่ใช่ข้อสรุป —
ข้อความที่จะอ้างในรายงานต้องเปิดดูภาพหน้าตรวจซ้ำ (OCR ผิดตัวอักษร/วรรณยุกต์ได้) แล้วบันทึกเป็นข้อเท็จจริงใน goal7_analysis.py (OCR_FACTS)

ค้นด้วยข้อความที่ตัดวรรณยุกต์/ไม้ทัณฑฆาต (OCR มักตกหล่น) · รัน: python analysis/goal7_ocr_scan.py
"""
from __future__ import annotations

import json
import re
import tempfile
import zipfile
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
D32 = ROOT / "data/32_goal7_chaophraya2"
OUT = ROOT / "analysis/goal7/ocr_findings.json"
TONE = re.compile(r"[่-์]")
VOL = {"สมบูรณ์ เล่ม 1": "eia2569_main1", "สมบูรณ์ เล่ม 2": "eia2569_main2", "ภาคผนวก เล่ม 1": "eia2569_app1", "ภาคผนวก เล่ม 2": "eia2569_app2"}

QUERIES = {
    "gate_rules": ["เกณฑ์การเปิด", "เปิดปิดประตู", "เปิด-ปิดประตู", "การเปิดประตู", "ปิดประตู", "คู่มือการบริหาร", "ผู้สั่งการ", "คณะกรรมการบริหารจัดการโครงการ", "แผนการบริหารจัดการน้ำ", "ระดับน้ำที่ต้องเปิด"],
    "fault_boreholes": ["รอยเลื่อน", "เจาะสำรวจ", "หลุมเจาะ", "ผลการเจาะ"],
    "culvert_invert": ["ระดับท้องท่อ", "ท้องท่อ", "ระดับท้องคลอง", "ระดับธรณีท่อ", "ความลึกวางท่อ"],
    "telemetry_locations": ["โทรมาตร", "ศูนย์ปฏิบัติการ", "ระบบเตือนภัย", "สถานีวัดระดับน้ำ"],
    "lateral_flood_model": ["แบบจำลองน้ำท่วม", "น้ำท่วมด้านข้าง", "HEC-RAS", "MIKE", "แบบจำลองสองมิติ", "น้ำท่วมซ้ำซาก", "น้ำท่วมขัง"],
    "khlong29": ["ยี่สิบเก้า", "คลองยี่สิบเก้า"],
    "mussel_notification": ["หอยแมลงภู่", "ผู้เลี้ยง", "แจ้งเตือนล่วงหน้า", "ก่อนการระบายน้ำ"],
    "ground_level_table": ["ระดับดินเดิม", "ระดับพื้นดินเดิม", "ระดับดินธรรมชาติ", "ระดับพื้นดิน"],
    "nn_benefit": ["นครนายก"],
    "diversion_duration": ["1-2 เดือน", "1 - 2 เดือน", "ระยะเวลาการผันน้ำ", "จำนวนวันที่ผันน้ำ", "วันต่อปี"],
    "tourism": ["ท่องเที่ยว", "กิจกรรมทางน้ำ", "เรือท่องเที่ยว", "พักผ่อนหย่อนใจ"],
    "subsidence": ["ทรุดตัว", "การทรุด", "ดินเหนียวอ่อน"],
}


def norm(s: str) -> str:
    return TONE.sub("", s)


def corpora():
    """(label, page, text) ของ OCR ทุกชุด + ชั้นข้อความของ 4 เล่ม EIA 2569"""
    for jl in sorted((D32 / "ocr").glob("*/pages.jsonl")):
        label = jl.parent.name
        for ln in jl.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                r = json.loads(ln)
                yield "ocr:" + label, r["page"], " ".join(x.strip() for x in r["text"].split("\n") if x.strip())
    zp = D32 / "official_eia/256909-65.zip"
    with tempfile.TemporaryDirectory() as td, zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            lab = next((v for k, v in VOL.items() if k in n), None)
            if not lab:
                continue
            p = Path(z.extract(n, td))
            d = fitz.open(p)
            for i, pg in enumerate(d, 1):
                t = pg.get_text().strip()
                if t:
                    yield "text:" + lab, i, re.sub(r"\s+", " ", t)
            d.close()


def main() -> None:
    nq = {g: [(q, norm(q)) for q in qs] for g, qs in QUERIES.items()}
    res: dict = {g: {} for g in QUERIES}
    n_pages = 0
    for src, page, text in corpora():
        n_pages += 1
        nt = norm(text)
        for g, qs in nq.items():
            for q, qn in qs:
                for m in re.finditer(re.escape(qn), nt):
                    h = res[g].setdefault(q, {"n": 0, "hits": []})
                    h["n"] += 1
                    if len(h["hits"]) < 12:
                        h["hits"].append({"src": src, "page": page, "snippet": nt[max(0, m.start() - 110):m.end() + 140]})
    summary = {g: {q: v["n"] for q, v in d.items()} for g, d in res.items()}
    OUT.write_text(json.dumps({"pages_scanned": n_pages, "summary": summary, "hits": res,
                               "note": "ตัวชี้หน้าจากข้อความที่ตัดวรรณยุกต์ — ต้องเปิดภาพหน้าตรวจก่อนอ้าง"}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("pages", n_pages)
    for g, d in summary.items():
        print(g, d)


if __name__ == "__main__":
    main()
