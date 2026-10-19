"""เป้าหมาย 7 — ตัวโหลดค่าคงที่ที่มีแหล่งอ้างอิง (analysis/goal7/source_constants.json)

ทำไมต้องมี (รอบ 6): ค่านำเข้าของการคำนวณ (เช่น พื้นที่หน้าตัด 504 ตร.ม. · น้ำท่า S.26 · ค่าบำรุงรักษา) เคยถูกพิมพ์เป็น literal ในสคริปต์
โดยไม่มีหน้า/รูป/ตารางอ้างอิง และเคยคำนวณย้อนผิด (ความกว้างท้องคลอง 54.5 แทน 51.0) · ไฟล์ JSON เก็บค่า + แหล่ง (เอกสาร·หน้า·ตาราง/รูป) + วิธีได้ค่า +
วิธีตรวจ · สคริปต์วิเคราะห์เรียก `value("<id>")` แทนพิมพ์ตัวเลข

ใช้: from goal7_source_constants import value, record   (สคริปต์ใน analysis/ เพิ่ม sys.path ของโฟลเดอร์นี้อัตโนมัติเมื่อรันตรง)
ผลลัพธ์: ไม่มี (โมดูลไลบรารี)
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "analysis/goal7/source_constants.json"
METHODS = {"text_layer", "visual_reading", "derived", "assumption", "user_stated"}

_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(PATH.read_text(encoding="utf-8"))
    return _cache


def record(cid: str) -> dict:
    """ระเบียนเต็มของค่าคงที่ (ค่า · แหล่ง · วิธี · การตรวจ)"""
    try:
        return _load()["constants"][cid]
    except KeyError as e:
        raise KeyError(f"ไม่มีค่าคงที่ '{cid}' ใน {PATH.name} — เพิ่มพร้อมแหล่งอ้างอิงก่อนใช้") from e


def value(cid: str):
    """ค่าที่ใช้คำนวณ (ไม่ใช่ค่าที่พิมพ์ในแหล่งเสมอไป — ดู value_in_source ถ้ามี)"""
    return record(cid)["value"]


def all_ids() -> list[str]:
    return list(_load()["constants"])
