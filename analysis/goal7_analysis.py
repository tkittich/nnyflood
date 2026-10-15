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
    "eirr_2565": {"v": "อัตราผลตอบแทนทางเศรษฐกิจ 14.52%", "tier": "A", "src": "เอกสารกรมชลประทาน มี.ค. 2565 (ระยะที่ 1)"},
    "bcr_2569": {"v": "อัตราส่วนผลประโยชน์ต่อต้นทุน 2.12 (คิดลด 7%) · 1.48 (9%) · 0.97 (12%) · อัตราผลตอบแทนทางเศรษฐกิจ 10.94%", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 2 ตาราง 8.8-1 (หน้า 8-19)"},
    "design_depth_m": {"v": 7.0, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38 (กม.23–ปลายคลอง) · ข่าวปี 2564/2569 ระบุ 6 ม."},
    "design_bed_slope": {"v": "1:25,000 (0.04 ม./กม.)", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38"},
    "water_above_ground_m": {"v": "1–3.3", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38 (ระดับน้ำสูงสุดออกแบบสูงกว่าพื้นเดิม กม.23–ปลายคลอง · \"คลองลอย\")"},
    "crest_msl_end": {"v": "+4.00 ม.รทก. (กม.109–ปลายคลอง · เผื่อพ้นน้ำ 1.50 ม.)", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38 และ 2-79"},
    "end_water_level": {"v": "+1.50 หน้าประตูปลายคลอง · +2.50 หลังอัดน้ำ", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-38"},
    "side_drain": {"v": "คูระบายน้ำกว้าง 3 ม. ลึก 1 ม. ด้านนอกคันทั้งสองฝั่ง", "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-45"},
    "n_cross_structures_eia": {"v": 34, "tier": "A", "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-60 (อาคารเชื่อมคลองแบบท่อระบายน้ำ+ไซฟอน) — นับต่างจากตารางแผนที่ของรายงานนี้"},
    "eia_board": {"v": "คชก. เห็นชอบ พ.ค. 2568 · กก.วล. ครั้งที่ 6/2568 เห็นชอบ 18 ธ.ค. 2568", "tier": "A", "src": "สรุปการประชุมจังหวัดนครนายก 9 ก.ย. 2569 — ชื่อในมติ ทางระบายน้ำหลากเจ้าพระยาฝั่งตะวันออกตอนล่าง (ป่าสัก–อ่าวไทย)"},
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
    {"year": "พ.ย. 2561", "event": "รายงานสิ่งแวดล้อมฉบับหลัก (ตามที่สมาคมพลเมืองนครนายกระบุ)", "tier": "C"},
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


EIA_SECTION = {"D_m": 7.0, "A_m2": 504.0, "V_ms": 1.20, "n": 0.016, "slope_1_n": 25000, "z1": 3.0, "z2": 2.0, "road_m": 10.0,
               "src": "รายงานผลกระทบสิ่งแวดล้อม เล่ม 1 หน้า 2-39 (รูปที่ 2.3.2-11 ตาราง กม.23–134)"}


def eia_levels(dem_profile_rows):
    """ระดับน้ำ/สันคัน ตามค่าของรายงานผลกระทบสิ่งแวดล้อมเทียบพื้นดินจาก DEM (ประมาณ — ใช้ลาดก้นคลอง 1:25,000 ต่อจากระดับ +2.50 ที่ กม.109)"""
    g = {p["km"]: p["ground_m"] for p in dem_profile_rows}
    out = []
    for km in (40, 50, 60, 70, 100):
        if km not in g:
            continue
        water = 2.5 + max(0, 109 - km) * (1000 / 25000) / 1.0 * 1.0 if km < 109 else 2.5
        # หน่วย: ลาด 1:25,000 = 0.04 ม./กม.
        water = 2.5 + (109 - km) * 0.04
        crest = water + 1.5
        out.append({"km": km, "ground_dsm_m": g[km], "water_msl_m": round(water, 2), "water_above_ground_m": round(water - g[km], 1),
                    "crest_msl_m": round(crest, 2), "crest_above_ground_m": round(crest - g[km], 1)})
    return {"rows": out, "note": "ค่าคำนวณของรายงานนี้จากตัวเลขรายงานผลกระทบสิ่งแวดล้อม (ลาด 1:25,000 + ระดับ +2.50 ที่ กม.109 + เผื่อพ้นน้ำ 1.50) ไม่ใช่ตัวเลขในแบบ · พื้นดินเป็นความสูงพื้นผิว ±2–4 ม. · ไม่รวมการลดระดับที่ปตร.กลางคลอง กม.74 และ 102",
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
    1: "ตรวจไม่ได้ครบ — ไม่มีฉบับ พ.ย. 2561 มาเทียบ · ที่ตรวจได้: ผลตอบแทนที่ 12% ปี 2560 (13.33%, B/C 1.12, มูลค่าปัจจุบันสุทธิ 10,046 ล้านบาท) ต่างจากฉบับ 2569 (10.94%, 0.97, −2,821) · แนวเขตคลองลดจาก ~200 ม. เหลือ 170/180 ม. หลังรับฟังความเห็นปี 2560",
    7: "ฉบับ 2569: ที่ดิน 16,288 ไร่ · ผู้ถือครอง 2,600 ราย · สิ่งปลูกสร้าง 1,378 หลัง (ตัวเลข 1,563 หลังของผู้ยื่นต่างจาก 1,378 — ต้องดูว่านับต่างกันหรือไม่) · ตารางเศรษฐศาสตร์มีค่าชดเชยสิ่งปลูกสร้าง ไม้ยืนต้น ค่าเสียโอกาสการใช้ที่ดิน และอาชีพประมงท้ายน้ำ",
    8: "ประวัติ: กลุ่มย่อยในองครักษ์ 27 ก.ค. 2559 (2 เวที) และ 1 มี.ค. 2560 (อบต.คลองใหญ่) แต่ประชุมสาธารณะ 2 ครั้งอยู่นอกนครนายก · รายงานสำรวจผู้ถูกเวนคืน 123 ราย: ร้อยละ 55.3 ยังไม่ทราบเกี่ยวกับโครงการ · ร้อยละ 20 ไม่ยินยอมให้ที่ดิน (เหตุหลัก: กลัวได้ค่าเวนคืนต่ำ ร้อยละ 41.35)",
    9: "ปี 2560 ที่ 12%: ผลตอบแทน 13.33% B/C 1.12 (คุ้มค่า) → ฉบับ 2569: 10.94% B/C 0.97 (ไม่คุ้มค่า) · ตรงกับตารางที่ 8.8-1: อัตราส่วนผลประโยชน์ต่อต้นทุน 2.12 / 1.48 / 0.97 ที่คิดลด 7 / 9 / 12 % — ไม่คุ้มค่าที่ 12% (รายงานสรุปเช่นนั้นเอง) · ตัวเลข \"เผื่อเหลือเผื่อขาด 5 ล้านบาท\" ยังไม่ได้ตรวจ",
    12: "ตารางเศรษฐศาสตร์ (ตาราง 8.8-2) มีรายการค่าชดเชยสิ่งปลูกสร้างและไม้ยืนต้น ค่าเสียโอกาสการใช้ที่ดิน และความเสียหายอาชีพประมงท้ายน้ำ — ผู้เช่า/ผู้ไม่มีเอกสารสิทธิ์ยังไม่พบในตารางที่ตรวจ",
}

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
    {"date": "28–29 มี.ค. 2560", "event": "ประชุมสาธารณะครั้งที่ 2 (2 เวที: สระบุรี และสมุทรปราการ)", "n": 267, "nn_venue": False,
     "note": "ผู้ได้รับผลกระทบ 106 คน · พื้นที่ศึกษา 6 จังหวัด 13 อำเภอ รวมบ้านนาและองครักษ์ — ไม่มีเวทีในนครนายก"},
]

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
            "official_total_crossings": {"eia_2569": 34 + 5, "design_2560": DESIGN_2560["crossings_siphon_drain"] + DESIGN_2560["crossings_with_locks"]},
            "all_route_crossings_sheets": sum(1 for r in rows if r["kind"] in ("อาคารเชื่อมจุดตัดคลอง", "ท่อระบายน้ำและไซฟอน")),
            "all_route_road_bridges_sheets": sum(1 for r in rows if r["kind"] == "สะพานรถยนต์"),
            "note": "แบบ 2565 นับจากเอกสารกรมชลประทาน (14+5 อาคารตัดคลอง · สะพานรถยนต์ 15) · แบบ 2569 นับจากแผนที่รายช่วงที่ผู้ใช้ได้มา อ่านด้วยตา"}


def main():
    OUT.mkdir(exist_ok=True)
    mk = json.load(open(D7 / "km_markers.geojson"))["features"]
    L = max(f["properties"]["km"] for f in mk)
    c = {
        "meta": {"built_by": "analysis/goal7_analysis.py", "alignment_source": "Google My Maps (ผู้ใช้สร้าง — ไม่เป็นทางการ)"},
        "facts": FACTS, "design_segments": design_check(), "eia_land": EIA_LAND, "eia_econ": EIA_ECON, "eia_social": EIA_SOCIAL, "concern_checks": CONCERN_CHECKS, "eia_section": EIA_SECTION, "eia_levels": eia_levels(dem_profile()["profile_every_10km"]), "design_2565": DESIGN_2565, "design_2565_structs": DESIGN_2565_STRUCTS, "meeting_20260909": MEETING_20260909, "struct_compare": struct_compare(), "design_2560": DESIGN_2560, "participation": PARTICIPATION, "concerns": CONCERNS, "civic_funding": CIVIC_FUNDING, "design_history": DESIGN_HISTORY,
        "alignment_qa": json.loads((D7 / "alignment_qa.json").read_text(encoding="utf-8")),
        "provinces_km": {"สระบุรี": [0, KM_NN0], "นครนายก": [KM_NN0, KM_NN1], "ฉะเชิงเทรา": [KM_NN1, KM_SP0], "สมุทรปราการ": [KM_SP0, 135.7]},
        "structures": structures(), "dem": dem_profile(), "manning": manning(), "c2": c2_peaks(),
        "pasak_dam": pasak_dam(), "corridor_area": corridor_area(round(L, 1)), "flood_band": flood_band(),
    }
    (OUT / "canonical.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: c[k] for k in ("structures", "c2", "pasak_dam", "corridor_area", "flood_band")}, ensure_ascii=False, indent=1)[:5000])


if __name__ == "__main__":
    main()
