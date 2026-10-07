# ดึงข้อมูลโทรมาตรเขื่อนขุนด่านฯ เป็นชุดข้อมูลฝึกโมเดลทำนายระดับน้ำ (เป้าหมาย #4)
# ที่มา: http://khundan-tele.rid.go.th/station_detail.php (POST urlencoded)
# ความละเอียด: **15 นาที ใช้ได้ทุกช่วงความยาว** — ทดสอบ 6 ต.ค. 69: ขอช่วง 2022-01-01..2025-12-31
#   ได้ 138,822 แถว median gap 15 นาที · ไฟล์ *FULLYEAR*.csv ของโครงการเองก็เป็น 15 นาที
#   ⚠️ อย่าตีความ API ว่า "ช่วง <=7 วัน -> 15 นาที / ยาวกว่านั้น -> รายวัน 07:00" — ไม่จริง
#   (ดึง 5 ปี 15 นาทีได้จริง) · สคริปต์นี้ยังดึงเป็นก้อน 6 วันเพื่อกัน timeout/ตัดช่วง
# สถานี: 61=Ny.1B(ใกล้เขื่อน) 62=Ny.7(ตัวเมือง) 63=ท้ายน้ำปตร.ท่าช้าง 105=NY.3(ปลายน้ำ)
import urllib.request, urllib.parse, re, json, time, datetime as dt
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "16_training_data"
OUT.mkdir(exist_ok=True)
STATIONS = {61: "Ny1B", 62: "Ny7", 63: "ThaChang_tail", 105: "NY3"}

def fetch(n_id, d_from, d_to):
    body = urllib.parse.urlencode({"n_id": str(n_id), "date_from": d_from, "date_to": d_to}).encode()
    req = urllib.request.Request(
        "http://khundan-tele.rid.go.th/station_detail.php", data=body,
        headers={"User-Agent": "Mozilla/5.0 flood-analysis/1.0",
                 "Content-Type": "application/x-www-form-urlencoded"})
    txt = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", errors="ignore")
    rows = []
    for tr in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", txt):
        c = [x.strip() for x in re.findall(r"<t[dh][^>]*>([^<]*)", tr)]
        if len(c) >= 4 and re.match(r"\d{2}/\d{2}/\d{4}", c[0]):
            rows.append(c[:5])
    return rows

def chunk_15min():
    """1 มิ.ย. – 4 ต.ค. 69 ราย 15 นาที เป็นก้อน 6 วัน"""
    start, end = dt.date(2026, 6, 1), dt.date(2026, 10, 4)
    allrows = {k: [] for k in STATIONS}
    d = start
    while d <= end:
        d2 = min(d + dt.timedelta(days=6), end)
        rng = f"{d.isoformat()}~{d2.isoformat()}"
        for n_id in STATIONS:
            for attempt in range(3):
                try:
                    r = fetch(n_id, d.isoformat(), d2.isoformat())
                    allrows[n_id].extend(r)
                    print(f"{rng} st{n_id}: +{len(r)}", flush=True)
                    break
                except Exception as e:
                    print(f"{rng} st{n_id}: retry {attempt} ({e})", flush=True)
                    time.sleep(5)
            time.sleep(1)
        d = d2 + dt.timedelta(days=1)
    return allrows

if __name__ == "__main__":
    t0 = time.time()
    data = chunk_15min()
    for n_id, name in STATIONS.items():
        rows = data[n_id]
        # ไฟล์ csv: datetime_iso,level_msl_m,q_cms,rain_mm (เรียงเวลาเดิม = ใหม่->เก่า)
        csv = OUT / f"khundan_15min_{name}_Jun-Oct2026.csv"
        with open(csv, "w", encoding="utf-8") as f:
            f.write("datetime,level_msl_m,q_cms,rain_mm\n")
            for c in rows:
                dd, tt = c[0], c[1]
                day, mon, yr = dd.split("/")
                iso = f"{yr}-{mon}-{day}T{tt}:00"
                f.write(f"{iso},{c[2]},{c[3]},{c[4] if len(c) > 4 else ''}\n")
        print(f"{name}: {len(rows)} rows -> {csv.name}", flush=True)
    json.dump({"fetched_at": dt.datetime.now().isoformat(),
               "source": "http://khundan-tele.rid.go.th/station_detail.php (POST n_id/date_from/date_to)",
               "resolution": "15-min (<=7d chunks), 2026-06-01..2026-10-04"},
              open(OUT / "fetch_info.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"done in {time.time()-t0:.0f}s")
