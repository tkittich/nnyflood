#!/usr/bin/env python3
"""tools/install_hooks.py — ติดตั้ง Git Pre-Commit Hook สำหรับคลังข้อมูล nnyflood

การทำงาน:
    ติดตั้งสคริปต์ .git/hooks/pre-commit เพื่อตรวจความถูกต้องอัตโนมัติก่อน commit:
    1. python catalog.py check (ตรวจสอบว่าไม่มีพาธหรือไฟล์ในสารบัญที่ขาดหาย)
    2. python -m pytest tests/test_thai_language_lint.py tests/test_standards_integrity.py -q
"""
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = ROOT / ".git" / "hooks" / "pre-commit"

HOOK_CONTENT = """#!/bin/sh
# nnyflood git pre-commit hook
# ป้องกันการ commit ไฟล์ที่มีคำผิด คำชน สารบัญล้าสมัย หรือรายงานที่ขาดป้ายกำกับ

echo "🔍 [Pre-commit] 1/2 ตรวจสอบสารบัญระบบ (catalog.py check)..."
python catalog.py check
if [ $? -ne 0 ]; then
    echo "❌ [Pre-commit] สารบัญระบบ catalog.py มีไฟล์สูญหาย กรุณาตรวจสอบก่อน commit"
    exit 1
fi

echo "🔍 [Pre-commit] 2/2 ตรวจสอบภาษาไทยและมาตรฐานเอกสาร (pytest)..."
python -m pytest tests/test_thai_language_lint.py tests/test_standards_integrity.py -q
if [ $? -ne 0 ]; then
    echo "❌ [Pre-commit] ตรวจพบคำผิด คำชน หรือมาตรฐานเอกสารไม่ผ่าน กรุณาแก้ไขก่อน commit"
    exit 1
fi

echo "✅ [Pre-commit] ผ่านการตรวจสอบทั้งหมด เรียบร้อยดี"
exit 0
"""


def install():
    if not (ROOT / ".git").exists():
        print("❌ ไม่พบโฟลเดอร์ .git กรุณารันใน root ของ repository")
        sys.exit(1)

    HOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    HOOK_PATH.write_text(HOOK_CONTENT, encoding="utf-8")

    # ตั้งค่า executable permission (สำหรับ Linux/macOS/Git Bash)
    try:
        current_stat = HOOK_PATH.stat().st_mode
        HOOK_PATH.chmod(current_stat | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass

    print(f"✅ ติดตั้ง Git Pre-commit Hook เรียบร้อยแล้วที่: {HOOK_PATH.relative_to(ROOT)}")
    print("   จะทำงานอัตโนมัติทุกครั้งที่มีคำสั่ง 'git commit'")


if __name__ == "__main__":
    install()
