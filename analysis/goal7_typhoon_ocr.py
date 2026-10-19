"""เป้าหมาย 7 — Local Typhoon-OCR บน NVIDIA GeForce RTX 4090 สำหรับเอกสาร EIA 2569

ใช้โมเดล Vision-Language: scb10x/typhoon-ocr1.5-2b (สถาปัตยกรรม Qwen-VL)
แก้ปัญหาสระ วรรณยุกต์ และคงรูปตาราง Markdown 100%
รันผ่าน venv ภายนอก: E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_typhoon_ocr.py [args]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data/32_goal7_chaophraya2/typhoon_ocr"


def init_engine(model_id: str = "scb10x/typhoon-ocr1.5-2b", device: str = "cuda:0"):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    print(f"กำลังโหลดโมเดล {model_id} บนอุปกรณ์ {device} (VRAM: {round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2)} GB)...", flush=True)
    t0 = time.time()
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        dtype=torch.bfloat16,
        device_map=device
    )
    print(f"โหลดโมเดลสำเร็จใน {time.time() - t0:.2f} วินาที", flush=True)
    return processor, model


SHORT_PROMPT = "Extract text in markdown format."
_GEN_STATE: dict = {"truncated": False}   # ตัวแปรต่อกระบวนการ: รอบล่าสุดถูกตัดด้วยเวลา/ความยาวหรือไม่ (ใช้บันทึกใน meta)
MAX_TIME_S = {"scan": 70.0, "figure": 45.0, "text": 70.0}   # เพดานเวลาต่อหน้า (วินาที) — หน้าตารางหนาแน่นเคยวนซ้ำจน 184 วินาที/หน้า
ECHO_MARKERS = ("RAW_TEXT_START", "Below is an image of a document page", "Your task is to return the markdown representation")
THAI_RX = __import__("re").compile(r"[฀-๿]")


def is_echo(text: str) -> bool:
    """โมเดลบางหน้าสะท้อนแม่แบบคำสั่งกลับแทนการถอดความ (เจอ 23% ของ eia_clarify2_att1) — ถือว่าล้มเหลว"""
    return any(m in (text or "") for m in ECHO_MARKERS)


def _official_prompt(page, w: float, h: float) -> str:
    raw = (page.get_text() or "").strip()[:3000]
    parts = [
        "Below is an image of a document page, along with its dimensions and possibly some raw textual content previously extracted from it. "
        "Note that the text extraction may be incomplete or partially missing. Carefully consider both the layout and any available text to reconstruct the document accurately.",
        "Your task is to return the markdown representation of this document, presenting tables in HTML format as they naturally appear.",
        "If the document contains images or figures, analyze them and include the tag <figure>IMAGE_ANALYSIS</figure> in the appropriate location.",
        "Your final output must be in JSON format with a single key `natural_text` containing the response.",
        "RAW_TEXT_START",
        f"Page dimensions: {w:.1f}x{h:.1f}",
        raw,
        "RAW_TEXT_END",
    ]
    return "\n".join(parts)


def _generate(img, prompt: str, processor, model, device: str, max_new_tokens: int = 4096, max_time: float | None = None) -> str:
    import torch

    messages = [{"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": prompt}]}]
    inputs = processor.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt"
    ).to(device)
    _t0 = __import__("time").time()
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens, max_time=max_time, repetition_penalty=1.1, do_sample=False)
    _GEN_STATE["truncated"] = bool(max_time and (__import__("time").time() - _t0) >= 0.97 * max_time) or (generated_ids.shape[1] - inputs.input_ids.shape[1]) >= max_new_tokens
    out = processor.batch_decode([o[len(i):] for i, o in zip(inputs.input_ids, generated_ids)], skip_special_tokens=True)[0].strip()
    if out.startswith("{") and "natural_text" in out[:40]:
        try:
            out = json.loads(out)["natural_text"]
        except Exception:
            pass
    return out


def _render(doc, page_num: int, dpi: int, rotate: int = 0):
    from PIL import Image

    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if rotate:
        img = img.rotate(-rotate, expand=True)   # rotate=90 = หมุนตามเข็มนาฬิกา 90°
    return page, img


def ocr_page(doc, page_num: int, processor, model, device: str = "cuda:0", dpi: int = 150) -> str:
    """ถอดความหน้าเดียวแบบเดิม (คำสั่งสั้น มุมเดิม) — คงไว้เพื่อความเข้ากันได้"""
    _, img = _render(doc, page_num, dpi)
    return _generate(img, SHORT_PROMPT, processor, model, device)


def classify_page(page) -> str:
    """จัดชนิดหน้า: 'scan' = หน้าสแกน/ภาพล้วน (แทบไม่มีข้อความในไฟล์ + ภาพใหญ่) · 'figure' = หน้ามีข้อความแต่มีภาพ/รูป/ตารางที่เป็นภาพขนาดใหญ่ · 'text' = ข้อความล้วน"""
    area = page.rect.width * page.rect.height
    frac = 0.0
    for im in page.get_images(full=True):
        for r in page.get_image_rects(im[0]):
            frac += (r.width * r.height) / area
    frac = min(frac, 1.0)
    n_text = len((page.get_text() or "").strip())
    if n_text < 80 and frac > 0.3:
        return "scan"
    if n_text >= 80 and frac > 0.25:
        return "figure"
    return "text"


def ocr_page_robust(doc, page_num: int, processor, model, device: str = "cuda:0", dpi: int = 150, kind: str = "auto") -> tuple[str, dict]:
    """ถอดความแบบทนความล้มเหลว (รอบ 6) — ทดสอบ 19 ต.ค. 69 กับรูปที่ 2.3.2-11 หน้า 144:
    · คำสั่งสั้นให้ผลดีกับหน้าสแกนที่เป็นข้อความ แต่หน้ารูป/แบบวิศวกรรมมักสะท้อนแม่แบบคำสั่งกลับ (echo)
    · แม่แบบคำสั่งทางการแก้ echo ได้ แต่ **แต่งข้อมูลขึ้นเอง** บนแบบวิศวกรรม (เช่น 'ถนน123-456') และช้า ~160 วินาที/หน้า → ไม่ใช้เป็นค่าตั้งต้น
    ดังนั้น: scan = ลองมุม 0→90→270 ด้วยคำสั่งสั้น · figure = ลองครั้งเดียว จำกัดความยาว ถ้า echo ให้ทำเครื่องหมายว่า 'ต้องอ่านภาพ/ตัดตาราง' (ไม่แต่งข้อความ)
    · มีธง official=True ใน meta เมื่อใช้แม่แบบทางการ (ไม่ใช้ในคิวปกติ)"""
    page = doc[page_num - 1]
    if kind == "auto":
        kind = classify_page(page)
    plan = [(0, "short")] if kind in ("figure", "text") else [(0, "short"), (90, "short"), (270, "short")]
    max_new = 1200 if kind == "figure" else 4096
    attempts = []
    best_text, best_score = "", -1
    for rot, prompt_kind in plan:
        _, img = _render(doc, page_num, dpi if rot == 0 else max(dpi, 170), rot)
        txt = _generate(img, SHORT_PROMPT, processor, model, device, max_new_tokens=max_new, max_time=MAX_TIME_S.get(kind, 70.0))
        truncated = _GEN_STATE["truncated"]
        echo = is_echo(txt)
        thai = len(THAI_RX.findall(txt))
        attempts.append({"rotate": rot, "prompt": prompt_kind, "echo": echo, "thai_chars": thai, "chars": len(txt), "truncated": truncated})
        score = -1 if echo else thai + len(txt) // 50
        if score > best_score:
            best_text, best_score = txt, score
        if not echo and thai >= 30:
            break
    echo_final = best_score < 0
    return ("" if echo_final else best_text), {"truncated": any(a_["truncated"] for a_ in attempts), "kind": kind, "attempts": attempts, "echo_final": echo_final, "needs_visual": echo_final or (kind == "figure"), "official": False}


def record_done(r: dict) -> bool:
    """หน้าที่ถือว่า 'ทำแล้ว': ไม่มี error และ (ผ่านตัวทนความล้มเหลวแล้ว หรือเป็นข้อความที่ไม่ใช่การสะท้อนแม่แบบ) — ผลเก่าที่ echo จะถูกทำใหม่"""
    if r.get("error"):
        return False
    if (r.get("meta") or {}).get("needs_visual") is not None:
        return True
    txt = r.get("text") or ""
    return bool(txt) and not is_echo(txt)


def worker_task(pdf_path_str: str, label: str, worker_id: int, task_queue, dpi: int, target_dir_str: str, kind: str = "auto"):
    import pymupdf
    import time
    import json
    from pathlib import Path

    target_dir = Path(target_dir_str)
    doc = pymupdf.open(pdf_path_str)
    total_pages = len(doc)
    processor, model = init_engine()
    out_file = target_dir / f"pages_part_{worker_id}.jsonl"

    while True:
        try:
            p = task_queue.get_nowait()
        except Exception:
            break

        t0 = time.time()
        try:
            md_text, meta = ocr_page_robust(doc, p, processor, model, dpi=dpi, kind=kind)
            rec = {
                "page": p,
                "text": md_text,
                "meta": meta,
                "sec": round(time.time() - t0, 2),
                "worker": worker_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            rec = {
                "page": p,
                "error": str(e)[:300],
                "sec": round(time.time() - t0, 2),
                "worker": worker_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        with out_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
        print(f"  [Worker {worker_id} | {label}] หน้า {p}/{total_pages} เสร็จใน {rec['sec']} วินาที", flush=True)


def run_job(pdf_path: str | Path, label: str, pages: list[int] | None = None, dpi: int = 150, workers: int = 1, kind: str = "auto"):
    import multiprocessing
    import pymupdf

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"ไม่พบไฟล์ PDF: {pdf_path}")

    target_dir = OUT_DIR / label
    target_dir.mkdir(parents=True, exist_ok=True)
    jl_path = target_dir / "pages.jsonl"

    done_pages = set()
    if jl_path.exists():
        for line in jl_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    _r = json.loads(line)
                    if record_done(_r):
                        done_pages.add(_r["page"])
                except Exception:
                    pass

    # ตรวจสอบ part files ที่อาจยังไม่ได้รวม
    for pf in target_dir.glob("pages_part_*.jsonl"):
        for line in pf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    _r = json.loads(line)
                    if record_done(_r):
                        done_pages.add(_r["page"])
                except Exception:
                    pass

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    page_list = pages if pages else list(range(1, total_pages + 1))
    todo = [p for p in page_list if p not in done_pages]

    print(f"[{label}] ทั้งหมด {len(page_list)} หน้า | ทำแล้ว {len(done_pages)} หน้า | เหลือ {len(todo)} หน้า (กำลังรัน {workers} workers)", flush=True)
    if not todo:
        print(f"[{label}] ทำเสร็จครบทุกหน้าแล้ว ข้าม", flush=True)
        return

    t_start = time.time()

    # คิวงานแบบไดนามิก: Worker ที่เสร็จก่อนจะดึงหน้าถัดไปทันที (Work Stealing)
    q = multiprocessing.Queue()
    for p in todo:
        q.put(p)

    if workers <= 1 or len(todo) == 1:
        # รันกระบวนการเดี่ยว
        worker_task(str(pdf_path), label, 0, q, dpi, str(target_dir), kind)
    else:
        # รันกระบวนการคู่ขนานแบบคิวงานอิสระ
        processes = []
        for wid in range(workers):
            p = multiprocessing.Process(
                target=worker_task,
                args=(str(pdf_path), label, wid + 1, q, dpi, str(target_dir), kind)
            )
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

    # รวมไฟล์ part ทั้งหมดเข้าสู่ pages.jsonl
    all_recs_dict = {}
    if jl_path.exists():
        for line in jl_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                all_recs_dict[r["page"]] = r

    for pf in list(target_dir.glob("pages_part_*.jsonl")):
        for line in pf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                all_recs_dict[r["page"]] = r
        try:
            pf.unlink()  # ลบไฟล์ part ชั่วคราวหลังรวมเสร็จ
        except Exception:
            pass

    sorted_recs = sorted(all_recs_dict.values(), key=lambda x: x["page"])
    with jl_path.open("w", encoding="utf-8") as f:
        for r in sorted_recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # รวมเป็นเอกสาร Markdown ฉบับสมบูรณ์
    md_full = [f"# {label} — เอกสารถอดความด้วย Typhoon-OCR บน RTX 4090\n"]
    for r in sorted_recs:
        p = r["page"]
        txt = r.get("text", "")
        md_full.append(f"\n<!-- Page {p} -->\n## หน้าที่ {p}\n\n{txt}\n\n---")

    (target_dir / "document.md").write_text("\n".join(md_full), encoding="utf-8")
    print(f"[{label}] รวมเป็น {target_dir / 'document.md'} เรียบร้อย (รวมเวลา {(time.time() - t_start)/60:.1f} นาที)", flush=True)


def pending_pages(label: str, page_list: list[int]) -> list[int]:
    """หน้าที่ยังไม่ถือว่าทำแล้ว (ดู record_done) ของป้ายเอกสารนั้น — อ่านทั้ง pages.jsonl และไฟล์ part ที่ยังไม่รวม"""
    target_dir = OUT_DIR / label
    done: set[int] = set()
    for jl in [target_dir / "pages.jsonl", *target_dir.glob("pages_part_*.jsonl")]:
        if jl.exists():
            for line in jl.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        r = json.loads(line)
                        if record_done(r):
                            done.add(r["page"])
                    except Exception:
                        pass
    return [p for p in page_list if p not in done]


def finalize_label(label: str) -> None:
    """รวมไฟล์ part ของป้ายเอกสารเข้า pages.jsonl และสร้าง document.md (ใช้ซ้ำได้ ไม่เสียหายถ้าเรียกหลายรอบ)"""
    target_dir = OUT_DIR / label
    jl_path = target_dir / "pages.jsonl"
    recs: dict[int, dict] = {}
    for src in [jl_path, *sorted(target_dir.glob("pages_part_*.jsonl"))]:
        if src.exists():
            for line in src.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    recs[r["page"]] = r
    if not recs:
        return
    for pf in list(target_dir.glob("pages_part_*.jsonl")):
        try:
            pf.unlink()
        except Exception:
            pass
    ordered = sorted(recs.values(), key=lambda x: x["page"])
    with jl_path.open("w", encoding="utf-8") as f:
        for r in ordered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    md_full = [f"# {label} — เอกสารถอดความด้วย Typhoon-OCR บน RTX 4090\n"]
    for r in ordered:
        md_full.append(f"\n<!-- Page {r['page']} -->\n## หน้าที่ {r['page']}\n\n{r.get('text', '')}\n\n---")
    (target_dir / "document.md").write_text("\n".join(md_full), encoding="utf-8")


def global_worker(worker_id: int, task_queue, dpi: int = 150) -> None:
    """worker ถาวรหนึ่งตัว: โหลดโมเดลครั้งเดียว แล้วดึงงาน (pdf, label, page, kind) จากคิวรวมทุกเอกสาร จนคิวว่าง
    ไม่มีจุดรอให้อีก worker หรืองานอื่นเสร็จก่อน (ผู้ใช้ 19 ต.ค. 69: 2 งานอิสระต้องไม่รอกัน)"""
    import pymupdf

    processor, model = init_engine()
    docs: dict[str, object] = {}
    while True:
        try:
            task = task_queue.get_nowait()
        except Exception:
            break
        pdf, label, page, kind = task["pdf"], task["label"], task["page"], task["kind"]
        t0 = time.time()
        try:
            doc = docs.get(pdf) or docs.setdefault(pdf, pymupdf.open(pdf))
            text, meta = ocr_page_robust(doc, page, processor, model, dpi=dpi, kind=kind)
            rec = {"page": page, "text": text, "meta": meta, "sec": round(time.time() - t0, 2), "worker": worker_id, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
        except Exception as e:  # noqa: BLE001
            rec = {"page": page, "error": str(e)[:300], "sec": round(time.time() - t0, 2), "worker": worker_id, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
        d = OUT_DIR / label
        d.mkdir(parents=True, exist_ok=True)
        with (d / f"pages_part_{worker_id}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
        print(f"  [W{worker_id} | {label}] หน้า {page} ({kind}) เสร็จใน {rec['sec']} วินาที", flush=True)


def run_global_queue(tasks: list[dict], workers: int = 2, dpi: int = 150) -> None:
    """คิวรวม: tasks เรียงตามความสำคัญ · worker ดึงจากหัวคิวอิสระต่อกัน · รวมผลทุกป้ายเอกสารตอนจบ"""
    import multiprocessing

    q = multiprocessing.Queue()
    for tk in tasks:
        q.put(tk)
    labels = sorted({tk["label"] for tk in tasks})
    print(f"คิวรวม {len(tasks)} หน้า ใน {len(labels)} เอกสาร · {workers} worker", flush=True)
    procs = [multiprocessing.Process(target=global_worker, args=(w + 1, q, dpi)) for w in range(workers)]
    for pr in procs:
        pr.start()
    for pr in procs:
        pr.join()
    for lb in labels:
        finalize_label(lb)
    print("รวมผลเสร็จทุกเอกสาร", flush=True)


def main():
    import multiprocessing
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="เป้าหมาย 7 — Local Typhoon-OCR บน RTX 4090")
    parser.add_argument("--pdf", required=True, help="พาธไฟล์ PDF")
    parser.add_argument("--label", required=True, help="ชื่อกลุ่มเอกสาร (เช่น letter54_measures)")
    parser.add_argument("--pages", help="หน้าที่ต้องการแปลง (เช่น 1,2,3 หรือ 1-10)")
    parser.add_argument("--dpi", type=int, default=150, help="DPI สำหรับแปลงหน้าภาพ (ค่าเริ่มต้น 150)")
    parser.add_argument("--kind", default="auto", choices=["auto", "scan", "figure", "text"], help="ชนิดหน้า (auto = จัดอัตโนมัติรายหน้า)")
    parser.add_argument("--workers", type=int, default=1, help="จำนวน worker ทำงานขนานบน GPU (เช่น 2)")

    args = parser.parse_args()

    pages = None
    if args.pages:
        pages = []
        for part in args.pages.split(","):
            if "-" in part:
                s, e = part.split("-")
                pages.extend(range(int(s), int(e) + 1))
            else:
                pages.append(int(part))

    run_job(args.pdf, args.label, pages=pages, dpi=args.dpi, workers=args.workers, kind=args.kind)


if __name__ == "__main__":
    main()

