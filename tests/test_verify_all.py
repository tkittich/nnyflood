"""ทดสอบตัวช่วยตัดสินผลของ tools/verify_all.py — คำเตือนเมื่อขั้นตอนผ่านแบบมีเงื่อนไข (รหัสออก 2)

ที่มา (R6-07): verify_all.py เดิมนับรหัสออก 2 (ไฟล์ข้อมูลขนาดใหญ่หายบางส่วน) เป็น "ผ่าน" เงียบ ๆ
โดยไม่มีคำเตือน — เทสต์นี้ตรึงกติกา: รหัสที่อนุญาตแต่ไม่ใช่ 0 ต้องผ่านพร้อมคำเตือนเสมอ
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("verify_all_tool", ROOT / "tools/verify_all.py")
_verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_verify)


def test_clean_pass_has_no_warning():
    ok, warning = _verify.step_verdict(0)
    assert ok is True
    assert warning is None


def test_allowed_nonzero_code_warns():
    ok, warning = _verify.step_verdict(2, (0, 2))
    assert ok is True
    assert warning is not None and "2" in warning


def test_disallowed_nonzero_code_fails():
    ok, warning = _verify.step_verdict(2)  # รหัส 2 ไม่ได้อยู่ในรายการที่อนุญาต
    assert ok is False
    assert warning is None

    ok2, _ = _verify.step_verdict(1, (0, 2))
    assert ok2 is False
