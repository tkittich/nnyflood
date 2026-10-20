"""เทียบตัวแยกส่วนหน้าเอกสาร (ไม่ต้องใช้ GPU) — โครงผลและตรรกะรวมกรอบ"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_layout_compare as m  # noqa: E402


def test_merge_overlapping_boxes():
    b = m.merge_overlapping([[0, 0, 10, 10], [5, 5, 20, 20], [100, 100, 110, 110]])
    assert len(b) == 2


def test_visual_boxes_exclude_captions():
    blocks = [{"type": "image", "bbox": [0, 0, 1, 1]}, {"type": "image_caption", "bbox": [0, 0, 1, 1]}, {"type": "text", "bbox": [0, 0, 1, 1]}]
    assert len(m.visual_boxes(blocks)) == 1


def test_result_file_has_both_tools_with_coverage():
    f = ROOT / "analysis/goal7/layout_compare.json"
    r = json.loads(f.read_text(encoding="utf-8"))
    assert set(r["tools"]) == {"unlimited_ocr", "pp_doclayoutv3"}
    for t in r["tools"].values():
        assert 0 <= t["mean_coverage"] <= 1 and 0 <= t["mean_excess"] <= 1
