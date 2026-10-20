"""ตัวแยกบล็อกของนำร่อง VLM (ไม่ต้องใช้ GPU) — รูปแบบ <|det|>ประเภท [กรอบ]<|/det|>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))
import goal7_vlm_pilot as m  # noqa: E402


def test_parse_blocks_and_bbox_scaling():
    raw = "<|det|>text [[10, 20, 500, 60]]<|/det|>ข้อความ\n<|det|>figure [[100,200,900,700]]<|/det|>\n<|det|>table\n[[0, 800, 999, 990]]<|/det|>| a | b |"
    b = m.parse_blocks(raw)
    assert [x["type"] for x in b] == ["text", "figure", "table"]
    assert b[0]["text"] == "ข้อความ" and b[2]["text"] == "| a | b |"
    assert m.bbox_to_px(b[1]["bbox"], 2000, 3000) == (200, 600, 1800, 2100)


def test_known_answer_samples_have_truth_and_models_listed():
    assert sum(1 for s in m.SAMPLES if s["truth"]) == 3
    assert "unlimited_ocr" in m.MODELS and m.MODELS["unlimited_ocr"] == "baidu/Unlimited-OCR"
