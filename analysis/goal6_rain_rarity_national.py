"""เป้าหมาย 6 — ฝน POWER ระดับชาติ: ความหายากฝน 7/30 วัน ครบ 199 จุดวัดในคลังระดับชาติ

ต่อจุดวัดใน data/30_national_warehouse/waterlevels/ (199 จุด): หาพิกัดจาก station_all.json
→ ดึงฝนรายวัน NASA POWER 1981–2026 (แคชต่อจุด · รีซูมได้เพราะไฟล์เป็นตัวทำเครื่องหมาย)
→ สะสมสูงสุด 7/30 วันใน ก.ค.–ต.ค. ทุกปี → อันดับ/คาบคืน Weibull ของ 2569

ผลลัพธ์: analysis/goal6/rain_rarity_national.json/.md
raw: data/22_goal6_network/raw/rain_rarity_national/ (แคช POWER ต่อจุด)
ทำซ้ำได้ · รัน: python analysis/goal6_rain_rarity_national.py [--workers N]
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = ROOT / "data/30_national_warehouse/waterlevels"
STATION_ALL = ROOT / "data/02_thaiwater/raw/station_all.json"
RAW_DIR = ROOT / "data/22_goal6_network/raw/rain_rarity_national"
OUT_JSON = ROOT / "analysis/goal6/rain_rarity_national.json"
OUT_MD = ROOT / "analysis/goal6/rain_rarity_national.md"
YEARS = (1981, 2026)
WINDOWS = (7, 30)


def fetch_daily(lon: float, lat: float, key: str) -> dict:
    """รายวัน 1981–2026 · cache ต่อจุดวัด (ไฟล์เป็นตัวทำเครื่องหมาย — รีซูมได้)"""
    p = RAW_DIR / f"power_{key}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR"
           f"&community=RE&format=JSON&longitude={lon:.4f}&latitude={lat:.4f}"
           f"&start={YEARS[0]}0101&end={YEARS[1]}1009")
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                d = json.load(resp)
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    daily = {f"{k[:4]}-{k[4:6]}-{k[6:8]}": v for k, v in d["properties"]["parameter"]["PRECTOTCORR"].items() if v >= 0}
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(daily, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
    return daily


def best_window(daily: dict, year: int, days: int, month_from: int = 7, month_to: int = 10) -> tuple[float, str | None]:
    """สะสมสูงสุด `days` วันต่อเนื่องในหน้าฝน ก.ค.–ต.ค. ของปีนั้น"""
    dates = sorted(d for d in daily if d.startswith(str(year)) and month_from <= int(d[5:7]) <= month_to)
    vals = [daily[d] for d in dates]
    if len(vals) < days:
        return float("nan"), None
    best_sum, best_end = -1.0, None
    run = 0.0
    for i, v in enumerate(vals):
        run += v
        if i >= days:
            run -= vals[i - days]
        if i >= days - 1 and run > best_sum:
            best_sum, best_end = run, dates[i]
    return best_sum, best_end


def rarity(daily: dict) -> dict:
    """อันดับ/คาบคืนของ 2569 เทียบ 46 ปี (Weibull (n+1)/อันดับ) ต่อหน้าต่าง 7/30 วัน"""
    out = {}
    for win in WINDOWS:
        annual = {y: best_window(daily, y, win) for y in range(YEARS[0], YEARS[1] + 1)}
        vals = sorted((s for s, _ in annual.values() if s == s), reverse=True)
        v26 = annual.get(2026, (float("nan"), None))[0]
        rank = vals.index(v26) + 1 if v26 == v26 and vals else None
        n = len(vals)
        out[f"best{win}"] = {
            "value_mm": round(v26, 1) if v26 == v26 else None,
            "end_date": annual.get(2026, (0.0, None))[1],
            "rank_in_n": rank, "n_years": n,
            "weibull_rp_yr": round((n + 1) / rank, 1) if rank else None,
        }
    return out


def main() -> None:
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 6
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sa = json.loads(STATION_ALL.read_text(encoding="utf-8"))["data"]
    by_id = {r["station_id"]: r for r in sa}

    stations = []
    for p in sorted(WAREHOUSE.glob("*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        st = by_id.get(rec["station_id"], {})
        lat, lon = st.get("station_lat"), st.get("station_long")
        if lat is None or lon is None:
            print(f"ข้าม {rec['station_id']} — ไม่มีพิกัด", flush=True)
            continue
        key = str(rec["station_id"])
        stations.append({"id": rec["station_id"], "code": rec.get("code", ""), "name": rec.get("name", ""),
                         "basin": rec.get("basin", ""), "lat": lat, "lon": lon, "key": key})

    print(f"จุดวัด {len(stations)} จุด · workers {workers}", flush=True)

    def one(s):
        try:
            daily = fetch_daily(s["lon"], s["lat"], s["key"])
            return s, rarity(daily)
        except Exception as e:
            print(f"พลาด {s['id']}: {e}", flush=True)
            return s, None

    out = {"window_event": "2026-07-01..2026-10-09", "source": "NASA POWER PRECTOTCORR 1981-2026",
           "note": "กริด 0.5° รีดยอดฝนเบลอ — ค่าสถานีจริงสูงกว่าเสมอ", "points": {}}
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for s, rr in ex.map(lambda x: one(x), stations):
            done += 1
            if rr is None:
                continue
            out["points"][s["key"]] = {**s, **rr}
            if done % 20 == 0 or done == len(stations):
                OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"เสร็จ {done}/{len(stations)}", flush=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # MD: จัดกลุ่มตามลุ่ม · เรียงตามคาบคืน 7 วัน (ใหญ่→เล็ก)
    lines = ["# ฝนความหายากระดับชาติ — ครบ 199 จุดวัดในคลัง (Q1 ขยายทั้งประเทศ)", "",
             "> NASA POWER กริด 0.5° 1981–2026 · สะสมสูงสุด 7/30 วันใน ก.ค.–ต.ค. · "
             "คาบคืน Weibull (n+1)/อันดับ · <b>กริดหยาบรีดยอดฝนเบลอ = ค่าสถานีจริงสูงกว่าเสมอ</b>", "",
             "| จุดวัด | รหัส | ลุ่ม | 7 วันสูงสุด 2569 (มม.) | อันดับ | คาบคืน~ | 30 วัน (มม.) | คาบคืน~ |",
             "|---|---|---|---|---|---|---|---|"]
    pts = sorted(out["points"].values(), key=lambda r: -(r["best7"]["weibull_rp_yr"] or 0))
    for r in pts:
        b7, b30 = r["best7"], r["best30"]
        lines.append(f"| {r['name']} | {r['code']} | {r['basin']} | {b7['value_mm']} | "
                     f"{b7['rank_in_n']}/{b7['n_years']} | ~{b7['weibull_rp_yr']} ปี | "
                     f"{b30['value_mm']} | ~{b30['weibull_rp_yr']} ปี |")
    n_top = sum(1 for r in pts if (r["best7"]["rank_in_n"] or 99) <= 3)
    lines += ["", f"**สรุปหยาบ**: จุดวัดที่ฝน 7 วัน 2569 ติดอันดับ 1–3 ของ 46 ปี = **{n_top}/{len(pts)} จุด** "
              "(แตะเพื่อดูรายจุด · เทียบเกณฑ์นครนายก 248 มม./7 วัน = มาตรฐานเตือน 150)", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD} · จุด {len(out['points'])}", flush=True)


if __name__ == "__main__":
    main()
