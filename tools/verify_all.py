#!/usr/bin/env python3
"""tools/verify_all.py — ตัวตรวจความถูกต้องแบบครบวงจรของโปรเจกต์ nnyflood (Unified System Verification)

การทำงาน:
    รันชุดการตรวจสอบความถูกต้อง 4 ขั้นตอน:
    1. สารบัญระบบ (catalog.py check) — ตรวจไฟล์/โฟลเดอร์ในสเปก
    2. ความสมบูรณ์ของข้อมูล (verify_data_integrity.py --quick) — ตรวจ SHA-256 ของไฟล์ข้อมูล
    3. ภาษาไทยและมาตรฐานเอกสาร (pytest test_standards_integrity + test_thai_language_lint)
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


def run_step(step_num: int, total_steps: int, title: str, cmd: list[str], allow_exit_codes: tuple[int, ...] = (0,)) -> bool:
    print(f"[{step_num}/{total_steps}] 🔍 {title}...")
    start = time.perf_counter()
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    elapsed = time.perf_counter() - start

    if res.returncode in allow_exit_codes:
        print(f"    ✅ ผ่าน ({elapsed:.2f} วินาที)")
        return True
    else:
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

    total_steps = 3 if args.quick else 4
    success = True

    # ขั้นตอนที่ 1: ตรวจสารบัญ catalog.py
    step1 = run_step(
        1, total_steps,
        "ตรวจสอบความมีอยู่จริงของไฟล์ในสารบัญ (catalog.py check)",
        [sys.executable, "catalog.py", "check"]
    )
    if not step1:
        success = False

    # ขั้นตอนที่ 2: ตรวจ integrity ของไฟล์ข้อมูลดิบ (allow code 0 and 2; code 2 = missing optional/large files, but 0 mismatch)
    step2 = run_step(
        2, total_steps,
        "ตรวจสอบ SHA-256 ข้อมูลดิบ (verify_data_integrity.py --quick)",
        [sys.executable, "analysis/verify_data_integrity.py", "--quick"],
        allow_exit_codes=(0, 2)
    )
    if not step2:
        success = False

    # ขั้นตอนที่ 3: ตรวจสอบมาตรฐานเอกสารและภาษาไทย
    step3 = run_step(
        3, total_steps,
        "ตรวจสอบมาตรฐานเอกสารและภาษาไทย (pytest lint)",
        [sys.executable, "-m", "pytest", "tests/test_standards_integrity.py", "tests/test_thai_language_lint.py", "-q"]
    )
    if not step3:
        success = False

    # ขั้นตอนที่ 4: ตรวจสอบชุดทดสอบทั้งหมด
    if not args.quick:
        step4 = run_step(
            4, total_steps,
            "รันชุดทดสอบระบบทั้งหมด (pytest tests/)",
            [sys.executable, "-m", "pytest", "tests/", "-q"]
        )
        if not step4:
            success = False

    print("=" * 72)
    if success:
        print("🎉 ระบบผ่านการตรวจสอบความสมบูรณ์ 100% พร้อมสำหรับการเผยแพร่และจัดเก็บ")
        print("=" * 72)
        sys.exit(0)
    else:
        print("⚠️ พบข้อผิดพลาดในการตรวจสอบ กรุณาแก้ไขก่อนส่งมอบงาน")
        print("=" * 72)
        sys.exit(1)


if __name__ == "__main__":
    main()
