"""สร้างรายงาน 7 (ประชาชน) + 8 (วิชาการ) ให้ตรงกัน — รันจนผังหัวข้อนิ่ง (โทเคนอ้างข้ามฉบับต้องใช้ผังของอีกฉบับ)

ใช้: python report/goal7_build_all.py          # วิเคราะห์ใหม่ก่อนด้วย: python analysis/goal7_analysis.py
"""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/goal7"


def h() -> str:
    return hashlib.sha256(b"".join((OUT / f"outline_{n}.json").read_bytes() for n in ("public", "academic") if (OUT / f"outline_{n}.json").exists())).hexdigest()


for rnd in range(1, 4):
    before = h()
    for b in ("goal7_build_public.py", "goal7_build_academic.py"):
        subprocess.run([sys.executable, str(ROOT / "report" / b)], check=True)
    if h() == before:
        print(f"ผังหัวข้อนิ่งที่รอบ {rnd}")
        break
else:
    raise SystemExit("ผังหัวข้อไม่นิ่งภายใน 3 รอบ — ตรวจ key/โทเคนอ้างวน")
