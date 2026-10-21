"""OCR รุ่นที่ 2 (ไม่ใช้ GPU) — ตรรกะนับตัวเลขและเทียบความตรงกันของตัวอ่านสองตัว"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))
import goal7_ocr_v2 as v2  # noqa: E402


def test_numbers_of_ignores_km_marks_and_thai_digits():
    n = v2.numbers_of("| 0+000 | 23+000 | ๖๐๕.๒๒ | 53.00 | 10,000 |")
    assert 605.22 in n and 53.0 in n and 10000.0 in n and 0.0 not in n


def test_digit_score_counts_decimals_and_long_ints():
    assert v2.digit_score("a 1.25 b 2 c 480") == 2


def test_volume_map_covers_four_volumes():
    assert set(v2.VOLS) == {"eia2569_main1", "eia2569_main2", "eia2569_app1", "eia2569_app2"}
