"""แบบจำลองชลศาสตร์ 2 มิติแบบจำกัดความเร็ว (local-inertial · Bates 2010) ของที่ราบองครักษ์ แทนถังเติมน้ำ: น้ำเข้าจากอัตราไหลที่ Ny.7 (เมืองนครนายก) ไหลตามลำน้ำและล้นตลิ่งตามความสูงพื้นดิน
คำถามที่ตั้งก่อนดูผล: (1) แบบจำลองไหลที่มีเวลา สองค่าปรับ (ความลึกร่องน้ำ D · ค่าความขรุขระที่ราบน้ำท่วม n) ทำนายพื้นที่น้ำท่วมที่ดาวเทียมเห็น 27 ก.ย. และ 2 ต.ค. ได้ดีกว่าถังเติมน้ำ (IoU 0.31/0.25 ชุดหลัก) หรือไม่ ·
(2) ค่าที่ปรับด้วยวันที่ 27 ก.ย. ทำนายวันที่ 2 ต.ค. ได้หรือไม่ (ไม่ปรับซ้ำ) · (3) ผลต่างระหว่าง DEM 3 ชุดเป็นอย่างไร
กติกา: เลือก (D, n) ที่ IoU ดีสุดของ 27 ก.ย. ต่อ DEM แล้วรายงาน 2 ต.ค. โดยไม่ปรับซ้ำ · ท่วม = ลึก ≥ 0.10 ม. ในอำเภอ · ผลออกทางไหนก็รายงานตามนั้น
ข้อจำกัด (สำคัญ): น้ำเข้าจากจุดเดียว (Ny.7) ไม่มีสาขา/ฝนบนพื้นที่/ประตูน้ำ/คันกั้น/สถานีสูบ · อัตราไหล Ny.7 มาจากเส้นโค้งอัตราไหลแบบประมาณ (±20% ช่วงสูง) · ลำน้ำเป็นเซลล์เดียวกว้างราว 90 ม. ขุดลึก D · พื้นที่ ~90 ม. ·
ไม่ใช่แบบจำลองทำนายใช้งานจริง — ใช้ดูว่ากลไกล้นตลิ่งจากลำน้ำสายหลักอธิบายพื้นที่น้ำท่วมได้เท่าใด
รัน: python analysis/goal7_ongkharak_hydraulic_2d.py prep   แล้ว   E:/theera/typhoon_env/Scripts/python.exe analysis/goal7_ongkharak_hydraulic_2d.py run
ผลลัพธ์: data/13_sentinel1_copernicus/derived/hydraulic2d_inputs.npz (disk-only) · analysis/goal7/ongkharak_hydraulic_2d.json
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
DER = ROOT / "data/13_sentinel1_copernicus/derived"
NPZ = DER / "hydraulic2d_inputs.npz"
EXT = os.environ.get("H2D_EXT", "") == "1"                      # รอบขยายกริด: ค่าที่ดีที่สุดรอบแรกอยู่ขอบกริด (ซึมน้อยสุด ระบายช้าสุด)
OUT = ROOT / ("analysis/goal7/ongkharak_hydraulic_2d_rain_ext.json" if (os.environ.get("H2D_MODE", "") == "rain" and EXT) else "analysis/goal7/ongkharak_hydraulic_2d_rain.json" if os.environ.get("H2D_MODE", "") == "rain" else "analysis/goal7/ongkharak_hydraulic_2d.json")
RAIN_NPZ = ROOT / "data/35_goal7_event_rain/rain_fields.npz"
Q_CSV = ROOT / "analysis/ny7_flow_series_2025_2026.csv"
NY7 = (14.20048, 101.219307)
LAT0, LAT1, LON0, LON1 = 13.98, 14.28, 100.97, 101.33      # หน้าต่างแบบจำลอง
K = 3                                                      # 30 ม. → ~90 ม.
MODE_RAIN = os.environ.get("H2D_MODE", "") == "rain"       # โหมดฝน: เริ่ม 20 ก.ย. 00:00 ใช้ฝนรายวัน + แก้ท้องร่อง
T0 = dt.datetime(2026, 9, 20, 0, 0) if MODE_RAIN else dt.datetime(2026, 9, 24, 0, 0)
T_END = dt.datetime(2026, 10, 3, 6, 30)
REC = {"peak_27sep": dt.datetime(2026, 9, 27, 18, 28), "oct2_validated": dt.datetime(2026, 10, 2, 6, 9)}
G = 9.81
HMIN = 1e-3
THRESH = 0.10
GRID_RAIN = {"f_mmh": [2.0, 6.0], "k_per_day": [0.2, 0.5, 1.0], "D": [1.0], "n_fp": [0.06]}      # กริดโหมดฝน: อัตราซึมลงดิน · อัตราระบายน้ำขังออก (ต่อวัน)
GRID_RAIN_EXT = {"f_mmh": [1.0, 2.0], "k_per_day": [0.05, 0.1], "D": [1.0], "n_fp": [0.06]}      # ขยายกริดลงทางค่าซึมต่ำ/ระบายช้า (รอบแรก f=2 · k=0.2 ดีสุดที่ขอบ)
GRID = (GRID_RAIN_EXT if EXT else GRID_RAIN) if MODE_RAIN else {"D": [0.5, 1.0, 2.0], "n_fp": [0.04, 0.08]}      # รอบแรก D=3,5 ม. (ร่องลึก) ไม่มีน้ำล้นเลย (IoU≈0) จึงเปลี่ยนไปช่วงตื้นกว่า — บันทึกไว้ว่าเปลี่ยนหลังเห็นผล D=3 ม. n=0.04
N_CH = 0.03


def block(a: np.ndarray, k: int, how: str) -> np.ndarray:
    ny, nx = (a.shape[0] // k) * k, (a.shape[1] // k) * k
    b = a[:ny, :nx].reshape(ny // k, k, nx // k, k).transpose(0, 2, 1, 3).reshape(ny // k, nx // k, k * k)
    if how == "mean":
        n_ok = np.sum(~np.isnan(b), axis=2)
        s = np.nansum(b, axis=2)
        out = np.where(n_ok >= (k * k) / 2, s / np.maximum(n_ok, 1), np.nan)
        return out.astype("float32")
    if how == "any":
        return b.any(axis=2)
    return b.astype("float32").mean(axis=2) >= 0.5


def prep() -> None:
    import goal7_ongkharak_2d_depression as dep
    import goal7_ongkharak_connected_fill as cf
    mask30 = np.load(dep.MASK_ONG_PATH).astype(bool)
    dems = dep.load_dems(mask30)
    river30 = cf.river_mask(cf.extract_river())
    res, x0, y1 = cf.GRID["res"], cf.GRID["x0"], cf.GRID["y1"]
    r0, r1 = int((y1 - LAT1) / res), int((y1 - LAT0) / res)
    c0, c1 = int((LON0 - x0) / res), int((LON1 - x0) / res)
    sl = (slice(r0, r1), slice(c0, c1))
    out = {name: block(np.asarray(dems[name], dtype="float32")[sl], K, "mean") for name in ("copernicus_raw", "fabdem_raw", "fabdem_stepped", "fabdem_corrected")}
    out["river"] = block(river30[sl], K, "any")
    out["mask"] = block(mask30[sl], K, "maj")
    for key, pth in dep.SAR_MASKS.items():
        out[key] = block(np.load(pth).astype(bool)[sl], K, "maj")
    # เซลล์ลำน้ำที่ใกล้ Ny.7 ที่สุด
    ny, nx = out["river"].shape
    rr, cc = np.nonzero(out["river"])
    ly = (y1 - r0 * res) - (np.arange(ny) + 0.5) * res * K
    lx = (x0 + c0 * res) + (np.arange(nx) + 0.5) * res * K
    d2 = (ly[rr] - NY7[0]) ** 2 + (lx[cc] - NY7[1]) ** 2
    j = int(np.argmin(d2))
    out["ny7_rc"] = np.array([rr[j], cc[j]])
    out["ny7_snap_km"] = np.array([math.sqrt(d2[j]) * 111.0])
    lat_mid = 0.5 * (LAT0 + LAT1)
    out["dxdy"] = np.array([res * K * 111320.0 * math.cos(math.radians(lat_mid)), res * K * 110574.0])
    # อัตราไหล Ny.7 รายชั่วโมงเทียบ T0 (เวลาท้องถิ่น)
    hrs, q = [], []
    for r in csv.DictReader(open(Q_CSV, encoding="utf-8")):
        t = dt.datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M")
        if T0 - dt.timedelta(hours=6) <= t <= T_END + dt.timedelta(hours=6):
            hrs.append((t - T0).total_seconds() / 3600.0)
            q.append(float(r["q_cms"]))
    out["q_hours"], out["q_cms"] = np.array(hrs), np.array(q)
    np.savez_compressed(NPZ, **out)
    print("เตรียมข้อมูล", {k: v.shape for k, v in out.items() if hasattr(v, "shape")}, "snap km", float(out["ny7_snap_km"][0]), "Q n", len(q), "peak", max(q))


def condition_bed(z0, river):
    """ปรับท้องลำน้ำให้ไม่สูงขึ้นตามทิศน้ำไหล: เซลล์ลำน้ำแต่ละเซลล์ชี้ไปเพื่อนบ้านลำน้ำที่ต่ำสุด แล้วส่งค่าต่ำสุดตามทิศปลายน้ำซ้ำจนนิ่ง (ขุดสันที่กั้นหลุม)"""
    z = np.where(np.isnan(z0), 60.0, z0).astype("float64")
    ny, nx = z.shape
    rr, cc = np.nonzero(river)
    idx = -np.ones(z.shape, dtype=np.int64)
    idx[rr, cc] = np.arange(len(rr))
    down = np.arange(len(rr))
    zr = z[rr, cc]
    for k, (r, c) in enumerate(zip(rr, cc)):
        best, bz = k, zr[k]
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < ny and 0 <= c2 < nx and idx[r2, c2] >= 0 and z[r2, c2] < bz:
                    best, bz = int(idx[r2, c2]), z[r2, c2]
        if best == k:                      # หลุม: ชี้ไปเพื่อนบ้านลำน้ำที่ต่ำสุด (แม้สูงกว่า) เพื่อให้ส่งค่าต่ำสุดไปข้างหน้าได้
            alt = [(z[r + dr, c + dc], int(idx[r + dr, c + dc])) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr or dc) and 0 <= r + dr < ny and 0 <= c + dc < nx and idx[r + dr, c + dc] >= 0]
            if alt:
                best = min(alt)[1]
        down[k] = best
    bed = zr.copy()
    for _ in range(len(rr)):
        new = bed.copy()
        np.minimum.at(new, down, bed)      # ส่งค่าที่ต่ำที่สุดต้นน้ำลงปลายน้ำ
        if np.array_equal(new, bed):
            break
        bed = new
    out = z.copy()
    out[rr, cc] = bed
    out[np.isnan(z0)] = np.nan
    return out.astype("float32")


def simulate(z0, river, q_hours, q_cms, rc, dx, dy, D, n_fp, rain=None, f_mmh=0.0, k_day=0.0, q_scale=1.0):
    import torch
    dev = "cuda"
    if rain is not None:
        z0 = condition_bed(z0, river)
    z = torch.tensor(np.where(np.isnan(z0), 60.0, z0), dtype=torch.float32, device=dev)
    rv = torch.tensor(river, device=dev)
    rain_t = torch.tensor(rain, dtype=torch.float32, device=dev) if rain is not None else None
    rain_in = 0.0
    z = torch.where(rv, z - D, z)
    ny, nx = z.shape
    n = torch.full_like(z, n_fp)
    n[rv] = N_CH
    nfx, nfy = 0.5 * (n[:, :-1] + n[:, 1:]), 0.5 * (n[:-1, :] + n[1:, :])
    h = torch.zeros_like(z)
    h[rv] = 0.3
    qx = torch.zeros((ny, nx - 1), device=dev)
    qy = torch.zeros((ny - 1, nx), device=dev)
    edge = torch.zeros_like(z, dtype=torch.bool)
    edge[0, :] = edge[-1, :] = True
    edge[:, 0] = edge[:, -1] = True
    t_end = (T_END - T0).total_seconds()
    rec = {k: (v - T0).total_seconds() for k, v in REC.items()}
    qh, qc = torch.tensor(q_hours * 3600.0, dtype=torch.float32), torch.tensor(q_cms, dtype=torch.float32)
    qh_np, qc_np = q_hours * 3600.0, q_cms
    t, step, dt_s, snaps = 0.0, 0, 5.0, {}
    inflow_vol = 0.0
    cell = dx * dy
    # บัญชีน้ำ (R7-28 · กติกา docs/HYDRAULIC2D_RERUN_PREREG.md §2) — บันทึกอย่างเดียว ไม่กระทบการไหล
    bud = {k: torch.zeros((), dtype=torch.float64, device=dev) for k in ("out", "drain", "clamp_gain", "rain")}
    init_vol = float(h.sum()) * cell
    while t < t_end:
        if step % 10 == 0:
            hmax = float(h.max())
            if not math.isfinite(hmax) or hmax > 40.0:           # ไม่เสถียร: หยุดและรายงาน
                raise RuntimeError(f"ไม่เสถียรที่ t={t/3600:.2f} ชม. hmax={hmax} dt={dt_s}")
            dt_s = float(min(8.0, max(1.0, 0.4 * min(dx, dy) / math.sqrt(G * (hmax + 1.0)))))        # +1 ม. กันระดับน้ำขึ้นเร็วระหว่างรอบตรวจ
            for k, tr in rec.items():
                if k not in snaps and t + dt_s >= tr:
                    snaps[k] = (h >= THRESH).cpu().numpy()
        eta = z + h
        hfx = (torch.maximum(eta[:, :-1], eta[:, 1:]) - torch.maximum(z[:, :-1], z[:, 1:])).clamp(min=0)
        qx = torch.where(hfx > HMIN, (qx - G * hfx * dt_s * (eta[:, 1:] - eta[:, :-1]) / dx) / (1 + G * dt_s * nfx ** 2 * qx.abs() / hfx.clamp(min=HMIN) ** (7 / 3)), torch.zeros_like(qx))
        hfy = (torch.maximum(eta[:-1, :], eta[1:, :]) - torch.maximum(z[:-1, :], z[1:, :])).clamp(min=0)
        qy = torch.where(hfy > HMIN, (qy - G * hfy * dt_s * (eta[1:, :] - eta[:-1, :]) / dy) / (1 + G * dt_s * nfy ** 2 * qy.abs() / hfy.clamp(min=HMIN) ** (7 / 3)), torch.zeros_like(qy))
        dh = torch.zeros_like(h)
        dh[:, :-1] -= qx / dx
        dh[:, 1:] += qx / dx
        dh[:-1, :] -= qy / dy
        dh[1:, :] += qy / dy
        hq = torch.where(edge & (h > HMIN), h * torch.sqrt(G * h.clamp(min=0)) / dx, torch.zeros_like(h))     # ไหลออกตามขอบแบบวิกฤต
        bud["out"] += hq.sum().double() * (dt_s * cell)
        raw = h + dt_s * (dh - hq)
        bud["clamp_gain"] += (raw.clamp(min=0) - raw).sum().double() * cell
        h = raw.clamp(min=0)
        q_now = float(np.interp(t, qh_np, qc_np)) * q_scale
        h[rc[0], rc[1]] += dt_s * q_now / cell
        if rain_t is not None:
            j = min(rain_t.shape[0] - 1, max(0, int(math.floor((t - 7 * 3600.0) / 86400.0)) + 1))
            eff = (rain_t[j] / 24.0 - f_mmh).clamp(min=0.0)                  # มม./ชม. หลังหักการซึมลงดิน
            h += dt_s * eff / 3.6e6
            bud["rain"] += eff.sum().double() * (dt_s / 3.6e6 * cell)
            if k_day > 0:
                h_old = h
                h = torch.where(rv, h, h * (1 - dt_s * k_day / 86400.0))
                bud["drain"] += (h_old - h).sum().double() * cell     # ระบายน้ำขังออกตามลำคลอง/ท่อ (ไม่ใช้กับเซลล์ลำน้ำ)
        inflow_vol += dt_s * q_now
        t += dt_s
        step += 1
    for k in rec:
        snaps.setdefault(k, (h >= THRESH).cpu().numpy())
    final = float(h.sum()) * cell
    b = {k: float(v) for k, v in bud.items()}
    total_in = inflow_vol + b["rain"]
    closure = init_vol + inflow_vol + b["rain"] + b["clamp_gain"] - b["out"] - b["drain"] - final
    budget = {"initial_mcm": round(init_vol / 1e6, 2), "inflow_mcm": round(inflow_vol / 1e6, 2), "rain_mcm": round(b["rain"] / 1e6, 2), "clamp_gain_mcm": round(b["clamp_gain"] / 1e6, 2),
              "edge_outflow_mcm": round(b["out"] / 1e6, 2), "drained_mcm": round(b["drain"] / 1e6, 2), "final_mcm": round(final / 1e6, 2),
              "closure_error_mcm": round(closure / 1e6, 3), "closure_error_pct_of_input": round(100.0 * closure / total_in, 3) if total_in else None}
    return snaps, {"steps": step, "inflow_mcm": round(inflow_vol / 1e6, 1), "final_stored_mcm": round(final / 1e6, 1), "rain_effective_mcm": round(b["rain"] / 1e6, 1) if rain_t is not None else None, "budget": budget}


def iou(pred, sar, mask, valid, cell_km2=0.0081):
    p, s = pred & mask & valid, sar & mask & valid
    u = float((p | s).sum())
    return {"iou": round(float((p & s).sum()) / u, 3) if u else None, "precision": round(float((p & s).sum()) / max(1.0, float(p.sum())), 3),
            "recall": round(float((p & s).sum()) / max(1.0, float(s.sum())), 3), "area_km2": round(float(p.sum()) * cell_km2, 1)}


def run(limit_runs: int = 0, only_dem: str = "") -> None:
    Z = np.load(NPZ)
    dx, dy = (float(v) for v in Z["dxdy"])
    rc = (int(Z["ny7_rc"][0]), int(Z["ny7_rc"][1]))
    mask = Z["mask"]
    res = {"setup": {"cell_m": [round(dx, 1), round(dy, 1)], "window": [LAT0, LAT1, LON0, LON1], "thresh_m": THRESH, "grid": GRID, "mode": "rain" if MODE_RAIN else "q_only", "n_channel": N_CH, "t0": str(T0), "t_end": str(T_END),
                     "ny7_snap_km": round(float(Z["ny7_snap_km"][0]), 2), "sar_area_km2": {k: round(float((Z[k] & mask).sum()) * dx * dy / 1e6, 1) for k in REC}}, "dems": {}}
    n_run = 0
    for dem in [d for d in ("fabdem_corrected", "fabdem_stepped", "fabdem_raw", "copernicus_raw") if not only_dem or d == only_dem]:
        z0 = Z[dem]
        valid = ~np.isnan(z0)
        rows = []
        rain = np.load(RAIN_NPZ)["fields"] if MODE_RAIN else None
        combos = [(D, nf, f, k) for D in GRID["D"] for nf in GRID["n_fp"] for f in GRID.get("f_mmh", [0.0]) for k in GRID.get("k_per_day", [0.0])]
        if True:
            for D, nf, f_mmh, k_day in combos:
                if limit_runs and n_run >= limit_runs:
                    break
                t0 = time.time()
                snaps, info = simulate(z0, Z["river"], Z["q_hours"], Z["q_cms"], rc, dx, dy, D, nf, rain, f_mmh, k_day)
                row = {"D_m": D, "n_fp": nf, "f_mmh": f_mmh, "k_per_day": k_day, **info, "sec": round(time.time() - t0)}
                for k in REC:
                    row[k] = iou(snaps[k], Z[k], mask, valid, dx * dy / 1e6)
                rows.append(row)
                n_run += 1
                print(dem, D, nf, f_mmh, k_day, row["sec"], "s", {k: row[k]["iou"] for k in REC}, "inflow", info["inflow_mcm"], "stored", info["final_stored_mcm"], flush=True)
        if rows:
            best = max(rows, key=lambda r: r["peak_27sep"]["iou"] or 0)
            res["dems"][dem] = {"runs": rows, "best_by_27sep": {"D_m": best["D_m"], "n_fp": best["n_fp"], "f_mmh": best["f_mmh"], "k_per_day": best["k_per_day"], "iou_27sep": best["peak_27sep"]["iou"], "iou_2oct_not_refit": best["oct2_validated"]["iou"]}}
    sens = json.loads((ROOT / "analysis/goal7/ongkharak_2d_depression_summary.json").read_text(encoding="utf-8"))["dem_sensitivity"]
    res["bucket_baseline"] = {k: {"peak_27sep": v["sar_fit"]["peak_27sep"]["iou"], "oct2_validated": v["sar_fit"]["oct2_validated"]["iou"]} for k, v in sens.items()}
    res["bucket_baseline"]["connected_fill_copernicus_s0"] = {"peak_27sep": 0.367, "oct2_validated": 0.321}
    (OUT.with_name(f"{OUT.stem}_{only_dem}.json") if only_dem else OUT).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v["best_by_27sep"] for k, v in res["dems"].items()}, ensure_ascii=False))


def combine() -> None:
    """รวมผลโหมดฝนรอบแรกกับรอบขยายกริด แล้วเลือกค่าที่ดีที่สุดด้วย IoU วันที่ 27 ก.ย. จากทุกชุดค่า (กติกาเดิม)"""
    a = json.loads((ROOT / "analysis/goal7/ongkharak_hydraulic_2d_rain.json").read_text(encoding="utf-8"))
    b = json.loads((ROOT / "analysis/goal7/ongkharak_hydraulic_2d_rain_ext.json").read_text(encoding="utf-8"))
    for dem, v in a["dems"].items():
        v["runs"] += b["dems"][dem]["runs"]
        best = max(v["runs"], key=lambda r: r["peak_27sep"]["iou"] or 0)
        v["best_by_27sep"] = {"D_m": best["D_m"], "n_fp": best["n_fp"], "f_mmh": best["f_mmh"], "k_per_day": best["k_per_day"], "iou_27sep": best["peak_27sep"]["iou"], "iou_2oct_not_refit": best["oct2_validated"]["iou"]}
    a["setup"]["grid"] = {"round1": a["setup"]["grid"], "round2_extension": b["setup"]["grid"]}
    (ROOT / "analysis/goal7/ongkharak_hydraulic_2d_rain_all.json").write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v["best_by_27sep"] for k, v in a["dems"].items()}, ensure_ascii=False))


def qsens(dem: str) -> None:
    """ความไวต่อน้ำเข้า × 0.8 และ × 1.2 ที่ (f, k) ดีสุดของพื้นผิวนั้น (เลือกไว้แล้วจากผลรอบก่อนหน้า — กติกา §3) · ต้องรันโหมดฝน"""
    assert MODE_RAIN, "ต้องตั้ง H2D_MODE=rain"
    Z = np.load(NPZ)
    dx, dy = (float(v) for v in Z["dxdy"])
    rc = (int(Z["ny7_rc"][0]), int(Z["ny7_rc"][1]))
    mask = Z["mask"]
    z0 = Z[dem]
    valid = ~np.isnan(z0)
    best = json.loads((ROOT / "analysis/goal7/ongkharak_hydraulic_2d_rain_all.json").read_text(encoding="utf-8"))["dems"][dem]["best_by_27sep"]
    rain = np.load(RAIN_NPZ)["fields"]
    rows = []
    for s in (0.8, 1.2):
        t0 = time.time()
        snaps, info = simulate(z0, Z["river"], Z["q_hours"], Z["q_cms"], rc, dx, dy, best["D_m"], best["n_fp"], rain, best["f_mmh"], best["k_per_day"], q_scale=s)
        row = {"q_scale": s, "f_mmh": best["f_mmh"], "k_per_day": best["k_per_day"], **info, "sec": round(time.time() - t0)}
        for k in REC:
            row[k] = iou(snaps[k], Z[k], mask, valid, dx * dy / 1e6)
        rows.append(row)
        print(dem, "q x", s, row["sec"], "s", {k: row[k]["iou"] for k in REC}, flush=True)
    (ROOT / f"analysis/goal7/ongkharak_hydraulic_2d_qsens_{dem}.json").write_text(json.dumps({"dem": dem, "runs": rows}, ensure_ascii=False, indent=1), encoding="utf-8")


def qsens_merge() -> None:
    out = {}
    for d in ("fabdem_corrected", "fabdem_stepped", "fabdem_raw", "copernicus_raw"):
        out[d] = json.loads((ROOT / f"analysis/goal7/ongkharak_hydraulic_2d_qsens_{d}.json").read_text(encoding="utf-8"))["runs"]
    (ROOT / "analysis/goal7/ongkharak_hydraulic_2d_qsens.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print({d: [(r["q_scale"], r["peak_27sep"]["iou"], r["oct2_validated"]["iou"]) for r in v] for d, v in out.items()})


def merge() -> None:
    """รวมผลที่รันขนานแยกตาม DEM (แต่ละ DEM รันเป็นกระบวนการของตัวเอง)"""
    parts = [json.loads(OUT.with_name(f"{OUT.stem}_{d}.json").read_text(encoding="utf-8")) for d in ("fabdem_corrected", "fabdem_stepped", "fabdem_raw", "copernicus_raw")]
    res = parts[0]
    for x in parts[1:]:
        res["dems"].update(x["dems"])
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v["best_by_27sep"] for k, v in res["dems"].items()}, ensure_ascii=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prep"
    if cmd == "prep":
        prep()
    elif cmd == "merge":
        merge()
    elif cmd == "combine":
        combine()
    elif cmd == "qsens":
        qsens(sys.argv[2])
    elif cmd == "qsens_merge":
        qsens_merge()
    else:
        run(int(sys.argv[2]) if len(sys.argv) > 2 else 0, sys.argv[3] if len(sys.argv) > 3 else "")
