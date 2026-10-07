"""
QA5: 18-day rain (12-29 Sep 2026) -> river level/drainage analysis
     + perfect-management counterfactual at Ny.7 (town gauge).

Inputs (analysis/):
  nn_rain_daily_2026.csv, waterlevel_hourly_sep2026_stations.csv,
  dam_khun_dan_daily_2013_2026.csv
Rating (khundan_tele_findings K5): Q = 242*(h_msl-4.55)^0.66 ; Ny.7 gauge = MSL+1.59
"""
import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from common import GAUGE_OFFSET, RATING_A, RATING_B, RATING_C

# อิง __file__ ไม่ใช่ cwd (ไม่ hardcode พาธ จะได้พอร์ตเครื่องอื่นได้)
A = Path(__file__).resolve().parent


def read_csv(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ---------- load rain ----------
rain_rows = read_csv(A / "nn_rain_daily_2026.csv")
stations = [c for c in rain_rows[0].keys() if c != "date"]
rain = {}  # date -> {station: mm}
for r in rain_rows:
    rain[r["date"]] = {
        s: float(r[s]) if r[s] not in ("", None) else np.nan for s in stations
    }

D0, D1 = "2026-09-12", "2026-09-29"
dates_ev = [r["date"] for r in rain_rows if D0 <= r["date"] <= D1]

cum = {s: np.nansum([rain[d][s] for d in dates_ev]) for s in stations}
rank = sorted(cum.items(), key=lambda x: -x[1])
print("== 18-day rain (12-29 Sep) by station ==")
for s, v in rank:
    print(f"  {s:28s} {v:7.1f} mm")

foothill = [s for s, v in rank if v >= 900]
plain = [s for s, v in rank if v < 900]
print("foothill band:", [s.split('_')[1] for s in foothill])
print("plain band   :", [s.split('_')[1] for s in plain])
plain = [s for s in plain if s.split('_')[1] != 'นครนายก'] or plain  # keep town separate
town = "48417_นครนายก"

daily_foothill = np.array([np.nanmean([rain[d][s] for s in foothill]) for d in dates_ev])
daily_plain = np.array([np.nanmean([rain[d][s] for s in plain]) for d in dates_ev])
daily_town = np.array([rain[d][town] for d in dates_ev])
print("\ndate        foothill  plain  town")
for i, d in enumerate(dates_ev):
    print(f"{d}  {daily_foothill[i]:7.1f} {daily_plain[i]:6.1f} {daily_town[i]:5.1f}")
print(f"totals: foothill {daily_foothill.sum():.0f}  plain {daily_plain.sum():.0f}  town {daily_town.sum():.0f}")

# ---------- load hourly levels ----------
lv = read_csv(A / "waterlevel_hourly_sep2026_stations.csv")
def parse_lv(col):
    out = []
    for r in lv:
        if r.get(col) not in ("", None):
            out.append((datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M"), float(r[col])))
    return out

ny7 = parse_lv("Ny7_เมือง")
ny1b = parse_lv("Ny1B_เขานางบวช")

def q_ny7(gauge):
    h = gauge - GAUGE_OFFSET
    if h <= RATING_B:
        return 0.0
    return RATING_A * (h - RATING_B) ** RATING_C

# ---------- baselevel rise before the event ----------
def daily_min(series, d0="2026-09-01", d1="2026-09-25"):
    out = {}
    for t, v in series:
        ds = t.strftime("%Y-%m-%d")
        if d0 <= ds <= d1:
            out[ds] = min(out.get(ds, 1e9), v)
    return out

dm7 = daily_min(ny7)
print("\n== Ny.7 daily-min gauge (system filling) ==")
for d in ["2026-09-05", "2026-09-10", "2026-09-15", "2026-09-18", "2026-09-21", "2026-09-23", "2026-09-24", "2026-09-25"]:
    if d in dm7:
        print(f"  {d}: {dm7[d]:.2f} m (Q~{q_ny7(dm7[d]):.0f} m3/s)")

# ---------- rain->level response early vs late ----------
rows_d = [r["date"] for r in rain_rows if "2026-09-01" <= r["date"] <= "2026-10-04"]
ny7_mean = {}
for ds in set(t.strftime("%Y-%m-%d") for t, _ in ny7):
    vals = [v for t, v in ny7 if t.strftime("%Y-%m-%d") == ds]
    ny7_mean[ds] = float(np.mean(vals))

def rain_idx(d):
    if d not in rain:
        return np.nan
    return np.nanmean([rain[d][s] for s in foothill]) * 0.7 + np.nanmean([rain[d][s] for s in plain]) * 0.3

pairs = []
for i, d in enumerate(rows_d[:-1]):
    d1 = rows_d[i + 1]
    if d in ny7_mean and d1 in ny7_mean:
        pairs.append((d, rain_idx(d), ny7_mean[d1] - ny7_mean[d]))
early = [(r, dl) for d, r, dl in pairs if "2026-09-12" <= d <= "2026-09-18" and not np.isnan(r)]
late = [(r, dl) for d, r, dl in pairs if "2026-09-19" <= d <= "2026-09-25" and not np.isnan(r)]
def slope(pairs_):
    x = np.array([p[0] for p in pairs_]); y = np.array([p[1] for p in pairs_])
    return np.polyfit(x, y, 1)[0] if len(x) > 3 else np.nan
print("\n== dLevel(Ny.7 next-day) per mm rain ==")
print(f"  early 12-18 Sep: {slope(early)*100:.2f} cm/mm (n={len(early)})")
print(f"  late  19-25 Sep: {slope(late)*100:.2f} cm/mm (n={len(late)})")

# ---------- overbank threshold & onset ----------
onset = [v for t, v in ny7 if t == datetime(2026, 9, 26, 22, 0)]
onset2 = [v for t, v in ny7 if t == datetime(2026, 9, 26, 23, 0)]
print("\n== onset 26 Sep: Ny.7 gauge 22:00 =", onset, "23:00 =", onset2)
if onset and onset2:
    L_flood = (onset[0] + onset2[0]) / 2
else:
    L_flood = 7.4
    print("!! WARNING: ไม่พบแถว onset 26 ก.ย. 22:00/23:00 — ใช้ค่าสมมุติ 7.4 ม. (ตรวจข้อมูลก่อนเชื่อผล)")
print(f"   flood-onset gauge ~{L_flood:.2f} m -> Q~{q_ny7(L_flood):.0f} m3/s (bankfull-ish)")

peak7 = max(ny7, key=lambda x: x[1])
print(f"   Ny.7 peak gauge {peak7[1]:.2f} at {peak7[0]} -> Q~{q_ny7(peak7[1]):.0f} m3/s")

# ---------- recession / drainage after peak ----------
def night_recess(d_str):
    """mean hourly fall 01:00-05:00 next night"""
    t0 = datetime.strptime(d_str, "%Y-%m-%d") + timedelta(hours=1)
    seg = [(t, v) for t, v in ny7 if t0 <= t <= t0 + timedelta(hours=4)]
    if len(seg) < 3:
        return np.nan, np.nan
    fall = (seg[0][1] - seg[-1][1]) / 4.0
    return fall, np.mean([v for _, v in seg])

print("\n== night recession at Ny.7 (cm/h @ mean gauge) ==")
for d in ["2026-09-13", "2026-09-16", "2026-09-20", "2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02"]:
    f, m = night_recess(d)
    if not np.isnan(f):
        print(f"  night {d}: {f*100:5.1f} cm/h @ {m:.2f} m (Q~{q_ny7(m):.0f})")

# ---------- dam releases ----------
dam = {r["date"]: r for r in read_csv(A / "dam_khun_dan_daily_2013_2026.csv")}
print("\n== dam daily released/inflow/storage 24 Sep-2 Oct ==")
for d in ["2026-09-24", "2026-09-25", "2026-09-26", "2026-09-27", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02"]:
    r = dam.get(d)
    if r:
        print(f"  {d}: rel {float(r['released_mcm_d']):6.2f} MCM  in {float(r['inflow_mcm_d']):6.2f}  S {float(r['storage_mcm']):7.2f}")

# ---------- volume balance 25-28 Sep at Ny.7 ----------
def vol_past(t0, t1):
    seg = [(t, v) for t, v in ny7 if t0 <= t <= t1]
    qs = [q_ny7(v) for _, v in seg]
    return np.trapezoid(qs, dx=3600.0) / 1e6, max(qs)

V_out, Qmax = vol_past(datetime(2026, 9, 25), datetime(2026, 9, 28))
rel_vol = sum(float(dam[d]["released_mcm_d"]) for d in ["2026-09-25", "2026-09-26", "2026-09-27"] if d in dam)
rain_vol_foo = daily_foothill[:17].sum() / 1000 * 1188 * (3 / 18)  # crude: 25-27 share
print(f"\n== volumes 25-28 Sep: past Ny.7 {V_out:.1f} MCM (Qmax~{Qmax:.0f}); dam release {rel_vol:.1f} MCM")

# ---------- counterfactual daily model ----------
# dL = a*rain_idx(prev) + b*rel(prev) - c*(L-6.0)
X, Y, Ds = [], [], []
for i in range(1, len(rows_d)):
    d, dp = rows_d[i], rows_d[i - 1]
    if d in ny7_mean and dp in rain and dp in dam and rain[dp][town] == rain[dp][town]:
        rel = float(dam[dp]["released_mcm_d"]) if dam[dp]["released_mcm_d"] else np.nan
        if rel == rel:
            X.append([rain_idx(dp), rel, ny7_mean[dp] - 6.0])
            Y.append(ny7_mean[d] - ny7_mean[dp])
            Ds.append(d)
X, Y = np.array(X), np.array(Y)
coef, res, *_ = np.linalg.lstsq(X, Y, rcond=None)
pred = X @ coef
r2 = 1 - ((Y - pred) ** 2).sum() / ((Y - Y.mean()) ** 2).sum()
a, b, c = coef
print(f"\n== daily model dL = {a*100:.2f}cm/mm_rain + {b*100:.2f}cm/(MCM/d rel) - {c:.3f}*(L-6.0) | R2={r2:.2f} n={len(Y)}")

# scenario simulation 24 Sep - 4 Oct
def simulate(label, rel_override):
    L = ny7_mean["2026-09-23"]
    S = float(dam["2026-09-23"]["storage_mcm"])
    traj = []
    for i, d in enumerate(rows_d):
        if d < "2026-09-24":
            continue
        dp = rows_d[rows_d.index(d) - 1]
        rel = rel_override.get(d, float(dam[d]["released_mcm_d"]))
        infl = float(dam[d]["inflow_mcm_d"]) if dam[d]["inflow_mcm_d"] else 0
        S = S + infl - rel
        ri = rain_idx(dp) if dp in rain else 0
        if np.isnan(ri):
            ri = 0
        L = L + a * ri + b * rel - c * (L - 6.0)
        traj.append((d, L, S, rel))
    pk = max(traj, key=lambda x: x[1])
    above = [t for t in traj if t[1] >= L_flood]
    print(f"\n[{label}] peak day-mean {pk[1]:.2f} m on {pk[0]} | max S {max(t[2] for t in traj):.1f} | days>=onset {len(above)}")
    return traj

traj_actual = simulate("actual", {})
# S1: drawdown to URC by 24 Sep (extra 2.5/d until), storm absorb, cap after
urc_24 = float(dam["2026-09-24"]["upper_rule_curve_mcm"])
s1 = {}
S = float(dam["2026-09-23"]["storage_mcm"])
for d in [x for x in rows_d if "2026-09-24" <= x <= "2026-10-04"]:
    infl = float(dam[d]["inflow_mcm_d"]) if dam[d]["inflow_mcm_d"] else 0
    if d <= "2026-09-25":
        rel = float(dam[d]["released_mcm_d"]) + max(0, min(2.5, S - urc_24))
    elif d <= "2026-09-29":
        rel = max(0.5, min(12.0, infl - 2.0))  # absorb, keep small release
    else:
        rel = min(15.0, max(1.0, S - 210) / 2 + infl / 2)
    s1[d] = rel
    S = S + infl - rel
simulate("S1 perfect (URC+absorb)", s1)
simulate("S2 zero release 25-29", {d: 0.5 for d in s1 if "2026-09-25" <= d <= "2026-09-29"})
