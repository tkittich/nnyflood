# ทดลอง: เพิ่ม "ตัวแปรความอิ่มน้ำของลุ่ม" (API index + ฝนสะสม 14/30 วัน) ช่วยโมเดลทำนายหรือไม่
# คำถาม: "ฝนเท่าเดิมแต่ความอิ่มน้ำไม่เท่ากัน ทำให้น้ำสูงไม่เท่ากัน"
# วิธี: pipeline เดียวกับ goal4_model_v1 (+24 ชม. เป็นหลัก) เทียบ RMSE ก่อน/หลังเพิ่มตัวแปร
import csv, datetime as dt
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression
from rain_window import windows_for_grid

A = Path(__file__).resolve().parent
D16 = A.parent / "data" / "16_training_data"

def load_years(name):
    out = {}
    for fn in sorted(D16.glob(f"khundan_15min_{name}_Jun-Oct*.csv")):
        yr = int(fn.name[-8:-4]); d = {}
        for r in csv.reader(open(fn, encoding="utf-8")):
            if r[0] in ("datetime", "") or not r[0]:
                continue
            d[dt.datetime.fromisoformat(r[0])] = float(r[1]) if r[1] not in ("", "-") else np.nan
        out[yr] = d
    return out

def despike(d, thr=0.5):
    ts = sorted(d); lv = np.array([d[t] for t in ts]); bad = np.zeros(len(ts), bool)
    for i in range(1, len(ts) - 3):
        if abs(lv[i] - lv[i-1]) > thr and abs(lv[i] - lv[i+3]) < thr * 0.6:
            bad[i:i+3] = True
    lv = lv.copy(); lv[bad] = np.nan
    g = np.where(np.isfinite(lv))[0]
    return dict(zip(ts, np.interp(np.arange(len(ts)), g, lv[g]))) if len(g) else {}

ny7y, ny1y = load_years("Ny7"), load_years("Ny1B")
SEGS, H7, H1, TALL = [], [], [], []
for yr in sorted(ny7y):
    t0, t1 = dt.datetime(yr, 6, 1), dt.datetime(yr, 10, 4, 23, 0)
    grid = [t0 + dt.timedelta(hours=h) for h in range(int((t1-t0).total_seconds()//3600)+1)]
    def hourly(d):
        out = np.full(len(grid), np.nan); idx = {t: i for i, t in enumerate(grid)}; b = {}
        for t, lv in d.items():
            h = t.replace(minute=0)
            if h in idx and np.isfinite(lv): b.setdefault(h, []).append(lv)
        for h, v in b.items(): out[idx[h]] = np.mean(v)
        g = np.where(np.isfinite(out))[0]
        return np.interp(np.arange(len(grid)), g, out[g]) if len(g) else out
    H7.append(hourly(despike(ny7y[yr]))); H1.append(hourly(despike(ny1y.get(yr, {}))))
    TALL += grid; SEGS.append((len(TALL)-len(grid), len(TALL)))
H7, H1, grid = np.concatenate(H7), np.concatenate(H1), TALL

rain = {r[0]: (float(r[1]) + float(r[3])) / 2 for r in csv.reader(open(D16 / "power_rain_daily_3pts_2021_2026.csv")) if r[0] != "date"}
RD = np.array([rain.get(t.strftime("%Y%m%d"), 0.0) for t in grid])

# หน้าต่างฝนสะสม 1/3/7/14/30 วัน — ห้ามใช้ roll() แบบ cumsum เลื่อน n ช่อง
# (ไม่ใช่หน้าต่าง n วัน) บนกริดรายชั่วโมงที่ฝนรายวันถูกทำซ้ำ 24 ช่อง = ข้อมูลอนาคตรั่ว
# RD ยังใช้ต่อสำหรับ API index ด้านล่าง (อ้าง RD[i-1] เฉพาะตอนเที่ยงคืน = ฝนเมื่อวาน ไม่รั่ว)
_w = windows_for_grid(rain, grid, (1, 3, 7, 14, 30))
R1, R3, R7, R14, R30 = _w[1], _w[3], _w[7], _w[14], _w[30]
# API index (Antecedent Precipitation Index): API(t) = 0.9*API(t-1) + rain(t-1) — ความจำฝนหย่อน decay
API = np.zeros(len(grid))
for i in range(1, len(grid)):
    if grid[i].hour == 0:
        API[i] = 0.9 * API[i-1] + RD[i-1]
    else:
        API[i] = API[i-1]

def at(a, i, b_): return a[i-b_] if i-b_ >= 0 else np.nan

FEATS_BASE = ["H7(t)", "H7(t-3)", "H7(t-24)", "dH7_6h", "H1B(t)", "H1B(t-6)", "H1B(t-24)", "dH1B_6h", "TW", "R1", "R3", "R7"]
FEATS_MOIST = FEATS_BASE + ["R14", "R30", "API"]
Xb, Xm, Y, T = [], [], [], []
so = np.zeros(len(grid), bool)
for s, e in SEGS: so[s + 192:e] = True
for i in range(len(grid)):
    if not so[i]: continue
    oky = any(s <= i and i + 48 < e for s, e in SEGS)
    Xb.append([H7[i], at(H7, i, 3), at(H7, i, 24), H7[i]-at(H7, i, 6), H1[i], at(H1, i, 6), at(H1, i, 24), H1[i]-at(H1, i, 6), 2.0, R1[i], R3[i], R7[i]])
    Xm.append(Xb[-1] + [R14[i], R30[i], API[i]])
    Y.append([H7[i+h] if oky else np.nan for h in (6, 24, 48)]); T.append(grid[i])
Xb, Xm, Y, T = np.array(Xb), np.array(Xm), np.array(Y), np.array(T)
ok = np.isfinite(Y).all(1) & np.isfinite(Xb).all(1) & np.isfinite(Xm).all(1)
Xb, Xm, Y, T = Xb[ok], Xm[ok], Y[ok], T[ok]
tr = np.array([t < dt.datetime(2026, 9, 20) for t in T]); te = ~tr
ev = np.array([dt.datetime(2026, 9, 25) <= t <= dt.datetime(2026, 9, 30) for t in T[te]])

print(f"ฝึก {tr.sum()} / ทดสอบ {te.sum()} ชม.\n{'ตัวแปร':<26}{'RMSE+6':>8}{'RMSE+24':>9}{'RMSE+48':>9}{'  RMSE+24 เหตุการณ์':>20}")
for nm, X in (("ฐาน 12 ตัวแปร", Xb), ("เพิ่ม R14+R30+API (15)", Xm)):
    vals = []
    for k in range(3):
        lin = LinearRegression().fit(X[tr], Y[tr, k])
        p = lin.predict(X[te])
        vals.append(np.sqrt(np.mean((p - Y[te, k]) ** 2)) * 100)
    print(f"{nm:<26}{vals[0]:>8.1f}{vals[1]:>9.1f}{vals[2]:>9.1f}")
    if nm.startswith("เพิ่ม"):
        lin24 = LinearRegression().fit(X[tr], Y[tr, 1])
        coef = dict(zip(["R14", "R30", "API"], lin24.coef_[-3:]))
        print("   สัมประสิทธิ์ความอิ่มน้ำ (+24 ชม.):", {k: round(v, 5) for k, v in coef.items()})
# เหตุการณ์
for nm, X in (("ฐาน", Xb), ("เพิ่มความอิ่มน้ำ", Xm)):
    lin = LinearRegression().fit(X[tr], Y[tr, 1])
    p = lin.predict(X[te])
    print(f"  {nm}: RMSE เหตุการณ์ +24 ชม. = {np.sqrt(np.mean((p[ev]-Y[te,1][ev])**2))*100:.1f} ซม.")
