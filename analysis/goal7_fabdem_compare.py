"""เป้าหมาย 7 — เทียบความสูงพื้นดินตามแนวคลอง: FABDEM (ดินเปล่า) vs Copernicus GLO-30 (ผิวสูงสุด) vs ค่าอ่านจากรูปตัดตามยาว

อินพุต: data/08_dem_topography/fabdem/*.tif (FABDEM V1-2) · data/08_dem_topography/raw/Copernicus_DSM_COG_10_*.tif
        data/32_goal7_chaophraya2/derived/{centerline,km_markers}.geojson · analysis/goal7/canonical.json (eia_profile.ground_readings)
เอาต์พุต: analysis/goal7/fabdem_compare.json
หมายเหตุ: FABDEM ไม่ใช่ข้อมูลสำรวจ (≈30 ม.) ใช้เทียบ/ตรวจความสมเหตุสมผลเท่านั้น
"""
import json
import statistics as st
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent.parent
FAB = ROOT / "data/08_dem_topography/fabdem"
GLO = ROOT / "data/08_dem_topography/raw"
D7 = ROOT / "data/32_goal7_chaophraya2/derived"
OUT = ROOT / "analysis/goal7/fabdem_compare.json"


def sampler(pattern_dir, fmt):
    ds = {}
    for lat in (13, 14, 15):
        for lon in (100, 101):
            p = pattern_dir / fmt.format(lat=lat, lon=lon)
            if p.exists():
                ds[(lat, lon)] = rasterio.open(p)

    def f(lon, lat):
        d = ds.get((int(lat), int(lon)))
        if d is None:
            return None
        v = next(d.sample([(lon, lat)]))[0]
        return None if v is None or v < -100 or np.isnan(v) else float(v)
    return f


def main():
    fab = sampler(FAB, "N{lat}E{lon}_FABDEM_V1-2.tif")
    glo = sampler(GLO, "Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM.tif")
    mk = json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]
    pts = sorted((f["properties"]["km"], *f["geometry"]["coordinates"]) for f in mk)
    can = json.loads((ROOT / "analysis/goal7/canonical.json").read_text(encoding="utf-8"))
    hand = {r[0]: r[1] for r in can["eia_profile"]["ground_readings"]} if isinstance(can["eia_profile"]["ground_readings"][0], list) else {r["km"]: r["ground_m"] for r in can["eia_profile"]["ground_readings"]}
    rows = []
    for km, lon, lat in pts:
        if km != int(km) or int(km) % 5:
            continue
        a, b = fab(lon, lat), glo(lon, lat)
        if a is None or b is None:
            continue
        h = float(np.interp(km, sorted(hand), [hand[k] for k in sorted(hand)])) if hand else None
        rows.append({"km": int(km), "fabdem_m": round(a, 2), "glo30_m": round(b, 2), "hand_read_m": None if h is None else round(h, 2),
                     "glo30_minus_fabdem_m": round(b - a, 2), "fabdem_minus_hand_m": None if h is None else round(a - h, 2)})
    nn = [r for r in rows if 38 <= r["km"] <= 74]
    summ = {}
    for key in ("glo30_minus_fabdem_m", "fabdem_minus_hand_m"):
        v = [r[key] for r in nn if r[key] is not None]
        if v:
            summ[key] = {"n": len(v), "mean": round(st.mean(v), 2), "median": round(st.median(v), 2), "min": min(v), "max": max(v)}
    crest = {r["km"]: r["crest_m"] for r in can["eia_profile"]["rows"]}
    ca = [crest[r["km"]] - r["fabdem_m"] for r in rows if 40 <= r["km"] <= 70 and r["km"] in crest]
    summ["crest_above_fabdem_km40_70_m"] = {"n": len(ca), "min": round(min(ca), 1), "max": round(max(ca), 1)} if ca else None
    out = {"note": "FABDEM V1-2 ≈30 ม. ไม่ใช่ข้อมูลสำรวจ · จุดคือหมุด กม. ทุก 5 กม. · ช่วงนครนายก กม.38–74", "rows": rows, "summary_nn_reach": summ}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False))
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
