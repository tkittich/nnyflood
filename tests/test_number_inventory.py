"""รอบ 6: เครื่องมือบัญชีตัวเลขต้องรันได้และมีครบ 5 ส่วน (ตัวเลขผลลัพธ์ไม่ถูกบังคับ — เป็นรายการให้คนตัดสิน)"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import number_inventory as ni  # noqa: E402


def test_extract_numbers_with_units():
    got = [(v, u) for _, v, _, u, _ in ni.extract("ท้องคลองกว้าง 51 ม. และความจุ 1,988 ล้าน ลบ.ม. ราว 10.49%")]
    assert (51.0, "m") in got and (1988.0, "mcm") in got and (10.49, "pct") in got


def test_concept_scan_flags_two_values(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("ท้องคลองกว้าง 51 ม.\nท้องคลองกว้าง 54.5 ม.\n", encoding="utf-8")
    res = ni.concept_scan([], [f])
    assert "ความกว้างท้องคลอง" in res and len(res["ความกว้างท้องคลอง"]) == 2


def test_full_scan_has_all_sections():
    reports, docs, builders = ni.sources()
    leaves, values = ni.json_leaves()
    res = {
        "A": ni.concept_scan(reports, docs),
        "B": ni.orphan_scan(reports, ni.known_set(values)),
        "C": ni.key_conflicts(leaves),
        "D": ni.builder_literals(builders),
        "E": ni.stale_status_counts(),
    }
    md = ni.render(res)
    for h in ("## A.", "## B.", "## C.", "## D.", "## E."):
        assert h in md
