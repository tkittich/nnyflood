"""เป้าหมาย 7 — ชุดมิตรเอิร์ธระดับประเทศ ("3 Thailand", โหลดเอง 20 ต.ค. 69): ตรวจรายการ · ดึงชั้นที่ใช้ได้จริง (สถานีอุทกวิทยา กรมชลประทาน · จุดร่องน้ำตัดถนน · หมู่บ้านพร้อมระดับพื้น) ใกล้แนวคลอง

ผลตรวจ (ดู analysis/goal7/mitrearth_thailand_summary.json): ชุดที่โหลดครั้งแรก (1,147 ไฟล์) ไม่ครบ — ชุดฉบับสมบูรณ์ (8,086 ไฟล์) มี shapefile สมบูรณ์ 179 ชุด ขาดเล็กน้อย 12 ชุด (ส่วนใหญ่ชั้นหลุมยุบ/แผ่นดินถล่ม/พื้นที่ภัยแล้ง ที่อยู่นอกขอบเขตโครงการ)
· 36 SAGA: ภาพ TIFF ระดับประเทศเป็นภาพ 8 บิต (ไม่ใช่ค่าความสูง/ความลาด) ส่วนกริดรายจังหวัดความละเอียด 0.01° (~1.1 กม.) — หยาบเกินใช้ในโครงการ
· 21 Topo Map: มีเพียงไฟล์ .ige ขนาด 0 ไบต์ (ไม่มีข้อมูล)
ชั้นน้ำท่วม GISTDA/ระดับน้ำทะเลสูงขึ้น/DEMPro ประมวลผลใน analysis/goal7_mitrearth_national.py
ข้อควรระวัง: ข้อความภาษาไทยในบางแอตทริบิวต์ของ KMZ เสียรูป (วรรณยุกต์กลายเป็น '?') · แนวคลองจากหมุด กม. (official_geometry) เป็นแนวประมาณ — ระยะถึงแนวคลองคลาดได้ ~0.5 กม.
สิทธิ์ใช้งาน: ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์

รัน: python analysis/goal7_mitrearth_thailand.py
ผลลัพธ์: analysis/goal7/mitrearth_thailand_summary.json · analysis/goal7/rid_hydro_stations_study_area.csv · analysis/goal7/stream_road_crossings_corridor.csv
"""
from __future__ import annotations

import csv
import html
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "data/10_mitrearth_gis/thailand_national_full"
GEOM = ROOT / "analysis/goal7/official_geometry.json"
OUT = ROOT / "analysis/goal7/mitrearth_thailand_summary.json"
TO_UTM = Transformer.from_crs(4326, 32647, always_xy=True).transform
STUDY_BBOX = (100.0, 13.3, 101.7, 15.6)       # lon_min, lat_min, lon_max, lat_max (ลุ่มเจ้าพระยาตอนล่าง–นครนายก–อ่าวไทย)
STUDY_PROVINCES = {"Nakhon Nayok", "Bangkok", "Chachoengsao", "Nonthaburi", "Pathum Thani", "Prachin Buri", "Phra Nakhon Si Ayutthaya", "Ang Thong", "Sing Buri", "Samut Prakan", "Samut Sakhon",
                   "Saraburi", "Lop Buri", "Chai Nat"}


def placemarks(kmz: Path):
    z = zipfile.ZipFile(kmz)
    k = next(x for x in z.namelist() if x.endswith(".kml"))
    t = z.read(k).decode("utf-8", "ignore")
    for m in re.finditer(r"<Placemark.*?</Placemark>", t, re.S):
        b = m.group(0)
        nm = re.search(r"<name>(.*?)</name>", b, re.S)
        co = re.search(r"<coordinates>\s*([^<]+?)\s*</coordinates>", b, re.S)
        attrs = {html.unescape(a).strip(): html.unescape(v).strip() for a, v in re.findall(r"<td>([^<]*)</td>\s*<td>([^<]*)</td>", b)}
        if co:
            x, y = (float(v) for v in co.group(1).split()[0].split(",")[:2])
            yield (html.unescape(nm.group(1)) if nm else ""), x, y, attrs


def canal_tree():
    st = json.loads(GEOM.read_text(encoding="utf-8"))["stations"]
    km = np.array([s["km"] for s in st])
    xs, ys = np.array([s["x"] for s in st]), np.array([s["y"] for s in st])
    dense_km = np.arange(km[0], km[-1], 0.05)
    dx, dy = np.interp(dense_km, km, xs), np.interp(dense_km, km, ys)
    return cKDTree(np.column_stack([dx, dy])), dense_km


def reach_of(km: float) -> str:
    return "กม.0–23" if km < 23 else ("กม.23–134" if km < 134 else "กม.134–135.9")


def completeness() -> dict:
    stems = defaultdict(set)
    for p in PACK.rglob("*"):
        if p.is_file() and not p.name.endswith(".shp.xml"):
            stems[(str(p.parent), p.stem)].add(p.suffix.lower())
    inc, ok = 0, 0
    for ex in stems.values():
        if ex & {".shp", ".shx", ".dbf", ".sbn"}:
            if {".shp", ".shx", ".dbf"} - ex:
                inc += 1
            else:
                ok += 1
    return {"files": sum(1 for p in PACK.rglob("*") if p.is_file()), "shapefile_sets_complete": ok, "shapefile_sets_incomplete": inc}


def stations() -> dict:
    f = next(PACK.glob("24 GE Hydrology/1*/3_Hydro_Station_RID*.kmz"))
    rows = [(n, x, y, a) for n, x, y, a in placemarks(f) if STUDY_BBOX[0] <= x <= STUDY_BBOX[2] and STUDY_BBOX[1] <= y <= STUDY_BBOX[3]]
    out = ROOT / "analysis/goal7/rid_hydro_stations_study_area.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "lon", "lat", "description"])
        for n, x, y, a in sorted(rows, key=lambda r: (r[0], r[1])):
            w.writerow([n, round(x, 5), round(y, 5), a.get("Descriptio", "")])
    allp = list(placemarks(f))
    return {"total_stations": len(allp), "in_study_area": len(rows), "csv": str(out.relative_to(ROOT)), "codes_in_study_area": sorted({r[0].split(".")[0] for r in rows}),
            "ny_stations": sorted({r[0] for r in rows if r[0].startswith("Ny")}), "note": "สถานีอุทกวิทยากรมชลประทานพร้อมพิกัด — ใช้ระบุพิกัด Ny.1B / Ny.7 และสถานีอื่นที่เคยไม่มีพิกัดในคลัง"}


def crossings(tree) -> dict:
    f = next(PACK.glob("38 City*/4-4*"))
    rows = []
    tot = 0
    for n, x, y, a in placemarks(f):
        tot += 1
        if not (STUDY_BBOX[0] <= x <= STUDY_BBOX[2] and STUDY_BBOX[1] <= y <= STUDY_BBOX[3]):
            continue
        ux, uy = TO_UTM(x, y)
        d, i = tree[0].query([ux, uy])
        if d <= 3000:
            km = float(tree[1][i])
            el = re.search(r"[-\d.]+", a.get("ELEVATION", ""))
            da = re.search(r"[\d.]+", a.get("DRAIN_AREA", ""))
            rows.append({"km": round(km, 2), "dist_m": int(d), "name": n, "elevation_m": float(el.group()) if el else None, "drain_area_km2": float(da.group()) if da else None, "lon": round(x, 5), "lat": round(y, 5)})
    rows.sort(key=lambda r: r["km"])
    out = ROOT / "analysis/goal7/stream_road_crossings_corridor.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    by_reach = Counter(reach_of(r["km"]) for r in rows)
    return {"total_points_nationwide": tot, "within_3km_of_canal": len(rows), "by_reach": dict(by_reach), "largest_drain_areas_km2": sorted([r["drain_area_km2"] for r in rows if r["drain_area_km2"]], reverse=True)[:5], "csv": str(out.relative_to(ROOT)),
            "note": "จุดที่ร่องน้ำตัดถนน (ชั้น 'จุดร่องน้ำตัดถนน' จังหวัด) ภายใน 3 กม. จากแนวคลองประมาณ — ใช้ตรวจเทียบอาคารตัดคลองใน EIA (99 แถว) ไม่ใช่รายการอาคารจริง"}


def villages(tree) -> dict:
    p = next(PACK.glob("33 GE Village Nature Slide Flow Flood/3 Village Regional Flood*.txt"))
    raw = p.read_bytes().decode("cp874", "replace").splitlines()
    head = raw[0].split("\t")
    ix = {h.strip(): i for i, h in enumerate(head)}
    n_all = 0
    in_prov, near = Counter(), defaultdict(list)
    for ln in raw[1:]:
        c = ln.split("\t")
        if len(c) < len(head):
            continue
        n_all += 1
        prov = c[ix["ProvinceEn"]].strip()
        if prov in STUDY_PROVINCES:
            in_prov[prov] += 1
        try:
            lon, lat, el = float(c[ix["Longitude"]]), float(c[ix["Lattitude"]]), float(c[ix["Elevation(m)"]])
        except ValueError:
            continue
        if not (STUDY_BBOX[0] <= lon <= STUDY_BBOX[2] and STUDY_BBOX[1] <= lat <= STUDY_BBOX[3]):
            continue
        ux, uy = TO_UTM(lon, lat)
        d, i = tree[0].query([ux, uy])
        if d <= 5000:
            near[reach_of(float(tree[1][i]))].append((d, el))
    res = {"villages_nationwide": n_all, "villages_by_study_province": dict(in_prov), "near_canal": {}}
    for r, v in near.items():
        d = np.array([x[0] for x in v])
        e = np.array([x[1] for x in v])
        res["near_canal"][r] = {"within_1km": int((d <= 1000).sum()), "within_2km": int((d <= 2000).sum()), "within_5km": len(v), "elevation_m_median_within_2km": round(float(np.median(e[d <= 2000])), 1) if (d <= 2000).any() else None}
    res["note"] = "ชั้น 'หมู่บ้านในพื้นที่น้ำท่วมระดับภูมิภาค' (มิตรเอิร์ธ): พิกัด · ระดับพื้น · ความลาด · ที่ตั้ง (นับเป็นจำนวนหมู่บ้าน ไม่ระบุชื่อ) — ไม่ใช่รายการผู้ได้รับผลกระทบ · ที่มาของระดับพื้นไม่ระบุ (นัย DEM 30 ม. ของมิตรเอิร์ธ)"
    return res


def main() -> None:
    tree = canal_tree()
    summary = {"source": {"pack": "data/10_mitrearth_gis/thailand_national_full/ (ย้ายจาก data/manual/3 Thailand 20 ต.ค. 69 — ฉบับสมบูรณ์ 8,086 ไฟล์ 16 GB)", "site": "https://www.mitrearth.org/category/map/", "license_note": "ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์"},
               "completeness": completeness(), "rid_hydro_stations": stations(), "stream_road_crossings": crossings(tree), "villages_regional_flood": villages(tree)}
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("completeness",)}, ensure_ascii=False))
    print("stations", summary["rid_hydro_stations"]["in_study_area"], summary["rid_hydro_stations"]["ny_stations"])
    print("crossings", summary["stream_road_crossings"]["within_3km_of_canal"], summary["stream_road_crossings"]["by_reach"])
    print("villages", summary["villages_regional_flood"]["villages_nationwide"], summary["villages_regional_flood"]["near_canal"])


if __name__ == "__main__":
    main()
