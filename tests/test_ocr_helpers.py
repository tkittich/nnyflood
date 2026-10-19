"""รอบ 6: ตัวช่วยของคิว Typhoon-OCR (ตรวจ echo/ความสมบูรณ์ของหน้า) ต้องไม่ถดถอย — ไม่เรียก GPU"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_typhoon_ocr as ty  # noqa: E402


def test_is_echo_detects_template_leak():
    assert ty.is_echo("Below is an image of a document page, along with its dimensions")
    assert ty.is_echo("... RAW_TEXT_START ...")
    assert not ty.is_echo("รายงานการประเมินผลกระทบสิ่งแวดล้อม บทที่ 2")


def test_record_done_redoes_echo_and_errors():
    assert not ty.record_done({"page": 1, "error": "x"})
    assert not ty.record_done({"page": 1, "text": "RAW_TEXT_START Page dimensions"})
    assert not ty.record_done({"page": 1, "text": ""})
    assert ty.record_done({"page": 1, "text": "ข้อความปกติ"})
    assert ty.record_done({"page": 1, "text": "", "meta": {"needs_visual": True, "echo_final": True}})   # ทำเครื่องหมายต้องอ่านภาพแล้ว ไม่ทำซ้ำ


def test_figure_pages_have_shorter_time_cap_than_scans():
    assert ty.MAX_TIME_S["figure"] < ty.MAX_TIME_S["scan"]
