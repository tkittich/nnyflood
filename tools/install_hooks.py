#!/usr/bin/env python3
"""tools/install_hooks.py — ติดตั้ง Git Pre-Commit Hook สำหรับคลังข้อมูล nnyflood

การทำงาน:
    ติดตั้งสคริปต์ .git/hooks/pre-commit เพื่อตรวจความถูกต้องอัตโนมัติก่อน commit:
    1. <PY> catalog.py check (ตรวจสอบว่าไม่มีพาธหรือไฟล์ในสารบัญที่ขาดหาย)
    2. <PY> -m pytest tests/test_thai_language_lint.py tests/test_standards_integrity.py tests/test_data_consistency.py -q

    <PY> ถูกเลือกจาก interpreter ที่ `import pytest` ได้จริง (python3.14 → python3 → python)
    เพราะบนเครื่องที่มี managed runtime หลายตัว `python` เปล่า ๆ อาจชี้ไปตัวที่ไม่มี pytest
    ทำให้ hook ล้มทุก commit ด้วย "No module named pytest"
"""
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = ROOT / ".git" / "hooks" / "pre-commit"

HOOK_CONTENT = """#!/bin/sh
# nnyflood git pre-commit hook
# ป้องกันการ commit ไฟล์ที่มีคำผิด คำชน สารบัญล้าสมัย หรือรายงานที่ขาดป้ายกำกับ
#
# เลือก interpreter ที่ import pytest ได้จริง — ห้ามใช้ `python` เปล่า ๆ
# เพราะ PATH อาจชี้ไปตัวที่ไม่มี pytest (managed runtime) แล้ว hook จะล้มทุก commit

PY=""
for c in python3.14 python3 python; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import pytest" >/dev/null 2>&1; then
        PY="$c"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "❌ [Pre-commit] ไม่พบ Python ที่มี pytest — รัน 'pip install -r requirements.txt' แล้วลองใหม่"
    exit 1
fi

echo "🔍 [Pre-commit] 1/2 ตรวจสอบสารบัญระบบ (catalog.py check)..."
"$PY" catalog.py check
if [ $? -ne 0 ]; then
    echo "❌ [Pre-commit] สารบัญระบบ catalog.py มีไฟล์สูญหาย กรุณาตรวจสอบก่อน commit"
    exit 1
fi

echo "🔍 [Pre-commit] 2/2 ตรวจสอบภาษาไทย มาตรฐานเอกสาร และความสอดคล้องข้อมูล (pytest)..."
"$PY" -m pytest tests/test_thai_language_lint.py tests/test_standards_integrity.py tests/test_data_consistency.py -q
if [ $? -ne 0 ]; then
    echo "❌ [Pre-commit] ตรวจพบคำผิด คำชน มาตรฐานเอกสารไม่ผ่าน หรือมีตัวเลขขัดแย้ง/ปลดประจำการ กรุณาแก้ไขก่อน commit"
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
