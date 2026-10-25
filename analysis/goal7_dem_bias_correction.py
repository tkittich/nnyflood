"""เป้าหมาย 7 — ปรับความสูง FABDEM/Copernicus (30 ม.) ให้ใกล้ DEM 5 ม. (DEMPro) ในที่ราบต่ำ แล้วตรวจกับเส้นดินธรรมชาติใน EIA ตลอดแนวคลอง (นอกหน้าต่าง DEMPro)

เหตุผล: DEMPro (5 ม.) ใกล้ดิน EIA ที่สุด (ต่าง ~0.4 ม.) แต่ครอบแนวคลองเพียง ~10 กม. จาก 135.9 กม. ส่วนที่เหลือต้องใช้ DEM 30 ม. ซึ่งสูงกว่าพื้นราว 1.2–1.8 ม. ในที่ราบต่ำ ·
วิธี: ในหน้าต่าง DEMPro ของจังหวัดที่อยู่ในไทล์ FABDEM/Copernicus ที่มี (ที่ราบเจ้าพระยาตอนล่าง) เทียบค่า FABDEM−DEMPro เป็นรายช่วงความสูง → แบบจำลองส่วนต่างเป็นฟังก์ชันของความสูง FABDEM เอง
(ใช้ได้ที่ไม่มี DEMPro) → ตรวจนอกตัวอย่างด้วยการตัดทีละหน้าต่าง (leave-one-window-out) และกับเส้นดิน EIA 2.3.2-9 ทั้ง 24 จุดตลอดแนวคลอง
ข้อจำกัด: DEMPro ไม่ใช่การสำรวจอิสระ (ที่มาไม่ระบุ) · ส่วนต่างขึ้นกับสิ่งปกคลุม (ป่า/อาคาร/นา) ซึ่งแบบจำลองนี้ไม่รู้ · แนวคลองจากหมุดคลาด ~0.5 กม. · ดิน EIA อ่านจากรูป ±0.2 ม. · ใช้ได้เฉพาะที่ราบต่ำ (FABDEM < 15 ม.)

รัน: python analysis/goal7_dem_bias_correction.py
ผลลัพธ์: analysis/goal7/dem_bias_correction.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
from goal7_fabdem_compare import FAB, GLO, sampler  # noqa: E402  (reuse-first)

PROVS = ROOT / "data/10_mitrearth_gis/thailand_provinces_full"
GEOM = ROOT / "analysis/goal7/official_geometry.json"
CANON = ROOT / "analysis/goal7/canonical.json"
OUT = ROOT / "analysis/goal7/dem_bias_correction.json"
BINS = [(-5, 1), (1, 2), (2, 3), (3, 5), (5, 8), (8, 15)]
STEP = 40      # ทุก 40 เซลล์ DEMPro (~200 ม.) · เฉลี่ยกล่อง 6×6 เซลล์ (~30 ม.) ให้พื้นที่เท่าเซลล์ FABDEM
TO_WGS = Transformer.from_crs(32647, 4326, always_xy=True).transform
FABS = sampler(FAB, "N{lat}E{lon}_FABDEM_V1-2.tif")
GLOS = sampler(GLO, "Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM.tif")


def windows():
    for d in sorted(PROVS.iterdir()):
        if not re.match(r"^\d+ ", d.name) or d.name.startswith("0 "):
            continue
        num = d.name.split()[0]
        gf = next((x for x in d.iterdir() if x.is_dir() and x.name.startswith(num + " ") and "GIS" not in x.name and "GE" not in x.name), None)
        dp = next(iter((gf / "GIS File").glob("*DEMPro*.grd")), None) if gf and (gf / "GIS File").exists() else None
        if dp:
            yield d.name, dp


def sample_window(dp: Path):
    ds = rasterio.open(dp)
    a = ds.read(1).astype("float32")
    a[a > 1e10] = np.nan
    rows = []
    for r in range(3, ds.height - 3, STEP):
        for c in range(3, ds.width - 3, STEP):
            box = a[r - 3:r + 3, c - 3:c + 3]
            if np.isnan(box).any():
                continue
            lon, lat = ds.xy(r, c)
            f, g = FABS(lon, lat), GLOS(lon, lat)
            if f is None or g is None:
                continue
            rows.append((float(box.mean()), float(f), float(g)))
    return np.array(rows)


def bias_table(arr: np.ndarray) -> dict:
    """ส่วนต่าง FABDEM − DEMPro ตามช่วงความสูงของ FABDEM"""
    out = {}
    for lo, hi in BINS:
        m = (arr[:, 1] >= lo) & (arr[:, 1] < hi)
        if m.sum() >= 30:
            d = arr[m, 1] - arr[m, 0]
            g = arr[m, 2] - arr[m, 0]
            out[f"{lo}..{hi}"] = {"n": int(m.sum()), "fabdem_minus_dempro_median_m": round(float(np.median(d)), 2), "sd_m": round(float(d.std()), 2), "glo30_minus_dempro_median_m": round(float(np.median(g)), 2)}
    return out


def correct(f: np.ndarray, table: dict, which: str = "fabdem_minus_dempro_median_m") -> np.ndarray:
    out = f.copy()
    for key, v in table.items():
        lo, hi = (float(x) for x in key.split(".."))
        m = (f >= lo) & (f < hi)
        out[m] = f[m] - v[which]
    return out


TAPER_END_M = 30.0      # กติกา §1.4: ส่วนต่างลดเป็นศูนย์เป็นเส้นตรงถึงความสูง FABDEM นี้


def _pav(y: list, w: list) -> list:
    """ถดถอยไอโซโทนิก (pool-adjacent-violators) ให้ y ไม่ลดลง — กติกา §1.2"""
    blocks = [[float(v), float(c), 1] for v, c in zip(y, w)]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] > blocks[i + 1][0]:
            a, b = blocks[i], blocks[i + 1]
            wsum = a[1] + b[1]
            blocks[i] = [(a[0] * a[1] + b[0] * b[1]) / wsum, wsum, a[2] + b[2]]
            del blocks[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    out = []
    for v, _, n in blocks:
        out += [v] * n
    return out


def monotone_knots(arr: np.ndarray) -> dict:
    """จุดผูกของการปรับแบบต่อเนื่อง: (มัธยฐาน FABDEM, มัธยฐาน DEMPro) ต่อช่วงความสูง แล้วบังคับ y ไม่ลดลง — กติกา §1.1–1.2"""
    xs, ys, ws = [], [], []
    for lo, hi in BINS:
        m = (arr[:, 1] >= lo) & (arr[:, 1] < hi)
        if m.sum() >= 30:
            xs.append(float(np.median(arr[m, 1])))
            ys.append(float(np.median(arr[m, 0])))
            ws.append(int(m.sum()))
    return {"x": [round(v, 3) for v in xs], "y": [round(v, 3) for v in _pav(ys, ws)], "n": ws}


def correct_monotone(f: np.ndarray, knots: dict) -> np.ndarray:
    """ปรับความสูง FABDEM แบบต่อเนื่องและไม่ลดลงตามความสูงดิบ — กติกา §1.3–1.5 (ต่ำกว่าจุดผูกแรก: ส่วนต่างคงที่ · สูงกว่า 30 ม.: ไม่ปรับ)"""
    x = np.array(knots["x"], dtype=float)
    y = np.array(knots["y"], dtype=float)
    f = np.asarray(f, dtype=float)
    out = np.interp(f, np.concatenate([x, [TAPER_END_M]]), np.concatenate([y, [TAPER_END_M]]))
    lo = f < x[0]
    out[lo] = f[lo] - (x[0] - y[0])
    hi = f > TAPER_END_M
    out[hi] = f[hi]
    return out


def max_step_m(fn) -> float:
    """รอยกระโดดสูงสุดระหว่างจุดที่ห่างกัน 0.01 ม. บนช่วง −5..40 ม. (ผลต้อง ≤ 0.05 — เงื่อนไขที่เทสต์ตรวจ)"""
    g = np.arange(-5.0, 40.0, 0.01)
    d = np.diff(fn(g))
    return float(np.abs(d).max())


def ongkharak_bucket(table: dict, knots: dict) -> dict:
    """ถังเติมน้ำองครักษ์ด้วย FABDEM ดิบ เทียบ FABDEM ที่ปรับแล้ว: ระดับที่ให้พื้นที่เท่าเรดาร์ และพื้นที่ที่ระดับเกจ TNy10 (+2.35 ม.รทก.)"""
    import goal7_mitrearth_layers as ml
    import goal7_ongkharak_connected_fill as cf
    mask = np.load(ml.DER / "mask_district_อำเภอองครักษ์.npy")
    fab = cf.fabdem_on_grid()
    stp = correct(np.where(np.isnan(fab), 99.0, fab), table)
    stp[np.isnan(fab)] = np.nan
    cor = correct_monotone(np.where(np.isnan(fab), 99.0, fab), knots)
    cor[np.isnan(fab)] = np.nan
    out = {}
    for k, f in {"peak_27sep": np.load(ml.DER / "flood_peak_27sep1828.npy").astype(bool), "oct2_validated": np.load(ml.DER / "flood_2oct_validated.npy").astype(bool)}.items():
        sar = f & mask & ~np.isnan(fab)
        row = {"sar_km2": round(float(sar.sum()) * ml.CELL_KM2, 1)}
        for nm, dem in (("fabdem_raw", fab), ("fabdem_stepped", stp), ("fabdem_corrected", cor)):
            best = None
            for h in np.arange(-2.0, 8.0, 0.05):
                a = float((mask & (dem <= h)).sum())
                if best is None or abs(a - sar.sum()) < abs(best[1] - sar.sum()):
                    best = (round(float(h), 2), a)
            bt = mask & (dem <= best[0])
            inter, un = float((bt & sar).sum()), float((bt | sar).sum())
            row[nm] = {"effective_level_m": best[0], "offset_vs_gauge_2_35_m": round(best[0] - 2.35, 2), "iou": round(inter / un, 3), "area_at_gauge_level_km2": round(float((mask & (dem <= 2.35)).sum()) * ml.CELL_KM2, 1)}
        out[k] = row
    return out


def main() -> None:
    per = {}
    allr = []
    for name, dp in windows():
        arr = sample_window(dp)
        if len(arr) < 500:
            continue
        low = arr[arr[:, 1] < 15]
        per[name] = {"n_points": int(len(arr)), "n_lowland": int(len(low)), "fabdem_minus_dempro_lowland": {"mean_m": round(float((low[:, 1] - low[:, 0]).mean()), 2), "sd_m": round(float((low[:, 1] - low[:, 0]).std()), 2)} if len(low) else None,
                     "glo30_minus_dempro_lowland": {"mean_m": round(float((low[:, 2] - low[:, 0]).mean()), 2)} if len(low) else None, "dempro_median_m": round(float(np.median(arr[:, 0])), 1)}
        allr.append((name, arr))
        print(name[:30], per[name]["fabdem_minus_dempro_lowland"], flush=True)
    pooled = np.vstack([a for _, a in allr])
    table = bias_table(pooled)
    knots = monotone_knots(pooled)
    # ตัดทีละหน้าต่าง
    loo = {}
    for name, arr in allr:
        rest = np.vstack([a for n, a in allr if n != name])
        t = bias_table(rest)
        low = arr[arr[:, 1] < 15]
        if len(low) < 100:
            continue
        raw = low[:, 1] - low[:, 0]
        stp = correct(low[:, 1], t) - low[:, 0]
        cor = correct_monotone(low[:, 1], monotone_knots(rest)) - low[:, 0]
        loo[name] = {"raw_mae_m": round(float(np.abs(raw).mean()), 2), "stepped_mae_m": round(float(np.abs(stp).mean()), 2), "corrected_mae_m": round(float(np.abs(cor).mean()), 2),
                     "raw_bias_m": round(float(raw.mean()), 2), "stepped_bias_m": round(float(stp.mean()), 2), "corrected_bias_m": round(float(cor.mean()), 2),
                     "corrected_sd_m": round(float(cor.std()), 2)}
    gain = [v["raw_mae_m"] - v["corrected_mae_m"] for v in loo.values()]
    gain_stepped = [v["raw_mae_m"] - v["stepped_mae_m"] for v in loo.values()]
    # ตรวจกับเส้นดิน EIA ตลอดแนวคลอง (ทุกจุดที่อ่านได้ กม. ≤ 134)
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    gp = canon["eia_profile"]["ground_readings"]
    st = json.loads(GEOM.read_text(encoding="utf-8"))["stations"]
    km = np.array([s["km"] for s in st])
    rows = []
    for k, z in gp:
        if k > 134:
            continue
        i = int(np.argmin(np.abs(km - k)))
        x0, y0 = st[i]["x"], st[i]["y"]
        vals_f, vals_g = [], []
        for dx in range(-300, 301, 100):
            for dy in range(-300, 301, 100):
                lo, la = TO_WGS(x0 + dx, y0 + dy)
                f, g = FABS(lo, la), GLOS(lo, la)
                if f is not None:
                    vals_f.append(f)
                if g is not None:
                    vals_g.append(g)
        if vals_f:
            rows.append((k, z, float(np.median(vals_f)), float(np.median(vals_g))))
    arr = np.array(rows)
    eia, fab, glo = arr[:, 1], arr[:, 2], arr[:, 3]
    low = fab < 15
    cor_stp = correct(fab, table)
    cor = correct_monotone(fab, knots)
    res = {
        "method": __doc__.split("\n\n")[1].replace("\n", " "), "windows_used": len(allr), "pooled_points": int(len(pooled)), "bias_table_by_fabdem_height": table, "per_window": per,
        "leave_one_window_out": {"per_window": loo, "mean_mae_gain_m": round(float(np.mean(gain)), 2), "windows_improved": int(sum(g > 0 for g in gain)), "windows_total": len(gain),
                                 "stepped": {"mean_mae_gain_m": round(float(np.mean(gain_stepped)), 2), "windows_improved": int(sum(g > 0 for g in gain_stepped))},
                                 "corrected_mae_range_m": [min(v["corrected_mae_m"] for v in loo.values()), max(v["corrected_mae_m"] for v in loo.values())],
                                 "corrected_sd_range_m": [min(v["corrected_sd_m"] for v in loo.values()), max(v["corrected_sd_m"] for v in loo.values())]},
        "eia_ground_check": {"n_points": int(len(arr)), "n_lowland_fabdem_lt_15m": int(low.sum()),
                             "fabdem_raw": {"bias_m": round(float((fab - eia)[low].mean()), 2), "mae_m": round(float(np.abs(fab - eia)[low].mean()), 2)},
                             "fabdem_stepped": {"bias_m": round(float((cor_stp - eia)[low].mean()), 2), "mae_m": round(float(np.abs(cor_stp - eia)[low].mean()), 2)},
                             "fabdem_corrected": {"bias_m": round(float((cor - eia)[low].mean()), 2), "mae_m": round(float(np.abs(cor - eia)[low].mean()), 2)},
                             "copernicus_raw": {"bias_m": round(float((glo - eia)[low].mean()), 2), "mae_m": round(float(np.abs(glo - eia)[low].mean()), 2)},
                             "rows_km_eia_fab_corrected": [[round(float(a), 1), round(float(b), 2), round(float(c), 2), round(float(d), 2)] for a, b, c, d in zip(arr[:, 0], eia, fab, cor)]},
    }
    res["monotone_correction"] = {"rule": "docs/DEM_CORRECTION_PREREG.md (ตั้งก่อนดูผล 25 ต.ค. 69)", "knots": knots, "taper_end_m": TAPER_END_M,
                                  "max_step_m": round(max_step_m(lambda g: correct_monotone(g, knots)), 3), "max_step_stepped_table_m": round(max_step_m(lambda g: correct(g, table)), 2)}
    res["ongkharak_bucket"] = ongkharak_bucket(table, knots)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ongkharak", json.dumps(res["ongkharak_bucket"], ensure_ascii=False))
    print("table", table)
    print("LOO", res["leave_one_window_out"]["mean_mae_gain_m"], res["leave_one_window_out"]["windows_improved"], "/", res["leave_one_window_out"]["windows_total"])
    print("EIA", res["eia_ground_check"]["fabdem_raw"], res["eia_ground_check"]["fabdem_corrected"], res["eia_ground_check"]["copernicus_raw"], "n", res["eia_ground_check"]["n_lowland_fabdem_lt_15m"])


if __name__ == "__main__":
    main()
