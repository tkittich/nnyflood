"""เป้าหมาย 7 — ตรวจค่าคงที่ใน analysis/goal7/source_constants.json กับเอกสารต้นทาง (ชั้นข้อความของ PDF EIA + ภาพหลักฐาน)

ตรวจ 2 แบบ: (1) text_layer — ค้นข้อความที่คาดหมาย (ตัดวรรณยุกต์) ในหน้าที่ระบุของเล่ม EIA 2569 ที่อยู่ใน data/32_goal7_chaophraya2/official_eia/256909-65.zip
(2) image_evidence — ไฟล์ภาพหลักฐานมีอยู่และแฮช SHA-256 ตรงที่บันทึก (ภาพต้องเปิดดูด้วยตาเพื่อยืนยันค่า — สคริปต์ตรวจแค่ว่าภาพไม่ถูกเปลี่ยน)
ผลสถานะ: verified_text · verified_image · failed (ตรวจแล้วไม่พบ) · assumption · unverified (ไม่มีวิธีตรวจ) · conflict (ขัดกับค่าอื่นในไฟล์ — ต้องคนตัดสิน)
บันทึกเลขหน้าที่พิมพ์ (เช่น 2-92) จากหัวหน้าอัตโนมัติ · ไม่แก้ source_constants.json

รัน: python analysis/goal7_verify_constants.py
ผลลัพธ์: analysis/goal7/source_constants_verification.json
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal7_ocr_scan as sc  # noqa: E402  (reuse-first: ตัวอ่านชั้นข้อความ/OCR ชุดเดียวกับที่ค้นช่องว่างความรู้)

ROOT = Path(__file__).resolve().parent.parent
CONST = ROOT / "analysis/goal7/source_constants.json"
OUT = ROOT / "analysis/goal7/source_constants_verification.json"
PRINTED = re.compile(r"(?:รายละเอียดโครงการ|ประเมินผลกระทบสิ่งแวดล้อม)[^\n]{0,60}?\b(\d{1,2}-\d{1,3})\b\s*FN_EIA")


def main() -> None:
    consts = json.loads(CONST.read_text(encoding="utf-8"))["constants"]
    need: dict[tuple[str, int], str] = {}
    for c in consts.values():
        for v in c["verify"]:
            if v["type"] == "text_layer":
                need[(v["corpus"], v["page"])] = ""
    for src, page, text in sc.corpora():
        if (src, page) in need:
            need[(src, page)] = text
    results = {}
    for cid, c in consts.items():
        checks = []
        for v in c["verify"]:
            if v["type"] == "text_layer":
                text = need.get((v["corpus"], v["page"]), "")
                nt = sc.norm(text)
                found = {n: (sc.norm(n) in nt) for n in v["needles"]}
                m = PRINTED.search(text) if text else None
                checks.append({"type": "text_layer", "corpus": v["corpus"], "pdf_page": v["page"], "printed_page": m.group(1) if m else None,
                               "page_text_chars": len(text), "needles": found, "ok": bool(text) and all(found.values())})
            elif v["type"] == "image_evidence":
                p = ROOT / v["file"]
                ok = p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == v["sha256"]
                checks.append({"type": "image_evidence", "file": v["file"], "reading": v.get("reading"), "sha256_ok": ok, "ok": ok})
        if c["method"] == "assumption":
            status = "assumption"
        elif not checks:
            status = "unverified"
        elif any(x["type"] == "text_layer" and not x["ok"] for x in checks):
            status = "failed"
        elif any(x["type"] == "text_layer" and x["ok"] for x in checks):
            status = "verified_text"
        else:
            status = "verified_image" if all(x["ok"] for x in checks) else "failed"
        if c.get("conflicts_with"):
            status = "conflict"
        results[cid] = {"status": status, "checks": checks, "conflicts_with": c.get("conflicts_with", [])}
    summary: dict[str, int] = {}
    for r in results.values():
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    OUT.write_text(json.dumps({"verified_on": time.strftime("%Y-%m-%d"), "constants_sha256": hashlib.sha256(CONST.read_bytes()).hexdigest(), "summary": summary, "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(summary)
    for cid, r in results.items():
        if r["status"] in ("failed", "conflict", "unverified"):
            print(" ", r["status"], cid)


if __name__ == "__main__":
    main()
