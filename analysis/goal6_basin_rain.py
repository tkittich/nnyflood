"""ฝนเฉลี่ยทั้งลุ่ม (ถ่วงน้ำหนักตามพื้นที่) + ฝนรวมฤดู — รีวิว Sonnet A2 (12 ต.ค. 69)

ทำไม: เดิมเทียบ "ฝน 7 วันสูงสุดที่จุดวัด" รายจุด (ซ้ำช่องกริดเดียวกัน · ไม่แทนทั้งลุ่ม · ไม่มีฝนรวมฤดู
ซึ่งเป็นตัวชี้ที่สำคัญของปี 2554) → คำนวณฝนเฉลี่ยลุ่มเหนือจุดวัดหลักของแต่ละลุ่ม

วิธี (ไม่มีขั้นตอนที่ต้องมือ):
 1. ลุ่มรับน้ำเหนือจุดวัด = รวม HydroBASINS lev08 ทุกแปลงเหนือน้ำ (ไล่ NEXT_DOWN) ของแปลงที่จุดวัดตั้งอยู่
 2. กริดฝน NASA POWER (MERRA-2) 0.5° × 0.625° → น้ำหนักเซลล์ = สัดส่วนพื้นที่ลุ่มที่ซ้อนกับเซลล์
 3. ใช้แคชรายจุดเดิม (rain_rarity_national) ถ้ามีเซลล์เดียวกัน · ที่เหลือดึงใหม่ที่ศูนย์กลางเซลล์
 4. ตัวชี้รายปี 1981–2026 ในหน้าต่างร่วม ก.ค.1–(วันสุดท้ายที่มีข้อมูลปี 2569) ทุกปี — ไม่ตัดปี 2569 ฝ่ายเดียว:
    ฝนรวมฤดู · ฝนรวม ส.ค.–ก.ย. · สูงสุด 7/30/60 วัน → อันดับของ 2554 และ 2569 จาก 46 ปี

ผลลัพธ์: analysis/goal6/basin_rain.json/.md · raw: data/22_goal6_network/raw/basin_rain/ (เซลล์ที่ดึงใหม่)
รัน: python -I analysis/goal6_basin_rain.py [--workers N]   (-I: ไม่โหลดโมดูลจากโฟลเดอร์ปัจจุบัน)
"""

from __future__ import annotations

import io
import json
import math
import sys
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import shapefile
from shapely.geometry import Point, box, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
ZIP08 = ROOT / "data/22_goal6_network/raw/hydrobasins/hybas_as_lev08_v1c.zip"
STATION_ALL = ROOT / "data/02_thaiwater/raw/station_all.json"
NAT = ROOT / "analysis/goal6/rain_rarity_national.json"
NAT_RAW = ROOT / "data/22_goal6_network/raw/rain_rarity_national"
RAW = ROOT / "data/22_goal6_network/raw/basin_rain"
OUT_JSON = ROOT / "analysis/goal6/basin_rain.json"
OUT_MD = ROOT / "analysis/goal6/basin_rain.md"

DLAT, DLON = 0.5, 0.625
# ลุ่ม → (รหัสจุดวัดหลักของลุ่ม ตรงกับ L3 TARGET, ป้าย)
TARGETS = {
    "ping_cp": ("C.2", "ปิง–วัง–ยม–น่าน เหนือนครสวรรค์ (C.2)"),
    "bkk_lower": ("C.13", "ทั้งลุ่มเหนือท้ายเขื่อนเจ้าพระยา (C.13)"),
    "pasak": ("S.26", "ป่าสักเหนือพระรามหก (S.26)"),
    "maeklong": ("K.3A", "แม่กลองเหนือกาญจนบุรี (K.3A)"),
    "bp_prach": ("Kgt.3", "บางปะกงเหนือกบินทร์บุรี (Kgt.3)"),
    "thachin": ("T.1", "ท่าจีนเหนือนครชัยศรี (T.1)"),
    "nakhonnayok": ("Ny.7", "นครนายกเหนือตัวเมือง (Ny.7)"),
}
Y0, Y1 = 1981, 2026


def read_lev08():
    z = zipfile.ZipFile(ZIP08)
    n = "hybas_as_lev08_v1c"
    r = shapefile.Reader(shp=io.BytesIO(z.read(n + ".shp")), shx=io.BytesIO(z.read(n + ".shx")),
                         dbf=io.BytesIO(z.read(n + ".dbf")))
    # ประเทศไทยและรอบ ๆ เท่านั้น (ลดเวลา)
    recs = []
    for sr in r.iterShapeRecords():
        x0, y0, x1, y1 = sr.shape.bbox
        if x1 < 96 or x0 > 108 or y1 < 4 or y0 > 22:
            continue
        d = sr.record.as_dict()
        recs.append({"id": d["HYBAS_ID"], "down": d["NEXT_DOWN"], "up_area": d["UP_AREA"],
                     "geom": shape(sr.shape.__geo_interface__)})
    return recs


def upstream_ids(recs, start_id):
    children: dict[int, list[int]] = {}
    for r in recs:
        children.setdefault(r["down"], []).append(r["id"])
    out, stack = {start_id}, [start_id]
    while stack:
        for c in children.get(stack.pop(), []):
            if c not in out:
                out.add(c)
                stack.append(c)
    return out


def gauge_polygon(recs, lat, lon):
    pt = Point(lon, lat)
    hit = [r for r in recs if r["geom"].bounds[0] <= lon <= r["geom"].bounds[2]
           and r["geom"].bounds[1] <= lat <= r["geom"].bounds[3] and r["geom"].contains(pt)]
    if hit:
        return hit[0], 0.0
    # จุดวัดริมแม่น้ำอาจตกขอบแปลง — เลือกแปลงที่ใกล้สุดภายใน ~3 กม. (รายงานระยะ)
    best = min(recs, key=lambda r: r["geom"].distance(pt))
    return best, best["geom"].distance(pt)


def cell_of(lat, lon):
    return round(lat / DLAT) * DLAT, round(lon / DLON) * DLON


def fetch_cell(lat, lon):
    p = RAW / f"cell_{lat:.1f}_{lon:.3f}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    url = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR&community=RE&format=JSON"
           f"&longitude={lon:.4f}&latitude={lat:.4f}&start={Y0}0101&end={Y1}1231")
    last = None
    for a in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                d = json.load(resp)
            daily = {f"{k[:4]}-{k[4:6]}-{k[6:8]}": v for k, v in d["properties"]["parameter"]["PRECTOTCORR"].items() if v >= 0}
            RAW.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps(daily), encoding="utf-8")
            tmp.replace(p)
            return daily
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (a + 1))
    raise RuntimeError(f"fetch {lat},{lon}: {last}")


def main() -> None:
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 6
    sa = json.loads(STATION_ALL.read_text(encoding="utf-8"))["data"]
    by_code = {}
    for r in sa:
        by_code.setdefault(r.get("station_old_code"), r)
    # แคชเดิมตามเซลล์: ใช้สถานีใดก็ได้ที่ตกเซลล์นั้น (ค่า POWER เหมือนกันในเซลล์เดียว)
    nat = json.loads(NAT.read_text(encoding="utf-8"))["points"]
    cache_by_cell: dict[tuple[float, float], Path] = {}
    for k, p in nat.items():
        c = cell_of(p["lat"], p["lon"])
        f = NAT_RAW / f"power_{k}.json"
        if f.exists():
            cache_by_cell.setdefault(c, f)

    print("อ่าน HydroBASINS lev08 ...", flush=True)
    recs = read_lev08()
    print(f"  แปลง {len(recs)} (กรอบไทย)", flush=True)

    catch = {}
    for bid, (code, label) in TARGETS.items():
        st = by_code.get(code)
        if not st:
            print(f"  ไม่พบจุดวัด {code}", flush=True)
            continue
        lat, lon = st["station_lat"], st["station_long"]
        poly, dist = gauge_polygon(recs, lat, lon)
        ids = upstream_ids(recs, poly["id"])
        geom = unary_union([r["geom"] for r in recs if r["id"] in ids])
        area_km2 = sum(r["geom"].area for r in recs if r["id"] in ids)  # (องศา² — แค่ตรวจเทียบ UP_AREA)
        catch[bid] = {"code": code, "label": label, "lat": lat, "lon": lon, "n_polygons": len(ids),
                      "snap_dist_deg": round(dist, 4), "up_area_km2": poly["up_area"], "geom": geom}
        print(f"  {bid}: {code} → {len(ids)} แปลง · UP_AREA {poly['up_area']:.0f} ตร.กม. · snap {dist:.3f}°", flush=True)

    # เซลล์ที่ต้องใช้ + น้ำหนัก
    need: dict[tuple[float, float], None] = {}
    weights: dict[str, dict[tuple[float, float], float]] = {}
    for bid, c in catch.items():
        g = c["geom"]
        x0, y0, x1, y1 = g.bounds
        w = {}
        la = math.floor(y0 / DLAT) * DLAT
        while la <= y1 + DLAT:
            lo = math.floor(x0 / DLON) * DLON
            while lo <= x1 + DLON:
                clat, clon = cell_of(la, lo)
                cell = box(clon - DLON / 2, clat - DLAT / 2, clon + DLON / 2, clat + DLAT / 2)
                a = g.intersection(cell).area * math.cos(math.radians(clat))
                if a > 0:
                    w[(clat, clon)] = w.get((clat, clon), 0.0) + a
                lo += DLON
            la += DLAT
        tot = sum(w.values())
        weights[bid] = {k: v / tot for k, v in w.items()}
        for k in w:
            need[k] = None
    cells = list(need)
    print(f"เซลล์ที่ต้องใช้ {len(cells)} · แคชเดิม {sum(1 for c in cells if c in cache_by_cell)}", flush=True)

    series: dict[tuple[float, float], dict[str, float]] = {}
    todo = []
    for c in cells:
        if c in cache_by_cell:
            series[c] = json.loads(cache_by_cell[c].read_text(encoding="utf-8"))
        else:
            todo.append(c)
    print(f"ต้องดึงใหม่ {len(todo)} เซลล์", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for c, d in zip(todo, ex.map(lambda x: fetch_cell(*x), todo)):
            series[c] = d

    # วันสุดท้ายปี 2569 ที่มีครบทุกเซลล์
    last = min(max(k for k in d if k.startswith("2026")) for d in series.values())
    mmdd_end = last[5:]
    print("วันสุดท้ายร่วมปี 2569:", last, flush=True)

    out = {"window": f"07-01..{mmdd_end}", "last_common_date_2026": last,
           "method": "ถ่วงน้ำหนักตามพื้นที่ซ้อนเซลล์ POWER 0.5°×0.625° กับลุ่มรับน้ำเหนือจุดวัด (HydroBASINS lev08)",
           "basins": {}}
    for bid, c in catch.items():
        wsum = weights[bid]
        dates = sorted(set().union(*[set(series[k]) for k in wsum]))
        daily = {}
        for d in dates:
            num = den = 0.0
            for k, w in wsum.items():
                v = series[k].get(d)
                if v is not None:
                    num += v * w
                    den += w
            if den > 0.9:
                daily[d] = num / den
        years = {}
        for y in range(Y0, Y1 + 1):
            ds = [f"{y}-{m:02d}-{dd:02d}" for m in range(7, 11) for dd in range(1, 32)
                  if f"{m:02d}-{dd:02d}" <= mmdd_end and f"{y}-{m:02d}-{dd:02d}" in daily]
            vals = np.array([daily[d] for d in ds])
            if len(vals) < 90:
                continue
            def mx(n):
                return float(max(vals[i:i + n].sum() for i in range(len(vals) - n + 1)))
            sep_aug = float(sum(daily[d] for d in ds if "08-01" <= d[5:] <= "09-30"))
            years[y] = {"season_total": float(vals.sum()), "aug_sep_total": sep_aug,
                        "max7": mx(7), "max30": mx(30), "max60": mx(60), "n_days": len(vals)}
        res = {"label": c["label"], "gauge": c["code"], "n_polygons": c["n_polygons"], "up_area_km2": c["up_area_km2"],
               "n_cells": len(wsum), "years_n": len(years), "metrics": {}}
        for m in ("season_total", "aug_sep_total", "max7", "max30", "max60"):
            vs = {y: v[m] for y, v in years.items()}
            order = sorted(vs.values(), reverse=True)
            res["metrics"][m] = {
                "v2554": round(vs.get(2011, float("nan")), 1), "v2569": round(vs.get(2026, float("nan")), 1),
                "rank2554": order.index(vs[2011]) + 1 if 2011 in vs else None,
                "rank2569": order.index(vs[2026]) + 1 if 2026 in vs else None,
                "n": len(vs), "median": round(float(np.median(list(vs.values()))), 1),
                "max_other": round(max(v for y, v in vs.items() if y not in (2011, 2026)), 1),
            }
        out["basins"][bid] = res
        print(f"  {bid}: ฤดู 2554 อันดับ {res['metrics']['season_total']['rank2554']} "
              f"({res['metrics']['season_total']['v2554']}) · 2569 อันดับ {res['metrics']['season_total']['rank2569']} "
              f"({res['metrics']['season_total']['v2569']}) · max7 อันดับ {res['metrics']['max7']['rank2554']}/"
              f"{res['metrics']['max7']['rank2569']}", flush=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    md = ["# ฝนเฉลี่ยทั้งลุ่มรับน้ำ (ถ่วงน้ำหนักตามพื้นที่) — อันดับ 2554 เทียบ 2569 จาก 46 ปี", "",
          f"> NASA POWER PRECTOTCORR 1981–2026 · หน้าต่างร่วมทุกปี 1 ก.ค.–{mmdd_end} · ลุ่ม = HydroBASINS lev08 เหนือจุดวัดหลัก · "
          "เลขอันดับ 1 = สูงสุดใน 46 ปี", "",
          "| ลุ่ม | เซลล์ | ฝนรวมฤดู 2554 (อันดับ) | ฝนรวมฤดู 2569 (อันดับ) | ส.ค.–ก.ย. 2554/2569 | สูงสุด 7 วัน 2554/2569 | สูงสุด 30 วัน 2554/2569 | มัธยฐานฤดู (มม.) |",
          "|---|---|---|---|---|---|---|---|"]
    for bid, r in out["basins"].items():
        m = r["metrics"]
        md.append(f"| {r['label']} | {r['n_cells']} | {m['season_total']['v2554']:.0f} ({m['season_total']['rank2554']}) | "
                  f"{m['season_total']['v2569']:.0f} ({m['season_total']['rank2569']}) | "
                  f"{m['aug_sep_total']['rank2554']}/{m['aug_sep_total']['rank2569']} | "
                  f"{m['max7']['rank2554']}/{m['max7']['rank2569']} | {m['max30']['rank2554']}/{m['max30']['rank2569']} | "
                  f"{m['season_total']['median']:.0f} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("เขียนแล้ว:", OUT_JSON, flush=True)


if __name__ == "__main__":
    main()
