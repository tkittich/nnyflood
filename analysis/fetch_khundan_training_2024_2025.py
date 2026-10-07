# ดึงข้อมูลฝึกโมเดลปี 2024-2025 (ขยาย data/16_training_data) — เจอว่า API ให้ย้อนหลังอย่างน้อยถึง 2024
import urllib.request, urllib.parse, re, time, datetime as dt
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / "data" / "16_training_data"
STATIONS = {61: "Ny1B", 62: "Ny7", 63: "ThaChang_tail"}

def fetch(n_id, d_from, d_to):
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

for year in (2024, 2025):
    allrows = {k: [] for k in STATIONS}
    d = dt.date(year, 6, 1)
    end = dt.date(year, 10, 4)
    while d <= end:
        d2 = min(d + dt.timedelta(days=6), end)
        for n_id in STATIONS:
            for attempt in range(3):
                try:
                    r = fetch(n_id, d.isoformat(), d2.isoformat())
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
        print(f"SAVED {fn.name}: {len(allrows[n_id])} rows", flush=True)
print("done")
