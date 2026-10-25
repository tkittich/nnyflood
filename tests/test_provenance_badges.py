"""B3 (รีวิวรอบ 7): ป้ายผ่านการตรวจในกล่องประวัติต้องอ่านจากไฟล์ผลตรวจจริง ไม่ใช่ข้อความคงที่"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "report"))
import goal6_reportlib as lib  # noqa: E402


def _box(tmp_path, gates=None):
    p = tmp_path / "v.json"
    if gates is not None:
        p.write_text(json.dumps({"git_rev": "abc1234", "checked_at": "2026-10-25T12:00+07:00", "gates": gates}), encoding="utf-8")
    return lib.provenance_box("x.json", verification_path=p)


def test_no_file_no_checkmarks(tmp_path):
    h = _box(tmp_path)
    assert "&#10003;" not in h and "ยังไม่ได้ตรวจ" in h


def test_failed_gate_has_no_checkmark(tmp_path):
    h = _box(tmp_path, {"thai": "pass", "contrast": "fail", "legal_privacy": "pass", "canonical": "pass"})
    assert h.count("&#10003;") == 3 and "ไม่ผ่านความเปรียบต่างสี" in h


def test_all_pass_four_checkmarks_and_revision(tmp_path):
    h = _box(tmp_path, {"thai": "pass", "contrast": "pass", "legal_privacy": "pass", "canonical": "pass"})
    assert h.count("&#10003;") == 4 and "abc1234" in h


def test_committed_verification_file_is_wellformed():
    v = json.loads((ROOT / "report/assets/verification.json").read_text(encoding="utf-8"))
    assert set(v["gates"]) == {"thai", "contrast", "legal_privacy", "canonical"} and set(v["gates"].values()) <= {"pass", "fail"}
