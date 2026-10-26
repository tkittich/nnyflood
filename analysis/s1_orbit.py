"""Sentinel-1: เลขวงโคจรสัมพัทธ์และเวลาถ่ายจากชื่อฉาก (ใช้จับคู่ฉากอ้างอิงตามวงโคจร)

ที่มา: S1C และ S1D เป็นดาวเทียมคู่ที่ใช้วงโคจรเดียวกันได้ · เลขวงโคจรสัมพัทธ์ = (เลขวงโคจรสัมบูรณ์ − ค่าชดเชยของดาวเทียม) mod 175 + 1
ใช้โดย: goal6_s1_stage2_water.py · goal6_s1_reference_audit.py · goal7_s1_chachoengsao_recent.py
ผลลัพธ์: ไม่มี (โมดูลไลบรารี)
รัน: python -c "import sys; sys.path.insert(0, 'analysis'); import s1_orbit"
"""
from __future__ import annotations

import re

OFFSET = {"A": 73, "B": 27, "C": 172, "D": 73}
EVENT_START = "2026-09-24T00:00:00"        # ฉากอ้างอิงต้องถ่ายก่อนเวลานี้ (UTC)


def rel_orbit(name: str) -> int:
    ab = int(re.search(r"_(\d{6})_[0-9A-F]{6}_", name).group(1))
    return (ab - OFFSET[name[2]]) % 175 + 1


def start_of(name: str) -> str:
    """เวลาเริ่มถ่าย (UTC) รูป YYYY-MM-DDTHH:MM:SS"""
    m = re.search(r"_(\d{8})T(\d{6})_", name)
    d, t = m.group(1), m.group(2)
    return f"{d[:4]}-{d[4:6]}-{d[6:]}T{t[:2]}:{t[2:4]}:{t[4:]}"
