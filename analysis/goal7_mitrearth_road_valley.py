"""จุดที่ถนนตัดร่องน้ำ (ชั้น Valley_X_Road_Point ของมิตรเอิร์ธ) และจุดเสี่ยงน้ำตัดถนน ในอำเภอองครักษ์ — ชั้นสุดท้ายที่ยังไม่ได้ใช้ของ R7-14
คำถาม: ถนน (รวมทางหลวง 305) ตัดร่องน้ำที่จุดใดในแอ่งองครักษ์ และพื้นดินตรงจุดเหล่านั้นอยู่ต่ำกว่าระดับน้ำจริง (TNy10 +2.35 ม.รทก.) กี่จุด
วิธี: อ่านจุด (ถนนตัดร่องน้ำ) ทั้งจังหวัด → เลือกจุดในอำเภอองครักษ์ด้วยหน้ากากอำเภอ → สุ่มความสูงพื้นดิน FABDEM ดิบ และ FABDEM ที่ปรับแบบต่อเนื่อง (กติกา docs/DEM_CORRECTION_PREREG.md) → นับจุดต่ำกว่าระดับน้ำจริง · แยกเฉพาะทางหลวง 305
ข้อจำกัด (สำคัญ): ความสูงนี้คือ **พื้นดินเปล่า** ไม่ใช่ระดับผิวถนน — ถนนมีคันสูงกว่าพื้นดิน จึงบอกไม่ได้ว่าน้ำล้นถนนที่ระดับใด (ช่องว่าง route305_crown_elevation ยังเปิด) · ค่า ELEVATION ในชั้นมิตรเอิร์ธเองสูงกว่าเส้นชั้นความสูงจริงราว 4 ม. (ดู mitrearth_layers_summary) จึงไม่ใช้
สิทธิ์ใช้งานข้อมูล: ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์ · รายงานเฉพาะจำนวนและช่วงความสูง ไม่ระบุชื่อบุคคล
รัน: python analysis/goal7_mitrearth_road_valley.py
ผลลัพธ์: analysis/goal7/mitrearth_road_valley.json
"""
from __future__ import annotations

import glob
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import rasterio
import shapefile  # pyshp

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal7_fabdem_compare import FAB, sampler  # noqa: E402  (reuse-first)
import goal7_dem_bias_correction as bc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DER = ROOT / "data/13_sentinel1_copernicus/derived"
OUT = ROOT / "analysis/goal7/mitrearth_road_valley.json"
BIAS = ROOT / "analysis/goal7/dem_bias_correction.json"
GRID = json.loads((DER / "grid.json").read_text(encoding="utf-8"))
TR = rasterio.transform.from_origin(GRID["x0"], GRID["y1"], GRID["res"], GRID["res"])
STAGE_OBS = 2.35        # TNy10 17 ต.ค. 69 ม.รทก. (ค่าเดียวกับ goal7_ongkharak_2d_depression)


def in_mask(mask: np.ndarray, lon: float, lat: float) -> bool:
    r, c = rasterio.transform.rowcol(TR, lon, lat)
    return 0 <= r < mask.shape[0] and 0 <= c < mask.shape[1] and bool(mask[r, c])


def stats(v: list[float]) -> dict:
    a = np.array(v)
    return {"n": int(len(a)), "min_m": round(float(a.min()), 2), "median_m": round(float(np.median(a)), 2), "max_m": round(float(a.max()), 2)} if len(a) else {"n": 0}


def main() -> None:
    shp = glob.glob(str(ROOT / "data/10_mitrearth_gis/**/6 Road Cut Valley and Ridge/18_Valley_X_Road_Point_-_mitrearth.shp"), recursive=True)[0]
    r = shapefile.Reader(shp.replace(".shp", ""), encoding="utf-8")
    fld = [f[0] for f in r.fields[1:]]
    mask = np.load(DER / "mask_district_อำเภอองครักษ์.npy")
    knots = json.loads(BIAS.read_text(encoding="utf-8"))["monotone_correction"]["knots"]
    fab = sampler(FAB, "N{lat}E{lon}_FABDEM_V1-2.tif")
    prov_roads = Counter()
    pts = []
    for rec in r.records():
        d = dict(zip(fld, rec))
        prov_roads[d["NAME_T"]] += 1
        lon, lat = float(d["POINT_X"]), float(d["POINT_Y"])
        if in_mask(mask, lon, lat):
            f = fab(lon, lat)
            if f is not None:
                pts.append({"road": d["NAME_T"], "raw": float(f), "cor": float(bc.correct_monotone(np.array([f]), knots)[0]), "drain": d["DRAIN_AREA"]})
    hw305 = [p for p in pts if re.search(r"\b305\b|305$", p["road"] or "")]

    def block(sel: list[dict]) -> dict:
        raw, cor = [p["raw"] for p in sel], [p["cor"] for p in sel]
        return {"fabdem_raw": stats(raw), "fabdem_corrected": stats(cor),
                "below_observed_stage_raw": int(sum(v < STAGE_OBS for v in raw)), "below_observed_stage_corrected": int(sum(v < STAGE_OBS for v in cor))}
    # จุดเสี่ยงน้ำตัดถนน (KMZ)
    kmz = glob.glob(str(ROOT / "data/10_mitrearth_gis/**/18 นครนายก - จุดเสี่ยงน้ำตัดถนน - mitrearth.kmz"), recursive=True)
    risk = {"n_province": None, "n_in_district": None}
    if kmz:
        z = zipfile.ZipFile(kmz[0])
        kml = z.read([n for n in z.namelist() if n.endswith(".kml")][0]).decode("utf-8")
        coords = re.findall(r"<coordinates>\s*([-\d.]+),([-\d.]+)", kml)
        risk = {"n_province": len(coords), "n_in_district": int(sum(in_mask(mask, float(a), float(b)) for a, b in coords)), "same_layer_as_valley_x_road": len(coords) == int(sum(prov_roads.values()))}
    out = {
        "source": "ชั้น Valley_X_Road_Point และ 'จุดเสี่ยงน้ำตัดถนน' ของมิตรเอิร์ธ (ประโยชน์สาธารณะ/การศึกษา ห้ามใช้เชิงพาณิชย์)",
        "observed_stage_msl_m": STAGE_OBS,
        "province_valley_x_road_points": int(sum(prov_roads.values())),
        "in_ongkharak": {"n": len(pts), **block(pts)} if pts else {"n": 0},
        "in_ongkharak_highway_305": {"n": len(hw305), **block(hw305)} if hw305 else {"n": 0},
        "top_roads_in_ongkharak": Counter(p["road"] for p in pts).most_common(5),
        "water_cut_road_risk_points": risk,
        "caveat": "ความสูงคือพื้นดินเปล่า (FABDEM) ไม่ใช่ระดับผิวถนน — ไม่ใช้ยืนยันระดับที่น้ำล้นถนน · ช่องว่าง route305_crown_elevation ยังเปิด",
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "caveat"}, ensure_ascii=False)[:1400])


if __name__ == "__main__":
    main()
