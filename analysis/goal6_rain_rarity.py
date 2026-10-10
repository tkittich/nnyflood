"""เป้าหมาย 6 — Q1: ฝนเหตุการณ์ 2569 หายากแค่ไหน (คาบคืนเชิงหยาบจาก POWER 1981–2026)

ต่อจุดฝนใน config (14 จุด 6 ลุ่ม): ดึงฝนรายวัน NASA POWER 1981–2026 → คำนวณ
(1) สะสมสูงสุด 7/30 วัน ใน ก.ค.–ต.ค. ของแต่ละปี (2) ค่า 2569 ตกอันดับที่เท่าไร
(3) period คาดคะเน = (จำนวนปี+1)/อันดับ (Weibull อย่างง่าย — ระบุข้อจำกัดกริด 0.5°)

ผลลัพธ์: analysis/goal6/rain_rarity.json/.md · raw: data/22_goal6_network/raw/rain_rarity/
ทำซ้ำได้ · รัน: python analysis/goal6_rain_rarity.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "analysis/goal6/config.json"
RAW_DIR = ROOT / "data/22_goal6_network/raw/rain_rarity"
OUT_JSON = ROOT / "analysis/goal6/rain_rarity.json"
OUT_MD = ROOT / "analysis/goal6/rain_rarity.md"
YEARS = (1981, 2026)


def fetch_daily(lon: float, lat: float, key: str) -> dict:
    """รายวัน 1981–2026 · cache ต่อจุดฝน"""
    p = RAW_DIR / f"power_{key}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR"
           f"&community=RE&format=JSON&longitude={lon}&latitude={lat}"
           f"&start={YEARS[0]}0101&end={YEARS[1]}1009")
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.load(resp)
    series = d["properties"]["parameter"]["PRECTOTCORR"]
    daily = {f"{k[:4]}-{k[4:6]}-{k[6:8]}": v for k, v in series.items() if v >= 0}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(daily, ensure_ascii=False), encoding="utf-8")
    return daily


def best_window(daily: dict, year: int, days: int, month_from: int = 7, month_to: int = 10) -> tuple[float, str | None]:
    dates = sorted(d for d in daily if d.startswith(str(year)) and int(d[5:7]) >= month_from and int(d[5:7]) <= month_to)
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


def main() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = {"window_event": "2026-07-01..2026-10-09", "points": {}}
    for bid, rec in cfg["basins"].items():
        for label, (lon, lat) in rec["rain_points"].items():
            key = f"{bid}_{label}".replace(" ", "_").replace("(", "").replace(")", "")
            daily = fetch_daily(lon, lat, key)
            time.sleep(0.2)
            rec_p = {"basin": bid, "point": label, "lonlat": [lon, lat]}
            for win in (7, 30):
                annual = {}
                for y in range(YEARS[0], YEARS[1] + 1):
                    s, end = best_window(daily, y, win)
                    annual[y] = (s, end)
                # ค่า 2569 อันดับเท่าไรใน 46 ปี
                year_vals = sorted((s for y, (s, _) in annual.items() if s == s), reverse=True)
                v26 = annual.get(2026, (float("nan"), None))[0]
                rank = year_vals.index(v26) + 1 if v26 == v26 and year_vals else None
                n = len(year_vals)
                rp = round((n + 1) / rank, 1) if rank else None
                rec_p[f"best{win}"] = {"value_mm": round(v26, 1) if v26 == v26 else None,
                                       "end_date": annual.get(2026, (0, None))[1],
                                       "rank_in_46y": rank, "weibull_rp_yr": rp,
                                       "annual_series": {str(y): [round(s, 1) if s == s else None, e]
                                                         for y, (s, e) in annual.items()}}
            out["points"][key] = rec_p
            b7 = rec_p["best7"]
            print(f"{bid}/{label}: 7วัน {b7['value_mm']} มม. · อันดับ {b7['rank_in_46y']}/{46} · RP~{b7['weibull_rp_yr']} ปี", flush=True)
            OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # MD
    lines = ["# ฝนเหตุการณ์ปลาย ก.ย. 2569 หายากแค่ไหน (Q1)", "",
             "> NASA POWER กริด 0.5° 1981–2026 · สะสมสูงสุด 7/30 วันใน ก.ค.–ต.ค. · "
             "คาบคืนแบบ Weibull (n+1)/อันดับ — <b>กริดหยาบรีดยอดฝนเบลอ = ค่าสถานีจริงสูงกว่าเสมอ</b>", "",
             "| ลุ่ม/จุด | 7 วันสูงสุด 2569 | อันดับใน 46 ปี | คาบคืน~ | 30 วันสูงสุด 2569 | คาบคืน~ |", "|---|---|---|---|---|---|"]
    for key, rec in out["points"].items():
        b7, b30 = rec["best7"], rec["best30"]
        lines.append(f"| {rec['basin']} · {rec['point']} | {b7['value_mm']} | {b7['rank_in_46y']}/46 | "
                     f"~{b7['weibull_rp_yr']} ปี | {b30['value_mm']} | ~{b30['weibull_rp_yr']} ปี |")
    lines += ["", "เทียบเกณฑ์เหตุการณ์นครนายก: 248 มม./7 วัน (มาตรฐานเตือน 150) — อ่านคู่ข้อจำกัดกริดข้างบน", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()