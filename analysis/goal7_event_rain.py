"""ฝนรายวันรอบที่ราบองครักษ์ ช่วงเหตุการณ์ 20 ก.ย.–4 ต.ค. 2569 จากสถานีวัดฝนในกรอบ (thaiwater GET ไม่ต้องใช้คีย์) แล้วประมาณเป็นสนามฝนรายวันบนกริดแบบจำลองด้วยการถ่วงน้ำหนักผกผันระยะทาง (IDW)
ตั้งไว้ก่อนดูผล: สถานีในกรอบ lat 13.85–14.5 · lon 100.85–101.6 ที่ปรากฏในชั้น rain_24h ล่าสุด · IDW กำลัง 2 ใช้ 6 สถานีใกล้สุดที่มีค่า · ค่ารายวัน = ฝน 24 ชม. ที่ลงวันที่นั้น (ถือเป็น 07:00 ของวันก่อนถึง 07:00 ของวันนั้น ตามธรรมเนียมรายงานฝน — ความคลาดเคลื่อนเวลาครึ่งวันถึงหนึ่งวัน)
ข้อจำกัด: ฝนรายวันเท่านั้น (ไม่มีรายชั่วโมงในชุดนี้) แจกแจงเท่ากันตลอดวัน · สถานีกระจายไม่สม่ำเสมอ · ฝนตกหนักเฉพาะที่ (พายุฝนฟ้าคะนอง) อาจพลาด
รัน: python analysis/goal7_event_rain.py
ผลลัพธ์: data/35_goal7_event_rain/raw/<สถานี>.json (disk-only · manifest.md) และ data/35_goal7_event_rain/rain_fields.npz · analysis/goal7/event_rain_summary.json
"""
import datetime as dt
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/35_goal7_event_rain/raw"
NPZ = ROOT / "data/35_goal7_event_rain/rain_fields.npz"
OUT = ROOT / "analysis/goal7/event_rain_summary.json"
SNAP = ROOT / "data/26_national_rainfall_stations/raw/national_rain_24h_all_stations.json"
INP = ROOT / "data/13_sentinel1_copernicus/derived/hydraulic2d_inputs.npz"
BASE = "https://api-v3.thaiwater.net/api/v1/thaiwater30/provinces/rain3d_graph"
BOX = (13.85, 14.5, 100.85, 101.6)
D0, D1 = dt.date(2026, 9, 20), dt.date(2026, 10, 4)
WIN = (13.98, 14.28, 100.97, 101.33)      # หน้าต่างแบบจำลอง (ต้องตรงกับ goal7_ongkharak_hydraulic_2d)
K, RES = 3, 0.0002777777777777778


def stations() -> list[dict]:
    out = []
    for s in json.loads(SNAP.read_text(encoding="utf-8"))["data"]:
        st = s.get("station") or {}
        la, lo = st.get("tele_station_lat"), st.get("tele_station_long")
        if la is None or lo is None:
            continue
        if BOX[0] <= float(la) <= BOX[1] and BOX[2] <= float(lo) <= BOX[3]:
            out.append({"id": st["id"], "lat": float(la), "lon": float(lo), "name": (st.get("tele_station_name") or {}).get("th"), "province": s["geocode"]["province_name"]["th"]})
    return out


def fetch(sid: int) -> list:
    f = RAW / f"{sid}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    url = BASE + "?" + urllib.parse.urlencode({"station_id": sid, "start_date": D0.isoformat(), "end_date": D1.isoformat()})
    for k in range(3):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nnyflood-research/1.0"}), timeout=60))
            f.write_text(json.dumps(r["data"], ensure_ascii=False), encoding="utf-8")
            return r["data"]
        except Exception:   # noqa: BLE001
            time.sleep(2 + 2 * k)
    return []


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    sts = stations()
    days = [(D0 + dt.timedelta(days=i)).isoformat() for i in range((D1 - D0).days + 1)]
    mat = np.full((len(sts), len(days)), np.nan, dtype="float32")
    for i, s in enumerate(sts):
        for r in fetch(s["id"]):
            d = r["rainfall_datetime"][:10]
            if d in days and r["rainfall_value"] is not None:
                mat[i, days.index(d)] = float(r["rainfall_value"])
        time.sleep(0.15)
    # กริดแบบจำลอง
    Z = np.load(INP)
    ny, nx = Z["mask"].shape
    y1 = 14.533055555555556                   # กริดเรดาร์ y1 (goal7 grid.json)
    x0 = 100.89333333333333
    r0 = int((y1 - WIN[1]) / RES)
    c0 = int((WIN[2] - x0) / RES)
    lat = (y1 - r0 * RES) - (np.arange(ny) + 0.5) * RES * K
    lon = (x0 + c0 * RES) + (np.arange(nx) + 0.5) * RES * K
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    fields = np.zeros((len(days), ny, nx), dtype="float32")
    sla = np.array([s["lat"] for s in sts])
    slo = np.array([s["lon"] for s in sts])
    kx = math.cos(math.radians(14.1))
    for di in range(len(days)):
        ok = np.nonzero(~np.isnan(mat[:, di]))[0]
        if len(ok) == 0:
            continue
        d2 = ((LA[..., None] - sla[ok]) ** 2 + ((LO[..., None] - slo[ok]) * kx) ** 2)       # ตร.องศา (ประมาณ)
        order = np.argsort(d2, axis=2)[..., :6]
        dd = np.take_along_axis(d2, order, axis=2)
        w = 1.0 / np.maximum(dd, 1e-8)
        vals = mat[ok, di][order]
        fields[di] = ((w * vals).sum(axis=2) / w.sum(axis=2)).astype("float32")
    np.savez_compressed(NPZ, fields=fields, days=np.array(days))
    tot = np.nansum(mat, axis=1)
    summ = {"note": "ฝนรายวันจากสถานีในกรอบ — ประมาณสนามฝนด้วย IDW (ดูหัวไฟล์)", "n_stations": len(sts), "days": days, "stations_with_data": int(np.sum(~np.isnan(mat).all(axis=1))),
            "domain_mean_mm_per_day": [round(float(f.mean()), 1) for f in fields], "domain_total_mm_20sep_to_4oct": round(float(fields.sum(axis=0).mean()), 0),
            "stations_total_mm": {"min": round(float(tot.min()), 0), "median": round(float(np.median(tot)), 0), "max": round(float(tot.max()), 0)},
            "heaviest_days": sorted(zip(days, [round(float(f.mean()), 1) for f in fields]), key=lambda x: -x[1])[:4]}
    OUT.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False)[:900])


if __name__ == "__main__":
    main()
