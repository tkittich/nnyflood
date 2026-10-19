"""เป้าหมาย 6 — ถดถอยหาอัตราส่งผ่านน้ำทะเลหนุนสู่ระดับน้ำ C.12 สามเสน (tide gain ∂H_C12/∂H_tide)

ที่มา (รีวิวรอบ 6 · งาน C1): สมการ analysis/compound_flood_risk.py ตั้ง ∂H/∂น้ำหนุน = 1.0 โดยไม่สอบเทียบ
(ค้างที่ B-03 / R6-04) — สคริปต์นี้ประมาณค่าจากอนุกรมรายชั่วโมงปี 2569 ของโครงการเอง
(C.12 สามเสน · CPY015 สะพานกรุงเทพ · BKK001 ต้นน้ำ) เพื่อให้มีหลักฐานที่ทำซ้ำได้ในที่เดียว

วิธี (เขียนก่อนดูผล — pre-registration):
  ก) ระดับ: H_C12(t) = a + g·tide(t−τ) + b·BKK001(t) + e  · เลือก τ ∈ 0..6 ชม. ที่ R² สูงสุด
  ข) แถบน้ำขึ้นน้ำลง: ลบค่าเฉลี่ยเคลื่อนที่ 25 ชม. (ตัดน้ำเหนือที่เปลี่ยนช้า) แล้วถดถอย H_hp บน tide_hp(t−τ)
  ค) รายงานแยกช่วงก่อนเหตุการณ์ (< 20 ก.ย.) และช่วงเหตุการณ์ (≥ 20 ก.ย.)
  ความคลาดเคลื่อนมาตรฐาน: Newey–West (ความหน่วง 48 ชม.) เพราะส่วนตกค้างรายชั่วโมงสัมพันธ์กันสูง

ข้อจำกัด: ข้อมูลฤดูเดียว ไม่มีอัตราไหลรายชั่วโมงที่บางไทร (ใช้ระดับ BKK001 แทน) ผลนี้คือ "หลักฐานเชิงสำรวจ"
ไม่ใช่การสอบเทียบหลายปี — ห้ามใช้แทนค่าสอบเทียบจนกว่าจะมีข้อมูลหลายฤดู (B-03 ใน docs/OFFLINE_DATA_BACKLOG.md)

รัน: python analysis/goal6_tide_gain_regression.py
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal6_l3_coastal_model import RAW_DIR, load_series  # noqa: E402  (reuse-first: ตัวโหลดอนุกรมเดียวกับโมเดล L3)

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "analysis/goal6/tide_gain_regression.json"
EVENT_START = "2026-09-20 00:00"
NW_LAGS = 48
MAX_TAU = 6
FMT = "%Y-%m-%d %H:00"


def newey_west_ols(X: np.ndarray, y: np.ndarray, lags: int = NW_LAGS):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta
    xtx_inv = np.linalg.inv(X.T @ X)
    xe = X * e[:, None]
    s = xe.T @ xe
    for L in range(1, lags + 1):
        w = 1.0 - L / (lags + 1.0)
        g = xe[L:].T @ xe[:-L]
        s += w * (g + g.T)
    cov = xtx_inv @ s @ xtx_inv
    r2 = 1.0 - float(e @ e) / float(((y - y.mean()) ** 2).sum())
    return beta, np.sqrt(np.diag(cov)), r2, e


def moving_mean_25(v: np.ndarray) -> np.ndarray:
    pad = np.pad(v, 12, mode="edge")
    return np.convolve(pad, np.ones(25) / 25.0, mode="valid")


def _summ(beta_i, se_i, e, n, extra=None):
    rho = float(np.corrcoef(e[:-1], e[1:])[0, 1])
    d = {"n": int(n), "gain": float(beta_i), "gain_se_nw": float(se_i),
         "gain_ci95": [float(beta_i - 1.96 * se_i), float(beta_i + 1.96 * se_i)],
         "n_effective": float(len(e) * (1 - rho) / (1 + rho))}
    d.update(extra or {})
    return d


def fit_levels(c12, tide, up, tau, lo=None, hi=None):
    ks, h, td, u = [], [], [], []
    for k in sorted(c12):
        t = dt.datetime.strptime(k, FMT)
        kt = (t - dt.timedelta(hours=tau)).strftime(FMT)
        if kt in tide and k in up and (lo is None or k >= lo) and (hi is None or k < hi):
            ks.append(k); h.append(c12[k]); td.append(tide[kt]); u.append(up[k])
    X = np.column_stack([np.ones(len(ks)), td, u])
    beta, se, r2, e = newey_west_ols(X, np.array(h))
    return _summ(beta[1], se[1], e, len(ks), {"tau_h": tau, "r2": float(r2),
                 "river_coef_bkk001": float(beta[2]), "intercept": float(beta[0])})


def fill_short_gaps(series: dict, max_gap: int = 2):
    """เติมช่องว่างสั้น (≤ max_gap ชม.) ด้วยการแทรกเชิงเส้น — C.12 ขาดชั่วโมง 00:00 ทุกวัน จึงต้องเติมก่อนทำแถบน้ำขึ้นน้ำลง
    คืน (อนุกรมใหม่, จำนวนจุดที่เติม)"""
    keys = sorted(series)
    out = dict(series)
    filled = 0
    for a, b in zip(keys[:-1], keys[1:]):
        ta, tb = dt.datetime.strptime(a, FMT), dt.datetime.strptime(b, FMT)
        gap = int((tb - ta).total_seconds() // 3600) - 1
        if 1 <= gap <= max_gap:
            for j in range(1, gap + 1):
                out[(ta + dt.timedelta(hours=j)).strftime(FMT)] = series[a] + (series[b] - series[a]) * j / (gap + 1)
                filled += 1
    return out, filled


def fit_tidal_band(c12, tide, tau, lo=None, hi=None):
    """แถบน้ำขึ้นน้ำลง: ตัดเป็นช่วงชั่วโมงติดกัน (≥ 100 ชม.) แล้วลบค่าเฉลี่ยเคลื่อนที่ 25 ชม."""
    keys = sorted(set(c12) & set(tide))
    ts = [dt.datetime.strptime(k, FMT) for k in keys]
    segs, cur = [], [0]
    for i in range(1, len(keys)):
        if (ts[i] - ts[i - 1]).total_seconds() == 3600:
            cur.append(i)
        else:
            segs.append(cur)
            cur = [i]
    segs.append(cur)
    xs, ys = [], []
    for sg in segs:
        if len(sg) < 100:
            continue
        h = np.array([c12[keys[i]] for i in sg])
        td = np.array([tide[keys[i]] for i in sg])
        hp_h, hp_t = h - moving_mean_25(h), td - moving_mean_25(td)
        for j, i in enumerate(sg):
            if j - tau < 0 or j < 12 or j > len(sg) - 13:
                continue
            k = keys[i]
            if (lo is None or k >= lo) and (hi is None or k < hi):
                xs.append(hp_t[j - tau])
                ys.append(hp_h[j])
    X = np.column_stack([np.ones(len(xs)), np.array(xs)])
    y = np.array(ys)
    beta, se, r2, e = newey_west_ols(X, y)
    return _summ(beta[1], se[1], e, len(y), {"tau_h": tau, "r2": float(r2)})


def main() -> None:
    c12 = load_series(RAW_DIR / "2599_C.12_2026_hourly.json")
    tide = load_series(RAW_DIR / "4_CPY015_2026_hourly.json")
    up = load_series(RAW_DIR / "11_BKK001_2026_hourly.json")

    lag_scan = [fit_levels(c12, tide, up, tau) for tau in range(MAX_TAU + 1)]
    best = max(lag_scan, key=lambda r: r["r2"])
    c12_f, n_fill_c12 = fill_short_gaps(c12)
    tide_f, n_fill_tide = fill_short_gaps(tide)
    band_scan = [fit_tidal_band(c12_f, tide_f, t) for t in range(MAX_TAU + 1)]
    band_best = max(band_scan, key=lambda r: r["r2"])
    tb = band_best["tau_h"]

    out = {
        "metadata": {
            "title": "ถดถอยอัตราส่งผ่านน้ำทะเลหนุนสู่ระดับน้ำ C.12 (tide gain)",
            "stations": {"target": "C.12 สามเสน", "tide": "CPY015 สะพานกรุงเทพ", "upstream_proxy": "BKK001"},
            "season": "2569 ฤดูเดียว",
            "se_method": f"Newey–West ความหน่วง {NW_LAGS} ชม.",
            "event_start": EVENT_START,
            "series_end": {"c12": max(c12), "tide": max(tide), "bkk001": max(up)},
            "gap_fill": {"method": "แทรกเชิงเส้นช่องว่าง ≤ 2 ชม. (เฉพาะแถบน้ำขึ้นน้ำลง)", "filled_c12": n_fill_c12, "filled_tide": n_fill_tide},
            "limitation": "ข้อมูลฤดูเดียว ไม่มีอัตราไหลรายชั่วโมงที่บางไทร (ใช้ระดับ BKK001 แทน) — หลักฐานเชิงสำรวจ ไม่ใช่การสอบเทียบหลายปี",
            "note_on_earlier_claim": "ค่า 0.705 ± 0.016 ที่เคยอ้างในเอกสารรอบ 5 ไม่มีสคริปต์ผลิตในคลัง — ค่าที่ทำซ้ำได้คือผลในไฟล์นี้",
        },
        "levels_all": {"best_tau": best, "lag_scan": lag_scan},
        "levels_pre_event": fit_levels(c12, tide, up, best["tau_h"], hi=EVENT_START),
        "levels_event": fit_levels(c12, tide, up, best["tau_h"], lo=EVENT_START),
        "tidal_band_all": {"best_tau": band_best, "lag_scan": band_scan},
        "tidal_band_pre_event": fit_tidal_band(c12_f, tide_f, tb, hi=EVENT_START),
        "tidal_band_event": fit_tidal_band(c12_f, tide_f, tb, lo=EVENT_START),
    }
    out["headline"] = {
        "definition": "อัตราส่งผ่านเฉพาะแถบน้ำขึ้นน้ำลง (ลบค่าเฉลี่ยเคลื่อนที่ 25 ชม.) ทั้งฤดู",
        "gain": round(band_best["gain"], 3),
        "gain_ci95": [round(x, 3) for x in band_best["gain_ci95"]],
        "tau_h": tb,
        "n": band_best["n"],
        "levels_gain_all": round(best["gain"], 3),
        "levels_gain_ci95": [round(x, 3) for x in best["gain_ci95"]],
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    h = out["headline"]
    print(f"บันทึก {OUT_JSON}")
    print(f"  แถบน้ำขึ้นน้ำลง: gain {h['gain']} {h['gain_ci95']} tau={h['tau_h']} ชม. n={h['n']}")
    print(f"  ระดับ (รวม BKK001): gain {h['levels_gain_all']} {h['levels_gain_ci95']}")
    for k in ("levels_pre_event", "levels_event", "tidal_band_pre_event", "tidal_band_event"):
        r = out[k]
        print(f"  {k}: gain {r['gain']:.3f} +-{1.96 * r['gain_se_nw']:.3f} n={r['n']} n_eff={r['n_effective']:.0f}")


if __name__ == "__main__":
    main()
