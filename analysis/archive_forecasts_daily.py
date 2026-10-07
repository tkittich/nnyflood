# เก็บพยากรณ์ฝน "ฉบับจริงตามรอบ" ล่วงหน้าสำหรับพายุลูกถัดไป + ระดับน้ำจริงล่าสุดแนบท้าย
# ทำงาน: ทุกวัน 09:15 และ 21:15 (ก่อนพายุ ตามคำขอผู้ใช้ 6 ต.ค. 69)
# แหล่ง: Open-Meteo v1/forecast (ฉบับออกจริงวันนั้น 5 โมเดล) + khundan-tele (Ny.7/Ny.1B 48 ชม.ล่าสุด)
# หมายเหตุ: previous-runs เก็บย้อนได้แค่ ~7 วัน — ระบบนี้จึงต้อง "เก็บทุกวัน" ตั้งแต่ก่อนพายุมา
import urllib.request, urllib.parse, json, re, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "17_forecast_archive"
OUT.mkdir(exist_ok=True)

PTS = {"north": (14.40, 101.05), "south": (14.20, 101.20)}   # เซลล์เดียวกับฝน POWER ของโมเดลทำนาย
MODELS = ["gfs_seamless", "ecmwf_ifs025", "icon_seamless", "gem_seamless", "jma_seamless"]
UA = {"User-Agent": "flood-analysis/1.0"}
now = dt.datetime.now()
snap = OUT / now.strftime("%Y%m%d_%H%M")
snap.mkdir(exist_ok=True)

# ---------- 1) พยากรณ์ฝนรายวัน 7 วันล่วงหน้า ทุกโมเดล ----------
fc = {}
for pt, (lat, lon) in PTS.items():
    for m in MODELS:
        q = urllib.parse.urlencode({"latitude": lat, "longitude": lon,
                                    "daily": "precipitation_sum", "models": m,
                                    "forecast_days": 7, "timezone": "Asia/Bangkok"})
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(
                f"https://api.open-meteo.com/v1/forecast?{q}", headers=UA), timeout=60).read())
            fc[f"{pt}|{m}"] = {"time": d["daily"]["time"], "precipitation_sum": d["daily"]["precipitation_sum"]}
        except Exception as e:
            fc[f"{pt}|{m}"] = {"error": str(e)[:200]}
json.dump({"fetched_at": now.isoformat(timespec="seconds"),
           "endpoint": "https://api.open-meteo.com/v1/forecast (ฉบับออกจริงของรอบล่าสุด)",
           "points": {k: list(v) for k, v in PTS.items()}, "models": MODELS, "data": fc},
          open(snap / "forecast_models_7d.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 2) ระดับน้ำจริง 48 ชม.ล่าสุด (เพื่อเทียบพยากรณ์ภายหลัง) ----------
def khundan(n_id, d0, d1):
    body = urllib.parse.urlencode({"n_id": str(n_id), "date_from": d0, "date_to": d1}).encode()
    req = urllib.request.Request("http://khundan-tele.rid.go.th/station_detail.php", data=body,
                                 headers={**UA, "Content-Type": "application/x-www-form-urlencoded"})
    txt = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", errors="ignore")
    rows = []
    for tr in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", txt):
        c = [x.strip() for x in re.findall(r"<t[dh][^>]*>([^<]*)", tr)]
        if len(c) >= 4 and re.match(r"\d{2}/\d{2}/\d{4}", c[0]):
            rows.append(c[:5])
    return rows

obs = {}
for n_id, name in ((62, "Ny7"), (61, "Ny1B")):
    try:
        obs[name] = khundan(n_id, (now - dt.timedelta(days=2)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"))[:200]
    except Exception as e:
        obs[name] = {"error": str(e)[:200]}
json.dump({"fetched_at": now.isoformat(timespec="seconds"),
           "source": "http://khundan-tele.rid.go.th/station_detail.php", "rows_newest_first": obs},
          open(snap / "observed_ny7_ny1b_48h.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 3) สรุปสั้น + แจ้งเตือน ----------
ok = {k: v for k, v in fc.items() if "precipitation_sum" in v}
print(f"เก็บแล้ว: {snap.name} | โมเดลสำเร็จ {len(ok)}/{len(fc)}")
alert = []
for m in MODELS:
    vals = []
    for pt in PTS:
        d = fc.get(f"{pt}|{m}", {})
        if "precipitation_sum" in d:
            vals += [v for v in d["precipitation_sum"] if v]
    if vals:
        tot = sum(vals) / 2
        print(f"  {m:<16} ฝนรวม 7 วัน (เฉลี่ย 2 จุด): {tot:5.1f} มม.")
        if tot >= 150:
            alert.append(f"{m}={tot:.0f}mm")
if alert:
    print(f"⚠ ฝน 7 วันเกินเกณฑ์เฝ้าระวัง 150 มม.: {', '.join(alert)}")
