# ทดสอบย้อนหลังหลายฤดูของ "สูตรทำนายระดับน้ำ Ny.7" (โมเดลเดียวกับ goal4_model_v1.py)
# วิธี: leave-one-season-out — ปีที่ทดสอบ Y ถูกถอดออกจากชุดฝึกทั้งหมด (2021/2022/2024/2025)
#       ส่วน 2026 ใช้เงื่อนไขเดียวกับรายงานหลัก (ฝึกทุกฤดูก่อน 19 ก.ย. 69 / ทดสอบเหตุการณ์)
# ข้อมูล: khundan_15min_*_FULLYEAR{2021,2022,2024,2025}.csv (ทั้งปี) + Jun-Oct2026 (เหตุการณ์)
#         + ฝนรายวัน NASA POWER 2021–2026 · ปี 2023 สถานี Ny.7 ออฟไลน์ทั้งฤดู จึงไม่มีในชุดทดสอบ
# ผล: analysis/goal4_model_backtest_long.json + report/assets/m_backtest_long.png
# หมายเหตุ: ฝึกจากข้อมูล "ทั้งปี" 4 ฤดู — ต่างจาก goal4_model_v1.py ที่ใช้เฉพาะ มิ.ย.–ต.ค.
#           ตัวเลข RMSE ของสองสคริปต์จึงเทียบกันตรง ๆ ไม่ได้ (ดูหมายเหตุในรายงาน)
# ผู้จัดทำ: AI — ควรตรวจทานโดยผู้เชี่ยวชาญสถิติ/อุทกวิทยา
import csv, json, re, datetime as dt
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression

BASE = Path(__file__).resolve().parent
D16 = BASE.parent / "data" / "16_training_data"
ASSETS = BASE.parent / "report" / "assets"

YEARS = [2021, 2022, 2024, 2025]          # ปีที่มี FULLYEAR (2023 สถานีออฟไลน์)
HORIZONS = [6, 24, 48]

def load_file(fn):
    d = {}
    for r in csv.reader(open(fn, encoding="utf-8")):
        if r[0] == "datetime" or not r[0]:
            continue
        t = dt.datetime.fromisoformat(r[0])
        lv = float(r[1]) if r[1] not in ("", "-") else np.nan
        d[t] = lv
    return d

def despike(d, thr=0.5):
    """จุดที่กระโดด >thr ใน 15 นาที แล้วกลับใกล้เดิมภายใน 3 ช่อง = ค่าปลอม → เติมเส้นตรง"""
    ts = sorted(d)
    lv = np.array([d[t] for t in ts])
    bad = np.zeros(len(ts), bool)
    for i in range(1, len(ts) - 3):
        if abs(lv[i] - lv[i - 1]) > thr and abs(lv[i] - lv[i + 3]) < thr * 0.6:
            bad[i] = bad[i + 1] = bad[i + 2] = True
    good = np.where(~bad)[0]
    s = np.interp(np.arange(len(ts)), good, lv[good])
    return dict(zip(ts, s))

# ตัวกรองพิสัยกายภาพก่อนอะไรก็ตาม — ข้อมูลดิบ FULLYEAR มีช่วงเซนเซอร์ซ่อมบำรุงที่รายงาน
# ค่าไร้ความหมาย (เช่น Ny.1B ~11–15 เม.ย. 2021 = 0–65 ม.) ซึ่ง despike จับไม่ได้
# เพราะไม่ใช่ "กระโดดแล้วกลับ" — ตัดทิ้งเป็น NaN แล้วเติมเส้นตรงใน hourly()
RANGE = {"Ny7": (0.0, 13.0), "Ny1B": (0.5, 15.0), "ThaChang_tail": (0.0, 15.0)}

def load_station(fn, st):
    lo, hi = RANGE[st]
    return {t: v for t, v in load_file(fn).items() if lo <= v <= hi}

series = {}                                   # station -> {year: {t: level}}
for st in ("Ny7", "Ny1B", "ThaChang_tail"):
    series[st] = {}
    for y in YEARS:
        fn = D16 / f"khundan_15min_{st}_FULLYEAR{y}.csv"
        series[st][y] = despike(load_station(fn, st))
    fn26 = D16 / f"khundan_15min_{st}_Jun-Oct2026.csv"
    if fn26.exists():
        series[st][2026] = load_file(fn26)    # เหตุการณ์ 69: ข้อมูลดิบตามต้นฉบับ (v1 ไม่ despike ปี 69 — คงเดิม)

# ---------- กริดรายชั่วโมงต่อปี แล้วต่อเป็นอนุกรมเดียว ----------
SEGS, TALL = [], []
H7L, H1L, TWL = [], [], []
for y in sorted(series["Ny7"]):
    if y == 2026:
        t0, t1 = dt.datetime(2026, 6, 1), dt.datetime(2026, 10, 4, 23, 0)
    else:
        t0, t1 = dt.datetime(y, 1, 1), dt.datetime(y, 12, 31, 23, 0)
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

    H7L.append(hourly(series["Ny7"][y])); H1L.append(hourly(series["Ny1B"].get(y, {})))
    TWL.append(hourly(series["ThaChang_tail"].get(y, {})))
    TALL += grid
    SEGS.append((y, len(TALL) - len(grid), len(TALL)))

H7 = np.concatenate(H7L); H1 = np.concatenate(H1L); TW = np.concatenate(TWL)
grid = TALL

# ---------- ฝนรายวัน NASA POWER + หน้าต่าง 1/3/7 วัน (ตรรกะเดียวกับ v1) ----------
rain_pw = {}
for r in csv.reader(open(D16 / "power_rain_daily_3pts_2021_2026.csv", encoding="utf-8")):
    if r[0] == "date":
        continue
    rain_pw[r[0]] = (float(r[1]) + float(r[3])) / 2
from rain_window import windows_for_grid
R24, R72, R168 = (windows_for_grid(rain_pw, grid, (1, 3, 7))[n] for n in (1, 3, 7))

def at(a, i, back):
    j = i - back
    return a[j] if j >= 0 else np.nan

# ---------- สร้างตัวอย่าง (ฟีเจอร์ 12 ตัว เหมือน v1 ทุกประการ) ----------
X_all, Y_all, T_all = [], [], []
seg_ok = np.zeros(len(grid), bool)
for _, s, e in SEGS:
    seg_ok[s + 24 * 8:e] = True                 # ต้องมีประวัติย้อน 8 วันในปีเดียวกัน
for i in range(len(grid)):
    if not seg_ok[i]:
        continue
    tw = TW[i]
    X_all.append([H7[i], at(H7, i, 3), at(H7, i, 24), H7[i] - at(H7, i, 6),
                  H1[i], at(H1, i, 6), at(H1, i, 24), H1[i] - at(H1, i, 6),
                  tw if np.isfinite(tw) else 2.0,
                  R24[i], R72[i], R168[i]])
    _, s, e = next((ys, ss, ee) for ys, ss, ee in SEGS if ss <= i < ee)
    ok_y = i + 48 < e
    Y_all.append([H7[i + h] if ok_y else np.nan for h in HORIZONS])
    T_all.append(grid[i])

X_all = np.array(X_all); Y_all = np.array(Y_all)
T_all = np.array(T_all); YR_s = np.array([t.year for t in T_all])
ok = np.isfinite(Y_all).all(1) & np.isfinite(X_all).all(1)
X_all, Y_all, T_all = X_all[ok], Y_all[ok], T_all[ok]
YR_s = np.array([t.year for t in T_all])
# กันเซนเซอร์เพี้ยนระดับรุนแรง (ค่านอกพิสัยกายภาพของแม่น้ำนี้)
plaus = (Y_all > -1.0).all(1) & (Y_all < 13.0).all(1) & (X_all[:, 0] > -1.0) & (X_all[:, 0] < 13.0)
X_all, Y_all, T_all, YR_s = X_all[plaus], Y_all[plaus], T_all[plaus], YR_s[plaus]
print(f"ตัวอย่างรวม {len(T_all)} ชม. จาก {sorted(set(YR_s))}")

# ---------- leave-one-season-out + โฟลด์เหตุการณ์ 69 (เงื่อนไขเดียวกับ v1) ----------
BANKFULL = 6.86
folds = {}
for y in [2021, 2022, 2024, 2025]:
    folds[str(y)] = {"train": YR_s != y, "test": YR_s == y, "label": f"ฤดู {y}"}
folds["2026"] = {"train": T_all < dt.datetime(2026, 9, 20),
                 "test": (T_all >= dt.datetime(2026, 9, 20)) & (YR_s == 2026),
                 "label": "เหตุการณ์ 2569 (ฝึกทุกฤดูก่อน 19 ก.ย.)"}

out = {"method": "leave-one-season-out (ปีที่ทดสอบถูกถอดออกจากชุดฝึก) · โมเดลเส้นตรง 12 ตัวแปร (ฟีเจอร์ชุดเดียวกับ v1) · ฝึกจากข้อมูลทั้งปี 4 ฤดู — ต่างจาก v1 ที่ใช้ มิ.ย.–ต.ค. · ปี 2026 ใช้เงื่อนไขเดียวกับรายงานหลัก",
       "folds": {}}
for y, fl in folds.items():
    tr, te = fl["train"], fl["test"]
    row = {"n_train": int(tr.sum()), "n_test": int(te.sum())}
    preds24 = None
    for k, h in enumerate(HORIZONS):
        m = LinearRegression().fit(X_all[tr], Y_all[tr, k])
        p = m.predict(X_all[te])
        yte = Y_all[te, k]
        wet = np.array([dt.datetime(t.year, 6, 1) <= t <= dt.datetime(t.year, 10, 31) for t in T_all[te]])
        row[f"rmse{h}_all"] = round(float(np.sqrt(np.mean((p - yte) ** 2)) * 100), 1)
        row[f"rmse{h}_wet"] = round(float(np.sqrt(np.mean((p[wet] - yte[wet]) ** 2)) * 100), 1) if wet.sum() else None
        if h == 24:
            row["rmse24_persistence_wet"] = round(float(np.sqrt(np.mean((X_all[te, 0][wet] - yte[wet]) ** 2)) * 100), 1) if wet.sum() else None
            preds24 = (T_all[te], yte, p)
    out["folds"][y] = row
    print(f"{y}: n_test={row['n_test']}  RMSE+24 ทั้งปี {row['rmse24_all']} ซม. | ฤดูน้ำหลาก {row['rmse24_wet']} ซม. (persistence {row['rmse24_persistence_wet']})")

json.dump(out, open(BASE / "goal4_model_backtest_long.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------- กราฟ 5 แผง: จริง vs ทำนาย +24 ชม. ----------
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
    return f"{d.day} {THAI_M[d.month]}" + (f" {d.year + 543}" if d.month == 1 else "")
THAI_DAY_FMT = FuncFormatter(_thai_day)

fig, axes = plt.subplots(5, 1, figsize=(9.6, 13.5), dpi=130)
for ax, y in zip(axes, [2021, 2022, 2024, 2025, "2026"]):
    fl = folds[str(y)]
    tr, te = fl["train"], fl["test"]
    yte = Y_all[te, 1]
    p = LinearRegression().fit(X_all[tr], Y_all[tr, 1]).predict(X_all[te])
    T = T_all[te]
    r = out["folds"][str(y)]
    wet = np.array([dt.datetime(t.year, 6, 1) <= t <= dt.datetime(t.year, 10, 31) for t in T])
    ax.plot(T, yte, "k-", lw=1.1, label="ระดับจริง Ny.7")
    ax.plot(T, p, "-", color="#d62728", lw=0.95, label="ทำนายล่วงหน้า 24 ชม. (สูตร)")
    ax.axhline(BANKFULL, color="#ef6c00", ls="--", lw=0.8)
    if str(y) == "2026":
        ax.axvspan(dt.datetime(2026, 9, 25), dt.datetime(2026, 9, 30), color="#fdecea", zorder=0)
        ax.set_title("เหตุการณ์น้ำท่วม 69 — ฝึกด้วยทุกฤดูก่อน 19 ก.ย. (เดิมของรายงาน)", fontsize=10)
    else:
        ax.set_title(f"{fl['label']} — ถอดปีนี้ออกจากชุดฝึกทั้งหมด (leave-one-season-out)", fontsize=10)
    ax.set_ylabel("ม.รทก.")
    ax.text(0.995, 0.92, f"RMSE +24 ชม. · ทั้งปี {r['rmse24_all']} ซม. · ฤดูน้ำหลาก {r['rmse24_wet']} ซม."
            + (f" (คงที่ {r['rmse24_persistence_wet']} ซม.)" if r.get("rmse24_persistence_wet") else ""),
            transform=ax.transAxes, ha="right", va="top", fontsize=8.6, color="#37474f",
            bbox=dict(fc="white", ec="#b0bec5", alpha=0.9, boxstyle="round,pad=0.3"))
    ax.xaxis.set_major_formatter(THAI_DAY_FMT)
    if y == 2021:
        ax.legend(loc="upper left", fontsize=8.5)
    ax.grid(alpha=0.3)
axes[0].set_title("ปี 2021 — ถอดปีนี้ออกจากชุดฝึกทั้งหมด (leave-one-season-out)", fontsize=10)
axes[-1].set_xlabel("ระดับน้ำ (ม.รทก.) ที่ Ny.7 สะพานหน้าจวนผู้ว่าฯ · ปี 2023 สถานีออฟไลน์ทั้งฤดู จึงไม่มีแผง")
fig.suptitle("ทดสอบย้อนหลังของสูตรทำนาย +24 ชม. — ทุกฤดูที่มีข้อมูล (5 ปี) — AI จัดทำ ควรตรวจทานโดยผู้เชี่ยวชาญ", fontsize=11.5, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.975])
fig.savefig(ASSETS / "m_backtest_long.png")
plt.close(fig)
print("saved", ASSETS / "m_backtest_long.png")
