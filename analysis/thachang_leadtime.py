# ทำนายท้ายน้ำ ปตร.ท่าช้าง (63) จาก Ny.7 — สัญญาณจริงหรือแค่เทรนด์ฤดูร่วม? (P3)
#
# ปัญหา: r ดิบ 0.95 @ +21h อาจมาจาก "recession ร่วม" (ทั้งสองจุดลดตามฤดูพร้อมกัน)
#        ไม่ใช่ routing จริง -> ต้องทดสอบ:
#          1) corr ของ "ผลต่าง" (Δ1h) — ลบเทรนด์ออกแล้วยังสูงไหม
#          2) corr ของ detrend (ลบ rolling mean)
#          3) เทียบกับ persistence (ตัวทำนายพื้นฐานสุด) บนช่วงทดสอบที่แยกออกมา
#          4) fit เทรน/ทดสอบ แยกตามเวลา (1-20 ก.ย. = train · 21-30 ก.ย. = test)
#
# ใช้: python analysis/thachang_leadtime.py
# ออก: analysis/thachang_leadtime.json + analysis/thachang_leadtime.md
import csv
import datetime as dt
import json
import math
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "20_multistation_levels"
OUT_JSON = ROOT / "analysis" / "thachang_leadtime.json"
OUT_MD = ROOT / "analysis" / "thachang_leadtime.md"

DRIVER, TARGET = "62", "63"          # Ny.7 -> ท้ายน้ำ ท่าช้าง
TRAIN_END = dt.datetime(2026, 9, 20, 23, 59)
LAGS = list(range(1, 37))            # 1..36 ชม.


def hourly(sid, tol_min=25):
    """กริดรายชั่วโมงจาก CSV — เลือกค่าที่ใกล้ชั่วโมงนั้นสุดภายใน ±tol นาที."""
    pts = []
    p = DATA / f"st{sid}.csv"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            s = (r["level_msl_m"] or "").strip()
            if s in ("", "-"):
                continue
            try:
                v = float(s)
            except ValueError:
                continue
            pts.append((dt.datetime.fromisoformat(r["datetime"]), v))
    pts.sort()
    out = {}
    for t, v in pts:
        h = t.replace(minute=0, second=0)
        if h not in out or abs(t - h) < abs(out[h][0] - h):
            out[h] = (t, v)
    return {h: tv[1] for h, tv in out.items()
            if abs((tv[0] - h).total_seconds()) <= tol_min * 60}


def corr(xs, ys):
    p = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(p) < 30:
        return None, len(p)
    a = [x for x, _ in p]
    b = [y for _, y in p]
    ma, mb = st.mean(a), st.mean(b)
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if sa == 0 or sb == 0:
        return None, len(p)
    return sum((x - ma) * (y - mb) for x, y in p) / (sa * sb), len(p)


def rolling_mean(series, keys, win=25):
    """ค่าเฉลี่ยเคลื่อนที่ centred บนกริด (keys เรียงแล้ว)."""
    idx = {k: i for i, k in enumerate(keys)}
    out = {}
    half = win // 2
    for k in keys:
        i = idx[k]
        seg = [series[keys[j]] for j in range(max(0, i - half), min(len(keys), i + half + 1))
               if keys[j] in series]
        out[k] = st.mean(seg) if seg else None
    return out


def rmse(pred, truth):
    p = [(a, b) for a, b in zip(pred, truth) if a is not None and b is not None]
    if not p:
        return None
    return math.sqrt(sum((a - b) ** 2 for a, b in p) / len(p))


def main():
    s_drv = hourly(DRIVER)
    s_tgt = hourly(TARGET)
    keys = sorted(set(s_drv) & set(s_tgt))
    if len(keys) < 100:
        raise SystemExit(f"ข้อมูลร่วมน้อยเกินไป: {len(keys)} ชม.")

    drv = {k: s_drv[k] for k in keys}
    tgt = {k: s_tgt[k] for k in keys}

    # ---- 1) corr ระดับดิบ vs ผลต่าง vs detrend ----
    def diff1(series, k):
        a = series.get(k)
        b = series.get(k - dt.timedelta(hours=1))
        return None if (a is None or b is None) else a - b

    lag_rows = []
    for L in LAGS:
        pairs = [(k, k + dt.timedelta(hours=L)) for k in keys]
        raw_x = [drv[k] for k, k2 in pairs if k2 in tgt]
        raw_y = [tgt[k2] for k, k2 in pairs if k2 in tgt]
        r_raw, n = corr(raw_x, raw_y)
        # ผลต่าง 1 ชม.
        dx = [diff1(drv, k) for k, _ in pairs]
        dy = [diff1(tgt, k2) for _, k2 in pairs]
        r_dif, _ = corr(dx, dy)
        lag_rows.append({"lag_h": L, "r_raw": r_raw, "r_diff": r_dif, "n": n})

    best_raw = max((r for r in lag_rows if r["r_raw"] is not None), key=lambda r: r["r_raw"])
    best_dif = max((r for r in lag_rows if r["r_diff"] is not None), key=lambda r: abs(r["r_diff"]))

    # ---- 2) detrend ----
    t_drv = rolling_mean(drv, keys, 25)
    t_tgt = rolling_mean(tgt, keys, 25)
    d_drv = {k: (drv[k] - t_drv[k]) if t_drv[k] is not None else None for k in keys}
    d_tgt = {k: (tgt[k] - t_tgt[k]) if t_tgt[k] is not None else None for k in keys}
    detrend_rows = []
    for L in LAGS:
        x = [d_drv[k] for k in keys]
        y = [d_tgt.get(k + dt.timedelta(hours=L)) for k in keys]
        r, _ = corr(x, y)
        detrend_rows.append({"lag_h": L, "r_detrend": r})
    best_det = max((r for r in detrend_rows if r["r_detrend"] is not None),
                   key=lambda r: abs(r["r_detrend"]))

    # ---- 3) predictor เทรน/ทดสอบ แยกเวลา ที่ lag = best_raw ----
    # เทียบ 3 โมเดล — สำคัญ: ต้องเทียบกับ persistence เสมอ ไม่งั้น r สูงหลอกตา
    #   A) persistence            : ŷ(t+L) = y(t)
    #   B) level transfer         : ŷ(t+L) = a + b·x(t)
    #   C) persistence + Δต้นน้ำ  : ŷ(t+L) = y(t) + c + d·(x(t) − x(t−L))
    #      -> ตอบคำถามจริงว่า "Ny.7 ให้ข้อมูลเกินกว่า persistence ไหม"
    L = best_raw["lag_h"]

    def ols(X, y):
        """X = list of rows (มี 1 ค่าคงที่นำหน้าแล้ว) -> สัมประสิทธิ์"""
        n = len(X)
        k = len(X[0])
        XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
        Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
        # แก้ระบบด้วย Gaussian elimination
        M = [row[:] + [Xty[a]] for a, row in enumerate(XtX)]
        for c in range(k):
            p = max(range(c, k), key=lambda r: abs(M[r][c]))
            M[c], M[p] = M[p], M[c]
            if abs(M[c][c]) < 1e-12:
                return None
            for r in range(k):
                if r != c:
                    f = M[r][c] / M[c][c]
                    for cc in range(c, k + 1):
                        M[r][cc] -= f * M[c][cc]
        return [M[a][k] / M[a][a] for a in range(k)]

    def usable(lo, hi):
        ks = []
        for k in keys:
            k2 = k + dt.timedelta(hours=L)
            if k2 not in tgt or not (lo <= k <= hi):
                continue
            if k - dt.timedelta(hours=L) not in drv:
                continue
            ks.append(k)
        return ks

    train_keys = usable(dt.datetime(2026, 9, 1), TRAIN_END)
    test_keys = usable(TRAIN_END, dt.datetime(2026, 9, 30, 23, 59))
    event_keys = usable(dt.datetime(2026, 9, 26), dt.datetime(2026, 9, 30, 23, 59))

    def build(ks):
        xs = [drv[k] for k in ks]
        ys = [tgt[k + dt.timedelta(hours=L)] for k in ks]
        dx = [drv[k] - drv[k - dt.timedelta(hours=L)] for k in ks]
        cur = [tgt[k] for k in ks]
        return xs, ys, dx, cur

    xs_tr, ys_tr, dx_tr, cur_tr = build(train_keys)
    cB = ols([[1.0, x] for x in xs_tr], ys_tr)                       # B
    cC = ols([[1.0, d] for d in dx_tr], [y - c for y, c in zip(ys_tr, cur_tr)])  # C (ทำนาย Δ)

    def predict(ks, which):
        xs, ys, dx, cur = build(ks)
        if which == "A":
            return cur, ys
        if which == "B":
            a, b = cB
            return [a + b * x for x in xs], ys
        cc, dd = cC
        return [c + cc + dd * d for c, d in zip(cur, dx)], ys

    preds = {m: predict(test_keys, m) for m in ("A", "B", "C")}
    ev_preds = {m: predict(event_keys, m) for m in ("A", "B", "C")}
    r_test, n_test = corr(preds["B"][0], preds["B"][1])

    out = {
        "driver": {"id": DRIVER, "name": "Ny.7"},
        "target": {"id": TARGET, "name": "ท้ายน้ำ ปตร.ท่าช้าง"},
        "common_hours": len(keys),
        "target_hours": len(s_tgt),
        "best_raw_lag": {"lag_h": best_raw["lag_h"], "r": round(best_raw["r_raw"], 4)},
        "best_diff_lag": {"lag_h": best_dif["lag_h"], "r": round(best_dif["r_diff"], 4)},
        "best_detrend_lag": {"lag_h": best_det["lag_h"], "r": round(best_det["r_detrend"], 4)},
        "lag_table": lag_rows,
        "detrend_table": detrend_rows,
        "models": {
            "A_persistence": {"form": f"level_63(t+{L}) = level_63(t)"},
            "B_level_transfer": {
                "form": f"level_63(t+{L}) = {cB[0]:.3f} + {cB[1]:.3f} * level_62(t)" if cB else None},
            "C_persistence_plus_upstream_change": {
                "form": (f"level_63(t+{L}) = level_63(t) + {cC[0]:.3f} + {cC[1]:.3f} * "
                         f"(level_62(t) - level_62(t-{L}))") if cC else None},
        },
        "evaluation": {
            "lag_h": L,
            "train_n": len(train_keys),
            "test_n": len(test_keys),
            "event_n": len(event_keys),
            "test_rmse_m": {m: round(rmse(*preds[m]), 4) for m in ("A", "B", "C")},
            "event_rmse_m": {m: round(rmse(*ev_preds[m]), 4) for m in ("A", "B", "C")},
            "test_r_B": round(r_test, 4) if r_test is not None else None,
        },
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- markdown ----
    ev = out["evaluation"]
    t_rmse, e_rmse = ev["test_rmse_m"], ev["event_rmse_m"]
    best_test = min(t_rmse, key=lambda m: t_rmse[m] if t_rmse[m] is not None else 9e9)

    L_ = []
    L_.append("# ทำนายท้ายน้ำ ท่าช้าง (63) จาก Ny.7 — สัญญาณจริงหรือเทรนด์ร่วม? (P3)\n")
    L_.append("> ## ⚠️ ขอบเขตจำกัด — อ่านคู่กับ `analysis/goal4_thachang_model.md` (ทดสอบหลายฤดู)\n"
              "> เอกสารนี้ทดสอบ **30 วันเท่านั้น** (ฝึก 1–20 ก.ย. · ทดสอบ 21–30 ก.ย.)\n"
              "> เมื่อทดสอบบน **หลายฤดู** (ฝึก 2024+2025 · ทดสอบ 2026) พบว่า\n"
              "> **สัมประสิทธิ์ ΔNy.7 ยุบจาก 0.173 → 0.002** → โมเดล B **เท่ากับ persistence เป๊ะ**\n"
              "> → ข้อสรุป \"ดีกว่า persistence 27%\" **ไม่ generalize — ใช้ได้เฉพาะหน้าต่างฝึก 20 วันของการทดสอบนี้**\n"
              "> เหตุผลเชิงกายภาพ: สถานีนี้อยู่ **ท้าย ปตร.ท่าช้าง** (ประตูระบายน้ำ) → ระดับถูกกำหนดโดยบาน\n"
              "> ไม่ใช่ปริมาณน้ำที่ไหลมา — กลไกเดียวกับคลองสายใหญ่ (P1)\n")
    L_.append(f"ข้อมูล: `data/20_multistation_levels/` · ชั่วโมงร่วม (มีทั้งสองจุด) {out['common_hours']} · "
              f"ท่าช้างมีข้อมูล {out['target_hours']} ชม.\n")
    L_.append("## 1. คำถามที่ต้องตอบ\n")
    L_.append("r ดิบ 0.95 อาจเป็น **recession ร่วม** (สองจุดลดตามฤดูพร้อมกัน) ไม่ใช่ routing จริง\n")
    L_.append("## 2. แยกสามทาง\n")
    L_.append("| วิธี | lag ที่ดีสุด | r | อ่านว่า |")
    L_.append("|---|---:|---:|---|")
    L_.append(f"| ระดับดิบ | +{best_raw['lag_h']} ชม. | **{best_raw['r_raw']:+.3f}** | สูง — แต่ปนเทรนด์ฤดู |")
    L_.append(f"| ผลต่าง 1 ชม. (ลบเทรนด์) | +{best_dif['lag_h']} ชม. | **{best_dif['r_diff']:+.3f}** | "
              f"{'สัญญาณยังอยู่' if abs(best_dif['r_diff'] or 0) > 0.3 else 'สัญญาณจางมาก'} |")
    L_.append(f"| detrend (ลบ rolling mean 25 ชม.) | +{best_det['lag_h']} ชม. | **{best_det['r_detrend']:+.3f}** | "
              f"{'สัญญาณยังอยู่' if abs(best_det['r_detrend'] or 0) > 0.3 else '**สัญญาณจางมาก**'} |")
    L_.append("")
    L_.append("## 3. เทียบ 3 โมเดล — เทรน 1–20 ก.ย. · ทดสอบ 21–30 ก.ย.\n")
    L_.append(f"ที่ lag **+{L} ชม.** · train {ev['train_n']} · test {ev['test_n']} · event (26–30 ก.ย.) {ev['event_n']}\n")
    L_.append("| โมเดล | สูตร | RMSE test (ม.) | RMSE ช่วงเหตุการณ์ (ม.) |")
    L_.append("|---|---|---:|---:|")
    labels = {
        "A": ("A persistence", "level_63(t+L) = level_63(t)"),
        "B": ("B level transfer", out["models"]["B_level_transfer"]["form"]),
        "C": ("C persistence + ΔNy.7", out["models"]["C_persistence_plus_upstream_change"]["form"]),
    }
    for m in ("A", "B", "C"):
        lab, form = labels[m]
        star = " ⭐" if m == best_test else ""
        L_.append(f"| **{lab}**{star} | `{form}` | {t_rmse[m]} | {e_rmse[m]} |")
    L_.append("")
    L_.append(f"→ **ตัวที่ RMSE ต่ำสุดบน test = {labels[best_test][0]}**")
    if best_test == "A":
        L_.append("→ **Ny.7 ไม่ได้ให้ข้อมูลเกินกว่า persistence** ในช่วงที่ทดสอบ — r สูงเป็นเพราะเทรนด์ร่วม")
    L_.append("")
    L_.append("## 4. ตาราง lag (ระดับดิบ vs ผลต่าง)\n")
    L_.append("| lag (ชม.) | r ระดับดิบ | r ผลต่าง |")
    L_.append("|---:|---:|---:|")
    for r in lag_rows:
        if r["lag_h"] % 2 == 1:
            rr = f"{r['r_raw']:+.3f}" if r["r_raw"] is not None else "—"
            rd = f"{r['r_diff']:+.3f}" if r["r_diff"] is not None else "—"
            L_.append(f"| +{r['lag_h']} | {rr} | {rd} |")
    L_.append("")
    L_.append("> **อ่านตารางนี้ให้ดี:** r ระดับดิบ *แกว่งตาม lag* (ขึ้น 0.96 ที่ +13, ตก 0.78 ที่ +21, "
              "กลับขึ้น 0.96 ที่ +35) — เป็นลายเซ็นของ **เทรนด์/รอบวันร่วม** ไม่ใช่เวลาที่น้ำเดินทาง\n"
              "> r ผลต่าง (ตัดเทรนด์) พีคที่ +11…+13 ชม. (r≈0.52) — **นี่คือหลักฐานเดียวที่หนุนว่ามีเวลาน้ำเดินทางจริง**\n")
    OUT_MD.write_text("\n".join(L_) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON.name} + {OUT_MD.name}")
    print(f"best raw lag +{best_raw['lag_h']}h r={best_raw['r_raw']:.3f} | "
          f"diff lag +{best_dif['lag_h']}h r={best_dif['r_diff']:.3f} | "
          f"detrend +{best_det['lag_h']}h r={best_det['r_detrend']:.3f}")
    print(f"test RMSE  A={t_rmse['A']} B={t_rmse['B']} C={t_rmse['C']}  (best={best_test})")
    print(f"event RMSE A={e_rmse['A']} B={e_rmse['B']} C={e_rmse['C']}")


if __name__ == "__main__":
    main()
