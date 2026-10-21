"""ทดลอง Indra OCR (datalab-to/indra-ocr · CPU · ONNX) กับหน้าตัวอย่างนำร่อง: ทิศหมุนของหน้า · ป้ายตัวเลขในภาพวาดที่อ่านได้ · กรอบบล็อกข้อความ
สิ่งที่อยากรู้: (1) ตรวจทิศหมุนของหน้าภาพวาดแนวนอนได้ถูกไหม (แทนการลองสองทิศด้วยโมเดลภาพ) (2) อ่านตัวเลขเฉลยในภาพวาดได้เท่าใดแบบเร็วบน CPU (3) ข้อความไทยในหน้าข้อความอ่านได้ใกล้เคียง Typhoon หรือไม่
ข้อจำกัด: ไม่มีป้ายบล็อก "รูป" (มีเฉพาะ Text · Section-Header · Table · Caption · Footnote ...) จึงใช้เป็นตัวแยกรูปโดยตรงไม่ได้ · ใบอนุญาตน้ำหนัก OpenRAIL-M แก้ไข (ใช้วิจัยได้ · ต้องระบุที่มา · แบ่งปันใบอนุญาตเดิมต่อ)
รัน: E:/theera/indra_env/Scripts/python.exe analysis/goal7_indra_probe.py
ผลลัพธ์: data/32_goal7_chaophraya2/vlm_pilot/outputs/indra_ocr/ และ analysis/goal7/indra_probe.json
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / "data/32_goal7_chaophraya2/vlm_pilot"
OUT = ROOT / "analysis/goal7/indra_probe.json"
TH = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
# เฉลย (ตรงกับ goal7_vlm_pilot.SAMPLES — คัดลอกไว้เพราะสคริปต์นี้รันใน env ที่ไม่มี numpy ชุดเดียวกับตัวอื่น)
TRUTH = {
    "sec_table": ["605.22", "53.0", "480", "90.3", "5.426", "1.235", "0.025", "604.85", "51.0", "504", "95.27", "5.29", "0.016", "1187", "398.97", "2.925", "0.517"],
    "long_profile": ["1.75", "6.45", "0.55"],
    "siphon_text": ["34", "2.00", "4.00", "3.00", "15", "2.3.2-20"],
}
VARIANTS = ("dpi150", "dpi250", "rot250")


def hit(x: str, nums) -> bool:
    try:
        v = float(x)
    except ValueError:
        return x in nums
    for n in nums:
        try:
            if abs(float(n) - v) < 1e-9:
                return True
        except ValueError:
            continue
    return x in nums


def main() -> None:
    import cv2
    import indra_ocr
    conv = indra_ocr.load(threads=4)
    outdir = PILOT / "outputs" / "indra_ocr"
    outdir.mkdir(parents=True, exist_ok=True)
    res = {}
    for sid in ("sec_table", "long_profile", "control_text", "siphon_text"):
        for var in VARIANTS:
            f = PILOT / f"{sid}__{var}.png"
            if not f.exists():
                continue
            gray = cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2GRAY)
            t0 = time.time()
            page = conv.ocr(gray)
            sec = time.time() - t0
            text = page.text
            nums = set(re.findall(r"\d+(?:\.\d+)*", text.translate(TH)))
            tr = TRUTH.get(sid)
            row = {"sec": round(sec, 1), "rotation": getattr(page, "rotation", None), "skew": getattr(page, "skew", None), "lines": len(page.lines), "blocks": len(page.blocks),
                   "labels": sorted({b["label"] for b in page.blocks})}
            if tr:
                row["found"], row["of"] = sum(hit(x, nums) for x in tr), len(tr)
            res.setdefault(sid, {})[var] = row
            (outdir / f"{sid}__{var}__indra.json").write_text(json.dumps({"id": sid, "variant": var, "rotation": row["rotation"], "text": text,
                                                                         "blocks": [{"type": b["label"], "bbox": b["bbox"], "text": b["text"]} for b in page.blocks]}, ensure_ascii=False), encoding="utf-8")
            print(sid, var, row, flush=True)
    OUT.write_text(json.dumps({"note": "Indra OCR บน CPU 4 เธรด · เฉลยตรวจแล้ว 3 หน้า", "results": res}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
