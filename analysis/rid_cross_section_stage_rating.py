# ตรวจไขว้ rating curve แบบเต็มช่วงระดับน้ำ + ขยายหน้าตัดด้วย Copernicus DEM
#
# ปิดข้อ 4 ของ analysis/rid_cross_section_findings.md ที่ค้างว่า "ยังไม่สรุปได้ เพราะหน้าตัด
# ถูกตัดที่ระดับพีค" — ทำ 3 อย่าง:
#   (A) สกัดหน้าตัด "หลายปี" จากไฟล์ RID เดียวกัน (2565/2566/2567/2568) → เทียบการเปลี่ยนท้องน้ำ
#   (B) ขยายหน้าตัด 2568 ด้วย Copernicus DEM 30 ม. ต่อออกนอกช่วงสำรวจ (-60 ฝั่งซ้าย / +150 ฝั่งขวา)
#       โดยหาทิศตั้งฉากกับแนวแม่น้ำ (OSM waterways) ที่พิกัดสถานี Ny.7 (101.2193, 14.2005)
#   (C) สร้าง rating curve จากเรขาคณิต (Manning) ตลอดช่วงระดับน้ำ แล้วเทียบกับ Q = 242(h-4.55)^0.66
#       ของโปรเจค — ไม่ใช่แค่ที่พีค
#
# ข้อจำกัดที่ต้องคงไว้: DEM = DSM (ผิวน้ำ/ยอดพืชพรรณ ไม่ใช่ท้องน้ำ) → ใช้ได้เฉพาะ "ที่ราบน้ำท่วมถึง"
#   ห้ามใช้ DEM แทนท้องน้ำในช่วงสำรวจ · ช่วง DEM 30 ม. หยาบกว่าหน้าตัดสำรวจ (10 ม.) 3 เท่า
import json
import math
from pathlib import Path

import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parent.parent
DER19 = ROOT / "data" / "19_rid_cross_sections" / "derived"
RAW = ROOT / "data" / "19_rid_cross_sections" / "raw"
DER13 = ROOT / "data" / "13_sentinel1_copernicus" / "derived"

SLOPE = 9.0 / 28000.0        # m/m จากโปรไฟล์แม่น้ำของโปรเจค
GAUGE_OFFSET = 1.59          # เกจ = ม.รทก. + 1.59
N_MANNING = 0.035            # ค่ากลางสำหรับที่ราบลุ่ม tropical

# ระวังหน่วย: ต้องเป็น "เมตร/องศา" — ถ้าเผลอใช้ กม./องศา (111.32) ระยะ 350 ม. จะกลายเป็น ~340 กม.
M_PER_DEG_LAT = 111320.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(14.24))  # ม./องศา lon (เดิมหาร cos = ยาวเกิน 6.1%)

# คอลัมน์ปีสำรวจในไฟล์ RID (1-based): (ปี พ.ศ., offset_col, elev_col)
YEAR_COLS = [(2568, 18, 19), (2567, 20, 21), (2565, 22, 23), (2566, 26, 27)]

STATIONS = {
    "Ny.7": {"peak_msl": 7.64, "peak_gauge": 9.23, "lon": 101.2193, "lat": 14.2005},
    "Ny.1B": {"peak_msl": 11.07, "peak_gauge": 11.0, "lon": None, "lat": None},
}


# ---------- (A) สกัดหน้าตัดหลายปี ----------

def parse_year(path, off_col, elev_col):
    """อ่าน (offset_m, elev_msl_m) จากคอลัมน์ที่ระบุ · ข้ามแถวหัวตาราง"""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    pts = []
    for r in range(2, ws.max_row + 1):
        e = ws.cell(r, elev_col).value
        o = ws.cell(r, off_col).value
        if isinstance(e, (int, float)) and isinstance(o, (int, float)):
            pts.append((float(o), float(e)))
    pts.sort()
    return np.array(pts) if pts else None


def ground(xs, ys, x):
    return np.interp(x, xs, ys)


def geometry(xs, ys, stage, dx=0.25):
    """ความกว้างผิวน้ำ / พื้นที่เปียก / เส้นรอบเปียก ที่ระดับ stage (ม.รทก.)

    ระวังเส้นรอบเปียก: อย่าใช้ width + (span) ≈ 2 เท่าของความกว้างผิวน้ำ
    เพราะนับ "ผิวน้ำอิสระ" เข้าไปด้วย — ตามมาตรฐาน (และ HEC-RAS) ต้องเป็น "ขอบเปียกแข็ง"
    = ความยาวผิวดินที่จมน้ำ + หน้าตัดแนวตั้งสองข้าง **ไม่รวมผิวน้ำอิสระ**
    ถ้านับผิวน้ำ R จะต่ำเกิน ~2 เท่า → Q ต่ำเกิน 1.63 เท่า → ได้ n ต่ำผิดปกติ (0.027)
    """
    grid = np.arange(xs.min(), xs.max() + dx, dx)
    g = ground(xs, ys, grid)
    depth = np.clip(stage - g, 0.0, None)
    area = float(depth.sum() * dx)
    wet = depth > 0
    width = float(wet.sum() * dx)
    perim = 0.0
    idx = np.where(wet)[0]
    if len(idx):
        for k in range(len(idx) - 1):
            if idx[k + 1] == idx[k] + 1:
                perim += math.hypot(dx, g[idx[k + 1]] - g[idx[k]])
        perim += float(depth[idx[0]] + depth[idx[-1]])   # หน้าตัดแนวตั้งสองข้าง
    return width, area, perim


def manning_q(area, perim, n=N_MANNING):
    if area <= 0 or perim <= 0:
        return 0.0
    R = area / perim
    return (1.0 / n) * area * (R ** (2.0 / 3.0)) * (SLOPE ** 0.5)


def manning_compound(xs, ys, stage, dx=0.25, bank_stage=6.86, n_chan=0.030, n_fp=0.055):
    """Manning แบบภาคผสม (divided channel): แยก 'ร่องน้ำ' กับ 'ที่ราบน้ำท่วมถึง'
    แล้วรวม conveyance K = Σ (1/n)·A·R^(2/3) · Q = K·√S
    เหตุผล: Manning ใช้ n เดียวจะลงโทษที่ราบกว้าง-ตื้นเกินจริง (wetted perimeter โตเร็ว)
    n_chan 0.030 (ร่องน้ำธรรมชาติ), n_fp 0.055 (ที่ราบมีพืช/สิ่งกีดขวาง) — ค่ามาตรฐานช่วงกว้าง"""
    grid = np.arange(xs.min(), xs.max() + dx, dx)
    g = ground(xs, ys, grid)
    depth = np.clip(stage - g, 0.0, None)
    chan = (g <= bank_stage) & (depth > 0)      # คอลัมน์ที่เป็น "ร่องน้ำ"
    fp = (g > bank_stage) & (depth > 0)         # คอลัมน์ที่เป็น "ที่ราบท่วม"
    K = 0.0
    parts = {}
    for name, m, n in (("channel", chan, n_chan), ("floodplain", fp, n_fp)):
        if not m.any():
            parts[name] = {"area_m2": 0.0, "width_m": 0.0, "conveyance": 0.0}
            continue
        a = float(depth[m].sum() * dx)
        w = float(m.sum() * dx)
        idx = np.where(m)[0]
        # เส้นรอบเปียก = ความยาวผิวดิน + หน้าตัดแนวตั้งสองข้าง (ไม่รวมผิวน้ำอิสระ)
        p = 0.0
        if len(idx):
            for k in range(len(idx) - 1):
                if idx[k + 1] == idx[k] + 1:
                    p += math.hypot(dx, g[idx[k + 1]] - g[idx[k]])
            p += float(depth[idx[0]] + depth[idx[-1]])
        k = (1.0 / n) * a * ((a / p) ** (2.0 / 3.0)) if p > 0 else 0.0
        K += k
        parts[name] = {"area_m2": round(a, 1), "width_m": round(w, 1), "conveyance": round(k, 1)}
    parts["q_cms"] = round(K * (SLOPE ** 0.5), 1)
    return parts


def project_rating(h_msl):
    """rating curve ของโปรเจค (ใช้เฉพาะช่วง h>4.55)"""
    return 242.0 * max(h_msl - 4.55, 0.0) ** 0.66


def n_that_matches(area, perim, q_target):
    """n ที่ทำให้ Manning = q_target (แก้ด้วย bisection)"""
    if area <= 0 or perim <= 0 or q_target <= 0:
        return float("nan")
    lo, hi = 0.005, 0.50
    for _ in range(90):
        mid = (lo + hi) / 2
        if manning_q(area, perim, mid) > q_target:
            lo = mid
        else:
            hi = mid
    return lo


# ---------- (B) ขยายหน้าตัดด้วย DEM ----------

def load_dem():
    gr = json.load(open(DER13 / "grid.json", encoding="utf-8"))
    return gr, np.load(DER13 / "dem_30m.npy")


def dem_at(gr, dem, lon, lat):
    c = int((lon - gr["x0"]) / (gr["x1"] - gr["x0"]) * dem.shape[1])
    r = int((gr["y1"] - lat) / (gr["y1"] - gr["y0"]) * dem.shape[0])
    if 0 <= r < dem.shape[0] and 0 <= c < dem.shape[1]:
        z = dem[r, c]
        return float(z) if z > 0 else np.nan
    return np.nan


def river_perp_bearing(lon, lat, W):
    """มุมตั้งฉากกับแนวแม่น้ำนครนายกที่จุดใกล้ (lon,lat) ที่สุด"""
    best = None
    for r in W["rivers"]:
        if r["name"] != "แม่น้ำนครนายก":
            continue
        c = r["coords"]
        for j in range(len(c) - 1):
            (ax, ay), (bx, by) = c[j], c[j + 1]
            dx, dy = (bx - ax) * M_PER_DEG_LON, (by - ay) * M_PER_DEG_LAT
            if dx == 0 and dy == 0:
                continue
            t = max(0.0, min(1.0, ((lon - ax) * dx + (lat - ay) * dy) / (dx * dx + dy * dy)))
            d = math.hypot((lon - (ax + t * dx)) * M_PER_DEG_LON, (lat - (ay + t * dy)) * M_PER_DEG_LAT)
            if best is None or d < best[0]:
                L = math.hypot(dx, dy)
                best = (d, -dy / L, dx / L)   # หน่วย: (px, py) ต่อหนึ่งหน่วย lon/lat-scaled
    return best


def dem_profile(gr, dem, lon0, lat0, px, py, ds):
    """ค่า DEM ตามแนวภาคตัดขวาง ระยะ ds (เมตร) จากจุด (lon0,lat0)"""
    out = []
    for s in ds:
        lon = lon0 + s * px / M_PER_DEG_LON
        lat = lat0 + s * py / M_PER_DEG_LAT
        out.append(dem_at(gr, dem, lon, lat))
    return np.array(out)


def fit_align(gr, dem, lon0, lat0, px, py, xs, ys):
    """หา (sign, shift) ที่ทำให้ DEM(offset) ตรงกับหน้าตัดสำรวจมากที่สุด
    ใช้เฉพาะช่วงที่ทั้งคู่มีค่า และกรองท้องน้ำออก (survey < 1.5 ม.รทก. = ใต้ผิวน้ำที่ DSM มองไม่เห็น)"""
    ds = np.arange(-320.0, 320.5, 5.0)
    zs = dem_profile(gr, dem, lon0, lat0, px, py, ds)
    ok_dem = ~np.isnan(zs)
    best = None
    for sign in (+1, -1):
        for shift in np.arange(-120, 121, 5.0):
            # offset_survey -> ds = sign*offset + shift
            dss = sign * xs + shift
            zz = np.interp(dss, ds[ok_dem], zs[ok_dem], left=np.nan, right=np.nan)
            m = ~np.isnan(zz) & (ys > 1.5)      # เทียบเฉพาะที่ราบ/ตลิ่ง (ไม่ใช่ท้องน้ำ)
            if m.sum() < 6:
                continue
            rms = float(np.sqrt(np.mean((zz[m] - ys[m]) ** 2)))
            if best is None or rms < best[0]:
                best = (rms, sign, shift, int(m.sum()))
    return best, ds, zs


def newest(years):
    """หน้าตัดปีล่าสุด (2568 ถ้ามี ไม่งั้นปีสูงสุดที่มี) — เลี่ยง `or` บน numpy array"""
    return years[2568] if 2568 in years else years[sorted(years)[-1]]


def main():
    report = {}
    for stem, cfg in STATIONS.items():
        path = RAW / f"{stem}_2025.xlsx"
        if not path.exists():
            print(f"!! ไม่พบ {path}")
            continue
        print(f"\n{'='*72}\n===== {stem} =====")

        # --- (A) หลายปี ---
        years = {}
        for y, oc, ec in YEAR_COLS:
            pts = parse_year(path, oc, ec)
            if pts is not None and len(pts) >= 8:
                years[y] = pts
        print(f"ปีที่พบในไฟล์: {sorted(years)}")
        yr_rows = {}
        for y, pts in sorted(years.items()):
            xs, ys = pts[:, 0], pts[:, 1]
            thal = float(ys.min())
            w, a, p = geometry(xs, ys, cfg["peak_msl"])
            yr_rows[y] = {
                "n_points": int(len(pts)),
                "offset_range_m": [float(xs.min()), float(xs.max())],
                "thalweg_msl": round(thal, 3),
                "thalweg_offset_m": float(xs[int(np.argmin(ys))]),
                "crest_max_msl": round(float(ys.max()), 3),
                "area_at_peak_m2": round(a, 1),
                "width_at_peak_m": round(w, 1),
                "manning_q_at_peak_cms": round(manning_q(a, p), 1),
            }
            print(f"   {y}: {len(pts):3} pts  offset {xs.min():6.1f}..{xs.max():5.1f}  "
                  f"thalweg {thal:6.3f} ม.รทก. @ {xs[int(np.argmin(ys))]:6.1f}  "
                  f"| A@peak {a:6.1f} ตร.ม.  Q_manning@peak {manning_q(a, p):6.1f}")

        # --- (B) ขยายด้วย DEM ---
        dem_ext = None
        if cfg["lon"] is not None:
            gr, dem = load_dem()
            W = json.load(open(DER13 / "waterways.json", encoding="utf-8"))
            bearing = river_perp_bearing(cfg["lon"], cfg["lat"], W)
            if bearing:
                _, px, py = bearing
                pts = newest(years)
                xs, ys = pts[:, 0], pts[:, 1]
                best, ds, zs = fit_align(gr, dem, cfg["lon"], cfg["lat"], px, py, xs, ys)
                if best:
                    rms, sign, shift, npts = best
                    print(f"\n  DEM align: sign={sign:+d} shift={shift:+.0f} ม. "
                          f"RMS={rms:.2f} ม. (n={npts})  [เทียบเฉพาะที่ราบ >1.5 ม.รทก.]")
                    # ตรวจว่า DEM ตรงกับหน้าตัดสำรวจ "ในช่วงทับซ้อน" ได้ไหม — ถ้าไม่ ต่อปลายไม่ได้
                    dss = sign * xs + shift
                    ok = ~np.isnan(zs)
                    zz = np.interp(dss, ds[ok], zs[ok], left=np.nan, right=np.nan)
                    m = ~np.isnan(zz) & (ys > 1.5)
                    worst = float(np.max(np.abs(zz[m] - ys[m]))) if m.any() else float("nan")
                    print(f"  ในช่วงทับซ้อน: RMS {rms:.2f} ม. · คลาดสูงสุด {worst:.2f} ม. (n={npts})")
                    w0, a0, p0 = geometry(xs, ys, cfg["peak_msl"])
                    dem_ext = {
                        "sign": int(sign), "shift_m": float(shift),
                        "rms_overlap_m": round(rms, 2), "max_err_overlap_m": round(worst, 2),
                        "n_overlap": int(npts),
                        "survey_area_at_peak_m2": round(a0, 1),
                        "survey_manning_q_at_peak_cms": round(manning_q(a0, p0), 1),
                        "project_q_at_peak_cms": round(project_rating(cfg["peak_msl"]), 1),
                    }
                    # ยอมรับเฉพาะเมื่อ DEM ทำซ้ำหน้าตัดสำรวจได้ (RMS < 1 ม.) เท่านั้น
                    if rms >= 1.0:
                        dem_ext["accepted"] = False
                        dem_ext["reason"] = (
                            f"DEM (DSM) คลาดจากหน้าตัดสำรวจ {rms:.1f} ม. RMS ในช่วงทับซ้อน "
                            f"(สูงสุด {worst:.1f} ม.) — ต่อปลายจะใส่ระดับผิดเข้าหน้าตัด จึงปฏิเสธ")
                        print(f"  ❌ ปฏิเสธการต่อปลาย: RMS {rms:.2f} ม. ≥ 1.0 — DSM ไม่ตรงกับหน้าตัดสำรวจจริง")
                    else:
                        left = [(float(sign * (d - shift)), float(z))
                                for d, z in zip(ds[ok], zs[ok])
                                if sign * (d - shift) < xs.min() - 2]
                        right = [(float(sign * (d - shift)), float(z))
                                 for d, z in zip(ds[ok], zs[ok])
                                 if sign * (d - shift) > xs.max() + 2]
                        comb = np.array(sorted(left + [(float(x), float(y)) for x, y in pts] + right))
                        w1, a1, p1 = geometry(comb[:, 0], comb[:, 1], cfg["peak_msl"])
                        dem_ext.update({
                            "accepted": True,
                            "n_left_added": len(left), "n_right_added": len(right),
                            "offset_range_m": [float(comb[:, 0].min()), float(comb[:, 0].max())],
                            "area_at_peak_m2": round(a1, 1),
                            "manning_q_at_peak_cms": round(manning_q(a1, p1), 1),
                        })
                        print(f"  ✅ ต่อปลายซ้าย {len(left)} จุด · ขวา {len(right)} จุด → "
                              f"offset {comb[:, 0].min():.0f}..{comb[:, 0].max():.0f} ม. · "
                              f"A@peak {a0:.1f}→{a1:.1f} · Q {manning_q(a0, p0):.1f}→{manning_q(a1, p1):.1f}")

        # --- (C) rating curve เต็มช่วง ---
        pts = newest(years)
        xs, ys = pts[:, 0], pts[:, 1]
        stage_lo = float(math.ceil(ys.min()))
        stage_hi = float(np.floor(ys.max() * 2) / 2)
        curve = []
        for stage in np.arange(max(stage_lo, 4.0), stage_hi + 0.01, 0.5):
            w, a, p = geometry(xs, ys, stage)
            qm = manning_q(a, p)
            qp = project_rating(stage)
            comp = manning_compound(xs, ys, stage)
            curve.append({
                "stage_msl": round(float(stage), 2),
                "gauge_m": round(float(stage) + GAUGE_OFFSET, 2),
                "width_m": round(w, 1),
                "area_m2": round(a, 1),
                "manning_q_cms": round(qm, 1),
                "manning_compound_q_cms": comp["q_cms"],
                "project_q_cms": round(qp, 1),
                "ratio_manning_over_project": round(qm / qp, 3) if qp > 1 else None,
                "ratio_compound_over_project": round(comp["q_cms"] / qp, 3) if qp > 1 else None,
                "n_to_match_project": round(n_that_matches(a, p, qp), 4) if qp > 1 else None,
            })
        print(f"\n  --- rating curve เต็มช่วง (n เดี่ยว={N_MANNING} · ภาคผสม n_chan=0.030/n_fp=0.055) ---")
        print("   stage(ม.รทก.)  เกจ   กว้าง    A      Q_nเดียว  Q_ผสม  Q_โปรเจค  n_ที่ต้องใช้")
        for r in curve:
            print(f"   {r['stage_msl']:8.2f} {r['gauge_m']:7.2f} {r['width_m']:7.1f} {r['area_m2']:8.1f}"
                  f" {r['manning_q_cms']:9.1f} {r['manning_compound_q_cms']:7.1f} {r['project_q_cms']:9.1f}"
                  f" {(r['n_to_match_project'] or 0):10.4f}")

        # --- (D) ความไวของ Manning ต่อค่า n ที่ระดับพีค ---
        w_p, a_p, per_p = geometry(xs, ys, cfg["peak_msl"])
        qp_peak = project_rating(cfg["peak_msl"])
        n_match = n_that_matches(a_p, per_p, qp_peak)
        print(f"\n  --- ณ พีค {cfg['peak_msl']} ม.รทก. (เกจ {cfg['peak_gauge']}) ---")
        print(f"    A={a_p:.0f} ตร.ม. · เส้นรอบเปียก {per_p:.0f} ม. · R={a_p/per_p:.2f} ม.")
        print(f"    Q_manning n เดี่ยว (0.035) = {manning_q(a_p, per_p):.0f} ม³/วิ · rating โปรเจค = {qp_peak:.0f}")
        print(f"    -> n ที่ทำให้ตรง rating = {n_match:.4f}  (ช่วงปกติของที่ราบลุ่ม = 0.04–0.07)")
        sens = []
        for nch in (0.030, 0.035, 0.040):
            for nfp in (0.045, 0.055, 0.070):
                q = manning_compound(xs, ys, cfg["peak_msl"], n_chan=nch, n_fp=nfp)["q_cms"]
                sens.append({"n_chan": nch, "n_fp": nfp, "q_cms": q})
        qs = [s["q_cms"] for s in sens]
        print(f"    ภาคผสม (n_chan 0.030–0.040 × n_fp 0.045–0.070): Q = {min(qs):.0f}–{max(qs):.0f} ม³/วิ "
              f"→ {'คลุม rating' if min(qs) <= qp_peak <= max(qs) else 'สูงกว่า rating'}")

        report[stem] = {
            "peak_stage_msl": cfg["peak_msl"],
            "peak_gauge_m": cfg["peak_gauge"],
            "years": yr_rows,
            "dem_extension": dem_ext,
            "rating_curve": curve,
            "peak_geometry": {"area_m2": round(a_p, 1), "perimeter_m": round(per_p, 1),
                              "hydraulic_radius_m": round(a_p / per_p, 2)},
            "n_single_to_match_project": round(n_match, 4),
            "compound_sensitivity_at_peak": sens,
            "slope_m_per_m": SLOPE,
            "manning_n_used": N_MANNING,
        }

    out = ROOT / "analysis" / "rid_cross_section_stage_rating.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
