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


def ocr_page(doc, page_num: int, processor, model, device: str = "cuda:0", dpi: int = 150) -> str:
    from PIL import Image
    import torch

    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": "Extract text in markdown format."},
            ],
        }
    ]

    inputs = processor.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=4096,
            repetition_penalty=1.1,
            do_sample=False
        )

    output_text = processor.batch_decode(
        [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)],
        skip_special_tokens=True,
    )
    return output_text[0].strip()


def worker_task(pdf_path_str: str, label: str, worker_id: int, task_queue, dpi: int, target_dir_str: str):
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
            md_text = ocr_page(doc, p, processor, model, dpi=dpi)
            rec = {
                "page": p,
                "text": md_text,
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


def run_job(pdf_path: str | Path, label: str, pages: list[int] | None = None, dpi: int = 150, workers: int = 1):
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
                    done_pages.add(json.loads(line)["page"])
                except Exception:
                    pass

    # ตรวจสอบ part files ที่อาจยังไม่ได้รวม
    for pf in target_dir.glob("pages_part_*.jsonl"):
        for line in pf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    done_pages.add(json.loads(line)["page"])
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
        worker_task(str(pdf_path), label, 0, q, dpi, str(target_dir))
    else:
        # รันกระบวนการคู่ขนานแบบคิวงานอิสระ
        processes = []
        for wid in range(workers):
            p = multiprocessing.Process(
                target=worker_task,
                args=(str(pdf_path), label, wid + 1, q, dpi, str(target_dir))
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


def main():
    import multiprocessing
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="เป้าหมาย 7 — Local Typhoon-OCR บน RTX 4090")
    parser.add_argument("--pdf", required=True, help="พาธไฟล์ PDF")
    parser.add_argument("--label", required=True, help="ชื่อกลุ่มเอกสาร (เช่น letter54_measures)")
    parser.add_argument("--pages", help="หน้าที่ต้องการแปลง (เช่น 1,2,3 หรือ 1-10)")
    parser.add_argument("--dpi", type=int, default=150, help="DPI สำหรับแปลงหน้าภาพ (ค่าเริ่มต้น 150)")
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

    run_job(args.pdf, args.label, pages=pages, dpi=args.dpi, workers=args.workers)


if __name__ == "__main__":
    main()

