"""ลุ่มน้ำบางปะกงทั้งลุ่ม (ไม่แบ่งตามจังหวัด) และเหตุที่ฉะเชิงเทรา "ท่วมหนักและท่วมนาน" — วิเคราะห์จากข้อมูลที่มี ไม่ใช้ข้อสรุปล่วงหน้า
คำถามที่ตั้งก่อนดูผล: (1) พื้นที่น้ำท่วมสัมพันธ์กับ "ระดับความสูงพื้นดิน" มากกว่าเส้นเขตจังหวัดหรือไม่ · (2) ฉะเชิงเทรา อยู่ปลายลุ่มรับน้ำจากพื้นที่เหนือน้ำเท่าใด และพื้นราบต่ำเพียงใดเมื่อเทียบจังหวัดเหนือน้ำ ·
(3) ณ ปัจจุบัน ระดับน้ำสถานีในลุ่มยังสูงกว่าตลิ่งหรือไม่ และนานกี่วัน · (4) ท่วมซ้ำซากหรือไม่ (ความถี่น้ำท่วม 14 ปีของ GISTDA)
ข้อจำกัด: ชั้นน้ำท่วม 30 วันของ GISTDA เป็นชั้นผสมหลายภาพ (ทุกรูปทรงมีรายชื่อฉากเดียวกัน) แยกวันท่วมต่อแปลงไม่ได้ จึงใช้ "พื้นที่ ณ วันดึงข้อมูล" เท่านั้น ·
ความสูงใช้ FABDEM ที่ปรับด้วยตารางส่วนต่างจาก DEM 5 ม. (ความไม่แน่นอน ±0.7–1.0 ม. นอกหน้าต่าง DEM 5 ม.) · ครอบคลุมเฉพาะจังหวัดที่อยู่ในแผ่น FABDEM ที่มี (ไม่รวมสระแก้ว/ชลบุรีตอนล่าง)
รัน: python analysis/goal7_bangpakong_chachoengsao.py
ผลลัพธ์: analysis/goal7/bangpakong_chachoengsao.json
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

import numpy as np
import rasterio
import rasterio.features
import rasterio.windows
import shapefile
from pyproj import Transformer
from shapely.geometry import Point, shape as shp_shape
from shapely.ops import transform as shp_transform, unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal6_basin_rain as br  # noqa: E402  (reuse-first: HydroBASINS lev08 · ไล่ต้นน้ำ)
import goal7_dem_bias_correction as bc  # noqa: E402  (reuse-first: ตารางปรับ FABDEM)

PACKS = ROOT / "data/10_mitrearth_gis/thailand_provinces_full"
GIST = ROOT / "data/12_gistda_flood/raw/provinces"
FAB = ROOT / "data/08_dem_topography/fabdem"
SERIES = ROOT / "data/34_goal7_bangpakong/raw/station_series"
SNAP = ROOT / "data/34_goal7_bangpakong/raw"
BIAS = ROOT / "analysis/goal7/dem_bias_correction.json"
OUT = ROOT / "analysis/goal7/bangpakong_chachoengsao.json"
TO_UTM = Transformer.from_crs(4326, 32647, always_xy=True).transform
PROV = {"ฉะเชิงเทรา": "10 ", "นครนายก": "18 ", "ปราจีนบุรี": "31 "}
ELEV_BINS = [(-9, 2, "ต่ำกว่า 2 ม."), (2, 5, "2–5 ม."), (5, 10, "5–10 ม."), (10, 25, "10–25 ม."), (25, 999, "สูงกว่า 25 ม.")]
STEP = 3                      # FABDEM ~30 ม. → ตาราง ~90 ม.
LON0, LON1, LAT0, LAT1 = 100.3, 102.0, 13.0, 14.7
MOUTH = (13.45, 100.99)        # ปากแม่น้ำบางปะกง


def reader(p: Path):
    b = p.with_suffix("")
    return shapefile.Reader(shp=open(f"{b}.shp", "rb"), shx=open(f"{b}.shx", "rb"))


def province_outline(name: str):
    d = next(p for p in PACKS.iterdir() if p.name.startswith(PROV[name]))
    f = next(p for p in d.rglob("*.shp") if p.name.lower().endswith("tambon area.shp"))
    gs = []
    for s in reader(f).iterShapes():
        g = shp_shape(s.__geo_interface__)
        gs.append(g if g.is_valid else g.buffer(0))
    return unary_union(gs)


def terrain():
    """FABDEM (ปรับแล้ว) ตาราง ~90 ม. คลุมลองจิจูด 100.3–102.0 ละติจูด 13.0–14.7 — คืน (ความสูง, transform)"""
    tbl = json.loads(BIAS.read_text(encoding="utf-8"))["bias_table_by_fabdem_height"]
    res = STEP / 3600.0
    nx, ny = int(round((LON1 - LON0) / res)), int(round((LAT1 - LAT0) / res))
    arr = np.full((ny, nx), np.nan, dtype="float32")
    tr = rasterio.transform.from_origin(LON0, LAT1, res, res)
    for f in sorted(FAB.glob("N*E*_FABDEM_V1-2.tif")):
        m = re.match(r"N(\d+)E(\d+)", f.name)
        la, lo = int(m.group(1)), int(m.group(2))
        if la + 1 <= LAT0 or la >= LAT1 or lo + 1 <= LON0 or lo >= LON1:
            continue
        with rasterio.open(f) as ds:
            a = ds.read(1, out_shape=(3600 // STEP, 3600 // STEP), resampling=rasterio.enums.Resampling.average).astype("float32")
        a[a < -100] = np.nan
        r0, c0 = int(round((LAT1 - (la + 1)) / res)), int(round((lo - LON0) / res))
        r1, c1 = max(r0, 0), max(c0, 0)
        sub = a[r1 - r0:, c1 - c0:]
        sub = sub[: ny - r1, : nx - c1]
        arr[r1:r1 + sub.shape[0], c1:c1 + sub.shape[1]] = sub
    ok = ~np.isnan(arr)
    arr[ok] = bc.correct(arr[ok], tbl)
    return arr, tr


def cell_area_km2(tr, ny):
    res = tr.a
    lat = LAT1 - (np.arange(ny) + 0.5) * res
    return (res * 111.32) * (res * 111.32 * np.cos(np.radians(lat)))   # ตร.กม. ต่อเซลล์ รายแถว


def zone_of(z):
    out = np.full(z.shape, -1, dtype="int8")
    for i, (lo, hi, _) in enumerate(ELEV_BINS):
        out[(z >= lo) & (z < hi)] = i
    return out


def flood_raster(files, shape, tr, mask):
    """สัดส่วนน้ำท่วมต่อเซลล์ (0–1) — รูปทรงของ GISTDA ใหญ่กว่าพื้นที่น้ำท่วมจริง (f_area ไม่รวมแหล่งน้ำถาวร) จึงถ่วงด้วย f_area/พื้นที่รูปทรง
    (สมมติกระจายเท่ากันในรูปทรง — เป็นค่าประมาณ ผลรวมพื้นที่ตรงกับ f_area ของ GISTDA)"""
    items = []
    for f in files:
        for ft in json.loads(Path(f).read_text(encoding="utf-8")):
            try:
                g = shp_shape(ft["geometry"])
            except Exception:   # noqa: BLE001
                continue
            la = g.centroid.y
            geom_m2 = g.area * (111320.0 ** 2) * np.cos(np.radians(la))
            frac = min(1.0, (ft["properties"].get("f_area") or 0.0) / geom_m2) if geom_m2 > 0 else 0.0
            items.append((g, float(frac)))
    ras = rasterio.features.rasterize(items, out_shape=shape, transform=tr, fill=0.0, dtype="float32")
    ras[~mask] = 0.0
    return ras


def gauges():
    snap = next(iter(sorted(SNAP.glob("*_waterlevel_load.json"))[-1:]))
    cur = {r["station"]["id"]: r for r in json.loads(snap.read_text(encoding="utf-8"))["waterlevel_data"]["data"]}
    outl = {n: province_outline(n) for n in PROV}
    rows = []
    for f in sorted(SERIES.glob("*.json")):
        sid = int(f.stem.rsplit("_", 1)[1])
        d = json.loads(f.read_text(encoding="utf-8"))["data"]
        g = [(dt.datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M"), x["value"]) for x in d["graph_data"] if x.get("value") is not None]
        r = cur.get(sid)
        if not g or r is None:
            continue
        st = r["station"]
        bank = d.get("min_bank") or st.get("min_bank")
        if bank is None:
            continue
        pt = Point(st["tele_station_long"], st["tele_station_lat"])
        prov = next((n for n, o in outl.items() if o.contains(pt)), "อื่น ๆ")
        ts, v = zip(*g)
        v = np.array(v, dtype=float)
        step_h = np.median(np.diff([t.timestamp() for t in ts])) / 3600.0
        above = v > bank
        last_t = ts[-1]
        day = np.array([(last_t - t).total_seconds() / 86400.0 for t in ts])
        run = 0.0
        for k in range(len(v) - 1, -1, -1):          # ช่วงต่อเนื่องที่สูงกว่าตลิ่งจนถึงค่าล่าสุด
            if not above[k]:
                break
            run = day[k]
        peak_k = int(np.argmax(v))
        rows.append({"code": st.get("tele_station_oldcode"), "name": st["tele_station_name"]["th"], "province": prov,
                     "lat": st["tele_station_lat"], "lon": st["tele_station_long"], "bank_m": round(float(bank), 2),
                     "latest_m": round(float(v[-1]), 2), "latest_time": ts[-1].strftime("%Y-%m-%d %H:%M"), "latest_minus_bank_m": round(float(v[-1] - bank), 2),
                     "peak_m": round(float(v.max()), 2), "peak_time": ts[peak_k].strftime("%Y-%m-%d %H:%M"),
                     "hours_above_bank_30d": round(float(above.sum() * step_h), 0), "run_above_bank_days_to_latest": round(run, 1),
                     "change_last_7d_m": round(float(np.mean(v[day <= 1.0]) - np.mean(v[(day > 7.0) & (day <= 8.0)])) if (day > 7.0).any() else None, 2) if (day > 7.0).any() else None,
                     "situation_level": r.get("situation_level")})
    rows.sort(key=lambda x: (x["province"], x["code"] or ""))
    return {"snapshot": snap.name, "window_days": 30, "stations": rows,
            "above_bank_now": [x["code"] for x in rows if x["latest_minus_bank_m"] > 0],
            "note": "ตลิ่ง = min_bank ของระบบ thaiwater (ตลิ่งฝั่งต่ำ) · ระดับสูงกว่าตลิ่งหมายถึงน้ำล้นตลิ่งที่จุดนั้น ไม่ได้หมายความว่าท่วมทั้งตำบล"}


def gistda_30d():
    out = {}
    for pv in ("ฉะเชิงเทรา", "ปราจีนบุรี", "นครนายก"):
        row = {}
        for tag, fn in (("2026-10-16", f"{pv}_30days_2026-10-16.json"), ("2026-10-20", f"{pv}_30days.json")):
            fs = json.loads((GIST / fn).read_text(encoding="utf-8"))
            am = {}
            for ft in fs:
                p = ft["properties"]
                a = am.setdefault(p["ap_tn"], {"area_km2": 0.0, "rice_km2": 0.0, "pop": 0})
                a["area_km2"] += (p.get("f_area") or 0) / 1e6
                a["rice_km2"] += (p.get("rice_area") or 0) / 1e6
                a["pop"] += p.get("population") or 0
            row[tag] = {"total_km2": round(sum(x["area_km2"] for x in am.values()), 1), "rice_km2": round(sum(x["rice_km2"] for x in am.values()), 1),
                        "by_amphoe": {k: {"area_km2": round(v["area_km2"], 1), "rice_km2": round(v["rice_km2"], 1)} for k, v in sorted(am.items(), key=lambda kv: -kv[1]["area_km2"])}}
        out[pv] = row
    return out


def gistda_recent():
    """ชั้นน้ำท่วม 1 / 3 / 7 วันล่าสุดของ GISTDA (ดึง 20 ต.ค.) — 7 วันคลุมฉากหลายดาวเทียมถึง 20 ต.ค. ; 1–3 วันคลุมแนวเดียวของฉากเดียวจึงใช้เทียบทั้งจังหวัดไม่ได้"""
    out = {}
    for pv in ("ฉะเชิงเทรา", "ปราจีนบุรี", "นครนายก"):
        row = {}
        for ep in ("1day", "3days", "7days"):
            f = GIST / f"{pv}_{ep}.json"
            if not f.exists():
                continue
            fs = json.loads(f.read_text(encoding="utf-8"))
            sc = sorted(set(re.findall(r"([A-Za-z0-9]+_2026\d{4}_\d{4})", " ".join(x["properties"]["file_name"] for x in fs[:200]))))
            am = {}
            for ft in fs:
                q = ft["properties"]
                am[q["ap_tn"]] = am.get(q["ap_tn"], 0.0) + (q.get("f_area") or 0) / 1e6
            row[ep] = {"area_km2": round(sum(am.values()), 1), "scenes": sc, "by_amphoe": {k: round(v, 1) for k, v in sorted(am.items(), key=lambda kv: -kv[1])}}
        row["share_of_30d_still_in_7d_pct"] = None
        out[pv] = row
    return out


def flood_freq():
    out = {}
    for pv in ("ฉะเชิงเทรา", "นครนายก", "ปราจีนบุรี"):
        f = GIST / f"{pv}_flood-freq.json"
        if not f.exists():
            continue
        fs = json.loads(f.read_text(encoding="utf-8"))
        tot = 0.0
        by = {}
        yrs = {y: 0.0 for y in range(2011, 2025)}
        am = {}
        for ft in fs:
            p = ft["properties"]
            km2 = (p.get("area_rai") or 0) * 1600.0 / 1e6
            fr = int(p.get("freq") or 0)
            tot += km2
            by[fr] = by.get(fr, 0.0) + km2
            for y in yrs:
                if p.get(f"y_{y}"):
                    yrs[y] += km2
            a = am.setdefault(p.get("ap_tn"), {"ever": 0.0, "ge3": 0.0, "ge5": 0.0})
            a["ever"] += km2
            a["ge3"] += km2 if fr >= 3 else 0
            a["ge5"] += km2 if fr >= 5 else 0
        out[pv] = {"ever_flooded_km2": round(tot, 1), "ge3_years_km2": round(sum(v for k, v in by.items() if k >= 3), 1), "ge5_years_km2": round(sum(v for k, v in by.items() if k >= 5), 1),
                   "ge8_years_km2": round(sum(v for k, v in by.items() if k >= 8), 1), "per_year_km2": {str(k): round(v, 1) for k, v in yrs.items()},
                   "by_amphoe": {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in sorted(am.items(), key=lambda kv: -kv[1]["ever"])}}
    return out


def basin_frame(outlines):
    recs = br.read_lev08()
    near = [r for r in recs if r["geom"].distance(Point(MOUTH[1], MOUTH[0])) < 0.15]
    mouth = max(near, key=lambda r: r["up_area"])
    ids = br.upstream_ids(recs, mouth["id"])
    polys = [r for r in recs if r["id"] in ids]
    basin = unary_union([r["geom"] for r in polys])
    area = shp_transform(TO_UTM, basin).area / 1e6
    ov = {}
    for n, o in outlines.items():
        a_p = shp_transform(TO_UTM, o).area / 1e6
        a_i = shp_transform(TO_UTM, o.intersection(basin)).area / 1e6
        ov[n] = {"province_km2": round(a_p, 0), "in_basin_km2": round(a_i, 0), "share_of_province_in_basin_pct": round(100 * a_i / a_p, 1), "share_of_basin_pct": round(100 * a_i / area, 1)}
    # พื้นที่รับน้ำเหนือสถานี BPK003 (บางน้ำเปรี้ยว) และ Kgt.1 (กบินทร์บุรี)
    ups = {}
    for code, (lat, lon) in {"BPK003 บางน้ำเปรี้ยว": (13.87032, 101.14574), "Kgt.1 สะพานณรงค์ดำริ (กบินทร์บุรี)": (14.05144, 101.367378), "Kgt.3 สะพานต้นน้ำบางปะกง": (13.98666, 101.705406)}.items():
        pol, dist = br.gauge_polygon(recs, lat, lon)
        up = br.upstream_ids(recs, pol["id"])
        ups[code] = {"upstream_area_km2": round(sum(r["up_area"] for r in recs if r["id"] == pol["id"]), 0) or None,
                     "area_union_km2": round(shp_transform(TO_UTM, unary_union([r["geom"] for r in recs if r["id"] in up])).area / 1e6, 0), "snap_deg": round(dist, 3)}
    return {"hydrobasins_level": 8, "n_subbasins": len(polys), "basin_area_km2": round(area, 0), "mouth_up_area_km2_hydrosheds": round(mouth["up_area"], 0), "overlap_with_provinces": ov, "upstream_of_gauges": ups}


def variance_explained(prov_id, zone, flooded, valid):
    """สัดส่วนความแปรผันของ "สัดส่วนน้ำท่วมต่อเซลล์" ที่อธิบายได้ด้วยกลุ่ม (1 − SSE/SST) บนเซลล์ในจังหวัดที่ศึกษา"""
    y = flooded[valid].astype(float)       # สัดส่วนน้ำท่วมต่อเซลล์ (0–1)
    sst = ((y - y.mean()) ** 2).sum()

    def r2(g):
        ssw = 0.0
        for k in np.unique(g):
            m = g == k
            ssw += ((y[m] - y[m].mean()) ** 2).sum()
        return 1 - ssw / sst
    gp, gz = prov_id[valid], zone[valid]
    return {"by_province": round(float(r2(gp)), 3), "by_elevation_zone": round(float(r2(gz)), 3), "by_both": round(float(r2(gp * 10 + gz)), 3)}


def daily_means(code_id: str):
    d = json.loads((SERIES / f"{code_id}.json").read_text(encoding="utf-8"))["data"]
    by = {}
    for x in d["graph_data"]:
        if x.get("value") is not None:
            by.setdefault(x["datetime"][:10], []).append(x["value"])
    return {k: sum(v) / len(v) for k, v in sorted(by.items())}, d.get("min_bank")


def bpk_story(gs):
    """ลำดับเวลายอดน้ำเหนือน้ำ → บางน้ำเปรี้ยว (BPK003) · อัตราลดระดับ · ความชันผิวน้ำระหว่างสถานี (ระยะเส้นตรง = ขอบบนของความชัน)"""
    st = {s["code"]: s for s in gs["stations"]}
    up = ["Kgt.3", "Kgt.6", "PRC004", "PRC005", "Kgt.1"]
    peaks = {c: st[c]["peak_time"] for c in up if c in st}
    t_up = min(dt.datetime.strptime(v, "%Y-%m-%d %H:%M") for v in peaks.values())
    t_b = dt.datetime.strptime(st["BPK003"]["peak_time"], "%Y-%m-%d %H:%M")
    dm, bank = daily_means("BPK003_151")
    days = sorted(dm)
    last7 = days[-8:]
    rate = (dm[last7[0]] - dm[last7[-1]]) / (len(last7) - 1)
    need = (dm[last7[-1]] - bank) / rate if rate > 0 else None
    la, lo = st["BPK003"]["lat"], st["BPK003"]["lon"]

    def km(a, b):
        return float(np.hypot((a["lat"] - b["lat"]) * 111.32, (a["lon"] - b["lon"]) * 111.32 * np.cos(np.radians(la))))
    slopes = {}
    for a, b in (("Kgt.1", "BPK003"), ("BPK003", "BPK001")):
        d_km = km(st[a], st[b])
        slopes[f"{a}→{b}"] = {"straight_km": round(d_km, 1), "level_drop_m": round(st[a]["latest_m"] - st[b]["latest_m"], 2), "slope_m_per_km_upper_bound": round((st[a]["latest_m"] - st[b]["latest_m"]) / d_km, 3)}
    return {"upstream_peak_times": peaks, "first_upstream_peak": t_up.strftime("%Y-%m-%d %H:%M"), "bpk003_peak_time": st["BPK003"]["peak_time"], "lag_first_upstream_to_bpk003_days": round((t_b - t_up).total_seconds() / 86400.0, 1),
            "bpk003_recession_m_per_day_last7d": round(rate, 3), "bpk003_days_to_bank_if_same_rate": round(need, 0) if need else None,
            "note_extrapolation": "ประมาณจากอัตราลดระดับ 7 วันล่าสุดคงที่ — ไม่ได้พยากรณ์ (ฝนใหม่ น้ำทะเลหนุน และการระบายตามประตูทำให้เปลี่ยนได้)",
            "surface_slopes": slopes, "bpk003_upstream_area_km2": None}


def main() -> None:
    outlines = {n: province_outline(n) for n in PROV}
    z, tr = terrain()
    ny, nx = z.shape
    area = cell_area_km2(tr, ny)[:, None] * np.ones((1, nx))
    zone = zone_of(z)
    pid = np.zeros(z.shape, dtype="int8")
    masks = {}
    for i, (n, o) in enumerate(outlines.items(), 1):
        m = rasterio.features.rasterize([(o, 1)], out_shape=z.shape, transform=tr, fill=0, dtype="uint8").astype(bool) & ~np.isnan(z)
        masks[n] = m
        pid[m] = i
    flood = flood_raster([GIST / f"{n}_30days.json" for n in PROV], z.shape, tr, pid > 0)
    flood7 = flood_raster([GIST / f"{n}_7days.json" for n in PROV], z.shape, tr, pid > 0)
    terr = {}
    for n, m in masks.items():
        zz = z[m]
        row = {"land_km2": round(float(area[m].sum()), 0), "median_elev_m": round(float(np.median(zz)), 1),
               "flooded_km2_grid": round(float((area * flood)[m].sum()), 0), "flooded_pct": round(100 * float((area * flood)[m].sum() / area[m].sum()), 1), "by_elevation": {}}
        for i, (lo, hi, lab) in enumerate(ELEV_BINS):
            mz = m & (zone == i)
            a_all, a_fl = float(area[mz].sum()), float((area * flood)[mz].sum())
            a_7 = float((area * flood7)[mz].sum())
            row["by_elevation"][lab] = {"land_pct": round(100 * a_all / float(area[m].sum()), 1), "land_km2": round(a_all, 0), "flooded_km2": round(a_fl, 0), "flooded_pct_of_zone": round(100 * a_fl / a_all, 1) if a_all else None,
                                        "flooded_7d_km2": round(a_7, 0), "still_flooded_7d_share_of_30d_pct": round(100 * a_7 / a_fl, 0) if a_fl > 1 else None}
        terr[n] = row
    all_m = pid > 0
    zone_all = {}
    for i, (lo, hi, lab) in enumerate(ELEV_BINS):
        mz = all_m & (zone == i)
        a_all, a_fl = float(area[mz].sum()), float((area * flood)[mz].sum())
        zone_all[lab] = {"land_km2": round(a_all, 0), "flooded_km2": round(a_fl, 0), "flooded_pct_of_zone": round(100 * a_fl / a_all, 1) if a_all else None}
    rng = np.random.default_rng(7)
    idx = np.flatnonzero(all_m.ravel() & (zone.ravel() >= 0))
    sub = rng.choice(idx, size=min(400000, idx.size), replace=False)
    v = np.zeros(z.size, dtype=bool)
    v[sub] = True
    ve = variance_explained(pid.ravel(), zone.ravel(), flood.ravel(), v)
    basin = basin_frame(outlines)
    res = {"generated": dt.date.today().isoformat(), "terrain": {"cell_m": 90, "dem": "FABDEM ปรับด้วยตารางส่วนต่าง DEM 5 ม.", "provinces": terr, "all_three_by_elevation": zone_all,
                                                              "variance_explained_flooded_cells": ve, "sampled_cells": int(sub.size)},
           "basin": basin, "gistda_30d": gistda_30d(), "gistda_recent": (gr := gistda_recent()), "flood_freq": flood_freq(), "gauges": (gs := gauges())}
    res["story"] = bpk_story(gs)
    for pv, v in gr.items():
        if "7days" in v:
            v["share_of_30d_still_in_7d_pct"] = round(100 * v["7days"]["area_km2"] / res["gistda_30d"][pv]["2026-10-20"]["total_km2"], 0)
    res["story"]["bpk003_upstream_area_km2"] = basin["upstream_of_gauges"]["BPK003 บางน้ำเปรี้ยว"]["area_union_km2"]
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("basin",)}, ensure_ascii=False, indent=1)[:1500])
    print(json.dumps(res["terrain"], ensure_ascii=False, indent=1)[:3500])


if __name__ == "__main__":
    main()
