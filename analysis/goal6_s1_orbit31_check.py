"""ตรวจค่าควบคุมวงโคจร 31 ด้วยฉากอ้างอิงที่สาม — ขั้นคิว: ค้นคลัง CDSE อย่างเดียว ไม่ดาวน์โหลด ไม่คำนวณ

กติกาตั้งก่อนค้นคลัง: docs/S1_ORBIT31_CONTROL_PREREG.md §2 (alt2 = ฉากวงโคจร 31 วัน UTC ล่าสุดที่เก่ากว่าวันฉากทางเลือกอย่างน้อย 6 วัน ตั้งแต่ 25 ส.ค.)
ขั้นคำนวณ (M0–M2) ทำหลังเจ้าของโครงการอนุมัติรายการฉากและขนาด (อนุมัติ 28 ต.ค. 69)
รัน: python analysis/goal6_s1_orbit31_check.py queue | download-queue | process | compute
ผลลัพธ์: data/22_goal6_network/raw/s1_audit/s1_audit_queue_orbit31.json · analysis/goal6/s1_orbit31_check.json/.md
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
from goal6_s1_reference_audit import LABELS, basin_pre_scenes  # noqa: E402
from s1_orbit import rel_orbit, start_of  # noqa: E402

ORBIT = 31
MIN_DAYS = 6
RAW = ROOT / "data/22_goal6_network/raw/s1_audit"
OUT = RAW / "s1_audit_queue_orbit31.json"
BASINS = ["bp_prach", "pasak", "maeklong", "thachin", "ping_cp", "bkk_lower"]


def alt_day_of(basin: str) -> str:
    """วันฉากทางเลือกเดิมของวงโคจร 31 (UTC) จากผลความไวเดิม"""
    f = ROOT / "analysis/goal6" / ("s1_ref_sensitivity.json" if basin == "bp_prach" else f"s1_ref_sensitivity_{basin}.json")
    rows = [p for p in json.loads(f.read_text(encoding="utf-8"))["passes"] if p["rel_orbit"] == ORBIT]
    return rows[0]["alt_ref_day"]


def queue() -> None:
    have = {p.name for p in RAW.glob("*.SAFE")}
    out = {}
    for b in BASINS:
        alt = dt.date.fromisoformat(alt_day_of(b))
        ps = [p for p in basin_pre_scenes(b) if rel_orbit(p["Name"]) == ORBIT]
        cand = [p for p in ps if (alt - dt.date.fromisoformat(start_of(p["Name"])[:10])).days >= MIN_DAYS]
        if not cand:
            out[b] = {"alt_day_utc": alt.isoformat(), "alt2_day_utc": None, "scenes": [], "orbit31_days_seen_utc": sorted({start_of(p["Name"])[:10] for p in ps})}
            continue
        day = max(start_of(p["Name"])[:10] for p in cand)
        pick = sorted([p for p in cand if start_of(p["Name"])[:10] == day], key=lambda p: p["Name"])
        out[b] = {"alt_day_utc": alt.isoformat(), "alt2_day_utc": day, "orbit31_days_seen_utc": sorted({start_of(p["Name"])[:10] for p in ps}),
                  "scenes": [{"name": p["Name"], "start_utc": start_of(p["Name"]), "size_mb": round(p.get("ContentLength", 0) / 1e6), "on_disk": p["Name"] in have} for p in pick]}
    uniq = {s["name"]: s for v in out.values() for s in v["scenes"]}
    OUT.write_text(json.dumps({"note": "คิวตามกติกา docs/S1_ORBIT31_CONTROL_PREREG.md §2 — ค้นคลังอย่างเดียว ยังไม่ดาวน์โหลด", "basins": out,
                               "unique_scenes": len(uniq), "unique_size_mb": sum(s["size_mb"] for s in uniq.values()),
                               "to_download": sorted(n for n, s in uniq.items() if not s["on_disk"])}, ensure_ascii=False, indent=1), encoding="utf-8")
    for b, v in out.items():
        print(LABELS[b], "· alt2", v["alt2_day_utc"], "·", len(v["scenes"]), "ฉาก", sum(s["size_mb"] for s in v["scenes"]), "MB")
    print("รวมไม่ซ้ำ", len(uniq), "ฉาก", sum(s["size_mb"] for s in uniq.values()), "MB · ต้องโหลด", sum(1 for s in uniq.values() if not s["on_disk"]))


def download_queue() -> Path:
    """คิวรูปแบบที่ goal6_s1_download.py อ่านได้ ({'basins': {กลุ่ม: [{name,start,content_length_mb}]}}) — ใช้หลังได้รับอนุมัติเท่านั้น"""
    q = json.loads(OUT.read_text(encoding="utf-8"))
    scenes = {s["name"]: s for v in q["basins"].values() for s in v["scenes"]}
    p = RAW / "s1_audit_queue_orbit31_dl.json"
    p.write_text(json.dumps({"note": "คิวดาวน์โหลดฉากที่สาม วงโคจร 31 (อนุมัติ 28 ต.ค. 69)", "basins": {"orbit31": [
        {"name": n, "start": s["start_utc"], "content_length_mb": s["size_mb"]} for n, s in sorted(scenes.items())]}}, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def _job(args: tuple[str, str]) -> str:
    """1 งาน = 1 ฉาก บนกริด 1 ลุ่ม (รันในโพรเซสลูก — ตัวแปรโมดูลต้องตั้งในนี้ เพราะ Windows ไม่สืบทอดจากแม่)"""
    import goal6_s1_stage1 as s1
    from goal6_s1_reference_audit import ST1_NEW, scene_dir
    b, name = args
    s1.OUT = ST1_NEW
    s1.RAW_S1 = scene_dir(name)
    try:
        return s1.process_job(b, name)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR {b}/{name[:40]}: {type(exc).__name__} {str(exc)[:120]}"


def process(workers: int = 5) -> None:
    """ประมวลผลฉากที่สาม (geocode/calibrate เป็นกริดลุ่ม) ด้วยตัวประมวลผลเดิม — ขนานข้ามงาน (แต่ละงานใช้แรม ~5 GB)"""
    import shutil
    from multiprocessing import Pool

    from goal6_s1_reference_audit import ST1_NEW, ST1_OLD, load_db
    q = json.loads(OUT.read_text(encoding="utf-8"))["basins"]
    jobs = []
    for b, v in q.items():
        (ST1_NEW / b).mkdir(parents=True, exist_ok=True)
        if not (ST1_NEW / f"grid_{b}.json").exists():
            shutil.copy(ST1_OLD / f"grid_{b}.json", ST1_NEW / f"grid_{b}.json")
        jobs += [(b, s["name"]) for s in v["scenes"] if load_db(b, s["name"].replace(".SAFE", ""), "vh") is None]
    print(f"งานที่เหลือ {len(jobs)} (โพรเซส {workers})", flush=True)
    with Pool(workers) as pool:
        for res in pool.imap_unordered(_job, jobs):
            print(res, flush=True)


def compute() -> None:
    """M0–M2 ต่อลุ่ม ด้วยกฎตรวจจับเดิม (นำ detect/mosaic_db มาใช้ซ้ำ) — กติกา §3"""
    import numpy as np

    from goal6_s1_reference_audit import queue_sens_path
    from goal6_s1_stage2_water import mosaic_db
    from s1_change_detect import detect
    cell = 0.0009
    summ = json.loads((ROOT / "data/22_goal6_network/derived/s1_stage2/summary.json").read_text(encoding="utf-8"))
    q = json.loads(OUT.read_text(encoding="utf-8"))["basins"]
    rows = []
    for b in BASINS:
        row = {"basin": b, "label": LABELS[b]}
        v = q[b]
        if not v["scenes"]:
            rows.append({**row, "status": "no_third_scene"})
            continue
        P = [r for r in summ[b]["scenes"] if rel_orbit(r["scene"]) == ORBIT and r["reference"] == r["scene"]]
        plan = {p["rel"]: p for p in json.loads(queue_sens_path(b).read_text(encoding="utf-8"))["plan"]}
        S, T = plan[ORBIT]["alt_ref"], [s["name"].replace(".SAFE", "") for s in v["scenes"]]
        low = np.load(ROOT / f"data/22_goal6_network/derived/s1_stage1/mask_lowland_{b}.npy")
        mos = {k: (mosaic_db(b, tags, "vh"), mosaic_db(b, tags, "vv")) for k, tags in (("P", P[0]["slices"]), ("S", S), ("T", T))}

        def run(post, pre):
            w = detect(pre[0], post[0], pre[1], post[1], low)
            ok = np.isfinite(pre[0]) & np.isfinite(post[0]) & np.isfinite(pre[1]) & np.isfinite(post[1]) & low
            return round(float(w.sum()) * cell, 1), round(float(ok.sum()) / float(low.sum()), 3)
        m0, c0 = run(mos["P"], mos["S"])
        m1, c1 = run(mos["P"], mos["T"])
        m2, c2 = run(mos["S"], mos["T"])
        stored = [x["alt_ref_km2"] for x in json.loads((ROOT / "analysis/goal6" / ("s1_ref_sensitivity.json" if b == "bp_prach" else f"s1_ref_sensitivity_{b}.json")).read_text(encoding="utf-8"))["passes"]
                  if x["rel_orbit"] == ORBIT and x["role"] == "control_primary_reference_pass"]
        alt2_ict = (dt.datetime.fromisoformat(min(s["start_utc"] for s in v["scenes"])) + dt.timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
        rows.append({**row, "status": "ok", "alt2_day_utc": v["alt2_day_utc"], "alt2_ict": alt2_ict, "n_slices_alt2": len(T), "M0_km2": m0, "M0_stored_km2": stored[0] if stored else None,
                     "M1_km2": m1, "M2_km2": m2, "valid_frac": {"M0": c0, "M1": c1, "M2": c2},
                     "M1_over_M0": round(m1 / m0, 2) if m0 else None, "M2_over_M0": round(m2 / m0, 2) if m0 else None})
        print(rows[-1], flush=True)
    ok = [r for r in rows if r["status"] == "ok"]
    out = {"rule": "docs/S1_ORBIT31_CONTROL_PREREG.md", "n_basins": len(ok), "rows": rows,
           "M1_gt_M2": sum(1 for r in ok if r["M1_km2"] > r["M2_km2"]), "M1_lt_M2": sum(1 for r in ok if r["M1_km2"] < r["M2_km2"]),
           "M1_eq_M2": sum(1 for r in ok if r["M1_km2"] == r["M2_km2"])}
    (ROOT / "analysis/goal6/s1_orbit31_check.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# ค่าควบคุมวงโคจร 31 ด้วยฉากที่สาม (26 ส.ค.)", "", "กติกา `docs/S1_ORBIT31_CONTROL_PREREG.md` · บรรยายเท่านั้น · ตร.กม. ในที่ราบต่ำ", "",
          "| ลุ่ม | M0 (20 ก.ย. เทียบ 8 ก.ย.) | M1 (20 ก.ย. เทียบ 26 ส.ค.) | M2 (8 ก.ย. เทียบ 26 ส.ค.) | M1÷M0 | M2÷M0 |", "|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['label']} | " + (f"{r['M0_km2']} | {r['M1_km2']} | {r['M2_km2']} | {r['M1_over_M0']} | {r['M2_over_M0']} |" if r["status"] == "ok" else "ไม่มีฉากที่สาม | | | | |"))
    md += ["", f"จำนวนลุ่มที่ M1 > M2: {out['M1_gt_M2']} · M1 < M2: {out['M1_lt_M2']} · เท่ากัน: {out['M1_eq_M2']}", ""]
    (ROOT / "analysis/goal6/s1_orbit31_check.md").write_text(chr(10).join(md), encoding="utf-8")


if __name__ == "__main__":
    cmd = sys.argv[1:] or [""]
    {"queue": queue, "download-queue": lambda: print(download_queue()), "process": lambda: process(int(cmd[1]) if len(cmd) > 1 else 5), "compute": compute}.get(cmd[0], lambda: sys.exit("ใช้: queue | download-queue | process | compute"))()
