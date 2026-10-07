# ขยาย "สูตรทำนายระดับน้ำ" จาก Ny.7 จุดเดียว → ทุกจุดที่มีข้อมูลย้อนหลายฤดูพอฝึกได้
# จุดที่ฝึกได้จริง (ข้อมูล 15 นาที 4–5 ฤดูจาก khundan-tele): Ny.7 (ตัวเมือง — โมเดลหลักแยกอยู่
# ใน goal4_model_v1.py), Ny.1B (ใกล้เขื่อน), ท้ายน้ำปตร.ท่าช้าง — อีก 16 จุด (คลองสายใหญ่/ปตร.
# สาขา) มีข้อมูลเฉพาะช่วงเหตุการณ์ ~30 วัน ยังฝึกไม่ได้ (ดูข้อเสนอเป้าหมาย 5 เรื่องเก็บข้อมูลย้อนหลัง)
# วิธีเดียวกับ goal4_model_backtest_long.py: leave-one-season-out + โฟลด์เหตุการณ์ 69
# ผล: analysis/goal4_model_multistation.json + report/assets/m_multistation.png
import csv, json, datetime as dt
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression

BASE = Path(__file__).resolve().parent
D16 = BASE.parent / "data" / "16_training_data"
ASSETS = BASE.parent / "report" / "assets"
YEARS = [2021, 2022, 2024, 2025]

def load_file(fn):
    d = {}
    for r in csv.reader(open(fn, encoding="utf-8")):
        if r[0] == "datetime" or not r[0]:
            continue
        d[dt.datetime.fromisoformat(r[0])] = float(r[1]) if r[1] not in ("", "-") else np.nan
    return d

def despike(d, thr=0.5):
    ts = sorted(d)
    lv = np.array([d[t] for t in ts])
    bad = np.zeros(len(ts), bool)
    for i in range(1, len(ts) - 3):
        if abs(lv[i] - lv[i - 1]) > thr and abs(lv[i] - lv[i + 3]) < thr * 0.6:
            bad[i] = bad[i + 1] = bad[i + 2] = True
    good = np.where(~bad)[0]
    return dict(zip(ts, np.interp(np.arange(len(ts)), good, lv[good])))

RANGE = {"Ny7": (0.0, 13.0), "Ny1B": (0.5, 15.0), "ThaChang_tail": (0.0, 15.0)}
def load_station(fn, st):
    lo, hi = RANGE[st]
    return {t: v for t, v in load_file(fn).items() if lo <= v <= hi}

series = {}
for st in ("Ny7", "Ny1B", "ThaChang_tail"):
    series[st] = {}
    for y in YEARS:
        series[st][y] = despike(load_station(D16 / f"khundan_15min_{st}_FULLYEAR{y}.csv", st))
    series[st][2026] = load_file(D16 / f"khundan_15min_{st}_Jun-Oct2026.csv")

SEGS, TALL = [], []
HL = {st: [] for st in series}
for y in sorted(series["Ny7"]):
    t0, t1 = (dt.datetime(2026, 6, 1), dt.datetime(2026, 10, 4, 23, 0)) if y == 2026 else (dt.datetime(y, 1, 1), dt.datetime(y, 12, 31, 23, 0))
    grid = [t0 + dt.timedelta(hours=h) for h in range(int((t1 - t0).total_seconds() // 3600) + 1)]

    def hourly(d):
        out = np.full(len(grid), np.nan)
        idx = {t: i for i, t in enumerate(grid)}
        bucket = {}
        for t, v in d.items():
            h = t.replace(minute=0)
            if h in idx and np.isfinite(v):
                bucket.setdefault(h, []).append(v)
        for h, vals in bucket.items():
            out[idx[h]] = np.mean(vals)
        good = np.where(np.isfinite(out))[0]
        if len(good):
            out = np.interp(np.arange(len(grid)), good, out[good])
        return out

    for st in series:
        HL[st].append(hourly(series[st][y]))
    TALL += grid
    SEGS.append((y, len(TALL) - len(grid), len(TALL)))

H = {st: np.concatenate(HL[st]) for st in HL}
grid = TALL
rain_pw = {}
for r in csv.reader(open(D16 / "power_rain_daily_3pts_2021_2026.csv", encoding="utf-8")):
    if r[0] != "date":
        rain_pw[r[0]] = (float(r[1]) + float(r[3])) / 2
from rain_window import windows_for_grid
R24, R72, R168 = (windows_for_grid(rain_pw, grid, (1, 3, 7))[n] for n in (1, 3, 7))

def at(a, i, back):
    j = i - back
    return a[j] if j >= 0 else np.nan

# ตัวอย่างร่วม: ฟีเจอร์ = ระดับตัวเอง (t/t−3/t−24/Δ6h) + Ny.7 ณ t (สังเกตแล้ว — ไม่มีอนาคตรั่ว) + ฝน 1/3/7 วัน
X_all, Y_all, T_all, TGT = [], [], [], []
seg_ok = np.zeros(len(grid), bool)
for _, s, e in SEGS:
    seg_ok[s + 24 * 8:e] = True
for i in range(len(grid)):
    if not seg_ok[i]:
        continue
    for tgt, other in (("Ny1B", H["Ny7"]), ("ThaChang_tail", H["Ny7"])):
        h = H[tgt]
        X_all.append([h[i], at(h, i, 3), at(h, i, 24), h[i] - at(h, i, 6),
                      other[i], R24[i], R72[i], R168[i]])
        _, s, e = next((ys, ss, ee) for ys, ss, ee in SEGS if ss <= i < ee)
        Y_all.append([h[i + 24] if i + 24 < e else np.nan])
        T_all.append(grid[i])
        TGT.append(tgt)

X_all = np.array(X_all); Y_all = np.array(Y_all)
T_all = np.array(T_all); TGT = np.array(TGT)
ok = np.isfinite(Y_all).all(1) & np.isfinite(X_all).all(1)
X_all, Y_all, T_all, TGT = X_all[ok], Y_all[ok], T_all[ok], TGT[ok]
plaus = (Y_all[:, 0] > -1.0) & (Y_all[:, 0] < 16.0)
X_all, Y_all, T_all, TGT = X_all[plaus], Y_all[plaus], T_all[plaus], TGT[plaus]

TARGETS = {
    "Ny1B": ("Ny.1B บ้านเขานางบวช (ใกล้เขื่อน)", None),
    "ThaChang_tail": ("ท้ายน้ำ ปตร.ท่าช้าง (ท้ายลุ่ม)", None),
}
out = {"method": "leave-one-season-out (ปีที่ทดสอบถูกถอดออกจากชุดฝึก) · สูตรเส้นตรง 8 ตัวแปร: ระดับตัวเอง t/t−3/t−24/Δ6h + ระดับ Ny.7 ณ t + ฝน POWER 1/3/7 วัน · ทำนาย +24 ชม.",
       "stations": {}}
preds = {}
for tgt, (label, _) in TARGETS.items():
    m = TGT == tgt
    Xs, Ys, Ts = X_all[m], Y_all[m], T_all[m]
    YR = np.array([t.year for t in Ts])
    st_out = {"label": label}
    T, yte, p = None, None, None
    for y in [2021, 2022, 2024, 2025, "2026"]:
        if y == "2026":
            tr = Ts < dt.datetime(2026, 9, 20)
            te = (Ts >= dt.datetime(2026, 9, 20)) & (YR == 2026)
        else:
            tr, te = YR != y, YR == y
        if te.sum() < 100:
            continue
        mod = LinearRegression().fit(Xs[tr], Ys[tr, 0])
        pr = mod.predict(Xs[te]); yy = Ys[te, 0]
        wet = np.array([dt.datetime(t.year, 6, 1) <= t <= dt.datetime(t.year, 10, 31) for t in Ts[te]])
        f = st_out.setdefault("folds", {}).setdefault(str(y), {})
        f["n_test"] = int(te.sum())
        f["rmse24_all"] = round(float(np.sqrt(np.mean((pr - yy) ** 2)) * 100), 1)
        f["rmse24_wet"] = round(float(np.sqrt(np.mean((pr[wet] - yy[wet]) ** 2)) * 100), 1)
        f["persistence24_wet"] = round(float(np.sqrt(np.mean((Xs[te, 0][wet] - yy[wet]) ** 2)) * 100), 1)
        if y == "2026":
            T, yte, p = Ts[te], yy, pr
    out["stations"][tgt] = st_out
    if T is not None:
        preds[tgt] = (T, yte, p)
    w = st_out["folds"]
    print(tgt, "| ฤดูน้ำหลาก (ซม.):", {y: w[y]["rmse24_wet"] for y in w}, "| persistence:", {y: w[y]["persistence24_wet"] for y in w})

json.dump(out, open(BASE / "goal4_model_multistation.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- กราฟ 2 แผง (เหตุการณ์ 69) ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]
THAI_M = {1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
          7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."}
def _thai_day(x, pos):
    d = mdates.num2date(x)
    return f"{d.day} {THAI_M[d.month]}"
THAI_DAY_FMT = FuncFormatter(_thai_day)

fig, axes = plt.subplots(len(preds), 1, figsize=(9.2, 4.4 * len(preds)), dpi=130)
axes = np.atleast_1d(axes)
for ax, (tgt, label) in zip(axes, TARGETS.items()):
    if tgt not in preds:
        continue
    T, yte, p = preds[tgt]
    ev = np.array([dt.datetime(2026, 9, 23) <= t <= dt.datetime(2026, 10, 3) for t in T])
    ax.plot(T[ev], yte[ev], "k-", lw=2, label="ระดับจริง")
    ax.plot(T[ev], p[ev], "-", color="#d62728", lw=1.5, label="ทำนายล่วงหน้า 24 ชม. (สูตร)")
    f26 = out["stations"][tgt]["folds"]["2026"]
    ax.set_title(f"{label} — RMSE เหตุการณ์ {f26['rmse24_wet']} ซม. (ทั้งฤดู {f26['rmse24_all']} ซม. · คงที่ {f26['persistence24_wet']} ซม.)", fontsize=10)
    ax.xaxis.set_major_formatter(THAI_DAY_FMT)
    ax.legend(fontsize=8.5, loc="upper left"); ax.grid(alpha=0.3)
    ax.set_ylabel("ม.")
axes[0].set_title(TARGETS["Ny1B"][0] + " (ม.)", fontsize=10)
fig.suptitle("สูตรทำนายระดับน้ำล่วงหน้า 24 ชม. — จุดวัดอื่นนอกจากตัวเมือง (ทดสอบเหตุการณ์ 69) — AI จัดทำ ควรตรวจทานโดยผู้เชี่ยวชาญ", fontsize=10.5, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(ASSETS / "m_multistation.png")
plt.close(fig)
print("saved", ASSETS / "m_multistation.png")
