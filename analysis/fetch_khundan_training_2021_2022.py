# ดึงข้อมูลฝึกโมเดลปี 2021-2022 (Ny.7 ปี 2023 ออฟไลน์ ข้าม) + ฝน POWER 2021-2026 + ฝนพยากรณ์ครอบช่วงทดสอบ
import urllib.request, urllib.parse, re, json, time, datetime as dt
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / "data" / "16_training_data"
STATIONS = {61: "Ny1B", 62: "Ny7", 63: "ThaChang_tail"}

def post_fetch(n_id, d_from, d_to):
    body = urllib.parse.urlencode({"n_id": str(n_id), "date_from": d_from, "date_to": d_to}).encode()
    req = urllib.request.Request("http://khundan-tele.rid.go.th/station_detail.php", data=body,
        headers={"User-Agent": "Mozilla/5.0 flood-analysis/1.0", "Content-Type": "application/x-www-form-urlencoded"})
    txt = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", errors="ignore")
    rows = []
    for tr in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", txt):
        c = [x.strip() for x in re.findall(r"<t[dh][^>]*>([^<]*)", tr)]
        if len(c) >= 4 and re.match(r"\d{2}/\d{2}/\d{4}", c[0]):
            rows.append(c[:5])
    return rows

for year in (2021, 2022):
    allrows = {k: [] for k in STATIONS}
    d = dt.date(year, 6, 1)
    end = dt.date(year, 10, 4)
    while d <= end:
        d2 = min(d + dt.timedelta(days=6), end)
        for n_id in STATIONS:
            for attempt in range(3):
                try:
                    r = post_fetch(n_id, d.isoformat(), d2.isoformat())
                    allrows[n_id].extend(r)
                    print(f"{year} {d}~{d2} st{n_id}: +{len(r)}", flush=True)
                    break
                except Exception as e:
                    print(f"{year} {d} st{n_id}: retry {attempt} ({e})", flush=True)
                    time.sleep(5)
            time.sleep(0.7)
        d = d2 + dt.timedelta(days=1)
    for n_id, name in STATIONS.items():
        fn = OUT / f"khundan_15min_{name}_Jun-Oct{year}.csv"
        with open(fn, "w", encoding="utf-8") as f:
            f.write("datetime,level_msl_m,q_cms,rain_mm\n")
            for c in allrows[n_id]:
                dd, mon, yr = c[0].split("/")
                f.write(f"{yr}-{mon}-{dd}T{c[1]}:00,{c[2]},{c[3]},{c[4] if len(c) > 4 else ''}\n")
        print(f"SAVED {fn.name}: {len(allrows[n_id])}", flush=True)

# ---- ฝน NASA POWER 2021-2026 (3 จุดเดิม) ----
PTS = {"west_foothill": (14.40, 101.00), "mid_plain": (14.30, 101.15), "town_east": (14.20, 101.20)}
cols = {}
for name, (lat, lon) in PTS.items():
    url = (f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR"
           f"&community=RE&longitude={lon}&latitude={lat}&start=20210601&end=20261004&format=JSON")
    d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "flood-analysis/1.0"}), timeout=90).read())
    cols[name] = d["properties"]["parameter"]["PRECTOTCORR"]
    print("POWER", name, len(cols[name]), flush=True)
    time.sleep(1)
dates = sorted(cols["west_foothill"])
fn = OUT / "power_rain_daily_3pts_2021_2026.csv"
with open(fn, "w", encoding="utf-8") as f:
    f.write("date,west_foothill,mid_plain,town_east\n")
    for d_ in dates:
        f.write(f"{d_},{cols['west_foothill'][d_]},{cols['mid_plain'][d_]},{cols['town_east'][d_]}\n")
print("POWER saved", len(dates), flush=True)

# ---- ฝนพยากรณ์ (Historical Forecast API) ครอบช่วงทดสอบ 13 ก.ย.-4 ต.ค. 69 ----
MODELS = ["gfs_seamless", "ecmwf_ifs025", "icon_seamless", "gem_seamless", "jma_seamless"]
out = {}
for pt, (lat, lon) in PTS.items():
    for m in MODELS:
        q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "daily": "precipitation_sum",
                                    "models": m, "start_date": "2026-09-13", "end_date": "2026-10-04",
                                    "timezone": "Asia/Bangkok"})
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(
                "https://historical-forecast-api.open-meteo.com/v1/forecast?" + q,
                headers={"User-Agent": "flood-analysis/1.0"}), timeout=60).read())
            out[f"{pt}|{m}"] = dict(zip(d["daily"]["time"], d["daily"]["precipitation_sum"]))
        except Exception as e:
            print("fcst FAIL", pt, m, e, flush=True)
        time.sleep(0.7)
json.dump(out, open(OUT / "model_rain_histforecast_sep2026.json", "w"), indent=1)
print("fcst rain saved", len(out), flush=True)
print("done")
