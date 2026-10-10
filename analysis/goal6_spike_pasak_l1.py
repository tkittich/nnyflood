"""เป้าหมาย 6 — spike ลุ่มแรก L1: ป่าสัก (ผู้ใช้ยืนยันรอบแรก 5 ลุ่ม 10 ต.ค. 69)

ทำตามคำถาม Q2 (URC compliance) + Q3/Q4 (timeline เหตุการณ์ + lag เชิงหยาบ) ของ GOAL6_PLAN §7.1:

1. เขื่อนป่าสักชลสิทธิ์ (dam_id 11) — ประวัติรายวันเดินปีถอยจนว่าง 2 ปีต่อเนื่อง
   (storage/inflow/released + URC เทมเพลตเดือน-วัน) → สถิติ "วันเกิน URC" รายปี
   เทียบรูปแบบเดียวกันกับขุนด่านฯ จาก analysis/dam_khun_dan_daily_2013_2026.csv
2. จุดวัดลุ่มป่าสัก (จาก goal6_basin_readiness.json) — รายชั่วโมง 1 ก.ค.–9 ต.ค. 69
   → ระดับสูงสุด/เวลาพีค + lag เชิงหยาบ ท้ายเขื่อน(S.28)→ท้ายเขื่อนพระรามหก(S.26)
3. ฝน NASA POWER รายวัน 2026 2 จุด (ลุ่มบน 15.75N/100.9E · อยุธยา 14.35N/100.55E)
   → ฝนสะสม ก.ย. + 7 วันสูงสุด เทียบเกณฑ์เหตุการณ์นครนายก (248 มม./7 วัน)

ผลลัพธ์: analysis/goal6_spike_pasak_findings.md + goal6_spike_pasak.json
raw: data/22_goal6_network/raw/spike_pasak/
รัน: python analysis/goal6_spike_pasak_l1.py
"""

from __future__ import annotations

import csv
import json
import time
import urllib.request
from pathlib import Path

import goal6_screen_basins as g6

ROOT = Path(__file__).resolve().parent.parent
DAM_ID = 11
DAM_NAME = "ป่าสักชลสิทธิ์ (พระรามหก)"
NORMAL_STORAGE = 872.0  # ลลบ.ม. จาก goal6_dam_candidates.json
KHUNDAN_CSV = ROOT / "analysis/dam_khun_dan_daily_2013_2026.csv"
READINESS = ROOT / "analysis/goal6_basin_readiness.json"
RAW_DIR = ROOT / "data/22_goal6_network/raw/spike_pasak"
OUT_JSON = ROOT / "analysis/goal6_spike_pasak.json"
OUT_MD = ROOT / "analysis/goal6_spike_pasak_findings.md"
WINDOW = ("2026-07-01", "2026-10-09")

POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
    "?parameters=PRECTOTCORR&community=RE&format=JSON"
    "&longitude={lon}&latitude={lat}&start=20260101&end=20261009"
)
RAIN_POINTS = {"ลุ่มบนป่าสัก (15.75N/100.9E)": (100.9, 15.75), "อยุธยา (14.35N/100.55E)": (100.55, 14.35)}


def dam_walk_history() -> dict:
    """เดินปีถอยจนว่าง 2 ปีต่อเนื่อง · คืน {year: {date: {'storage','inflow','released'}}} + URC เดือน-วัน"""
    years: dict[str, dict[str, dict]] = {}
    empty_streak = 0
    urc_mmdd: dict[str, float] = {}
    for y in range(2026, 2004, -1):
        storage = g6.fetch_dam_series(DAM_ID, "dam_storage", str(y))
        if not storage:
            empty_streak += 1
            print(f"  dam {DAM_ID} ปี {y}: ว่าง ({empty_streak}/2)")
            if empty_streak >= 2:
                break
            continue
        empty_streak = 0
        inflow = g6.fetch_dam_series(DAM_ID, "dam_inflow", str(y)) or []
        released = g6.fetch_dam_series(DAM_ID, "dam_released", str(y)) or []
        if not urc_mmdd:
            for dt, v in g6.fetch_dam_urc(DAM_ID, "2026"):
                if dt and len(dt) >= 10:
                    urc_mmdd[dt[5:]] = v
        rows = {dt: {"storage": v, "inflow": None, "released": None} for dt, v in storage}
        for dt, v in inflow:
            if dt in rows:
                rows[dt]["inflow"] = v
        for dt, v in released:
            if dt in rows:
                rows[dt]["released"] = v
        years[str(y)] = rows
        print(f"  dam {DAM_ID} ปี {y}: {len(rows)} วัน")
        time.sleep(0.08)
    return {"years": years, "urc_mmdd": urc_mmdd}


def urc_stats(rows: dict[str, dict], urc_mmdd: dict[str, float]) -> dict:
    over_total = over_sep_oct = over_aug_sep = 0
    for dt, r in rows.items():
        v, u = r.get("storage"), urc_mmdd.get(dt[5:5 + 5])
        if v is None or u is None:
            continue
        if v > u:
            over_total += 1
            if "09-01" <= dt[5:10] <= "10-09":
                over_sep_oct += 1
            if "08-01" <= dt[5:10] <= "09-30":
                over_aug_sep += 1
    return {"days_over_urc": over_total, "days_over_urc_sep_oct": over_sep_oct, "days_over_urc_aug_sep": over_aug_sep}


def khundan_stats() -> list[dict]:
    if not KHUNDAN_CSV.exists():
        return []
    out: dict[str, dict] = {}
    with open(KHUNDAN_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            dt = row["date"]
            st, u = row["storage_mcm"], row["upper_rule_curve_mcm"]
            if not st or not u:
                continue
            y = dt[:4]
            rec = out.setdefault(y, {"days_over_urc": 0, "days_over_urc_sep_oct": 0, "days_over_urc_aug_sep": 0})
            if float(st) > float(u):
                rec["days_over_urc"] += 1
                if "09-01" <= dt[5:10] <= "10-09":
                    rec["days_over_urc_sep_oct"] += 1
                if "08-01" <= dt[5:10] <= "09-30":
                    rec["days_over_urc_aug_sep"] += 1
    return [{"dam": "ขุนด่านปราการชล", "year": y, **v} for y, v in sorted(out.items())]


def fetch_station_year(sid: int, code: str) -> dict:
    u = (
        f"{g6.API_BASE}public/waterlevel_graph?station_type=tele_waterlevel"
        f"&station_id={sid}&start_date={WINDOW[0]}&end_date={WINDOW[1]}"
    )
    data = g6.get_json(u).get("data") or {}
    vals = [(r.get("datetime"), g6.fnum(r.get("value")), g6.fnum(r.get("discharge"))) for r in data.get("graph_data") or []]
    vals = [x for x in vals if x[1] is not None]
    meta = {k: data.get(k) for k in ("min_bank", "warning_level", "critical_level", "ground_level", "qmax")}
    p = RAW_DIR / f"{sid}_{g6.sanitize(code)}_2026_hourly.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"station_id": sid, "code": code, "meta": meta, "graph_data": vals}, ensure_ascii=False), encoding="utf-8")
    peak = max(vals, key=lambda x: x[1]) if vals else (None, None, None)
    return {"station_id": sid, "code": code, "n": len(vals), "max": peak[1], "peak_dt": peak[0],
            "meta": meta, "raw": p.name}


def fetch_power(lon: float, lat: float) -> dict:
    req = urllib.request.Request(
        POWER_URL.format(lon=lon, lat=lat), headers={"User-Agent": "nnyflood-goal6/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        d = json.load(resp)
    series = d["properties"]["parameter"]["PRECTOTCORR"]
    daily = {f"{k[:4]}-{k[4:6]}-{k[6:8]}": v for k, v in series.items() if v >= 0}
    # 7 วันสูงสุด (window ปิดด้านหลัง)
    dates = sorted(daily)
    best, best_sum = None, -1.0
    for i in range(6, len(dates)):
        s = sum(daily[x] for x in dates[i - 6: i + 1] if daily[x] >= 0)
        if s > best_sum:
            best_sum, best = s, dates[i]
    sep_total = sum(v for dt, v in daily.items() if dt[:7] == "2026-09" and v >= 0)
    return {"daily": daily, "sep_total_mm": round(sep_total, 1), "best7_mm": round(best_sum, 1), "best7_end": best}


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out: dict = {"dam": DAM_NAME, "dam_id": DAM_ID, "normal_storage": NORMAL_STORAGE, "window": WINDOW}

    print("1) ประวัติเขื่อนป่าสัก...")
    hist = dam_walk_history()
    urc = hist["urc_mmdd"]
    per_year = []
    for y in sorted(hist["years"], reverse=True):
        rows = hist["years"][y]
        st = urc_stats(rows, urc)
        vals = [r["storage"] for r in rows.values() if r.get("storage") is not None]
        rel = [r["released"] for r in rows.values() if r.get("released") is not None]
        per_year.append({"year": y, "n_days": len(rows), "max_storage": max(vals) if vals else None,
                         "max_released": max(rel) if rel else None, **st})
    out["dam_years"] = per_year
    out["urc_mmdd"] = urc

    print("2) จุดวัดลุ่มป่าสัก (รายชั่วโมง 1 ก.ค.–9 ต.ค. 69)...")
    stations: list[dict] = []
    if READINESS.exists():
        rs = json.loads(READINESS.read_text(encoding="utf-8"))["basins"].get("pasak", {}).get("stations", [])
    else:
        rs = []
    if not rs:  # fallback จาก screen summary
        ss = json.loads((ROOT / "analysis/goal6_screen_2026_summary.json").read_text(encoding="utf-8"))["stations"]
        rs = [x for x in ss if x.get("basin") == "ลุ่มน้ำป่าสัก"]
    for st in rs:
        stations.append({**st, **fetch_station_year(st["id"], st["code"])})
        print(f"  {st['code']} {st['name'][:20]} -> n={stations[-1]['n']} max={stations[-1]['max']} @ {stations[-1]['peak_dt']}")
    out["stations"] = stations

    print("3) ฝน NASA POWER 2026...")
    rain = {}
    for label, (lon, lat) in RAIN_POINTS.items():
        rain[label] = fetch_power(lon, lat)
        print(f"  {label}: ก.ย. {rain[label]['sep_total_mm']} มม. · 7วันสูงสุด {rain[label]['best7_mm']} มม. ปลาย {rain[label]['best7_end']}")
    out["rain_2026"] = {k: {kk: vv for kk, vv in v.items() if kk != "daily"} for k, v in rain.items()}
    (RAW_DIR / "nasa_power_2026.json").write_text(json.dumps(rain, ensure_ascii=False), encoding="utf-8")

    out["khundan_compare"] = khundan_stats()
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # --- lag เชิงหยาบ ---
    s28 = next((s for s in stations if s["code"].startswith("S.28")), None)
    s26 = next((s for s in stations if s["code"].startswith("S.26")), None)
    lag = None
    if s28 and s26 and s28["peak_dt"] and s26["peak_dt"]:
        from datetime import datetime
        t1 = datetime.fromisoformat(s28["peak_dt"])
        t2 = datetime.fromisoformat(s26["peak_dt"])
        lag = round((t2 - t1).total_seconds() / 3600, 1)

    # --- findings MD ---
    ev = out["dam_years"][0] if out["dam_years"] else {}
    lines = [
        "# spike L1 ลุ่มแรก: ป่าสัก — ผลเบื้องต้น",
        "",
        f"> สร้างโดย `analysis/goal6_spike_pasak_l1.py` · เขื่อนป่าสักชลสิทธิ์/พระรามหก (dam_id 11, "
        f"เก็บปกติ {NORMAL_STORAGE:.0f} ลลบ.ม.) · หน้าต่างเหตุการณ์ {WINDOW[0]}..{WINDOW[1]}",
        "",
        "## 1. Q2 — URC compliance เขื่อนป่าสัก (เทียบขุนด่านฯ วิธีเดียวกัน)",
        "",
        "| ปี | วันเกิน URC (ทั้งปี) | ใน ก.ย.–ต.ค. | ใน ส.ค.–ก.ย. (กลางหน้าฝน) | เก็บสูงสุด |",
        "|---|---|---|---|---|",
    ]
    for r in sorted(out["dam_years"], key=lambda x: -int(x["year"])):
        lines.append(
            f"| {r['year']} | {r['days_over_urc']} | {r['days_over_urc_sep_oct']} | "
            f"{r['days_over_urc_aug_sep']} | {r['max_storage']} |"
        )
    lines += [
        "",
        "**เทียบขุนด่านฯ** (จาก `dam_khun_dan_daily_2013_2026.csv` — canonical: เกิน 12/14 ปี แต่กระจุก ต.ค.–ธ.ค.; "
        "กลางหน้าฝน ส.ค.–ก.ย. เฉพาะ 2561/2565/2567/2569):",
        "",
        "| ปี | ขุนด่านฯ วันเกิน URC (ทั้งปี) | กลางหน้าฝน ส.ค.–ก.ย. |",
        "|---|---|---|",
    ]
    for r in out["khundan_compare"]:
        lines.append(f"| {r['year']} | {r['days_over_urc']} | {r['days_over_urc_aug_sep']} |")
    lines += [
        "",
        "## 2. เหตุการณ์ ก.ย.–ต.ค. 69 — เขื่อน → จุดวัด",
        "",
        f"- เขื่อน 2569: เก็บสูงสุด **{ev.get('max_storage')}** ลลบ.ม. · วันเกิน URC ก.ย.–ต.ค. "
        f"**{ev.get('days_over_urc_sep_oct')} วัน** (ทั้งหน้าต่าง) · ปล่อยสูงสุด {ev.get('max_released')} ลลบ.ม./วัน",
        "",
        "| จุดวัด | ชื่อ | ระดับสูงสุด | เวลาพีค | จำนวนชม.มีค่า | min_bank |",
        "|---|---|---|---|---|---|",
    ]
    for s in stations:
        mb = s["meta"].get("min_bank")
        lines.append(f"| {s['code']} | {s['name'][:24]} | {s['max']} | {s['peak_dt']} | {s['n']} | {mb} |")
    if lag is not None:
        lines += [
            "",
            f"- **lag เชิงหยาบ (พีคท้ายเขื่อน S.28 → พีคท้ายเขื่อนพระรามหก S.26) = {lag} ชม.** "
            "(พระรามหก = ชื่อทางการของเขื่อนป่าสักเดียวกัน — สองจุดอยู่ช่วงท้ายเขื่อน · "
            "เขื่อนรายงานรายวันเท่านั้น — จังหวะเปิดบานรายชั่วโมงไม่มีใน API = FOI รายเขื่อน)",
        ]
    lines += [
        "",
        "## 3. ฝน (NASA POWER กริด 0.5° — รีดยอดฝนเบลอ ใช้เทียบเชิงหยาบ)",
        "",
        "| จุด | ฝนสะสม ก.ย. 69 | 7 วันสูงสุด | ปลายหน้าต่าง 7 วัน |",
        "|---|---|---|---|",
    ]
    for label, v in out["rain_2026"].items():
        lines.append(f"| {label} | {v['sep_total_mm']} มม. | {v['best7_mm']} มม. | {v['best7_end']} |")
    lines += [
        "",
        "เทียบเกณฑ์นครนายก: เหตุการณ์ ก.ย. 69 = 248 มม./7 วัน (มาตรฐานเตือน 150) — POWER กริดหยาบมักต่ำกว่าสถานีจริง",
        "",
        "## 4. สิ่งที่ hardcode ใน spike (อินพุตออกแบบ config.json ต่อลุ่ม)",
        "",
        "- basin name ที่ใช้กรอง (\"ลุ่มน้ำป่าสัก\" ฯลฯ) · dam_id 11 · normal_storage 872 · พิกัดจุดฝน ·",
        "  หน้าต่างเหตุการณ์ · การจับคู่ URC แบบเดือน-วัน (เทมเพลตปี 2020) · โครงซ้อน 1 ชั้นของบางเขื่อน",
        "",
        "## 5. ช่องว่างที่ยังเปิด (ต่อเป้าหมายถัดไปของลุ่มนี้)",
        "",
        "- อัตราไหล/บานรายชั่วโมงของเขื่อนป่าสัก (API มีเฉพาะรายวัน) → FOI/โทรมาตรโครงการ",
        "- Q4 attribution เชิงปริมาตร (water balance) ต้องมีฝนลุ่มเฉพาะถิ่นละเอียดกว่า POWER 0.5°",
        "- rating curve ที่ S.26/S.28 (จะได้ Q แทนระดับ) · GISTDA ท่วมราย pass ของลุ่ม (มนุษย์)",
        "- L2: ฉาก S1 ช่วง 23 ก.ย.–2 ต.ค. ครอบลุ่มป่าสัก (ผู้ใช้ดาวน์โหลด CDSE)",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD} · lag {lag}")


if __name__ == "__main__":
    main()