"""นำร่องเทียบแบบจำลองภาพ-ภาษา (VLM) อ่านหน้าที่ไม่ใช่ข้อความล้วน (ตาราง · รูปตัด · ภาพผสมตัวอักษร) — Typhoon ยังเป็นตัวหลักของข้อความล้วน
ตั้งไว้ก่อนดูผล: ชุดตัวอย่างมี 3 หน้า "เฉลยที่ตรวจแล้ว" (ตารางรูปตัด · รูปตัดตามยาว · หน้าผสมข้อความกับภาพ) + หน้าควบคุมข้อความล้วน + หน้า needs_visual ไม่มีเฉลย
คะแนน = สัดส่วนของค่าเฉลยที่ปรากฏในผลถอด (ปรับเลขไทยเป็นเลขอารบิก) · ผลถอดทั้งหมดเป็น "ร่าง" ห้ามนำตัวเลขไปใช้ในรายงานก่อนเทียบภาพหน้าจริง
ภาพ 3 แบบต่อหน้า: dpi150 (ฐาน) · dpi250 (วาดซ้ำจาก PDF ละเอียดขึ้น) · enh (dpi150 ขยาย 2 เท่าและเพิ่มความคมชัด — ทดสอบว่าช่วยหรือเพิ่มข้อผิดพลาด)
ขั้นแยกส่วน (layout): Unlimited-OCR (สภาพแวดล้อมแยก E:/theera/unlimited_ocr_env) อ่านหน้าแล้วให้กรอบบล็อกพร้อมประเภท (<|det|>ประเภท [กรอบ]<|/det|>) → ตัดบล็อกรูป/แผนภูมิ/ตาราง/แบบแปลนออกเป็นภาพย่อย → โมเดลที่เก่งภาพกว่าอ่านเฉพาะภาพย่อย (`run <รหัส> crops`)
รัน: python analysis/goal7_vlm_pilot.py render | layout | run <รหัสโมเดล> [crops] | score   (render/score ใช้ typhoon_env · layout ใช้ unlimited_ocr_env · run ใช้ typhoon_env ยกเว้นโมเดลที่ต้องการเวอร์ชันเฉพาะ)
ผลลัพธ์: data/32_goal7_chaophraya2/vlm_pilot/ (ภาพ · ผลถอด) และ analysis/goal7/vlm_pilot_scores.json
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / "data/32_goal7_chaophraya2/vlm_pilot"
EIA = ROOT / "data/32_goal7_chaophraya2/official_eia/extracted"
OCR = ROOT / "data/32_goal7_chaophraya2/typhoon_ocr"
SCORES = ROOT / "analysis/goal7/vlm_pilot_scores.json"
TH = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
VARIANTS = ("dpi150", "dpi250", "enh", "rot250")   # rot250 = dpi250 หมุนตามเข็ม 90° เฉพาะหน้าภาพวาดแนวนอนที่ตัวอักษรอ่านจากล่างขึ้นบน
PROMPT = "อ่านหน้านี้ทั้งหมดอย่างละเอียด ถอดข้อความและตัวเลขทุกตัวตามที่เห็นให้ตรงตัวอักษร ตารางให้เขียนเป็นตาราง Markdown ถ้าเป็นรูปให้ระบุตัวเลขและป้ายกำกับทุกอันที่อ่านได้ ห้ามเดาค่าที่มองไม่เห็น"
# รหัสโมเดล → (repo, วิธีโหลด) — น้ำหนักต้องดาวน์โหลดก่อน (ขออนุมัติผู้ใช้เป็นรายโมเดล)
UOCR_ENV = "E:/theera/unlimited_ocr_env/Scripts/python.exe"
LAYOUT_PROMPT = "<image>document parsing."
VISUAL_TYPES = ("image", "figure", "chart", "picture", "diagram", "table", "plan", "drawing")   # ประเภทบล็อกที่ส่งต่อให้โมเดลภาพ (ยืนยันชื่อประเภทจริงหลังรันครั้งแรก)
DET_RE = re.compile(r"<\|det\|>\s*([^<\[\s]+)\s*(\[+[^<]*?\]+)?\s*<\|/det\|>", re.DOTALL)
MODELS = {
    "qwen25vl7b": "Qwen/Qwen2.5-VL-7B-Instruct",          # 16.6 GB — ตัวฐานที่ผู้ใช้เลือก
    "qwen3vl8b": "Qwen/Qwen3-VL-8B-Instruct",              # 17.5 GB
    "qwen35_4b": "Qwen/Qwen3.5-4B",                        # 9.3 GB — รุ่นใหม่กว่า (Qwen3.5-9B 19.3 GB เสี่ยงล้น VRAM 24 GB จึงยังไม่ใช้)
    "internvl35_8b": "OpenGVLab/InternVL3_5-8B-HF",        # 17.1 GB
    "pathumma": "nectec/Pathumma-llm-vision-3.0.0-re",     # 4.9 GB — ปรับสำหรับ OCR ไทย (ฐาน Qwen3-VL-2B)
    "minicpmv47_1b": "openbmb/MiniCPM-V-4.7-1B",           # 3.1 GB
    "unlimited_ocr": "baidu/Unlimited-OCR",                # 6.7 GB — ใช้เป็นตัวแยกส่วนหน้า (layout) และเทียบอ่านหน้าตาราง/ข้อความ · ภาษาไทยยังไม่ทราบ
}
# ไม่ใช้เพราะโมเดล+ข้อมูลไม่พอใน VRAM 24 GB: Qwen2.5-VL-32B-AWQ (20.7) · InternVL3-14B (30.2) · Qwen3.5-27B/35B-A3B · MiniCPM-V-4.7-35B-A3B int4 (22.6)
HF_HOME = "E:/theera/hf_cache"      # น้ำหนักโมเดลเก็บนอก git และนอกไดรฟ์ C
# เฉลยที่ตรวจแล้ว: ตัวเลขที่รายงานผลกระทบสิ่งแวดล้อมพิมพ์ไว้ (ดู analysis/goal7/official_geometry.json)
SAMPLES = [
    {"id": "sec_table", "pdf": "main1.pdf", "page": 144, "kind": "ตารางรูปตัด 3 ช่วง", "rotate": True, "truth": ["605.22", "53.0", "480", "90.3", "5.426", "1.235", "0.025", "604.85", "51.0", "504", "95.27", "5.29", "0.016", "1187", "398.97", "2.925", "0.517"]},
    {"id": "long_profile", "pdf": "main1.pdf", "page": 142, "kind": "รูปตัดตามยาว 2.3.2-9", "rotate": True, "truth": ["1.75", "6.45", "0.55"]},
    {"id": "siphon_text", "pdf": "main1.pdf", "page": 165, "kind": "ข้อความผสมภาพจำลอง (ท่อลอด 34 แห่ง)", "truth": ["34", "2.00", "4.00", "3.00", "15", "2.3.2-20"]},
    {"id": "control_text", "pdf": "main1.pdf", "page": 162, "kind": "ควบคุม: หน้าข้อความ", "truth": []},
]
UNKEYED_DOCS = [("eia2569_main1", "main1.pdf", 3), ("eia_clarify2_att1", None, 3), ("eia2569_app1", "app1.pdf", 2), ("onwr_bangpakong_final", None, 2)]


def needs_visual_pages(label: str) -> list[int]:
    f = OCR / label / "pages.jsonl"
    if not f.exists():
        return []
    out = []
    for ln in f.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            if (r.get("meta") or {}).get("needs_visual") or r.get("needs_visual"):
                out.append(r["page"])
    return sorted(out)


def enhance(img):
    from PIL import Image, ImageFilter
    big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    return big.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))


def render() -> None:
    import pymupdf
    from PIL import Image
    PILOT.mkdir(parents=True, exist_ok=True)
    jobs = [(s["id"], EIA / s["pdf"], s["page"], s.get("rotate", False)) for s in SAMPLES]
    for label, pdf, k in UNKEYED_DOCS:
        pages = needs_visual_pages(label)
        if not pages or pdf is None:        # เอกสารที่ไม่ได้อยู่ในโฟลเดอร์ official_eia ข้ามไว้ก่อน (ตัวอย่างไม่มีเฉลยเป็นส่วนเสริม)
            continue
        step = max(1, len(pages) // k)
        for p in pages[::step][:k]:
            jobs.append((f"nv_{label}_p{p}", EIA / pdf, p, False))
    manifest = []
    for sid, pdf, page, rot in jobs:
        doc = pymupdf.open(pdf)
        for var, dpi in (("dpi150", 150), ("dpi250", 250)):
            pix = doc[page - 1].get_pixmap(dpi=dpi)
            im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            im.save(PILOT / f"{sid}__{var}.png")
            if rot and var == "dpi250":
                im.rotate(-90, expand=True).save(PILOT / f"{sid}__rot250.png")
        pix = doc[page - 1].get_pixmap(dpi=150)
        enhance(Image.frombytes("RGB", [pix.width, pix.height], pix.samples)).save(PILOT / f"{sid}__enh.png")
        manifest.append({"id": sid, "pdf": Path(pdf).name, "page": page})
    (PILOT / "samples.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(manifest), "หน้า ×", len(VARIANTS), "แบบ →", PILOT)


def run(model_key: str, target: str = "pages") -> None:
    import os
    os.environ.setdefault("HF_HOME", HF_HOME)
    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor
    repo = MODELS[model_key]
    proc = AutoProcessor.from_pretrained(repo, trust_remote_code=True)
    model = AutoModelForImageTextToText.from_pretrained(repo, dtype=torch.bfloat16, device_map="cuda:0", trust_remote_code=True)
    outdir = PILOT / "outputs" / model_key
    outdir.mkdir(parents=True, exist_ok=True)
    if target == "crops":
        items = [(c["id"], ("crop",)) for c in json.loads((PILOT / "crops.json").read_text(encoding="utf-8"))]
    else:
        items = [(s["id"], ("dpi250",) if s["id"].startswith("nv_") else VARIANTS) for s in json.loads((PILOT / "samples.json").read_text(encoding="utf-8"))]   # หน้าไม่มีเฉลยรันแบบ dpi250 แบบเดียว (ประหยัดเวลา)
    for sid, variants in items:
        s = {"id": sid}
        for var in variants:
            if not (PILOT / f"{s['id']}__{var}.png").exists():
                continue
            dst = outdir / f"{s['id']}__{var}.json"
            if dst.exists():
                continue
            img = Image.open(PILOT / f"{s['id']}__{var}.png")
            msgs = [{"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": PROMPT}]}]
            inp = proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt").to(model.device)
            t0 = time.time()
            with torch.no_grad():
                ids = model.generate(**inp, max_new_tokens=1800, do_sample=False)
            text = proc.batch_decode(ids[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0]
            dst.write_text(json.dumps({"id": s["id"], "variant": var, "model": repo, "sec": round(time.time() - t0, 1), "text": text}, ensure_ascii=False), encoding="utf-8")
            print(model_key, s["id"], var, round(time.time() - t0, 1), "s", flush=True)


def parse_blocks(raw: str):
    """แยกบล็อกจากผลของ Unlimited-OCR: คืนรายการ {type, bbox(ตามที่โมเดลให้), text} · ข้อความของบล็อก = ตัวอักษรหลังเครื่องหมายจนถึงเครื่องหมายถัดไป"""
    out = []
    ms = list(DET_RE.finditer(raw))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(raw)
        nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", m.group(2) or "")]
        out.append({"type": m.group(1).strip().lower(), "bbox": nums[:4] if len(nums) >= 4 else None, "text": raw[m.end():end].strip()})
    return out


def bbox_to_px(bbox, w, h, scale=1000.0):
    """กรอบเป็นสัดส่วน 0–999 (สมมติตามรูปแบบ DeepSeek-OCR — ตรวจกับผลจริงก่อนใช้) → พิกเซล"""
    x0, y0, x1, y1 = bbox
    return int(x0 / scale * w), int(y0 / scale * h), int(x1 / scale * w), int(y1 / scale * h)


def layout() -> None:
    """รันด้วย unlimited_ocr_env: ถอดทุกหน้าตัวอย่าง (แบบ dpi250) เก็บผลดิบ + กรอบ + ภาพย่อยของบล็อกภาพ/ตาราง"""
    import torch
    from PIL import Image
    from transformers import AutoModel, AutoTokenizer
    os.environ.setdefault("HF_HOME", HF_HOME)
    tok = AutoTokenizer.from_pretrained(MODELS["unlimited_ocr"], trust_remote_code=True)
    model = AutoModel.from_pretrained(MODELS["unlimited_ocr"], trust_remote_code=True, use_safetensors=True, torch_dtype=torch.bfloat16).eval().cuda()
    outdir = PILOT / "outputs" / "unlimited_ocr"
    cropdir = PILOT / "crops"
    outdir.mkdir(parents=True, exist_ok=True)
    cropdir.mkdir(exist_ok=True)
    crops = []
    for s in json.loads((PILOT / "samples.json").read_text(encoding="utf-8")):
        img_path = PILOT / f"{s['id']}__dpi250.png"
        t0 = time.time()
        res = model.infer(tok, prompt=LAYOUT_PROMPT, image_file=str(img_path), output_path=str(outdir / "_work"), base_size=1024, image_size=640, crop_mode=True,
                          max_length=32768, no_repeat_ngram_size=35, ngram_window=128, save_results=False, eval_mode=True)
        raw = res if isinstance(res, str) else str(res)
        blocks = parse_blocks(raw)
        (outdir / f"{s['id']}__layout.json").write_text(json.dumps({"id": s["id"], "variant": "dpi250", "model": "baidu/Unlimited-OCR", "sec": round(time.time() - t0, 1), "text": raw, "blocks": blocks}, ensure_ascii=False), encoding="utf-8")
        im = Image.open(img_path)
        for k, b in enumerate(blocks):
            if b["bbox"] and any(v in b["type"] for v in VISUAL_TYPES):
                x0, y0, x1, y1 = bbox_to_px(b["bbox"], *im.size)
                m = 12
                cid = f"{s['id']}_c{k}_{b['type']}"
                im.crop((max(0, x0 - m), max(0, y0 - m), min(im.width, x1 + m), min(im.height, y1 + m))).save(cropdir / f"{cid}__crop.png")
                crops.append({"id": cid, "page": s["id"], "type": b["type"], "bbox": b["bbox"]})
        print("layout", s["id"], len(blocks), "บล็อก", round(time.time() - t0, 1), "s", flush=True)
    (PILOT / "crops.json").write_text(json.dumps(crops, ensure_ascii=False, indent=1), encoding="utf-8")


def norm(t: str) -> str:
    return re.sub(r"(?<=\d),(?=\d{3}\b)", "", t.translate(TH))


def score() -> None:
    truth = {s["id"]: s["truth"] for s in SAMPLES if s["truth"]}
    res = {}
    for mdir in sorted((PILOT / "outputs").glob("*")):
        for f in sorted(mdir.glob("*.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            if r["id"] not in truth:
                continue
            nums = set(re.findall(r"\d+(?:\.\d+)*", norm(r["text"])))
            found = [x for x in truth[r["id"]] if x in nums or x.rstrip("0").rstrip(".") in nums]
            res.setdefault(mdir.name, {}).setdefault(r["id"], {})[r["variant"]] = {"found": len(found), "of": len(truth[r["id"]]), "share": round(len(found) / len(truth[r["id"]]), 2), "sec": r["sec"]}
    SCORES.write_text(json.dumps({"note": "สัดส่วนค่าเฉลยที่ปรากฏในผลถอด · ร่าง ไม่ใช่ค่ายืนยัน", "scores": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "render"
    {"render": render, "score": score, "layout": layout}.get(cmd, lambda: run(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "pages"))()
