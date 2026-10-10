"""เป้าหมาย 6 — L3: โมเดลทำนายระดับน้ำรายลุ่ม (วิธีเดียวกับ goal4_model_v1)

โครงเดิมนครนายก: สูตรเส้นตรง 11 ตัวแปร vs persistence vs GBDT ที่ +6/+24/+48 ชม.
ปรับต่อลุ่ม: จุดเป้าหมาย = จุดวัดเมืองหลักของลุ่ม (code ที่มีอนุกรมยาวสุด) ·
ต้นน้ำ = จุดวัดใกล้เขื่อน · ฝน R24/R72/R168 จาก NASA POWER รายวันของจุดฝนลุ่มบน (data/22 rain_rarity raw มี 1981–2026)
หน้าต่างฝึก: ทุกฤดูฝน 6 มิ.ย.–4 ต.ค. ที่มีข้อมูล (2020–2026) · ทดสอบ: กลางเหตุการณ์ 20 ก.ย.–9 ต.ค. 69
ผลลัพธ์: analysis/goal6/<basin>/l3_model.json + l3_model.md
รัน: python analysis/goal6_l3_model.py [--basin id,...]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from rain_window import windows_for_grid  # noqa: E402 — helper กลาง (ไม่มีข้อมูลอนาคต ตามเทส test_core)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "analysis/goal6/config.json"
OUT_BASE = ROOT / "analysis/goal6"
RAW_RAIN = ROOT / "data/22_goal6_network/raw/rain_rarity"
RAW_ST = ROOT / "data/22_goal6_network/raw"
READINESS = ROOT / "analysis/goal6_basin_readiness.json"

# จุดเป้าหมายต่อลุ่ม (จุดวัดเมืองหลัก — เลือกด้วยมือจาก L1: อนุกรมยาว + จุดบริบทชัด)
TARGET = {
    "pasak": ("S.26", "ท้ายเขื่อนพระรามหก", "S.28"),      # เป้าหมาย/ต้นน้ำ (ท้ายเขื่อนป่าสัก)
    "maeklong": ("K.3A", "สะพานข้ามแม่น้ำแม่กลอง (กาญจนบุรี)", "K.62"),  # ท้ายลุ่ม/ต้น
    "bp_prach": ("Kgt.3", "สะพานต้นน้ำบางปะกง (กบินทร์บุรี)", "Kgt.15B"),
    "thachin": ("T.1", "ที่ว่าการ อ.นครชัยศรี", "T.13"),
    "ping_cp": ("C.2", "ท่าเรือ นครสวรรค์", "P.17"),
    "bkk_lower": ("C.13", "ท้ายเขื่อนเจ้าพระยา", "C.22A"),  # ปากเกร็ด = ต้นทางเข้า กทม.
}


def fetch_hourly(sid: int, y: int) -> dict[str, float]:
    import goal6_screen_basins as g6
    u = (f"{g6.API_BASE}public/waterlevel_graph?station_type=tele_waterlevel"
         f"&station_id={sid}&start_date={y}-01-01&end_date={y}-12-31")
    try:
        data = g6.get_json(u).get("data") or {}
    except RuntimeError:
        return {}
    out = {}
    for r in data.get("graph_data") or []:
        v = r.get("value")
        if v is None:
            continue
        try:
            dt.datetime.fromisoformat(r["datetime"])  # validate
            out[r["datetime"]] = float(v)
        except (ValueError, TypeError):
            continue
    return out


def daily_rain(key: str) -> dict[str, float]:
    p = RAW_RAIN / f"power_{key}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def hourly_grid(d: dict[str, float], y: int) -> tuple[list, np.ndarray]:
    t0, t1 = dt.datetime(y, 6, 1), dt.datetime(y, 10, 4, 23)
    grid = [t0 + dt.timedelta(hours=h) for h in range(int((t1 - t0).total_seconds() // 3600) + 1)]
    idx = {t.replace(minute=0): i for i, t in enumerate(grid)}
    bucket: dict[dt.datetime, list[float]] = {}
    for s, v in d.items():
        try:
            t = dt.datetime.fromisoformat(s)
        except ValueError:
            continue
        h = t.replace(minute=0)
        if h in idx:
            bucket.setdefault(h, []).append(v)
    out = np.full(len(grid), np.nan)
    for h, vals in bucket.items():
        out[idx[h]] = np.mean(vals)
    return grid, out


def at(a: np.ndarray, i: int, back: int) -> float:
    j = i - back
    return a[j] if j >= 0 else np.nan


def rain_windows(daily: dict[str, float], grid_t: list) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """R24/R72/R168 สะสมถึง<b>สิ้นสุดเมื่อวาน</b> — ใช้ helper กลาง rain_window.windows_for_grid
    (H6 รีวิว Sift: ตัวเดิม rain_at ใช้ฝน 'วันนี้' ทั้งวันตั้งแต่เที่ยงคืน = รั่วถึง 23 ชม. —
    repo จดวิธีถูกไว้แล้วใน rain_window.py + เทส test_day_window_uses_no_future_information)
    คืน (R24, R72, R168) ยาวเท่า grid_t · ค่าคงที่ทั้งวัน = ผลรวมถึงเมื่อวาน"""
    daily_map = {d.replace("-", ""): v for d, v in daily.items()
                 if isinstance(v, (int, float)) and v >= 0}
    w = windows_for_grid(daily_map, grid_t, spans=(1, 3, 7))
    return w[1], w[3], w[7]


def run_basin(bid: str, rec: dict, out_json: Path, out_md: Path) -> None:
    tgt_code, tgt_name, up_code = TARGET[bid]
    stations = {s["code"]: s for s in rec["stations"]}
    st_tgt = next((s for s in rec["stations"] if s["code"] == tgt_code), None)
    st_up = next((s for s in rec["stations"] if s["code"] == up_code), None)
    if not st_tgt:
        print(f"  {bid}: ไม่พบจุดเป้าหมาย {tgt_code}", flush=True)
        return

    # โหลดอนุกรมรายชั่วโมง (cache รายจุด-ปี)
    cache = {}
    for sid, label in [(st_tgt["id"], "tgt"), (st_up["id"], "up") if st_up else (None, None)]:
        if sid is None:
            continue
        for y in range(2020, 2027):
            if (sid, y) not in cache:
                raw_p = RAW_ST / f"l1_cache_{sid}_{y}.json"
                if raw_p.exists():
                    cache[(sid, y)] = json.loads(raw_p.read_text(encoding="utf-8"))
                else:
                    cache[(sid, y)] = fetch_hourly(sid, y)
                    raw_p.write_text(json.dumps(cache[(sid, y)]), encoding="utf-8")

    # ฝน: จุดฝนลุ่มบนแรกของลุ่ม
    rain_label, (rlon, rlat) = next(iter(rec["rain_points"].items()))
    rkey = f"{bid}_{rain_label}".replace(" ", "_").replace("(", "").replace(")", "")
    daily = daily_rain(rkey)

    # ประกอบเมทริกซ์
    X, Y, T, tgt_t = [], [], [], None
    for y in range(2020, 2027):
        g_t, tgt = hourly_grid(cache.get((st_tgt["id"], y), {}), y)
        if len(g_t) == 0:
            continue
        # H6: หน้าต่างฝนของปีนี้ — สิ้นสุดเมื่อวาน (helper กลาง rain_window · ไม่มีข้อมูลอนาคต)
        r24y, r72y, r168y = rain_windows(daily, g_t)
        _, up = hourly_grid(cache.get((st_up["id"], y), {}), y) if st_up else (None, None)
        for i, t in enumerate(g_t):
            if not np.isfinite(tgt[i]):
                continue
            ok_hist = all(np.isfinite(at(tgt, i, b)) for b in (3, 6, 24))
            r24, r72, r168 = r24y[i], r72y[i], r168y[i]
            if not ok_hist:
                continue
            x = [tgt[i], at(tgt, i, 3), at(tgt, i, 24), tgt[i] - at(tgt, i, 6)]
            if up is not None:
                x += [up[i], at(up, i, 6), at(up, i, 24)]
            x += [r24, r72, r168]
            X.append(x)
            Y.append([tgt[i + h] if i + h < len(g_t) else np.nan for h in (6, 24, 48)])
            T.append(t)
    X, Y, T = np.array(X, float), np.array(Y, float), np.array(T, dtype=object)
    ok = np.isfinite(X).all(1) & np.isfinite(Y).all(1)
    X, Y, T = X[ok], Y[ok], np.array([t for t, o in zip(T, ok) if o])
    if len(X) < 2000:
        print(f"  {bid}: ตัวอย่างไม่พอ ({len(X)})", flush=True)
        return
    te = np.array([t >= dt.datetime(2026, 9, 20) for t in T])
    tr = ~te
    results = {}
    for k, h in enumerate((6, 24, 48)):
        ytr, yte = Y[tr, k], Y[te, k]
        rows = []
        p_pers = X[te, 0]
        lin = LinearRegression().fit(X[tr], ytr)
        p_lin = lin.predict(X[te])
        gb = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06, max_depth=4,
                                           min_samples_leaf=40, random_state=0).fit(X[tr], ytr)
        p_gb = gb.predict(X[te])
        ev = np.array([dt.datetime(2026, 9, 25) <= t <= dt.datetime(2026, 10, 2) for t in T[te]])
        for nm, p in (("persistence", p_pers), ("linear", p_lin), ("GBDT", p_gb)):
            rmse = np.sqrt(np.mean((p - yte) ** 2)) * 100
            mae = np.mean(np.abs(p - yte)) * 100
            rmse_ev = np.sqrt(np.mean((p[ev] - yte[ev]) ** 2)) * 100 if ev.any() else None
            rows.append({"model": nm, "rmse_cm": round(rmse, 1), "mae_cm": round(mae, 1),
                         "rmse_event_cm": round(rmse_ev, 1) if rmse_ev is not None else None})
        results[str(h)] = {"rows": rows, "coef_linear": [round(c, 4) for c in lin.coef_],
                           "n_train": int(tr.sum()), "n_test": int(te.sum())}
        best = min(rows, key=lambda r: r["rmse_cm"])
        print(f"  {bid} +{h}ชม.: ดีสุด {best['model']} RMSE {best['rmse_cm']} ซม. "
              f"(เหตุการณ์ {rows[1]['rmse_event_cm']})", flush=True)
    out = {"basin": bid, "target": {"code": tgt_code, "name": tgt_name},
           "upstream": up_code, "rain_point": rain_label,
           "train_hours": int(tr.sum()), "test_hours": int(te.sum()),
           "results": results}
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# L3 โมเดลทำนาย — {rec['label']} (จุดเป้าหมาย {tgt_code})", "",
          f"> ฝึก {int(tr.sum())} ชม. (2020–2026 ฤดูฝน) · ทดสอบกลางเหตุการณ์ 20 ก.ย.–9 ต.ค. 69 · "
          f"ตัวแปร {X.shape[1]} (ระดับ+Δ3/24ชม. + ต้นน้ำ {up_code} + ฝน 24/72/168 ชม. POWER)", "",
          "| ระยะ | โมเดล | RMSE ทดสอบ (ซม.) | RMSE เหตุการณ์ (ซม.) | MAE (ซม.) |", "|---|---|---|---|---|"]
    for h in ("6", "24", "48"):
        for r in results[h]["rows"]:
            md.append(f"| +{h} ชม. | {r['model']} | {r['rmse_cm']} | {r['rmse_event_cm']} | {r['mae_cm']} |")
    md += ["", "⚠️ เกณฑ์เทียบเดียวกับนครนายก: ระยะใช้งานจริง +6/+24 ชม. · ค่าอนุกรมมีช่องว่าง (ครอบคลุม 45–80%)", ""]
    out_md.write_text("\n".join(md), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--basin", default=None)
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    targets = args.basin.split(",") if args.basin else list(cfg["basins"].keys())
    for bid in targets:
        rec = cfg["basins"][bid]
        print(f"=== L3 {bid} ({rec['label']}) ===", flush=True)
        try:
            run_basin(bid, rec, OUT_BASE / bid / "l3_model.json", OUT_BASE / bid / "l3_model.md")
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {bid}: {type(exc).__name__} {str(exc)[:120]}", flush=True)


if __name__ == "__main__":
    main()