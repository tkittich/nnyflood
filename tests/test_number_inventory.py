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


def test_builder_literal_gate_no_new_untraced_numbers():
    """R7-07: ตัวเลขฝังใน builder ที่ไม่มีที่มาใน JSON เพิ่มใหม่ไม่ได้ (baseline: analysis/goal7/literal_allowlist.json) และรายการที่ถอดแล้วต้องลบออก"""
    _, _, builders = ni.sources()
    _, values = ni.json_leaves()
    new, stale = ni.gate_violations(builders, ni.known_set(values))
    assert not new, f"ตัวเลขฝังใหม่ใน builder (ให้อ่านจาก JSON/โทเคน): {sorted(new)[:5]}"
    assert not stale, f"ถอดตัวเลขฝังแล้ว — รัน tools/number_inventory.py --write-allowlist: {sorted(stale)[:5]}"


def test_builder_literal_gate_catches_injected_error(tmp_path):
    """ทดสอบประตูด้วยข้อผิดจำลอง: builder ที่พิมพ์ '1777 ตร.กม.' ต้องถูกจับ"""
    b = tmp_path / "fake_builder.py"
    b.write_text('X = "พื้นที่ท่วม 1777 ตร.กม. ทั้งหมด"\n', encoding="utf-8")
    new, _ = ni.gate_violations([b], ni.known_set([1.0]), allow={})
    assert ("fake_builder.py", "1777 ตร.กม.") in new
    ok, _ = ni.gate_violations([b], ni.known_set([1777.0]), allow={})
    assert not ok   # ตรงค่าใน JSON = มีที่มา
