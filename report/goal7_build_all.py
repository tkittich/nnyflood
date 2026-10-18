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

sys.path.insert(0, str(ROOT / "report"))
from goal7_engine import PENDING  # noqa: E402

for f in ("คลองเจ้าพระยา2_ประชาชน.html", "คลองเจ้าพระยา2_วิชาการ.html"):
    if PENDING in (ROOT / "report" / f).read_text(encoding="utf-8"):
        raise SystemExit(f"{f}: ยังมีโทเคนอ้างข้ามฉบับที่ไม่พบ key (พิมพ์ผิด?)")

# สร้างสมุดปกขาวเชิงนโยบายควบคู่เสมอ
subprocess.run([sys.executable, str(ROOT / "report/goal7_build_policy_brief.py")], check=True)
print("สร้างรายงานเป้าหมาย 7 ครบทั้ง 3 ฉบับสำเร็จ")
