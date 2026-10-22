"""เทียบ Typhoon กับ Indra OCR บนหน้าที่มี "ชั้นข้อความ PDF" (เฉลยที่แน่นอน) — วัดความคล้ายตัวอักษรและการพบตัวเลข ตัวไหนอ่านไทยพิมพ์/ตารางได้แม่นกว่า
เกณฑ์ตั้งก่อนดูผล: 30 หน้าชุดเดียวกับ goal7_indra_text_eval (สุ่มเมล็ด 7 · ชั้นข้อความยาว >1,500 อักขระ) · ความคล้าย = SequenceMatcher บน 3,000 อักขระแรก (ตัดช่องว่าง เลขไทย→อารบิก ตัดแท็ก HTML ของตาราง Typhoon) · พบตัวเลข = สัดส่วนเซตตัวเลขของชั้นข้อความที่พบในผลถอด
ข้อจำกัด: เป็นหน้าพิมพ์สะอาด (ไม่ใช่หน้าสแกนเสื่อมสภาพ) · Typhoon อ่านด้วยโหมด text ที่ 150 dpi
รัน: E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_typhoon_ocr.py --pdf .../main1.pdf --label tmp_typhoon_eval --pages <หน้า> --kind text --workers 2  แล้ว  E:/theera/indra_env/Scripts/python.exe analysis/goal7_ocr_accuracy_vs_textlayer.py
ผลลัพธ์: analysis/goal7/ocr_accuracy_vs_textlayer.json
"""
import difflib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data/32_goal7_chaophraya2/official_eia/extracted/main1.pdf"
TY = ROOT / "data/32_goal7_chaophraya2/typhoon_ocr/tmp_typhoon_eval/pages.jsonl"
PAGES = json.loads((ROOT / "analysis/goal7/indra_text_eval.json").read_text(encoding="utf-8"))["pages"]
OUT = ROOT / "analysis/goal7/ocr_accuracy_vs_textlayer.json"
TH = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")


def clean(s: str) -> str:
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", " ", s).translate(TH))


def numset(s: str) -> set:
    return set(re.findall(r"\d+(?:\.\d+)*", re.sub(r"<[^>]+>", " ", s).translate(TH)))


def score(truth_raw: str, out_raw: str) -> tuple[float, float]:
    t, o = clean(truth_raw), clean(out_raw)
    sim = difflib.SequenceMatcher(None, t[:3000], o[:3000], autojunk=False).ratio()
    nt = numset(truth_raw)
    return round(sim, 3), round(len(nt & numset(out_raw)) / max(1, len(nt)), 3)


def main() -> None:
    import cv2
    import indra_ocr
    import numpy as np
    import pymupdf
    ty = {}
    for ln in TY.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            ty[r["page"]] = r.get("text") or ""
    doc = pymupdf.open(PDF)
    conv = indra_ocr.load(threads=4)
    rows = []
    for p in PAGES:
        if p not in ty:
            continue
        pg = doc[p - 1]
        truth = pg.get_text()
        pix = pg.get_pixmap(dpi=200)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if pix.n >= 3 else img[:, :, 0]
        ind = conv.ocr(gray).text
        st, nt = score(truth, ty[p])
        si, ni = score(truth, ind)
        rows.append({"page": p, "typhoon_sim": st, "typhoon_numrecall": nt, "indra_sim": si, "indra_numrecall": ni,
                     "has_table_tags": "<table" in ty[p] or "<td" in ty[p]})
    n = len(rows)
    res = {"note": "เทียบชั้นข้อความ PDF (เฉลยแน่นอน) · 30 หน้า EIA เล่ม 1 · Typhoon โหมด text 150 dpi · Indra 200 dpi", "pages_compared": n, "rows": rows,
           "mean": {k: round(sum(r[k] for r in rows) / n, 3) for k in ("typhoon_sim", "typhoon_numrecall", "indra_sim", "indra_numrecall")} if n else None,
           "pages_indra_better": sum(1 for r in rows if r["indra_sim"] > r["typhoon_sim"] + 0.02), "pages_typhoon_better": sum(1 for r in rows if r["typhoon_sim"] > r["indra_sim"] + 0.02)}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("pages_compared", "mean", "pages_indra_better", "pages_typhoon_better")}, ensure_ascii=False))
    shutil.rmtree(TY.parent, ignore_errors=True)       # ไม่ให้ผลทดสอบปนเข้าดัชนีค้นหา


if __name__ == "__main__":
    main()
