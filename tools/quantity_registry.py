#!/usr/bin/env python3
"""tools/quantity_registry.py — ตรวจทะเบียนตัวตนของปริมาณ (analysis/goal7/quantities.json) กับ canonical และค่าคงที่ต้นทาง (R7-08)

ตรวจ: (1) ทุกปริมาณมีชื่อ·ขอบเขต·นิยาม·หน่วย·ชนิดที่มา (2) ตัวชี้ canonical_ref ชี้ถึงตัวเลขจริง (3) ทุกพารามิเตอร์ใน reconciled_parameters มีทะเบียน
(4) ค่าคงที่ต้นทาง (source_constants) ต้องเท่ากับค่ามาตรฐาน หรือตรงกับตัวแปรที่จดไว้ใน variants — ถ้าไม่ตรง = ข้อมูลใหม่ต่างจาก canonical (ทริกเกอร์)
(5) กราฟพึ่งพาไม่วนและอ้างถึงได้ (6) สถานะ "ถูกโต้แย้ง" ส่งต่อไปยังปริมาณที่พึ่งพา

รัน: python tools/quantity_registry.py
ผลลัพธ์: พิมพ์รายงานตรวจ (exit 1 ถ้ามีข้อผิดพลาด)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "analysis/goal7/quantities.json"
CANON = ROOT / "analysis/goal7/canonical.json"
CONSTS = ROOT / "analysis/goal7/source_constants.json"
CANON6 = ROOT / "analysis/goal6/canonical.json"      # ปริมาณของเป้าหมาย 6 ระบุด้วย canonical_file: "goal6"
KINDS = {"stated", "computed", "assumed", "measured", "simulated"}
REQ = ("id", "name_th", "scope", "definition", "unit", "kind", "status")


def _resolve(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        cur = cur[part]
    return cur


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def effective_status(quantities: list[dict]) -> dict[str, list[str]]:
    """คืน {id: [ต้นเหตุที่ถูกโต้แย้ง]} — ว่าง = ไม่ถูกโต้แย้ง · สืบทอดผ่าน depends_on"""
    by = {q["id"]: q for q in quantities}
    memo: dict[str, list[str]] = {}

    def go(i: str, stack: tuple = ()) -> list[str]:
        if i in memo:
            return memo[i]
        if i in stack:
            raise ValueError("กราฟพึ่งพาวน: " + " → ".join(stack + (i,)))
        q = by[i]
        causes = [i] if q["status"] == "disputed" else []
        for d in q["depends_on"]:
            causes += go(d, stack + (i,))
        memo[i] = sorted(set(causes))
        return memo[i]

    return {i: go(i) for i in by}


def check(reg: list[dict] | None = None) -> tuple[list[str], dict[str, list[str]]]:
    reg = json.loads(REG.read_text(encoding="utf-8"))["quantities"] if reg is None else reg
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    canon6 = json.loads(CANON6.read_text(encoding="utf-8"))
    consts = json.loads(CONSTS.read_text(encoding="utf-8"))["constants"]
    errs: list[str] = []
    ids = [q.get("id") for q in reg]
    if len(ids) != len(set(ids)):
        errs.append("id ซ้ำในทะเบียน")
    for q in reg:
        miss = [k for k in REQ if not q.get(k)]
        if "depends_on" not in q:
            miss.append("depends_on")
        if miss:
            errs.append(f"{q.get('id')}: ขาดฟิลด์ {miss}")
        if q.get("kind") not in KINDS:
            errs.append(f"{q.get('id')}: kind ไม่ถูกต้อง {q.get('kind')!r}")
        if q.get("status") not in ("settled", "disputed"):
            errs.append(f"{q.get('id')}: status ไม่ถูกต้อง")
        if q.get("status") == "disputed" and not q.get("disputed_by"):
            errs.append(f"{q['id']}: disputed ต้องระบุ disputed_by")
        for d in q.get("depends_on", []):
            if d not in ids:
                errs.append(f"{q['id']}: depends_on '{d}' ไม่มีในทะเบียน")
    covered = set()
    for q in reg:
        ref, cv = q.get("canonical_ref"), None
        g6 = q.get("canonical_file") == "goal6"
        if ref:
            if not g6:
                covered.add(ref.split(".")[1])
            try:
                cv = _resolve(canon6 if g6 else canon, ref)
            except (KeyError, TypeError):
                errs.append(f"{q['id']}: canonical_ref '{ref}' ไม่พบ")
            else:
                if not isinstance(cv, (int, float)):
                    errs.append(f"{q['id']}: canonical_ref '{ref}' ไม่ใช่ตัวเลข")
                    cv = None
        sc = q.get("source_constant")
        if sc and g6:
            errs.append(f"{q['id']}: ปริมาณ goal6 ยังไม่รองรับ source_constant")
        elif sc:
            if sc not in consts:
                errs.append(f"{q['id']}: source_constant '{sc}' ไม่มีใน source_constants.json")
            elif cv is not None:
                sv = consts[sc]["value"]
                variants = [v.get("value") for v in canon["reconciled_parameters"][ref.split(".")[1]].get("variants", {}).values() if isinstance(v, dict)]
                if not _close(sv, cv) and not any(isinstance(v, (int, float)) and _close(v, sv) for v in variants):
                    errs.append(f"{q['id']}: ค่าคงที่ต้นทาง {sc}={sv} ต่างจากค่ามาตรฐาน {cv} และไม่อยู่ใน variants — กระทบยอดก่อน")
    for p in canon["reconciled_parameters"]:
        if p not in covered:
            errs.append(f"reconciled_parameters.{p} ไม่มีในทะเบียนตัวตนของปริมาณ")
    try:
        eff = effective_status(reg)
    except (ValueError, KeyError) as e:
        errs.append(str(e))
        eff = {}
    return errs, eff


def main() -> int:
    errs, eff = check()
    for e in errs:
        print("❌", e)
    for i, causes in eff.items():
        if causes:
            print("⚠️ ถูกโต้แย้ง:", i, "←", ", ".join(causes))
    print("ทะเบียนปริมาณ:", "ผ่าน" if not errs else f"พบ {len(errs)} ข้อผิดพลาด")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
