#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""สคริปต์ดึงชั้นข้อมูลน้ำท่วมจาก GISTDA Disaster Platform API (2026) — ตัวเชื่อมโยงไปยัง goal6_fetch_gistda_flood.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))

from goal6_fetch_gistda_flood import main

if __name__ == "__main__":
    main()
