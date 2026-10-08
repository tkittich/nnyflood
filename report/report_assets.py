"""Generate all chart/frame PNGs for the public HTML report."""
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

THAI_M = {1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
          7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."}
def thai_day(x, pos):
    d = mdates.num2date(x)
    return f"{d.day} {THAI_M[d.month]}"
def thai_month(x, pos):
    d = mdates.num2date(x)
    return THAI_M[d.month] + (f" {d.year + 543}" if d.month == 1 else "")
THAI_DAY_FMT = FuncFormatter(thai_day)
THAI_MONTH_FMT = FuncFormatter(thai_month)
import numpy as np
import shapefile
from shapely.geometry import shape as shp_shape

plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma", "Loma", "Garuda", "Norasi", "DejaVu Sans"]
# พาธ A/OUT/DER และ shapefile อิง ROOT ทั้งหมด — รันจากโฟลเดอร์ไหนก็ได้
ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "analysis"
OUT = ROOT / "report" / "assets"
OUT.mkdir(exist_ok=True)

BLUE, RED, ORANGE, GREEN, GRAY = "#1565c0", "#c62828", "#ef6c00", "#2e7d32", "#546e7a"

# ---------- C1 rain ----------
rows = list(csv.DictReader(open(A / "nn_rain_daily_2026.csv", encoding="utf-8-sig")))
heavy = ["STN0553_นางรอง", "BSCL_ศรีจุฬา", "WRRS_ศรีกะอาง", "BHUN_นาหินลาด", "48417_นครนายก", "STN1584_ท่ามะปราง"]
dates = [r["date"] for r in rows if "2026-09-12" <= r["date"] <= "2026-09-29"]
vals = np.array([np.nanmean([float(r[s]) if r[s] else np.nan for s in heavy]) for r in rows if "2026-09-12" <= r["date"] <= "2026-09-29"])
dt = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
ax.bar(dt, vals, color=BLUE, alpha=0.85, width=0.75)
ax2 = ax.twinx()
ax2.plot(dt, np.cumsum(vals), color=RED, lw=2.2, marker="o", ms=3.5)
ax2.set_ylabel("ฝนสะสม (มม.)", color=RED)
ax2.tick_params(axis="y", labelcolor=RED)
ax.set_ylabel("ฝนรายวัน เฉลี่ยแถบหนัก (มม.)")
ax.xaxis.set_major_formatter(THAI_DAY_FMT)
ax.annotate("26 ก.ย.\nเริ่มท่วมค่ำนี้", xy=(datetime(2026, 9, 26), 176), xytext=(-70, 30),
            textcoords="offset points", fontsize=9, color=RED, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=RED))
ax.set_title("ฝนตกหนักต่อเนื่อง 18 วัน (12–29 ก.ย. 2569) — เฉลี่ยสถานีแถบฝนหนัก 6 สถานี (รวม 1,058–1,416 มม./สถานี)")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout(); plt.savefig(OUT / "c1_rain.png"); plt.close()

# ---------- data for C2/C3/C4 ----------
lv = list(csv.DictReader(open(A / "waterlevel_hourly_sep2026_stations.csv", encoding="utf-8-sig")))
ny7 = [(datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M"), float(r["Ny7_เมือง"])) for r in lv if r["Ny7_เมือง"]]
dam = {r["date"]: r for r in csv.DictReader(open(A / "dam_khun_dan_daily_2013_2026.csv", encoding="utf-8-sig"))}
rel_daily = {"2026-09-24": 1.50, "2026-09-25": 2.21, "2026-09-26": 4.61, "2026-09-27": 31.66,
             "2026-09-28": 19.43, "2026-09-29": 13.41, "2026-09-30": 5.48, "2026-10-01": 1.27, "2026-10-02": 6.38}
def q_of(g):
    h = g - 1.59
    return 242 * (h - 4.55) ** 0.66 if h > 4.55 else 0.0
def stage_of(Q):
    if Q <= 62:
        return 6.14 + Q / 62 * 0.2
    return 4.55 + (Q / 242) ** (1 / 0.66) + 1.59
QBANK = q_of(8.45)

# ---------- C2 level + release ----------
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
seg = [(t, g) for t, g in ny7 if datetime(2026, 9, 24) <= t <= datetime(2026, 10, 2)]
ts = [t for t, _ in seg]; gs = [g for _, g in seg]
ax.plot(ts, gs, color=BLUE, lw=2, label="ระดับน้ำแม่น้ำที่ตัวเมือง (สถานี Ny.7)")
ax.axhline(8.45, color=RED, ls="--", lw=1.4)
ax.text(datetime(2026, 9, 24, 2), 8.5, "ระดับล้นตลิ่ง ~8.45 ม. (น้ำเริ่มท่วมบ้านเรือน)", color=RED, fontsize=9, fontweight="bold")
rel_ts = list(rel_daily.keys()); rel_vs = [v * 11.574 for v in rel_daily.values()]
ax2 = ax.twinx()
ax2.step([datetime.strptime(d, "%Y-%m-%d") + timedelta(hours=12) for d in rel_ts], rel_vs, where="post", color=ORANGE, lw=2)
ax2.set_ylabel("อัตราปล่อยน้ำเขื่อน (ม³/วินาที)", color=ORANGE)
ax2.tick_params(axis="y", labelcolor=ORANGE)
ax2.annotate("เร่งปล่อย 366 ม³/วิ", xy=(datetime(2026, 9, 27, 12), 366), xytext=(-16, -52),
             textcoords="offset points", color=ORANGE, fontsize=9, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=ORANGE))
ax.annotate("เริ่มท่วม\n26 ก.ย. 23:00", xy=(datetime(2026, 9, 26, 23), 8.49), xytext=(-80, 42),
            textcoords="offset points", fontsize=9, fontweight="bold",
            arrowprops=dict(arrowstyle="->", lw=1.2))
ax.annotate("น้ำสูงสุด 9.23 ม.\n27 ก.ย. 10:00", xy=(datetime(2026, 9, 27, 10), 9.23), xytext=(14, 8),
            textcoords="offset points", fontsize=9, fontweight="bold", color="#0d47a1",
            arrowprops=dict(arrowstyle="->", color="#0d47a1"))
ax.annotate("ลดการปล่อย\nน้ำลดเร็ว", xy=(datetime(2026, 9, 30, 6), 7.6), xytext=(10, 35),
            textcoords="offset points", fontsize=9, color=GREEN, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=GREEN))
ax.set_ylabel("ระดับน้ำ (ม. ระดับเกจ)")
ax.xaxis.set_major_formatter(THAI_DAY_FMT)
ax.set_title("ระดับน้ำที่ตัวเมือง vs การปล่อยน้ำเขื่อนขุนด่านฯ (24 ก.ย.–2 ต.ค. 2569)", pad=14)
ax.legend(loc="upper right", fontsize=9)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.subplots_adjust(top=0.88)
plt.savefig(OUT / "c2_level_release.png"); plt.close()

# ---------- C3 storage vs URC ----------
fig, ax = plt.subplots(figsize=(9.5, 4.2), dpi=150)
dts, st, urc = [], [], []
for d in sorted(dam):
    if "2026-07-15" <= d <= "2026-10-04":
        dts.append(datetime.strptime(d, "%Y-%m-%d"))
        st.append(float(dam[d]["storage_mcm"]))
        urc.append(float(dam[d]["upper_rule_curve_mcm"]) if dam[d]["upper_rule_curve_mcm"] else np.nan)
ax.plot(dts, st, color=BLUE, lw=2.2, label="ปริมาณน้ำเก็บจริง")
ax.plot(dts, urc, color=RED, ls="--", lw=1.8, label="เส้นควบคุมบน (URC)")
ax.axhline(224, color=GRAY, ls=":", lw=1.5)
ax.text(dts[2], 226, "ความจุเก็บปกติ 224 ลลบ.ม.", color=GRAY, fontsize=9)
first_above = next(t for t, s, u in zip(dts, st, urc) if s > u)
ax.annotate(f"ทะลุเส้นควบคุม 30 ส.ค.\nเหนือเส้นต่อเนื่อง 36 วัน", xy=(first_above, st[dts.index(first_above)]),
            xytext=(20, -52), textcoords="offset points", fontsize=9.5, fontweight="bold", color=RED,
            arrowprops=dict(arrowstyle="->", color=RED))
ax.annotate("เต็ม 224.34\nเช้า 27 ก.ย.", xy=(datetime(2026, 9, 27), 224.34), xytext=(-105, -8),
            textcoords="offset points", fontsize=9.5, fontweight="bold",
            arrowprops=dict(arrowstyle="->"))
ax.set_ylabel("ล้านลบ.ม.")
ax.xaxis.set_major_formatter(THAI_MONTH_FMT)
ax.set_title("น้ำเก็บเขื่อนขุนด่านฯ เหนือเส้นควบคุมบนตั้งแต่ 30 ส.ค. — เหลือพื้นที่กันน้ำน้อยเมื่อพายุมาถึง")
ax.legend(loc="upper left", fontsize=9)
ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(OUT / "c3_storage_urc.png"); plt.close()

# ---------- C4 scenarios ----------
def scenario(cap=None, zero_until=None):
    out = []
    for t, g in ny7:
        if not (datetime(2026, 9, 25) <= t <= datetime(2026, 10, 3)):
            continue
        src = (t - timedelta(hours=12)).strftime("%Y-%m-%d")
        r = rel_daily.get(src, 0.0)
        s_rate = r * 1e6 / 86400
        if cap is not None and src >= "2026-09-27":
            s_rate = min(r, cap) * 1e6 / 86400
        if zero_until and src <= zero_until:
            s_rate = 0.0
        Q = max(q_of(g) - r * 1e6 / 86400 + s_rate, 15)
        out.append((t, stage_of(Q)))
    return out

fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.plot(ts, gs, color=BLUE, lw=2.4, label="ที่เกิดจริง (น้ำสูงสุด 9.23 ม. · ท่วมขัง 65 ชม.)")
s1 = scenario(cap=12.0)
s2 = scenario(zero_until="2026-09-30")
ax.plot([t for t, _ in s1], [g for _, g in s1], color=ORANGE, lw=1.8, ls="--",
        label="ทำตาม URC + กะปล่อย ≤140 ม³/วิ ตั้งแต่ 27 ก.ย. (ล้นตลิ่งเหลือ 12 ชม.)")
ax.plot([t for t, _ in s2], [g for _, g in s2], color=GREEN, lw=1.8, ls="-.",
        label="URC + กักน้ำไว้ช่วงน้ำสูงสุด (น้ำสูงสุด 8.75 ม. · เหลือ 8 ชม.)")
ax.fill_between(ts, 8.45, gs, where=np.array(gs) > 8.45, color=RED, alpha=0.14)
ax.axhline(8.45, color=RED, ls=":", lw=1.2)
ax.text(datetime(2026, 9, 25), 8.5, "ระดับล้นตลิ่ง", color=RED, fontsize=9)
ax.set_ylabel("ระดับน้ำ (ม. เกจ)")
ax.xaxis.set_major_formatter(THAI_DAY_FMT)
ax.set_title("ถ้าบริหารน้ำต่างไป — จำลองจากไฮโดรกราฟจริง (ลบองค์ประกอบการปล่อยน้ำเขื่อนตามสถานการณ์)")
ax.legend(loc="upper left", fontsize=8.6)
ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(OUT / "c4_scenarios.png"); plt.close()

print("charts done")

# ---------- flood frames ----------
DER = ROOT / "data" / "13_sentinel1_copernicus" / "derived"
gr = json.load(open(DER / "grid.json"))
prov_geo = json.load(open(DER / "osm_nakhonnayok_boundary.json", encoding="utf-8"))["geojson"]
import matplotlib.colors as mcolors

# ภูมิประเทศพื้นหลัง: hillshade จาก DEM Copernicus GLO-30 30 ม. (สีเทากลาง — ไม่แย่งสีกับน้ำท่วม/ถนน/แม่น้ำ)
# พื้นที่นอกครอบ DEM (NaN ~52% ของกรอบกริด) วาดเป็นเทาอ่อนเกือบขาว
DEM = np.load(DER / "dem_30m.npy")
def _hillshade():
    z = DEM.astype(float)
    gy, gx = np.gradient(np.nan_to_num(z, nan=0.0))
    az, alt = np.radians(315.0), np.radians(45.0)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    sh = np.cos(alt) * np.cos(slope) + np.sin(alt) * np.sin(slope) * np.cos(az - aspect)
    sh = np.clip((sh - 0.25) / 0.75, 0.05, 1.0)
    sh = np.round(sh * 13) / 13.0          # posterize ระดับเทา — PNG บีบได้ดีกว่า gradient ต่อเนื่องหลายเท่า
    sh[np.isnan(z)] = 0.97
    return sh
SHADED = _hillshade()          # คำนวณครั้งเดียว ใช้ร่วมทุกแผนที่
# โทนน้ำตาลตามระดับความสูงจริง: ขาว/ครีม = ที่ราบ → น้ำตาลเข้ม = ภูเขา (คู่กับ hillshade เป็นแสงเงา)
DEM_BINS = np.array([0, 30, 80, 150, 300, 500, 750, 1100, 99999])
DEM_COLORS = np.array([
    [1.00, 0.99, 0.96],   # <30 ม. ที่ราบน้ำท่วมถึง
    [0.98, 0.95, 0.87],
    [0.93, 0.87, 0.72],
    [0.85, 0.75, 0.55],
    [0.71, 0.59, 0.40],
    [0.56, 0.45, 0.30],
    [0.41, 0.33, 0.22],
    [0.27, 0.21, 0.14],   # >1100 ม. ยอดเขาเขาใหญ่
])
def _terrain_rgb():
    valid = np.isfinite(DEM)
    idx = np.clip(np.digitize(np.where(valid, DEM, 0), DEM_BINS) - 1, 0, len(DEM_COLORS) - 1)
    # ที่ราบ (<80 ม.) เงาจางมาก — hillshade ของ DSM ติด noise ต้นไม้/บ้าน = ลายเทา
    # ไล่เข้มขึ้นช่วง 80–300 ม. แล้วเต็มกำลังบนภูเขา
    t = np.clip((np.where(valid, DEM, 0) - 80) / 220, 0, 1)
    factor = (0.85 + 0.15 * SHADED) * (1 - t) + (0.45 + 0.55 * SHADED) * t
    rgb = DEM_COLORS[idx] * factor[..., None]
    rgb = np.round(rgb * 12) / 12                                # posterize — ไฟล์เล็ก
    rgb[~valid] = 1.0                                            # นอกครอบ DEM = ขาว
    return rgb
TERRAIN_RGB = _terrain_rgb()
def draw_terrain(ax):
    ax.imshow(TERRAIN_RGB, extent=[gr["x0"], gr["x1"], gr["y0"], gr["y1"]], origin="upper",
              interpolation="nearest", aspect="auto", zorder=0.6)

ROADS = json.load(open(DER / "roads_major.json"))
ROAD_STYLE = {"motorway": ("#b26a00", 1.5), "trunk": ("#b26a00", 1.3), "primary": ("#9b8b7a", 1.0),
              "secondary": ("#c1b6ac", 0.7), "tertiary": ("#d8d0c8", 0.5)}
ROAD_LABEL_REFS = {"33", "304", "305", "331", "358"}

WATER = json.load(open(DER / "waterways.json"))
def _segments(c, max_km=0.7):
    # แยกช่วงที่กระโดด (กันเส้นตรงเชื่อมปลอมเวลา polyline ถูกต่อจากหลาย way)
    c = np.asarray(c, float)
    if len(c) < 2:
        return [c]
    d = np.hypot(np.diff(c[:, 0]), np.diff(c[:, 1])) * 111
    cuts = np.where(d > max_km)[0]
    segs, prev = [], 0
    for j in list(cuts) + [len(c) - 1]:
        if j - prev >= 1:
            segs.append(c[prev:j + 1])
        prev = j + 1
    return segs

def draw_water(ax, labels=False):
    import numpy as np
    from matplotlib.patches import Polygon as MplPoly
    for wb in WATER["waters"] + WATER.get("reservoir", []):
        c = np.array(wb["coords"])
        ax.add_patch(MplPoly(c, closed=True, facecolor="#b2dfdb", edgecolor="none", alpha=0.85, zorder=1.5))
    for cn in WATER["canals"]:
        for seg in _segments(cn["coords"]):
            ax.plot(seg[:, 0], seg[:, 1], color="#5fb3aa", lw=0.55, zorder=2.6, alpha=0.9)
    for rv in WATER["rivers"]:
        for seg in _segments(rv["coords"]):
            ax.plot(seg[:, 0], seg[:, 1], color="#1e8f82", lw=1.15, zorder=2.7)
    if labels:
        done = set()
        for rv in sorted(WATER["rivers"], key=lambda r: -r["km"]):
            nm = rv["name"]
            if nm and nm not in done and rv["km"] > 20:
                c = np.array(rv["coords"]); m = c[len(c) // 2]
                ax.text(m[0], m[1], nm, fontsize=6.8, color="#0e6655", style="italic", zorder=6,
                        ha="center", bbox=dict(fc="white", ec="none", alpha=0.6, pad=0.5))
                done.add(nm)
        res_poly = WATER.get("reservoir", [])
        if res_poly:
            pts = [p for w in res_poly for p in w["coords"]]
            cx = sum(p[0] for p in pts)/len(pts); cy = sum(p[1] for p in pts)/len(pts)
            

def draw_roads(ax, label=False):
    import numpy as np
    for rd in ROADS:
        col, lw = ROAD_STYLE.get(rd["cls"], ("#d8d0c8", 0.5))
        c = np.array(rd["coords"])
        ax.plot(c[:, 0], c[:, 1], color=col, lw=lw, zorder=2, solid_capstyle="round")
    if label:
        done = set()
        for rd in ROADS:
            ref = rd["ref"].split(";")[0] if rd["ref"] else ""
            if ref in ROAD_LABEL_REFS and ref not in done:
                c = np.array(rd["coords"]); m = c[len(c) // 2]
                ax.text(m[0], m[1], "ทล." + ref, fontsize=6.5, color="#8a5a00", fontweight="bold", zorder=6,
                        ha="center", bbox=dict(fc="white", ec="none", alpha=0.65, pad=0.6))
                done.add(ref)

def base_ax(title, area_txt, terrain=True):
    fig, ax = plt.subplots(figsize=(7.6, 7.5), dpi=120)
    ax.set_aspect(110.96 / (111.32 * np.cos(np.radians(14.24))))
    ax.set_xlim(gr["x0"], gr["x1"]); ax.set_ylim(gr["y0"], gr["y1"])
    ax.set_xticks([]); ax.set_yticks([])
    if terrain:
        draw_terrain(ax)
    for ring in ([prov_geo["coordinates"][0]] if prov_geo["type"] == "Polygon" else [p[0] for p in prov_geo["coordinates"]]):
        rr = np.array(ring); ax.plot(rr[:, 0], rr[:, 1], color="0.25", lw=1.2)
    draw_water(ax)
    draw_roads(ax)
    ax.set_title(title, fontsize=12.5, fontweight="bold")
    ax.text(0.02, 0.02, area_txt, transform=ax.transAxes, fontsize=15, color="#0d47a1",
            fontweight="bold", bbox=dict(fc="white", ec="#0d47a1", alpha=0.9, boxstyle="round,pad=0.4"))
    return fig, ax

def npy_frame(npy, title, area, outname=None):
    # สร้างสองเวอร์ชัน: พร้อมภูมิประเทศ (ใช้ปกติ) และ _plain (สำหรับสวิตช์เปิด/ปิดภูมิประเทศในสไลเดอร์)
    base = outname or npy.replace("flood_", "").replace("_validated", "").replace(".npy", "")
    mask = np.load(DER / npy)
    prov = np.load(DER / "mask_province.npy")
    show = np.where(mask & prov, 1.0, np.nan)
    for terr, suffix in ((True, ""), (False, "_plain")):
        fig, ax = base_ax(title, area, terrain=terr)
        ax.imshow(show, extent=[gr["x0"], gr["x1"], gr["y0"], gr["y1"]], origin="upper",
                  cmap=mcolors.ListedColormap([(0.13, 0.44, 0.86, 0.75)]), vmin=0, vmax=1,
                  interpolation="nearest", aspect="auto", zorder=1.2)
        fig.tight_layout()
        fig.savefig(OUT / f"frame_{base}{suffix}.jpg", pil_kwargs={"quality": 88})
        plt.close(fig)
    print("frame npy", npy)

npy_frame("flood_20260922_1820.npy", "22 ก.ย. 2569 18:20 น. (Sentinel-1 · ประมวลผลเอง)", "0 ตร.กม. — ก่อนเหตุการณ์")
npy_frame("flood_20260927_0600.npy", "27 ก.ย. 2569 06:00 น. (Sentinel-1 · ประมวลผลเอง)", "62.2 ตร.กม. (แถบครอบ 34%)", outname="ours_27sep0600")
npy_frame("flood_20260928_1819.npy", "28 ก.ย. 2569 18:19 น. (Sentinel-1 · ประมวลผลเอง)", "แถบครอบ 9% ตะวันออก = 0")
npy_frame("flood_2oct_validated.npy", "2 ต.ค. 2569 06:09 น. (Sentinel-1 · ประมวลผลเอง)", "436.3 ตร.กม.")

frames = [
    ("rd2_20260924_1815", "24 ก.ย. 2569 18:15 น. (RADARSAT-2 · GISTDA)", "11.8 ตร.กม."),
    ("S1D_20260927_0601", "27 ก.ย. 2569 06:01 น. (Sentinel-1 · GISTDA)", "8.3 ตร.กม."),
    ("PEAK_OURS", "27 ก.ย. 2569 18:28 น. (Sentinel-1 · ประมวลผลเอง)", "509.3 ตร.กม."),
    ("S1D_20261002_0609", "2 ต.ค. 2569 06:09 น. (Sentinel-1 · GISTDA)", "306.9 ตร.กม."),
]
for name, title, area in frames:
    for terr, suffix in ((True, ""), (False, "_plain")):
        fig, ax = base_ax(title, area, terrain=terr)
        if name == "PEAK_OURS":
            mask = np.load(DER / "flood_peak_27sep1828.npy")
            prov = np.load(DER / "mask_province.npy")
            show = np.where(mask & prov, 1.0, np.nan)
            ax.imshow(show, extent=[gr["x0"], gr["x1"], gr["y0"], gr["y1"]], origin="upper",
                      cmap=mcolors.ListedColormap([(0.13, 0.44, 0.86, 0.75)]), vmin=0, vmax=1,
                      interpolation="nearest", aspect="auto", zorder=1.2)
        else:
            r = shapefile.Reader(ROOT / "data" / "manual" / f"shp_{name}" / f"{name}.shp", encoding="latin-1")
            fields = [f[0] for f in r.fields[1:]]
            i_id = fields.index("PV_IDN")
            for sr in r.iterShapeRecords():
                if int(sr.record[i_id]) != 26:
                    continue
                geom = shp_shape(sr.shape.__geo_interface__)
                if not geom.is_valid:
                    geom = geom.buffer(0)
                geoms = [geom] if geom.geom_type == "Polygon" else [p for p in geom.geoms if p.geom_type == "Polygon"]
                for p in geoms:
                    x, y = p.exterior.xy
                    ax.fill(x, y, color=(0.13, 0.44, 0.86, 0.75), lw=0, zorder=1.2)
        fig.tight_layout()
        fig.savefig(OUT / f"frame_{name}{suffix}.jpg", pil_kwargs={"quality": 88})
        plt.close(fig)
    print("frame", name)
print("all assets done ->", OUT)

# ---------- zone scenario map (with roads) ----------
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
fig, ax = plt.subplots(figsize=(7.6, 9.1), dpi=120)
ax.set_aspect(110.96 / (111.32 * np.cos(np.radians(14.24))))
ax.set_xlim(gr["x0"], gr["x1"]); ax.set_ylim(gr["y0"], gr["y1"])
ax.set_xticks([]); ax.set_yticks([])
for ring in ([prov_geo["coordinates"][0]] if prov_geo["type"] == "Polygon" else [p[0] for p in prov_geo["coordinates"]]):
    rr = np.array(ring); ax.plot(rr[:, 0], rr[:, 1], color="0.25", lw=1.2)
draw_terrain(ax)
draw_water(ax)
draw_roads(ax)
both_m = np.load(DER / "flood_zone_both.npy"); only_m = np.load(DER / "flood_zone_peak_only.npy")
prov_m = np.load(DER / "mask_province.npy")
for mask, color in ((both_m, (0.85, 0.20, 0.13, 0.75)), (only_m, (0.20, 0.60, 0.25, 0.75))):
    m = np.where(mask & prov_m, 1.0, np.nan)
    ax.imshow(m, extent=[gr["x0"], gr["x1"], gr["y0"], gr["y1"]], origin="upper",
              cmap=mcolors.ListedColormap([color]), vmin=0, vmax=1, interpolation="nearest",
              aspect="auto", zorder=1.2)
ax.set_title("โซนผลกระทบภายใต้ 'การบริหารสมบูรณ์แบบ' (ประมาณการจากดาวเทียบ 2 ช่วงเวลา)", fontsize=12.5, fontweight="bold")
ax.legend(handles=[
    Patch(fc=(0.20, 0.60, 0.25, 0.75), label="รอด — แห้งโดย 2 ต.ค. (~219 ตร.กม.)"),
    Patch(fc=(0.85, 0.20, 0.13, 0.75), label="ยังมีน้ำ ระบายใน ~1–2 วัน (~291 ตร.กม. · แถบริมน้ำ/คลอง)"),
    Line2D([0], [0], color="#17457e", lw=1.6, label="แม่น้ำ (OSM)"),
    Line2D([0], [0], color="#a8cbe8", lw=1.2, label="คลองสายใหญ่ (OSM)"),
    Line2D([0], [0], color="#b26a00", lw=1.5, label="ถนนสายหลัก (OSM)"),
    Line2D([0], [0], color="0.25", lw=1.2, label="เขตจังหวัด (OSM)"),
    Patch(fc=(0.85, 0.75, 0.55), label="ภูมิประเทศ: น้ำตาลเข้ม = สูง (DEM 30 ม.)")],
    loc="upper center", bbox_to_anchor=(0.5, -0.004), ncol=2, fontsize=8.4,
    framealpha=0.95, columnspacing=1.3, handlelength=1.7, borderpad=0.55)
ax.text(0.985, 0.988, "สมมติฐาน: น้ำสูงสุด 9.23 → 8.75 ม. (−0.48) · เหนือตลิ่ง 65 → 8 ชม.", transform=ax.transAxes, ha="right", va="top",
        fontsize=9, color="#0d47a1", fontweight="bold",
        bbox=dict(fc="white", ec="#0d47a1", alpha=0.9, boxstyle="round,pad=0.35"))
fig.tight_layout()
fig.savefig(OUT / "zone_scenario.png")
plt.close(fig)
print("zone map with roads saved")


# ---------- c6: อนุกรมพื้นที่-เวลา ฉบับข้อมูลครบทุกจุดที่มี ----------
from datetime import datetime
import matplotlib.pyplot as plt2
fig, ax = plt2.subplots(figsize=(8.6, 4.6), dpi=130)
ours = [
    (datetime(2026, 9, 15, 18, 28), 0.0, "ฐานก่อนน้ำท่วม (คู่วงโคจร)"),
    (datetime(2026, 9, 19, 6, 9), 0.0, "ฐานก่อนน้ำท่วม (คู่วงโคจร)"),
    (datetime(2026, 9, 22, 18, 20), 0.0, "ก่อนเหตุการณ์ (แถบครอบ 9%)"),
    (datetime(2026, 9, 27, 6, 0), 62.2, "แถบครอบ 34%"),
    (datetime(2026, 9, 27, 18, 28), 509.3, "น้ำสูงสุด"),
    (datetime(2026, 10, 2, 6, 9), 436.3, ""),
]
gistda = [
    (datetime(2026, 9, 24, 18, 15), 11.8, ""),
    (datetime(2026, 9, 27, 6, 1), 8.3, ""),
    (datetime(2026, 10, 2, 6, 9), 306.9, ""),
]
ax.plot([d for d, v, n in ours], [v for d, v, n in ours], "o-", color="#1565c0", lw=2,
        ms=6, label="ประมวลผลเองจาก Sentinel-1 (COPERNICUS)")
ax.plot([d for d, v, n in gistda], [v for d, v, n in gistda], "s--", color="#ef6c00", lw=1.6,
        ms=6, label="ผลิตภัณฑ์ทางการ GISTDA")
ax.annotate("62.2 ตร.กม. (ภาพครอบเพียง 34% — ฉากเดียวกับที่ GISTDA รายงาน 8.3 ทั้งจังหวัด)",
            xy=ours[3][:2], xytext=(-4, 60), textcoords="offset points", fontsize=7.8, color="#1565c0",
            ha="right", va="bottom", arrowprops=dict(arrowstyle="->", color="#1565c0", lw=0.8))
ax.annotate("น้ำสูงสุด 509.3 · 27 ก.ย. 18:28", xy=ours[4][:2], xytext=(12, 2), textcoords="offset points",
            fontsize=8.5, color="#0d47a1", fontweight="bold", va="center")
ax.annotate("2 ต.ค.: เรา 436.3 · GISTDA 306.9", xy=(ours[5][0], 395), xytext=(-16, -4),
            textcoords="offset points", fontsize=8, color="#37474f", ha="right", va="top")
ax.annotate("8.3 — ต่ำกว่าพื้นที่จริงมาก (น้ำขณะถ่าย ≈ ระดับน้ำสูงสุด)", xy=gistda[1][:2], xytext=(10, 10),
            textcoords="offset points", fontsize=7.5, color="#ef6c00", va="bottom")
ax.annotate("28 ก.ย. 18:19 = 0 ในแถบครอบ 9% ตะวันออก (ส่วนใหญ่เป็นป่าเขา ไม่ใช่พื้นที่ท่วมหลัก จึงไม่จุด)",
            xy=(datetime(2026, 9, 29, 6), 432), fontsize=7.5, color="#78909c", ha="right")
ax.margins(x=0.07)
ax.set_ylabel("พื้นที่น้ำท่วม (ตร.กม.)")
ax.set_title("อนุกรมพื้นที่น้ำท่วมนครนายก — ทุกจุดข้อมูลที่มี (15 ก.ย. – 2 ต.ค. 2569)")
ax.xaxis.set_major_formatter(THAI_DAY_FMT)
ax.legend(fontsize=8.5, loc="upper left")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "c6_area_time.png")
plt2.close(fig)
print("c6 complete-series saved")

# ---------- คัดลอกรูปที่ "สคริปต์ใน analysis/ เป็นคนสร้าง" เข้ามาใน report/assets ----------
# เหตุที่ต้องมีบล็อกนี้: build_*_report.py อ่านรูปจาก report/assets เท่านั้น ขณะที่สคริปต์
# โมเดลเขียนรูปไว้ข้างเอกสารของตัวเองใน analysis/ — ต้องคัดลอกมาทุกครั้งก่อนประกอบรายงาน
# ไม่งั้นรายงานอาจใช้รูปที่ไม่ตรงกับตัวเลขในเนื้อหาได้เงียบ ๆ
import shutil
for _fig, _producer in (("goal4_model_v1_event.png", "analysis/goal4_model_v1.py"),
                        ("goal4_counterfactual_model.png", "analysis/goal4_counterfactual_model.py")):
    _src = A / _fig
    if _src.exists():
        shutil.copy2(_src, OUT / _fig)
        print(f"copied {_fig}  <- {_producer}")
    else:
        print(f"!! ขาด {_fig} — รัน {_producer} ก่อน")
