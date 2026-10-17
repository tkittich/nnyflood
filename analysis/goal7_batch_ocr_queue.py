"""เป้าหมาย 7 — Batch Runner คิวงานถอดความเอกสาร (Typhoon-OCR Queue บน RTX 4090)

ประมวลผลเอกสารค้างท่อ (Backlog Items) ทั้งหมดในคลังอย่างเป็นระบบด้วย 2 Workers บน GPU:
1. ph1_closing (57 หน้า): ปัจฉิมนิเทศป่าสัก-อ่าวไทย ระยะที่ 1
2. ph1_group1_draft (12 หน้า): เอกสารกลุ่มย่อย 1 ระยะที่ 1
3. ph1_group2_doc (12 หน้า): เอกสารกลุ่มย่อย 2 ระยะที่ 1
4. ph2_orientation_summary (11 หน้า): สรุปผลการประชุมปฐมนิเทศ ระยะที่ 2
5. ph2_orientation_doc (11 หน้า): เอกสารปฐมนิเทศ ระยะที่ 2
6. ph2_orientation_board (7 หน้า): บอร์ดนิทรรศการปฐมนิเทศ ระยะที่ 2
7. ph2_subgroup1_doc (6 หน้า): เอกสารกลุ่มย่อย 1 ระยะที่ 2
8. ph2_subgroup1_board (4 หน้า): บอร์ดกลุ่มย่อย 1 ระยะที่ 2
9. eia_rejection_letter (11 หน้า): หนังสือแจ้งมติไม่เห็นชอบรายงาน EIA คลองระบายน้ำหลาก
10. lowereast_group2_1520 (13 หน้า): เอกสารกลุ่มย่อย 2 เจ้าพระยาฝั่งตะวันออกตอนล่าง

รันผ่าน venv: E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_batch_ocr_queue.py [--workers 2]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis.goal7_typhoon_ocr import run_job

BACKLOG_JOBS = [
    {
        "label": "ph1_closing",
        "title": "การนำเสนอปัจฉิมนิเทศ ป่าสัก-อ่าวไทย ระยะที่ 1 (57 หน้า)",
        "pdf": ROOT / "data/manual/ป่าสัก-อ่าวไทย-ระยะที่1/นำเสนอปัจฉิมนิเทศ_29-30_05_66.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph1_group1_draft",
        "title": "ร่างเอกสารกลุ่มย่อย 1 ป่าสัก-อ่าวไทย ระยะที่ 1 (12 หน้า)",
        "pdf": ROOT / "data/manual/ป่าสัก-อ่าวไทย-ระยะที่1/ป่าสักอ่าวไทย_ร่างกลุ่มย่อย1_A4.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph1_group2_doc",
        "title": "เอกสารกลุ่มย่อย 2 ป่าสัก-อ่าวไทย ระยะที่ 1 (12 หน้า)",
        "pdf": ROOT / "data/manual/ป่าสัก-อ่าวไทย-ระยะที่1/ป่าสักอ่าวไทย_เอกสาร กลุ่มย่อย2 _A4 final.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph2_orientation_summary",
        "title": "สรุปผลการประชุมปฐมนิเทศ ป่าสัก-อ่าวไทย ระยะที่ 2 (11 หน้า)",
        "pdf": ROOT / "data/manual/ป่าสัก-อ่าวไทย-ระยะที่2/ป่าสัก-อ่าวไทย ระยะที่ 2/2. การประชุมปฐมนิเทศ (16-17-02-66)/สรปผลการประชุมปฐมนิเทศ (16-17 02 2566).pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph2_orientation_doc",
        "title": "เอกสารปฐมนิเทศ ป่าสัก-อ่าวไทย ระยะที่ 2 (11 หน้า)",
        "pdf": ROOT / "data/manual/ป่าสัก-อ่าวไทย-ระยะที่2/ป่าสัก-อ่าวไทย ระยะที่ 2/2. การประชุมปฐมนิเทศ (16-17-02-66)/เอกสารปฐมนิเทศ ป่าสัก-อ่าวไทย ระยะที่ 2.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph2_orientation_board",
        "title": "บอร์ดนิทรรศการปฐมนิเทศ ป่าสัก-อ่าวไทย ระยะที่ 2 (7 หน้า)",
        "pdf": ROOT / "data/manual/ป่าสัก-อ่าวไทย-ระยะที่2/ป่าสัก-อ่าวไทย ระยะที่ 2/2. การประชุมปฐมนิเทศ (16-17-02-66)/บอร์ด ปฐมนิเทศป่าสักอ่าวไทย ระยะที่ 2.pdf",
        "pages": None,
        "dpi": 120,
    },
    {
        "label": "ph2_subgroup1_doc",
        "title": "เอกสารกลุ่มย่อย 1 ป่าสัก-อ่าวไทย ระยะที่ 2 (6 หน้า)",
        "pdf": ROOT / "data/manual/ป่าสัก-อ่าวไทย-ระยะที่2/ป่าสัก-อ่าวไทย ระยะที่ 2/3. การประชุมกลุ่มย่อย ครั้งที่ 1/เอกสารกลุ่มย่อย 1 ป่าสัก-อ่าวไทย ระยะที่ 2.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph2_subgroup1_board",
        "title": "บอร์ดกลุ่มย่อย 1 ป่าสัก-อ่าวไทย ระยะที่ 2 (4 หน้า)",
        "pdf": ROOT / "data/manual/ป่าสัก-อ่าวไทย-ระยะที่2/ป่าสัก-อ่าวไทย ระยะที่ 2/3. การประชุมกลุ่มย่อย ครั้งที่ 1/บอร์ดกลุ่มย่อย 1 ป่าสัก-อ่าวไทย ระยะที่ 2.pdf",
        "pages": None,
        "dpi": 120,
    },
    {
        "label": "eia_rejection_letter",
        "title": "หนังสือแจ้งมติไม่เห็นชอบรายงาน EIA ทางระบายน้ำหลาก (11 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/EIA/1. แจ้งมติไม่เห็นชอบ EIA ทางระบายน้ำหลาก.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "lowereast_group2_1520",
        "title": "เอกสารกลุ่มย่อย 2 ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง (13 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/1520group2.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph2_public_board2",
        "title": "บอร์ดนิทรรศการรับฟังความคิดเห็นสาธารณะ ครั้งที่ 2 (7 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/การประชุมรับฟังความคิดเห็นสาธารณะ ครั้งที่ 2/board-2.pdf",
        "pages": None,
        "dpi": 120,
    },
    {
        "label": "ph2_public_doc2",
        "title": "เอกสารรับฟังความคิดเห็นสาธารณะ ครั้งที่ 2 (21 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/การประชุมรับฟังความคิดเห็นสาธารณะ ครั้งที่ 2/document-2.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph1_public_brochure1",
        "title": "แผ่นพับประชาสัมพันธ์รับฟังความคิดเห็นสาธารณะ ครั้งที่ 1 (4 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/การประชุมรับฟังความคิดเห็นสาธารณะ ครั้งที่ 1/brochure-1.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph1_group1_floodway",
        "title": "เอกสารกลุ่มย่อย 1 ทางระบายน้ำหลาก (2 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/การประชุมกลุ่มย่อย ครั้งที่ 1 (ทางระบายน้ำหลาก)/group1.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph1_news1",
        "title": "จดหมายข่าวกลุ่มย่อย 1 ปรับปรุงระบบชลประทาน (2 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/การประชุมกลุ่มย่อย ครั้งที่ 1 (ปรับปรุงระบบชลประทาน)/news-1.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "ph1_news2",
        "title": "จดหมายข่าวกลุ่มย่อย 1 ทางระบายน้ำหลาก (2 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/การประชุมกลุ่มย่อย ครั้งที่ 1 (ทางระบายน้ำหลาก)/news-2.pdf",
        "pages": None,
        "dpi": 150,
    },
    {
        "label": "knowledge_exchange_93p",
        "title": "เอกสารแลกเปลี่ยนเรียนรู้การบริหารจัดการน้ำ (93 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/แลกเปลี่ยนเรียนรู้.pdf",
        "pages": None,
        "dpi": 140,
    },
    {
        "label": "eia_clarify2_att1",
        "title": "เอกสารแนบ EIA ชี้แจงครั้งที่ 2 เล่ม 1-2 (542 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/EIA/EIA โครงการทางระบายน้ำหลากเจ้าพระยาฝั่งตะวันออกตอนล่าง ของกรมชลประทาน/รายงานชี้แจงเพิ่มเติมครั้งที่ 2/2. เอกสารแนบ (เล่ม 1-2).pdf",
        "pages": None,
        "dpi": 140,
    },
    {
        "label": "eia_clarify2_att2",
        "title": "เอกสารแนบ EIA ชี้แจงครั้งที่ 2 เล่ม 2-2 (689 หน้า)",
        "pdf": ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/EIA/EIA โครงการทางระบายน้ำหลากเจ้าพระยาฝั่งตะวันออกตอนล่าง ของกรมชลประทาน/รายงานชี้แจงเพิ่มเติมครั้งที่ 2/3. เอกสารแนบ (เล่ม 2-2).pdf",
        "pages": None,
        "dpi": 140,
    },
]


def update_search_index():
    """เรียก tools/mini_fts.py เพื่อปรับปรุงดัชนีการค้นหาแบบเต็ม"""
    try:
        from tools.mini_fts import index_all
        cnt = index_all(verbose=True)
        print(f"🔄 ปรับปรุงดัชนี Mini-FTS เรียบร้อย ({cnt} รายการ)", flush=True)
    except Exception as e:
        print(f"⚠️ ไม่สามารถอัปเดตดัชนี FTS อัตโนมัติ: {e}", flush=True)


def process_queue(workers: int = 2, selected_labels: list[str] | None = None):
    print("=" * 70, flush=True)
    print(f"🚀 เริ่มคิวงานประมวลผล Typhoon-OCR บน NVIDIA GeForce RTX 4090 ({workers} Workers)", flush=True)
    print("=" * 70, flush=True)

    t_total_start = time.time()
    completed_jobs = 0

    for idx, job in enumerate(BACKLOG_JOBS, 1):
        label = job["label"]
        if selected_labels and label not in selected_labels:
            continue

        pdf_path = job["pdf"]
        title = job["title"]
        dpi = job.get("dpi", 150)
        pages = job.get("pages")

        print(f"\n[{idx}/{len(BACKLOG_JOBS)}] กำลังประมวลผล: {title}", flush=True)
        print(f"  พาธ: {pdf_path.relative_to(ROOT)}", flush=True)
        print(f"  โฟลเดอร์ผลลัพธ์: data/32_goal7_chaophraya2/typhoon_ocr/{label}", flush=True)

        t_job_start = time.time()
        try:
            run_job(
                pdf_path=pdf_path,
                label=label,
                pages=pages,
                dpi=dpi,
                workers=workers,
            )
            elapsed_min = (time.time() - t_job_start) / 60.0
            print(f"✅ สำเร็จงาน [{label}] ในเวลา {elapsed_min:.2f} นาที", flush=True)
            completed_jobs += 1

            # ปรับปรุงดัชนี FTS เพื่อให้ค้นหาได้ทันที
            update_search_index()

        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดในงาน [{label}]: {e}", flush=True)

    total_min = (time.time() - t_total_start) / 60.0
    print("\n" + "=" * 70, flush=True)
    print(f"🎉 คิวงานทั้งหมดเสร็จสิ้น: สำเร็จ {completed_jobs} งาน (รวมเวลา {total_min:.2f} นาที)", flush=True)
    print("=" * 70, flush=True)


def main():
    import multiprocessing
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="เป้าหมาย 7 — Batch Runner คิวงานถอดความเอกสารด้วย Typhoon-OCR")
    parser.add_argument("--workers", type=int, default=2, help="จำนวน Workers คู่ขนาน (ค่าเริ่มต้น 2 สำหรับ RTX 4090)")
    parser.add_argument("--labels", help="ระบุฉลากงานที่ต้องการทำ คั่นด้วยจุลภาค (เช่น ph1_closing,eia_rejection_letter)")

    args = parser.parse_args()
    selected_labels = [s.strip() for s in args.labels.split(",")] if args.labels else None

    process_queue(workers=args.workers, selected_labels=selected_labels)


if __name__ == "__main__":
    main()
