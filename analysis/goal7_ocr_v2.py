"""ขั้นตอน OCR รุ่นที่ 2 สำหรับหน้า needs_visual ของ EIA — แยกส่วนหน้า → ตัดภาพย่อยรูป/ตาราง/แบบแปลน → โมเดลภาพอ่านภาพย่อยแบบขยายคมชัด (ผลเป็นร่างเสมอ)
ขั้นตอน (ต่อไฟล์ ทำซ้ำได้ ข้ามงานที่เสร็จแล้ว): layout (Unlimited-OCR · unlimited_ocr_env) → crops (ไม่ใช้ GPU) → read <โมเดล> (typhoon_env) → report
ข้อสรุปตัวอ่านจากนำร่อง: ตัวหลัก Qwen3-VL-8B · ตัวที่สอง Qwen2.5-VL-7B (ผิดคนละจุด ใช้จับค่าที่ไม่ตรงกัน) — ดู docs/OCR_WORKFLOW_V2.md
ข้อจำกัด: ความละเอียดต้นฉบับเป็นเพดาน (ภาพวาดเป็น JPEG ภาพเดียว) · หมุนภาพวาดแนวนอนด้วยการลองสองทิศกับบล็อกใหญ่ · ภาพสีสดจัดเป็นภาพถ่าย/แผนที่ ข้ามการอ่านรอบแรก · ข้อความไทยในบล็อกข้อความเป็นร่างจาก Unlimited-OCR (วรรณยุกต์ผิดได้) ไม่ใช่ผลของ Typhoon
รัน: python analysis/goal7_ocr_v2.py pages | E:/theera/unlimited_ocr_env/Scripts/python.exe analysis/goal7_ocr_v2.py layout <เล่ม> [--limit N] | python analysis/goal7_ocr_v2.py crops <เล่ม> | E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_ocr_v2.py read <รหัสโมเดล> <เล่ม> | python analysis/goal7_ocr_v2.py report
ผลลัพธ์: data/32_goal7_chaophraya2/ocr_v2/<เล่ม>/p<หน้า>/ (ภาพ · layout.json · crops · reads) และ analysis/goal7/ocr_v2_summary.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_vlm_pilot as pilot  # noqa: E402  (reuse-first: ตัวแยกบล็อก · กรอบ→พิกเซล · ขยายคมชัด · รายชื่อโมเดล)

OCR = ROOT / "data/32_goal7_chaophraya2/typhoon_ocr"
EIA = ROOT / "data/32_goal7_chaophraya2/official_eia/extracted"
V2 = ROOT / "data/32_goal7_chaophraya2/ocr_v2"
SUMMARY = ROOT / "analysis/goal7/ocr_v2_summary.json"
VOLS = {"eia2569_main1": "main1.pdf", "eia2569_main2": "main2.pdf", "eia2569_app1": "app1.pdf", "eia2569_app2": "app2.pdf"}
MIN_AREA = 0.015           # กรอบเล็กกว่า 1.5% ของหน้าไม่ตัด (ไอคอน/โลโก้)
BIG_AREA = 0.25            # บล็อกใหญ่ (>=25% ของหน้า) ลองสองทิศ
COLORFUL = 0.22            # ความอิ่มสีเฉลี่ยสูงกว่านี้ = ภาพถ่าย/แผนที่สี ข้ามการอ่านรอบแรก
READ_TRIAGE = "minicpmv47_1b"      # คัดกรองเร็ว + เลือกทิศหมุนของบล็อกใหญ่
READ_MAIN = "qwen3vl8b"
READ_SECOND = "qwen25vl7b"
PROBE_TOKENS = 350
TRIAGE_TOKENS = 400
GATE = 6                    # ตัวอ่านหลัก/ตัวที่สองอ่านเฉพาะภาพย่อยที่การคัดกรองพบตัวเลขอย่างน้อยเท่านี้ (แผนที่/ภาพที่ไม่มีตัวเลขไม่เสียเวลา)


def needs_visual_pages(vol: str) -> list[int]:
    f = OCR / vol / "pages.jsonl"
    out = []
    for ln in f.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            if (r.get("meta") or {}).get("needs_visual") or r.get("needs_visual"):
                out.append(r["page"])
    return sorted(out)


def pdir(vol: str, page: int) -> Path:
    d = V2 / vol / f"p{page:04d}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cmd_pages(_a) -> None:
    for v in VOLS:
        print(v, len(needs_visual_pages(v)))


def cmd_layout(a) -> None:
    """รันด้วย unlimited_ocr_env"""
    import pymupdf
    import torch
    from transformers import AutoModel, AutoTokenizer
    os.environ.setdefault("HF_HOME", pilot.HF_HOME)
    pages = needs_visual_pages(a.vol)
    if a.limit:
        pages = pages[:: max(1, len(pages) // a.limit)][: a.limit]
    todo = [p for p in pages if not (pdir(a.vol, p) / "layout.json").exists()]
    if not todo:
        print("ไม่มีงานค้าง")
        return
    tok = AutoTokenizer.from_pretrained(pilot.MODELS["unlimited_ocr"], trust_remote_code=True)
    model = AutoModel.from_pretrained(pilot.MODELS["unlimited_ocr"], trust_remote_code=True, use_safetensors=True, torch_dtype=torch.bfloat16).eval().cuda()
    doc = pymupdf.open(EIA / VOLS[a.vol])
    for p in todo:
        d = pdir(a.vol, p)
        pix = doc[p - 1].get_pixmap(dpi=250)
        img = d / "page.png"
        pix.save(img)
        t0 = time.time()
        try:
            res = model.infer(tok, prompt=pilot.LAYOUT_PROMPT, image_file=str(img), output_path=str(d / "_work"), base_size=1024, image_size=640, crop_mode=True,
                              max_length=32768, no_repeat_ngram_size=35, ngram_window=128, save_results=False, eval_mode=True)
            raw = res if isinstance(res, str) else str(res)
            err = None
        except Exception as e:   # noqa: BLE001
            raw, err = "", f"{type(e).__name__}: {str(e)[:200]}"
            torch.cuda.empty_cache()
        (d / "layout.json").write_text(json.dumps({"vol": a.vol, "page": p, "sec": round(time.time() - t0, 1), "error": err, "text": raw, "blocks": pilot.parse_blocks(raw)}, ensure_ascii=False), encoding="utf-8")
        print("layout", a.vol, p, len(pilot.parse_blocks(raw)), "บล็อก", round(time.time() - t0, 1), "s", "ERR" if err else "", flush=True)


def saturation(im) -> float:
    import numpy as np
    small = im.resize((128, 128)).convert("HSV")
    return float(np.asarray(small)[:, :, 1].mean() / 255.0)


def cmd_crops(a) -> None:
    from PIL import Image
    for p in needs_visual_pages(a.vol):
        d = pdir(a.vol, p)
        lf = d / "layout.json"
        if not lf.exists() or (d / "crops.json").exists():
            continue
        im = Image.open(d / "page.png")
        blocks = json.loads(lf.read_text(encoding="utf-8"))["blocks"]
        vis = [(k, b) for k, b in enumerate(blocks) if b["bbox"] and any(v in b["type"] for v in pilot.VISUAL_TYPES) and "caption" not in b["type"]]
        keep = []
        for k, b in vis:
            x0, y0, x1, y1 = b["bbox"]
            area = (x1 - x0) * (y1 - y0) / 1e6
            if area < MIN_AREA:
                continue
            if any((o["bbox"][0] <= x0 + 2 and o["bbox"][1] <= y0 + 2 and o["bbox"][2] >= x1 - 2 and o["bbox"][3] >= y1 - 2) and (o is not b) and ((o["bbox"][2] - o["bbox"][0]) * (o["bbox"][3] - o["bbox"][1]) / 1e6 > area * 1.05) for _, o in vis):
                continue
            keep.append((k, b, area))
        crops = []
        (d / "crops").mkdir(exist_ok=True)
        for k, b, area in keep:
            x0, y0, x1, y1 = pilot.bbox_to_px(b["bbox"], *im.size)
            c = im.crop((max(0, x0 - 12), max(0, y0 - 12), min(im.width, x1 + 12), min(im.height, y1 + 12)))
            sat = saturation(c)
            cid = f"c{k}_{b['type']}"
            c.save(d / "crops" / f"{cid}.png")
            crops.append({"id": cid, "type": b["type"], "bbox": b["bbox"], "area_share": round(area, 3), "px": list(c.size), "saturation": round(sat, 3),
                          "big": area >= BIG_AREA, "skip_reason": "ภาพสีสด (ภาพถ่าย/แผนที่)" if sat > COLORFUL else None, "rotation": None})
        (d / "crops.json").write_text(json.dumps(crops, ensure_ascii=False, indent=1), encoding="utf-8")
        print("crops", a.vol, p, len(crops), flush=True)


def digit_score(text: str) -> int:
    return len(re.findall(r"\d+\.\d+|\d{3,}", pilot.norm(text)))


def cmd_read(a) -> None:
    """รันด้วย typhoon_env: อ่านภาพย่อยแบบขยายคมชัด · บล็อกใหญ่ลองสองทิศด้วยตัวหลัก (ตัวที่สองใช้ทิศที่ตัวหลักเลือก)"""
    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor
    os.environ.setdefault("HF_HOME", pilot.HF_HOME)
    triage = a.model == READ_TRIAGE
    jobs = []
    for p in needs_visual_pages(a.vol):
        d = pdir(a.vol, p)
        if (d / "crops.json").exists():
            for c in json.loads((d / "crops.json").read_text(encoding="utf-8")):
                if c["skip_reason"] or (d / "reads" / f"{c['id']}__{a.model}.json").exists():
                    continue
                if not triage:       # ตัวอ่านหลัก/ตัวที่สอง: ต้องผ่านการคัดกรองก่อน (Indra บน CPU เป็นหลัก · ไม่มีก็ใช้ MiniCPM)
                    tf = d / "reads" / f"{c['id']}__indra.json"
                    if not tf.exists():
                        tf = d / "reads" / f"{c['id']}__{READ_TRIAGE}.json"
                    if not tf.exists() or digit_score(json.loads(tf.read_text(encoding="utf-8"))["text"]) < GATE:
                        continue
                    if a.model == READ_SECOND and not (c["big"] or "table" in c["type"]):
                        continue
                jobs.append((p, d, c))
    if a.limit:
        jobs = jobs[: a.limit]
    if not jobs:
        print("ไม่มีงานค้าง")
        return
    repo = pilot.MODELS[a.model]
    proc = AutoProcessor.from_pretrained(repo, trust_remote_code=True)
    model = AutoModelForImageTextToText.from_pretrained(repo, dtype=torch.bfloat16, device_map="cuda:0", trust_remote_code=True)

    from transformers import StoppingCriteria, StoppingCriteriaList
    empty_rows = re.compile(r"(?:\|\s*){3,}\|\s*\n(?:\|\s*){3,}\|\s*\n(?:\|\s*){3,}\|\s*\n(?:\|\s*){3,}\|\s*\n(?:\|\s*){3,}\|")

    class StopEmptyRows(StoppingCriteria):
        """หยุดเมื่อโมเดลวนเขียนแถวตารางว่างซ้ำ ๆ (พบในนำร่อง: เสียเวลาจนเต็มโทเคน)"""
        def __init__(self, n0):
            self.n0, self.tick = n0, 0

        def __call__(self, input_ids, scores, **kw):
            self.tick += 1
            if self.tick % 48:
                return False
            tail = proc.batch_decode(input_ids[:, max(self.n0, input_ids.shape[1] - 160):], skip_special_tokens=True)[0]
            return bool(empty_rows.search(tail))

    def ask(img, max_new):
        if img.width * img.height > pilot.MAX_PIX:
            k = (pilot.MAX_PIX / (img.width * img.height)) ** 0.5
            img = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
        msgs = [{"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": pilot.PROMPT}]}]
        inp = proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt").to(model.device)
        try:
            with torch.no_grad():
                ids = model.generate(**inp, max_new_tokens=max_new, do_sample=False, stopping_criteria=StoppingCriteriaList([StopEmptyRows(inp["input_ids"].shape[1])]))
            txt = proc.batch_decode(ids[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0]
            return empty_rows.split(txt)[0] if empty_rows.search(txt) else txt
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            return "[OOM]"

    for p, d, c in jobs:
        t0 = time.time()
        (d / "reads").mkdir(exist_ok=True)
        base = Image.open(d / "crops" / f"{c['id']}.png")
        rot = c.get("rotation")
        probe = None
        if c["big"] and rot is None and triage:
            sc = {}
            for r in (0, -90):
                im = base.rotate(r, expand=True) if r else base
                sc[r] = digit_score(ask(pilot.enhance(im) if False else im, PROBE_TOKENS))
            rot = max(sc, key=sc.get)
            probe = {str(k): v for k, v in sc.items()}
            cs = json.loads((d / "crops.json").read_text(encoding="utf-8"))
            for x in cs:
                if x["id"] == c["id"]:
                    x["rotation"], x["rotation_probe"] = rot, probe
            (d / "crops.json").write_text(json.dumps(cs, ensure_ascii=False, indent=1), encoding="utf-8")
        im = base.rotate(rot or 0, expand=True) if rot else base
        text = ask(pilot.enhance(im), TRIAGE_TOKENS if triage else 1800)
        (d / "reads" / f"{c['id']}__{a.model}.json").write_text(json.dumps({"vol": a.vol, "page": p, "crop": c["id"], "model": repo, "rotation": rot or 0, "probe": probe, "sec": round(time.time() - t0, 1), "text": text}, ensure_ascii=False), encoding="utf-8")
        print("read", a.model, a.vol, p, c["id"], "rot", rot, round(time.time() - t0, 1), "s", flush=True)


def cmd_indra(a) -> None:
    """รันด้วย indra_env (CPU): อ่านภาพย่อยที่ผ่านการคัดกรอง ลองสองทิศ (0 / -90) แล้วเลือกทิศที่ได้ทศนิยมมากกว่า — แหล่งที่สามเทียบกับตัวอ่านภาพ"""
    import cv2
    import indra_ocr
    conv = indra_ocr.load(threads=4)
    n = 0
    for p in needs_visual_pages(a.vol):
        d = pdir(a.vol, p)
        if not (d / "crops.json").exists():
            continue
        for c in json.loads((d / "crops.json").read_text(encoding="utf-8")):
            out = d / "reads" / f"{c['id']}__indra.json"
            if c["skip_reason"] or out.exists():
                continue
            (d / "reads").mkdir(exist_ok=True)
            img = cv2.imread(str(d / "crops" / f"{c['id']}.png"))
            best = None
            for rot, code in ((0, None), (-90, cv2.ROTATE_90_CLOCKWISE)):
                im = img if code is None else cv2.rotate(img, code)
                page = conv.ocr(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY))
                sc = len(re.findall(r"\d+\.\d+|\d{3,}", pilot.norm(page.text)))
                if best is None or sc > best[0]:
                    best = (sc, rot, page.text, len(page.lines))
            out.write_text(json.dumps({"vol": a.vol, "page": p, "crop": c["id"], "model": "datalab-to/indra-ocr", "rotation": best[1], "decimals": best[0], "lines": best[3], "text": best[2]}, ensure_ascii=False), encoding="utf-8")
            if c["big"] and c.get("rotation") is None:        # ทิศหมุนของบล็อกใหญ่ให้ตัวอ่านภาพใช้ต่อ (แทนการลองด้วยโมเดลภาพ)
                cs = json.loads((d / "crops.json").read_text(encoding="utf-8"))
                for x in cs:
                    if x["id"] == c["id"]:
                        x["rotation"], x["rotation_source"] = best[1], "indra"
                (d / "crops.json").write_text(json.dumps(cs, ensure_ascii=False, indent=1), encoding="utf-8")
            n += 1
    print("indra", a.vol, n, "ภาพย่อย")


def numbers_of(text: str) -> set[float]:
    out = set()
    for t in re.findall(r"(?<![\d+])-?\d+(?:[.,]\d+)*(?![\d+])", re.sub(r"\d+\+\d+", "", pilot.norm(text))):
        try:
            out.add(float(t.replace(",", "")))
        except ValueError:
            pass
    return out


def cmd_report(_a) -> None:
    summ = {"note": "ผลทั้งหมดเป็นร่าง — เทียบตัวเลขกับข้อความรายงานก่อนใช้", "volumes": {}}
    for vol in VOLS:
        pages = needs_visual_pages(vol)
        row = {"needs_visual_pages": len(pages), "layout_done": 0, "crops": 0, "crops_skipped_colorful": 0, "read_main": 0, "read_second": 0, "read_indra": 0, "pairs": 0, "mean_agreement": None, "pairs_main_indra": 0, "mean_agreement_main_indra": None, "crops_with_2plus_readers": 0, "tier_high": 0, "tier_low": 0}
        agree, agree_i = [], []
        for p in pages:
            d = V2 / vol / f"p{p:04d}"
            if (d / "layout.json").exists():
                row["layout_done"] += 1
            if not (d / "crops.json").exists():
                continue
            for c in json.loads((d / "crops.json").read_text(encoding="utf-8")):
                row["crops"] += 1
                if c["skip_reason"]:
                    row["crops_skipped_colorful"] += 1
                    continue
                fa, fb = d / "reads" / f"{c['id']}__{READ_MAIN}.json", d / "reads" / f"{c['id']}__{READ_SECOND}.json"
                ta = json.loads(fa.read_text(encoding="utf-8"))["text"] if fa.exists() else None
                tb = json.loads(fb.read_text(encoding="utf-8"))["text"] if fb.exists() else None
                fi = d / "reads" / f"{c['id']}__indra.json"
                ti = json.loads(fi.read_text(encoding="utf-8"))["text"] if fi.exists() else None
                row["read_main"] += ta is not None
                row["read_second"] += tb is not None
                row["read_indra"] += ti is not None
                sets = [numbers_of(x) for x in (ta, tb, ti) if x]
                if len(sets) >= 2:                      # ฉันทามติ: ตัวเลขที่ปรากฏในตัวอ่านอย่างน้อย 2 ตัว · ขัดแย้ง: ปรากฏในตัวเดียว
                    allv = set().union(*sets)
                    cons = {v for v in allv if sum(v in s for s in sets) >= 2}
                    if len(cons) + len(allv - cons) >= 5:
                        row["crops_with_2plus_readers"] += 1
                        row["tier_high" if len(cons) >= 5 and (len(allv) - len(cons)) <= 0.25 * len(allv) else "tier_low"] += 1
                if ta and ti:
                    na, ni = numbers_of(ta), numbers_of(ti)
                    if na | ni:
                        agree_i.append(len(na & ni) / len(na | ni))
                        row["pairs_main_indra"] += 1
                if ta and tb:
                    na, nb = numbers_of(ta), numbers_of(tb)
                    if na | nb:
                        agree.append(len(na & nb) / len(na | nb))
                        row["pairs"] += 1
        if agree:
            row["mean_agreement"] = round(sum(agree) / len(agree), 3)
        if agree_i:
            row["mean_agreement_main_indra"] = round(sum(agree_i) / len(agree_i), 3)
        summ["volumes"][vol] = row
    SUMMARY.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("pages").set_defaults(fn=cmd_pages)
    sp.add_parser("report").set_defaults(fn=cmd_report)
    for n, fn in (("layout", cmd_layout), ("crops", cmd_crops)):
        q = sp.add_parser(n)
        q.add_argument("vol", choices=list(VOLS))
        q.add_argument("--limit", type=int, default=0)
        q.set_defaults(fn=fn)
    q = sp.add_parser("indra")
    q.add_argument("vol", choices=list(VOLS))
    q.set_defaults(fn=cmd_indra)
    q = sp.add_parser("read")
    q.add_argument("model")
    q.add_argument("vol", choices=list(VOLS))
    q.add_argument("--limit", type=int, default=0)
    q.set_defaults(fn=cmd_read)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
