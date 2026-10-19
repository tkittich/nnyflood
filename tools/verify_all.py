#!/usr/bin/env python3
"""tools/verify_all.py — ตัวตรวจความถูกต้องแบบครบวงจรของโปรเจกต์ nnyflood (Unified System Verification)

การทำงาน:
    รันชุดการตรวจสอบความถูกต้อง 4 ขั้นตอน:
    1. สารบัญระบบ (catalog.py check) — ตรวจไฟล์/โฟลเดอร์ในสเปก
    2. ความสมบูรณ์ของข้อมูล (verify_data_integrity.py --quick) — ตรวจ SHA-256 ของไฟล์ข้อมูล
    3. ภาษาไทย มาตรฐานเอกสาร และความสอดคล้องของข้อมูล (pytest test_standards_integrity + test_thai_language_lint + test_data_consistency)
    4. ชุดทดสอบระบบทั้งหมด (pytest tests/ -q)

การใช้งาน:
    python tools/verify_all.py          # ตรวจครบ 4 ขั้นตอน
    python tools/verify_all.py --quick  # ตรวจเฉพาะขั้นตอน 1-3
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# คำเตือนของขั้นตอนที่ "ผ่านแบบมีเงื่อนไข" (รหัสออกที่อนุญาตแต่ไม่ใช่ 0) — รวบไว้สรุปท้ายการตรวจ
WARNINGS: list[str] = []


def step_verdict(returncode: int, allow_exit_codes: tuple[int, ...] = (0,)) -> tuple[bool, str | None]:
    """ตัดสินผลของขั้นตอน: คืน (ผ่านหรือไม่, ข้อความเตือนเมื่อผ่านแบบมีเงื่อนไข).

    - รหัส 0 = ผ่านสมบูรณ์
    - รหัสที่อนุญาตแต่ไม่ใช่ 0 = ผ่านแบบมีเงื่อนไข — ต้องมีคำเตือนเสมอ
      (เช่นรหัส 2 ของการตรวจ SHA-256 = ไฟล์ข้อมูลขนาดใหญ่บางส่วนหาย/ไม่พร้อมในเครื่อง)
    - รหัสนอกเหนือรายการที่อนุญาต = ไม่ผ่าน
    """
    if returncode not in allow_exit_codes:
        return False, None
    if returncode != 0:
        return True, f"ผ่านแบบมีเงื่อนไข (รหัสออก {returncode}) — มีบางส่วนไม่ครบถ้วน โปรดตรวจรายละเอียดของขั้นตอนนี้"
    return True, None


def run_step(step_num: int, total_steps: int, title: str, cmd: list[str], allow_exit_codes: tuple[int, ...] = (0,)) -> bool:
    print(f"[{step_num}/{total_steps}] 🔍 {title}...")
    start = time.perf_counter()
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.perf_counter() - start

    ok, warning = step_verdict(res.returncode, allow_exit_codes)
    if ok and warning is None:
        print(f"    ✅ ผ่าน ({elapsed:.2f} วินาที)")
        return True
    if ok and warning is not None:
        WARNINGS.append(f"{title} — {warning}")
        print(f"    ⚠️  {warning} ({elapsed:.2f} วินาที)")
        tail = [ln for ln in res.stdout.strip().splitlines() if ln.strip()][-8:] if res.stdout else []
        for ln in tail:
            print(f"        {ln}")
        return True
    print(f"    ❌ ไม่ผ่าน (Exit Code: {res.returncode}, {elapsed:.2f} วินาที)")
    if res.stdout:
        print("--- STDOUT ---")
        print(res.stdout.strip())
    if res.stderr:
        print("--- STDERR ---")
        print(res.stderr.strip())
    return False


def main():
    parser = argparse.ArgumentParser(description="Unified System Verification for nnyflood")
    parser.add_argument("--quick", action="store_true", help="รันเฉพาะการตรวจสารบัญและความสมบูรณ์เบื้องต้น")
    args = parser.parse_args()

    print("=" * 72)
    print("  nnyflood — เครื่องมือตรวจความสมบูรณ์และมาตรฐานแบบครบวงจร")
    print("=" * 72)

    total_steps = 4 if args.quick else 5
    success = True

    # ขั้นตอนที่ 1: ตรวจสารบัญ catalog.py
    step1 = run_step(
        1, total_steps,
        "ตรวจสอบความมีอยู่จริงของไฟล์ในสารบัญ (catalog.py check)",
        [sys.executable, "catalog.py", "check"]
    )
    if not step1:
        success = False

    # ขั้นตอนที่ 2: ตรวจ integrity ของไฟล์ข้อมูลดิบ (รหัส 0 = ครบสมบูรณ์ · รหัส 2 = ไฟล์ขนาดใหญ่บางส่วนหาย — ผ่านแบบมีเงื่อนไขพร้อมคำเตือน)
    step2 = run_step(
        2, total_steps,
        "ตรวจสอบ SHA-256 ข้อมูลดิบ (verify_data_integrity.py --quick)",
        [sys.executable, "analysis/verify_data_integrity.py", "--quick"],
        allow_exit_codes=(0, 2)
    )
    if not step2:
        success = False

    # ขั้นตอนที่ 3: ทะเบียนเครื่องมือ/สภาพแวดล้อม (รหัส 2 = คำเตือน เช่น สคริปต์ยังไม่ลงทะเบียน — ไม่ทำให้ล้ม)
    step_doc = run_step(
        3, total_steps,
        "ตรวจทะเบียนเครื่องมือและสภาพแวดล้อม (tools/doctor.py)",
        [sys.executable, "tools/doctor.py"],
        allow_exit_codes=(0, 2)
    )
    if not step_doc:
        success = False

    # ขั้นตอนที่ 4: ตรวจสอบมาตรฐานเอกสาร ภาษาไทย และความสอดคล้องของข้อมูล
    step3 = run_step(
        4, total_steps,
        "ตรวจสอบมาตรฐานเอกสาร ภาษาไทย และสัญญาความสอดคล้องของข้อมูล (pytest lint & consistency)",
        [sys.executable, "-m", "pytest", "tests/test_standards_integrity.py", "tests/test_thai_language_lint.py", "tests/test_data_consistency.py", "-q"]
    )
    if not step3:
        success = False

    # ขั้นตอนที่ 4: ตรวจสอบชุดทดสอบทั้งหมด
    if not args.quick:
        step4 = run_step(
            5, total_steps,
            "รันชุดทดสอบระบบทั้งหมด (pytest tests/)",
            [sys.executable, "-m", "pytest", "tests/", "-q"]
        )
        if not step4:
            success = False

    print("=" * 72)
    if success:
        if WARNINGS:
            print("🟡 ระบบผ่านการตรวจสอบแบบมีเงื่อนไข (ไม่ใช่ 100%)")
            print(f"⚠️  หมายเหตุ: มี {len(WARNINGS)} ขั้นตอนที่ผ่านแบบมีเงื่อนไข (มีบางส่วนไม่ครบ เช่น ไฟล์ใหญ่นอก git) — ดูคำเตือนด้านบน")
        else:
            print("🎉 ระบบผ่านการตรวจสอบความสมบูรณ์ 100% พร้อมสำหรับการเผยแพร่และจัดเก็บ")
        print("=" * 72)
        sys.exit(0)
    else:
        print("⚠️ พบข้อผิดพลาดในการตรวจสอบ กรุณาแก้ไขก่อนส่งมอบงาน")
        print("=" * 72)
        sys.exit(1)


if __name__ == "__main__":
    main()
