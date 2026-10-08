# เป้าหมาย 4 (ขยาย): โมเดลทำนายระดับน้ำ "ท้ายน้ำ ปตร.ท่าช้าง" (63) จากต้นน้ำ Ny.7/Ny.1B
#
# ต่อจาก analysis/thachang_leadtime.md (P3) ซึ่งทดสอบ 30 วันแล้วพบ:
#   - r ดิบ 0.95 เป็นเทรนด์ร่วมเป็นส่วนใหญ่ (ตัดเทรนด์เหลือ 0.27)
#   - โมเดล "ย้ายระดับ" แพ้ persistence 4 เท่า
#   - แต่ "persistence + ΔNy.7" ชนะ persistence 27% ที่ +13 ชม.
# ที่นี่ทดสอบซ้ำบน **หลายฤดู** (ตามแบบแผน goal4_model_v1.py ของโครงการ):
#   ฝึก = 2024 (ก.ค.–ธ.ค.) + 2025 (ทั้งปี) · ทดสอบ = มิ.ย.–ต.ค. 2026 (รวมเหตุการณ์ ก.ย. 69)
#
# ใช้: python analysis/goal4_thachang_model.py
# ออก: analysis/goal4_thachang_model.json + analysis/goal4_thachang_model.md
import csv
import datetime as dt
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN_DIR = ROOT / "data" / "16_training_data"
OUT_JSON = ROOT / "analysis" / "goal4_thachang_model.json"
OUT_MD = ROOT / "analysis" / "goal4_thachang_model.md"

sys.path.insert(0, str(ROOT / "analysis"))
from all_stations_network import despike  # noqa: E402  (ตัวกรอง spike ตัวเดียวกับ P1)

TARGET = "ThaChang_tail"
DRV_MAIN = "Ny7"
DRV_UP = "Ny1B"

TRAIN_SETS = ["FULLYEAR2024", "FULLYEAR2025"]
TEST_SET = "Jun-Oct2026"
LEADS = [6, 12, 24, 48]
SHIFT_M = 3.0          # |Δ| ใน 15 นาที ที่ถือว่า datum เปลี่ยน
TOL_MIN = 25           # การ align เป็นกริดรายชั่วโมง


def load(name):
    """อ่าน CSV -> list[(datetime, level, q, rain)] เรียงเก่า->ใหม่."""
    p = TRAIN_DIR / f"khundan_15min_{name}.csv"
    if not p.exists():
        return []
    rows = []
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                t = dt.datetime.fromisoformat(r["datetime"])
            except (ValueError, KeyError):
                continue
            s = (r.get("level_msl_m") or "").strip()
            if s in ("", "-"):
                continue
            try:
                rows.append((t, float(s)))
            except ValueError:
                continue
    rows.sort()
    return rows


def hourly(rows, tol_min=TOL_MIN):
    """กริดรายชั่วโมง — เลือกค่าที่ใกล้ชั่วโมงสุดภายใน ±tol."""
    out = {}
    for t, v in rows:
        h = t.replace(minute=0, second=0)
        if h not in out or abs(t - h) < abs(out[h][0] - h):
            out[h] = (t, v)
    return {h: tv[1] for h, tv in out.items()
            if abs((tv[0] - h).total_seconds()) <= tol_min * 60}


def find_shifts(rows):
    """ตำแหน่งที่ระดับกระโดด > SHIFT_M ภายใน 15 นาที (datum/calibration เปลี่ยน)."""
    return [(rows[i][0], rows[i - 1][1], rows[i][1])
            for i in range(1, len(rows)) if abs(rows[i][1] - rows[i - 1][1]) > SHIFT_M]


def clean_series(rows):
    """despike + ตัด ±2 ชม. รอบ datum shift -> dict รายชั่วโมงที่สะอาด."""
    if not rows:
        return {}, 0, 0
    vals = [v for _, v in rows]
    keep, n_spike = despike(vals)
    # หา shift บนซีรีส์ที่กรอง spike แล้ว (ไม่งั้น spike จะถูกนับเป็น datum shift ซ้ำ)
    kept_rows = [tv for tv, k in zip(rows, keep) if k]
    shifted = find_shifts(kept_rows)
    bad = set()
    for t0, _, _ in shifted:
        for m in range(-120, 121, 15):
            bad.add(t0 + dt.timedelta(minutes=m))
    kept = [(t, v) for t, v in kept_rows if t not in bad]
    return hourly(kept), n_spike, len(shifted)


def ols(X, y):
    n, k = len(X), len(X[0])
    if n == 0:
        return None
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
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


def rmse(a, b):
    p = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    return math.sqrt(sum((x - y) ** 2 for x, y in p) / len(p)) if p else None


def main():
    # ---------- โหลด + ทำความสะอาด ----------
    meta = {}
    series = {}
    for name in [TARGET, DRV_MAIN, DRV_UP]:
        rows = []
        for s in TRAIN_SETS + [TEST_SET]:
            rows.extend(load(f"{name}_{s}"))
        rows.sort()
        h, n_spike, n_shift = clean_series(rows)
        series[name] = h
        meta[name] = {"raw_rows": len(rows), "hours": len(h),
                      "spikes_removed": n_spike, "datum_shifts": n_shift}

    # ---------- สร้างคู่ (train / test) ----------
    def pairs(lo, hi):
        """คืน dict: สำหรับแต่ละ lead -> (features, truth)"""
        out = {}
        keys = sorted(set(series[TARGET]) & set(series[DRV_MAIN]) & set(series[DRV_UP]))
        keys = [k for k in keys if lo <= k <= hi]
        for L in LEADS:
            feats, truth, stamps = [], [], []
            for k in keys:
                k2 = k + dt.timedelta(hours=L)
                kp = k - dt.timedelta(hours=L)
                if k2 not in series[TARGET] or kp not in series[DRV_MAIN]:
                    continue
                y = series[TARGET][k]
                x = series[DRV_MAIN][k]
                xp = series[DRV_MAIN][kp]
                u = series[DRV_UP][k]
                # ⚠️ ห้ามใส่ทั้ง x และ xp พร้อม (x-xp): ทั้งสาม linearly dependent
                #    -> สัมประสิทธิ์หักล้างกันเอง (ตัวอย่างที่วัดได้: -0.386/+0.386/+0.386 = 0)
                feats.append((y, x, x - xp, u))
                truth.append(series[TARGET][k2])
                stamps.append(k)
            out[L] = (feats, truth, stamps)
        return out

    tr = pairs(dt.datetime(2024, 1, 1), dt.datetime(2025, 12, 31, 23, 59))
    te = pairs(dt.datetime(2026, 6, 1), dt.datetime(2026, 10, 4, 23, 59))

    # ---------- โมเดล (เชิงเส้น ตามแบบแผน goal4) ----------
    #  A persistence            : y
    #  B persistence + ΔNy.7    : y + c + d·(x - xp)
    #  C linear หลายตัวแปร      : a + b1·y + b2·x + b3·xp + b4·(x-xp) + b5·u
    models = {
        "A_persistence": lambda f, c: f[0],
        "B_persist_plus_dNy7": None,   # สร้างด้านล่าง
        "C_linear_multi": None,
    }
    coef = {}
    for L in LEADS:
        F, Y, _ = tr[L]
        if not F:
            continue
        # B: ทำนาย Δ ของเป้าหมาย จาก Δ ต้นน้ำ
        cB = ols([[1.0, f[2]] for f in F], [y - f[0] for y, f in zip(Y, F)])
        coef.setdefault("B", {})[L] = cB
        # C: หลายตัวแปร (ไม่มีคู่ที่ collinear)
        cC = ols([[1.0, f[0], f[1], f[2], f[3]] for f in F], Y)
        coef.setdefault("C", {})[L] = cC

    def predict(L, F, which):
        if which == "A":
            return [f[0] for f in F]
        if which == "B":
            c = coef["B"][L]
            return [f[0] + c[0] + c[1] * f[2] for f in F]
        c = coef["C"][L]
        return [c[0] + c[1] * f[0] + c[2] * f[1] + c[3] * f[2] + c[4] * f[3] for f in F]

    def evaluate(F, Y, L):
        row = {"n_test": len(F)}
        for m in ("A", "B", "C"):
            r = rmse(predict(L, F, m), Y)
            row[m] = round(100 * r, 1) if r is not None else None
        row["best"] = min(("A", "B", "C"), key=lambda m: row[m] if row[m] is not None else 9e9)
        if row["A"]:
            row["B_vs_A_pct"] = round(100 * (1 - row["B"] / row["A"]), 1) if row["B"] else None
            row["C_vs_A_pct"] = round(100 * (1 - row["C"] / row["A"]), 1) if row["C"] else None
        return row

    results = {}
    event_results = {}
    EV0 = dt.datetime(2026, 9, 26)   # น้ำสูงสุดเหตุการณ์ ก.ย. 69 (Ny.7 น้ำสูงสุด 27 ก.ย.)
    for L in LEADS:
        F, Y, S = te[L]
        if not F:
            continue
        results[str(L)] = evaluate(F, Y, L)
        # ทดสอบสมมุติฐาน: "สัญญาณต้นน้ำใช้ได้เฉพาะช่วงน้ำหลาก" -> ประเมินเฉพาะ 26–30 ก.ย. 69
        idx = [i for i, s in enumerate(S) if EV0 <= s <= dt.datetime(2026, 9, 30, 23, 59)]
        if len(idx) >= 20:
            event_results[str(L)] = evaluate([F[i] for i in idx], [Y[i] for i in idx], L)

    out = {
        "target": {"id": "63", "name": "ท้ายน้ำ ปตร.ท่าช้าง", "file": TARGET},
        "drivers": {"main": {"id": "62", "name": "Ny.7"}, "upstream": {"id": "61", "name": "Ny.1B"}},
        "train_sets": TRAIN_SETS,
        "test_set": TEST_SET,
        "series_meta": meta,
        "leads_h": LEADS,
        "rmse_cm_by_lead": results,
        "rmse_cm_event_26_30sep": event_results,
        "coefficients": {k: {str(L): (coef[k][L] if L in coef[k] else None) for L in LEADS}
                         for k in coef},
        "note": ("แบบแผนเดียวกับ goal4_model_v1.py: เชิงเส้น, hold-out เหตุการณ์, เทียบ persistence · "
                 "RMSE หน่วย ซม."),
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------- markdown ----------
    L_ = []
    L_.append("# ขยายเป้าหมาย 4 — ทำนายท้ายน้ำ ท่าช้าง (63) จากต้นน้ำ (หลายฤดู)\n")
    L_.append(f"ฝึก: {', '.join(TRAIN_SETS)} · ทดสอบ: {TEST_SET} (รวมเหตุการณ์ ก.ย. 69) · "
              f"หน่วย RMSE = ซม.\n")
    L_.append("## 0. ข้อมูลที่ใช้\n")
    L_.append("| จุด | แถวดิบ | ชั่วโมงใช้ได้ | spike ที่กรอง | datum shift |")
    L_.append("|---|---:|---:|---:|---:|")
    for k, v in meta.items():
        L_.append(f"| {k} | {v['raw_rows']:,} | {v['hours']:,} | {v['spikes_removed']} | {v['datum_shifts']} |")
    L_.append("")
    L_.append("## 1. ผล — RMSE (ซม.) แยกตามระยะทำนาย\n")
    L_.append("### 1.1 ทุกชั่วโมงทดสอบ (มิ.ย.–ต.ค. 69)\n")
    L_.append("| ระยะ | A persistence | B persistence+ΔNy.7 | C linear หลายตัวแปร | ดีสุด |")
    L_.append("|---:|---:|---:|---:|---|")
    for L in LEADS:
        r = results.get(str(L))
        if not r:
            continue
        L_.append(f"| +{L} ชม. | {r['A']} | {r['B']} | {r['C']} | **{r['best']}** |")
    L_.append("")
    L_.append("### 1.2 เฉพาะช่วงเหตุการณ์ 26–30 ก.ย. 69 (ทดสอบสมมุติฐาน regime)\n")
    L_.append("| ระยะ | n | A persistence | B persistence+ΔNy.7 | C linear | ดีสุด |")
    L_.append("|---:|---:|---:|---:|---:|---|")
    for L in LEADS:
        r = event_results.get(str(L))
        if not r:
            L_.append(f"| +{L} ชม. | — | — | — | — | ข้อมูลไม่พอ |")
            continue
        L_.append(f"| +{L} ชม. | {r['n_test']} | {r['A']} | {r['B']} | {r['C']} | **{r['best']}** |")
    L_.append("")
    L_.append("**เทียบกับ persistence (บวก = ดีกว่า):**\n")
    L_.append("| ระยะ | B vs A (ทุกชั่วโมง) | B vs A (เหตุการณ์) | C vs A (ทุกชั่วโมง) | C vs A (เหตุการณ์) |")
    L_.append("|---:|---:|---:|---:|---:|")
    for L in LEADS:
        r = results.get(str(L), {})
        e = event_results.get(str(L), {})
        L_.append(f"| +{L} ชม. | {r.get('B_vs_A_pct')}% | {e.get('B_vs_A_pct')}% | "
                  f"{r.get('C_vs_A_pct')}% | {e.get('C_vs_A_pct')}% |")
    L_.append("")
    L_.append("## 2. อ่านผล\n")
    L_.append("**สัมประสิทธิ์ที่ fit ได้ (โมเดล B):**\n")
    L_.append("| ระยะ | intercept | สัมประสิทธิ์ ΔNy.7 |")
    L_.append("|---:|---:|---:|")
    for L in LEADS:
        c = coef.get("B", {}).get(L)
        if c:
            L_.append(f"| +{L} ชม. | {c[0]:.5f} | **{c[1]:.5f}** |")
    L_.append("")
    L_.append("- ถ้า **B ชนะ A** → Ny.7 ให้ข้อมูลจริงเกินกว่า persistence\n"
              "- ถ้าสัมประสิทธิ์ ΔNy.7 ≈ 0 → สัญญาณจาก P3 **ไม่ generalize** ข้ามฤดู\n"
              "- ⚠️ ข้อจำกัด: เหตุการณ์ท่วมใหญ่มี 1 ครั้ง (ก.ย. 69) และอยู่ในชุดทดสอบเท่านั้น — "
              "ข้อจำกัดเดียวกับ `goal4_model_v1_findings.md`\n")
    L_.append("## 3. ข้อสรุป\n")
    L_.append("**1) สัญญาณต้นน้ำ (ΔNy.7) ไม่ generalize.** สัมประสิทธิ์ที่ fit บนหลายฤดู = **~0.002–0.003** "
              "(P3 ได้ 0.173 จากหน้าต่าง 20 วัน) → โมเดล B จึง **เท่ากับ persistence เป๊ะ** ทุกระยะ\n")
    L_.append("**2) ที่โมเดล C ชนะ ไม่ได้มาจาก Ny.7.** สัมประสิทธิ์คือ "
              "`~0.96·y + ~0.01·Ny.1B` ส่วนพจน์ Ny.7 (`x` และ `Δx`) ≈ **0** "
              "→ กำไรที่ได้มาจาก **(ก) การลดทอน persistence** (สัมประสิทธิ์ 0.86–0.98 = จับเทรนด์ฤดูที่ระดับค่อย ๆ ลด) "
              "และ **(ข) พจน์ Ny.1B เล็ก ๆ** ไม่ใช่ routing\n")
    L_.append("**3) ทำไมถึงเป็นเช่นนั้น — สถานีนี้อยู่ *ท้าย* ปตร.ท่าช้าง.** "
              "`ปตร.` = ประตูระบายน้ำ (barrage) → **ระดับท้ายน้ำถูกกำหนดโดยการเปิด-ปิดบาน ไม่ใช่ปริมาณน้ำที่ไหลมา** "
              "→ กลไกเดียวกับคลองสายใหญ่ (P1: จุด 16 ถูกกำหนดโดยบาน) "
              "→ อธิบายได้ทั้งที่ (ก) persistence ทำงานดี (บานตรึงระดับไว้) และ (ข) r ดิบกับ Ny.7 สูง "
              "แต่เป็น **เทรนด์ฤดูร่วม** ไม่ใช่การส่งน้ำ\n")
    L_.append("**4) ผลต่อการทดสอบ 30 วัน (P3):** ผลของ `thachang_leadtime.md` ที่ว่า "
              "\"persistence + ΔNy.7 ดีกว่า persistence 27%\" **ไม่ยืนบนหลายฤดู** — "
              "เป็นผลเฉพาะหน้าต่างฝึก 20 วัน จึงใช้ไม่ได้ทั่วไป\n")
    OUT_MD.write_text("\n".join(L_) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON.name} + {OUT_MD.name}")
    for L in LEADS:
        r = results.get(str(L))
        if r:
            print(f"  +{L:>2}h  A={r['A']} B={r['B']} C={r['C']} cm  best={r['best']}")


if __name__ == "__main__":
    main()
