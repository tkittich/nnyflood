"""ประทับผลตรวจจริงของแต่ละด่าน (ภาษา · สี · กฎหมาย/ข้อมูลส่วนบุคคล · ผูกตัวเลขกลาง) ลงไฟล์ให้กล่องประวัติของรายงานอ่าน
รีวิวรอบ 7 (B3): ป้าย "✓ ผ่าน…" ในรายงานเคยเป็นข้อความคงที่ ไม่ได้อ่านผลตรวจใด ๆ — จึงให้ป้ายอ่านไฟล์นี้เท่านั้น
กติกา: ด่านที่ไม่มีผล/ไม่ผ่าน = ไม่ขึ้นเครื่องหมายถูก · ไฟล์บอกรหัสรุ่น git และเวลาที่ตรวจ (รายงานแสดงเมื่อรุ่นไม่ตรงกับปัจจุบัน)
รัน: python tools/write_verification.py   (verify_all.py เรียกให้อัตโนมัติท้ายการตรวจเต็ม)
ผลลัพธ์: report/assets/verification.json
"""
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report/assets/verification.json"

GATES = {
    "thai": ["tests/test_thai_language_lint.py", "tests/test_report3_language.py"],
    "contrast": ["tests/test_contrast.py"],
    "legal_privacy": ["tests/test_legal_compliance.py", "tests/test_privacy.py"],
    "canonical": ["tests/test_data_consistency.py", "tests/test_goal6_consistency.py", "tests/test_goal7_report.py", "tests/test_reports12.py", "tests/test_number_inventory.py"],
}


def git_rev() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=5, stdin=subprocess.DEVNULL)
        return r.stdout.strip() or "unknown"
    except Exception:   # noqa: BLE001
        return "unknown"


def run_gate(files: list[str]) -> str:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", *files], cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return "pass" if r.returncode == 0 else "fail"


def main() -> int:
    res = {k: run_gate(v) for k, v in GATES.items()}
    out = {"git_rev": git_rev(), "checked_at": dt.datetime.now().astimezone().isoformat(timespec="minutes"), "gates": res,
           "tests": {k: v for k, v in GATES.items()}}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("ประทับผลตรวจ:", res, "รุ่น", out["git_rev"])
    return 0 if all(v == "pass" for v in res.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
