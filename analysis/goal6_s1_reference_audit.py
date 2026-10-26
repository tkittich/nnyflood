"""ตรวจฉากอ้างอิงของแผนที่น้ำเรดาร์เป้าหมาย 6 ขั้นที่ 2 — กลุ่มที่อ้างอิงถ่ายระหว่างเหตุการณ์ (วินิจฉัยเท่านั้น)

กติกาตั้งก่อนดูผล: docs/S1_REFERENCE_AUDIT_PREREG.md · ไม่แก้ขั้นที่ 2 ไม่แก้ canonical ของเป้าหมาย 6
  queue   ค้นคลัง CDSE หาฉากอ้างอิงก่อน 24 ก.ย. ของวงโคจรเดียวกัน เขียนคิวฉากที่ยังไม่มีบนดิสก์
  process ลงพิกัดฉากอ้างอิงใหม่ (ฟังก์ชันขั้นที่ 1) แล้วตัดน้ำซ้ำด้วยกฎตรึงเดิม เทียบผลเดิม
ดาวน์โหลดด้วย: python analysis/goal6_s1_download.py --queue data/22_goal6_network/raw/s1_audit/s1_audit_queue.json --dest data/22_goal6_network/raw/s1_audit
รัน: python analysis/goal6_s1_reference_audit.py queue | process
ผลลัพธ์: data/22_goal6_network/raw/s1_audit/s1_audit_queue.json · analysis/goal6/s1_reference_audit.json
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal7_s1_chachoengsao_recent import query_aoi, rel_orbit, start_of  # noqa: E402  (ฟังก์ชันร่วม: เลขวงโคจรสัมพัทธ์/เวลาจากชื่อฉาก)

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "data/22_goal6_network/derived/s1_stage2/summary.json"
ST1_OLD = ROOT / "data/22_goal6_network/derived/s1_stage1"
ST1_NEW = ROOT / "data/22_goal6_network/derived/s1_audit_stage1"
RAWS = [ROOT / "data/22_goal6_network/raw/s1_2026", ROOT / "data/22_goal6_network/raw/s1_recent", ROOT / "data/22_goal6_network/raw/s1_audit"]
RAW_NEW = RAWS[2]
QUEUE = RAW_NEW / "s1_audit_queue.json"
OUT = ROOT / "analysis/goal6/s1_reference_audit.json"
EVENT_START = "20260924"                    # ฉากอ้างอิงถ่ายตั้งแต่วันนี้ = กลุ่มอ้างอิงเหตุการณ์
PRE_BEFORE = "2026-09-24T00:00:00.000Z"
CELL_KM2 = 0.0009
MATERIAL_PCT = 10.0                          # ป้ายอ่านตารางเท่านั้น ไม่ใช่เกณฑ์ผ่าน/ตก
LABELS = {"pasak": "ป่าสัก", "maeklong": "แม่กลอง", "ping_cp": "ปิง–เจ้าพระยาตอนบน", "thachin": "ท่าจีน",
          "bp_prach": "ลุ่มบางปะกง (นครนายก–ปราจีนบุรี)", "bkk_lower": "ลุ่มเจ้าพระยาตอนล่าง–กทม.–สมุทรปราการ"}


def event_ref_groups() -> list[dict]:
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    out = []
    for b, v in s.items():
        for hh, t in v["tracks"].items():
            ref = t["reference"]
            if re.search(r"_(\d{8})T", ref).group(1) >= EVENT_START:
                out.append({"basin": b, "hh": hh, "old_ref": ref, "rel": rel_orbit(ref),
                            "scenes": [r["scene"] for r in v["scenes"] if r["track"] == hh]})
    return out


def basin_pre_scenes(basin: str) -> list[dict]:
    import goal6_s1_queue as q
    bbox = q.BASINS[LABELS[basin]]
    return query_aoi(q.polygon_wkt(bbox), "2026-08-25T00:00:00.000Z", PRE_BEFORE)


def build_queue() -> None:
    groups = event_ref_groups()
    have = {p.name for d in RAWS if d.exists() for p in d.glob("*.SAFE")}
    cache, need, plan = {}, {}, []
    for g in groups:
        pre = cache.setdefault(g["basin"], basin_pre_scenes(g["basin"]))
        ps = [p for p in pre if rel_orbit(p["Name"]) == g["rel"]]
        if not ps:
            plan.append({**g, "new_ref": None})
            continue
        day = max(start_of(p["Name"])[:10] for p in ps)
        pick = [p["Name"] for p in ps if start_of(p["Name"])[:10] == day]
        plan.append({**g, "new_ref": pick, "new_ref_day": day})
        for p in ps:
            if p["Name"] in pick and p["Name"] not in have:
                need[p["Name"]] = {"name": p["Name"], "start": start_of(p["Name"]), "content_length_mb": round(p.get("ContentLength", 0) / 1e6)}
    RAW_NEW.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps({"note": "คิวตามกติกา docs/S1_REFERENCE_AUDIT_PREREG.md", "basins": {"ตรวจฉากอ้างอิง": sorted(need.values(), key=lambda x: x["name"][17:])}, "plan": plan},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"กลุ่มอ้างอิงเหตุการณ์ {len(groups)} · ฉากที่ต้องโหลด {len(need)} ({sum(x['content_length_mb'] for x in need.values()) / 1e3:.1f} GB)")
    for p in plan:
        print(p["basin"], p["hh"], "rel", p["rel"], "->", None if not p["new_ref"] else p["new_ref_day"], "n", 0 if not p["new_ref"] else len(p["new_ref"]))


def scene_dir(name: str) -> Path | None:
    for d in RAWS:
        if (d / name).exists():
            return d
    return None


def load_db(basin: str, tag: str, pol: str):
    for d in (ST1_NEW / basin, ST1_OLD / basin):
        p = d / f"{tag}_{pol}_db.npy"
        if p.exists():
            return np.load(p)
    return None


def mosaic(basin: str, tags: list[str], pol: str):
    out = None
    for t in tags:
        a = load_db(basin, t, pol)
        if a is None:
            return None
        out = a if out is None else np.where(np.isfinite(out), out, a)
    return out


def process() -> None:
    import goal6_s1_stage1 as s1
    from s1_change_detect import detect
    plan = json.loads(QUEUE.read_text(encoding="utf-8"))["plan"]
    for p in plan:
        for b in {p["basin"]}:
            (ST1_NEW / b).mkdir(parents=True, exist_ok=True)
            if not (ST1_NEW / f"grid_{b}.json").exists():
                shutil.copy(ST1_OLD / f"grid_{b}.json", ST1_NEW / f"grid_{b}.json")
    s1.OUT = ST1_NEW
    for p in plan:                                           # ลงพิกัดฉากอ้างอิงใหม่บนกริดของลุ่ม
        for name in p["new_ref"] or []:
            tag = name.replace(".SAFE", "")
            if load_db(p["basin"], tag, "vh") is None:
                d = scene_dir(name)
                if d is None:
                    print("ไม่พบฉาก", name, flush=True)
                    continue
                s1.RAW_S1 = d
                print(s1.process_job(p["basin"], name), flush=True)
    rows, per_basin = [], defaultdict(lambda: {"old_max": 0.0, "new_max": 0.0, "old_arg": None, "new_arg": None})
    for p in plan:
        b = p["basin"]
        base = {"basin": b, "hh": p["hh"], "rel_orbit": p["rel"], "old_ref": p["old_ref"][12:27]}
        refs = [n.replace(".SAFE", "") for n in p["new_ref"] or []]
        if not refs or any(load_db(b, t, "vh") is None for t in refs):
            rows.append({**base, "status": "no_pre_event_reference"})
            continue
        lowland = np.load(ST1_OLD / f"mask_lowland_{b}.npy")
        pre_vh, pre_vv = mosaic(b, refs, "vh"), mosaic(b, refs, "vv")
        for sc in p["scenes"]:
            post_vh, post_vv = load_db(b, sc, "vh"), load_db(b, sc, "vv")
            w = detect(pre_vh, post_vh, pre_vv, post_vv, lowland)
            new_km2 = round(float(w.sum()) * CELL_KM2, 1)
            old = json.loads((ROOT / f"data/22_goal6_network/derived/s1_stage2/{b}/{sc}_stats.json").read_text(encoding="utf-8"))["water_km2_lowland"]
            rows.append({**base, "status": "ok", "scene": sc[12:27], "new_ref_day": p["new_ref_day"], "old_km2": old, "new_km2": new_km2,
                         "diff_km2": round(new_km2 - old, 1)})
            pb = per_basin[b]
            if old > pb["old_max"]:
                pb["old_max"], pb["old_arg"] = old, f"{p['hh']} {sc[12:27]}"
            if new_km2 > pb["new_max"]:
                pb["new_max"], pb["new_arg"] = new_km2, f"{p['hh']} {sc[12:27]}"
            print(rows[-1], flush=True)
    # ค่าสูงสุดต่อลุ่มรวมกลุ่มที่ไม่ถูกตรวจ (ใช้ค่าเผยแพร่เดิมของทุกฉากในลุ่ม)
    summ = json.loads(SUMMARY.read_text(encoding="utf-8"))
    basin_view = {}
    for b, v in summ.items():
        pub_max = max((r["water_km2_lowland"] for r in v["scenes"]), default=0.0)
        audited = per_basin.get(b)
        untouched = max((r["water_km2_lowland"] for r in v["scenes"] if (r["track"]) not in {p["hh"] for p in plan if p["basin"] == b}), default=0.0)
        new_max = max(untouched, audited["new_max"]) if audited else pub_max
        basin_view[b] = {"published_max_km2": pub_max, "audited_max_km2": round(new_max, 1),
                         "change_pct": round(100 * (new_max - pub_max) / pub_max, 1) if pub_max else None,
                         "material_label": bool(pub_max and abs(100 * (new_max - pub_max) / pub_max) > MATERIAL_PCT),
                         "untouched_groups_max_km2": untouched, "audited_groups": audited}
    OUT.write_text(json.dumps({"rule": "docs/S1_REFERENCE_AUDIT_PREREG.md", "scenes": rows, "per_basin": basin_view}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("เขียน", OUT)


if __name__ == "__main__":
    {"queue": build_queue, "process": process}[sys.argv[1]]()
