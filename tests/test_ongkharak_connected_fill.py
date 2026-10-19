"""R7-04: ตัวเติมน้ำแบบเชื่อมต่อลำน้ำ — หน่วยย่อย + ผลสรุปต้องสมเหตุสมผลและตรงเกณฑ์ที่ประกาศไว้ก่อน"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_ongkharak_connected_fill as cf  # noqa: E402

SUMMARY = ROOT / "analysis/goal7/ongkharak_connected_fill_summary.json"


def test_connected_fill_excludes_disconnected_low_pocket():
    dem = np.full((20, 20), 5.0)
    dem[10, 0:6] = 1.0          # ร่องต่ำที่ต่อกับลำน้ำ
    dem[10, 15:18] = 1.0        # แอ่งต่ำที่ไม่ต่อกับลำน้ำ
    river = np.zeros_like(dem, dtype=bool)
    river[10, 0] = True
    valid = np.ones_like(dem, dtype=bool)
    d = np.zeros_like(dem)
    out = cf.connected_fill(dem, valid, river, d, 2.0, 0.0)
    assert out[10, 3] and not out[10, 16]


def test_slope_reduces_far_flooding():
    dem = np.full((5, 40), 2.0)
    river = np.zeros_like(dem, dtype=bool)
    river[:, 0] = True
    d = np.tile(np.arange(40) * 0.03, (5, 1))
    valid = np.ones_like(dem, dtype=bool)
    flat = cf.connected_fill(dem, valid, river, d, 2.5, 0.0).sum()
    sloped = cf.connected_fill(dem, valid, river, d, 2.5, 0.5).sum()
    assert sloped < flat


def test_score_perfect_and_disjoint():
    a = np.zeros((4, 4), dtype=bool)
    a[:2] = True
    assert cf.score(a, a)["iou"] == 1.0
    assert cf.score(a, ~a)["iou"] == 0.0


@pytest.mark.skipif(not SUMMARY.exists(), reason="ยังไม่ได้รันสคริปต์")
def test_summary_verdict_matches_criterion():
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    for name, v in s["verdict"]["by_dem"].items():
        gains = [g["gain_vs_bucket"] for g in v["per_date"].values()]
        assert v["meets_criterion"] == all(g >= cf.IOU_GAIN_REQUIRED for g in gains), name
    for r in s["dem"].values():
        for d in r.values():
            for x in d["by_slope_m_per_km"].values():
                assert 0 <= x["iou"] <= 1
