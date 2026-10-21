"""เทียบผลถอดของ Typhoon กับ Indra OCR (CPU) ทุกหน้าที่ Typhoon เคยอ่านไว้ — ตัวเลขตรงกันเท่าใด หน้าไหนขัดแย้งมาก (เป็นรายการหน้าไปตรวจด้วยตา)
ตั้งไว้ก่อนดูผล: หน้านับเมื่อทั้งสองตัวอ่านพบตัวเลขรวมกันอย่างน้อย 5 ค่า · วัดดัชนี Jaccard ของเซตตัวเลข (เลขไทย→อารบิก ตัดเครื่องหมาย กม. เช่น 23+000) · ขัดแย้งมาก = Jaccard < 0.5
ข้อจำกัด: ไม่มีเฉลยที่แน่นอน — ความตรงกันบอกแค่ว่าตัวไหนน่าตรวจ ไม่บอกว่าตัวไหนถูก (ต้องดูภาพหน้าตัดสิน) · Typhoon ใช้ความละเอียด 140–150 dpi ส่วน Indra ใช้ 200 dpi
รัน: E:/theera/indra_env/Scripts/python.exe analysis/goal7_indra_vs_typhoon.py [--labels a,b]
ผลลัพธ์: data/32_goal7_chaophraya2/indra_vs_typhoon/<ชื่อ>.jsonl และ analysis/goal7/indra_vs_typhoon.json
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))
OCR = ROOT / "data/32_goal7_chaophraya2/typhoon_ocr"
EIA = ROOT / "data/32_goal7_chaophraya2/official_eia/extracted"
OUTD = ROOT / "data/32_goal7_chaophraya2/indra_vs_typhoon"
SUMMARY = ROOT / "analysis/goal7/indra_vs_typhoon.json"
TH = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
EIA_VOLS = {"eia2569_main1": "main1.pdf", "eia2569_main2": "main2.pdf", "eia2569_app1": "app1.pdf", "eia2569_app2": "app2.pdf"}


def strip_tags(t: str) -> str:
    return re.sub(r"<[^>]+>", " ", t)


def nums(t: str) -> set:
    out = set()
    for x in re.findall(r"(?<![\d+])-?\d+(?:[.,]\d+)*(?![\d+])", re.sub(r"\d+\+\d+", "", strip_tags(t).translate(TH))):
        try:
            out.add(float(x.replace(",", "")))
        except ValueError:
            pass
    return out


def pdf_map() -> dict:
    import goal7_batch_ocr_queue as q
    m = {j["label"]: Path(j["pdf"]) for j in q.BACKLOG_JOBS}
    for k, v in EIA_VOLS.items():
        m[k] = EIA / v
    return m


def main() -> None:
    import cv2
    import indra_ocr
    import numpy as np
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="")
    a = ap.parse_args()
    OUTD.mkdir(parents=True, exist_ok=True)
    pm = pdf_map()
    labels = [x for x in a.labels.split(",") if x] or sorted(p.parent.name for p in OCR.glob("*/pages.jsonl") if p.parent.name in pm)
    conv = indra_ocr.load(threads=4)
    for lb in labels:
        out = OUTD / f"{lb}.jsonl"
        done = {json.loads(x)["page"] for x in out.read_text(encoding="utf-8").splitlines() if x.strip()} if out.exists() else set()
        recs = [json.loads(x) for x in (OCR / lb / "pages.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        todo = [r for r in recs if r["page"] not in done]
        if not todo:
            continue
        doc = pymupdf.open(pm[lb])
        t0 = time.time()
        with out.open("a", encoding="utf-8") as fh:
            for r in todo:
                try:
                    pix = doc[r["page"] - 1].get_pixmap(dpi=200)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if pix.n >= 3 else img[:, :, 0]
                    page = conv.ocr(gray)
                    ni, nt = nums(page.text), nums(r.get("text") or "")
                    row = {"page": r["page"], "n_typhoon": len(nt), "n_indra": len(ni), "jaccard": round(len(ni & nt) / len(ni | nt), 3) if (ni | nt) else None,
                           "chars_typhoon": len(strip_tags(r.get("text") or "")), "chars_indra": len(page.text), "kind": (r.get("meta") or {}).get("kind")}
                except Exception as e:   # noqa: BLE001
                    row = {"page": r["page"], "error": f"{type(e).__name__}: {str(e)[:120]}"}
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(lb, len(todo), "หน้า", round(time.time() - t0), "s", flush=True)
    # สรุป
    summ = {"note": "ความตรงกันของตัวเลข Typhoon vs Indra OCR (ไม่มีเฉลย — ใช้ชี้หน้าที่ควรตรวจด้วยตา)", "labels": {}}
    for f in sorted(OUTD.glob("*.jsonl")):
        rows = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
        use = [r for r in rows if r.get("jaccard") is not None and (r["n_typhoon"] + r["n_indra"]) >= 5]
        low = [r["page"] for r in use if r["jaccard"] < 0.5]
        summ["labels"][f.stem] = {"pages": len(rows), "pages_compared": len(use), "mean_jaccard": round(sum(r["jaccard"] for r in use) / len(use), 3) if use else None,
                                  "pages_low_agreement": len(low), "low_pages_sample": low[:15], "errors": sum(1 for r in rows if r.get("error"))}
    SUMMARY.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: (v["pages_compared"], v["mean_jaccard"], v["pages_low_agreement"]) for k, v in summ["labels"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
