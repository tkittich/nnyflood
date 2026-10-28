"""tests/test_render_status.py — ทุกคีย์ระดับบนของ canonical.json (เป้าหมาย 6 และ 7) ต้องมีสถานะการเรนเดอร์ที่ตรงกับตัวสร้างจริง

ทะเบียนอยู่ที่ analysis/common_render_status.py (แนบลง canonical ใต้ render_status โดยตัวผลิต canonical)
เทสต์ตรวจโครงสร้างและความสอดคล้องกับซอร์ส report/*.py เท่านั้น — ไม่ตัดสินว่าผลวิเคราะห์ใดควรลงรายงาน
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))

import common_render_status as crs  # noqa: E402


def _load(goal: str) -> dict:
    return json.loads((ROOT / f"analysis/{goal}/canonical.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("goal", ["goal6", "goal7"])
def test_every_canonical_key_has_matching_render_status(goal):
    canonical = _load(goal)
    assert canonical.get("render_status") == crs.REGISTRY[goal], (
        f"render_status ใน {goal}/canonical.json ไม่ตรงทะเบียน — รันตัวผลิต canonical ใหม่"
    )
    assert crs.problems(canonical, goal) == []


@pytest.mark.parametrize("goal", ["goal6", "goal7"])
def test_checker_detects_each_failure_mode(goal):
    base = copy.deepcopy(_load(goal))
    rendered = next(k for k, r in base["render_status"].items() if r["status"] == "rendered")

    missing = copy.deepcopy(base)
    del missing["render_status"][rendered]
    assert any("ไม่มีสถานะ" in p for p in crs.problems(missing, goal))

    stale = copy.deepcopy(base)
    stale["render_status"]["_no_such_key"] = {"status": "metadata"}
    assert any("ไม่มีใน canonical" in p for p in crs.problems(stale, goal))

    hidden = copy.deepcopy(base)
    hidden["render_status"][rendered] = {"status": "internal_only", "reason": "x"}
    assert any("ตัวสร้างอ่านอยู่" in p for p in crs.problems(hidden, goal))

    phantom = copy.deepcopy(base)
    phantom[goal + "_new_key"] = {}
    phantom["render_status"][goal + "_new_key"] = {"status": "rendered", "builders": ["goal6_build_report3_draft.py"]}
    assert any("ไม่พบในซอร์ส" in p or "ไม่มีตัวสร้างใดอ่าน" in p for p in crs.problems(phantom, goal))


def test_superseded_target_must_be_rendered_key():
    canonical = _load("goal7")
    bad = copy.deepcopy(canonical)
    bad["render_status"]["design_2565_structs"] = {
        "status": "superseded_by", "key": "illustrative_only", "reason": "x"}
    assert any("ต้องเป็นคีย์ที่ออกรายงานจริง" in p for p in crs.problems(bad, "goal7"))
