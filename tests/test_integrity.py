# ทดสอบตัวตรวจความครบถ้วนข้อมูล (analysis/verify_data_integrity.py) — ซึ่งเป็น gate ของ CI
# ครอบ: parser 3 รูปแบบ manifest · verify() OK/MISMATCH/MISSING/DELETED · exit code ·
#        resolve ด้วย basename ที่ชนกัน (ต้องเตือน ไม่แฮชผิดไฟล์แบบเงียบ)
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))

import verify_data_integrity as vi  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_ambiguous():
    vi.AMBIGUOUS.clear()
    yield
    vi.AMBIGUOUS.clear()


def _sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _mk(tmp_path, rel, data: bytes) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def test_parse_manifest_table_format(tmp_path):
    """รูปแบบ 1: ตาราง ``| `path` | size | hash |`` — อ่าน path + แฮชได้ตรง"""
    f = _mk(tmp_path, "a.csv", b"hello")
    md = tmp_path / "manifest.md"
    md.write_text(f"| `a.csv` | 5 B | `{_sha(f)}` |\n", encoding="utf-8")
    rows = vi.parse_manifest(md)
    assert len(rows) == 1
    assert rows[0][1] == "a.csv"
    assert rows[0][2] == _sha(f)


def test_parse_hashes_txt_format(tmp_path):
    """รูปแบบ 4: ไฟล์แยก `<64hex>  *name` (มี/ไม่มีดอกจัน)"""
    f = _mk(tmp_path, "raw/b.bin", b"abc")
    hf = tmp_path / "_hashes.txt"
    hf.write_text(f"{_sha(f)}  *raw/b.bin\n0{'0' * 63}  plain_name.csv\n", encoding="utf-8")
    rows = vi.parse_hashes_txt(hf)
    assert rows[0] == (hf.name, "raw/b.bin", _sha(f))
    assert rows[1][1] == "plain_name.csv"


def test_verify_ok_then_mismatch_exit_codes(tmp_path):
    """ไฟล์ตรงแฮช -> exit 0 · แก้ไฟล์ทีหลัง -> MISMATCH exit 1"""
    f = _mk(tmp_path, "derived/x.csv", b"data-v1")
    md = tmp_path / "manifest.md"
    md.write_text(f"| `derived/x.csv` | 7 B | `{_sha(f)}` |\n", encoding="utf-8")
    assert vi.main(["--only", str(tmp_path)]) == 0
    f.write_bytes(b"data-v2-tampered")
    assert vi.main(["--only", str(tmp_path)]) == 1


def test_verify_missing_exit_2(tmp_path):
    """แฮชของไฟล์ที่ไม่อยู่บนดิสก์ (ส่วนใหญ่บน clone) -> exit 2 ไม่ใช่ความล้มเหลว"""
    md = tmp_path / "manifest.md"
    md.write_text(f"| `big/raw.dat` | 9 GB | `{'ab' * 32}` |\n", encoding="utf-8")
    assert vi.main(["--only", str(tmp_path)]) == 2


def test_deleted_marker_not_missing(tmp_path):
    """ชื่อที่มี marker ไทล์ที่ลบแล้ว (T47PPS) = DELETED ไม่นับเป็น MISSING"""
    md = tmp_path / "manifest.md"
    md.write_text(f"| `T47PPS_tile_old.zip` | 1 GB | `{'cd' * 32}` |\n", encoding="utf-8")
    rows = vi.verify([tmp_path])
    assert rows[0][3] == "DELETED"
    assert vi.main(["--only", str(tmp_path)]) == 0


def test_ambiguous_basename_fallback_warns(tmp_path):
    """manifest ระบุชื่อไฟล์ลอย ๆ ที่มี 2 ไฟล์ชื่อเดียวกัน = ต้องเตือน AMBIGUOUS
    (และแฮชไฟล์แรกตามเดิม — แต่คนรันต้องเห็นว่าควรแก้ manifest)"""
    a = _mk(tmp_path, "sub1/x.dat", b"content-A")
    b = _mk(tmp_path, "sub2/x.dat", b"content-B")
    # แฮชของ sub2 แต่ manifest ระบุแค่ "x.dat" -> resolve ได้ sub1 -> MISMATCH + เตือน
    md = tmp_path / "manifest.md"
    md.write_text(f"| `x.dat` | 9 B | `{_sha(b)}` |\n", encoding="utf-8")
    assert vi.main(["--only", str(tmp_path)]) == 1
    assert len(vi.AMBIGUOUS) == 1
    assert Path(vi.AMBIGUOUS[0][2][0]) == a


def test_full_path_resolves_without_ambiguity(tmp_path):
    """manifest ระบุ path เต็ม = ไม่ผ่าน fallback ไม่เตือน"""
    a = _mk(tmp_path, "sub1/x.dat", b"content-A")
    _mk(tmp_path, "sub2/x.dat", b"content-B")
    md = tmp_path / "manifest.md"
    md.write_text(f"| `sub1/x.dat` | 9 B | `{_sha(a)}` |\n", encoding="utf-8")
    assert vi.main(["--only", str(tmp_path)]) == 0
    assert vi.AMBIGUOUS == []


def test_ambiguous_basename_silent_match_is_exit_3(tmp_path):
    """basename ชนกันแต่แฮช "ตรง" กับไฟล์แรกที่เจอ = เดิมผ่านเงียบ ๆ (exit 0)
    → GLM GL-18: ผลตรวจของรายการนั้นใช้ยืนยันไม่ได้ ต้อง exit 3 (CI ล้มที่ code > 2)"""
    a = _mk(tmp_path, "sub1/x.dat", b"content-A")
    _mk(tmp_path, "sub2/x.dat", b"content-B")
    md = tmp_path / "manifest.md"
    md.write_text(f"| `x.dat` | 9 B | `{_sha(a)}` |\n", encoding="utf-8")
    assert vi.main(["--only", str(tmp_path)]) == 3
    assert len(vi.AMBIGUOUS) == 1
