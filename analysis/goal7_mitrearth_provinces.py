"""เป้าหมาย 7 — ชั้นข้อมูลมิตรเอิร์ธรายจังหวัดลุ่มเจ้าพระยาตอนล่างถึงอ่าวไทย: ขอบเขตน้ำท่วม GISTDA 2548–2554 รายปี · ลุ่มน้ำย่อย · เทียบน้ำท่วม 2569 (เฉพาะส่วนที่อยู่ในกริดเรดาร์)

ครอบคลุม 11 จังหวัด: นครนายก (ชุดเต็มที่มีอยู่แล้ว) + กรุงเทพฯ · ฉะเชิงเทรา · นนทบุรี · ปทุมธานี · ปราจีนบุรี · อยุธยา · สมุทรปราการ · สมุทรสาคร · สิงห์บุรี · อ่างทอง (โหลดเอง 20 ต.ค. 69 ชุดย่อย 2/5/6/7)
ข้อจำกัดที่พบ (ไม่ใช่ข้อมูลที่หายจากการโหลด — โฟลเดอร์บน Drive ไม่มีไฟล์เหล่านี้): ชั้น GISTDA ของ สมุทรปราการ · สมุทรสาคร · สิงห์บุรี · อ่างทอง ไม่มีไฟล์ .shp/.dbf (มีแต่ .prj .shx) จึงไม่มีตัวเลขน้ำท่วมของ 4 จังหวัดนี้ ·
ลุ่มน้ำย่อย อ่างทองไม่มี .shp ของ Drainage Basin
วิธี: พื้นที่สุทธิรายปี = รูปปิดของปีนั้นลงตาราง 50 ม. (UTM 47N) โดยรูเปิดไม่นับ ส่วนซ้อนนับครั้งเดียว ตัดด้วยเส้นเขตจังหวัด · ปี 0 = ไม่ระบุปี ไม่นับในตารางรายปี · .prj ของชั้น GISTDA เป็นพิกัด WGS84 (ตรวจจากไฟล์) · เส้นเขตจังหวัดได้จากการรวมชั้นตำบล (`Tambon area`) เทียบพื้นที่จริง: กทม. 1,569 · นนทบุรี 633 · ฉะเชิงเทรา 5,238 ตร.กม.
ข้อควรระวัง: GISTDA แต่ละปีมาจากภาพต่างวันและต่างเกณฑ์ (ปีเดียวกันอาจไม่ครอบคลุมทุกจังหวัดเท่ากัน — เช่น 2007 มีเฉพาะบางจังหวัด) จึงเทียบปีข้ามจังหวัดเป็นขนาดคร่าว ๆ ไม่ใช่สถิติที่ครบถ้วน · ชุดมิตรเอิร์ธ ห้ามใช้เชิงพาณิชย์

รัน: python analysis/goal7_mitrearth_provinces.py
ผลลัพธ์: analysis/goal7/mitrearth_provinces_summary.json
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
import rasterio.features
import shapefile  # pyshp
from pyproj import Transformer
from shapely.geometry import shape as shp_shape
from shapely.ops import transform as shp_transform

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_mitrearth_layers as ml  # noqa: E402  (reuse-first: แตกไฟล์/กริดเรดาร์/ลงตารางชุดเดียวกับชุดนครนายก)

PROV = ROOT / "data/10_mitrearth_gis/provinces"
OUT = ROOT / "analysis/goal7/mitrearth_provinces_summary.json"
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32647", always_xy=True).transform
CELL_M = 50.0
NAMES = {"nakhon_nayok_18": "นครนายก", "chachoengsao_10": "ฉะเชิงเทรา", "prachin_buri_31": "ปราจีนบุรี", "pathum_thani_29": "ปทุมธานี", "nonthaburi_24": "นนทบุรี", "bangkok_02": "กรุงเทพมหานคร",
         "ayutthaya_33": "พระนครศรีอยุธยา", "ang_thong_72": "อ่างทอง", "sing_buri_65": "สิงห์บุรี", "samut_prakan_60": "สมุทรปราการ", "samut_sakhon_62": "สมุทรสาคร"}


def paths_for(pid: str) -> dict:
    if pid == "nakhon_nayok_18":
        ex = ml.extract()
        with zipfile.ZipFile(ml.ZIP) as z:
            for n in z.namelist():
                base = n.rsplit("/", 1)[-1]
                if "2 Boundary and Point" in n and base.startswith("18 Tambon area") and base.rsplit(".", 1)[-1] in ("shp", "dbf", "shx", "prj"):
                    dst = ml.EXT / base
                    if not dst.exists():
                        dst.write_bytes(z.read(n))
        return {"gistda": ex["gistda"], "basin": ex["basin"], "bound": ml.EXT / "18 Tambon area.shp"}
    d = PROV / pid
    g = sorted((d / "7 Geological Hazard").glob("*GISTDA*.shp"))
    b = sorted((d / "6 Valley Ridge and Basin").glob("* Drainage Basin.shp"))
    return {"gistda": g[0] if g else None, "basin": b[0] if b else None, "bound": next((f for f in sorted((d / "2 Boundary and Point").iterdir()) if f.name.lower().endswith("tambon area.shp")), None)}


def load_geoms(shp: Path, year_field: str | None = None):
    r = shapefile.Reader(str(shp))
    fields = [f[0] for f in r.fields[1:]]
    iy = fields.index(year_field) if year_field and year_field in fields else None
    for sr in r.iterShapeRecords():
        g = shp_shape(sr.shape.__geo_interface__)
        if not g.is_valid:
            g = g.buffer(0)
        yield (int(sr.record[iy]) if iy is not None else None), g


def province_outline(tambon_shp: Path, utm: bool = False):
    """เส้นเขตจังหวัด = รวมตำบลทั้งหมด (ชั้น `bound`/`pbound` ของชุดมิตรเอิร์ธเป็นกรอบแผนที่/จังหวัดข้างเคียง ใหญ่กว่าจังหวัด ~2 เท่า — ห้ามใช้)"""
    from shapely.ops import unary_union
    g = unary_union([g for _, g in load_geoms(tambon_shp)])
    return shp_transform(TO_UTM, g) if utm else g


def utm_grid(bounds):
    x0, y0, x1, y1 = bounds
    pad = CELL_M * 2
    x0, y0, x1, y1 = np.floor(x0 - pad), np.floor(y0 - pad), np.ceil(x1 + pad), np.ceil(y1 + pad)
    nx, ny = int((x1 - x0) / CELL_M), int((y1 - y0) / CELL_M)
    return rasterio.transform.from_origin(x0, y1, CELL_M, CELL_M), (ny, nx)


def province_stats(pid: str) -> dict:
    p = paths_for(pid)
    out: dict = {"name": NAMES[pid]}
    bound = province_outline(p["bound"], utm=True) if p.get("bound") else None
    if bound is None:
        out["error"] = "ไม่พบเส้นเขตจังหวัด"
        return out
    out["province_area_km2"] = round(bound.area / 1e6, 1)
    # ลุ่มน้ำย่อย
    if p["basin"]:
        areas = sorted((shp_transform(TO_UTM, g).area / 1e6 for _, g in load_geoms(p["basin"])), reverse=True)
        out["basins"] = {"n": len(areas), "largest_km2": [round(a, 1) for a in areas[:3]], "total_km2": round(sum(areas), 1)}
    else:
        out["basins"] = None
    # น้ำท่วม GISTDA
    if not p["gistda"]:
        out["gistda"] = None
        return out
    tr, shape = utm_grid(bound.bounds)
    prov_mask = rasterio.features.rasterize([(bound, 1)], out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool)
    by_year: dict[int, list] = {}
    for y, g in load_geoms(p["gistda"], "year"):
        by_year.setdefault(y, []).append(shp_transform(TO_UTM, g))
    cell_km2 = CELL_M * CELL_M / 1e6
    per_year, count = {}, np.zeros(shape, dtype=np.uint8)
    for y in sorted(k for k in by_year if k and k > 0):
        a = rasterio.features.rasterize(((g, 1) for g in by_year[y]), out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool) & prov_mask
        count += a.astype(np.uint8)
        per_year[str(y)] = {"polygons": len(by_year[y]), "area_km2": round(float(a.sum()) * cell_km2, 1), "share_pct": round(100.0 * float(a.sum()) / float(prov_mask.sum()), 1)}
    unk = by_year.get(0, [])
    unk_km2 = float((rasterio.features.rasterize(((g, 1) for g in unk), out_shape=shape, transform=tr, fill=0, dtype="uint8").astype(bool) & prov_mask).sum()) * cell_km2 if unk else 0.0
    ever = float((count > 0).sum()) * cell_km2
    out["gistda"] = {"per_year": per_year, "ever_flooded_km2": round(ever, 1), "ever_flooded_share_pct": round(100.0 * ever / out["province_area_km2"], 1),
                     "by_number_of_years_km2": {str(n): round(float((count == n).sum()) * cell_km2, 1) for n in range(1, int(count.max()) + 1)},
                     "unknown_year": {"polygons": len(unk), "area_km2": round(unk_km2, 1)}}
    return out


def vs_2026() -> dict:
    """น้ำท่วม 2569 (เรดาร์ Sentinel-1 ของโครงการ) เทียบ GISTDA เฉพาะส่วนจังหวัดที่อยู่ในกริดเรดาร์และมีชั้น GISTDA"""
    flood = {"peak_27sep": np.load(ml.DER / "flood_peak_27sep1828.npy").astype(bool), "oct2_validated": np.load(ml.DER / "flood_2oct_validated.npy").astype(bool)}
    cov = np.zeros(ml.SHAPE, dtype=bool)
    count = np.zeros(ml.SHAPE, dtype=np.uint8)
    used = []
    for pid in NAMES:
        p = paths_for(pid)
        if not p["gistda"] or not p.get("bound"):
            continue
        bmask = ml.rasterize([province_outline(p["bound"])]) & ~cov          # จังหวัดติดกันซ้อนกันเล็กน้อย — นับครั้งเดียว
        if not bmask.any():
            continue
        c = np.zeros(ml.SHAPE, dtype=np.uint8)
        yrs = {}
        for y, g in load_geoms(p["gistda"], "year"):
            yrs.setdefault(y, []).append(g)
        for y in sorted(k for k in yrs if k and k > 0):
            c += ml.rasterize(yrs[y]).astype(np.uint8)
        count = np.where(bmask, c, count)
        cov |= bmask
        used.append({"province": NAMES[pid], "cells_in_grid_km2": round(float(bmask.sum()) * ml.CELL_KM2, 1)})
    res = {"covered_provinces_in_grid": used, "covered_area_km2": round(float(cov.sum()) * ml.CELL_KM2, 1), "note": "คิดเฉพาะส่วนจังหวัดที่มีชั้น GISTDA และอยู่ในกริดเรดาร์ — ไม่ใช่ทั้งลุ่มน้ำ"}
    for k, f in flood.items():
        f = f & cov
        tot = float(f.sum())
        res[k] = {"flooded_2026_km2": round(tot * ml.CELL_KM2, 1), "share_flooded_in_any_past_year_pct": round(100.0 * float((f & (count > 0)).sum()) / tot, 1) if tot else None,
                  "by_number_of_past_years_pct": {str(n): round(100.0 * float((f & (count == n)).sum()) / tot, 1) for n in range(0, int(count.max()) + 1)} if tot else None}
    return res


def main() -> None:
    prov = {pid: province_stats(pid) for pid in NAMES}
    total = {}
    for s in prov.values():
        for y, v in ((s.get("gistda") or {}).get("per_year") or {}).items():
            total[y] = round(total.get(y, 0.0) + v["area_km2"], 1)
    summary = {
        "source": {"pack": "data/10_mitrearth_gis/provinces_zips/<จังหวัด>/*.zip (โหลดเอง 20 ต.ค. 69) แตกไว้ที่ data/10_mitrearth_gis/provinces/ · นครนายกจาก data/manual/18 นครนายก (NAKHON NAYOK).zip", "site": "https://www.mitrearth.org/category/map/", "license_note": "ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์"},
        "provinces": prov,
        "gistda_missing_provinces": [NAMES[k] for k, v in prov.items() if v.get("gistda") is None],
        "gistda_total_by_year_km2_covered_provinces": dict(sorted(total.items())),
        "vs_2026": vs_2026(),
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    for pid, s in prov.items():
        g = s.get("gistda")
        print(s["name"], s.get("province_area_km2"), "basins", (s.get("basins") or {}).get("n"), "| ever", g and g["ever_flooded_share_pct"], "% |", g and {y: v["area_km2"] for y, v in g["per_year"].items()})
    print("missing:", summary["gistda_missing_provinces"])
    print("2026:", {k: summary["vs_2026"][k]["share_flooded_in_any_past_year_pct"] for k in ("peak_27sep", "oct2_validated")}, summary["vs_2026"]["covered_area_km2"])


if __name__ == "__main__":
    main()
