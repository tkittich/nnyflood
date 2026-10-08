"""วินิจฉัยฟีเจอร์ของโมเดลทำนายระดับน้ำ Ny.7 — ตอบคำถามว่า "ablation วัดสัญญาณจริงหรือวัดความไม่เสถียร"

ประเด็น: ablation 3 แขนให้ผลที่อ่านตรง ๆ ไม่ได้
    +24 ชม.  เต็ม 12 = 108.6 · ตัดฝน (9) = 121.9 · ตัด Ny.1B+ฝน (4) = 119.1
    (หมายเหตุ: สคริปต์วินิจฉัยนี้ยังใช้ชุด 12 ตัว มี dH1B_6h เพื่อเทียบกับรัน 6 ต.ค. — v1 หลักตัดออกแล้วเหลือ 11 ตัว)
  ถ้าบล็อกฝน "มีสัญญาณจริง" การตัดออกต้องแย่ลง และถ้าบล็อก Ny.1B มีสัญญาณจริงด้วย
  ต้องได้ 12 < 9 < 4 — แต่ที่วัดได้คือ 12 < 4 < 9 (ตัด Ny.1B ออก *ดีกว่า* ตัดฝนออก)
  ขณะที่สัมประสิทธิ์ฝนมีขนาด ≤0.005 (× ~250 มม. = ~1 มม.) ซึ่งอธิบายส่วนต่าง 13 ซม. ไม่ได้

สมมติฐาน: R24 ⊂ R72 ⊂ R168 เป็นหน้าต่างซ้อนกันโดยธรรมชาติ -> คอลัมน์เกือบ linearly dependent
  -> สัมประสิทธิ์ไม่เสถียร การเติม/ถอดคอลัมน์หนึ่งไปเปลี่ยนสัมประสิทธิ์ตัวอื่นทั้งหมด
  -> ablation ตีความว่า "สัญญาณ" ไม่ได้

สคริปต์นี้วัด 2 อย่าง:
  1) corr ระหว่าง R24/R72/R168 และค่า VIF ของทุกคอลัมน์
  2) ความไว: เปลี่ยน seed/สับลำดับแถวฝึก แล้วดูว่าสัมประสิทธิ์แกว่งแค่ไหน (bootstrap)
"""
import csv, datetime as dt
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression

A = Path(__file__).resolve().parent
D16 = A.parent / "data" / "16_training_data"
import sys
sys.path.insert(0, str(A))
from rain_window import windows_for_grid

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

ny7y, ny1y, twy = load_years("Ny7"), load_years("Ny1B"), load_years("ThaChang_tail")
SEGS, H7, H1, TW, TALL = [], [], [], [], []
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
    TW.append(hourly(twy.get(yr, {})))
    TALL += grid; SEGS.append((len(TALL)-len(grid), len(TALL)))
H7, H1, TW, grid = np.concatenate(H7), np.concatenate(H1), np.concatenate(TW), TALL

rain = {r[0]: (float(r[1]) + float(r[3])) / 2
        for r in csv.reader(open(D16 / "power_rain_daily_3pts_2021_2026.csv", encoding="utf-8"))
        if r[0] != "date"}
_w = windows_for_grid(rain, grid, (1, 3, 7))
R24, R72, R168 = _w[1], _w[3], _w[7]

def at(a, i, b_): return a[i-b_] if i-b_ >= 0 else np.nan

FEATS = ["H7(t)", "H7(t-3)", "H7(t-24)", "dH7_6h", "H1B(t)", "H1B(t-6)", "H1B(t-24)",
         "dH1B_6h", "TW(t)", "R24", "R72", "R168"]
X, Y, T, TWmiss = [], [], [], []
so = np.zeros(len(grid), bool)
for s, e in SEGS: so[s + 192:e] = True
for i in range(len(grid)):
    if not so[i]: continue
    oky = any(s <= i and i + 48 < e for s, e in SEGS)
    tw = TW[i]                                   # ต้อง mirror goal4_model_v1.py: default 2.0 เมื่อหาย
    X.append([H7[i], at(H7, i, 3), at(H7, i, 24), H7[i]-at(H7, i, 6), H1[i], at(H1, i, 6),
              at(H1, i, 24), H1[i]-at(H1, i, 6), tw if np.isfinite(tw) else 2.0,
              R24[i], R72[i], R168[i]])
    TWmiss.append(0 if np.isfinite(tw) else 1)
    Y.append([H7[i+h] if oky else np.nan for h in (6, 24, 48)]); T.append(grid[i])
X, Y, T, TWmiss = np.array(X), np.array(Y), np.array(T), np.array(TWmiss)
ok = np.isfinite(Y).all(1) & np.isfinite(X).all(1)
X, Y, T, TWmiss = X[ok], Y[ok], np.array(T)[ok], TWmiss[ok]
tr = np.array([t < dt.datetime(2026, 9, 20) for t in T])
print(f"ท้ายน้ำหาย (ใช้ default 2.0): {TWmiss[tr].mean()*100:.0f}% (ฝึก) / {TWmiss[~tr].mean()*100:.0f}% (ทดสอบ)")

print("\n=== 1) corr ระหว่างฟีเจอร์ฝน (ชุดฝึก) ===")
print("        " + "".join(f"{n:>9}" for n in ["R24", "R72", "R168"]))
R = np.corrcoef(X[tr][:, [9, 10, 11]].T)
for i, a in enumerate(["R24", "R72", "R168"]):
    print(f"   {a:<6}" + "".join(f"{R[i][j]:>9.4f}" for j in range(3)))

print("\n=== corr กับ H7(t) (ชุดฝึก) ===")
with np.errstate(invalid="ignore", divide="ignore"):
    c0 = np.corrcoef(X[tr].T)[0]
for f, c in sorted(zip(FEATS, c0), key=lambda z: -abs(z[1]) if np.isfinite(z[1]) else 0):
    print(f"   {f:<10}{c:>+9.4f}" + ("   <-- ค่าคงที่ (corr ไม่นิยาม)" if not np.isfinite(c) else ""))

print("\n=== 2) ภาวะร่วมเส้นตรง (VIF) ===")
V = X[tr]
for j, f in enumerate(FEATS):
    others = np.delete(V, j, axis=1)
    r2 = LinearRegression().fit(others, V[:, j]).score(others, V[:, j])
    vif = np.inf if r2 >= 1 - 1e-12 else 1.0 / (1.0 - r2)
    print(f"   {f:<10}VIF = {vif:>9.1f}" + ("  <-- สูงมาก" if vif > 10 else ""))

print("\n=== 3) อันดับ (rank) ของเมทริกซ์ออกแบบ ===")
Vs = (V - V.mean(0)) / np.where(V.std(0) == 0, 1, V.std(0))
sv = np.linalg.svd(Vs, compute_uv=False)
print(f"   จำนวนคอลัมน์ = {V.shape[1]} · rank (tol 1e-10) = {np.linalg.matrix_rank(Vs, tol=1e-10)}")
print(f"   singular values: " + " ".join(f"{s:.3g}" for s in sv))
print(f"   -> คอลัมน์ที่ซ้ำซ้อน: {V.shape[1] - np.linalg.matrix_rank(Vs, tol=1e-10)} ตัว")
print("\n   ตรวจเอกลักษณ์: dH1B_6h = H1B(t) - H1B(t-6) ?")
d = V[:, 7] - (V[:, 4] - V[:, 5])
print(f"   max|dH1B_6h - (H1B(t) - H1B(t-6))| = {np.abs(d).max():.3e}")
print("   ตรวจเอกลักษณ์: dH7_6h = H7(t) - H7(t-6) ? (H7(t-6) ไม่ได้อยู่ในเซตฟีเจอร์ -> ไม่ซ้ำ)")
print(f"   corr(dH7_6h, H7(t)) = {np.corrcoef(V[:, 3], V[:, 0])[0,1]:+.4f}")

print("\n=== 5) การทดสอบชี้ขาด: ส่วนต่างจาก ablation มาจาก 'สัญญาณ' หรือ 'การกระจายสัมประสิทธิ์ใหม่' ===")
# ถ้าบล็อกฝนมีสัญญาณจริง: การ "ศูนย์สัมประสิทธิ์ฝน" (คงสัมประสิทธิ์ตัวอื่นไว้) ต้องทำให้ RMSE แย่ลง ~13 ซม.
# ถ้า RMSE แทบไม่ขยับ แต่การ "refit โดยไม่มีฝน" แย่ลง 13 ซม. -> ส่วนต่างมาจากการกระจายใหม่ = artifact
ev = np.array([dt.datetime(2026, 9, 25) <= t <= dt.datetime(2026, 9, 30) for t in T[~tr]])
te = ~tr
for k, h in enumerate((6, 24, 48)):
    m = LinearRegression().fit(X[tr], Y[tr, k])
    p_full = m.predict(X[te])
    # ศูนย์เฉพาะบล็อกฝน (คอลัมน์ 9,10,11) โดยคงสัมประสิทธิ์อื่นทั้งหมด
    Xz = X[te].copy(); Xz[:, 9:12] = 0.0
    p_rainzero = Xz @ m.coef_ + m.intercept_
    # refit โดยตัดคอลัมน์ฝนออกจริง ๆ
    p_refit = LinearRegression().fit(X[tr][:, :9], Y[tr, k]).predict(X[te][:, :9])
    r_full = np.sqrt(np.mean((p_full[ev] - Y[te, k][ev]) ** 2)) * 100
    r_zero = np.sqrt(np.mean((p_rainzero[ev] - Y[te, k][ev]) ** 2)) * 100
    r_refit = np.sqrt(np.mean((p_refit[ev] - Y[te, k][ev]) ** 2)) * 100
    print(f"   +{h:>2} ชม.  เต็ม {r_full:>6.1f} | ศูนย์ฝน(คง coef อื่น) {r_zero:>6.1f} "
          f"| refit ไม่มีฝน {r_refit:>6.1f}   -> ส่วนต่างจริง {r_zero - r_full:+.1f} · ส่วนต่างจากการ refit {r_refit - r_full:+.1f}")
print("\n   อ่านผล: ถ้า 'ส่วนต่างจริง' ~0 แต่ 'ส่วนต่างจากการ refit' ใหญ่ = ablation ตีความว่า signal ไม่ได้")

print("\n=== 6) ความไม่เสถียรของสัมประสิทธิ์ (bootstrap 200 รอบ, +24 ชม.) ===")
rng = np.random.default_rng(0)
idx_tr = np.where(tr)[0]
coefs = np.array([LinearRegression().fit(X[b], Y[b, 1]).coef_
                  for b in (rng.choice(idx_tr, size=len(idx_tr), replace=True) for _ in range(200))])
point = LinearRegression().fit(X[tr], Y[tr, 1]).coef_
print(f"   {'ฟีเจอร์':<10}{'สัมประสิทธิ์':>14}{'SD (bootstrap)':>16}{'SD/|c|':>10}")
for f, c, sd in zip(FEATS, point, coefs.std(0)):
    ratio = abs(sd / c) if abs(c) > 1e-9 else np.inf
    print(f"   {f:<10}{c:>14.4f}{sd:>16.4f}{ratio:>10.2f}")

