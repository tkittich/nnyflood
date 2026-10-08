# เป้าหมาย #4 โมเดล v1: เทียบ "สูตรง่ายโปร่งใส" vs "machine learning" ในการทำนายระดับน้ำ Ny.7
# ข้อมูล: khundan-tele 15 นาที 1 มิ.ย.–4 ต.ค. 69 (Ny.7 เป้าหมาย, Ny.1B ต้นน้ำ, ท้ายน้ำท่าช้าง) + ฝนรายวัน TMD
# แบ่งชุด: ฝึก <= 19 ก.ย. / ทดสอบ 20 ก.ย.–4 ต.ค. (ครอบเหตุการณ์)
# ผู้จัดทำ: AI — ผลเป็นการทดลองเบื้องต้น ควรตรวจทานโดยผู้เชี่ยวชาญ
import csv, json, re, datetime as dt
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import HistGradientBoostingRegressor
from common import BANKFULL_MSL

BASE = Path(__file__).resolve().parent
D16 = BASE.parent / "data" / "16_training_data"

# ---------- โหลด + ทำความสะอาด (หลายปี: 2024/2025/2026 ถ้ามีไฟล์) ----------
def load_years(name):
    """คืน dict ปี -> dict เวลา -> (ระดับ, Q) จากทุกไฟล์ khundan_15min_{name}_Jun-Oct*.csv"""
    out = {}
    for fn in sorted(D16.glob(f"khundan_15min_{name}_Jun-Oct*.csv")):
        yr = int(re.search(r"(\d{4})\.csv$", fn.name).group(1))
        d = {}
        for r in csv.reader(open(fn, encoding="utf-8")):
            if r[0] == "datetime" or not r[0]:
                continue
            t = dt.datetime.fromisoformat(r[0])
            lv = float(r[1]) if r[1] not in ("", "-") else np.nan
            q = float(r[2]) if len(r) > 2 and r[2] not in ("", "-") else np.nan
            d[t] = (lv, q)
        out[yr] = d
        print(f"โหลด {fn.name}: {len(d)} แถว")
    return out

ny7y, ny1y, twy = load_years("Ny7"), load_years("Ny1B"), load_years("ThaChang_tail")

def despike(d, thr=0.5):
    """จุดที่กระโดด >thr ใน 15 นาที แล้วกลับใกล้เดิมภายใน 3 ช่อง = ค่าปลอม → เติมเส้นตรง"""
    ts = sorted(d); lv = np.array([d[t][0] for t in ts])
    bad = np.zeros(len(ts), bool)
    for i in range(1, len(ts) - 3):
        if abs(lv[i] - lv[i-1]) > thr and abs(lv[i] - lv[i+3]) < thr * 0.6:
            bad[i] = bad[i+1] = bad[i+2] = True
    lv = lv.copy()
    for i in np.where(bad)[0]:
        lv[i] = np.nan
    s = pd_interp(ts, lv)
    return dict(zip(ts, s)), int(bad.sum())

def pd_interp(ts, lv):
    good = np.where(np.isfinite(lv))[0]
    return np.interp(np.arange(len(ts)), good, lv[good])

# despike(): เรียกครั้งเดียวต่อปี (ถ้าเรียกสองรอบ รอบแรกจะทิ้งผล)
ny7s, ny1s, tws = {}, {}, {}
n7spike = n1spike = 0
for yr in ny7y:
    ny7s[yr], c1 = despike(ny7y[yr])
    ny1s[yr], c2 = despike(ny1y.get(yr, {}))
    tws[yr] = twy.get(yr, {})
    n7spike += c1
    n1spike += c2

# ---------- กริดรายชั่วโมงต่อปี แล้วต่อเป็นอนุกรมเดียว (แยกช่วงด้วยเวลา) ----------
SEGS = []      # (start_idx, end_idx) ของแต่ละปี สำหรับกัน feature ข้ามปี
H7, H1, TW, TALL = [], [], [], []
for yr in sorted(ny7s):
    t0, t1 = dt.datetime(yr, 6, 1), dt.datetime(yr, 10, 4, 23, 0)
    grid = [t0 + dt.timedelta(hours=h) for h in range(int((t1 - t0).total_seconds() // 3600) + 1)]

    def hourly(d):
        out = np.full(len(grid), np.nan)
        idx = {t: i for i, t in enumerate(grid)}
        bucket = {}
        for t, v in d.items():
            lv = v[0] if isinstance(v, tuple) else v
            h = t.replace(minute=0)
            if h in idx and np.isfinite(lv):
                bucket.setdefault(h, []).append(lv)
        for h, vals in bucket.items():
            out[idx[h]] = np.mean(vals)
        good = np.where(np.isfinite(out))[0]
        if len(good):
            out = np.interp(np.arange(len(grid)), good, out[good])
        return out

    H7.append(hourly(ny7s[yr])); H1.append(hourly(ny1s.get(yr, {}))); TW.append(hourly(tws.get(yr, {})))
    TALL += grid
    SEGS.append((len(TALL) - len(grid), len(TALL)))

H7 = np.concatenate(H7); H1 = np.concatenate(H1); TW = np.concatenate(TW)
grid = TALL

# ---------- ฝนรายวัน NASA POWER (PRECTOTCORR ไม่ต้อง auth สม่ำเสมอทุกปี 2021-2026) ----------
# เซลล์กริด 0.5°: เหนือ (ครอบแถบเชิงเขาตะวันตก+ที่ราบกลาง) / ใต้ (ตัวเมือง+ปากพลี+องครักษ์ตะวันออก)
# หมายเหตุ: ปี 2023 สถานี Ny.7 ออฟไลน์ทั้งฤดู (khundan-tele คืน 0 แถว) โมเดลจึงฝึกจาก 2021/2022/2024/2025/2026
rain_pw = {}
for r in csv.reader(open(D16 / "power_rain_daily_3pts_2021_2026.csv", encoding="utf-8")):
    if r[0] == "date":
        continue
    rain_pw[r[0]] = (float(r[1]) + float(r[3])) / 2     # เฉลี่ยเซลล์เหนือ+ใต้

# ---------- หน้าต่างฝน 1/3/7 วัน ----------
# ตรรกะอยู่ที่ analysis/rain_window.py เพื่อให้ทั้ง 3 สคริปต์ใช้ตัวเดียวกัน
# (goal4_model_v1 · goal4_model_rainfcst_test · goal4_model_moisture_test)
# อ่าน docstring ในไฟล์นั้นสำหรับข้อควรระวัง (cumsum ไม่ใช่หน้าต่าง + ข้อมูลอนาคตรั่ว)
from rain_window import windows_for_grid

R24, R72, R168 = (windows_for_grid(rain_pw, grid, (1, 3, 7))[n] for n in (1, 3, 7))

# ---------- สร้างตัวอย่าง (t) ----------
def at(a, i, back):
    j = i - back
    return a[j] if j >= 0 else np.nan

# dH1B_6h ถูกตัด (8 ต.ค. 69) — เป็น H1B(t)-H1B(t-6) เป๊ะ = rank-deficient
# (predictions ไม่เปลี่ยน: column space เดิม) — ดู REVIEW.gemini.md G-04
FEATS = ["H7(t)", "H7(t-3)", "H7(t-24)", "dH7_6h", "H1B(t)", "H1B(t-6)", "H1B(t-24)",
         "TW(t)", "R24", "R72", "R168"]
HORIZONS = [6, 24, 48]
split = grid.index(dt.datetime(2026, 9, 20, 0, 0))

X_all, Y_all, T_all, TWmiss = [], [], [], []
seg_ok = np.zeros(len(grid), bool)           # True = อยู่ในปีเดียวกับประวัติย้อน 8 วัน
for s, e in SEGS:
    seg_ok[s + 24 * 8:e] = True
for i in range(len(grid)):
    if not seg_ok[i]:
        continue
    tw = TW[i]
    X_all.append([H7[i], at(H7, i, 3), at(H7, i, 24), H7[i] - at(H7, i, 6),
                  H1[i], at(H1, i, 6), at(H1, i, 24),
                  tw if np.isfinite(tw) else 2.0,      # ค่า default ตอนท้ายน้ำไม่ส่ง
                  R24[i], R72[i], R168[i]])
    TWmiss.append(0 if np.isfinite(tw) else 1)
    ok_y = any(s <= i and i + 48 < e for s, e in SEGS)   # เป้าหมาย +48 ชม. ต้องไม่ข้ามปี
    Y_all.append([H7[i + h] if ok_y else np.nan for h in HORIZONS])
    T_all.append(grid[i])

X_all = np.array(X_all); Y_all = np.array(Y_all); TWmiss = np.array(TWmiss)
ok = np.isfinite(Y_all).all(1) & np.isfinite(X_all).all(1)
X_all, Y_all, T_all, TWmiss = X_all[ok], Y_all[ok], np.array(T_all)[ok], TWmiss[ok]
tr = np.array([t < dt.datetime(2026, 9, 20) for t in T_all])
te = ~tr
print(f"ตัวอย่าง: ฝึก {tr.sum()} ชม. | ทดสอบ {te.sum()} ชม. (20 ก.ย.–4 ต.ค.) | spike ที่กรอง: Ny.7 {n7spike}, Ny.1B {n1spike}")
print(f"ท้ายน้ำหาย (ใช้ default): {TWmiss[tr].mean()*100:.0f}% (ฝึก) / {TWmiss[te].mean()*100:.0f}% (ทดสอบ)")

# ---------- โมเดล ----------
BANKFULL = BANKFULL_MSL  # ม.รทก. ≈ เกจ 8.45 ม. (ล้นตลิ่งเมือง) จาก datum 1.59 ม.
results = {}
preds = {}
for k, h in enumerate(HORIZONS):
    ytr, yte = Y_all[tr, k], Y_all[te, k]
    # 1) persistence: ทำนาย = ระดับปัจจุบัน
    p_pers = X_all[te, 0]
    # 2) สูตรเส้นตรง (คำนวณมือได้ — สัมประสิทธิ์คงที่)
    lin = LinearRegression().fit(X_all[tr], ytr)
    p_lin = lin.predict(X_all[te])
    # 3) gradient boosting (ML)
    gb = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06, max_depth=4,
                                       min_samples_leaf=40, random_state=0).fit(X_all[tr], ytr)
    p_gb = gb.predict(X_all[te])

    rows = []
    for nm, p in [("persistence", p_pers), ("linear", p_lin), ("GBDT", p_gb)]:
        rmse = np.sqrt(np.mean((p - yte) ** 2)) * 100
        mae = np.mean(np.abs(p - yte)) * 100
        # เหตุการณ์หลัก 25–30 ก.ย.
        ev = np.array([dt.datetime(2026, 9, 25) <= t <= dt.datetime(2026, 9, 30) for t in T_all[te]])
        rmse_ev = np.sqrt(np.mean((p[ev] - yte[ev]) ** 2)) * 100
        above_act = yte > BANKFULL
        above_pred = p > BANKFULL
        hit = (above_act & above_pred).sum() / above_act.sum() if above_act.sum() else np.nan
        far = (above_pred & ~above_act).sum() / above_pred.sum() if above_pred.sum() else np.nan
        rows.append((nm, rmse, mae, rmse_ev, hit, far))
    results[h] = rows
    preds[h] = (yte, p_pers, p_lin, p_gb, T_all[te])
    ipk = int(np.argmax(yte))
    print(f"\n== ทำนาย +{h} ชม. ==  น้ำสูงสุดจริง {yte[ipk]:.2f} ม. ({T_all[te][ipk]:%d %b %H:%M})")
    print(f"{'โมเดล':<12}{'RMSE ชม.(ซม.)':>14}{'MAE(ซม.)':>10}{'RMSE เหตุการณ์':>15}{'จับ>ตลิ่ง':>11}{'ระวังผิด':>10}{'น้ำสูงสุดผิด(ซม.)':>12}")
    for nm, rmse, mae, rmse_ev, hit, far in rows:
        pk_err = ({"persistence": p_pers, "linear": p_lin, "GBDT": p_gb}[nm][ipk] - yte[ipk]) * 100
        print(f"{nm:<12}{rmse:>14.1f}{mae:>10.1f}{rmse_ev:>15.1f}{hit*100:>10.0f}%{far*100:>9.0f}%{pk_err:>12.1f}")

# สัมประสิทธิ์สูตรเส้นตรง +24 ชม. (ตัวอย่างให้ผู้ใช้เห็นว่า "คำนวณมือ" หน้าตาเป็นแบบไหน)
lin24 = LinearRegression().fit(X_all[tr], Y_all[tr, 1])
print("\nสูตรเส้นตรง +24 ชม.:  H7(t+24) =")
for f, c in zip(FEATS, lin24.coef_):
    if abs(c) > 0.01:
        print(f"   {c:+.4f} × {f}")
print(f"   {lin24.intercept_:+.3f} (ค่าคงที่)")

# ---------- สัมประสิทธิ์ครบทุกตัวทุกระยะ -> goal4_linear_coeffs_full.json ----------
# ค่าสัมประสิทธิ์ครบสร้างจากโมเดลจริงในไฟล์นี้ (อ้างอิงใน DATA_DICTIONARY และรายงานวิชาการ)
coeffs_full = {}
for h, k in zip(HORIZONS, range(len(HORIZONS))):
    m = LinearRegression().fit(X_all[tr], Y_all[tr, k])
    coeffs_full[f"h{h}"] = {**{f: round(float(c), 5) for f, c in zip(FEATS, m.coef_)},
                            "const": round(float(m.intercept_), 5)}
json.dump(coeffs_full, open(BASE / "goal4_linear_coeffs_full.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nบันทึก: goal4_linear_coeffs_full.json (11 ตัวแปร × 3 ระยะ)")

# ---------- ตัวอย่างคำนวณมือ (ใช้ในรายงานฉบับประชาชน) ----------
# พิมพ์ค่าฟีเจอร์จริง + ผลแทนสูตร เพื่อให้คัดลอกลงรายงานได้ และเป็น self-check
# ว่าสูตรที่พิมพ์ออกมา "แทนค่าแล้วได้ผลตรงกับที่โมเดลทำนายจริง"
EX = dt.datetime(2026, 9, 25, 12, 0)
_i = grid.index(EX)
_exf = {"H7(t)": H7[_i], "H7(t-3)": at(H7, _i, 3), "H7(t-24)": at(H7, _i, 24),
        "dH7_6h": H7[_i] - at(H7, _i, 6), "H1B(t)": H1[_i], "H1B(t-6)": at(H1, _i, 6),
        "H1B(t-24)": at(H1, _i, 24),
        "TW(t)": TW[_i] if np.isfinite(TW[_i]) else 2.0,
        "R24": R24[_i], "R72": R72[_i], "R168": R168[_i]}
_manual = float(sum(c * _exf[f] for f, c in zip(FEATS, lin24.coef_)) + lin24.intercept_)
_actual = H7[_i + 24]
print(f"\nตัวอย่างคำนวณมือ: {EX:%d %b %H:%M} -> ทำนาย {EX + dt.timedelta(hours=24):%d %b %H:%M}")
for f in FEATS:
    print(f"   {f:<10}= {_exf[f]:>9.4f}")
print(f"   แทนสูตรได้ {_manual:.3f} ม.รทก. | ระดับจริง {_actual:.3f} | ต่าง {( _manual - _actual) * 100:+.0f} ซม.")

# ---------- Ablation: แยกดูว่า "บล็อกไหน" แบกสัญญาณ ----------
# รายงานวิชาการอ้าง ablation นี้ (ตัวเลข rerun หลังตัด dH1B_6h 8 ต.ค. 69)
# ฉบับย่อ 4 ตัวแปร แย่กว่าฉบับเต็มอย่างมีนัยสำคัญ
# -> ข้อมูลต้นน้ำ+ฝนมีสัญญาณจริง" — ตัวเลขนั้นไม่มีสคริปต์รองรับ และไม่แยกสองบล็อกออกจากกัน
# ตรวจซ้ำตรงนี้เป็น 3 แขน: เต็ม 12 / ตัดฝน (เหลือ 9) / ตัด Ny.1B+ฝน (เหลือ 4)
COMPACT = [0, 1, 2, 3]                      # H7(t), H7(t-3), H7(t-24), dH7_6h
NO_RAIN = list(range(8))                    # ตัด R24, R72, R168 ออก
ARMS = [("เต็ม 11 ตัว", None), ("ตัดฝน (8)", NO_RAIN), ("ตัด Ny.1B+ฝน (4)", COMPACT)]
ablation = {}
print(f"\nAblation — RMSE เหตุการณ์ 25–30 ก.ย. (ซม.)")
print(f"{'ระยะ':>7}" + "".join(f"{nm:>20}" for nm, _ in ARMS))
for h, k in zip(HORIZONS, range(len(HORIZONS))):
    yte = Y_all[te, k]
    ev = np.array([dt.datetime(2026, 9, 25) <= t <= dt.datetime(2026, 9, 30) for t in T_all[te]])
    vals = {}
    for nm, cols in ARMS:
        Xtr = X_all[tr] if cols is None else X_all[tr][:, cols]
        Xte = X_all[te] if cols is None else X_all[te][:, cols]
        p = LinearRegression().fit(Xtr, Y_all[tr, k]).predict(Xte)
        vals[nm] = round(float(np.sqrt(np.mean((p[ev] - yte[ev]) ** 2)) * 100), 1)
    ablation[h] = vals
    print(f"{'+' + str(h) + ' ชม.':>7}" + "".join(f"{vals[nm]:>20.1f}" for nm, _ in ARMS))
json.dump({str(h): v for h, v in ablation.items()},
          open(BASE / "goal4_model_v1_ablation.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("บันทึก: goal4_model_v1_ablation.json")

# lag จาก cross-correlation ช่วงฝึก (ต้นน้ำ→เมือง)
d1 = H1[split - 24 * 30: split] - np.nanmean(H1[split - 24 * 30: split])
d7 = H7[split - 24 * 30: split] - np.nanmean(H7[split - 24 * 30: split])
cc = [np.corrcoef(d7[:len(d7) - L], d1[L:])[0, 1] for L in range(0, 37, 3)]
best = int(np.nanargmax(cc)) * 3
print(f"\ncross-correlation Ny.1B→Ny.7 (ก.ค.–ก.ย.): lag ที่ดีสุด ~{best} ชม. (r={np.nanmax(cc):.2f})")

json.dump({str(h): [[nm, round(a, 2), round(b, 2), round(c, 2), round(d, 3), round(e, 3)]
                    for nm, a, b, c, d, e in rows] for h, rows in results.items()},
          open(BASE / "goal4_model_v1_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- กราฟ: ไฮโดรกราฟเหตุการณ์ จริง vs ทำนาย ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma", "Loma", "Garuda", "Norasi", "DejaVu Sans"]
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
THAI_M = {1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
          7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."}
def _thai_day(x, pos):
    d = mdates.num2date(x)
    return f"{d.day} {THAI_M[d.month]}"
THAI_DAY_FMT = FuncFormatter(_thai_day)


fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
for ax, h in zip(axes, HORIZONS):
    yte, p_pers, p_lin, p_gb, T = preds[h]
    ev = np.array([dt.datetime(2026, 9, 23) <= t <= dt.datetime(2026, 10, 3) for t in T])
    ax.plot([t for t, e in zip(T, ev) if e], yte[ev], "k-", lw=2, label="ระดับจริง Ny.7")
    ax.plot([t for t, e in zip(T, ev) if e], p_lin[ev], "-", color="#d62728", lw=1.4, label="สูตรเส้นตรง")
    ax.plot([t for t, e in zip(T, ev) if e], p_gb[ev], "-", color="#1f77b4", lw=1.4, label="ML (GBDT)")
    ax.plot([t for t, e in zip(T, ev) if e], p_pers[ev], ":", color="#7f7f7f", lw=1.2, label="คงที่ (persistence)")
    ax.axhline(BANKFULL, color="#d62728", ls="--", lw=0.8)
    ax.text(T[ev][-1], BANKFULL + 0.06, "ระดับล้นตลิ่งเมือง (6.86 ม.รทก.)", fontsize=8, color="#d62728", ha="right", va="bottom")
    r = results[h]
    ax.set_title(f"ทำนายล่วงหน้า +{h} ชม. — RMSE เหตุการณ์: เส้นตรง {r[1][3]:.1f} ซม. · ML {r[2][3]:.1f} ซม. · คงที่ {r[0][3]:.1f} ซม.", fontsize=10)
    ax.set_ylabel("ม.รทก."); ax.legend(loc="upper left", fontsize=8); ax.grid(alpha=0.3)
axes[-1].set_xlabel("ทดสอบนอกชุดฝึก 23 ก.ย. – 3 ต.ค. 69 (ฝึกด้วยข้อมูล 1 มิ.ย. – 19 ก.ย.)")
# กราฟฉบับประชาชน: แผงเดียว +24 ชม. (โมเดลเดียวกันทุกประการ)
_y24, _pp24, _pl24, _pg24, _T24 = preds[24]
_ev24 = np.array([dt.datetime(2026, 9, 25) <= t <= dt.datetime(2026, 9, 30) for t in _T24])
figC, axC = plt.subplots(figsize=(8.8, 4.7), dpi=130)
axC.plot([t for t, e in zip(_T24, _ev24) if e], _y24[_ev24], "k-", lw=2, label="ระดับน้ำจริง ณ Ny.7 (สะพานหน้าจวนผู้ว้าฯ)")
axC.plot([t for t, e in zip(_T24, _ev24) if e], _pl24[_ev24], "-", color="#d62728", lw=1.6, label="ทำนายล่วงหน้า 24 ชม. ด้วยสูตรในรายงาน")
axC.axhline(BANKFULL, color="#ef6c00", ls="--", lw=1)
axC.text(_T24[_ev24][-1], BANKFULL + 0.05, "ระดับล้นตลิ่ง 6.86 ม.รทก.", fontsize=8, color="#ef6c00", ha="right", va="bottom")
axC.set_ylabel("ระดับน้ำ (ม.รทก.)")
axC.set_title("ตัวอย่างผลงานสูตรทำนาย — ทดสอบนอกชุดฝึก ช่วงเหตุการณ์ 25–30 ก.ย. 69")
axC.xaxis.set_major_formatter(THAI_DAY_FMT)
axC.legend(fontsize=9, loc="upper left"); axC.grid(alpha=0.3)
figC.tight_layout()
figC.savefig(Path(__file__).resolve().parent.parent / "report" / "assets" / "m_simple24.png")
plt.close(figC)
print("saved report/assets/m_simple24.png")

fig.suptitle("เป้าหมาย #4 โมเดล: ทำนายระดับน้ำ Ny.7 — สูตรเส้นตรง vs ML (AI จัดทำ ควรตรวจทานโดยผู้เชี่ยวชาญ)")
for a in fig.axes:
    a.xaxis.set_major_formatter(THAI_DAY_FMT)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(BASE / "goal4_model_v1_event.png", dpi=130)
print("\nบันทึก: goal4_model_v1_event.png + goal4_model_v1_results.json")
