"""เป้าหมาย 6 — พยากรณ์ฝนย้อนหลัง (previous runs) ช่วงเหตุการณ์ 2569 ต่อจุดฝนลุ่ม

คำถาม Q3-เสริม: ถ้าฝึกระบบเตือนด้วยพยากรณ์จริง ณ วันนั้น จะรู้ทันไหม (แบบนครนายก: GFS ไม่ช่วยที่ +24)
แหล่ง: Open-Meteo Archive API (ERA5) ดึงรายวัน 1 ก.ค.–9 ต.ค. 69 ต่อจุด — และ
Forecast API archive of runs: เทียบฝนพยากรณ์ที่ "รู้ก่อน" ด้วย previous_run参数 (จุดเดียวจบใน 1 request)
หมายเหตุ: Open-Meteo previous_runs ของ forecast = /v1/forecast?previous_day=N จำกัดย้อนไม่ไกล;
ทางที่ใช้ได้เชิงหลักฐาน = ฝนเรียลไทม์เชิงสังเคราะห์ (ERA5) เทียบสถานี — ระดับพยากรณ์จริงรอ TMD token
ผลลัพธ์: analysis/goal6/rain_obs_2026.json/.md (อนุกรมเรียลไทม์จริงต่อจุด — อินพุตบท "เตือนภัย")
รัน: python analysis/goal6_rain_obs_2026.py
"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "analysis/goal6/config.json"
RAW_DIR = ROOT / "data/22_goal6_network/raw/rain_obs_2026"
OUT_JSON = ROOT / "analysis/goal6/rain_obs_2026.json"
OUT_MD = ROOT / "analysis/goal6/rain_obs_2026.md"
URL = ("https://archive-api.open-meteo.com/v1/archive"
       "?latitude={lat}&longitude={lon}&start_date=2026-07-01&end_date=2026-10-09"
       "&daily=precipitation_sum&timezone=Asia%2FBangkok")


def fetch(lon: float, lat: float) -> dict:
    url = URL.format(lon=lon, lat=lat)
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    daily = d["daily"]
    return {date: (v or 0.0) for date, v in zip(daily["time"], daily["precipitation_sum"])}


def main() -> None:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    md = ["# ฝนเรียลไทม์ 1 ก.ค.–9 ต.ค. 2569 (Open-Meteo/ERA5) — อินพุตบทเตือนภัยต่อลุ่ม", "",
          "| ลุ่ม/จุด | ก.ย. สะสม | 7 วันสูงสุด | ปลายหน้าต่าง | วัน 50 มม.+ |", "|---|---|---|---|---|"]
    for bid, rec in cfg["basins"].items():
        for label, (lon, lat) in rec["rain_points"].items():
            key = f"{bid}_{label}".replace(" ", "_").replace("(", "").replace(")", "").replace("/", "-")
            p = RAW_DIR / f"{key}.json"
            daily = json.loads(p.read_text(encoding="utf-8")) if p.exists() else fetch(lon, lat)
            if not p.exists():
                p.write_text(json.dumps(daily, ensure_ascii=False), encoding="utf-8")
            dates = sorted(daily)
            sep = sum(v for d, v in daily.items() if d[:7] == "2026-09")
            best, bend = -1.0, None
            for i in range(6, len(dates)):
                s = sum(daily[x] for x in dates[i - 6:i + 1])
                if s > best:
                    best, bend = s, dates[i]
            heavy = sum(1 for v in daily.values() if v >= 50)
            out[key] = {"basin": bid, "point": label, "sep_total_mm": round(sep, 1),
                        "best7_mm": round(best, 1), "best7_end": bend, "days_ge_50mm": heavy}
            md.append(f"| {bid} · {label} | {sep:.0f} | {best:.0f} | {bend} | {heavy} |")
            print(f"{bid}/{label}: ก.ย. {sep:.0f} · 7วัน {best:.0f} · 50มม.+ {heavy} วัน", flush=True)
            time.sleep(0.3)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()