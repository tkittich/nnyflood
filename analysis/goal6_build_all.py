"""เป้าหมาย 6 — สร้างครบชุดคำเดียว: วิเคราะห์ → canonical → builders → pytest

ทำให้ "อัปเดตบางส่วน" เป็นไปไม่ได้โดยโครงสร้าง — แก้ค่าใด ๆ ให้แก้สคริปต์ต้นทางแล้วรันไฟล์นี้
ลำดับ:
  1. goal6_c2_attribution.py        (corr + chain + สถานการณ์ปล่อยล่วงหน้า)
  2. goal6_l3_model.py --basin all  (โมเดล 6 ลุ่ม — ต้องแคช raw อยู่แล้ว)
  3. goal6_canonical.py             (รวมตัวเลขทุกชุด → canonical.json + retired ledger)
  4. builders รายงาน 3 + 4          (อ่าน canonical ล้วน)
  5. pytest tests/                  (รวม test_goal6_consistency — ค่าเก่า/เอกสารเก่า = ตก)

ขั้นที่ไม่รวม (ต้องเครือข่าย/แคชใหญ่ — รันแยกเมื่อข้อมูลใหม่): goal6_rain_rarity_national,
rain_rarity_2554, screen_basins, s1_*, bkk_sea_mask (รวมอยู่ใน canonical ผ่าน l2_sea_adjust)

รัน: python analysis/goal6_build_all.py [--skip-l3]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(cmd: list[str], name: str, allow_fail: bool = False) -> bool:
    print(f"\n=== {name} ===", flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        if allow_fail:
            print(f"⚠️ {name}: exit {r.returncode} (ข้าม)")
            return False
        print(f"❌ {name} ล้ม (exit {r.returncode}) — หยุด")
        sys.exit(r.returncode)
    return True


def main() -> None:
    skip_l3 = "--skip-l3" in sys.argv
    run([PY, "analysis/goal6_c2_attribution.py"], "1/5 C.2 attribution")
    if not skip_l3:
        run([PY, "analysis/goal6_l3_model.py"], "2/5 โมเดล L3 6 ลุ่ม")
    run([PY, "analysis/goal6_canonical.py"], "3/5 canonical.json")
    run([PY, "report/goal6_build_report3_draft.py"], "4/5 รายงานที่ 3")
    run([PY, "report/goal6_build_report4_draft.py"], "4/5 รายงานที่ 4")
    run([PY, "-m", "pytest", "tests/", "-q"], "5/5 pytest (รวมเทสความสม่ำเสมอ)")
    print("\n✅ build_all ครบ — รายงาน/canonical/เอกสารตรงกันทุกตัว (ตรวจโดยเทส)")


if __name__ == "__main__":
    main()
