"""เป้าหมาย 6 — H1: ประวัติเขื่อนผู้สมัครที่ยังไม่ได้ดึง (เติมให้ครบ 24 แห่ง) → benchmark 2554

ลุ่มที่ทำผ่าน spike/L1 มีประวัติครบแล้ว 9 เขื่อน — สคริปต์นี้เดินปีถอย (ว่าง 2 ปีต่อเนื่องหยุด)
เขื่อนที่เหลือ แล้วคำนวณ URC compliance รายปีเทียบเทมเพลต (ยืนยันแล้วว่าเป็น curve จริง)
ผลลัพธ์: analysis/goal6/dam_history_all.json + dam_history_all.md  (ตารางเทียบ 2554 vs 2569 ทุกเขื่อน)
raw: data/22_goal6_network/raw/dam_history_all/ (ประวัติเต็มรายเขื่อน)
ทำซ้ำได้ — เขื่อนที่มี raw แล้วข้าม · รัน: python analysis/goal6_dam_history_all.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import goal6_screen_basins as g6
import goal6_spike_pasak_l1 as pasak
import goal6_spike_maeklong_l1 as mk  # dam_walk(dam_id) parameterized

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "analysis/goal6_dam_candidates.json"
RAW_DIR = ROOT / "data/22_goal6_network/raw/dam_history_all"
OUT_JSON = ROOT / "analysis/goal6/dam_history_all.json"
OUT_MD = ROOT / "analysis/goal6/dam_history_all.md"


def dam_full(dam_id: int) -> dict:
    hist = mk.dam_walk(dam_id)
    per_year = []
    for y in sorted(hist["years"], reverse=True):
        rows = hist["years"][y]
        st = pasak.urc_stats(rows, hist["urc_mmdd"])
        vals = [r["storage"] for r in rows.values() if r.get("storage") is not None]
        rel = [r["released"] for r in rows.values() if r.get("released") is not None]
        per_year.append({"year": int(y), "n_days": len(rows), "max_storage": max(vals) if vals else None,
                         "max_released": max(rel) if rel else None, **st})
    return {"dam_id": dam_id, "urc_points": len(hist["urc_mmdd"]),
            "first_year": min((int(r["year"]) for r in per_year if r["n_days"] > 0), default=None),
            "years": per_year, "urc_mmdd": hist["urc_mmdd"],
            "storage_all": {y: rows for y, rows in hist["years"].items()}}


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cands = json.loads(CANDIDATES.read_text(encoding="utf-8"))["candidates"]
    out: dict = {"dams": {}}
    if OUT_JSON.exists():
        out = json.loads(OUT_JSON.read_text(encoding="utf-8"))

    for c in cands:
        name = c["dam_name"]
        dids = c["dam_ids"]
        # เขื่อนที่มีประวัติแล้วจาก spike/L1 (ดูด้วย raw ไฟล์)
        raw_path = RAW_DIR / f"dam_{dids[0]}.json"
        if raw_path.exists():
            continue
        # เลือก dam_id ที่มีข้อมูลมากสุด (ลองทีละ id)
        best = None
        for did in dids:
            try:
                rec = dam_full(did)
            except RuntimeError:
                rec = None
            if rec and rec["years"] and (best is None or rec["first_year"] < best["first_year"]):
                best = rec
                best["dam_id_used"] = did
        if not best:
            out["dams"][name] = {"dam_ids": dids, "error": "ไม่มีข้อมูล"}
        else:
            best.pop("storage_all", None)
            full = {k: v for k, v in best.items()}
            (RAW_DIR / f"dam_{best['dam_id_used']}.json").write_text(
                json.dumps({"name": name, **best}, ensure_ascii=False), encoding="utf-8")
            out["dams"][name] = {"basin": c["basin"], "normal_storage": c["normal_storage"], **best}
        print(f"  {name}: {('ลึกถึง ' + str(out['dams'][name].get('first_year'))) if out['dams'][name].get('first_year') else 'ไม่มีข้อมูล'}", flush=True)
        OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(0.1)

    # MD: ตาราง 2554 vs 2569 ทุกเขื่อน
    lines = ["# URC compliance ทุกเขื่อนผู้สมัคร — เทียบ 2554 vs 2569 (H1 benchmark)", "",
             "> สร้างโดย `analysis/goal6_dam_history_all.py` · เทมเพลต URC = curve จริง (ยืนยันไขว้ 5,025 แถว)", "",
             "| เขื่อน | ลุ่ม | เก็บปกติ | 2554: เกิน URC (ปี/ก.ย.–ต.ค.) | 2554 เก็บพีค | 2569: เกิน URC (ก.ย.–ต.ค.) | 2569 เก็บพีค |", "|---|---|---|---|---|---|---|"]
    for name, rec in sorted(out["dams"].items(), key=lambda kv: -(kv[1].get("normal_storage") or 0)):
        ys = rec.get("years", [])
        r11 = next((r for r in ys if r["year"] == 2011), None)
        r26 = next((r for r in ys if r["year"] == 2026), None)
        ns = rec.get("normal_storage")
        f = lambda r, k: (r[k] if r else "—")
        pct11 = f" ({r11['max_storage']/ns*100:.0f}%)" if r11 and r11.get("max_storage") and ns else ""
        pct26 = f" ({r26['max_storage']/ns*100:.0f}%)" if r26 and r26.get("max_storage") and ns else ""
        lines.append(
            f"| {name} | {rec.get('basin', '')} | {ns or '—'} | "
            f"{f(r11, 'days_over_urc')} / {f(r11, 'days_over_urc_sep_oct')} | {f(r11, 'max_storage')}{pct11} | "
            f"{f(r26, 'days_over_urc_sep_oct')} | {f(r26, 'max_storage')}{pct26} |"
        )
    lines += ["", "## สิ่งที่เห็นจากตาราง (จะเขียนเต็มในรายงานที่ 4)", "",
              "- 2554: เขื่อนระบบเจ้าพระยาเต็มเกิน URC จริง (ภูมิพล 127 วัน · ป่าสัก 241 วัน) · ระบบ กฟผ. 0 วัน",
              "- 2569: ระลอกเดียวปลาย ก.ย. — เขื่อนเกิน URC 9 แห่งกระจายหลายลุ่ม",
              ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()