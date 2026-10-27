"""เทียบพื้นที่น้ำเรดาร์ต่อลุ่ม (ขั้นที่ 2 หลังจับฉากอ้างอิงตามวงโคจรสัมพัทธ์) กับชั้นน้ำท่วมสะสม 30 วันรายจังหวัดของ GISTDA

กติกาตั้งก่อนดูผล: docs/S1_GISTDA_CROSSCHECK_PREREG.md · ไม่มีเกณฑ์ผ่าน/ตก · ไม่แก้ตัวเลขที่เผยแพร่
รัน: python analysis/goal6_s1_gistda_crosscheck.py
ผลลัพธ์: analysis/goal6/s1_gistda_crosscheck.json · analysis/goal6/s1_gistda_crosscheck.md
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from shapely.geometry import shape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal6_s1_stage2_water import load_db, mosaic_db  # noqa: E402  (ภาพอ้างอิงรวมชิ้นส่วน · ตัวโหลดฉากเดียวกับขั้นที่ 2)

ROOT = Path(__file__).resolve().parent.parent
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
STAGE2 = ROOT / "data/22_goal6_network/derived/s1_stage2"
GPROV = ROOT / "data/12_gistda_flood/raw/provinces"
OUT_JSON = ROOT / "analysis/goal6/s1_gistda_crosscheck.json"
OUT_MD = ROOT / "analysis/goal6/s1_gistda_crosscheck.md"
CELL_KM2 = 0.0009
LOW_PRECISION = 0.50                       # ถ้อยคำบรรยายเท่านั้น (กติกาข้อ 3)
# ชื่อจังหวัดในชั้น GISTDA (ไทย) → รหัสจังหวัดมาตรฐานในชั้นขอบเขตจังหวัดทั้งประเทศของมิตรเอิร์ธ
PROVINCES = {"กรุงเทพมหานคร": 10, "สมุทรปราการ": 11, "นนทบุรี": 12, "ปทุมธานี": 13, "พระนครศรีอยุธยา": 14, "อ่างทอง": 15, "ลพบุรี": 16,
             "สิงห์บุรี": 17, "ชัยนาท": 18, "สระบุรี": 19, "ฉะเชิงเทรา": 24, "ปราจีนบุรี": 25, "นครนายก": 26, "นครสวรรค์": 60, "สุพรรณบุรี": 72}
KMZ = ROOT / "data/10_mitrearth_gis/thailand_national_full/22 GE Bound Province District Subdistrict/2-1 Province Boundary - mitrearth.kmz"


def latest_file(thai: str) -> Path | None:
    """ฉบับดึงล่าสุดของจังหวัด: ไฟล์ที่มีวันที่ท้ายชื่อมากสุด ไม่มีวันที่ = ฉบับเก่าสุด"""
    def key(p: Path) -> str:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
        return m.group(1) if m else "0000-00-00"
    cands = sorted(GPROV.glob(f"{thai}_30days*.json"), key=key)
    return cands[-1] if cands else None


def province_polygons() -> dict:
    """รหัสจังหวัด → รูปหลายเหลี่ยมรวม จากชั้นขอบเขตจังหวัดทั้งประเทศ (ชั้น pbound รายจังหวัดถูกตัดตามกรอบแผนที่ ใช้ไม่ได้ — ดูข้อ 5 ของกติกา)"""
    import tempfile
    import zipfile
    with tempfile.TemporaryDirectory() as td:
        zipfile.ZipFile(KMZ).extractall(td)
        g = gpd.read_file(glob.glob(td + "/*.kml")[0])
    g["code"] = g["description"].map(lambda s: int(re.search(r"PRV_CODE</td>\s*<td>(\d+)", s).group(1)))
    return {int(c): d.geometry.union_all() for c, d in g.groupby("code")}


def rasterize_geoms(geoms, grid):
    tr = from_bounds(grid["x0"], grid["y0"], grid["x1"], grid["y1"], grid["nx"], grid["ny"])
    geoms = [g for g in geoms if g is not None and not g.is_empty]
    if not geoms:
        return np.zeros((grid["ny"], grid["nx"]), bool)
    return rasterize([(g, 1) for g in geoms], out_shape=(grid["ny"], grid["nx"]), transform=tr, fill=0, dtype="uint8").astype(bool)


def prf(s1, gis):
    tp = float((s1 & gis).sum())
    p = tp / max(float(s1.sum()), 1.0)
    r = tp / max(float(gis.sum()), 1.0)
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0,
            "radar_km2": round(float(s1.sum()) * CELL_KM2, 1), "gistda_km2": round(float(gis.sum()) * CELL_KM2, 1),
            "ratio_radar_to_gistda": round(float(s1.sum()) / max(float(gis.sum()), 1.0), 2)}


def main() -> None:
    summ = json.loads((STAGE2 / "summary.json").read_text(encoding="utf-8"))
    polys = province_polygons()
    gcache, res = {}, {}
    for bid, rec in summ.items():
        grid = json.loads((STAGE1 / f"grid_{bid}.json").read_text(encoding="utf-8"))
        low = np.load(STAGE1 / f"mask_lowland_{bid}.npy")
        bbox = (grid["x0"], grid["y0"], grid["x1"], grid["y1"])
        use = []
        for thai, code in PROVINCES.items():
            geom = polys.get(code)
            if geom is None or geom.bounds[2] < bbox[0] or geom.bounds[0] > bbox[2] or geom.bounds[3] < bbox[1] or geom.bounds[1] > bbox[3]:
                continue
            f = latest_file(thai)
            if f is not None:
                use.append((thai, geom, f))
        if not use:
            res[bid] = {"status": "no_comparable_province"}
            continue
        dom_prov = rasterize_geoms([u[1] for u in use], grid)
        gis_geoms = []
        for thai, _geom, f in use:
            if f not in gcache:
                gcache[f] = [shape(x["geometry"]) for x in json.loads(f.read_text(encoding="utf-8")) if x.get("geometry")]
            gis_geoms += gcache[f]
        gis = rasterize_geoms(gis_geoms, grid)
        scenes = [r for r in rec["scenes"] if r["reference"] != r["scene"]]
        pk = max(scenes, key=lambda r: r["water_km2_lowland"])
        masks = {}
        for label, sel in (("A_peak_scene", [pk]), ("B_union_all_scenes", scenes)):
            w = np.zeros(low.shape, bool)
            foot = np.zeros(low.shape, bool)
            for r in sel:
                w |= np.load(STAGE2 / bid / f"{r['scene']}_water.npy")
                post = load_db(bid, r["scene"], "vh")
                pre = mosaic_db(bid, r["reference_all"], "vh")
                foot |= np.isfinite(post) & np.isfinite(pre)
            dom = low & foot & dom_prov
            m = prf(w & dom, gis & dom)
            m["domain_km2"] = round(float(dom.sum()) * CELL_KM2, 1)
            m["radar_total_km2_whole_grid"] = round(float((w & low).sum()) * CELL_KM2, 1)      # พื้นที่เรดาร์ทั้งกริดลุ่ม (รวมจังหวัดที่ไม่มีชั้น GISTDA)
            m["share_of_radar_in_domain"] = round(m["radar_km2"] / max(m["radar_total_km2_whole_grid"], 0.1), 3)
            m["label_low_precision"] = bool(m["precision"] < LOW_PRECISION)
            masks[label] = m
        res[bid] = {"status": "ok", "provinces": [u[0] for u in use], "gistda_files": [u[2].name for u in use], "peak_scene": pk["scene"][12:40], **masks}
        print(bid, {k: (v["precision"], v["recall"], v["radar_km2"], v["gistda_km2"]) for k, v in masks.items()}, flush=True)
    OUT_JSON.write_text(json.dumps({"rule": "docs/S1_GISTDA_CROSSCHECK_PREREG.md", "basins": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# เทียบพื้นที่น้ำเรดาร์กับ GISTDA 30 วัน (หลังจับฉากอ้างอิงตามวงโคจรสัมพัทธ์)", "",
         "> กติกา `docs/S1_GISTDA_CROSSCHECK_PREREG.md` (ตั้งก่อนคำนวณ) · GISTDA 30 วันเป็นผลสะสมหลายฉากหลายดาวเทียม ไม่ใช่ความจริงภาคสนาม · ไม่มีเกณฑ์ผ่าน/ตก", "",
         "| ลุ่ม | มาสก์เรดาร์ | ความแม่น | ความครบ | F1 | เรดาร์ (ตร.กม.) | GISTDA (ตร.กม.) | อัตราส่วน | โดเมน (ตร.กม.) |", "|---|---|---|---|---|---|---|---|---|"]
    for b, v in res.items():
        if v["status"] != "ok":
            L.append(f"| {b} | เทียบไม่ได้ (ไม่มีชั้น GISTDA ของจังหวัดในลุ่ม) | | | | | | | |")
            continue
        for k in ("A_peak_scene", "B_union_all_scenes"):
            m = v[k]
            L.append(f"| {b} | {k} | {m['precision']:.0%} | {m['recall']:.0%} | {m['f1']:.2f} | {m['radar_km2']} | {m['gistda_km2']} | {m['ratio_radar_to_gistda']} | {m['domain_km2']} |")
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
