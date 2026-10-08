# สร้าง x1 (rating curve) และ x2 (ไฮโดรกราฟ 3 สถานี) ฉบับแกนภาษาไทย
import json, csv, datetime as dt
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma", "Loma", "Garuda", "Norasi", "DejaVu Sans"]
A = Path(__file__).resolve().parent
OUT = A / "assets"
THAI_M = {1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
          7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."}
def _thai_day(x, pos):
    d = mdates.num2date(x)
    return f"{d.day} {THAI_M[d.month]}"
THAI_DAY_FMT = FuncFormatter(_thai_day)

ev = json.load(open(A.parent / "analysis" / "khundan_tele_event_data.json", encoding="utf-8"))

# ---------- x1: rating curve Ny.7 (คู่ระดับ-อัตราไหลจริงช่วงเหตุการณ์) ----------
pts = []
for r in ev["Ny7_peak"] + ev["Ny7_rec"]:
    lv, q = r.get("level_msl_m"), r.get("q_cms")
    if lv not in ("", None) and q not in ("", None):
        pts.append((float(lv), float(q)))
pts = sorted(set(pts))
h = np.array([p[0] for p in pts]); q = np.array([p[1] for p in pts])
hfit = np.linspace(4.0, 7.8, 200)
qfit = 242.0 * np.maximum(hfit - 4.55, 0) ** 0.66
fig, ax = plt.subplots(figsize=(7.4, 4.8), dpi=130)
ax.scatter(h, q, s=7, alpha=0.45, color="#1565c0", label="คู่วัดจริง (ระดับ–อัตราไหล รายชั่วโมง 25 ก.ย.–2 ต.ค. 69)")
ax.plot(hfit, qfit, color="#c62828", lw=2, label="สมการประมาณ: Q ≈ 242×(h−4.55)^0.66")
ax.axvline(6.86, color="#ef6c00", ls="--", lw=1)
ax.set_ylim(top=max(q) * 1.16)
ax.text(6.9, max(q) * 1.06, "ระดับล้นตลิ่งเมือง 6.86 ม.รทก. (≈ เกจ 8.45)", fontsize=8, color="#ef6c00", va="top")
ax.annotate("น้ำสูงสุดจริง 7.68 ม.รทก.\n(สถานีอ่าน Q สูงกว่าสมการ ~18%)", xy=(7.68, 690), xytext=(-118, -6),
            textcoords="offset points", fontsize=8, color="#37474f",
            arrowprops=dict(arrowstyle="->", color="#37474f", lw=0.7))
ax.set_xlabel("ระดับน้ำ ณ Ny.7 (ม.รทก.)")
ax.set_ylabel("อัตราไหล Q (ลบ.ม./วินาที)")
ax.set_title("ความสัมพันธ์ระดับ–อัตราไหลของสถานี Ny.7 (สะพานหน้าจวนผู้ว้าฯ)")
ax.legend(fontsize=8.5, loc="upper left"); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(OUT / "x1_rating.png"); plt.close(fig)
print("x1 saved")

# ---------- x2: ไฮโดรกราฟ 3 สถานี + การปล่อย ----------
def series(key):
    t, lv, qq = [], [], []
    for r in ev[key]:
        if r.get("level_msl_m") in ("", None):
            continue
        t.append(dt.datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M"))
        lv.append(float(r["level_msl_m"]))
        qq.append(float(r["q_cms"]) if r.get("q_cms") not in ("", None, "-") else np.nan)
    o = np.argsort(t)
    return np.array(t)[o], np.array(lv)[o], np.array(qq)[o]

fig, ax = plt.subplots(figsize=(9, 5), dpi=130)
for key, name, c in [("Ny1B_peak", "Ny.1B ใกล้เขื่อน (ต้นน้ำ)", "#6a1b9a"),
                     ("Ny7_peak", "Ny.7 สะพานหน้าจวนผู้ว้าฯ (ตัวเมือง)", "#1565c0"),
                     ("Ny7_rec", "Ny.7 (ต่อ)", "#1565c0"),
                     ("ThaChang_peak", "ท้ายน้ำปตร.ท่าช้าง", "#00838f")]:
    if key not in ev:
        continue
    t, lv, qq = series(key)
    ax.plot(t, lv, color=c, lw=1.6, label=name if "ต่อ" not in name else None)
dam = {r["date"]: float(r["released_mcm_d"] or 0) for r in
       csv.DictReader(open(A.parent / "analysis" / "dam_khun_dan_daily_2013_2026.csv", encoding="utf-8-sig"))}
days = [d for d in sorted(dam) if "2026-09-24" <= d <= "2026-10-04"]
ax2 = ax.twinx()
ax2.step([dt.date.fromisoformat(d) for d in days], [dam[d] for d in days], where="post",
         color="#ef6c00", lw=1.6, alpha=0.85, label="ปล่อยน้ำเขื่อน (ลลบ.ม./วัน)")
ax2.set_ylabel("ปริมาณปล่อยน้ำเขื่อน (ล้าน ลบ.ม./วัน)", color="#ef6c00")
ax2.tick_params(axis="y", colors="#ef6c00")
ax.set_ylabel("ระดับน้ำ (ม.รทก.)")
ax.set_title("ไฮโดรกราฟ 3 สถานี เทียบการปล่อยน้ำเขื่อน 24 ก.ย.–4 ต.ค. 69")
ax.xaxis.set_major_formatter(THAI_DAY_FMT)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=8.5, loc="upper left")
ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(OUT / "x2_hydro3.png"); plt.close(fig)
print("x2 saved")
