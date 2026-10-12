"""น้ำเข้า–ปล่อย–เก็บ รายเขื่อน 2554 vs 2569 เทียบประวัติ 22 ปี — แยก "ฝน/น้ำเข้า" ออกจาก "สถานะ/การเดินเขื่อน"
(รีวิว Sonnet 12 ต.ค. 69 · H4 ข้อ "ข้อมูลน้ำเข้าอ่างปี 2554 ยังไม่ได้ใช้")

ข้อมูล: คลังข้อมูลน้ำแห่งชาติ analyst/dam_yearly_graph (dam_inflow · dam_released · dam_storage รายวัน) 2005–2026
ต่อเขื่อน 24 แห่ง → raw/dam_flows/dam_<id>.json (disk-only + SHA-256)

ตัวชี้ต่อเขื่อน-ปี (หน้าต่าง ก.ย.1–ต.ค.9 = "W" เดียวกับวันเกินเส้นกำกับ · ฤดู ก.ค.1–ต.ค.9 = "S"):
  น้ำเข้า S/W (ล้าน ลบ.ม.) · ปล่อย W · เก็บ ณ 1 ก.ย. เทียบเส้นกำกับบน · วันเกินเส้นกำกับ W ·
  สัดส่วนที่อ่างเก็บไว้ = (น้ำเข้า W − ปล่อย W) / น้ำเข้า W · พื้นที่ว่างใต้ความจุเก็บปกติ ณ 1 ก.ย.
แล้วเทียบอันดับน้ำเข้าของ 2554/2569 ในประวัติ + จัดกลุ่ม "เกินเส้นกำกับทั้งที่น้ำเข้าไม่สูง"

ผลลัพธ์: analysis/goal6/dam_inflow.json/.md
รัน: python analysis/goal6_dam_inflow.py [--refresh] [--workers N]
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import goal6_screen_basins as g6  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HIST = ROOT / "analysis/goal6/dam_history_all.json"
RAW = ROOT / "data/22_goal6_network/raw/dam_flows"
OUT_JSON = ROOT / "analysis/goal6/dam_inflow.json"
OUT_MD = ROOT / "analysis/goal6/dam_inflow.md"
YEARS = range(2005, 2027)
S_FROM, W_FROM, END = "07-01", "09-01", "10-09"
TYPES = ("dam_storage", "dam_inflow", "dam_released")


def fetch_dam(dam_id: int) -> dict:
    p = RAW / f"dam_{dam_id}.json"
    if p.exists() and "--refresh" not in sys.argv:
        return json.loads(p.read_text(encoding="utf-8"))
    out: dict = {"dam_id": dam_id, "fetched": time.strftime("%Y-%m-%d"), "years": {}}
    for y in YEARS:
        rec = {}
        for t in TYPES:
            rows = g6.fetch_dam_series(dam_id, t, str(y)) or []
            rec[t] = {dt: v for dt, v in rows if dt}
            time.sleep(0.05)
        if any(rec[t] for t in TYPES):
            out["years"][str(y)] = rec
    RAW.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def vals(d: dict, y: int, a: str, b: str):
    return [v for k, v in sorted(d.items()) if f"{y}-{a}" <= k[:10] <= f"{y}-{b}" and v is not None]


def metrics(rec: dict, y: int, urc: dict, ns: float) -> dict | None:
    sto, inf, rel = rec["dam_storage"], rec["dam_inflow"], rec["dam_released"]
    w_in, w_rel = vals(inf, y, W_FROM, END), vals(rel, y, W_FROM, END)
    s_in = vals(inf, y, S_FROM, END)
    w_days = (np.datetime64(f"{y}-{END}") - np.datetime64(f"{y}-{W_FROM}")).astype(int) + 1
    s_days = (np.datetime64(f"{y}-{END}") - np.datetime64(f"{y}-{S_FROM}")).astype(int) + 1
    if len(w_in) < 0.8 * w_days or len(s_in) < 0.8 * s_days or len(w_rel) < 0.8 * w_days:
        return None
    # ปริมาณน้ำเข้า/ปล่อยรายวันเป็น ล้าน ลบ.ม./วัน (ค่าวันที่ขาดถูกชดเชยด้วยค่าเฉลี่ยวัน)
    in_w = float(np.mean(w_in) * w_days)
    rel_w = float(np.mean(w_rel) * w_days)
    in_s = float(np.mean(s_in) * s_days)
    s0 = next((v for k, v in sorted(sto.items()) if k[:10] >= f"{y}-{W_FROM}" and v is not None), None)
    if s0 is None:
        return None
    u0 = urc.get(W_FROM)
    over = sum(1 for k, v in sto.items() if f"{y}-{W_FROM}" <= k[:10] <= f"{y}-{END}" and v is not None
               and urc.get(k[5:10]) is not None and v > urc[k[5:10]])
    return {
        "inflow_season_mcm": round(in_s, 1), "inflow_window_mcm": round(in_w, 1), "release_window_mcm": round(rel_w, 1),
        "retained_share": round((in_w - rel_w) / in_w, 3) if in_w > 0 else None,
        "peak_inflow": round(float(max(w_in)), 1), "peak_release": round(float(max(w_rel)), 1),
        "storage_sep1": round(float(s0), 1), "urc_sep1": round(float(u0), 1) if u0 else None,
        "sep1_over_urc_mcm": round(float(s0 - u0), 1) if u0 else None,
        "headroom_normal_sep1_mcm": round(float(ns - s0), 1), "days_over_urc_window": over,
    }


def main() -> None:
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    hist = json.loads(HIST.read_text(encoding="utf-8"))["dams"]
    items = [(n, int(r["dam_id_used"])) for n, r in hist.items() if r.get("dam_id_used")]
    print(f"เขื่อน {len(items)} · ดึง/อ่านแคช ...", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        data = dict(zip([n for n, _ in items], ex.map(lambda x: fetch_dam(x[1]), items)))

    res: dict = {"window": f"{W_FROM}..{END}", "season": f"{S_FROM}..{END}", "dams": {}}
    for name, did in items:
        h = hist[name]
        urc = h["urc_mmdd"]
        ns = h["normal_storage"]
        per = {}
        for y_str, rec in data[name]["years"].items():
            m = metrics(rec, int(y_str), urc, ns)
            if m:
                per[int(y_str)] = m
        if 2011 not in per and 2026 not in per:
            res["dams"][name] = {"note": "ไม่มีข้อมูลน้ำเข้า/ปล่อยพอ", "years": len(per)}
            continue
        in_s = {y: m["inflow_season_mcm"] for y, m in per.items()}
        def rank(y):
            return sorted(in_s.values(), reverse=True).index(in_s[y]) + 1 if y in in_s else None
        r = {"basin": h["basin"], "normal_storage": ns, "n_years": len(per),
             "median_inflow_season": round(float(np.median(list(in_s.values()))), 1),
             "y2554": per.get(2011), "y2569": per.get(2026),
             "inflow_rank2554": rank(2011), "inflow_rank2569": rank(2026)}
        # ความสัมพันธ์น้ำเข้ากับวันเกินเส้นทั่วประวัติ (Spearman) — บอกว่าอ่างนี้ "ตามน้ำเข้า" แค่ไหน
        ys = sorted(per)
        a = np.array([per[y]["inflow_season_mcm"] for y in ys])
        b = np.array([per[y]["days_over_urc_window"] for y in ys])
        if len(ys) >= 8 and b.std() > 0:
            ra, rb = a.argsort().argsort(), b.argsort().argsort()
            r["spearman_inflow_vs_days_over"] = round(float(np.corrcoef(ra, rb)[0, 1]), 2)
        else:
            r["spearman_inflow_vs_days_over"] = None
        r["years_over_any_window"] = sum(1 for y in ys if per[y]["days_over_urc_window"] > 0)
        res["dams"][name] = r

    OUT_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    md = ["# น้ำเข้า–ปล่อย–เก็บ รายเขื่อน: 2554 เทียบ 2569 เทียบประวัติ 22 ปี", "",
          "> หน้าต่างน้ำเข้าฤดู 1 ก.ค.–9 ต.ค. · หน้าต่างวันเกินเส้นกำกับ 1 ก.ย.–9 ต.ค. · อันดับน้ำเข้า 1 = สูงสุดในปีที่มีข้อมูล · "
          "สัดส่วนที่อ่างเก็บ = (น้ำเข้า − ปล่อย) / น้ำเข้า ในหน้าต่างก.ย.–ต.ค.", "",
          "| เขื่อน | ปีที่มีข้อมูล | น้ำเข้าฤดู 2554 (อันดับ) | น้ำเข้าฤดู 2569 (อันดับ) | เก็บ 1 ก.ย. เหนือเส้น 2554 / 2569 (ล้าน ลบ.ม.) | วันเกินเส้น 2554 / 2569 | เก็บไว้ได้ 2554 / 2569 | ρ(น้ำเข้า, วันเกิน) |",
          "|---|---|---|---|---|---|---|---|"]
    for name, r in sorted(res["dams"].items(), key=lambda kv: -(kv[1].get("normal_storage") or 0)):
        if "y2554" not in r:
            continue
        a, b = r["y2554"], r["y2569"]
        f = lambda m, k: (m[k] if m else "—")
        md.append(f"| {name} | {r['n_years']} | {f(a, 'inflow_season_mcm')} ({r['inflow_rank2554'] or '—'}) | "
                  f"{f(b, 'inflow_season_mcm')} ({r['inflow_rank2569'] or '—'}) | "
                  f"{f(a, 'sep1_over_urc_mcm')} / {f(b, 'sep1_over_urc_mcm')} | "
                  f"{f(a, 'days_over_urc_window')} / {f(b, 'days_over_urc_window')} | "
                  f"{f(a, 'retained_share')} / {f(b, 'retained_share')} | {r['spearman_inflow_vs_days_over']} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(OUT_MD.read_text(encoding="utf-8")[:3500])


if __name__ == "__main__":
    main()
