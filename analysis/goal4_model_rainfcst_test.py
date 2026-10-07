# ทดลอง: ถ้าโมเดลทำนายระดับ Ny.7 ใช้ "ฝนพยากรณ์" เป็นอินพุตแทน "ฝนสังเกตจริง" ผลจะเสียหายไหม แค่ไหน
# (ทดสอบใช้ผลจากโมเดลพยากรณ์ฝนหลายโมเดล — GFS/ECMWF/ICON/GEM/JMA จาก Historical Forecast API)
# วิธี: ฝึกสูตรเส้นตรงด้วยฝนสังเกต (POWER) เหมือน goal4_model_v1 ทุกประการ
#        แล้วทดสอบช่วง 20 ก.ย.–4 ต.ค. 69 หลายรอบ — เปลี่ยนเฉพาะฟีเจอร์ฝนในชุดทดสอบเป็นฝนพยากรณ์รายโมเดล
# ผู้จัดทำ: AI — ผลการทดลองเบื้องต้น ควรตรวจทานโดยผู้เชี่ยวชาญ
import csv, json, datetime as dt
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression
from rain_window import windows_for_grid
from common import BANKFULL_MSL

A = Path(__file__).resolve().parent
D16 = A.parent / "data" / "16_training_data"

def load_years(name):
    out = {}
    for fn in sorted(D16.glob(f"khundan_15min_{name}_Jun-Oct*.csv")):
        yr = int(fn.name[-8:-4])
        d = {}
        for r in csv.reader(open(fn, encoding="utf-8")):
            if r[0] in ("datetime", "") or not r[0]:
                continue
            d[dt.datetime.fromisoformat(r[0])] = float(r[1]) if r[1] not in ("", "-") else np.nan
        out[yr] = d
    return out

ny7y, ny1y = load_years("Ny7"), load_years("Ny1B")

def despike(d, thr=0.5):
    ts = sorted(d); lv = np.array([d[t] for t in ts])
    bad = np.zeros(len(ts), bool)
    for i in range(1, len(ts) - 3):
        if abs(lv[i] - lv[i-1]) > thr and abs(lv[i] - lv[i+3]) < thr * 0.6:
            bad[i:i+3] = True
    lv = lv.copy()
    lv[bad] = np.nan
    good = np.where(np.isfinite(lv))[0]
    if not len(good):
        return {}
    s = np.interp(np.arange(len(ts)), good, lv[good])
    return dict(zip(ts, s))

H7y = {yr: despike(d) for yr, d in ny7y.items()}
H1y = {yr: despike(ny1y.get(yr, {})) for yr in ny7y}

SEGS, H7, H1, TALL = [], [], [], []
for yr in sorted(H7y):
    t0, t1 = dt.datetime(yr, 6, 1), dt.datetime(yr, 10, 4, 23, 0)
    grid = [t0 + dt.timedelta(hours=h) for h in range(int((t1 - t0).total_seconds() // 3600) + 1)]

    def hourly(d):
        out = np.full(len(grid), np.nan)
        idx = {t: i for i, t in enumerate(grid)}
        bucket = {}
        for t, lv in d.items():
            h = t.replace(minute=0)
            if h in idx and np.isfinite(lv):
                bucket.setdefault(h, []).append(lv)
        for h, vals in bucket.items():
            out[idx[h]] = np.mean(vals)
        good = np.where(np.isfinite(out))[0]
        if len(good):
            out = np.interp(np.arange(len(grid)), good, out[good])
        return out

    H7.append(hourly(H7y[yr])); H1.append(hourly(H1y.get(yr, {})))
    TALL += grid
    SEGS.append((len(TALL) - len(grid), len(TALL)))
H7 = np.concatenate(H7); H1 = np.concatenate(H1); grid = TALL

rain_pw = {}
for r in csv.reader(open(D16 / "power_rain_daily_3pts_2021_2026.csv", encoding="utf-8")):
    if r[0] != "date":
        rain_pw[r[0]] = (float(r[1]) + float(r[3])) / 2

fc = json.load(open(D16 / "model_rain_histforecast_sep2026.json", encoding="utf-8"))
def fc_rain(model):
    """ฝนพยากรณ์รายวัน (เฉลี่ย west+town) ของโมเดลหนึ่ง — คืน dict YYYYMMDD -> mm"""
    a, b = fc.get(f"west_foothill|{model}", {}), fc.get(f"town_east|{model}", {})
    return {k.replace("-", ""): ((a.get(k) or 0) + (b.get(k) or 0)) / 2 for k in a}

MODELS = ["gfs_seamless", "ecmwf_ifs025", "icon_seamless", "gem_seamless", "jma_seamless"]
rain_sources = {"ฝนสังเกต (POWER)": rain_pw}
for m in MODELS:
    rain_sources[f"ฝนพยากรณ์ {m.split('_')[0].upper()}"] = fc_rain(m)
ens = {}
for k in list(fc_rain("gfs_seamless")):
    vals = [fc_rain(m).get(k) for m in MODELS]
    ens[k] = sum(v for v in vals if v is not None) / len(MODELS)
rain_sources["ฝนพยากรณ์ ensemble 5 โมเดล"] = ens

def at(a, i, back):
    j = i - back
    return a[j] if j >= 0 else np.nan

def build(daily):
    # หน้าต่างฝน 1/3/7 วัน — ห้ามใช้ roll_from() แบบ cumsum เลื่อน n ช่อง
    # (ไม่ใช่หน้าต่าง n วัน) บนกริดรายชั่วโมงที่ฝนรายวันถูกทำซ้ำ 24 ช่อง = ข้อมูลอนาคตรั่ว
    w = windows_for_grid(daily, grid, (1, 3, 7))
    R24, R72, R168 = w[1], w[3], w[7]
    X, Y, T = [], [], []
    seg_ok = np.zeros(len(grid), bool)
    for s, e in SEGS:
        seg_ok[s + 24 * 8:e] = True
    for i in range(len(grid)):
        if not seg_ok[i]:
            continue
        ok_y = any(s <= i and i + 48 < e for s, e in SEGS)
        X.append([H7[i], at(H7, i, 3), at(H7, i, 24), H7[i] - at(H7, i, 6),
                  H1[i], at(H1, i, 6), at(H1, i, 24), H1[i] - at(H1, i, 6),
                  2.0, R24[i], R72[i], R168[i]])
        Y.append([H7[i + h] if ok_y else np.nan for h in (6, 24, 48)])
        T.append(grid[i])
    X, Y, T = np.array(X), np.array(Y), np.array(T)
    ok = np.isfinite(Y).all(1) & np.isfinite(X).all(1)
    return X[ok], Y[ok], T[ok]

Xobs, Y, T = build(rain_sources["ฝนสังเกต (POWER)"])      # ฐานสำหรับฝึก (ฝนสังเกตเสมอ)
tr = np.array([t < dt.datetime(2026, 9, 20) for t in T])
te = ~tr
BANK_H = BANKFULL_MSL
ev = np.array([dt.datetime(2026, 9, 25) <= t <= dt.datetime(2026, 9, 30) for t in T[te]])
p_pers = Xobs[te, 0]
print(f"ฝึก {tr.sum()} ชม. | ทดสอบ {te.sum()} ชม. | ปีที่ใช้: {sorted(H7y)}")
print(f"\nทำนาย +24 ชม. ช่วงเหตุการณ์ 25-30 ก.ย. เมื่อเปลี่ยนแหล่งฝนของชุดทดสอบ:")
print(f"{'แหล่งฝนอินพุต':<28}{'RMSE ชม.(ซม.)':>14}{'พีค(ม.รทก.)':>12}{'ชม.>ล้นตลิ่ง':>13}")
rows_out = []
for k in range(3):
    h = (6, 24, 48)[k]
    lin = LinearRegression().fit(Xobs[tr], Y[tr, k])
    print(f"--- ทำนายล่วงหน้า +{h} ชม. ---")
    print(f"{'คงที่ (persistence)':<28}{np.sqrt(np.mean((p_pers[ev]-Y[te,k][ev])**2))*100:>14.1f}{p_pers[ev].max():>12.2f}{(p_pers[ev]>BANK_H).sum():>13d}")
    for name, daily in rain_sources.items():
        Xsrc, _, _ = build(daily)
        # Xsrc ต้องตรง timeline เดียวกับ Xobs (จำนวนแถวเท่ากัน)
        p = lin.predict(Xsrc[te])
        rmse = np.sqrt(np.mean((p[ev] - Y[te, k][ev]) ** 2)) * 100
        print(f"{name:<28}{rmse:>14.1f}{p[ev].max():>12.2f}{(p[ev]>BANK_H).sum():>13d}")
        if h == 24:
            rows_out.append((name, round(rmse, 1), round(p[ev].max(), 2), int((p[ev] > BANK_H).sum())))
json.dump(rows_out, open(A / "goal4_rainfcst_input_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nบันทึก: goal4_rainfcst_input_results.json (+24 ชม.)")
