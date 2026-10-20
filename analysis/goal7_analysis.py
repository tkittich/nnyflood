"""เป้าหมาย 7 — วิเคราะห์เบื้องต้นคลองเจ้าพระยา2 (K3–K8) → analysis/goal7/canonical.json

อินพุต (ทั้งหมดมีอยู่ใน repo — ไม่ดึงใหม่):
  data/32_goal7_chaophraya2/derived/{centerline,km_markers}.geojson   (goal7_clean_alignment.py)
  analysis/goal7/structures_all.csv                                (ถอดด้วยตาจากภาพ P2_01–14 — ต้องตรวจซ้ำ)
  data/08_dem_topography/raw/*.tif   Copernicus GLO-30 (DSM ±2–4 ม.)
  data/22_goal6_network/raw/C2_nakhonsawan_waterlevel_hourly_*.json   ปริมาณน้ำรายชั่วโมง C.2
  analysis/goal6/dam_inflow.json                                      น้ำเข้า–ปล่อยเขื่อนป่าสัก 2554/2569
  data/manual/shp_*/                                                  GISTDA น้ำท่วมจากดาวเทียม (S1/RADARSAT-2)
นิยาม/เกณฑ์ลงทะเบียนไว้ใน docs/GOAL7_PLAN.md ก่อนดูผล · ตัวตรวจแยกอยู่ที่ tests/test_goal7_report.py
ข้อควรระวัง: แนวคลองมาจาก My Maps (ไม่ใช่ข้อมูลทางการ) — ทุกผลที่ใช้แนวนี้เป็น "ประมาณ"
"""
import csv, glob, json, math, os, warnings
from collections import Counter
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal7_source_constants import value as _K  # noqa: E402  ค่านำเข้าที่มีแหล่งอ้างอิง

import numpy as np
import rasterio
import shapefile
from scipy.optimize import brentq
from shapely.geometry import LineString, Point, shape
from shapely.ops import substring, unary_union

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
D7 = ROOT / "data/32_goal7_chaophraya2/derived"
OUT = ROOT / "analysis/goal7"
LAT0, LON0 = 14.2, 100.9
KX = 111.32e3 * math.cos(math.radians(LAT0)); KY = 110.57e3

def to_m(lon, lat): return np.c_[(np.asarray(lon) - LON0) * KX, (np.asarray(lat) - LAT0) * KY]

# ขอบเขตโดยประมาณจากภาพแผนที่ (ตรวจด้วยตา — ใช้ประกอบเท่านั้น)
KM_NN0, KM_NN1 = 38.6, 73.2
KM_SP0 = 111.0               # ภาพ P1_05: เข้า อ.บางบ่อ จ.สมุทรปราการ ราว กม.111
WIDTH_170_UNTIL_KM = 23.0   # ภาพ P2_05: 170 ม. ถึง ~กม.23 แล้ว 200 ม.


def bucket(km):
    if km < KM_NN0: return "สระบุรี"
    if km <= KM_NN1: return "นครนายก"
    return "ฉะเชิงเทรา" if km < KM_SP0 else "สมุทรปราการ"


def structures():
    rows = list(csv.DictReader(open(OUT / "structures_all.csv", encoding="utf-8")))
    for r in rows: r["km"] = float(r["km"])
    by = {}
    for b in ("สระบุรี", "นครนายก", "ฉะเชิงเทรา", "สมุทรปราการ"):
        rs = [r for r in rows if bucket(r["km"]) == b]
        c = Counter(r["kind"] for r in rs)
        by[b] = {"n": len(rs), "kinds": dict(c)}
    nn = [r for r in rows if bucket(r["km"]) == "นครนายก"]
    sip = [r["km"] for r in nn if r["kind"] == "ท่อระบายน้ำและไซฟอน"]
    named_canal = [r for r in nn if r["kind"] == "ท่อระบายน้ำและไซฟอน" and r["name"]]
    return {
        "n_total": len(rows),
        "n_crossing_old_canals": sum(1 for r in rows if r["kind"] in ("ท่อระบายน้ำและไซฟอน", "อาคารเชื่อมจุดตัดคลอง")),
        "all_rows": rows,
        "by_province": by,
        "nakhonnayok": {
            "km_from": KM_NN0, "km_to": KM_NN1, "length_km": round(KM_NN1 - KM_NN0, 1),
            "n_siphon": len(sip), "n_siphon_named": len(named_canal),
            "mean_spacing_km": round((KM_NN1 - KM_NN0) / len(sip), 1),
            "n_bridge": sum(1 for r in nn if r["kind"] == "สะพานรถยนต์"),
            "n_gate": sum(1 for r in nn if r["kind"] == "ประตูระบายน้ำ"),
            "siphons": [{"km": r["km"], "name": r["name"]} for r in nn if r["kind"] == "ท่อระบายน้ำและไซฟอน"],
        },
        "sheets_checked": "ครบ 24 แผ่น: P2_01–14 (กม.0–81) และ P1_01–10 (กม.78–135.6) — อ่านด้วยตาจากภาพย่อ",
    }


def dem_profile():
    tiles = {(14, 100): "N14_00_E100", (14, 101): "N14_00_E101", (13, 100): "N13_00_E100", (13, 101): "N13_00_E101"}
    ds = {k: rasterio.open(ROOT / f"data/08_dem_topography/raw/Copernicus_DSM_COG_10_{v}_00_DEM.tif") for k, v in tiles.items()}
    def z(lon, lat):
        return float(next(ds[(math.floor(lat), math.floor(lon))].sample([(lon, lat)]))[0])
    def zmed(lon, lat, r=0.0006):
        return float(np.median([z(lon + dx, lat + dy) for dx in (-r, 0, r) for dy in (-r, 0, r)]))
    mk = json.load(open(D7 / "km_markers.geojson"))["features"]
    pts = sorted((f["properties"]["km"], *f["geometry"]["coordinates"]) for f in mk)
    prof = [{"km": int(km), "ground_m": round(zmed(lon, lat), 1)} for km, lon, lat in pts if km == int(km) and int(km) % 10 == 0]
    trans = []
    for km in (45, 50, 55, 60):
        km_, lon, lat = [p for p in pts if p[0] == km][0]
        vals = []
        for dkm in (-12, -8, -4, 0, 4, 8, 12):
            vals.append(zmed(lon + dkm / (111.32 * math.cos(math.radians(lat))), lat))
        trans.append({"km": km, "range_m": round(max(vals) - min(vals), 1)})
    g = {p["km"]: p["ground_m"] for p in prof}
    slope = (g[40] - g[100]) / 60.0
    return {"profile_every_10km": prof, "ew_transects_range_m": trans,
            "mean_slope_m_per_km_40_100": round(slope, 3), "note": "DSM ±2–4 ม. — ค่าประกอบ ไม่ใช่ค่าสำรวจ"}


def manning():
    def Q(y, b, z, n, S):
        A = (b + z * y) * y; P = b + 2 * y * (1 + z * z) ** .5
        return A / n * (A / P) ** (2 / 3) * S ** .5
    rows = []
    for b in (100, 130, 170):
        for n in (0.015, 0.025):
            for S in (0.00002, 0.00005):
                y = brentq(lambda y: Q(y, b, 2, n, S) - 600, 0.1, 30)
                A = (b + 2 * y) * y
                rows.append({"bottom_width_m": b, "n": n, "slope_m_per_km": S * 1000,
                             "depth_m": round(y, 1), "velocity_ms": round(600 / A, 2)})
    d = [r["depth_m"] for r in rows]
    return {"Q_m3s": 600, "side_slope": "1:2", "rows": rows,
            "depth_min_m": min(d), "depth_max_m": max(d)}


def c2_peaks():
    out = {}
    for f in sorted(glob.glob(str(ROOT / "data/22_goal6_network/raw/C2_nakhonsawan_waterlevel_hourly_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        day = {}
        for r in d["graph_data"]:
            if r.get("discharge") is not None:
                day.setdefault(r["datetime"][:10], []).append(r["discharge"])
        if not day: continue
        dm = {k: sum(v) / len(v) for k, v in day.items()}
        k = max(dm, key=dm.get)
        out[int(d["year"])] = {"peak_daily_m3s": round(dm[k]), "date": k, "n_days": len(dm)}
    return {"station": "C.2 นครสวรรค์ (ต้นน้ำเขื่อนเจ้าพระยา)", "qmax_api_m3s": 3735, "years": out,
            "canal_new_reach_m3s": 600, "canal_old_reach_m3s": 930}


def pasak_dam():
    di = json.load(open(ROOT / "analysis/goal6/dam_inflow.json", encoding="utf-8"))["dams"]["ป่าสักชลสิทธิ์"]
    return {y: {"peak_inflow_m3s": di[y]["peak_inflow"], "peak_release_m3s": di[y]["peak_release"]}
            for y in ("y2554", "y2569")}


def corridor_area(L_km):
    a = {"all170": L_km * 0.17, "all200": L_km * 0.20,
         "mixed": WIDTH_170_UNTIL_KM * 0.17 + (L_km - WIDTH_170_UNTIL_KM) * 0.20}
    seg = sum(s["length_km"] * s["corridor_m"] / 1000 for s in DESIGN_SEGMENTS)
    return {"length_km": L_km,
            "rai": {**{k: round(v * 625) for k, v in a.items()}, "design_2569_segments": round(seg * 625)},
            "reported_rai": {"news_prachachat": 16208, "rid_2565": 16305, "rid_2569_sec2": 17703, "eia_2569_total": 16288, "eia_2569_canal": 15999},
            "note": "1 ตร.กม. = 625 ไร่ · ความกว้างอ่านจากภาพ (170 ม. ถึง ~กม.23 แล้ว 200 ม.) หรือจากตัวแปรออกแบบรายช่วงชั้น B (220/170/160 ม.) — เป็นค่าเทียบ ไม่ใช่ผลวัดที่ดินจริง · ตัวเลขทางการรวมเขื่อนทดน้ำ ทำนบ คลองเชื่อม ฯลฯ"}


def flood_band():
    cl = json.load(open(D7 / "centerline.geojson"))["features"][0]["geometry"]["coordinates"]
    xy = to_m([c[0] for c in cl], [c[1] for c in cl])
    line = LineString(xy)                      # ทิศ: อ่าวไทย → ชัยนาท
    mk = json.load(open(D7 / "km_markers.geojson"))["features"]
    pts = sorted((f["properties"]["km"], *f["geometry"]["coordinates"]) for f in mk)
    s = np.array([line.project(Point(*to_m([p[1]], [p[2]])[0])) for p in pts]); kms = np.array([p[0] for p in pts])
    o = np.argsort(s); s_o, k_o = s[o], kms[o]
    def s_of(km):  # km → ระยะสะสมบนเส้นกลาง (เรียงตาม s)
        idx = np.argsort(k_o); return float(np.interp(km, k_o[idx], s_o[idx]))
    a, b = sorted((s_of(KM_NN0), s_of(KM_NN1)))
    sub = substring(line, a, b)
    R = 10000.0
    left = sub.buffer(R, single_sided=True)     # ซ้ายของทิศไป = ตะวันตก (ทิศ: ใต้→เหนือ)
    right = sub.buffer(-R, single_sided=True)
    corridor = sub.buffer(100)
    res = {}
    for p in sorted(glob.glob(str(ROOT / "data/manual/shp_*"))):
        n = os.path.basename(p)[4:]
        r = shapefile.Reader(f"{p}/{n}.shp", encoding="latin-1")
        F = [f[0] for f in r.fields[1:]]
        W = E = C = 0.0; byamp = Counter(); nrec = 0
        for sr in r.iterShapeRecords():
            rec = dict(zip(F, sr.record))
            try: pv = int(rec["PV_IDN"])
            except Exception: continue
            g = shape(sr.shape.__geo_interface__)
            if not g.is_valid: g = g.buffer(0)
            gm = shape({"type": "MultiPolygon" if g.geom_type == "MultiPolygon" else "Polygon",
                        "coordinates": json.loads(json.dumps(g.__geo_interface__["coordinates"]))})
            # → เมตร
            from shapely.ops import transform
            gm = transform(lambda x, y, z=None: ((np.asarray(x) - LON0) * KX, (np.asarray(y) - LAT0) * KY), gm)
            w = gm.intersection(left).area; e = gm.intersection(right).area; c = gm.intersection(corridor).area
            if w or e or c:
                nrec += 1
                try: amp = bytes(str(rec["AP_TN"]), "latin-1").decode("utf-8")
                except Exception: amp = str(rec["AP_TN"])
                byamp[amp] += (w + e) / 1600
            W += w; E += e; C += c
        if nrec:
            res[n] = {"west_rai": round(W / 1600), "east_rai": round(E / 1600),
                      "on_corridor_100m_rai": round(C / 1600), "records": nrec,
                      "by_amphoe_rai": {k: round(v) for k, v in byamp.items()}}
    return {"reach_km": [KM_NN0, KM_NN1], "band_km_each_side": 10, "scenes": res,
            "note": "ซ้าย/ตะวันตก = ฝั่งกรุงเทพฯ·ปทุมธานี · ขวา/ตะวันออก = ฝั่งนครนายกเมือง·ปราจีนฯ · รวมเฉพาะรูปทรงน้ำท่วม GISTDA ที่ตัดกับแถบ"}


# ทะเบียนข้อเท็จจริงโครงการ (ค้นเมื่อ 15 ต.ค. 69 — รายละเอียดแหล่ง: docs/GOAL7_PLAN.md §2)
# ชั้น A = แถลง/เอกสารทางการ · B = สื่อรายงานอ้างหน่วยงาน · C = ภาคประชาชน/ผู้ใช้ — ต้องแทนด้วยชั้น A เมื่อได้เอกสาร
FACTS = {
    "cabinet_date": {"v": "29 ก.ย. 2569", "tier": "A", "src": "สำนักข่าวประชาสัมพันธ์; สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 (เสนอ ครม. ก.ย. 2569)"},
    "budget_mb": {"v": 165000, "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 (ตามที่ กนช. เห็นชอบ 3 ธ.ค. 2568)"},
    "years": {"v": "ปีงบประมาณ 2570–2577 (8 ปี)", "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569"},
    "old_reach_km": {"v": 134.365, "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 (ปรับปรุงคลองชัยนาท–ป่าสัก)"},
    "old_reach_q": {"v": 930, "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 · ฐานเศรษฐกิจ 2 ต.ค. 2569 แยก 800 คลองขุดใหม่ + 130 ปลายคลองเดิม · ค่า 2,730 ที่เคยพบไม่ได้รับการยืนยัน"},
    "new_reach_km": {"v": 135.655, "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 · ตรงกับหมุด กม. ปลายแผนที่ผู้ใช้ (135.655) · เอกสารกรมชลประทาน 2565 ใช้ 135.9"},
    "new_reach_q": {"v": 600, "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569"},
    "new_reach_earth_km": {"v": 23.0, "tier": "B", "src": "ฐานเศรษฐกิจ 2 ต.ค. 2569 (คลองดิน 0.57 + 22.43 กม.)"},
    "new_reach_lined_km": {"v": 112.655, "tier": "B", "src": "ฐานเศรษฐกิจ 2 ต.ค. 2569 (คลองดาดคอนกรีตรูปตัวยู)"},
    "storage_mcm": {"v": 155.77, "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 (ชัยนาท–ป่าสัก 98.37 + ป่าสัก–อ่าวไทย 57.4 ล้าน ลบ.ม.)"},
    "benefit_rai_m": {"v": 3.48, "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 — คำนวณจากเหตุการณ์ปี 2554 · ค่าคาดการณ์ของโครงการ"},
    "benefit_damage_mb": {"v": "5,085–16,938", "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 (เฉลี่ยต่อปี) · ค่าคาดการณ์ของโครงการ"},
    "land_cost_mb": {"v": 23329, "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 (ฐานเศรษฐกิจ: 23,328)"},
    "land_rai_2565": {"v": 16305, "tier": "A", "src": "เอกสารกรมชลประทาน มี.ค. 2565 (พื้นที่ก่อสร้าง: เขื่อนทดน้ำ 343 + คลอง 15,962 ไร่ · 38 ตำบล 11 อำเภอ 5 จังหวัด)"},
    "land_rai_2569_sec2": {"v": 17703, "tier": "B", "src": "ฐานเศรษฐกิจ 2 ต.ค. 2569 อ้างกรมชลประทาน (ช่วงป่าสัก–อ่าวไทย; รวมช่วงเดิม 781 = 18,484)"},
    "land_rai_news": {"v": 16208, "tier": "B", "src": "ประชาชาติธุรกิจ (5 จังหวัด)"},
    "land_rai_civic": {"v": 16305, "tier": "C", "src": "สมาคมพลเมืองนครนายก — ตรงกับตัวเลขเอกสารกรมชลประทาน 2565"},
    "houses_news": {"v": 2600, "tier": "B", "src": "ประชาชาติธุรกิจ (เรียก \"บ้านเรือน\" — รายงานผลกระทบสิ่งแวดล้อมระบุ 2,600 คือจำนวนผู้ถือครองที่ดิน)"},
    "land_rai_eia": {"v": 16288, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 ตาราง 3.4.2-1 (หน้า 3-384): 3,957 แปลง · คลอง 15,999 + เขื่อนทดน้ำป่าสัก 289 ไร่"},
    "owners_eia": {"v": 2600, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 ตาราง 3.4.2-1: ผู้ถือครองที่ดินที่ถูกเวนคืน 2,600 ราย"},
    "structures_eia": {"v": 1378, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 3-383 และ 4-50: สิ่งปลูกสร้าง 1,378 หลัง ค่าชดเชย 1,994 ล้านบาท"},
    "compensation_total_mb": {"v": 21794, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 4-50: ที่ดิน 19,677 + สิ่งปลูกสร้าง 1,994 + ไม้ยืนต้น 123 ล้านบาท"},
    "houses_civic": {"v": 1563, "tier": "C", "src": "สมาคมพลเมืองนครนายก"},
    "eirr_2565": {"v": "อัตราผลตอบแทนทางเศรษฐกิจ 14.52%", "tier": "A", "src": "เอกสารประชุมกลุ่มย่อยครั้งที่ 3 ระยะที่ 1 (20–23 มี.ค. 2566) · ตัวเลขเดียวกับบทสรุปผู้บริหารรายงานผลกระทบสิ่งแวดล้อม 2561 หน้า 82 — ยังไม่ทราบว่าชุดไหนเป็นที่มา"},
    "bcr_2569": {"v": "อัตราส่วนผลประโยชน์ต่อต้นทุน 2.12 (คิดลด 7%) · 1.48 (9%) · 0.97 (12%) · อัตราผลตอบแทนทางเศรษฐกิจ 10.94%", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 2 ตาราง 8.8-1 (หน้า 8-19)"},
    "design_depth_m": {"v": 7.0, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38 (กม.23–ปลายคลอง) · ข่าวปี 2564/2569 ระบุ 6 ม."},
    "design_bed_slope": {"v": "1:25,000 (0.04 ม./กม.)", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38"},
    "water_above_ground_m": {"v": "1–3.3", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38 (ระดับน้ำสูงสุดออกแบบสูงกว่าพื้นเดิม กม.23–ปลายคลอง · \"คลองลอย\")"},
    "crest_msl_end": {"v": "+4.00 ม.รทก. (กม.109–ปลายคลอง · เผื่อพ้นน้ำ 1.50 ม.)", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38 และ 2-79"},
    "end_water_level": {"v": "+1.50 หน้าประตูปลายคลอง · +2.50 หลังอัดน้ำ", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38"},
    "side_drain": {"v": "คูระบายน้ำกว้าง 3 ม. ลึก 1 ม. ด้านนอกคันทั้งสองฝั่ง", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-45"},
    "n_cross_structures_eia": {"v": 34, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-60 (อาคารเชื่อมคลองแบบท่อระบายน้ำ+ไซฟอน) — นับต่างจากตารางแผนที่ของรายงานนี้"},
    "eia_board": {"v": "คชก. เห็นชอบ พ.ค. 2568 · กก.วล. ครั้งที่ 6/2568 เห็นชอบ 18 ธ.ค. 2568", "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 — ชื่อในมติ ทางระบายน้ำหลากเจ้าพระยาฝั่งตะวันออกตอนล่าง (ป่าสัก–อ่าวไทย)"},
    "marine_design_sea_level_msl": {"v": "+2.00 ถึง +2.49 ม.รทก.", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้า 2-38 และแบบจำลองน้ำทะเลมหาอุทกภัยปี 2554"},
    "marine_swan_waves_m": {"v": "0.4–1.2 ม.", "tier": "A", "src": "แบบจำลองคลื่นทะเล (<code>SWAN</code>) คลังข้อมูลน้ำแห่งชาติ 31 สถานีอ่าวไทยตอนบน"},
    "marine_gravity_drop_cms": {"v": "891 เหลือ 107", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้า 2-82 (การไหลตามแรงโน้มถ่วงลดลงเมื่อน้ำทะเลหนุนสูงสุด)"},
    "marine_backwater_km": {"v": 60, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้า 2-83 (ระยะน้ำเท้อย้อนกลับถึงคลองรังสิต กม.74)"},
    "estuary_salinity_defense": {"v": "0.11–0.21 กรัม/ลิตร (สำแล) และ 6.63 กรัม/ลิตร (บางปะกง)", "tier": "A", "src": "สถานีโทรมาตรคุณภาพน้ำ กรมชลประทาน/คลังข้อมูลน้ำแห่งชาติ 16 สถานีปากแม่น้ำ"},
    "corridor_rainfall_telemetry_stations": {"v": 4593, "tier": "A", "src": "คลังข้อมูลน้ำแห่งชาติ: สถานีโทรมาตรวัดน้ำฝนอัตโนมัติ 4,593 สถานี ครอบคลุม 77 จังหวัดและ 5 หน่วยงานหลัก"},
}

def canal_volume_by_official_reaches() -> dict:
    """ปริมาตรคลองจากตารางรูปตัดทางการ 3 ช่วง (รูปที่ 2.3.2-11): กม.0–23 · 23–134 · 134–135.9 (ปลายคลองขยายปากแตร A 504→1187 ตร.ม.)
    ช่วงปลายไม่มีค่าตามแนวยาว จึงรายงานกรอบล่าง/บน (A คงที่ 504 หรือ 1187) และค่ากลาง (เชิงเส้น) — ใช้ตรวจ 504 × 135.9"""
    a1, a2, a3 = _K("eia_area_reach1_m2"), _K("eia_area_m2"), _K("eia_area_end_m2")
    k1, k2, kend = _K("eia_reach_break_1_km"), _K("eia_reach_break_2_km"), _K("canal_length_km")
    v1, v2 = a1 * k1 * 1000.0, a2 * (k2 - k1) * 1000.0
    tail = kend - k2
    lo, mid, hi = a2 * tail * 1000.0, (a2 + a3) / 2.0 * tail * 1000.0, a3 * tail * 1000.0
    flat = a2 * kend * 1000.0
    f = lambda x: round(x / 1e6, 2)  # noqa: E731
    return {"reach1_mcm": f(v1), "reach2_mcm": f(v2), "tail_km": round(tail, 3), "tail_low_mcm": f(lo), "tail_mid_mcm": f(mid), "tail_high_mcm": f(hi),
            "total_low_mcm": f(v1 + v2 + lo), "total_mid_mcm": f(v1 + v2 + mid), "total_high_mcm": f(v1 + v2 + hi), "flat_504_mcm": f(flat),
            "flat_vs_mid_pct": round(100.0 * (flat - (v1 + v2 + mid)) / (v1 + v2 + mid), 2)}


# บัญชีระงับข้อขัดแย้งตัวเลขสำคัญ (Reconciled Parameters Schema)
# ใช้ระงับข้อขัดแย้งระหว่างแหล่งข้อมูลต่างกาลเวลา (Vintage) ขอบเขต (Scope) และชั้นความน่าเชื่อถือ (Tier)
RECONCILED_PARAMETERS = {
    "canal_bed_width": {
        "canonical_value_m": 51.0,
        "unit": "ม.",
        "resolution": "ใช้ 51.0 ม. — พื้นที่หน้าตัดน้ำ 504 ตร.ม. ลึก 7.0 ม. ล้อมด้วยลาดด้านในทั้งสองฝั่ง (Z1 = 3.0): 504 = 7×(51+3×7) ลงตัวพอดี และเส้นรอบรูปเปียก P = 51 + 2×7×√(1+3²) = 95.27 ม. ตรงกับที่ตารางรูปตัดของรายงาน (หน้า 2-39) พิมพ์ไว้ · ลาดด้านนอก (Z2 = 2.0) อยู่ฝั่งดินคัน ไม่เกี่ยวกับพื้นที่น้ำ · ผู้ใช้ยืนยันว่ารูปที่ 2.3.2-11 ระบุท้องคลอง 51 ม. ตั้งแต่ กม.23",
        "variants": {
            "eia_2569_official": {"value": 51.0, "vintage": 2569, "tier": "A", "kind": "ระบุในรูปที่ 2.3.2-11 หน้า 2-39 (ผู้ใช้ยืนยัน) และสอดคล้องกับ A=504, P=95.27", "source": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-39 รูปที่ 2.3.2-11 และตารางรูปตัด กม.23–134"},
            "draft_2560_symmetric": {"value": 51.0, "vintage": 2560, "tier": "B", "source": "สรุปชี้แจง มี.ค. 2560 (ลาดข้างสมมาตร 1:3) — ตรงกับฉบับ 2569"},
            "mean_slope_misreading": {"value": 54.5, "status": "discredited", "reason": "ได้จากการเฉลี่ยลาดด้านใน 3.0 กับลาดด้านนอก 2.0 เป็น 2.5 ซึ่งไม่ใช่รูปตัดของน้ำ และให้ P = 92.3 ม. ขัดกับ 95.27 ที่รายงานพิมพ์ไว้ — เพิกถอน 19 ต.ค. 69"},
            "retired_legacy": {"value": 48.0, "status": "retired", "reason": "ค่าคงที่สมมติเดิมที่ย้อนจาก 55.4 ล้าน ลบ.ม. — ปลดประจำการ"}
        }
    },
    "canal_length": {
        "canonical_value_km": 135.655,
        "unit": "กม.",
        "resolution": "ใช้ 135.655 กม. (หมุด กม. สุดท้าย/สรุปการประชุมจังหวัด) เป็นความยาวช่วงใหม่หลัก · 135.7 เป็นค่าปัดของค่าเดียวกันในตารางเทียบ · 135.9 เป็นค่าตามแบบ มี.ค. 2565 ที่ใช้คำนวณปริมาตรกักเก็บ (504 ตร.ม. × ความยาว) — ยังไม่ปรับปริมาตรให้ใช้ 135.655 เพราะต่างกันเพียง 0.2%",
        "variants": {
            "provincial_summary_and_km_pins": {"value": 135.655, "vintage": 2569, "tier": "A", "source": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 · หมุด กม. ปลายแผนที่"},
            "rounded_135_7": {"value": 135.7, "vintage": 2569, "tier": "A", "source": "ค่าปัดของ 135.655 ในตารางเทียบและตารางอาคารตัดขวาง"},
            "rid_march_2565_design": {"value": 135.9, "vintage": 2565, "tier": "B", "source": "เอกสารกรมชลประทาน มี.ค. 2565 (ปลายคลองปรับในแบบหลัง) · ตรงกับข้อความเล่ม 1 หน้า 87"},
            "eia2569_vol1_p119_ring_road_alignment": {"value": 135.963, "vintage": 2569, "tier": "A", "source": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 119 (แนวร่วมถนนวงแหวนรอบ 3 ความยาวรวม 135.963 กม.)"}
        }
    },
    "opex_annual": {
        "canonical_value_mb": _K("opex_annual_mb"),
        "unit": "ล้านบาท/ปี",
        "resolution": "ใช้ 264.80 ล้านบาท/ปี — ตรวจกับชั้นข้อความของรายงานฉบับสมบูรณ์ 2569 เล่ม 2 หน้า 159 แล้ว · ค่า 519 มีจริงในรายงานชี้แจงเพิ่มเติมครั้งที่ 2 (ธ.ค. 2566) หน้า 121 (ตรวจชั้นข้อความ 20 ต.ค. 69) ใช้สูตรเดียวกันแต่ฐานงานใหญ่กว่าราว 2 เท่า (ค่าอุปกรณ์ทดแทน 982 เทียบ 487.50 ล้านบาท) จึงเป็นของขอบเขต/ราคาคนละฉบับ ไม่ใช่ค่าผิด — ใช้ 264.80 เพราะเป็นฉบับล่าสุดตรงกับขอบเขตที่วิเคราะห์ (การตีความ) · ผลต่อต้นทุนต่อลบ.ม. ที่คิดลดร้อยละ 7: 6.68 เทียบ 6.81 บาท",
        "variants": {
            "eia2569_vol2_p159": {"value": _K("opex_annual_mb"), "vintage": 2569, "tier": "A", "source": "รายงานผลกระทบสิ่งแวดล้อม ฉบับสมบูรณ์ เล่ม 2 หน้า 159 (ตรวจกับชั้นข้อความ PDF แล้ว)"},
            "clarification2_dec2566_p121": {"value": _K("clarify2_opex_annual_mb"), "vintage": 2566, "tier": "A", "status": "verified_text_different_scope", "source": "รายงานชี้แจงเพิ่มเติมครั้งที่ 2 (ธ.ค. 2566) หน้า 121 (ตรวจชั้นข้อความแล้ว) · ราคาคงที่ปี 2566 · ฐานงานใหญ่กว่า EIA 2569 ราว 2 เท่า"}
        }
    },
    "canal_storage": {
        "canonical_total_mcm": 68.5,
        "canonical_active_mcm": 53.0,
        "canonical_dead_mcm": 15.5,
        "unit": "ล้าน ลบ.ม.",
        "resolution": "คำนวณจากพื้นที่หน้าตัดออกแบบ 504 ตร.ม. × ความยาว 135.9 กม. ได้ปริมาตรรวม 68.5 ล้าน ลบ.ม. หักน้ำก้นคลอง 2.0 ม. (15.5 ล้าน ลบ.ม. — ระดับ 2.0 ม. เป็นข้อสมมติของผู้จัดทำ ไม่ใช่ค่าจาก EIA) เหลือความจุใช้การ 53.0 ล้าน ลบ.ม. (เวลาเติมคลองที่ว่าง 24.5 ชั่วโมงที่ 600 ลบ.ม./วินาที)",
        "variants": {
            "eia_2569_geometric_derived": {"total": 68.5, "active": 53.0, "dead": 15.5, "tier": "A", "source": "EIA เล่ม 1 หน้า 2-39 (A=504 m² × L=135.9 km)"},
            "eia_2569_reach_table": {"total": canal_volume_by_official_reaches()["total_mid_mcm"], "range": [canal_volume_by_official_reaches()["total_low_mcm"], canal_volume_by_official_reaches()["total_high_mcm"]], "tier": "A", "source": "EIA เล่ม 1 หน้า 2-39 ตารางรูปตัด 3 ช่วง (A = 480 · 504 · 504→1187 ตร.ม.) — ตรวจ 504 × 135.9 ว่าไม่เพี้ยนจากแบบทางการ"},
            "author_assumed_segments": {"total": 74.0, "tier": "C", "source": "ผลรวมหน้าตัดตามช่วงที่ผู้จัดทำสมมติเอง (968 · 714 · 510 ตร.ม.) — ไม่ใช่แบบทางการ ใช้ตรวจความสอดคล้องเท่านั้น"},
            "provincial_summary_slide": {"total_sec2": 57.4, "total_sec1": 98.37, "total_combined": 155.77, "tier": "A", "source": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569"},
            "retired_legacy": {"total": 55.4, "status": "retired", "reason": "ค่าคงที่สมมติเดิมที่ไม่ปรากฏในเอกสาร EIA ใดๆ — ปลดประจำการ"}
        }
    },
    "land_acquisition": {
        "canonical_new_reach_rai": 16288,
        "unit": "ไร่",
        "resolution": "ใช้ตัวเลข 16,288 ไร่ ตามรายงานผลกระทบสิ่งแวดล้อม เล่ม 1 ตาราง 3.4.2-1 (หน้า 3-384) ซึ่งแจกแจงแปลงที่ดิน 3,957 แปลง (คลอง 15,999 ไร่ + เขื่อนทดน้ำป่าสัก 289 ไร่) ใน 4 จังหวัด เป็นค่าหลักสำหรับช่วงป่าสัก–อ่าวไทย",
        "variants": {
            "eia_2569_pasak_gulf": {"rai": 16288, "plots": 3957, "owners": 2600, "tier": "A", "source": "EIA เล่ม 1 ตาราง 3.4.2-1"},
            "rid_2565_study": {"rai": 16305, "tier": "A", "source": "เอกสารกรมชลประทาน มี.ค. 2565 (เขื่อน 343 + คลอง 15,962 ไร่)"},
            "news_thansettakij": {"rai": 17703, "tier": "B", "source": "ฐานเศรษฐกิจ 2 ต.ค. 2569 (รวมช่วงเดิม 781 = 18,484 ไร่)"},
            "civic_petition": {"rai": 16305, "tier": "C", "source": "สมาคมพลเมืองนครนายก (อ้างอิงเอกสารปี 2565)"}
        }
    },
    "project_budget": {
        "canonical_eia_capex_mb": 160046,
        "canonical_cabinet_ceiling_mb": 165000,
        "unit": "ล้านบาท",
        "resolution": "แยกบริบทชัดเจน: 160,046 ล้านบาท คือประมาณการงบลงทุนก่อสร้างตามรายงานผลกระทบสิ่งแวดล้อมฉบับชี้แจงครั้งที่ 2 (EIA 2569) ส่วน 165,000 ล้านบาท คือกรอบเพดานวงเงินรวมที่ กนช. และ ครม. เห็นชอบ (รวมสำรองฉุกเฉินและค่าบริหารโครงการ)",
        "variants": {
            "eia_2569_approved": {"budget_mb": 160046, "tier": "A", "source": "EIA 2569 เล่ม 2 และรายงานชี้แจงครั้งที่ 2"},
            "cabinet_ceiling": {"budget_mb": 165000, "tier": "A", "source": "สรุปการประชุมจังหวัด 9 ก.ย. 2569 ตามมติ กนช. 3 ธ.ค. 2568"},
            "draft_2560": {"budget_mb": 98000, "vintage": 2560, "tier": "B", "source": "เอกสารชี้แจงโครงการ มี.ค. 2560 (ราคาคงที่ปี 2560)"}
        }
    }
}

# ตัวแปรการออกแบบรายช่วง ช่วงป่าสัก–อ่าวไทย (ชั้น B: ฐานเศรษฐกิจ 2 ต.ค. 2569 อ้างกรมชลประทาน)
DESIGN_SEGMENTS = [
    {"name": "ช่วงที่ 1 คลองดิน", "length_km": 0.57, "corridor_m": 220, "bottom_m": 105, "depth_m": 8, "shape": "คางหมู", "lined": False},
    {"name": "ช่วงที่ 2 คลองดิน", "length_km": 22.43, "corridor_m": 170, "bottom_m": 88, "depth_m": 7, "shape": "คางหมู", "lined": False},
    {"name": "ช่วงที่ 3 ดาดคอนกรีตรูปตัวยู", "length_km": 112.655, "corridor_m": 160, "bottom_m": 85, "depth_m": 6, "shape": "ตัวยู", "lined": True},
]
DESIGN_2565 = {"bottom_m": 70, "depth_m": 6, "corridor_m": 200, "road_lanes": 2, "road_width_m": 10, "reach_km": [81.0, 134.35],
               "outlet_corridor_m": 690, "src": "กรมชลประทาน ต.ค. 2564 / มี.ค. 2565 (ระยะที่ 1 กม.81–135.9 จ.ฉะเชิงเทรา–สมุทรปราการ) ตามข่าวมติชน 27 ต.ค. 2564"}
DESIGN_2565_STRUCTS = {"crossings_14": 14, "crossings_with_lock_5": 5, "road_bridges": 15, "rail_bridge": 1, "road_crossings": 2, "gates_mid": 2}
MEETING_20260909 = {
    "title": "การประชุมรับฟังรายงานข้อเท็จจริงการดำเนินโครงการก่อสร้างคลองระบายน้ำหลากชัยนาท–ป่าสัก–อ่าวไทย",
    "date": "9 ก.ย. 2569", "place": "ศาลากลางจังหวัดนครนายก",
    "presenters": "สำนักงานทรัพยากรน้ำแห่งชาติ ภาค 2 และสำนักงานก่อสร้างชลประทานขนาดใหญ่ที่ 10 กรมชลประทาน",
    "attendees_n": 39,
    "concerns": [
        {"n": "2.1", "topic": "เวนคืนและจุดเชื่อมสาธารณูปโภค", "text": "ผลกระทบจากการเวนคืนและสิทธิประโยชน์ จุดตัดจุดเชื่อมถนน ไฟฟ้า ท่อน้ำ ท่อก๊าซ การบังคับใช้กฎหมายรถบรรทุกน้ำหนักเกินบนถนนคันคลอง — ขอให้นำแบบแปลนและภาพจำลองมาแสดง และประสานการรับมอบดูแลผิวจราจร สะพาน"},
        {"n": "2.2", "topic": "การเคลื่อนไหวคัดค้าน", "text": "มีการเคลื่อนไหวคัดค้านจากองค์การนอกภาครัฐและกลุ่มมวลชนในพื้นที่ อ.บ้านนา/องครักษ์ ห่วงการแบ่งแยกพื้นที่เกษตรและชุมชน การเปลี่ยนแปลงถนนสะพาน ผลกระทบต่อระบบชลประทานและระบายน้ำเดิม"},
        {"n": "2.3", "topic": "ระบายน้ำท่วมขังลงคลอง/ใช้น้ำแล้ง", "text": "น้ำท่วมขังหรือน้ำหลากในนครนายกระบายลงคลองนี้ได้หรือไม่ และเกษตรกรนำน้ำจากคลองไปใช้ในหน้าแล้งได้หรือไม่"},
        {"n": "2.4", "topic": "รูปแบบคัน ถนน สะพาน จุดตัดจุดเชื่อม", "text": "รูปแบบการก่อสร้างคันคลอง ถนน สะพาน จุดตัดจุดเชื่อม กระทบคลองเดิมและวิถีชีวิตเกษตรกรนาข้าวเพียงใด — ประชาชนขาดข้อมูลชัดเจนและไม่มีโอกาสแสดงความเห็นตั้งแต่ขั้นศึกษาออกแบบ"},
        {"n": "2.5", "topic": "ค่าทดแทน", "text": "เงินค่าทดแทนอาจไม่พอจัดหาที่ดิน/ที่อยู่ใหม่ในทำเลเดิม หรือไม่ครอบคลุมค่าเสียโอกาสธุรกิจและผลผลิต ที่ดินที่เหลือบางส่วนใช้งานยาก"},
        {"n": "2.6", "topic": "ความคุ้มค่า", "text": "ความคุ้มค่าที่ประชาชนในพื้นที่จะได้เทียบกับความสูญเสียทั้งเศรษฐกิจ สังคม สิ่งแวดล้อม"},
        {"n": "2.7", "topic": "ผลกระทบช่วงก่อสร้าง", "text": "การขุดดิน ขนดิน ทิ้งดิน การสัญจร การเปลี่ยนแปลงทางน้ำในลำคลองเดิม การระบายน้ำ ผลต่อสิ่งแวดล้อมและทรัพยากรธรรมชาติ"},
    ],
    "orders": ["รายงานผลการประชุมต่อกระทรวงมหาดไทย เกษตรและสหกรณ์ กรมชลประทาน สทนช.", "ให้อำเภอบ้านนา องครักษ์ และท้องถิ่นสื่อสารกับประชาชน", "จัดเวทีประชาคมระดับอำเภอและตำบล โดยเชิญกรมชลประทานและ สทนช. ชี้แจง"],
}


# ข้อห่วงกังวลที่สมาคมพลเมืองนครนายกยื่นต่อกรรมาธิการบริหารน้ำ สภาผู้แทนราษฎร (3 ส.ค. 2569) — ชั้น C
# เก็บเป็น "ข้อความที่ผู้ยื่นระบุ" ไม่ใช่ข้อเท็จจริงที่รายงานยืนยัน · แหล่ง: Thai PBS (thaipbs.or.th/news/content/508956)
CONCERNS = [
    {"n": 1, "topic": "เอกสารไม่ตรงกัน", "claim": "รายงานผลกระทบสิ่งแวดล้อมฉบับหลัก (พ.ย. 2561) กับฉบับย่อ (ก.พ. 2569) ต่างกันทั้งวงเงินลงทุน (113,989 กับ 160,046 ล้านบาท) พื้นที่เวนคืน ระยะก่อสร้าง (3 ปี กับ 7 ปี) และขอบเขตศึกษาผลกระทบ (2 กม. กับ 500 ม.)"},
    {"n": 2, "topic": "ทางเลือกอื่น", "claim": "เน้นคลองขนาดใหญ่โดยไม่เปรียบเทียบแก้มลิง การฟื้นฟูทางน้ำหลากเดิม หรือปรับปรุงคลองเดิม"},
    {"n": 3, "topic": "ผลกระทบสะสม", "claim": "ไม่เชื่อมโยงกับโครงการอื่นในแผนบรรเทาอุทกภัยลุ่มเจ้าพระยา (คลองชัยนาท–ป่าสัก คลองบางบาล–บางไทร ถนนวงแหวนรอบที่ 3)"},
    {"n": 4, "topic": "การผันน้ำข้ามลุ่ม", "claim": "ยังไม่ชัดว่าลุ่มน้ำต้นทางเสียโอกาสใช้น้ำหรือไม่ ปลายทางรับภาระเท่าไร และกระทบระบบนิเวศน้ำกร่อยอย่างไร"},
    {"n": 5, "topic": "ระบบนิเวศชายฝั่ง", "claim": "ขาดการวิเคราะห์สมดุลน้ำจืด–น้ำเค็ม การเคลื่อนตัวของตะกอน และสัตว์น้ำวัยอ่อน"},
    {"n": 6, "topic": "ความเสี่ยงท่วมพื้นที่ใหม่", "claim": "ยังไม่ชัดว่าพื้นที่ตามแนวคลองเสี่ยงท่วมเพิ่มหรือไม่ และใครได้/เสียประโยชน์"},
    {"n": 7, "topic": "ผลกระทบทางสังคม", "claim": "เวนคืนกว่าหมื่นไร่ กระทบกว่า 1,600 หลังคาเรือน แต่ขาดการวิเคราะห์อาชีพ การย้ายถิ่น ความมั่นคงทางอาหาร วัฒนธรรมชุมชน"},
    {"n": 8, "topic": "การมีส่วนร่วม", "claim": "ความเห็นคัดค้านไม่ถูกบันทึก และมติ กนช. 5/2568 ระบุว่าไม่พบผู้คัดค้านซึ่งผู้ยื่นว่าขัดกับหลักฐานที่แนบ"},
    {"n": 9, "topic": "เศรษฐศาสตร์", "claim": "ที่อัตราคิดลดร้อยละ 7 คุ้มค่า ร้อยละ 9 เฉียดฉิว ร้อยละ 12 ไม่คุ้มค่า (แนวทางของสภาพัฒน์ 6–9) และงบเผื่อเหลือเผื่อขาดเพียงราว 5 ล้านบาท"},
    {"n": 10, "topic": "สุขภาพ", "claim": "ขาดการวิเคราะห์ผลกระทบสุขภาพเชิงลึกและยังไม่อัปเดตตามกฎหมายล่าสุด"},
    {"n": 11, "topic": "แผนรับเหตุวิกฤต", "claim": "ไม่มีแผนรับน้ำเกินการออกแบบ คลองพัง ประตูขัดข้อง น้ำทะเลหนุน แผ่นดินไหว ฝนหนักจากภาวะโลกร้อน"},
    {"n": 12, "topic": "การชดเชย", "claim": "ชดเชยเฉพาะที่ดิน อาคาร พืชผล ไม่ครอบคลุมรายได้ระยะยาว ผู้เช่าที่ดิน ผู้ไม่มีเอกสารสิทธิ์ และกลุ่มเปราะบาง"},
    {"n": 13, "topic": "ข้อมูลล้าสมัย", "claim": "การศึกษาเริ่มปี 2555 สัญญา 2558 รายงานฉบับหลัก 2561 ฉบับใหม่ 2569 บางส่วนอ้างข้อมูลเดิม ข้อมูลภาคสนามอาจเก่ากว่า 10 ปี"},
]
CIVIC_FUNDING = {"budget_state_mb": 61438, "loan_adb_mb": 103562, "tier": "C", "src": "สมาคมพลเมืองนครนายก (อ้างตามรายงาน กนช.)"}
DESIGN_HISTORY = [
    {"year": "2555", "event": "กรมชลประทานศึกษาการบริหารจัดการน้ำฝั่งตะวันออก–ตะวันตกบริเวณท้ายเขื่อนเจ้าพระยา", "tier": "A"},
    {"year": "เม.ย. 2560", "event": "ศึกษาความเหมาะสม", "tier": "A"},
    {"year": "พ.ค. 2560", "event": "กนช. เห็นชอบหลักการแผนบรรเทาอุทกภัยเจ้าพระยาตอนล่าง 9 แผน", "tier": "A"},
    {"year": "27 พ.ย. 2561", "event": "กรมชลประทานส่งรายงานผลกระทบสิ่งแวดล้อมฉบับหลักให้ สผ. (หนังสือ กษ 0327/10446) · ตรวจเอกสารจริงแล้ว", "tier": "A"},
    {"year": "1 ก.พ. 2562", "event": "คชก. (ครั้งที่ 2/2562) มีมติให้กรมชลประทานจัดทำรายงานใหม่ตามแนวทางที่กำหนด · สผ. แจ้ง 18 ก.พ. 2562", "tier": "A"},
    {"year": "20 ก.ย. 2564", "event": "กรมชลประทานส่งรายงานชี้แจงเพิ่มเติมครั้งที่ 1 (ที่ปรึกษา บริษัท พิสุทธิ์ เทคโนโลยี จำกัด)", "tier": "A"},
    {"year": "28 ต.ค. 2564", "event": "คชก. (ครั้งที่ 7/2564) มีมติให้ปรับปรุง แก้ไข เพิ่มเติมข้อมูล · สผ. แจ้ง พ.ย. 2564", "tier": "A"},
    {"year": "19 ธ.ค. 2566", "event": "กรมชลประทานส่งรายงานชี้แจงเพิ่มเติมครั้งที่ 2 (ฉบับเดือนธันวาคม 2566)", "tier": "A"},
    {"year": "8 มี.ค. 2567", "event": "คชก. (ครั้งที่ 5/2567) มีมติให้ปรับปรุง แก้ไข เพิ่มเติมข้อมูล · สผ. แจ้ง มี.ค. 2567", "tier": "A"},
    {"year": "2564", "event": "สำรวจออกแบบช่วงชัยนาท–ป่าสักเสร็จ · ประชุมปฐมนิเทศระยะที่ 1 (ต.ค. 2564)", "tier": "A"},
    {"year": "มี.ค. 2565", "event": "ประชุมกลุ่มย่อยครั้งที่ 1 ระยะที่ 1 (ฉะเชิงเทรา)", "tier": "A"},
    {"year": "2567", "event": "สำรวจออกแบบช่วงป่าสัก–อ่าวไทยเสร็จ", "tier": "A"},
    {"year": "พ.ค. 2568", "event": "คชก. เห็นชอบรายงานสิ่งแวดล้อมช่วงป่าสัก–อ่าวไทย", "tier": "A"},
    {"year": "3 ธ.ค. 2568", "event": "กนช. เห็นชอบโครงการ (165,000 ล้านบาท · 8 ปี)", "tier": "A"},
    {"year": "18 ธ.ค. 2568", "event": "กก.วล. ครั้งที่ 6/2568 เห็นชอบรายงานสิ่งแวดล้อม", "tier": "A"},
    {"year": "ก.พ. 2569", "event": "รายงานสิ่งแวดล้อมฉบับย่อ (ตามที่สมาคมพลเมืองนครนายกระบุ)", "tier": "C"},
    {"year": "31 ก.ค./5 ส.ค. 2569", "event": "คณะอนุกรรมการ สศช. พิจารณา / สศช. เห็นชอบ", "tier": "A"},
    {"year": "3 ส.ค. 2569", "event": "สมาคมพลเมืองนครนายกยื่น 13 ข้อต่อกรรมาธิการบริหารน้ำ สภาผู้แทนราษฎร", "tier": "C"},
    {"year": "9 ก.ย. 2569", "event": "จังหวัดนครนายกประชุมรับฟังรายงานข้อเท็จจริง (ผู้เข้าร่วม 39 คน)", "tier": "A"},
    {"year": "29 ก.ย. 2569", "event": "ครม. อนุมัติ", "tier": "A"},
    {"year": "2570–2577", "event": "จัดหาที่ดินด้วยวิธีปรองดอง 2570–2573 · เวนคืนตามกฎหมาย 2570–2571 · ก่อสร้าง 2570–2577", "tier": "A"},
]


EIA_SECTION = {"D_m": _K("eia_depth_m"), "A_m2": _K("eia_area_m2"), "P_m": _K("eia_wetted_perimeter_m"), "B_m": _K("eia_bed_width_m"), "V_ms": _K("eia_velocity_ms"), "n": _K("eia_manning_n"), "slope_1_n": _K("eia_slope_1_n"), "z1": _K("eia_z_inner"), "z2": _K("eia_z_outer"), "road_m": _K("eia_road_each_side_m"),
               "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-39 (รูปที่ 2.3.2-11 ตาราง กม.23–134)"}


PROFILE_FIG = {
    "src": "รายงานผลกระทบสิ่งแวดล้อม ฉบับ ก.พ. 2569 เล่ม 1 รูปที่ 2.3.2-9 (หน้าพิมพ์ 2-37 · หน้าไฟล์ 142) · ภาพไฟล์ data/manual/EIA ทางระบายน้ำหลาก_สมบูรณ์ เล่ม 1-17907513091.jpg",
    "reading_error_m": 0.2,
    "method": "อ่านด้วยตาจากภาพขยาย 600 จุดต่อนิ้ว โดยเทียบเส้นตารางแนวตั้งทุก 1 ม. · ระดับน้ำ/สันคัน/ท้องคลองตรงกับสูตร (ท้อง −1.05 ม. ที่ กม.23 ลาด 1:25,000 ลึก 7 ม. เผื่อพ้นน้ำ 1.5 ม.) และค่าที่เขียนกำกับบนรูป",
    "labels_on_figure": {"km0.15": {"crest": 10.25, "water": 8.75, "bed": 1.75}, "km22.9": {"crest": 7.95, "water": 6.45},
                         "km23": {"crest": 7.45, "water": 5.95, "bed": -1.05}, "km75": {"crest": 5.36, "water": 3.86, "bed": -3.13},
                         "km109": {"crest": 4.0, "water": 2.5}, "km134": {"crest": 3.0, "bed": -5.504, "sea_high": 2.0, "backwater": 2.5, "water": 1.498},
                         "connect_canal_km39.8": {"crest": 3.2, "water": 2.0, "bed": -1.0}, "connect_canal_km51.5": {"crest": 2.808, "water": 1.408, "bed": -1.592}},
    # (กม., ความสูงพื้นดินธรรมชาติ ม.รทก.) อ่านจากเส้นประ "ระดับดินธรรมชาติ"
    "ground": [(0, 10.0), (6.5, 10.0), (9.8, 11.4), (12.8, 8.0), (15.3, 8.0), (22.0, 8.0), (24.5, 4.0), (28.0, 4.0), (36.9, 2.0),
               (50.0, 1.95), (56.7, 2.9), (57.8, 2.5), (60.0, 1.93), (65.0, 1.6), (70.0, 1.5), (75.0, 1.45), (85.0, 1.2), (95.0, 1.0),
               (105.0, 0.5), (118.0, 0.5), (123.0, 1.0), (129.0, 0.55), (131.0, 0.8), (134.0, 1.5)],
}


def _profile_levels(km):
    """ระดับน้ำสูงสุด/สันคัน/ท้องคลอง (ม.รทก.) ตามสูตรที่ตรงกับรูปที่ 2.3.2-9"""
    if km < 23:
        bed = 1.75 - (km - 0.15) * 0.1
        water = bed + 7.0
        crest = water + 1.5
    elif km <= 109:
        bed = -1.05 - (km - 23) * 0.04
        water = bed + 7.0
        crest = water + 1.5
    else:
        bed = -1.05 - (km - 23) * 0.04
        water = bed + 7.0
        crest = 4.0
    return bed, water, crest


def eia_profile():
    g = PROFILE_FIG["ground"]
    gx = [x[0] for x in g]
    gy = [x[1] for x in g]
    rows = []
    for km in list(range(0, 136, 5)):
        bed, water, crest = _profile_levels(km)
        z = float(np.interp(km, gx, gy))
        rows.append({"km": km, "ground_m": round(z, 2), "bed_m": round(bed, 2), "water_m": round(water, 2), "crest_m": round(crest, 2),
                     "water_above_ground_m": round(water - z, 1), "crest_above_ground_m": round(crest - z, 1)})
    nn = []
    for i in range(0, 503):
        km = 23.0 + i * 0.1
        if 38.6 <= km <= 73.2:
            bed, water, crest = _profile_levels(km)
            z = float(np.interp(km, gx, gy))
            nn.append((km, crest - z, water - z, z))
    return {**{k: v for k, v in PROFILE_FIG.items() if k != "ground"}, "ground_readings": PROFILE_FIG["ground"], "rows": rows,
            "nn_reach": {"km": [38.6, 73.2],
                         "crest_above_ground_min_m": round(min(x[1] for x in nn), 1), "crest_above_ground_max_m": round(max(x[1] for x in nn), 1),
                         "water_above_ground_min_m": round(min(x[2] for x in nn), 1), "water_above_ground_max_m": round(max(x[2] for x in nn), 1),
                         "ground_min_m": round(min(x[3] for x in nn), 2), "ground_max_m": round(max(x[3] for x in nn), 2)},
            "connecting_canal": {"km": [39.8, 51.5], "crest_msl": [3.2, 2.808], "water_msl": [2.0, 1.408], "bed_msl": [-1.0, -1.592], "bed_slope": "1:20,000",
                                 "basin": "PK-AT-4 แม่น้ำใน", "basin_rai": 206224, "q_m3s": 28.046,
                                 "src": "ฉบับ 2569 หน้า 2-41/2-42 (หน้าไฟล์ 146–147) และรูปที่ 2.3.2-9 — คลองเชื่อมจากแม่น้ำในไปคลองบางปลากดแล้วลงแม่น้ำนครนายก ขนานฝั่งซ้ายของคลองระบายน้ำหลาก"},
            "lateral_ditch": {"width_m": 3.0, "depth_m": 1.0, "src": "ฉบับ 2569 หน้า 2-45 (หน้าไฟล์ 150): คูระบายน้ำกว้าง 3 ม. ลึก 1 ม. ด้านนอกคันทั้งสองฝั่งตลอดแนว"},
            "upland_basins": {"ids": ["PK-AT-1", "PK-AT-2", "PK-AT-3"], "note": "พื้นดินสูงกว่าระดับน้ำสูงสุดของคลอง ระบายผ่านท่อระบายน้ำได้ทุกสถานการณ์ (หน้า 2-41)"}}


def eia_levels(dem_profile_rows):
    """ระดับน้ำ/สันคัน เทียบพื้นดินเดิมที่อ่านจากรูปตัดตามยาว (รูปที่ 2.3.2-9) — ไม่ใช้ DEM ผิวดิน"""
    g = {p["km"]: p["ground_m"] for p in dem_profile_rows}
    pr = PROFILE_FIG["ground"]
    gx = [x[0] for x in pr]
    gy = [x[1] for x in pr]
    out = []
    for km in (40, 45, 50, 55, 60, 65, 70, 100):
        bed, water, crest = _profile_levels(km)
        z = float(np.interp(km, gx, gy))
        out.append({"km": km, "ground_dsm_m": g.get(km), "ground_m": round(z, 2), "water_msl_m": round(water, 2),
                    "water_above_ground_m": round(water - z, 1), "crest_msl_m": round(crest, 2), "crest_above_ground_m": round(crest - z, 1)})
    return {"rows": out, "note": "พื้นดินเดิมอ่านจากเส้น \"ระดับดินธรรมชาติ\" ในรูปตัดตามยาว (รูปที่ 2.3.2-9) ±0.2 ม. · ระดับน้ำ/สันคันคำนวณจากสูตรที่ตรงกับค่ากำกับบนรูป (ลาด 1:25,000 ลึก 7 ม. เผื่อพ้นน้ำ 1.5 ม.) · ไม่รวมคลองเชื่อมแม่น้ำใน (กม.39.8–51.5)",
            "eia_range_water_above_ground_m": [1.0, 3.3], "eia_crest_above_ground_max_m": 4.8}


EIA_LAND = {
    "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 ตารางที่ 3.4.2-1 หน้า 3-384",
    "rows": [
        {"province": "สระบุรี", "owners": 797, "plots": 1304, "rai": 4348, "mb": 2843.1},
        {"province": "ปทุมธานี", "owners": 19, "plots": 30, "rai": 179, "mb": 91.2},
        {"province": "นครนายก", "owners": 661, "plots": 962, "rai": 4266, "mb": 3864.7},
        {"province": "ฉะเชิงเทรา", "owners": 775, "plots": 1133, "rai": 4901, "mb": 2265.8},
        {"province": "สมุทรปราการ", "owners": 338, "plots": 528, "rai": 2594, "mb": 10612.1},
    ],
    "total": {"owners": 2600, "plots": 3957, "rai": 16288, "mb": 19677.1, "canal_rai": 15999, "weir_rai": 289},
    "structures": {"n": 1378, "mb": 1994.0}, "trees": {"rai": 1303, "mb": 123.3}, "compensation_total_mb": 21794.4,
    "impact_rating": "ผลกระทบทางลบระดับมากที่สุด (-5) ในระยะก่อสร้าง · ระยะดำเนินการไม่มีผลกระทบเพิ่ม (0) — หน้า 4-50",
}
EIA_ECON = {
    "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 2 ตารางที่ 8.8-1 หน้า 8-19",
    "rows": [{"discount": 7, "eirr": 10.94, "bcr": 2.12, "npv_mb": 111359}, {"discount": 9, "eirr": 10.94, "bcr": 1.48, "npv_mb": 44199},
             {"discount": 12, "eirr": 10.94, "bcr": 0.97, "npv_mb": -2821}],
    "verdict": "คุ้มค่าที่ 7% และ 9% · ไม่คุ้มค่าที่ 12% (ตามที่รายงานสรุป)",
    "earlier_2560": {"src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 2 หน้า 9-137 (คำชี้แจงในประชุมสาธารณะครั้งที่ 2 มี.ค. 2560 · ราคาคงที่ปี 2560)",
                     "discount": 12, "eirr": 13.33, "bcr": 1.12, "npv_mb": 10046},
}
EIA_SOCIAL = {
    "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 2 บทที่ 6 หน้า 6-65 ถึง 6-82 (การสำรวจผู้ได้รับผลกระทบจากการเวนคืน 123 ราย)",
    "unaware_pct": 55.3, "consent_unconditional_pct": 0.55, "consent_appraised_pct": 10.11, "consent_market_pct": 66.27, "refuse_pct": 20.0,
    "refuse_reason_low_pay_pct": 41.35, "no_move_pct": 42.92, "same_tambon_pct": 64.89,
    "study_population": 31075, "study_households": 10827, "nakhonnayok_population": 4047,
}
CONCERN_CHECKS = {
    1: "ตรวจได้ส่วนหนึ่ง (15 ต.ค. 2569 — ได้เอกสารฉบับ 2561/2564/2566 แล้ว) — ฉบับหลัก 2561 ระบุราคาโครงการ 113,989 ล้านบาท (หน้าไฟล์ 78) · ระยะก่อสร้าง 3 ปี (หน้า 82 · 149) · ศึกษาที่ดิน/ชุดดินระยะ 500 ม. จากแนวคลอง (หน้า 159) — ตรงกับที่ผู้ยื่นระบุว่าฉบับหลักต่างจากฉบับย่อ · ส่วนตัวเลขฉบับย่อ ก.พ. 2569 (160,046 ล้านบาท · 7 ปี) ยังไม่มีเอกสารมาเทียบในชุดนี้ · ผลตอบแทนที่ 12%: ฉบับ 2561 B/C 1.35 · ฉบับ 2564 1.12 · ฉบับ 2566 0.99 · ฉบับ 2569 0.97 (ดูตาราง 3.9)",
    7: "ฉบับ 2569: ที่ดิน 16,288 ไร่ · ผู้ถือครอง 2,600 ราย · สิ่งปลูกสร้าง 1,378 หลัง (ตัวเลข 1,563 หลังของผู้ยื่นต่างจาก 1,378 — ต้องดูว่านับต่างกันหรือไม่) · ตารางเศรษฐศาสตร์มีค่าชดเชยสิ่งปลูกสร้าง ไม้ยืนต้น ค่าเสียโอกาสการใช้ที่ดิน และอาชีพประมงท้ายน้ำ",
    8: "ประวัติ: กลุ่มย่อยในองครักษ์ 27 ก.ค. 2559 (2 เวที) และ 1 มี.ค. 2560 (อบต.คลองใหญ่) แต่ประชุมสาธารณะ 2 ครั้งอยู่นอกนครนายก · รายงานสำรวจผู้ถูกเวนคืน 123 ราย: ร้อยละ 55.3 ยังไม่ทราบเกี่ยวกับโครงการ · ร้อยละ 20 ไม่ยินยอมให้ที่ดิน (เหตุหลัก: กลัวได้ค่าเวนคืนต่ำ ร้อยละ 41.35) · เพิ่ม (16 ต.ค. 2569): ปี 2566 มีประชุมทำความเข้าใจ 32 เวที 2,231 คน โดยนครนายก 6 เวทีที่ที่ว่าการอำเภอองครักษ์ (22–27 ก.พ. 2566) และประชุมกลุ่มผู้ใช้น้ำ 24 ก.พ. 2566 — อำเภอบ้านนามีเพียง ต.บ้านพริก ร่วมเวทีที่ 30 ที่อำเภอหนองเสือ จ.ปทุมธานี (ไม่มีเวทีในอำเภอบ้านนาเอง · เล่ม 2 ตาราง 9.5.7-4 และ 9.5.7-6 หน้าไฟล์ 362–368)",
    9: "ปี 2560 ที่ 12%: ผลตอบแทน 13.33% B/C 1.12 (คุ้มค่า) → ฉบับ 2569: 10.94% B/C 0.97 (ไม่คุ้มค่า) · ตรงกับตารางที่ 8.8-1: อัตราส่วนผลประโยชน์ต่อต้นทุน 2.12 / 1.48 / 0.97 ที่คิดลด 7 / 9 / 12 % — ไม่คุ้มค่าที่ 12% (รายงานสรุปเช่นนั้นเอง) · ตัวเลข \"เผื่อเหลือเผื่อขาด 5 ล้านบาท\" ยังไม่ได้ตรวจ",
    12: "ตารางเศรษฐศาสตร์ (ตาราง 8.8-2) มีรายการค่าชดเชยสิ่งปลูกสร้างและไม้ยืนต้น ค่าเสียโอกาสการใช้ที่ดิน และความเสียหายอาชีพประมงท้ายน้ำ — ผู้เช่า/ผู้ไม่มีเอกสารสิทธิ์ยังไม่พบในตารางที่ตรวจ",
    2: "ตรวจแล้วบางส่วน (16 ต.ค. 2569): เล่ม 1 บทที่ 1 วางโครงการเป็นหนึ่งในแผนงานบรรเทาอุทกภัยลุ่มเจ้าพระยาตอนล่างหลายองค์ประกอบ (รวมแก้มลิง ปรับปรุงคลองเดิม คลองบางบาล–บางไทร ถนนวงแหวนรอบที่ 3 — หน้าไฟล์ 89–97) · มีเปรียบเทียบทางเลือกของแนวคลองในช่วงหนึ่ง 3 ทางเลือก (หน้าไฟล์ 136) · ไม่พบหัวข้อเปรียบเทียบคลองใหญ่กับแก้มลิง/ฟื้นฟูทางน้ำเดิมในเล่ม 1 ด้วยการค้นคำสำคัญ · ผลสำรวจความเห็นในรายงาน (หน้าไฟล์ 585) มีผู้ให้เหตุผลว่าควรปรับปรุงคลองเดิมแบบแก้มลิง",
    3: "ตรวจแล้ว (16 ต.ค. 2569): เล่ม 1 หน้าไฟล์ 89 ระบุแผนงานอื่นในลุ่มเจ้าพระยาตอนล่างเป็นบริบท (รวมคลองบางบาล–บางไทร ถนนวงแหวนรอบที่ 3) · ไม่พบหัวข้อประเมินผลกระทบสะสมของหลายโครงการด้วยการค้นคำสำคัญ · คำว่า \"ผลกระทบสะสม\" พบครั้งเดียว ในบันทึกประชาพิจารณ์ครั้งที่ 2 เวทีที่ 2 ที่ผู้แทน สผ. เสนอให้นำเสนอภาพรวมที่คำนึงถึงผลกระทบสะสม (เล่ม 2 หน้า 9-145 · หน้าไฟล์ 328)",
    4: "ตรวจแล้วบางส่วน (16 ต.ค. 2569): รายงานจัดโครงการเป็น \"การผันน้ำข้ามลุ่มน้ำหลัก\" ที่ต้องทำรายงาน (เล่ม 1 หน้าไฟล์ 12, 98) · ปริมาณที่ผันพิจารณาจากน้ำท่าสถานี S.26 ท้ายเขื่อนพระรามหกที่ปัจจุบันไหลลงเจ้าพระยาและออกอ่าวไทย (หน้า 2-91 · หน้าไฟล์ 196) — เป็นการเปลี่ยนเส้นทางน้ำส่วนเกินจากลุ่มบน ไม่ใช่ดึงน้ำจากลุ่มที่ขาด · ไม่พบการประเมินผลต่อปากแม่น้ำเจ้าพระยาท้ายน้ำเมื่อน้ำส่วนนี้ไม่ไหลทางเดิม",
    5: "ตรวจแล้วบางส่วน (16 ต.ค. 2569): มีผลแบบจำลองน้ำขึ้นลงและปริมาณระบายออกอ่าวไทย 121–853 ลบ.ม./วินาที · ตะกอนเฉลี่ย 58 ตัน/ชม. (39 ลบ.ม./ชม.) · การเคลื่อนตัวของทรายชายฝั่งรายตำบลและแบบจำลองแนวชายฝั่ง 10 และ 20 ปี (กัดเซาะ 0.789 → 0.755 ม. ใน 10 ปี) · ความเค็มและการตายของหอย (เล่ม 1 บทที่ 2–4) · สัตว์น้ำวัยอ่อนมีเฉพาะคำอธิบายเชิงคุณภาพผ่านแพลงก์ตอน (หน้าไฟล์ 685–688) ไม่พบการคำนวณปริมาณ",
    6: "ตรวจแล้ว (16 ต.ค. 2569): ไม่พบแบบจำลองน้ำท่วมด้านข้างของคลองลอย (ช่องว่างความรู้เรื่องแบบจำลองน้ำท่วมด้านข้าง) · รายงานระบุเชิงคุณภาพว่าท่อระบายน้ำ/อาคารรับน้ำป่าออกแบบไม่ให้คลองกีดขวางทางน้ำ (เล่ม 1 หน้าไฟล์ 164) · การเปิดอาคารรับน้ำด้านข้างให้ระบายก่อนรับน้ำแม่น้ำเป็นเกณฑ์ของคลองชัยนาท–ป่าสัก (หน้าไฟล์ 196) · ไม่พบการประเมินผู้ได้/เสียประโยชน์รายพื้นที่",
    10: "ตรวจแล้ว (16 ต.ค. 2569): เล่ม 2 บทที่ 6 \"การประเมินผลกระทบด้านสุขภาพ\" ยาวราว 83 หน้า (หน้าไฟล์ 20–102) · อ้างแนวทางประเมินผลกระทบสุขภาพของ สผ. ฉบับปรับปรุง (พ.ค. 2565) และของกรมอนามัยฉบับล่าสุด (2558) รวมทั้งประกาศผลกระทบสิ่งแวดล้อมฉบับ 2566 และฉบับที่ 2 พ.ศ. 2568 (เล่ม 1 หน้าไฟล์ 100) · รวบรวมข้อมูลสาธารณสุขทุติยภูมิ 5 จังหวัด · มีข้อเสนอของผู้เชี่ยวชาญด้านสุขภาพในประชาพิจารณ์ (เล่ม 2 หน้า 9-256) · ค้นเว็บ 16 ต.ค. 2569 ไม่พบหลักฐานว่ามีการแก้กฎหมายสาธารณสุขเรื่องประเมินผลกระทบสุขภาพที่ประกาศใช้แล้ว (พบเพียงข่าวข้อเสนอแก้ไข ก.ย. 2569) — ยังไม่ได้ตรวจกับราชกิจจานุเบกษาโดยตรง",
    11: "ตรวจแล้ว (16 ต.ค. 2569): ค้นคำ \"ฉุกเฉิน/แผนรองรับ\" พบเฉพาะแผนรองรับอุบัติเหตุคนงานและสุขภาพ (เล่ม 1 หน้าไฟล์ 732 · เล่ม 2 หน้าไฟล์ 29, 408, 439) · ไม่พบแผนรับน้ำเกินการออกแบบ คันพัง หรือประตูขัดข้องของคลองในเล่มที่ค้น · พบข้อเสนอของผู้เชี่ยวชาญในประชาพิจารณ์ให้ระบุอัตราไหลที่รับได้และเผื่อค่าร้อยละเพื่อรองรับสถานการณ์ฉุกเฉิน (เล่ม 2 หน้า 9-256) · มีเกณฑ์จำกัดรับน้ำของคลองชัยนาท–ป่าสัก (650 ลบ.ม./วินาที ลึกไม่เกิน 7–8 ม.)",
    13: "ตรวจแล้ว (16 ต.ค. 2569): ตารางคุณภาพน้ำผิวดินส่วนหนึ่งใช้ผลปี 2555 (เล่ม 1 หน้า 3-59 · หน้าไฟล์ 265 — อายุราว 14 ปีเมื่อเทียบ 2569) ร่วมกับสถานีที่เก็บเพิ่ม 2 สถานี (หน้าไฟล์ 258) · ดินเก็บตัวอย่าง พ.ค. 2559 (หน้าไฟล์ 229–231) · สำรวจท่องเที่ยวภาคสนาม ต.ค. 2559 (หน้าไฟล์ 643) · ติดตามสำรวจผู้ได้รับผลกระทบรอบ 3–4 ปี 2566–2567 (หน้าไฟล์ 554–558) · ประชาพิจารณ์ล่าสุดเมษายน 2568 · สรุป: ข้อมูลสิ่งแวดล้อมพื้นฐานส่วนใหญ่อายุ 9–14 ปี ส่วนข้อมูลสังคม/ที่ดินใหม่กว่า",
}
CONCERN_CHECKS[12] = (CONCERN_CHECKS[12] + " · หนังสือมาตรการแนบท้ายหน้า 45: ให้ตั้งคณะกรรมการกำหนดราคาที่มีตัวแทนประชาชนระดับตำบล · "
                       "ผู้เชี่ยวชาญในประชาพิจารณ์เสนอให้มีมาตรการกลุ่มเปราะบาง โดยเฉพาะเกษตรกรที่เช่าที่ดิน (เล่ม 2 หน้า 9-256)")

# แบบเริ่มต้น มี.ค.–เม.ย. 2560 (เอกสารประชุมสาธารณะครั้งที่ 2 ของที่ปรึกษากรมชลประทาน — เก่ากว่ารายงานฉบับอนุมัติ 8–9 ปี)
DESIGN_2560 = {
    "src": "data/manual/lowereastchaophraya/…/document-2.pdf (ประชุมสาธารณะครั้งที่ 2, 28–29 มี.ค. 2560)",
    "length_km": 135.9, "q_m3s": 600, "road": "2 ช่องจราจร กว้าง 10 ม. ทั้งสองข้าง",
    "reach1": {"km": [0, 23], "type": "คลองดิน ต่ำกว่าพื้นเดิม (คลองจม)", "bottom_m": 53, "depth_m": 7, "corridor_m": 170},
    "reach2": {"km": [23, 135.9], "type": "คลองดาดคอนกรีต สูงกว่าพื้นเดิม (คลองลอย) ฐานรากดินอ่อน เสริมเข็ม", "bottom_m": 51, "depth_m": 7, "corridor_m": 180},
    "outlet": {"bottom_m": 380, "corridor_m": 480},
    "components_total": 99, "gates": 5, "forest_intakes": 4, "aqueducts": 7, "road_bridges": 41, "crossings_siphon_drain": 35,
    "rail_bridges": 2, "crossings_with_locks": 5, "cost_mb": 98003.63,
}
PARTICIPATION = [
    {"date": "26–27 ม.ค. 2559", "event": "ประชุมสาธารณะครั้งที่ 1 (2 เวที: สระบุรี และสมุทรปราการ)", "n": 227, "nn_venue": False,
     "note": "พื้นที่ศึกษา 8 จังหวัด 69 อำเภอ รวมบ้านนาและองครักษ์ — ไม่มีเวทีในนครนายก"},
    {"date": "25–29 เม.ย. 2559", "event": "กลุ่มย่อยครั้งที่ 1 งานปรับปรุงระบบชลประทาน (8 เวที)", "n": 490, "nn_venue": None, "note": "งานคนละส่วน (ปรับปรุงคลองชลประทานเดิม)"},
    {"date": "25 ก.ค.–1 ส.ค. 2559", "event": "กลุ่มย่อยครั้งที่ 1 งานทางระบายน้ำหลาก (11 เวที)", "n": 718, "nn_venue": True,
     "note": "เวทีที่ 5 อบต.คลองใหญ่ (65 คน, ผู้ได้รับผลกระทบ 13) · เวทีที่ 6 อบต.พระอาจารย์ (66 คน, ผู้ได้รับผลกระทบ 21) — 27 ก.ค. 2559 อ.องครักษ์"},
    {"date": "24 ก.พ.–3 มี.ค. 2560", "event": "กลุ่มย่อยครั้งที่ 2 งานทางระบายน้ำหลาก (11 เวที)", "n": 1082, "nn_venue": True, "note": "เวทีที่ 6 อบต.คลองใหญ่ อ.องครักษ์ (1 มี.ค. 2560) — ตามรายงานผลกระทบสิ่งแวดล้อม เล่ม 2 หน้า 9-100 · ผลรับฟัง: ลดแนวเขตคลองจาก ~200 ม. เป็น 170 ม. (กม.0–23) / 180 ม. (นครนายก)"},
    {"date": "มี.ค. 2565", "event": "กลุ่มย่อยครั้งที่ 1 งานออกแบบรายละเอียดระยะที่ 1 (ฉะเชิงเทรา)", "n": None, "nn_venue": False, "note": "เอกสารกรมชลประทาน มี.ค. 2565 — พื้นที่ฉะเชิงเทรา/สมุทรปราการ"},
    {"date": "16 ก.พ. 2566", "event": "ประชุมปฐมนิเทศงานออกแบบระยะที่ 2 (กม.0–81) เวทีที่ 1 ที่ อ.องครักษ์", "n": None, "nn_venue": True,
     "note": "ห้องประชุมแสดขาว โรงเรียนองครักษ์ — ครอบคลุม อ.องครักษ์ อ.บ้านนา อ.หนองเสือ อ.บางน้ำเปรี้ยว · เวทีที่ 2 ที่สระบุรี 17 ก.พ. 2566"},
    {"date": "20–23 มี.ค. 2566", "event": "กลุ่มย่อยครั้งที่ 3 ระยะที่ 1 (6 เวที)", "n": None, "nn_venue": False, "note": "ระยะที่ 1 กม.81–135.555 (ฉะเชิงเทรา/สมุทรปราการ)"},
    {"date": "28–29 มี.ค. 2560", "event": "ประชุมสาธารณะครั้งที่ 2 (2 เวที: สระบุรี และสมุทรปราการ)", "n": 267, "nn_venue": False,
     "note": "ผู้ได้รับผลกระทบ 106 คน · พื้นที่ศึกษา 6 จังหวัด 13 อำเภอ รวมบ้านนาและองครักษ์ — ไม่มีเวทีในนครนายก"},
    {"date": "8 ก.พ.–15 มี.ค. 2566", "event": "ประชุมทำความเข้าใจโครงการ 32 เวที (งานรายงานผลกระทบสิ่งแวดล้อม)", "n": 2231, "nn_venue": True,
     "note": "นครนายก 6 เวที ณ ที่ว่าการอำเภอองครักษ์ 22–27 ก.พ. 2566 (ต.บางปลากด คลองใหญ่ องครักษ์ พระอาจารย์ ×3) · เวทีหน่วยงานจังหวัดนครนายก 15 มี.ค. 2566 จัดที่สมุทรปราการ · อำเภอบ้านนามีเพียง ต.บ้านพริก ร่วมเวทีที่ 30 (หอประชุมอำเภอหนองเสือ จ.ปทุมธานี 10 มี.ค. 2566) — ไม่มีเวทีในอำเภอบ้านนาเอง"},
    {"date": "24 ก.พ. 2566", "event": "ประชุมกลุ่มย่อยผู้ใช้น้ำ จังหวัดนครนายก", "n": None, "nn_venue": True,
     "note": "ที่ว่าการอำเภอองครักษ์ · ผู้แทนผู้ใช้น้ำนครนายก 11 คน (ตาราง 9.5.10-1 ถึง 9.5.10-3)"},
]

DWR_PLAN = {
    "src": "สทนช. สำนักงานทรัพยากรน้ำแห่งชาติภาค 2 · แผนป้องกันและแก้ไขภาวะน้ำท่วมลุ่มน้ำเจ้าพระยา ปี 2566 (539 หน้า) หน้า 4-78, 4-88 ถึง 4-90, 2-58, ภาคผนวก ค-2/ค-3",
    "tier": "A",
    "chao_phraya_dam_release_max": 2840, "managed_max_m3s": 3465, "historical_peak_note": "ปี 2549 และ 2554 มากกว่า 5,000 ลบ.ม./วินาที",
    "diversion_now": {"chainat_pasak": 130, "chainat_ayutthaya": 30, "tha_chin": 200, "noi": 230, "makham_thao": 35, "total": 625},
    "canal_adds_m3s": 800, "rapi_phat_now": 210, "rapi_phat_target": 400,
    "rangsit_south_retention_rai": 420000, "retention_total_mcm_target": 1300,
    "flood_prone_rai": {"บ้านนา": {"low": 3807, "mid": 9670, "high": 0, "total": 13477}, "องครักษ์": {"low": 1727, "mid": 18951, "high": 0, "total": 20678}},
    "flood_prone_src": "กรมพัฒนาที่ดิน 2562 ตามภาคผนวก ค ตาราง ค-2 หน้า 333 (พื้นที่ประสบปัญหาน้ำท่วมซ้ำซาก)",
    "villages_at_risk_listed": {"บ้านนา": 3, "องครักษ์": 10, "src": "บัญชีหมู่บ้านเสี่ยง ภาคผนวก ง-3 หน้า 345 (นับจากรหัสหมู่บ้านที่ตัวอ่านได้ — อาจไม่ครบ)"},
    "event_2569": {"date": "14 ต.ค. 2569", "gistda_mcm": {"4 ต.ค.": 2010, "9 ต.ค.": 1088}, "drained_mcm": 922,
                   "route": "ปลายคลองรังสิต/คลอง 13 → ปตร.เสาวภาผ่องศรี (องครักษ์) → ปตร.สมบูรณ์ (บ้านสร้าง ปราจีนบุรี) → แม่น้ำบางปะกง (บางคล้า/บ้านโพธิ์) และรับน้ำที่หนองจอก/ประเวศ",
                   "src": "ข่าว สทนช. 14 ต.ค. 2569 (thailandplus.tv) และประชาชาติธุรกิจ — ชั้น B"},
}

# แบบรายละเอียด ม.ค. 2565–ก.ค. 2566 (เอกสารประชุมกลุ่มย่อยครั้งที่ 3 ระยะที่ 1 มี.ค. 2566 · เอกสารระยะที่ 2 ก.พ.–มิ.ย. 2566 — ก่อน EIA ฉบับอนุมัติ)
DESIGN_2566 = {
    "src": "data/manual/ป่าสัก-อ่าวไทย-ระยะที่1 (ประชุมกลุ่มย่อย 3 เวที 1–6, 20–23 มี.ค. 2566) และ …ระยะที่2 (เอกสารแนะนำโครงการ ม.ค. 2566 · ปฐมนิเทศ 16–17 ก.พ. 2566 · สัมมนา มิ.ย. 2566)",
    "phase1": {"km": [81.0, 135.555], "crossings": 27, "crossings_with_locks": 5, "road_bridges": 23, "rail_bridges": 1, "gates": 2, "end_gate_km": 133.936},
    "phase2": {"km": [0.0, 81.0], "crossings": 28, "aqueducts": 7, "road_bridges_p8": 30, "road_bridges_p17": 32, "rail_bridges": 1, "intakes": 4, "gates": 3,
               "reach_23_81": {"bottom_m": 70, "depth_m": 6, "corridor_m": 200}, "reach_0_23": {"bottom_m": 53, "depth_m": 7, "corridor_m": 170},
               "m6_km": 17.075, "expressway_km": 62.962, "tambons_nn": 6, "src_note": "นครนายก: บ้านนา 1 ตำบล (บ้านพริก) · องครักษ์ 5 ตำบล"},
    "total_crossings": 27 + 5 + 28,
    "total_road_bridges_min": 23 + 30, "total_road_bridges_max": 23 + 32,
    "plan_then": {"knch": 2568, "cabinet": 2568, "construction": "2570–2574", "complete": "2574–2575"},
    "design_period": {"phase1": "1 ก.ค. 2564 – 20 มิ.ย. 2566", "phase2": "1 ธ.ค. 2565 – 19 พ.ย. 2567"},
    "ph2_orientation_nn": {"date": "16 ก.พ. 2566", "venue": "ห้องประชุมแสดขาว โรงเรียนองครักษ์ อ.องครักษ์ จ.นครนายก", "covers": "อ.องครักษ์ อ.บ้านนา (นครนายก) · อ.หนองเสือ (ปทุมธานี) · อ.บางน้ำเปรี้ยว (ฉะเชิงเทรา)"},
    "note_depth": "เอกสาร 2564–2566 ใช้ท้อง 70 ม. ลึกน้ำ 6 ม. ช่วง กม.23 เป็นต้นไป · แต่ รายงานผลกระทบสิ่งแวดล้อม (ก.พ. 2569) ใช้ลึก 7 ม. ตามผลศึกษาปี 2560 — ขัดกัน ยังไม่ทราบค่าสุดท้ายของแบบ",
}

EIA_VERSIONS = {
    "src": "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/EIA/ (รายงานฉบับหลัก · ชี้แจงเพิ่มเติมครั้งที่ 1 · ครั้งที่ 2 + หนังสือแจ้งมติ คชก. 3 ฉบับ) · เลขหน้า = หน้าที่ของไฟล์",
    "status_note": "ทั้ง 3 รอบไม่ได้รับความเห็นชอบในครั้งนั้น: รอบ 1 คชก. ให้ทำรายงานใหม่ · รอบ 2–3 ให้ปรับปรุง แก้ไข เพิ่มเติม — ฉบับที่ คชก. เห็นชอบ (พ.ค. 2568) เป็นฉบับถัดมา",
    "rounds": [
        {"id": "r2561", "label": "ฉบับหลัก ส่ง พ.ย. 2561", "mti": "คชก. 1 ก.พ. 2562: ให้จัดทำรายงานใหม่", "pages": 953,
         "canal": {"length_km": 135.2, "q_max": 1000, "bed_m": "90–800", "depth_m": "2–6", "row_m": "210–260", "src": "หน้า 78 · 90"},
         "structures": 99, "road_bridges": 41, "rail_bridges": 2, "construction_years": 3, "cost_mb": 113989,
         "land_rai": 14609, "land_comp_mb": 17616, "buildings": 1625, "build_comp_mb": 1435,
         "econ": {"eirr_pct": 15.83, "bc9": 1.82, "npv9_mb": 73075, "bc12": 1.35, "npv12_mb": 29559, "src": "บทที่ 8 หน้า 784 (สรุปผู้บริหาร หน้า 82 ระบุ EIRR 14.52% · B/C 1.22 · NPV 14,127 ล้านบาท — ไม่ได้กระทบยอด)"},
         "float_rationale": "คลองในช่วง กม.23–134 ระดับน้ำสูงกว่าดินเดิม 1–3.3 ม. จึงเป็นคลองลอย · เพราะแนวคลองอยู่ใกล้ชุมชน ที่ดินแพง จึงกำหนดให้เป็นคลองดาดคอนกรีตเพื่อลดขนาดเขตคลอง (หน้า 117)",
         "reviewer_points": ["ทบทวนว่า 99 อาคารเป็นส่วนของโครงการ (ข้อ 1.1)", "ไม่ชัดเจนเรื่องระยะเวลาก่อสร้าง 3 ปี ไม่สมเหตุสมผล (ข้อ 1.12)", "รอยเลื่อนองครักษ์: เจาะสำรวจอย่างน้อย 5 หลุมตามแนวคลอง (ข้อ 5.4)", "ผลของน้ำทะเลสูงขึ้น (ตามคณะกรรมการระหว่างรัฐบาลว่าด้วยการเปลี่ยนแปลงสภาพภูมิอากาศ) ต่อการระบายน้ำ (ข้อ 12.1)", "ผลกระทบปลายคลองต่อป่าชายเลน/ตะกอน/ชายฝั่ง (ข้อ 8, 10, 13)"]},
        {"id": "r2564", "label": "ชี้แจงเพิ่มเติมครั้งที่ 1 ส่ง ก.ย. 2564", "mti": "คชก. 28 ต.ค. 2564: ให้ปรับปรุง แก้ไข เพิ่มเติม", "pages": 1020,
         "canal": {"length_km": 135.2, "q_max": 1000, "q_note": "ความเร็วปากคลองคำนวณที่ ~600 ม³/วินาที (หน้า 262)", "bed_m": "90–800", "depth_m": "2–6", "row_m": "210–260", "src": "หน้า 81 · 262"},
         "structures": 99, "road_bridges": 41, "rail_bridges": 2, "construction_years": 3, "cost_mb": None,
         "land_rai": 14609, "land_rai_summary": 16302, "land_comp_mb": 17616, "buildings": 1625, "build_comp_mb": 1435,
         "econ": {"eirr_pct": 13.33, "bc9": 1.51, "npv9_mb": 45115, "bc12": 1.12, "npv12_mb": 10046, "src": "บทที่ 8 หน้า 828–829"},
         "reviewer_points": ["แผนหลัก 9 แผนบรรเทาอุทกภัย: ข้อมูลสาระสำคัญและเหตุผลความจำเป็น (ข้อ 1.1)", "ทบทวนการอยู่คู่ถนนวงแหวนรอบ 3 และการป้องกันน้ำท่วม (ข้อ 1.2)", "เปรียบเทียบทางเลือกแนวเส้นทาง (ข้อ 1.5)", "ผลกระทบท้ายน้ำหากไม่ระบายลงทะเลได้ (ข้อ 1.6)"]},
        {"id": "r2566", "label": "ชี้แจงเพิ่มเติมครั้งที่ 2 ส่ง ธ.ค. 2566", "mti": "คชก. 8 มี.ค. 2567: ให้ปรับปรุง แก้ไข เพิ่มเติม", "pages": 413,
         "canal": {"length_km": 135.9, "q_max": 600, "bed_m": None, "depth_m": 7, "row_m": None, "src": "หน้า 73 (ช่วงชัยนาท–ป่าสัก 930 ม³/วินาที · ยาว 134.44 กม.)"},
         "structures": 99, "road_bridges": 41, "rail_bridges": 2, "construction_years": 5, "cost_mb": None,
         "land_rai": 16288, "land_rai_summary": 16302, "land_comp_mb": 19677, "buildings": 1378, "build_comp_mb": 1994,
         "econ": {"eirr_pct": 11.95, "bc9": 1.42, "npv9_mb": 33774, "bc12": 0.99, "npv12_mb": -392, "src": "บทที่ 3 หน้า 121"},
         "crossing_types": "จุดตัดคลองเดิมกับคลองระบายน้ำหลาก มี 3 แบบ: สะพานน้ำข้ามคลองเดิม (คลองเดิมสูงกว่า) · อุโมงค์น้ำ/ไซฟอนลอดใต้ (คลองเดิมต่ำกว่า) · ประตูเรือสัญจร (หน้า 300 · 307)",
         "reviewer_points": ["ให้จัดลำดับความสำคัญ 9 แผนงานและแสดงผลที่ลดน้ำท่วมได้ (ข้อ 1.1)", "ชี้แจงแผนบริหารน้ำที่จุดเชื่อมชัยนาท–ป่าสักกับเขื่อนทดน้ำป่าสัก (ข้อ 1.4)", "ทบทวนแนวทางไม่ใช้โครงสร้าง (ข้อ 1.5)", "ที่ดินที่ต้องหาเพิ่ม 14.04 ล้าน ลบ.ม. (ข้อ 1.6)"]},
        {"id": "r2569", "label": "ฉบับที่ คชก. เห็นชอบ (ใช้ในรายงานฉบับนี้)", "mti": "คชก. พ.ค. 2568 · กก.วล. 18 ธ.ค. 2568", "pages": None,
         "canal": {"length_km": 135.655, "q_max": 600, "bed_m": 70, "depth_m": 7.0, "row_m": 200, "src": "รายงานฉบับ ก.พ. 2569 (ดู 3.3b)"},
         "land_rai": 16288, "buildings": 1378, "econ": {"eirr_pct": 10.94, "bc9": 1.48, "bc12": 0.97, "npv12_mb": -2821}},
    ],
    "fault": {"claim": "รายงานฉบับ 2561 และ 2564 จัดรอยเลื่อนองครักษ์ (ยาวราว 177 กม. พาดผ่าน อ.องครักษ์) เป็น \"รอยเลื่อนที่ไม่มีพลัง\" และประเมินความเสี่ยงต่อโครงสร้างระดับน้อยถึงปานกลาง (ฉบับ 2564 หน้า 616–617)",
              "reviewer": "คชก. รอบ 1 ตามหนังสือ สผ. ที่ ทส 1010.6/2233 (18 ก.พ. 2562) ข้อ 5.4–5.5 สั่งให้ตัดคำว่า \"เป็นรอยเลื่อนไม่มีพลัง\" เพราะยังไม่มีการศึกษาในรายละเอียด ปรับเป็นมีความเสี่ยงน้อยและมีผลกระทบ และกำหนดเป็นมาตรการระยะก่อสร้างให้เจาะสำรวจดินอย่างน้อย 5 หลุมถึงชั้นดินแข็ง",
              "status": "ผลเจาะสำรวจ 5 หลุมเป็นมาตรการบังคับในระยะก่อสร้าง (ยังไม่เกิดขึ้นก่อนเริ่มโครงการ) — เอกสารที่มีพบเฉพาะเจาะสำรวจเพื่อหาวัสดุถม 2 หลุม ลึก 33.9 ม."},
    "qa": {
        "gates_km": [0.57, 23.0, 74.0, 102.0, 134.35],
        "gates_src": "ตาราง 2.3.2-3 (ปตร.ปากคลอง · กลางคลอง 1–3 · ปลายคลอง) · หลักการเดินประตู ฉบับ 2561 หน้า 138",
        "fault_len_km": 177, "fault_src": "ฉบับ 2564 หน้า 617",
        "found_soil_cement": "ตาราง 2.3.2-2 ฉบับ 2561: เสริมฐานรากด้วยเสาเข็มดินซีเมนต์/ผสมดินลึก ตามโซนดินอ่อน กม.23–135.9 (ปัจจัยความปลอดภัย 1.57–1.81)",
        "plans_n": 9, "plan_order": "อันดับแรก คลองป่าสัก–อ่าวไทย (แผนงาน 2.2) · อันดับสอง ชัยนาท–ป่าสัก (แผนงาน 2.1)",
        "plan_model": "ผลแบบจำลองในรายงานระบุว่ารับมือน้ำท่วมรอบ 50 ปีที่ใกล้เคียงปี 2554 ควรพัฒนาแผนงานที่ 7 และ 2 (ฉบับ 2566 หน้า 79) · แผนงานที่ 3 ยังจำเป็นหากต้องการความเชื่อมั่นสูงขึ้น",
        "om_mb_per_year": _K("opex_annual_mb"), "om_src": "รายงานผลกระทบสิ่งแวดล้อม ฉบับสมบูรณ์ 2569 เล่ม 2 หน้า 159 · เฉลี่ยรายปี · ร้อยละ 0.25 ของงานโยธา ร้อยละ 1 ของงานชลศาสตร์ ร้อยละ 1.5 ของระบบควบคุมระยะไกลและโทรมาตร",
    },
    "no_lateral_flood_model": "ค้นคำว่าแบบจำลองน้ำท่วม/ผลกระทบข้างคลอง/ท่วมขัง ในเนื้อรายงานฉบับ 2564 และ 2566 ไม่พบการคำนวณน้ำท่วมด้านข้างของคลองลอย (พบเฉพาะแบบจำลองระบายน้ำลงทะเลและชายฝั่ง)",
    "unchanged": ["แนวคิดคลองลอยดาดคอนกรีตตั้งแต่ กม.23 ตลอดทุกฉบับ (เหตุผล: ลดขนาดเขตคลองเพราะที่ดินแพง)", "จำนวนอาคารประกอบ 99 แห่ง สะพานรถยนต์ 41 + รถไฟ 2 แห่ง ตั้งแต่ 2561 ถึง 2566", "ที่ปรึกษา: บริษัท พิสุทธิ์ เทคโนโลยี จำกัด (ตามหนังสือ คชก. 2564 · 2567)"],
    "changed": ["ผลตอบแทนทางเศรษฐกิจลดลงทุกฉบับ: B/C ที่ 12% จาก 1.35 → 1.12 → 0.99 → 0.97", "พื้นที่เวนคืนเพิ่มจาก 14,609 เป็น 16,288 ไร่ · สิ่งปลูกสร้างลดจาก 1,625 เป็น 1,378 หลัง · ค่าชดเชยที่ดินเพิ่มจาก 17,616 เป็น 19,677 ล้านบาท", "ระยะก่อสร้างที่ระบุ 3 ปี (2561–2564) → 5 ปี (2566) → 7–8 ปี (2569)"],
    "other_files": [
        {"file": "เอกสาร วสท. \"แนวทางที่ถูกต้องในการบริหารจัดการอุทกภัยในลุ่มน้ำเจ้าพระยา\"", "what": "เอกสาร วสท. ปี 2556 (139 หน้า) ว่าด้วยการบริหารน้ำหลังมหาอุทกภัย 2554 — เป็นภูมิหลังทั่วไป ไม่ได้พูดถึงคลองนี้โดยเฉพาะ", "tier": "C"},
        {"file": "บันทึกสั้นของผู้ใช้ชื่อ \"เจ้าพระยา2\"", "what": "บันทึก 1 บรรทัดของผู้ใช้: ข้อเสนอลดระดับคลองจาก กม.23 ให้เสมอดินเดิม (บางจุดสูงถึง 5 ม.) เพื่อประหยัดงบ — ข้อเสนอ ไม่ใช่ข้อมูล", "tier": "C"},
    ],
}

PARTICIPATION.sort(key=lambda x: ["26–27 ม.ค. 2559", "25–29 เม.ย. 2559", "25 ก.ค.–1 ส.ค. 2559", "24 ก.พ.–3 มี.ค. 2560", "28–29 มี.ค. 2560", "มี.ค. 2565", "16 ก.พ. 2566", "8 ก.พ.–15 มี.ค. 2566", "24 ก.พ. 2566", "20–23 มี.ค. 2566"].index(x["date"]))


def design_check():
    """ตรวจว่าตัวแปรออกแบบรายช่วง (ชั้น B) รับ 600 ลบ.ม./วินาที ได้ด้วยความลาดชันเท่าไร เทียบความลาดพื้นดินตามแนว"""
    out = []
    for s in DESIGN_SEGMENTS:
        z = 0.0 if s["shape"] == "ตัวยู" else 2.0
        n = 0.015 if s["lined"] else 0.025
        b, y = s["bottom_m"], s["depth_m"]
        A = (b + z * y) * y
        P = b + 2 * y * math.sqrt(1 + z * z)
        R = A / P
        v = 600.0 / A
        S = (v * n / R ** (2 / 3)) ** 2
        out.append({**s, "assumed_side_slope": z, "assumed_n": n, "velocity_ms": round(v, 2),
                    "required_slope_m_per_km": round(S * 1000, 3), "area_m2": round(A)})
    area_km2 = sum(s["length_km"] * s["corridor_m"] / 1000 for s in DESIGN_SEGMENTS)
    return {"segments": out, "corridor_area_rai": round(area_km2 * 625),
            "note": "สมมติ: ตัวยูด้านตั้ง n=0.015 · คลองดินด้านลาด 1:2 n=0.025 · ไม่ใช่แบบออกแบบ — ใช้ดูความสอดคล้องเท่านั้น"}


def struct_compare():
    rows = list(csv.DictReader(open(OUT / "structures_all.csv", encoding="utf-8")))
    cross = [r for r in rows if float(r["km"]) >= 81.0 and r["kind"] in ("อาคารเชื่อมจุดตัดคลอง", "ท่อระบายน้ำและไซฟอน")]
    br = [r for r in rows if float(r["km"]) >= 81.0 and r["kind"] == "สะพานรถยนต์"]
    return {"reach_km": [81.0, 135.9],
            "n_crossing_2569_sheets": len(cross),
            "n_crossing_2565": DESIGN_2565_STRUCTS["crossings_14"] + DESIGN_2565_STRUCTS["crossings_with_lock_5"],
            "n_road_bridge_2569_sheets": len(br), "n_road_bridge_2565": DESIGN_2565_STRUCTS["road_bridges"],
            "official_total_crossings": {"eia_2569": 34 + 5, "design_2560": DESIGN_2560["crossings_siphon_drain"] + DESIGN_2560["crossings_with_locks"], "design_2566": DESIGN_2566["total_crossings"]},
            "phase_split": {"p1_sheets": sum(1 for r in rows if float(r["km"]) >= 81.0 and r["kind"] in ("อาคารเชื่อมจุดตัดคลอง", "ท่อระบายน้ำและไซฟอน")),
                            "p2_sheets": sum(1 for r in rows if float(r["km"]) < 81.0 and r["kind"] in ("อาคารเชื่อมจุดตัดคลอง", "ท่อระบายน้ำและไซฟอน")),
                            "p1_bridges_sheets": sum(1 for r in rows if float(r["km"]) >= 81.0 and r["kind"] == "สะพานรถยนต์"),
                            "p2_bridges_sheets": sum(1 for r in rows if float(r["km"]) < 81.0 and r["kind"] == "สะพานรถยนต์")},
            "all_route_crossings_sheets": sum(1 for r in rows if r["kind"] in ("อาคารเชื่อมจุดตัดคลอง", "ท่อระบายน้ำและไซฟอน")),
            "all_route_road_bridges_sheets": sum(1 for r in rows if r["kind"] == "สะพานรถยนต์"),
            "design_2566_phase1": {"crossings": DESIGN_2566["phase1"]["crossings"] + DESIGN_2566["phase1"]["crossings_with_locks"], "road_bridges": DESIGN_2566["phase1"]["road_bridges"]},
            "note": "แบบ 2565 นับจากเอกสารกรมชลประทาน (14+5 อาคารตัดคลอง · สะพานรถยนต์ 15) · แบบรายละเอียดมี.ค. 2566 ระยะที่ 1: 27+5 · สะพาน 23 (เพิ่มขึ้นจากแบบ 2565) · แผนที่ล่าสุดนับจากแผนที่รายช่วงที่ผู้ใช้ได้มา อ่านด้วยตา"}


def eia_structs_summary():
    """สรุปตารางอาคารประกอบ (ตาราง 2.3.2-3) จาก analysis/goal7/eia_structs.json (ผลิตโดย goal7_eia_structs.py)"""
    f = OUT / "eia_structs.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))
    nn = d["nn_reach"]
    cr = nn["crossings"]
    for c in cr:
        c["ratio"] = round(c["q_struct"] / c["q_in"], 2) if c.get("q_in") else None
        c["shortfall"] = c["q_struct"] < c["q_in"]
    ov = OUT / "waterchart_overlay.json"
    zone = None
    if ov.exists():
        ivs = json.loads(ov.read_text(encoding="utf-8"))["layers"]["Floodway"]["nn"]["km_intervals"]
        zc = [c for c in cr if any(a <= c["km"] <= b for a, b in ivs)]
        zone = {"intervals": ivs, "n": len(zc), "kms": [c["km"] for c in zc],
                "q_in_sum": round(sum(c["q_in"] for c in zc), 1), "q_struct_sum": round(sum(c["q_struct"] for c in zc), 1)}
    return {
        "src": "ตาราง 2.3.2-3 บัญชีอาคารประกอบของคลองระบายน้ำหลาก (รายงานผลกระทบสิ่งแวดล้อม) · q_in = อัตราไหลของคลองเดิมที่ตัดตามตาราง (ลบ.ม./วินาที — อย่างน้อย 2 จุดตรงกับน้ำหลากรอบ 10 ปี 5 วัน ของพื้นที่รับน้ำในตาราง 2.3.2-1: แม่น้ำใน 28.05 ↔ PK-AT-4 และคลองหนองแค 18.05 ↔ PK-AT-3 ส่วนจุดอื่นตารางไม่ระบุนิยาม) · q_struct = อัตราไหลของอาคารเชื่อม",
        "versions": {v: {"n": x["n"], "pdf_pages": x["pdf_pages"]} for v, x in d["versions"].items()},
        "identical_across_versions": len(d["diffs_vs_2561"]) == 0, "n_diffs": len(d["diffs_vs_2561"]),
        "match": d["match"],
        "nn": {"km": nn["km"], "n_all": nn["n_all"], "n_crossings": nn["n_crossings"], "n_road_bridges": nn["n_road_bridges"], "n_locks": nn["n_locks"],
               "q_in_sum": round(sum(c["q_in"] for c in cr), 1), "q_struct_sum": round(sum(c["q_struct"] for c in cr), 1),
               "n_shortfall": sum(c["shortfall"] for c in cr), "crossings": cr, "zone_floodway": zone},
    }


BASINS_2569 = [  # ตาราง 2.3.2-1 รายงานฉบับ 2569 (หน้าไฟล์ 149) · พื้นที่ ไร่ · น้ำหลากรอบ 10 ปี 5 วัน · อาคารระบาย/สูบ (ลบ.ม./วินาที)
    {"id": 1, "area_rai": 21642, "q10": 6.415, "canal": "คลองหนองสรวง", "outlet": "ท่อระบายน้ำ", "out_q": 6.145, "to": "คลองระบายน้ำหลาก", "route": "floodway"},
    {"id": 2, "area_rai": 36918, "q10": 15.712, "canal": "-", "outlet": "ท่อระบายน้ำ", "out_q": 15.712, "to": "คลองระบายน้ำหลาก", "route": "floodway"},
    {"id": 3, "area_rai": 45750, "q10": 18.080, "canal": "คลองหนองแค", "outlet": "ท่อระบายน้ำ", "out_q": 18.080, "to": "คลองระบายน้ำหลาก", "route": "floodway"},
    {"id": 4, "area_rai": 206224, "q10": 28.046, "canal": "แม่น้ำใน", "outlet": "ท่อระบายน้ำ + คลองเชื่อมไปคลองบางปลากด", "out_q": 28.046, "to": "คลองระบายน้ำหลาก/แม่น้ำนครนายก", "route": "connect"},
    {"id": 5, "area_rai": 501513, "q10": 112.54, "canal": "คลองเชียงรากน้อย", "outlet": "สถานีสูบน้ำเชียงรากน้อย", "out_q": 45.0, "to": "แม่น้ำเจ้าพระยา", "route": "pump"},
    {"id": 6, "area_rai": 553570, "q10": 176.921, "canal": "คลองรังสิตประยูรศักดิ์", "outlet": "ไซฟอนลอดคลอง", "out_q": 120.0, "to": "เจ้าพระยา/บางปะกง", "route": "siphon"},
    {"id": 7, "area_rai": 178479, "q10": 74.033, "canal": "คลองหกวาสายล่าง", "outlet": "ไซฟอนลอดคลอง", "out_q": 36.0, "to": "แม่น้ำบางปะกง", "route": "siphon"},
    {"id": 8, "area_rai": 172715, "q10": 71.642, "canal": "คลองแสนแสบ", "outlet": "สถานีสูบน้ำหนองจอก", "out_q": 60.0, "to": "คลองพระองค์ไชยานุชิต", "route": "pump"},
    {"id": 9, "area_rai": 175233, "q10": 46.472, "canal": "คลองประเวศบุรีรมย์", "outlet": "สถานีสูบน้ำประเวศ", "out_q": 60.0, "to": "คลองพระองค์ไชยานุชิต", "route": "pump"},
    {"id": 10, "area_rai": 224187, "q10": 115.834, "canal": "คลองชายทะเล", "outlet": "สถานีสูบน้ำ 6 แห่ง", "out_q": 301.0, "to": "อ่าวไทย", "route": "pump"},
    {"id": 11, "area_rai": 132281, "q10": 42.277, "canal": "คลองด่าน", "outlet": "สถานีสูบน้ำชลหารพิจิตร", "out_q": 120.0, "to": "อ่าวไทย", "route": "pump"},
    {"id": 12, "area_rai": 119807, "q10": 26.885, "canal": "คลองหกวาสายล่าง", "outlet": "สถานีสูบน้ำสมบูรณ์", "out_q": 15.0, "to": "แม่น้ำนครนายก", "route": "pump"},
    {"id": 13, "area_rai": 190444, "q10": 42.736, "canal": "คลองบางขนาก", "outlet": "สถานีสูบน้ำบางขนาก", "out_q": 54.0, "to": "แม่น้ำบางปะกง", "route": "pump"},
    {"id": 14, "area_rai": 156282, "q10": 49.948, "canal": "คลองนครเนื่องเขต", "outlet": "สถานีสูบน้ำท่าไข่", "out_q": 36.0, "to": "แม่น้ำบางปะกง", "route": "pump"},
    {"id": 15, "area_rai": 84814, "q10": 28.701, "canal": "คลองประเวศบุรีรมย์", "outlet": "สถานีสูบน้ำท่าถั่ว", "out_q": 48.0, "to": "แม่น้ำบางปะกง", "route": "pump"},
    {"id": 16, "area_rai": 106021, "q10": 30.28, "canal": "คลองสำโรง", "outlet": "สถานีสูบน้ำปากตะคอง", "out_q": 24.0, "to": "แม่น้ำบางปะกง", "route": "pump"},
    {"id": 17, "area_rai": 59612, "q10": 18.027, "canal": "คลองชายทะเล", "outlet": "สถานีสูบน้ำเทพรังสรรค์/พระยาวิสูตร", "out_q": 24.0, "to": "อ่าวไทย", "route": "pump"},
]


def basins_summary():
    rows = []
    for b in BASINS_2569:
        r = dict(b)
        r["q10_per_1000rai"] = round(b["q10"] / b["area_rai"] * 1000, 2)
        r["cap_ratio"] = round(b["out_q"] / b["q10"], 2)
        rows.append(r)
    below = [r["id"] for r in rows if r["cap_ratio"] < 0.95 and r["route"] in ("pump", "siphon")]
    return {"src": "ตาราง 2.3.2-1 รายงานฉบับ 2569 (หน้าพิมพ์ 2-44 · หน้าไฟล์ 149) — ที่มา: บริษัทที่ปรึกษา (2560) · น้ำหลากคำนวณจากฝนสูงสุด 5 วันรอบ 10 ปี ด้วยสัมประสิทธิ์การระบายน้ำ",
            "rows": rows, "total_area_rai": sum(b["area_rai"] for b in BASINS_2569), "below_capacity_ids": below,
            "note": "อัตราส่วนความจุ = อาคารระบาย/สูบที่ระบุ ÷ น้ำหลาก — ต่ำกว่า 1 ไม่ได้แปลว่าท่วมเสมอ (น้ำหลากเป็นค่าเฉลี่ย 5 วัน มีแก้มลิง/ที่ลุ่มรับ) แต่บอกพื้นที่ที่ระบบเดิมตึง"}


def options_screening(c):
    """ข้อเสนอเพื่อลดโทษ/เพิ่มประโยชน์ — การคัดกรองเชิงปริมาณ (ไม่ใช่การออกแบบ) · สมมติฐานระบุในฟิลด์ assumptions"""
    sec = c["eia_section"]
    z1, z2, road, D = sec["z1"], sec["z2"], sec["road_m"], sec["D_m"]
    n = sec["n"]
    FB, Q = 1.5, 600.0
    g40 = float(np.interp(40, [x[0] for x in PROFILE_FIG["ground"]], [x[1] for x in PROFILE_FIG["ground"]]))
    km_end, ws_end = 134.0, 1.5
    L_km = km_end - 40.0

    def cap(b, d, S):
        A = (b + z1 * d) * d
        P = b + 2 * d * math.sqrt(1 + z1 * z1)
        return (1 / n) * A * (A / P) ** (2 / 3) * S ** 0.5

    wide = []
    for ht in (3.3, 2.0, 1.0, 0.0):
        ws40 = g40 + ht
        S = (ws40 - ws_end) / (L_km * 1000)
        b = brentq(lambda x: cap(x, D, S) - Q, 5, 2000)
        crest_h = ht + FB
        half = b / 2 + z1 * (D + FB) + road + z2 * crest_h
        wide.append({"water_above_ground_m": ht, "crest_above_ground_m": round(crest_h, 1), "slope_1_n": round(1 / S), "bottom_m": round(b),
                     "corridor_m": round(2 * half), "land_vs_now_pct": None})
    base = wide[0]["corridor_m"]
    for w in wide:
        w["land_vs_now_pct"] = round((w["corridor_m"] / base - 1) * 100)
    eta, rho_g = 0.75, 9810.0
    outlet = []
    for dh in (1.0, 2.0, 3.0):
        P = rho_g * Q * dh / eta / 1e6
        outlet.append({"lower_m": dh, "crest_above_ground_km40_m": round(4.8 - dh, 1), "power_mw": round(P, 1), "gwh_per_10d": round(P * 240 / 1000, 2),
                       "note": "ระดับน้ำทั้งแนวลดลงเท่ากัน (ความลาดเท่าเดิม) ท้องคลองปลายทางลึกลงตามกัน"})
    lat = []
    for q in (10.0, 28.0, 60.0):
        for h in (1.7, 3.3):
            P = rho_g * q * h / eta / 1e6
            lat.append({"q_m3s": q, "lift_m": h, "power_mw": round(P, 2)})
    # โซลาร์ลอยน้ำ
    L_float = 134.0 - 23.0
    w_ws = (sec["A_m2"] / D - z1 * D) + 2 * z1 * D
    area_km2 = L_float * w_ws / 1000.0
    pv = []
    for cov in (0.1, 0.2):
        mwp = area_km2 * 1e6 * cov * 0.15 / 1000.0   # 0.15 kWp ต่อ ตร.ม.ผิวน้ำที่ปกคลุม
        pv.append({"coverage_pct": int(cov * 100), "mwp": round(mwp), "gwh_per_year": round(mwp * 1.4, 0),
                   "evap_saved_mcm_per_year": round(area_km2 * cov * 1.5 * 0.7, 1)})
    gate_vol = 25.0 * 1000 * w_ws * (2.5 - 1.5) / 1e6
    return {
        "assumptions": {"n": n, "pump_eff": eta, "Q_m3s": Q, "ground_km40_m": round(g40, 2), "end_level_m": ws_end, "pv_kwp_per_m2": 0.15,
                        "pv_kwh_per_kwp_year": 1400, "evap_m_per_year": 1.5, "evap_reduction": 0.7, "event_hours": 240,
                        "canal_water_width_m": round(w_ws), "canal_water_area_km2_km23_134": round(area_km2, 1)},
        "wide_canal": wide, "outlet_pump": outlet, "lateral_pump": lat, "floating_pv": pv,
        "outlet_gate_storage_mcm": round(gate_vol, 1),
        "src_note": "ค่าคัดกรองคำนวณเอง จากตัวเลขหน้าตัดและระดับในรายงานฯ — ใช้เทียบลำดับขนาดของทางเลือก ไม่ใช่แบบ",
    }


def runoff_screening(c):
    """ประมาณน้ำไหลบ่าตอนฝนหนักซ้อนช่วงผันน้ำหลาก — คัดกรองลำดับขนาดจากฝนกริด (ERA5 จุดตัวเมืองนครนายก 2543–2569) พื้นที่รับน้ำตามตาราง 2.3.2-1
    และทางระบายตามตาราง 2.3.2-3 · ไม่ใช่แบบจำลองไหลบ่า: สมมติฐานระบุไว้ใน assumptions"""
    import datetime as dt
    f = ROOT / "data/04_tmd_rainfall/raw_era5/town_daily.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))["daily"]
    dates = [dt.date.fromisoformat(x) for x in d["time"]]
    v = np.array([np.nan if x is None else x for x in d["precipitation_sum"]], dtype=float)
    best = {}
    for i in range(len(v) - 4):
        if dates[i].month in (7, 8, 9, 10, 11) and not np.isnan(v[i:i + 5]).any():
            s = float(v[i:i + 5].sum())
            y = dates[i].year
            if s > best.get(y, (0, None))[0]:
                best[y] = (s, dates[i].isoformat())
    yrs = sorted(y for y in best if y < 2026)
    vals = np.array([best[y][0] for y in yrs])
    beta = vals.std(ddof=1) * math.sqrt(6) / math.pi
    loc = vals.mean() - 0.5772 * beta
    gum = {str(T): round(loc - beta * math.log(-math.log(1 - 1 / T)), 0) for T in (2, 10, 50, 100)}
    R_event = round(best[2026][0], 0)
    DAY5 = 5 * 86400.0
    sel = [b for b in BASINS_2569 if b["id"] in (4, 6, 7, 12)]
    rows = []
    for b in sel:
        A = b["area_rai"] / 625.0
        row = {"id": b["id"], "canal": b["canal"], "area_km2": round(A), "q10_eia": b["q10"], "out_q": b["out_q"],
               "eia_drain_depth_mm": round(b["q10"] * DAY5 / (A * 1e6) * 1000, 0)}
        for Cc in (0.5, 0.8):
            for tag, Rr in (("event", R_event), ("t10", gum["10"])):
                q = Cc * Rr / 1000 * A * 1e6 / DAY5
                row[f"q_C{int(Cc*10)}_{tag}"] = round(q)
                row[f"deficit_mcm_C{int(Cc*10)}_{tag}"] = round(max(0.0, q - b["out_q"]) * DAY5 / 1e6, 1)
        rows.append(row)
    es = c["eia_structs"]["nn"]["crossings"]
    small = [x for x in es if x["sip_w"] == 2.0 and x["sip_h"] == 2.0]
    cap_small = sum(x["q_struct"] for x in small)
    ditch = c["embankment"]["ditch_q_each_side_m3s"]
    L = c["eia_structs"]["nn"]["km"][1] - c["eia_structs"]["nn"]["km"][0]
    strip = []
    for W in (2, 5, 10):
        A = W * L
        for Cc in (0.5, 0.8):
            q = Cc * R_event / 1000 * A * 1e6 / DAY5
            strip.append({"W_km": W, "C": Cc, "area_km2": round(A), "q_m3s": round(q), "per_km_m3s": round(q / L, 1)})
    cap_local = {"small_siphons_m3s": round(cap_small), "connecting_canal_m3s": 28.046,
                 "ditches_m3s_low": round(2 * ditch["1e-04"], 1), "ditches_m3s_high": round(2 * ditch["1e-03"], 1)}
    cap_local["total_low"] = round(cap_local["small_siphons_m3s"] + cap_local["connecting_canal_m3s"] + cap_local["ditches_m3s_low"])
    cap_local["total_high"] = round(cap_local["small_siphons_m3s"] + cap_local["connecting_canal_m3s"] + cap_local["ditches_m3s_high"])
    def v_sheet(n, h, S):
        return (1 / n) * h ** (2 / 3) * S ** 0.5 * 86.4   # กม./วัน
    travel = {"n": 0.05, "h_m": [0.2, 0.5], "slope_1_n": [10000, 70000],
              "km_per_day": {f"h{h}_S{s}": round(v_sheet(0.05, h, 1.0 / s), 1) for h in (0.2, 0.5) for s in (10000, 70000)}}
    return {
        "note": "ค่าประมาณลำดับขนาด ไม่ใช่แบบจำลอง — ฝนกริดหยาบ (สถานีบนเขาวัดได้ 1,058–1,416 มม./18 วัน) จึงเป็นขอบล่างของฝนจริง",
        "assumptions": {"rain_src": "ERA5 ผ่าน Open-Meteo (14.2355N, 101.2292E) 2543–2569 · ฝนสะสม 5 วันสูงสุดรายปี ก.ค.–พ.ย. · Gumbel",
                        "C_range": [0.5, 0.8], "C_note": "ที่นาอิ่มน้ำปลายฤดูฝน · ไม่มีค่าทางการ", "event_window_start": best[2026][1],
                        "sheet_n": 0.05, "ground_slope_note": "ตามรูปตัดตามยาว พื้นดิน +2.0→+1.45 ม. ตลอด กม.37–75 (≈1:70,000 ตามแนวคลอง) · ลาดขวางแนวไม่ทราบ ใช้ 1:10,000–1:70,000"},
        "rain_5d_mm": {"annual_max_n_years": len(yrs), "gumbel": gum, "event_2569": R_event, "event_rank": 1 + sum(1 for x in vals if x > R_event)},
        "basins": rows, "strip": strip, "local_capacity": cap_local, "travel": travel,
    }


def extra_questions(c):
    """ข้อมูลสำหรับคำถามชวนอ่านเพิ่ม: เวลาน้ำถึงทะเล · ระยะห่างสะพาน · คืนทุนแบบง่าย · ปลายคลอง/ชายฝั่ง · ผลต่อเหตุการณ์ 2569"""
    out = {}
    L = 135.9
    out["travel"] = {"length_km": L, "v_ms": [0.8, 1.2], "hours": [round(L * 1000 / v / 3600) for v in (1.2, 0.8)],
                     "src": "ความยาวและความเร็วออกแบบ 1.2 ม./วินาที ตามรายงาน (ความเร็วต่ำกว่านี้เมื่อน้ำน้อย)"}
    es = json.loads((OUT / "eia_structs.json").read_text(encoding="utf-8"))
    rows = es["versions"]["2561"]["rows"]
    br = [r for r in rows if r["kind"] == "road_bridge"]
    nn = [r for r in br if 38.6 <= r["km"] <= 73.2]
    kms = [r["km"] for r in nn]
    gaps = [round(b - a, 1) for a, b in zip(kms, kms[1:])]
    out["bridges"] = {"all_n": len(br), "all_mean_gap_km": round(135.9 / len(br), 1), "nn_n": len(nn),
                      "nn": [{"km": r["km"], "name": r["name"]} for r in nn], "nn_gaps_km": gaps,
                      "nn_max_gap_km": max(gaps), "nn_mean_gap_km": round(sum(gaps) / len(gaps), 1),
                      "rail_n": sum(1 for r in rows if r["kind"] == "rail_bridge"),
                      "locks_n": sum(1 for r in rows if r.get("lock"))}
    F = c["facts"]
    lo, hi = 5085.0, 16938.0
    cost = float(F["budget_mb"]["v"])
    om = float(_K("opex_annual_mb"))
    out["payback"] = {"cost_mb": cost, "benefit_mb_low": lo, "benefit_mb_high": hi, "om_mb": om,
                      "years_simple": [round(cost / hi, 1), round(cost / lo, 1)],
                      "years_net_of_om": [round(cost / (hi - om), 1), round(cost / (lo - om), 1)],
                      "src": f"งบ 165,000 ล้านบาท · ความเสียหายที่ลดได้เฉลี่ยปีละ 5,085–16,938 ล้านบาท (เอกสารจังหวัด) · ค่าดำเนินการและบำรุงรักษาปีละ {om:,.2f} ล้านบาท (รายงานฉบับสมบูรณ์ 2569 เล่ม 2 หน้า 159) · ไม่คิดลดค่าเงิน"}
    out["coast"] = {"salinity_drop_psu": 5, "affected_km": 3.5, "salinity_src": "ฉบับ 2569 เล่ม 1 หน้า 693 (แบบจำลอง ที่ 600 ลบ.ม./วินาที ผิวน้ำลดราว 5 หน่วย ท้องน้ำลดเล็กน้อย)",
                    "mangrove_rai": 47, "mangrove_src": "ฉบับ 2569 เล่ม 1 หน้า 752 · หนังสือแจ้งมติ 18 ก.พ. 2562 ข้อ 10.5",
                    "mussel_low_effect_ppt": 15, "mussel_src": "ฉบับ 2569 เล่ม 1 หน้า 694 (หอยแมลงภู่ตายสะสม 100% ที่ความเค็ม 5 และ 10 ภายใน 72 ชม. · 26% ที่ 15)",
                    "erosion_10y_m": {"without": 0.789, "with": 0.755}, "erosion_src": "ฉบับชี้แจงครั้งที่ 2 หน้า 165 (แบบจำลองชายฝั่ง: มีโครงการกัดเซาะเฉลี่ยลดลงเล็กน้อยเพราะตะกอนทับถมเพิ่ม)",
                    "mitigation": "เปิดประตูระบายน้ำลงอ่าวไทยเฉพาะช่วงเสี่ยงท่วม ราวเดือนกันยายน–ตุลาคมที่ผู้เลี้ยงหอยพักการเลี้ยง และแจ้งเตือนล่วงหน้า (หน้า 694)"}
    fb = c["flood_band"]["scenes"]["S1D_20261002_0609"]
    out["event2569"] = {"flood_rai_10km": fb["west_rai"] + fb["east_rai"], "by_amphoe": fb["by_amphoe_rai"], "on_corridor_100m_rai": fb["on_corridor_100m_rai"],
                        "canal_flow_m3s": 600,
                        "note": "คลองนี้รับน้ำจากแม่น้ำเจ้าพระยา/ป่าสัก ไม่ได้รับน้ำจากแม่น้ำนครนายกหรือเขื่อนขุนด่านปราการชล — เหตุน้ำท่วมนครนายก 26–29 ก.ย. 2569 (ฝนเป็นแถบ + บริหารเขื่อน) จึงอยู่นอกเป้าหมายของคลอง"}
    return out


def eia_construction_plan():
    """แผนการก่อสร้าง ลำดับงาน และมาตรการป้องกันน้ำท่วมระหว่างก่อสร้างตาม EIA 2569 (ตาราง 2.4.2-1 และบทที่ 5)"""
    return {
        "src": "รายงานผลกระทบสิ่งแวดล้อม โครงการทางระบายน้ำหลากเจ้าพระยาฝั่งตะวันออกตอนล่าง ฉบับสมบูรณ์ ก.พ. 2569 เล่ม 1 ตาราง 2.4.2-1 (หน้า 2-69 ถึง 2-74) และข้อ 2.4.2.3, เล่ม 2 บทที่ 5 ข้อ 2.1 (หน้า 5-9)",
        "direction": "ปลายน้ำไปต้นน้ำ (จากปากอ่าวไทย กม.135+655 มุ่งหน้าขึ้นสู่แม่น้ำป่าสัก กม.0+000)",
        "rationale": "ต้องขุดและเปิดทางระบายน้ำช่วงปลายน้ำให้สามารถระบายลงสู่อ่าวไทยได้ก่อน จึงจะสามารถเปิดรับน้ำหลากจากแม่น้ำป่าสักที่ต้นน้ำได้ เพื่อป้องกันไม่ให้น้ำเอ่อล้นเข้าท่วมพื้นที่ตอนกลางระหว่างก่อสร้าง",
        "duration_years_eia": 7,
        "fiscal_years_eia": "2571–2577",
        "duration_years_cabinet": 8,
        "fiscal_years_cabinet": "2570–2577 (รวมระยะจัดหาที่ดิน 2570–2573)",
        "contracts_total": 15,
        "contracts_table": [
            {"contract": "สัญญา 1–5", "phase": "ระยะที่ 1", "reach": "ปากอ่าวไทยถึงคลองสำโรง", "km": "กม.98+300–135+655", "start_fy": 2571, "end_fy": 2575, "scope": "ขุดคลองระบายน้ำหลาก, ประตูระบายน้ำปลายคลอง, สถานีสูบน้ำปลายคลอง, อาคารตัดผ่านคลองสำโรง"},
            {"contract": "สัญญา 6–10", "phase": "ระยะที่ 2", "reach": "คลองสำโรงถึงคลองรังสิตฯ (ฉะเชิงเทรา–องครักษ์)", "km": "กม.54+000–98+300", "start_fy": 2572, "end_fy": 2576, "scope": "ขุดคลองระบายน้ำหลากช่วงฉะเชิงเทราและนครนายกตอนล่าง (องครักษ์), ไซฟอนคลองรังสิตประยูรศักดิ์, อาคารบังคับน้ำกลางคลอง"},
            {"contract": "สัญญา 11–15", "phase": "ระยะที่ 3", "reach": "องครักษ์ถึงแม่น้ำป่าสัก (บ้านนา–สระบุรี)", "km": "กม.0+000–54+000", "start_fy": 2573, "end_fy": 2577, "scope": "ขุดคลองช่วงบ้านนาถึงสระบุรี, เขื่อนทดน้ำป่าสัก (ต.เริงราง อ.เสาไห้), ประตูระบายน้ำปากคลอง, ทางน้ำเชื่อมแม่น้ำป่าสัก"},
        ],
        "flood_measures": [
            "กำหนดตารางงานดินและงานขุดลอกในทางน้ำธรรมชาติเดิมให้ดำเนินการเฉพาะในฤดูแล้ง (พฤศจิกายน–เมษายน) เท่านั้น",
            "การก่อสร้างเขื่อนทดน้ำ อาคารบังคับน้ำ และประตูระบายน้ำในลำน้ำเดิม ให้ก่อสร้างทีละครึ่งลำน้ำ โดยคงลำน้ำอีกครึ่งหนึ่งไว้ให้ระบายน้ำหลากได้ตามธรรมชาติตลอดช่วงการก่อสร้าง",
            "จุดที่แนวคลองตัดผ่านคลองชลประทานและคลองส่งน้ำเดิม ให้ขุดทางเบี่ยงน้ำชั่วคราว พร้อมทำนบกั้นน้ำชั่วคราว เพื่อรักษาระดับการส่งน้ำและการระบายน้ำเดิมไม่ให้หยุดชะงัก",
            "จุดตัดคลองคมนาคมและระบายน้ำสำคัญ 5 สาย (คลองนครเนื่องเขต, คลองประเวศบุรีรมย์, คลองสำโรง, คลองปีกกา, คลองชายทะเล) ให้ใช้เข็มพืดเหล็กกั้นเฉพาะฐานรากอาคาร และเปิดช่องระบายน้ำให้กว้างเพียงพอไม่กีดขวางทางน้ำหลาก",
            "ห้ามทิ้งดินขุด กองดิน หรือเศษวัสดุก่อสร้างลงในลำน้ำสาธารณะหรือขวางเส้นทางระบายน้ำเดิมเด็ดขาด",
        ],
        "gap_assessment": "รายงานผลกระทบสิ่งแวดล้อมระบุมาตรการเฉพาะระดับจุดก่อสร้างอาคาร แต่ไม่มีแบบจำลองน้ำท่วมด้านข้าง และไม่มีแผนเผชิญเหตุน้ำท่วมทุ่งบ่า หากเกิดอุทกภัยใหญ่ในระหว่างการก่อสร้าง 7 ปีที่คันคลองบางส่วนสร้างเสร็จแล้วแต่ยังไม่เปิดใช้งานทั้งระบบ",
    }


def ongkharak_flood_persistence(c):
    """ข้อมูลการท่วมขังต่อเนื่องของ อ.องครักษ์ จนถึงปัจจุบัน (กลางเดือนตุลาคม 2569) และปฏิสัมพันธ์กับคลองใหม่"""
    return {
        "status_as_of": "17 ตุลาคม 2569",
        "dem_median_m": {"องครักษ์": 3.2, "เมืองนครนายก": 9.0, "ปากพลี": 9.1, "บ้านนา": 9.6},
        "low_villages_count": 116,
        "sample_lowest_villages": [
            {"name": "ปากคลองสิบห้าหกวา", "tambon": "ชุมพล", "dem_m": 1.02},
            {"name": "ช่องตะเคียน", "tambon": "บึงศาล", "dem_m": 2.32},
            {"name": "ปากบึงพระอาจารย์", "tambon": "บางสมบูรณ์", "dem_m": 2.38},
            {"name": "เหนือทด", "tambon": "ศีรษะกระบือ", "dem_m": 2.38},
            {"name": "องค์พาต", "tambon": "โพธิ์แทน", "dem_m": 2.42},
            {"name": "เตยน้อย", "tambon": "บางสมบูรณ์", "dem_m": 2.48},
            {"name": "เตยใหญ่", "tambon": "บางสมบูรณ์", "dem_m": 2.50},
            {"name": "คลอง 2", "tambon": "บางสมบูรณ์", "dem_m": 2.50},
            {"name": "ทำนบ", "tambon": "ชุมพล", "dem_m": 2.54},
            {"name": "คลอง 22", "tambon": "บางสมบูรณ์", "dem_m": 2.66},
            {"name": "ปากคลองสิบสี่", "tambon": "บึงศาล", "dem_m": 2.69},
            {"name": "ปากคลองพระอาจารย์", "tambon": "บางสมบูรณ์", "dem_m": 2.73},
            {"name": "ปากคลองยี่สิบสอง", "tambon": "ศีรษะกระบือ", "dem_m": 2.77},
            {"name": "ปากบึง", "tambon": "ศีรษะกระบือ", "dem_m": 2.78},
            {"name": "หัวหมอน", "tambon": "บึงศาล", "dem_m": 2.79},
        ],
        "stations_oct2026": {
            "atg101_chula": {"code": "ATG101", "name": "ปตร.จุฬาลงกรณ์ (ปากคลองรังสิตฯ ตะวันตก)", "watergate_in_msl": 1.18, "watergate_out_msl": 2.18, "status": "ระดับน้ำเจ้าพระยาสูงกว่าในคลอง 1.0 ม. ระบายธรรมชาติไม่ได้ การสูบออกเจ้าพระยาถูกจำกัดเพื่อป้องกันน้ำท่วมกรุงเทพฯ"},
            "atg08_dhammaraja": {"code": "ATG08", "name": "ปตร.พระธรรมราชา (คลอง 13 รังสิตฯ)", "watergate_in_msl": 2.93, "watergate_out_msl": 2.32, "status": "ระดับน้ำเหนือน้ำสูง 2.93 ม.รทก. น้ำถูกผลักและสูบข้าม ปตร. ด้วยเครื่องสูบน้ำเคลื่อนที่/สถานีสูบ มุ่งหน้าทิศตะวันออกสู่ทุ่งองครักษ์"},
            "tny10_ongkharak": {"code": "TNy10", "name": "คลองแม่น้ำใน อ.องครักษ์", "level_m_oct17": 2.35, "status": "ระดับน้ำในคลองขนานและทุ่ง 2.3–2.5 ม.รทก. สูงกว่าผิวดินชุมชน (1.0–2.5 ม.รทก.) น้ำขังค้างในแอ่งก้นกระทะ"},
            "ny7_mueang": {"code": "Ny.7", "name": "สะพานหน้าจวนผู้ว่าฯ อ.เมือง", "bank_m": 8.45, "level_m_oct17": 6.28, "status": "ลดลงต่ำกว่าตลิ่งสู่ระดับปกติ (6.28 ม.) ตั้งแต่ 4 ต.ค. 2569"},
            "bpk003_bangnampriao": {"code": "BPK003", "name": "บางน้ำเปรี้ยว ฉะเชิงเทรา", "level_m_oct10": 2.92, "level_m_oct17": 2.56, "oct17_range_m": [2.52, 2.61], "status": "ทรงตัวสูง 2.52–2.92 ม.รทก. สูงกว่าหรือเสมอระดับผิวดินชุมชนลุ่มต่ำองครักษ์"},
            "bpk001_bangpakong": {"code": "BPK001", "name": "ปากแม่น้ำบางปะกง ฉะเชิงเทรา", "swing_m": 2.32, "high_tide_m": 1.43, "low_tide_m": -1.05, "status": "ช่วงน้ำเกิดกลางเดือนตุลาคม แกว่งตัววันละ 2.3–2.5 ม. ปิดประตูระบายน้ำกันน้ำเค็มหนุนเกือบตลอดวัน"},
        },
        "hypothesis1_pump_mechanics": {
            "title": "สมมติฐานที่ 1: การสูบน้ำข้ามประตูระบายน้ำจากทุ่งรังสิตมายังทุ่งองครักษ์",
            "why_waterlevel_insufficient": "การตรวจวัดเฉพาะระดับน้ำคงที่สถิตสองฝั่งประตูน้ำไม่สามารถสรุปทิศทางการเคลื่อนที่ของมวลน้ำได้จริง เนื่องจากมีการติดตั้งเครื่องสูบน้ำขนาดใหญ่ที่สถานีสูบและเครื่องสูบน้ำเคลื่อนที่ (ท่อซิ่ง/ปั๊มไฮดรอลิก) สูบน้ำข้ามบานประตูน้ำที่ปิดอยู่และข้ามคันชะลอน้ำโดยตรง",
            "west_inflow_driver": "ระดับน้ำแม่น้ำเจ้าพระยาที่ ปตร.จุฬาลงกรณ์ (ATG101) สูงกว่าระดับน้ำในคลองรังสิตฯ (+2.18 vs +1.18 ม.รทก. สูงกว่า 1.0 ม.) จึงระบายออกเจ้าพระยาไม่ได้ และการสูบออกเจ้าพระยาถูกจำกัดเพื่อปกป้องกรุงเทพฯ มวลน้ำจึงต้องถูกผลักและสูบมาทางทิศตะวันออก ข้าม ปตร.พระธรรมราชา (ATG08 เหนือน้ำ +2.93 ม.รทก.) สู่คลองรังสิตตอนปลายและทุ่งองครักษ์",
            "east_downstream_block": "ปลายทางระบายน้ำสู่แม่น้ำบางปะกงและอ่าวไทย ที่สถานีบางน้ำเปรี้ยว (BPK003) ทรงตัวสูง 2.52–2.92 ม.รทก. ประกอบกับน้ำทะเลหนุนสูงช่วงน้ำเกิดที่ปากแม่น้ำบางปะกง (+1.43 ม.รทก.) ปิดกั้นการระบายตามแรงโน้มถ่วง",
            "conclusion": "อ.องครักษ์ จึงตกอยู่ในสภาวะ 'คีมหนีบสองด้าน' (Dual-sided Squeeze) คือรับน้ำที่ถูกสูบและผลักดันมาจากฝั่งรังสิตทางทิศตะวันตก ขณะที่ทางระบายน้ำออกสู่อ่าวไทยทางทิศตะวันออกและทิศใต้ถูกบล็อก น้ำจึงไม่มีทางไปและต้องขังค้างในแอ่งก้นกระทะเป็นเวลานาน",
        },
        "hydraulic_gradient": "< 0.00001 (น้อยกว่า 0.01 ม./กม.) ระหว่างทุ่งองครักษ์กับคลองบางน้ำเปรี้ยว ไม่สามารถระบายตามแรงโน้มถ่วงได้",
        "soil_property": "ดินเหนียวชุดองครักษ์และชุดรังสิต เนื้อดินแน่นทึบและเป็นดินกรดกำมะถัน อัตราการซึมน้ำลงดินแทบเป็นศูนย์",
        "retardation_dual": "รับน้ำหลากชะลอตัวจาก อ.เมือง/บ้านนา และรับน้ำระบายจากทุ่งรังสิตใต้ (คลอง 14–31) น้ำจึงขังเป็นสัปดาห์",
        "relation_to_canal": "คลองเจ้าพระยา2 ตัดผ่าน อ.องครักษ์ ช่วง กม.54–73 เป็นคลองลอย (ผิวน้ำ +3.8 ถึง +6.4 ม.รทก.) รับน้ำจากแม่น้ำป่าสักไปอ่าวไทย ไม่ได้รับน้ำท่วมขังในองครักษ์เข้าคลอง หากไม่มีสถานีสูบข้างคลองและขยายขนาดท่อลอดไซฟอน คลองใหม่จะไม่ช่วยลดน้ำท่วมองครักษ์ และคันดินต่อเนื่องอาจเป็นแนวชะลอน้ำหลากข้ามทุ่งเพิ่มเติม",
    }


def embankment_scenarios(c):
    """ประมาณผลของความสูงคันคลองเหนือพื้นเดิม ตามรูปตัดตามยาว (รูปที่ 2.3.2-9) — ไม่ใช่แบบจำลองน้ำท่วม
    ค่าที่ใช้: สันคันเหนือพื้นเดิม ช่วงนครนายก (จากโปรไฟล์) · หน้าตัดตามรายงาน · ตารางอาคาร · พื้นที่น้ำท่วมจริงจากดาวเทียม"""
    es = c["eia_structs"]
    pf = c.get("eia_profile")
    if not es or not pf:
        return None
    sec = c["eia_section"]
    z1, z2, road, D = sec["z1"], sec["z2"], sec["road_m"], sec["D_m"]
    b = sec["A_m2"] / D - z1 * D
    S0 = 1.0 / sec["slope_1_n"]
    FB = 1.5

    def q_manning(bw, d, n=sec["n"]):
        A = (bw + z1 * d) * d
        P = bw + 2 * d * math.sqrt(1 + z1 * z1)
        return (1 / n) * A * (A / P) ** (2 / 3) * S0 ** 0.5

    d6 = DESIGN_2566["phase2"]["reach_23_81"]
    caps = {"eia2569": {"bottom_m": round(b, 1), "depth_m": D, "q_m3s": round(q_manning(b, D))},
            "design2566": {"bottom_m": d6["bottom_m"], "depth_m": d6["depth_m"], "q_m3s": round(q_manning(d6["bottom_m"], d6["depth_m"]))}}
    L_reach = (74.0 - 23.0) * 1000
    nn = pf["nn_reach"]
    cases = []
    defs = [("eia_lo", "ต่ำสุดในช่วงนครนายก (ตรงโคกพื้นดินสูงที่ กม.56–57)", nn["crest_above_ground_min_m"]),
            ("eia_hi", "สูงสุดในช่วงนครนายก (ราว กม.40 พื้นดินต่ำสุด)", nn["crest_above_ground_max_m"])]
    for cid, label, H in defs:
        h = H - FB
        w_ws = b + 2 * z1 * D
        hh = min(h, D)
        w_g = w_ws - 2 * z1 * hh
        vol = L_reach * hh * (w_g + w_ws) / 2 / 1e6
        breach = {str(B): round(1.7 * B * h ** 1.5) for B in (30, 60, 100)}
        cases.append({"id": cid, "label": label, "crest_above_ground_m": round(H, 1), "water_above_ground_m": round(h, 1),
                      "outer_toe_from_crest_m": round(z2 * H, 1), "half_width_m": round(b / 2 + z1 * (D + FB) + road + z2 * H, 1),
                      "volume_above_ground_mcm": round(vol, 1), "breach_peak_m3s": breach,
                      "seep_gradient": round(h / (road + (z1 + z2) * H), 2)})
    cr = es["nn"]["crossings"]
    a_sip = sum(x["sip_n"] * x["sip_w"] * x["sip_h"] for x in cr)
    L_nn = es["nn"]["km"][1] - es["nn"]["km"][0]
    barrier = {"siphon_area_m2": round(a_sip), "length_km": round(L_nn, 1),
               "open_ratio_pct": {str(d): round(a_sip / (L_nn * 1000 * d) * 100, 2) for d in (0.5, 1.0, 1.5)}}
    # ความจุคูระบายน้ำขนานคัน (กว้าง 3 ม. ลึก 1 ม.) — ประมาณด้วยสูตรแมนนิ่ง ลาดผันแปร (สมมติฐาน)
    ld = pf["lateral_ditch"]
    ditch = {}
    for s in (1e-4, 3e-4, 1e-3):
        A = ld["width_m"] * ld["depth_m"]
        P = ld["width_m"] + 2 * ld["depth_m"]
        ditch[f"{s:.0e}"] = round((1 / 0.03) * A * (A / P) ** (2 / 3) * s ** 0.5, 1)
    fb = c["flood_band"]["scenes"]["S1D_20261002_0609"]
    return {
        "note": "ค่าประมาณจากรูปตัดตามยาวและตัวเลขในรายงานผลกระทบสิ่งแวดล้อม ไม่ใช่แบบจำลองน้ำท่วม · ใช้ความสูงคันตามเอกสารเท่านั้น — ตัวเลข \"ราว 6 ม.\" ที่มีผู้อ้างไม่พบที่มา",
        "assumptions": {"freeboard_m": FB, "z_inner": z1, "z_outer": z2, "crest_road_m": road, "weir_c": 1.7, "reach_between_gates_km": [23, 74],
                        "ditch_n": 0.03, "ditch_slopes": ["1:10,000", "1:3,000", "1:1,000"],
                        "flood_area_km2": round((fb["west_rai"] + fb["east_rai"]) / 625.0, 1),
                        "flood_area_src": "พื้นที่น้ำท่วมจริง 2 ต.ค. 2569 ภายใน 10 กม. สองฝั่งช่วงนครนายก (ดาวเทียม)"},
        "capacity": caps, "cases": cases, "barrier": barrier, "ditch_q_each_side_m3s": ditch,
        "routes": {"connecting_canal": pf["connecting_canal"], "upland": pf["upland_basins"], "ditch": ld},
    }



# ---- ข้อเท็จจริงจาก OCR/ชั้นข้อความของ EIA 2569 (16 ต.ค. 69) — ตรวจภาพหน้าหรือชั้นข้อความแล้ว (ดู data/32_goal7_chaophraya2/ocr_manifest.md) ----
OCR_S26 = {"annual_min_mcm": 453, "annual_mean_mcm": 2720, "annual_max_mcm": 6741, "augnov_mean_mcm": 1988, "augnov_min_mcm": 134,
           "years": "2528–2566", "full_flow_mcm_per_day": round(600 * 86400 / 1e6, 2),
           "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 ตาราง 2.5.3-2 (หน้า 2-92 · หน้าไฟล์ 197): ปริมาณน้ำท่ารายเดือนสถานี S.26 ท้ายเขื่อนพระรามหก"}
OCR_FACTS = [
    {"id": "mussel_notice_30d", "tier": "A", "check": "ภาพหน้า",
     "fact": "ก่อนเปิดประตูปลายคลองระบายน้ำ ต้องแจ้งผู้เพาะเลี้ยงสัตว์น้ำล่วงหน้าอย่างน้อย 30 วัน ผ่านป้ายประชาสัมพันธ์ ผู้นำชุมชน และผู้นำกลุ่มเพาะเลี้ยง · วางแผนเปิดช่วง ก.ย.–ต.ค. ให้ใช้เวลาสั้นที่สุด",
     "src": "หนังสือมาตรการแนบท้าย (ก.พ. 2569) หน้า 34–35 จาก 54"},
    {"id": "diversion_1_2_months", "tier": "A", "check": "ภาพหน้า",
     "fact": "ผันน้ำจากแม่น้ำป่าสักเฉพาะช่วงฝนตกหนักที่มีน้ำหลาก ประมาณ 1–2 เดือน", "src": "หนังสือมาตรการแนบท้าย หน้า 19 จาก 54"},
    {"id": "gate_committee", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "กรมชลประทานจะตั้งคณะกรรมการบริหารจัดการคลองผันน้ำหลาก เป็นผู้กำหนดนโยบายใช้น้ำที่เก็บกักในคลอง และมีอำนาจเปิด–ปิดประตูระบายน้ำ",
     "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 ภาคผนวก เล่ม 2 หน้าไฟล์ 223 และ 251 (ตอบข้อซักถามประชาพิจารณ์) · หนังสือมาตรการ หน้า 34"},
    {"id": "scada_master", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "ห้องควบคุมกลางระบบควบคุมระยะไกลและโทรมาตรอยู่ที่สำนักงานเขื่อนทดน้ำป่าสัก · สถานีสนามที่ประตูระบายน้ำ/สถานีสูบ วัดระดับน้ำเหนือ–ท้ายน้ำ ฝน ระยะเปิดบาน และสั่งเปิด–ปิดทางไกลผ่านชุดควบคุมอัตโนมัติ · งบ 723 ล้านบาท",
     "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้า 2-84 ถึง 2-87 (หน้าไฟล์ 189–191)"},
    {"id": "s26_diversion_window", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "ปริมาณผันพิจารณาจากน้ำท่าท้ายเขื่อนพระรามหก (S.26) ผันได้ทุกปีช่วง ส.ค.–พ.ย. สูงสุด 600 ลบ.ม./วินาที · น้ำท่ารายปี 2528–2566 ต่ำสุด 453 / เฉลี่ย 2,720 / สูงสุด 6,741 ล้าน ลบ.ม. · ส.ค.–พ.ย. เฉลี่ย 1,988",
     "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้า 2-91 ถึง 2-92 (หน้าไฟล์ 196–197)"},
    {"id": "chainat_pasak_rule", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "คลองชัยนาท–ป่าสัก: ผันเมื่อระดับหน้าเขื่อนเจ้าพระยาสูงกว่า +17.00 ม.รทก. (เก็บกัก +16.00) · ที่ ปตร.มโนรมย์ +18.50 ระบายราว 930 ลบ.ม./วินาที · ควบคุมประตูปากคลองรับไม่เกิน 650 ให้น้ำลึกไม่เกิน 7.0 ม. · เปิดอาคารรับน้ำป่าด้านข้างให้ระบายก่อน แล้วจึงรับน้ำเต็มที่ · ลึกได้ไม่เกิน 8.0 ม. ถ้าน้ำด้านข้างมาก · ใช้ได้เต็มที่เมื่อหน้าเขื่อนทดน้ำป่าสักไม่เกิน +10.00",
     "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้า 2-88 ถึง 2-91 (หน้าไฟล์ 193–196)"},
    {"id": "close_gates_store", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "สิ้นฤดูฝนปิดประตู 5 แห่ง (ปากคลอง กลางคลอง 3 แห่ง ปลายคลอง) เก็บน้ำช่วง ก.ย.–ต.ค. ใช้เสริมพื้นที่ชลประทาน 6 โครงการ (รวมนครนายก) ราว 16,000 ไร่ ภายใน 500 ม. สองฝั่ง · ไม่มีระบบส่งน้ำจากคลอง ต้องสูบลงระบบส่งน้ำเดิม",
     "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้า 2-97 (หน้าไฟล์ 202)"},
    {"id": "tide_model_fig", "tier": "A", "check": "ภาพหน้า (อ่านจากรูป ±0.2 ม.)",
     "fact": "รูปที่ 2.5.1-4: ระดับน้ำสูงสุดตามคลองขณะทะเลขึ้นสูงสุดกับลงต่ำสุดแยกจากกันตั้งแต่ราว กม.75 ลงไป — ปลายคลอง ≈ +2.5 กับ ≈ 0.0 ม.รทก. · ระยะน้ำเท้อ ≈ 60 กม. · ระบายออกอ่าวไทย 121.27–853.05 เฉลี่ย 591.90 ลบ.ม./วินาที",
     "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้า 2-80 ถึง 2-82 (หน้าไฟล์ 185–187)"},
    {"id": "tourism_measure", "tier": "A", "check": "ภาพหน้า",
     "fact": "ปีสุดท้ายของการก่อสร้างให้ฟื้นฟูภูมิทัศน์ปลายคลองและส่งเสริมการท่องเที่ยวตามศักยภาพพื้นที่ (ไม่ได้กำหนดกิจกรรมทางน้ำ)", "src": "หนังสือมาตรการแนบท้าย หน้า 53 จาก 54"},
    {"id": "boreholes_for_fill", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "เจาะสำรวจเพิ่มเติมเพื่อหาวัสดุถมคัน 2 หลุม ลึกรวม 33.9 ม. · แผนสำรวจเพิ่ม 139 แปลง 5,212.5 ไร่ (มือเจาะ ≥35 หลุม · บ่อสำรวจ ≥5 · เจาะตอก ≥3 ต่อแปลง) — ไม่ใช่การเจาะสำรวจรอยเลื่อน 5 หลุมที่ คชก. ขอ",
     "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 หน้าไฟล์ 246–248"},
    {"id": "fault_construction_measure", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "คชก. กำหนดให้การเจาะสำรวจดินอย่างน้อย 5 หลุมตามแนวคลองที่พาดผ่านรอยเลื่อนองครักษ์ถึงชั้นดินแข็ง เป็น \"มาตรการในระยะก่อสร้าง\" (ก่อนเริ่มขุดจริง) และให้ตัดคำว่า \"เป็นรอยเลื่อนไม่มีพลัง\" ออกเนื่องจากยังไม่มีการศึกษาในรายละเอียด ปรับระดับเป็นมีความเสี่ยงน้อย/มีผลกระทบ และปฏิบัติตามกฎกระทรวงแผ่นดินไหว พ.ศ. 2550",
     "src": "หนังสือ สผ. ที่ ทส 1010.6/2233 (18 ก.พ. 2562) ข้อ 5.4.1–5.4.3 และ 5.5 หน้า 4"},
    {"id": "construction_duration_3y_rejected", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "คชก. ชี้ว่าระยะเวลาก่อสร้าง 3 ปีที่ระบุเดิมไม่มีความสมเหตุสมผลกับขนาดและความซับซ้อนของโครงการ ส่งผลให้การวิเคราะห์เศรษฐศาสตร์คลาดเคลื่อนและได้ผลตอบแทนสูงเกินจริง",
     "src": "หนังสือ สผ. ที่ ทส 1010.6/2233 (18 ก.พ. 2562) ข้อ 1.12 หน้า 3"},
    {"id": "canal_dry_vs_ecology_conflict", "tier": "A", "check": "ชั้นข้อความ",
     "fact": "คชก. ตั้งข้อสังเกตความขัดแย้งเชิงนโยบาย: หน้า 3-223 ระบุออกแบบให้คลองแห้งได้ แต่งานส่วนอื่นระบุจะรักษาน้ำไว้เพื่อรักษาระบบนิเวศ",
     "src": "หนังสือ สผ. ที่ ทส 1010.6/2233 (18 ก.พ. 2562) ข้อ 1.16 หน้า 3"},
    {"id": "compensation_total", "tier": "A", "check": "ภาพหน้า",
     "fact": "ค่าชดเชยรวม 21,794,378,164 บาท: ที่ดิน 19,677,064,471 · สิ่งปลูกสร้าง 1,378 หลัง 1,994,012,623 · ไม้ยืนต้น 1,303 ไร่ 123,301,070 · ตั้งคณะกรรมการกำหนดราคาที่มีตัวแทนประชาชนระดับตำบล",
     "src": "หนังสือมาตรการแนบท้าย หน้า 45 จาก 54"},
]



# ---- ดินเปรี้ยว/ดินกรดกำมะถัน ตามแนวคลอง (16 ต.ค. 69) — ข้อมูลจากรายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 §3.1.3 (กรมพัฒนาที่ดิน 2562 · สำรวจดิน 26–27 พ.ค. 2559) ----
ACID_SRC = "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 บทที่ 3 §3.1.3 ตาราง 3.1.3-3, 3.1.3-5, 3.1.3-7 (หน้าไฟล์ 217–231) · รูปที่ 3.1.3-3 (หน้าไฟล์ 225)"
ACID_AREAS = {   # พื้นที่ชุดดินในแนวคลอง (ไร่) ตารางที่ 3.1.3-5
    "km0_23": {"total": 2140, "Tr": 2140},
    "km23_110": {"total": 10130, "Ok": 1768, "Rs": 2848, "Bp": 2171, "Bk": 882, "Cc": 1724, "Ma": 454, "Tr": 282},
    "km110_135": {"total": 2694, "Bp": 1302, "Bk": 753, "Sm": 377, "Bpg": 263},
}
ACID_SERIES = {
    "Ok": {"name": "ชุดดินองครักษ์", "ph": "4.0–4.5 ทั้งหน้าตัด (ชั้นบนราว 4.0 ภายใน 50 ซม.)",
           "note": "ดินเลนเหนียวทะเลชั้นล่าง · น้ำท่วมขังลึก 1 ม. นาน 6–7 เดือน · เหล็ก/อะลูมิเนียมละลายออกมากจนเป็นพิษต่อพืช · \"ไม่เหมาะต่อการเกษตรทุกประเภท\""},
    "Rs": {"name": "ชุดดินรังสิต", "ph": "4.0–5.0 (ต่ำกว่า 4.0 ที่ลึก 100–150 ซม.)",
           "note": "พบจุดจาโรไซต์ (ตัวชี้ดินกรดกำมะถัน) ที่ 50–100 ซม. · ต่ำลงไปเป็นดินเลน \"ดินเปรี้ยวจัด\" · เหมาะปานกลางสำหรับปลูกข้าว"},
    "Bp": {"name": "ชุดดินบางน้ำเปรี้ยว", "ph": "6.0–6.5 ชั้นบน · \"ดินเป็นกรดจัด\" ตามคำบรรยาย",
           "note": "พบดินเลนสีเทาปนเขียวที่ราว 150 ซม. ลงไป · อาจพบจุดเหลืองฟางข้าว · เหมาะปานกลางสำหรับปลูกข้าว"},
}
ACID_FIELD_PH = [   # ตาราง 3.1.3-7: (สถานี, ชั้นบน, ชั้นล่าง)
    ("วัดม่วงหวาน", 5.97, 5.57), ("อบต.หนองหมู (วิหารแดง)", 3.98, 3.93), ("ร.ร.บ้านช่องตะเคียน", 5.44, 4.59),
    ("ทุ่งนา ต.ดอนฉิมพลี (บางน้ำเปรี้ยว)", 3.72, 3.64), ("ที่ดินข้างคลองกระแซงเตย", 5.93, 4.01)]
ACID_OK_KM_MAP = [[32, 40], [44, 50]]   # อ่านจากรูปที่ 3.1.3-3 สีส้ม "ไม่เหมาะสมสำหรับพืชเศรษฐกิจ" (±2 กม.)


def acid_soil(c):
    """ดินเปรี้ยวกับการขุดลึก — คัดกรองลำดับขนาด: ปริมาตรดินขุดที่อยู่ในชุดดินกรด และปูนที่ต้องใช้ (ตามสมมติฐานกำมะถัน)"""
    dc = c["new_cases"]["deep_cut"]
    a1, a2 = ACID_AREAS["km23_110"], ACID_AREAS["km110_135"]
    acid1 = a1["Ok"] + a1["Rs"] + a1["Bp"]
    acid2 = a2["Bp"]
    f1, f2 = acid1 / a1["total"], acid2 / a2["total"]
    tot = sum(ACID_AREAS[k]["total"] for k in ACID_AREAS)
    acid_tot = acid1 + acid2
    L1, L2 = 87.0, 24.0          # กม.23–110 และ กม.110–134
    cut_deep, cut_now = dc["area_m2"], dc["area_now_below_ground_m2"]
    vol = {"design": round((L1 * f1 + L2 * f2) * cut_now / 1000, 1), "deep": round((L1 * f1 + L2 * f2) * cut_deep / 1000, 1)}
    rho, caco3_kg_per_t_per_pct, safety = 1.4, 31.25, 1.5
    lime = {}
    for case, v in vol.items():
        mt = v * 1e6 * rho / 1e6          # ล้านตันดิน
        lime[case] = {str(sp): round(mt * sp * caco3_kg_per_t_per_pct / 1000 * safety, 2) for sp in (0.2, 0.5, 1.0)}
    price = (1000, 1500)
    return {
        "src": ACID_SRC, "areas": ACID_AREAS, "series": ACID_SERIES, "field_ph": ACID_FIELD_PH, "ok_km_map": ACID_OK_KM_MAP,
        "acid_share_km23_110": round(f1 * 100, 1), "acid_share_km110_135": round(f2 * 100, 1), "acid_share_all": round(acid_tot / tot * 100, 1),
        "acid_rai_all": acid_tot, "soil_rai_all": tot,
        "ok_500m_rai": 4019 + 4303, "ok_rai_canal": a1["Ok"],
        "excavation_acid_mcm": vol, "cut_area_m2": {"design": cut_now, "deep": cut_deep},
        "lime_mt": lime, "lime_price_baht_per_t": list(price),
        "lime_cost_mb": {k: [round(v["0.5"] * price[0]), round(v["0.5"] * price[1])] for k, v in lime.items()},
        "assumptions": {"bulk_density_t_m3": rho, "caco3_kg_per_t_per_pct_s": caco3_kg_per_t_per_pct, "safety": safety,
                        "sulfur_pct_scenarios": [0.2, 0.5, 1.0],
                        "note": "รายงานผลกระทบสิ่งแวดล้อมวัดเฉพาะความเป็นกรด-ด่างชั้นตื้น ไม่มีปริมาณกำมะถัน/ศักย์กรด — ค่ากำมะถันเป็นสมมติฐานเพื่อดูลำดับขนาด · ถือว่าดินที่ขุดทั้งหมดในชุดดินกรดเป็นดินที่มีกำมะถัน (ขอบบน)"},
        "water_ph_2555": [6.96, 7.95], "water_ph_src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 ตาราง 3.1.7-4 (ผลปี 2555) หน้าไฟล์ 265",
    }



CONCERN_SHORT = {
 "1": "ตรวจได้ส่วนหนึ่ง — ตัวเลขต่างกันจริงตามเวอร์ชันของเอกสาร (ดูตารางเวอร์ชัน)",
 "2": "พบเปรียบเทียบเฉพาะแนวคลอง 3 ทางเลือก · ไม่พบเทียบกับแก้มลิง/ฟื้นฟูทางน้ำเดิม",
 "3": "ไม่พบหัวข้อผลกระทบสะสม (พบเพียงข้อเสนอของผู้แทน สผ. ในประชาพิจารณ์)",
 "4": "จัดเป็นโครงการผันน้ำข้ามลุ่ม · ไม่พบการประเมินผลท้ายน้ำเจ้าพระยา",
 "5": "มีแบบจำลองระบาย ตะกอน ชายฝั่ง ความเค็ม · สัตว์น้ำวัยอ่อนเป็นเชิงคุณภาพ",
 "6": "ไม่พบแบบจำลองน้ำท่วมด้านข้าง · มีเพียงหลักการไม่ให้กีดขวางทางน้ำ",
 "7": "ตัวเลขผู้ถือครอง 2,600 ราย ที่ดิน 16,288 ไร่ · 1,563 หลังของผู้ยื่นต่างจาก 1,378 หลังของรายงาน",
 "8": "มีเวทีในองครักษ์ปี 2559–2560 และ 6 เวทีปี 2566 (ที่ว่าการอำเภอองครักษ์) แต่เวทีสาธารณะปี 2559–2560 อยู่นอกจังหวัด · อำเภอบ้านนามีเพียง ต.บ้านพริก 1 ตำบลร่วมเวทีที่อำเภอหนองเสือ (ปี 2566) · ร้อยละ 55 ของผู้ถูกเวนคืนที่สำรวจยังไม่ทราบโครงการ",
 "9": "ตรงกับรายงาน: ไม่คุ้มค่าที่คิดลด 12%",
 "10": "มีบทประเมินสุขภาพราว 83 หน้า อ้างแนวทางฉบับปรับปรุง พ.ค. 2565",
 "11": "ไม่พบแผนรับน้ำเกินการออกแบบ/คันพัง (พบเฉพาะแผนอุบัติเหตุคนงาน)",
 "12": "ชดเชยที่ดิน อาคาร พืชผล ค่าเสียโอกาส · ผู้เช่าที่ดินมีข้อเสนอในประชาพิจารณ์",
 "13": "ตารางคุณภาพน้ำบางส่วนปี 2555 · สำรวจที่ดิน/ครัวเรือนปี 2566–2567"
}
NN_WATER_USERS = {
 "date": "24 ก.พ. 2566",
 "place": "หอประชุมที่ว่าการอำเภอองครักษ์",
 "n_reps": 11,
 "pairs": [
  [
   "คุณภาพน้ำของเกษตรกรริมน้ำ (น้ำเน่าเสีย น้ำขุ่น) ทั้งช่วงก่อสร้างและดำเนินการ",
   "ก่อสร้างคันดิน คูระบายน้ำ และบ่อดักตะกอนในพื้นที่กองวัสดุใกล้แหล่งน้ำ (มาตรการนิเวศวิทยาทางน้ำ ข้อ 2.1)"
  ],
  [
   "คลองตัดผ่านพื้นที่เกษตร ทำให้เข้าถึงระบบชลประทาน แหล่งน้ำเดิม และเส้นทางสัญจรเดิมไม่ได้",
   "ทางเบี่ยงน้ำของคลองส่งน้ำ · เชื่อมต่อคลองเดิมหรือลำรางเลียบแนว · สร้างสะพานรถยนต์ สะพานรถไฟ และประตูเรือทดแทนเส้นทางสัญจรเดิม (ข้อ 3.1, 3.7)"
  ],
  [
   "การระบายน้ำของพื้นที่ที่เป็นแอ่งต่ำ",
   "ก่อสร้างช่วงฤดูแล้ง · สร้างประตูทีละครึ่งลำน้ำ · ควบคุมเศษวัสดุไม่ให้ตกลำน้ำ (ข้อ 3.3)"
  ]
 ],
 "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 2 บทที่ 9 ตาราง 9.5.10-1 ถึง 9.5.10-3 (หน้าไฟล์ 445–450) — ไม่ระบุชื่อผู้เข้าร่วม"
}


# ---- เวทีประชุมทำความเข้าใจโครงการปี 2566 ที่เกี่ยวกับนครนายก (ตาราง 9.5.7-4 และ 9.5.7-6 · เล่ม 2 หน้าไฟล์ 362–368) ----
NN_TOPICS = ["ออกแบบ/รูปแบบคลอง", "การบริหารจัดการน้ำ", "การบริหารจัดการโครงการ", "ทรัพยากรธรรมชาติ", "ฝุ่น เสียง แรงสั่นสะเทือน", "วิถีชีวิตและชุมชน",
             "อาชีพ", "มาตรการดูแลเจ้าของที่ดิน", "มาตรการดูแลผู้เช่า", "เกณฑ์ค่าชดเชยที่ดิน", "การสื่อสารและประชาสัมพันธ์"]
NN_VENUES_2566 = [   # (เวที, วัน-เวลา, พื้นที่, สถานที่, ประเด็นที่ติ๊ก = ลำดับใน NN_TOPICS ที่นับจาก 1)
    (9, "16 ก.พ. 2566 เช้า", "ต.ศรีษะกระบือ · ต.ดอนฉิมพลี (อ.องครักษ์)", "หอประชุมที่ว่าการอำเภอบางน้ำเปรี้ยว จ.ฉะเชิงเทรา", [1, 7, 10, 11]),
    (14, "22 ก.พ. 2566 บ่าย", "ต.บางปลากด", "หอประชุมที่ว่าการอำเภอองครักษ์", [3, 8, 10]),
    (15, "23 ก.พ. 2566 เช้า", "ต.บางปลากด · ต.คลองใหญ่", "หอประชุมที่ว่าการอำเภอองครักษ์", [5, 8, 9, 10]),
    (16, "23 ก.พ. 2566 บ่าย", "ต.คลองใหญ่ · ต.องครักษ์", "หอประชุมที่ว่าการอำเภอองครักษ์", [5, 10]),
    (17, "24 ก.พ. 2566 เช้า", "ต.พระอาจารย์ (รอบ 1)", "หอประชุมที่ว่าการอำเภอองครักษ์", [1, 2, 5, 6, 11]),
    (18, "24 ก.พ. 2566 บ่าย", "ต.พระอาจารย์ (รอบ 2)", "หอประชุมที่ว่าการอำเภอองครักษ์", [1, 8, 10]),
    (19, "27 ก.พ. 2566 เช้า", "ต.พระอาจารย์ (รอบ 3)", "หอประชุมที่ว่าการอำเภอองครักษ์", [1, 10]),
    (30, "10 มี.ค. 2566 บ่าย", "ต.ศาลาครุ (หนองเสือ) · ต.บ้านพริก (บ้านนา) · ต.โพธิ์แทน (องครักษ์)", "หอประชุมอำเภอหนองเสือ จ.ปทุมธานี", [1, 5, 8, 10]),
    (32, "15 มี.ค. 2566 เช้า", "เฉพาะหน่วยงานจังหวัดฉะเชิงเทรา นครนายก สมุทรปราการ", "โรงแรมในอำเภอเมืองสมุทรปราการ", [1, 2, 6, 10]),
]
NN_VENUES_ALL_TOTAL = [21, 9, 5, 2, 22, 11, 10, 19, 2, 25, 6]   # แถว "รวม" ของตาราง 9.5.7-6 (32 เวที)
NN_VENUES_SRC = "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 2 บทที่ 9 ตาราง 9.5.7-4 และ 9.5.7-6 (หน้าไฟล์ 362–368) · ตาราง 9.5.7-6 ติ๊กเฉพาะประเด็นที่เวทีนั้นให้ความสำคัญ ไม่มีบันทึกรายคนรายเวทีในตาราง"


def nn_venues(c):
    rows, cnt = [], [0] * len(NN_TOPICS)
    for v, when, area, place, tk in NN_VENUES_2566:
        rows.append({"venue": v, "when": when, "area": area, "place": place, "topics": [NN_TOPICS[i - 1] for i in tk]})
        for i in tk:
            cnt[i - 1] += 1
    return {"rows": rows, "n_venues": len(rows), "topic_counts": dict(zip(NN_TOPICS, cnt)), "all_total": dict(zip(NN_TOPICS, NN_VENUES_ALL_TOTAL)), "src": NN_VENUES_SRC,
            "banna_note": "อำเภอบ้านนามีเพียงตำบลบ้านพริก 1 ตำบล ในเวทีที่ 30 ซึ่งจัดที่อำเภอหนองเสือ จ.ปทุมธานี — ไม่มีเวทีในอำเภอบ้านนาเอง"}


# ---- ศูนย์วิจัยนิวเคลียร์องครักษ์ (สทน.) กับคลอง: ระยะ น้ำท่วม ระดับ (พิกัดหมุด สทน. 14.1221 N, 101.0275 E ห่างคลอง 5.78 กม. ตรงกับ กม.57) ----
NUC_WEB = {
    "address": "9/9 หมู่ 7 ต.ทรายมูล อ.องครักษ์ จ.นครนายก (เว็บ สทน.)",
    "waste_site": "สำนักงานใหญ่องครักษ์เป็น 1 ใน 3 พื้นที่เก็บกากกัมมันตรังสีที่จัดการแล้ว (อีก 2 แห่ง บางเขน และเทคโนธานี) ตามรายงานตรวจรังสีสิ่งแวดล้อมปี 2562 ของ สทน.",
    "reactor": "โครงการเตาปฏิกรณ์วิจัย 20 เมกะวัตต์ที่องครักษ์ (แผนปี 2549) ถูกพักไว้แล้วโอนทรัพย์สินให้ สทน. · มีข่าวฟื้นแผนและการคัดค้านในพื้นที่ (2563–2566) ตามสื่อ",
    "src": "ค้นเว็บ 16 ต.ค. 2569: เว็บ สทน. · รายงานตรวจรังสีสิ่งแวดล้อมปี 2562 · สื่อ (มติชน · ไทยรัฐ · บางกอกโพสต์) · พิกัดหมุดจากผู้ใช้ (ตารางพิกัดหมุด) — ข้อมูลศูนย์/กากยังไม่ได้ตรวจกับเอกสารทางการของ สทน.",
}



NUC_POINT = {"lon": 101.0274776, "lat": 14.1220685,
             "src": "พิกัดหมุดสถาบันเทคโนโลยีนิวเคลียร์แห่งชาติ (องค์การมหาชน) บนแผนที่ออนไลน์ที่ผู้ใช้ให้มา 16 ต.ค. 2569 — เป็นหมุดของสถาบัน ไม่ใช่ขอบเขตรั้วหรือที่ตั้งอาคารเก็บกาก"}


def nuclear_point():
    """ระยะ/ฝั่ง/กม./ความสูง/น้ำท่วมดาวเทียม ณ หมุดศูนย์ (ใช้ shapely + shapefile น้ำท่วม GISTDA)"""
    lon, lat = NUC_POINT["lon"], NUC_POINT["lat"]
    KX, KY = 111.32 * math.cos(math.radians(lat)), 110.57
    cl = json.loads((D7 / "centerline.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"]
    pts = [((p[0] - lon) * KX, (p[1] - lat) * KY) for p in cl]

    def seg(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0, min(1, ((0 - a[0]) * dx + (0 - a[1]) * dy) / (dx * dx + dy * dy or 1)))
        q = (a[0] + t * dx, a[1] + t * dy)
        return math.hypot(*q), q
    d, q = min(seg(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    mk = sorted((m["properties"]["km"], m["geometry"]["coordinates"]) for m in json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"])
    qlon, qlat = q[0] / KX + lon, q[1] / KY + lat
    km = min(mk, key=lambda k: (k[1][0] - qlon) ** 2 + (k[1][1] - qlat) ** 2)[0]
    with rasterio.open(ROOT / "data/08_dem_topography/raw/Copernicus_DSM_COG_10_N14_00_E101_00_DEM.tif") as ds:
        vals = [float(next(ds.sample([(lon + dx, lat + dy)]))[0]) for dx in (-0.0006, 0, 0.0006) for dy in (-0.0006, 0, 0.0006)]
    pt = Point(lon, lat)
    passes = []
    for p in sorted(glob.glob(str(ROOT / "data/manual/shp_*"))):
        n = os.path.basename(p)[4:]
        r = shapefile.Reader(f"{p}/{n}.shp", encoding="latin-1")
        inside, best = False, 1e12
        for sh in r.shapes():
            g = shape(sh.__geo_interface__)
            if not g.is_valid:
                g = g.buffer(0)
            if g.contains(pt):
                inside = True
            best = min(best, g.distance(pt) * 111000.0)
        passes.append({"pass": n, "inside": inside, "nearest_flood_m": None if inside else round(best)})
    b, w, cr = _profile_levels(km)
    g0 = _ground(km)
    return {**NUC_POINT, "dist_to_canal_km": round(d, 2), "side": "ตะวันออก" if q[0] < 0 else "ตะวันตก", "canal_km": float(km),
            "dsm_m": {"median": round(float(np.median(vals)), 1), "min": round(min(vals), 1), "max": round(max(vals), 1)},
            "flood_passes": passes, "canal_at_km": {"ground_m": round(g0, 2), "water_msl_m": round(w, 2), "crest_msl_m": round(cr, 2)}}


def nuclear_site(c):
    import csv
    LAT0 = 14.0
    KX, KY = 111.32 * math.cos(math.radians(14.1)), 110.57
    cl = json.loads((D7 / "centerline.geojson").read_text(encoding="utf-8"))
    f = cl["features"][0] if "features" in cl else cl
    pts = [((p[0] - 100.9) * KX, (p[1] - LAT0) * KY) for p in f["geometry"]["coordinates"]]
    mk = sorted(((m["properties"]["km"], m["geometry"]["coordinates"]) for m in json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]))

    def seg(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy or 1)))
        q = (a[0] + t * dx, a[1] + t * dy)
        return math.hypot(p[0] - q[0], p[1] - q[1]), q

    rows = []
    for r in csv.DictReader(open(ROOT / "analysis/villages_warning_zones.csv", encoding="utf-8-sig")):
        if r["ตำบล"] != "ทรายมูล" or r["อำเภอ"] != "องครักษ์":
            continue
        p = ((float(r["lon"]) - 100.9) * KX, (float(r["lat"]) - LAT0) * KY)
        d, q = min(seg(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        qlon, qlat = q[0] / KX + 100.9, q[1] / KY + LAT0
        km = min(mk, key=lambda k: (k[1][0] - qlon) ** 2 + (k[1][1] - qlat) ** 2)[0]
        dem = float(r["DEM_มรทก"]) if r["DEM_มรทก"] not in ("", "nan") else None
        rows.append({"village": r["หมู่บ้าน"], "dist_km": round(d, 1), "side": "ตะวันออก" if p[0] > q[0] else "ตะวันตก", "canal_km": float(km), "dem_m": round(dem, 1) if dem is not None else None})
    rows.sort(key=lambda x: x["dist_km"])
    flood = None
    for r in csv.DictReader(open(ROOT / "analysis/gistda_flood_series_by_pass.csv", encoding="utf-8-sig")):
        if r["tambon"] == "ต.ทรายมูล" and r["amphoe"] == "อ.องครักษ์":
            flood = {"pass": r["pass"], "rai": float(r["flood_rai"]), "km2": float(r["flood_km2"])}
    kms = sorted({x["canal_km"] for x in rows})
    k0, k1 = kms[0], kms[-1]
    b, w, cr = _profile_levels(52.0)   # ระดับน้ำออกแบบ/สันคันที่ กม.~52 (ตัวแทนช่วงนี้)
    g = _ground(52.0)
    return {"web": NUC_WEB, "point": nuclear_point(), "villages": rows, "dist_min_km": rows[0]["dist_km"], "dist_max_km": rows[-1]["dist_km"],
            "all_east": all(x["side"] == "ตะวันออก" for x in rows), "canal_km_range": [k0, k1],
            "flood_2569": flood, "dem_range_m": [min(x["dem_m"] for x in rows if x["dem_m"] is not None and x["dem_m"] < 6),
                                                max(x["dem_m"] for x in rows if x["dem_m"] is not None and x["dem_m"] < 6)],
            "canal_at_km52": {"ground_m": round(g, 2), "water_msl_m": round(w, 2), "crest_msl_m": round(cr, 2), "water_above_ground_m": round(w - g, 1)},
            "eia_hits": 0, "eia_pages_scanned": 2467}


# ---- เจ้าพระยา2 กับลุ่มบางปะกง ----
def bpk_role(c):
    b = json.loads((ROOT / "analysis/goal7/basin_containment.json").read_text(encoding="utf-8"))
    km = {x["basin"]: x["km"] for x in b["basins"]}
    B = c["basins_2569"]
    return {"basin_km": km, "line_len_km": b["line_len_km"], "bpk_share_pct": round(km["บางปะกง"] / b["line_len_km"] * 100),
            "below_capacity_ids": B["below_capacity_ids"], "n_sub": len(B["rows"]),
            "event": c["extra_q"]["event2569"]["note"],
            "eia_role_statement": "โครงการจะมีบทบาทสำคัญในการตัดยอดมวลน้ำไม่ให้ไหลบ่าลงมาในพื้นที่ แต่ไม่มีบทบาทในการระบายน้ำในพื้นที่จังหวัดที่อยู่ตอนล่างของคลองระบายน้ำหลาก — ประโยชน์ต่อพื้นที่คือช่วยลดภาระการระบายน้ำของคลองเดิม",
            "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 2 ตาราง 9.5.7-7 ข้อ 1.2 (6) หน้าไฟล์ 370 (ถามตอบจากประชุมทำความเข้าใจ 32 เวที)"}


# ---- สนามกอล์ฟสองฝั่งคลอง (คัดกรองเชิงพื้นที่) ----
def golf_case(c):
    L = c["corridor_area"]["length_km"]
    nn_len = c["structures"]["nakhonnayok"]["length_km"]
    out = {"course_rai": [400, 600], "strip_m": 200, "assumption": "สนามกอล์ฟ 18 หลุมมาตรฐานใช้ที่ราว 400–600 ไร่ (สมมติฐานผู้จัดทำ ไม่ใช่ข้อมูลโครงการ) · แถบพัฒนาข้างละ 200 ม. ตามถามพัฒนาสองฝั่ง"}
    for lab, ln in (("all", L), ("nn", nn_len)):
        rai = ln * 1000 * 200 * 2 / 1600.0
        out[lab] = {"length_km": round(ln, 1), "strip_rai": round(rai), "courses": [round(rai / 600, 1), round(rai / 400, 1)]}
    out["frontage_km_per_course"] = [round(400 * 1600 / 200 / 1000, 1), round(600 * 1600 / 200 / 1000, 1)]
    return out


def _ground(km):
    g = PROFILE_FIG["ground"]
    return float(np.interp(km, [x[0] for x in g], [x[1] for x in g]))


def new_cases(c):
    """กรณีเพิ่ม 16 ต.ค. 69: (1) น้ำเท้อ/น้ำทะเลหนุน (2) ขุดลึกลดคัน + พัฒนาสองฝั่ง (3) ท่องเที่ยว (4) ไฟฟ้าจากน้ำไหล
    คัดกรองลำดับขนาดจากหน้าตัดตามรายงาน — สมมติฐานทุกข้อระบุใน assumptions · ไม่ใช่แบบออกแบบ"""
    sec = c["eia_section"]
    z, D, n, Q = sec["z1"], sec["D_m"], sec["n"], 600.0
    b = sec["A_m2"] / D - z * D
    S0 = 0.04 / 1000.0
    KM0, KM1 = 23.0, 134.0
    g = 9.81

    def geo(y):
        A = (b + z * y) * y
        P = b + 2 * y * math.sqrt(1 + z * z)
        return A, P, b + 2 * z * y

    def sf(y, q):
        A, P, _ = geo(y)
        return (q * n / (A * (A / P) ** (2 / 3))) ** 2

    def dydx(y, q):
        A, _, T = geo(y)
        fr2 = q * q * T / (g * A ** 3)
        return (S0 - sf(y, q)) / (1 - fr2)

    def normal(q):
        return brentq(lambda y: (1 / n) * geo(y)[0] * (geo(y)[0] / geo(y)[1]) ** (2 / 3) * math.sqrt(S0) - q, 0.05, 40)

    bed_end = _profile_levels(KM1)[0]

    def backwater(q, stage_end):
        yn = normal(q)
        y = max(stage_end - bed_end, yn)
        out = {134: y}
        dx = 0.05
        for i in range(1, int(round((KM1 - KM0) / dx)) + 1):
            k1 = dydx(y, q)
            k2 = dydx(y - 0.5 * dx * 1000 * k1, q)
            y = max(y - dx * 1000 * k2, yn)
            km = KM1 - i * dx
            if abs(km - round(km)) < 1e-6:
                out[int(round(km))] = y
        return yn, out

    cases = []
    for label, q, st in (("น้ำหลากเต็มกำลัง 600 · ปลายคลองตามแบบ +1.50", 600.0, 1.498),
                         ("น้ำหลากเต็มกำลัง 600 · อัดน้ำหลังประตู +2.50", 600.0, 2.5),
                         ("ผันน้ำน้อย 100 · น้ำทะเลหนุนสูงสุด +2.49", 100.0, 2.49)):
        yn, prof = backwater(q, st)
        surf = {k: round(_profile_levels(k)[0] + v, 2) for k, v in sorted(prof.items())}
        norm = round(yn, 2)
        rise = {k: prof[k] - yn for k in prof}
        reach = [k for k in sorted(rise) if rise[k] > 0.05]
        rise_m = {str(k): round(rise[k], 2) for k in (134, 120, 102, 74, 40)}
        r25 = [k for k in sorted(rise) if rise[k] > 0.25]
        cases.append({"label": label, "q_m3s": q, "stage_end_m": st, "normal_depth_m": norm,
                      "rise_m": rise_m, "length_rise_gt_025_km": (KM1 - min(r25) if r25 else 0.0),
                      "backwater_upto_km": (min(reach) if reach else None),
                      "backwater_length_km": (KM1 - min(reach) if reach else 0.0),
                      "surface_msl": {str(k): v for k, v in surf.items()}})
    w_ws = b + 2 * z * D
    stor = {}
    for a in (74, 102):
        v1 = (134 - a) * 1000 * w_ws * 1.0 / 1e6
        stor[f"km{a}_134"] = {"mcm_per_m_rise": round(v1, 1), "hours_at_600_per_m": round(v1 * 1e6 / Q / 3600, 1)}
    tide = {"design_high_m": 2.0, "behind_gate_m": 2.5, "gate_front_m": 1.5, "y2554_max_m": 2.49, "y2554_min_m": -1.49,
            "backwater_km_eia": 60, "storage": stor, "water_width_m": round(w_ws),
            "swan_waves_m": "0.4–1.2", "gravity_drop_cms": "891 เหลือ 107",
            "corridor_rain_stations": 4593,
            "src": "รายงานผลกระทบสิ่งแวดล้อม ฉบับ 2569 (ระดับน้ำทะเลสูงสุด +2.00 · หน้าประตู +1.50 · อัดน้ำ +2.50 · แบบจำลองคณิตศาสตร์ของรายงาน น้ำทะเล 2554 +2.49/−1.49 · น้ำเท้อ ~60 กม.) · เส้นน้ำเท้อคำนวณเอง ด้วยสมการการไหลไม่สม่ำเสมอแบบแมนนิง ขั้นละ 50 ม.",
            "official_fig": {"end_max_m": 2.5, "end_min_m": 0.0, "converge_km": 75, "level_at_converge_m": 3.3, "read_error_m": 0.2,
                             "points_max": [[23, 5.5], [75, 3.3], [134, 2.5]], "points_min": [[23, 5.35], [75, 3.3], [134, 0.05]],
                             "src": "รายงานผลกระทบสิ่งแวดล้อม 2569 เล่ม 1 รูปที่ 2.5.1-4 (หน้า 2-82) — อ่านจากรูป"},
            "cases": cases}
    g40 = _ground(40)
    S_flat = (g40 - 1.5) / (94 * 1000.0)

    def cap(Dd, S):
        A = (b + z * Dd) * Dd
        P = b + 2 * Dd * math.sqrt(1 + z * z)
        return (1 / n) * A * (A / P) ** (2 / 3) * math.sqrt(S)

    D_deep = brentq(lambda d: cap(d, S_flat) - Q, 2, 60)
    rows, mx, nnmax = [], 0.0, 0.0
    for km in range(38, 135, 2):
        w = g40 - (g40 - 1.5) * (km - 40) / 94 if km >= 40 else g40
        gr = _ground(km)
        crest = (w - gr) + 1.5
        mx = max(mx, crest)
        if 38.6 <= km <= 73.2:
            nnmax = max(nnmax, crest)
        rows.append((km, round(w, 2), round(gr, 2), round(crest, 1)))
    def deep_backwater(stage_end):
        bed_end_d = 1.5 - D_deep
        y = stage_end - bed_end_d
        out = {134: y - D_deep}

        def f(yy):
            A, P, T = geo(yy)
            return (S_flat - (Q * n / (A * (A / P) ** (2 / 3))) ** 2) / (1 - Q * Q * T / (g * A ** 3))
        dx = 0.05
        for i in range(1, int(round(111 / dx)) + 1):
            k1 = f(y)
            k2 = f(y - 0.5 * dx * 1000 * k1)
            y = max(y - dx * 1000 * k2, D_deep)
            km = 134 - i * dx
            if abs(km - round(km)) < 1e-6:
                out[int(round(km))] = y - D_deep
        return out

    dbw = deep_backwater(2.5)
    d_r25 = [k for k in sorted(dbw) if dbw[k] > 0.25]
    A_deep = (b + z * D_deep) * D_deep
    d_now = g40 - _profile_levels(40)[0]
    cut_now = (b + z * d_now) * d_now
    bank_now = 2 * 4.8 * (10 + (z + 2.0) * 4.8 / 2)
    bank_deep = 2 * 1.5 * (10 + (z + 2.0) * 1.5 / 2)
    L = c["corridor_area"]["length_km"]
    extra_cut = (A_deep - cut_now) * (134 - 23) * 1000 / 1e6
    top_w = b + 2 * z * D_deep
    deep = {"water_at_ground_km40_m": round(g40, 2), "slope_1_n": round(1 / S_flat), "depth_m": round(D_deep, 1), "bottom_m": round(b),
            "bed_km40_msl": round(g40 - D_deep, 1), "water_width_m": round(top_w), "area_m2": round(A_deep),
            "area_now_below_ground_m2": round(cut_now), "depth_now_below_ground_m": round(d_now, 1),
            "crest_above_ground_max_m": round(mx, 1), "crest_above_ground_nn_max_m": round(nnmax, 1),
            "bank_fill_now_m2": round(bank_now), "bank_fill_deep_m2": round(bank_deep),
            "extra_spoil_mcm_km23_134": round(extra_cut),
            "unit_cost_baht_per_m3": [60, 150], "extra_cut_cost_mb": [round(extra_cut * 60), round(extra_cut * 150)],
            "tide_rise_m": {str(k): round(dbw[k], 2) for k in (134, 120, 102, 74, 40)},
            "tide_rise_len_gt_025_km": (134 - min(d_r25) if d_r25 else 0.0),
            "storage_mcm_per_m_rise_km74_134": round((134 - 74) * 1000 * top_w / 1e6, 1),
            "rows": rows}
    loan, state = c["civic_funding"]["loan_adb_mb"], c["civic_funding"]["budget_state_mb"]
    dev = []
    for w in (100, 200, 300):
        rai = L * 1000 * w * 2 / 1600.0
        for p in (1.0, 3.0, 5.0):
            dev.append({"strip_m_each_side": w, "rai": round(rai), "net_mb_per_rai": p, "total_mb": round(rai * p),
                        "cover_loan_pct": round(rai * p / loan * 100)})
    be = {str(w): round(loan / (L * 1000 * w * 2 / 1600.0), 1) for w in (100, 200, 300)}
    land = {"scenarios": dev, "breakeven_mb_per_rai_for_loan": be, "loan_mb": loan, "state_mb": state, "length_km": L,
            "nn_comp_mb_per_rai": round(3864.7 / 4266, 2), "sp_comp_mb_per_rai": round(10612.1 / 2594, 2),
            "absorb_rai_per_year_200m_8y": round(L * 1000 * 400 / 1600.0 / 8),
            "breakeven_x_nn_comp": {k: round(v / (3864.7 / 4266), 1) for k, v in be.items()}}
    # ตัวอย่างส่วนผสมการใช้ที่ดินสองฝั่ง (สมมติฐานของผู้จัดทำ ไม่ใช่ข้อมูลตลาด): สัดส่วนพื้นที่ · รายได้สุทธิล้านบาท/ไร่ · เงื่อนไข
    mix_rows = [
        ("สวนสาธารณะ · ทางเดินริมน้ำ · พื้นที่รับน้ำ", 0.30, 0.0, "ต้องเว้นไว้เป็นที่รับน้ำท่วมข้างเคียง/ทางระบายน้ำ ไม่สร้างรายได้ตรง แต่ทำให้ที่ดินรอบ ๆ ขายได้ราคา"),
        ("กีฬาทางน้ำ · ท่าเรือ · ลานกิจกรรม", 0.10, 1.0, "ต้องหยุดได้ทันทีตอนผันน้ำหลาก · ผิวน้ำนิ่งลึกพอเฉพาะช่วงที่มีประตูกั้นระดับ"),
        ("ร้านอาหาร · ตลาดริมน้ำ", 0.10, 3.0, "ต้องการคนผ่านทางมาก จึงเหมาะริมช่วงใกล้ตัวเมือง/ทางหลวง"),
        ("ศูนย์การค้า · พาณิชยกรรม", 0.10, 6.0, "ต้องการประชากรและถนนใหญ่ เหมาะเฉพาะไม่กี่จุด (นครนายก ฉะเชิงเทรา)"),
        ("ที่อยู่อาศัย · หมู่บ้านจัดสรร", 0.40, 3.0, "ต้องถมสูงพ้นน้ำ และคำนึงดินกรดกำมะถันที่ขุดขึ้นมา (ดูคำถามดินเปรี้ยว)"),
    ]
    rai200 = L * 1000 * 200 * 2 / 1600.0
    blend = sum(r[1] * r[2] for r in mix_rows)
    land["mix"] = {"strip_m_each_side": 200, "rai": round(rai200),
                   "rows": [{"use": r[0], "share_pct": round(r[1] * 100), "net_mb_per_rai": r[2], "rai": round(rai200 * r[1]),
                             "total_mb": round(rai200 * r[1] * r[2]), "note": r[3]} for r in mix_rows],
                   "blend_mb_per_rai": round(blend, 2), "total_mb": round(rai200 * blend), "cover_loan_pct": round(rai200 * blend / loan * 100),
                   "retention_rai": round(rai200 * mix_rows[0][1]),
                   "sell_rai_per_year_8y": round(rai200 * (1 - mix_rows[0][1]) / 8)}
    area_km2 = (134 - 23) * w_ws / 1000.0
    om = c["eia_versions"]["qa"]["om_mb_per_year"]
    tour = {"water_area_km2": round(area_km2, 1), "water_width_m": round(w_ws), "raft_footprint_m2": 600,
            "rafts_per_pct_surface": round(area_km2 * 1e6 * 0.01 / 600),
            "bed_fall_km23_134_m": round(_profile_levels(KM0)[0] - _profile_levels(KM1)[0], 1),
            "drift_speed_kmh": round(sec["V_ms"] * 3.6, 1), "drift_hours_111km": round(111 / (sec["V_ms"] * 3.6)),
            "om_mb_per_year": om, "visitors_to_cover_om_m": {str(m): round(om / m, 1) for m in (100, 200, 400)},
            "longest_whitewater_found_km": {"purpose_built": 1.14, "river_reshaped_urban": 4.0, "olympic_slalom_m": 300},
            "src_ww": "ค้นเว็บ 16 ต.ค. 2569 (ยังไม่พบสถิติโลกที่ตรวจยืนยันได้): ศูนย์ล่องแก่งแห่งชาติสหรัฐ (ชาร์ล็อตต์) ช่องน้ำรวมราว 1,140 ม. สูบน้ำวน · แม่น้ำในเมืองโคลัมบัส (จอร์เจีย) ปรับให้ล่องแก่งได้ 1.5–2.5 ไมล์ (แหล่งข้อมูลขัดกัน เป็นคำโฆษณา) · สนามแข่งสลาลมโอลิมปิกมาตรฐานราว 300 ม."}
    V = sec["V_ms"]
    cp = 0.3
    pden = 0.5 * 1000 * V ** 3 * cp
    kin = []
    for frac in (0.1, 0.2):
        per = pden * sec["A_m2"] * frac / 1000.0
        kin.append({"swept_fraction": frac, "kw_per_station": round(per, 1), "mw_55_stations": round(per * 55 / 1000.0, 2)})
    ts = np.linspace(0, 2 * math.pi, 2000)
    head = np.maximum(1.5 - (0.5 + 2.0 * np.sin(ts)), 0.0)
    h_avg = float(head.mean())
    p_gate = 9810 * Q * h_avg * 0.8 / 1e6
    # วันผันน้ำเต็มกำลังเทียบเท่า = น้ำท่ารายปีที่ S.26 ÷ (600 ลบ.ม./วินาที × 86,400) — ขอบบน (สมมติว่าคลองรับน้ำ S.26 ได้ทั้งหมด)
    fd = OCR_S26["full_flow_mcm_per_day"]
    day_list = [round(OCR_S26["annual_min_mcm"] / fd), round(OCR_S26["annual_mean_mcm"] / fd), round(OCR_S26["annual_max_mcm"] / fd)]
    days = {str(d): {"label": lab, "gate_gwh": round(p_gate * 24 * d / 1000, 1),
                     "kinetic_gwh": [round(k["mw_55_stations"] * 24 * d / 1000, 1) for k in kin]}
            for d, lab in zip(day_list, ("ปีน้ำน้อย", "ปีเฉลี่ย", "ปีน้ำมาก"))}
    pv = c["options"]["floating_pv"]
    hyd = {"velocity_ms": V, "cp": cp, "power_density_w_m2": round(pden), "kinetic": kin,
           "gate_head_avg_m": round(h_avg, 2), "gate_open_fraction": round(float((head > 0).mean()), 2),
           "gate_power_mw_avg": round(p_gate, 1), "days_scenarios": days,
           "pv_gwh_per_year": [pv[0]["gwh_per_year"], pv[1]["gwh_per_year"]], "pv_mwp": [pv[0]["mwp"], pv[1]["mwp"]],
           "outlet_pump_mw_1m": c["options"]["outlet_pump"][0]["power_mw"],
           "assumptions": "ทะเลขึ้นลงแบบคลื่นไซน์ +0.5±2.0 ม.รทก. (ช่วง −1.49…+2.49 ของปี 2554) · น้ำปลายคลอง +1.5 · ประสิทธิภาพกังหัน 0.8 · "
                          "กังหันกลางน้ำ สัมประสิทธิ์กำลัง 0.3 · 55 สถานี (ทุก 2 กม.) · วันผันน้ำเต็มกำลังเทียบเท่า = น้ำท่ารายปีสถานี S.26 (ต่ำสุด/เฉลี่ย/สูงสุด ปี 2528–2566) ÷ 600 ลบ.ม./วินาที — ขอบบน"}
    return {"tide": tide, "deep_cut": deep, "land_dev": land, "tourism": tour, "hydro": hyd}


def main():
    OUT.mkdir(exist_ok=True)
    mk = json.load(open(D7 / "km_markers.geojson"))["features"]
    L = max(f["properties"]["km"] for f in mk)
    c = {
        "meta": {"built_by": "analysis/goal7_analysis.py", "alignment_source": "Google My Maps (ผู้ใช้สร้าง — ไม่เป็นทางการ)"},
        "facts": FACTS, "reconciled_parameters": RECONCILED_PARAMETERS, "canal_volume_check": canal_volume_by_official_reaches(), "design_segments": design_check(), "design_2566": DESIGN_2566, "dwr_plan": DWR_PLAN, "eia_land": EIA_LAND, "eia_econ": EIA_ECON, "eia_social": EIA_SOCIAL, "concern_checks": CONCERN_CHECKS, "eia_section": EIA_SECTION, "eia_levels": eia_levels(dem_profile()["profile_every_10km"]), "eia_profile": eia_profile(), "design_2565": DESIGN_2565, "design_2565_structs": DESIGN_2565_STRUCTS, "meeting_20260909": MEETING_20260909, "struct_compare": struct_compare(), "design_2560": DESIGN_2560, "participation": PARTICIPATION, "concerns": CONCERNS, "civic_funding": CIVIC_FUNDING, "design_history": DESIGN_HISTORY, "eia_versions": EIA_VERSIONS, "eia_structs": eia_structs_summary(),
        "alignment_qa": json.loads((D7 / "alignment_qa.json").read_text(encoding="utf-8")),
        "provinces_km": {"สระบุรี": [0, KM_NN0], "นครนายก": [KM_NN0, KM_NN1], "ฉะเชิงเทรา": [KM_NN1, KM_SP0], "สมุทรปราการ": [KM_SP0, 135.7]},
        "structures": structures(), "dem": dem_profile(), "manning": manning(), "c2": c2_peaks(),
        "pasak_dam": pasak_dam(), "corridor_area": corridor_area(round(L, 1)), "flood_band": flood_band(),
    }
    c["embankment"] = embankment_scenarios(c)
    c["basins_2569"] = basins_summary()
    sc = OUT / "eia2569_scan.json"
    if sc.exists():
        c["reading_coverage"] = {"scan": json.loads(sc.read_text(encoding="utf-8")),
                                 "kw": {"model": "แบบจำลอง", "flood_side": "น้ำท่วมซ้ำซาก/ขัง", "gate_rule": "เกณฑ์เดินประตู", "fault": "รอยเลื่อน",
                                        "salinity": "น้ำเค็ม", "subsidence": "ทรุดตัว", "opinion": "ความคิดเห็น/แบบสอบถาม", "cost": "ค่าก่อสร้าง/วงเงิน"}}
    c["options"] = options_screening(c)
    c["runoff"] = runoff_screening(c)
    c["extra_q"] = extra_questions(c)
    c["new_cases"] = new_cases(c)
    c["ocr_facts"] = {"facts": OCR_FACTS, "s26": OCR_S26}
    c["acid_soil"] = acid_soil(c)
    c["nn_venues_2566"] = nn_venues(c)
    c["nuclear_site"] = nuclear_site(c)
    c["bpk_role"] = bpk_role(c)
    c["golf_case"] = golf_case(c)
    c["concern_short"] = {str(k): v for k, v in CONCERN_SHORT.items()}
    c["nn_water_users"] = NN_WATER_USERS
    c["eia_construction"] = eia_construction_plan()
    c["ongkharak_flood"] = ongkharak_flood_persistence(c)
    cf_file = OUT / "counterfactual_simulation_summary.json"
    if cf_file.exists():
        # รีวิวรอบ 4: ตั้งชื่อ key ระบุโดเมน (คลองเจ้าพระยา 2) — กันชื่อชนกับสถานการณ์ของงานลุ่มนครนายก
        # รีวิวรอบ 6 (A4): รูปคลื่นสังเคราะห์ ไม่ใช่ผลวัด/สอบเทียบ — แยกไว้ใต้ illustrative_only ห้ามรายงานอ้าง
        c["illustrative_only"] = {"cp2_bypass_counterfactual": {
            "status": "illustrative_only",
            "note": "รูปคลื่นสังเคราะห์ (sin + สุ่ม) ความจุปลอดภัย 2,600 และ dQ/dh 1,100 ไม่มีที่มา — ห้ามอ้างในรายงาน",
            **json.loads(cf_file.read_text(encoding="utf-8"))}}
    for fname, k in [
        ("ayutthaya_dqdh_rating_summary.json", "ayutthaya_dqdh_rating"),
        ("ongkharak_2d_depression_summary.json", "ongkharak_2d_depression"),
        ("legal_and_nuclear_summary.json", "legal_and_nuclear_assessment"),
        ("acid_sulfate_soil_summary.json", "acid_sulfate_soil_assessment"),
        ("interbasin_transfer_summary.json", "interbasin_transfer_vectors"),
        ("dam_to_gulf_summary.json", "dam_to_gulf_corridors"),
        ("bangban_bangsai_comparison.json", "bangban_bangsai_case"),
        ("operational_economics_summary.json", "operational_economics"),
    ]:
        fpath = OUT / fname
        if fpath.exists():
            c[k] = json.loads(fpath.read_text(encoding="utf-8"))
    # ผลจากชุดมิตรเอิร์ธ/การปรับ DEM (20 ต.ค. 69): เก็บเฉพาะส่วนที่รายงานใช้ (ไม่เก็บบัญชี 77 จังหวัดรายละเอียด)
    if (OUT / "dem_bias_correction.json").exists():
        c["dem_bias_correction"] = json.loads((OUT / "dem_bias_correction.json").read_text(encoding="utf-8"))
    if (OUT / "dem_waterline_test.json").exists():
        c["dem_waterline_test"] = json.loads((OUT / "dem_waterline_test.json").read_text(encoding="utf-8"))
    if (OUT / "dem_gistda_waterline_test.json").exists():
        c["dem_gistda_waterline_test"] = json.loads((OUT / "dem_gistda_waterline_test.json").read_text(encoding="utf-8"))
    if (OUT / "bangpakong_chachoengsao.json").exists():
        c["bangpakong_chachoengsao"] = json.loads((OUT / "bangpakong_chachoengsao.json").read_text(encoding="utf-8"))
    if (OUT / "mitrearth_national_summary.json").exists():
        nat = json.loads((OUT / "mitrearth_national_summary.json").read_text(encoding="utf-8"))
        c["mitrearth_national"] = {k: nat[k] for k in ("gistda_corridor_2005_2019", "gistda_vs_2026_nakhon_nayok", "sea_level_rise_vs_canal", "dempro_vs_eia_ground")}
    (OUT / "canonical.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: c[k] for k in ("structures", "c2", "pasak_dam", "corridor_area", "flood_band")}, ensure_ascii=False, indent=1)[:5000])


if __name__ == "__main__":
    main()
