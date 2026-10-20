"""เทียบตัวแยกส่วนหน้าเอกสาร (layout) สำหรับนำร่อง VLM: Unlimited-OCR กับ PP-DocLayoutV3 บนหน้าตัวอย่าง 4 หน้าที่ผมวัดกรอบ "รูป/ภาพวาด" จริงด้วยตา
ตั้งไว้ก่อนดูผล: เฉลย = กรอบของรูป/ภาพวาด (ไม่รวมคำบรรยายใต้รูป) · วัดสองอย่าง — (ก) ความครอบคลุม: สัดส่วนพื้นที่กรอบเฉลยที่ถูกครอบด้วยกรอบรูปที่ตรวจพบ (ภาพย่อยต้องไม่ตัดภาพขาด)
(ข) ส่วนเกิน: สัดส่วนพื้นที่กรอบรูปที่ตรวจพบซึ่งอยู่นอกกรอบเฉลย (ภาพย่อยที่ไม่ใช่รูป) + จำนวนกรอบหลังรวมกรอบที่ซ้อนกัน (ยิ่งแตกเป็นชิ้นเล็กยิ่งแย่)
ข้อจำกัด: เฉลยมี 4 หน้า (ภาพวาด 3 หน้า + ภาพถ่าย 4 รูปหนึ่งหน้า) — ชี้แนวโน้มเท่านั้น · "control_text" ในชุดตัวอย่างเป็นหน้าแบบแปลน ปตร. ไม่ใช่หน้าข้อความ
รัน: E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_layout_compare.py detect  แล้ว  python analysis/goal7_layout_compare.py compare   (detect ต้องใช้ opencv-python-headless ใน typhoon_env)
ผลลัพธ์: data/32_goal7_chaophraya2/vlm_pilot/outputs/pp_doclayoutv3/ และ analysis/goal7/layout_compare.json
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / "data/32_goal7_chaophraya2/vlm_pilot"
OUT = ROOT / "analysis/goal7/layout_compare.json"
HF_HOME = "E:/theera/hf_cache"
PP_REPO = "PaddlePaddle/PP-DocLayoutV3_safetensors"
VISUAL = ("image", "chart", "figure", "table", "picture", "drawing")
EXCLUDE = ("caption", "title")      # คำบรรยายใต้รูปไม่นับเป็นรูป
# เฉลย: กรอบรูป/ภาพวาด สัดส่วน 0–999 ของหน้า dpi150 (วัดด้วยตาจากภาพหน้า)
TRUTH = {
    "sec_table": [[158, 101, 876, 825]],
    "long_profile": [[171, 98, 926, 859]],
    "control_text": [[160, 103, 873, 847]],
    "siphon_text": [[171, 111, 511, 290], [513, 111, 849, 290], [171, 292, 511, 470], [513, 292, 849, 470]],
}


def detect() -> None:
    os.environ.setdefault("HF_HOME", HF_HOME)
    from PIL import Image
    from transformers import pipeline
    det = pipeline("object-detection", model=PP_REPO, device=-1, threshold=0.3)
    outdir = PILOT / "outputs" / "pp_doclayoutv3"
    outdir.mkdir(parents=True, exist_ok=True)
    for sid in TRUTH:
        im = Image.open(PILOT / f"{sid}__dpi150.png").convert("RGB")
        res = det(im)
        boxes = []
        for r in res:
            b = r["box"]
            boxes.append({"type": str(r["label"]).lower(), "score": round(float(r["score"]), 3),
                          "bbox": [b["xmin"] / im.width * 1000, b["ymin"] / im.height * 1000, b["xmax"] / im.width * 1000, b["ymax"] / im.height * 1000]})
        (outdir / f"{sid}__layout.json").write_text(json.dumps({"id": sid, "model": PP_REPO, "blocks": boxes}, ensure_ascii=False), encoding="utf-8")
        print("detect", sid, len(boxes), sorted({b["type"] for b in boxes}), flush=True)


def visual_boxes(blocks):
    return [b["bbox"] for b in blocks if b.get("bbox") and any(v in b["type"] for v in VISUAL) and not any(e in b["type"] for e in EXCLUDE)]


def merge_overlapping(boxes):
    """รวมกรอบที่ซ้อนกันมากเป็นกรอบเดียว (ครอบทั้งสอง) เพื่อนับชิ้นภาพย่อยที่ต้องส่งต่อจริง"""
    from shapely.geometry import box as sbox
    from shapely.ops import unary_union
    if not boxes:
        return []
    u = unary_union([sbox(*b) for b in boxes])
    geoms = list(u.geoms) if hasattr(u, "geoms") else [u]
    return [g.bounds for g in geoms]


def compare() -> None:
    from shapely.geometry import box as sbox
    from shapely.ops import unary_union
    res = {"truth_pages": list(TRUTH), "tools": {}}
    for tool, folder in (("unlimited_ocr", "unlimited_ocr"), ("pp_doclayoutv3", "pp_doclayoutv3")):
        rows = {}
        for sid, truths in TRUTH.items():
            f = PILOT / "outputs" / folder / f"{sid}__layout.json"
            if not f.exists():
                continue
            blocks = json.loads(f.read_text(encoding="utf-8"))["blocks"]
            vb = visual_boxes(blocks)
            merged = merge_overlapping(vb)
            pred = unary_union([sbox(*b) for b in merged]) if merged else None
            tr = unary_union([sbox(*b) for b in truths])
            cover = (pred.intersection(tr).area / tr.area) if pred is not None else 0.0
            excess = ((pred.difference(tr).area / pred.area) if pred is not None and pred.area > 0 else 0.0)
            rows[sid] = {"truth_boxes": len(truths), "predicted_visual_raw": len(vb), "predicted_after_merge": len(merged), "coverage": round(cover, 3), "excess": round(excess, 3)}
        if rows:
            res["tools"][tool] = {"pages": rows, "mean_coverage": round(sum(r["coverage"] for r in rows.values()) / len(rows), 3), "mean_excess": round(sum(r["excess"] for r in rows.values()) / len(rows), 3)}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    {"detect": detect, "compare": compare}[sys.argv[1] if len(sys.argv) > 1 else "compare"]()
