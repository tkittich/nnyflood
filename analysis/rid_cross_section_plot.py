# วาดรูปตัดขวางลำน้ำจริง เทียบระดับน้ำสูงสุดเหตุการณ์ (Ny.7) + หน้าตัดท้ายน้ำ (Kgt.30 บางปะกง)
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ฟอนต์ไทย — ตามแบบเดียวกับ report/report_assets.py (ไม่ตั้งแล้วตัวอักษรไทยจะเป็นกล่อง)
plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]

ROOT = Path(__file__).resolve().parent.parent
DER = ROOT / "data" / "19_rid_cross_sections" / "derived"
OUT = ROOT / "analysis" / "rid_cross_section_ny7.png"


def load(stem):
    pts = []
    with open(DER / f"{stem}_profile.csv", encoding="utf-8") as f:
        next(f)
        for line in f:
            off, elev, _ = line.split(",", 2)
            pts.append((float(off), float(elev)))
    pts.sort()
    return np.array(pts)


fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 8.4), dpi=130)
fig.patch.set_facecolor("#0f1116")

for ax in (ax1, ax2):
    ax.set_facecolor("#0f1116")
    ax.tick_params(colors="#cfd3da", labelsize=8.5)
    for s in ax.spines.values():
        s.set_color("#3a3f4a")
    ax.grid(alpha=0.16, color="#8a93a5", lw=0.6)
    ax.set_ylabel("ระดับ (ม.รทก.)", color="#cfd3da", fontsize=9)

# ---- Ny.7 ----
p = load("Ny.7")
xs, ys = p[:, 0], p[:, 1]
ax1.fill_between(xs, ys, ys.min() - 1.2, color="#4b7fd6", alpha=0.16)
ax1.plot(xs, ys, color="#7fb3ff", lw=1.7, label="เส้นสำรวจหน้าตัด (RID 2568)")
ax1.axhline(7.64, color="#ff5c5c", lw=1.9, ls="--",
            label="ระดับสูงสุดเหตุการณ์ 7.64 ม.รทก. (เกจ 9.23)")
ax1.axhline(6.86, color="#ffd54f", lw=1.4, ls=":",
            label="ค่า BANKFULL ที่โปรเจคใช้ 6.86 (เกจ 8.45)")
ax1.axhline(8.213, color="#7ee787", lw=1.5, ls="-.",
            label="สันตลิ่ง/ตอม่อซ้ายสำรวจจริง 8.213 (เกจ 9.80)")
ax1.axhline(2.624, color="#9aa4b5", lw=1.0, ls="-",
            label="ผิวน้ำ ณ วันสำรวจ 2.624 (ราบสองฝั่ง = ตรวจ datum ผ่าน)")
ax1.annotate("", xy=(-40, 7.64), xytext=(-40, 8.213),
             arrowprops=dict(arrowstyle="<->", color="#7ee787", lw=1.2))
ax1.annotate("น้ำสูงสุด 7.64 ต่ำกว่าสันตลิ่ง 0.57 ม.\n→ น้ำไม่ล้นสันที่หน้าตัดนี้ แต่ท่วมที่ราบ",
             xy=(-38, 7.93), xytext=(8, 9.15), color="#7ee787", fontsize=8.4,
             arrowprops=dict(arrowstyle="->", color="#7ee787", lw=1.0))
ax1.annotate("พื้นตลิ่งลาดลงจากสัน (8.21) เหลือ 6.94 → น้ำท่วมที่ราบก่อนถึงสัน",
             xy=(-55, 6.94), xytext=(-58, 4.6), color="#ffd54f", fontsize=8.2,
             arrowprops=dict(arrowstyle="->", color="#ffd54f", lw=1.0))
ax1.set_title("Ny.7 แม่น้ำนครนายก (สะพานหน้าบ้านผู้ว่าฯ) — น้ำสูงสุดไม่ล้นสันตลิ่ง แต่ท่วมที่ราบ",
              color="#f0f3f8", fontsize=10.5)
ax1.legend(facecolor="#171a21", edgecolor="#3a3f4a", labelcolor="#cfd3da",
           fontsize=7.6, loc="lower right")
ax1.set_ylim(-4, 10)

# ---- Kgt.30 ----
p2 = load("Kgt.30")
x2, y2 = p2[:, 0], p2[:, 1]
ax2.fill_between(x2, y2, y2.min() - 2, color="#4b7fd6", alpha=0.16)
ax2.plot(x2, y2, color="#7fb3ff", lw=1.7, label="เส้นสำรวจหน้าตัด Kgt.30 (RID 2568)")
ax2.axhline(2.72, color="#7ee787", lw=1.4, ls="-.",
            label="สันตลิ่งซ้าย ~2.72 ม.รทก. (ตลิ่งต่ำแบบปากน้ำ)")
ax2.annotate(f"ท้องน้ำ {y2.min():.2f} ม.รทก.", xy=(114, y2.min()), xytext=(150, -9),
             color="#ffd54f", fontsize=8.4,
             arrowprops=dict(arrowstyle="->", color="#ffd54f", lw=1.0))
ax2.set_title("Kgt.30 แม่น้ำบางปะกง (ตัวเมืองฉะเชิงเทรา) — กว้าง ~380 ม. ใช้เป็นท้ายน้ำของแบบจำลอง",
              color="#f0f3f8", fontsize=10.5)
ax2.legend(facecolor="#171a21", edgecolor="#3a3f4a", labelcolor="#cfd3da",
           fontsize=7.6, loc="lower right")
ax2.set_xlabel("ระยะจากจุดอ้างอิง (ม.)", color="#cfd3da", fontsize=9)

fig.suptitle("รูปตัดขวางลำน้ำจริงจากกรมชลประทาน — ตรวจกับเหตุการณ์น้ำท่วม ก.ย. 2569",
             color="#f0f3f8", fontsize=11.5, y=0.985)
fig.tight_layout(rect=[0, 0, 1, 0.965])
fig.savefig(OUT, facecolor=fig.get_facecolor())
print("saved", OUT)
