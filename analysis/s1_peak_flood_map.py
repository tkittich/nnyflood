"""Peak flood map: 27 Sep 2026 18:28 change-detection extent on DEM hillshade."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]

DER = Path(__file__).resolve().parent.parent / "data" / "13_sentinel1_copernicus" / "derived"  # อิง __file__
g = json.load(open(DER / "grid.json"))
RES = g["res"]
nx, ny = g["nx"], g["ny"]
x0, x1 = g["x0"], g["x1"]
y0, y1 = g["y0"], g["y1"]

dem = np.load(DER / "dem_30m.npy")
peak = np.load(DER / "flood_peak_27sep1828.npy")
oct2 = np.load(DER / "flood_2oct_validated.npy")
prov = np.load(DER / "mask_province.npy")

# hillshade
dy, dx = np.gradient(dem, RES * 111000, RES * 111000 * np.cos(np.radians(14.2)))
slope = np.sqrt(dx**2 + dy**2)
hs = 1 - slope / (np.nanpercentile(slope, 97) + 1e-9)
hs = np.clip(hs, 0.25, 1)

ext = [x0, x1, y0, y1]
fig, ax = plt.subplots(figsize=(11, 9), dpi=160)
ax.imshow(hs, extent=ext, cmap="gray", vmin=0, vmax=1, origin="upper", zorder=1)

# flood: peak = blue fill; 2 Oct = dashed outline via contour
peak_show = np.where(peak & prov, 1, 0).astype(float)
peak_show[~prov] = np.nan
cmap = matplotlib.colors.ListedColormap([(0, 0, 0, 0), (0.13, 0.44, 0.86, 0.62)])
ax.imshow(peak_show, extent=ext, cmap=cmap, vmin=0, vmax=1, origin="upper", zorder=3, interpolation="nearest")
oct2_show = np.where(oct2 & prov, 1, 0).astype(float)
ax.contour(oct2_show, levels=[0.5], colors=["#e07b00"], linewidths=0.7, extent=ext, origin="upper", zorder=4)

# boundaries
prov_geo = json.load(open(DER / "osm_nakhonnayok_boundary.json", encoding="utf-8"))["geojson"]
dists = json.load(open(DER / "osm_nakhonnayok_districts.json", encoding="utf-8"))

def rings(geo):
    if geo["type"] == "Polygon":
        return [geo["coordinates"][0]]
    return [p[0] for p in geo["coordinates"]]

for ring in rings(prov_geo):
    rr = np.array(ring)
    ax.plot(rr[:, 0], rr[:, 1], color="0.15", lw=1.4, zorder=5)
dist_style = dict(color="0.35", lw=0.8, ls="--", zorder=5)
centroids = {
    "อ.เมืองนครนายก": (101.315, 14.245, "111.8 ตร.กม."),
    "อ.องครักษ์": (101.075, 14.06, "241.7 ตร.กม."),
    "อ.บ้านนา": (100.985, 14.35, "85.9 ตร.กม."),
    "อ.ปากพลี": (101.385, 14.35, "69.9 ตร.กม."),
}
for name, d in dists.items():
    for ring in rings(d["geojson"]):
        rr = np.array(ring)
        ax.plot(rr[:, 0], rr[:, 1], **dist_style)
for name, (cx, cy, lab) in centroids.items():
    ax.text(cx, cy, name, fontsize=10.5, ha="center", color="0.05",
            fontweight="bold", zorder=7,
            bbox=dict(fc="white", ec="0.4", alpha=0.85, boxstyle="round,pad=0.25"))
    ax.text(cx, cy - 0.017, lab, fontsize=9, ha="center", color="#0b3d91", zorder=7,
            bbox=dict(fc="white", ec="none", alpha=0.75, boxstyle="round,pad=0.15"))

# waterways (OSM)
WATER = json.load(open(DER / "waterways.json"))
for r in WATER["rivers"]:
    rr = np.array(r["coords"])
    if r["name"] in ("แม่น้ำนครนายก", "แม่น้ำปราจีนบุรี"):
        ax.plot(rr[:, 0], rr[:, 1], color="#7fc4ff", lw=1.5, zorder=4)
    elif r["name"]:
        ax.plot(rr[:, 0], rr[:, 1], color="#9fd0f5", lw=0.7, zorder=3.5)
    else:
        ax.plot(rr[:, 0], rr[:, 1], color="#b9dcf7", lw=0.35, zorder=3.5)
for cw in WATER["canals"]:
    if not cw["name"]:
        continue
    rr = np.array(cw["coords"])
    ax.plot(rr[:, 0], rr[:, 1], color="#9fd0f5", lw=0.5, zorder=3.5)

# roads (OSM)
ROADS = json.load(open(DER / "roads_major.json"))
ROAD_STYLE = {"motorway": ("#ffb74d", 1.3), "trunk": ("#ffb74d", 1.1), "primary": ("#e0e0e0", 0.9),
              "secondary": ("#bdbdbd", 0.6), "tertiary": ("#9e9e9e", 0.4)}
labeled = set()
for rd in ROADS:
    col, lw = ROAD_STYLE.get(rd["cls"], ("#9e9e9e", 0.4))
    rr = np.array(rd["coords"])
    ax.plot(rr[:, 0], rr[:, 1], color=col, lw=lw, zorder=4, alpha=0.9)
    ref = rd["ref"].split(";")[0] if rd["ref"] else ""
    if ref in ("33", "304", "305", "331", "358") and ref not in labeled:
        m = rr[len(rr) // 2]
        ax.text(m[0], m[1], "ทล." + ref, fontsize=7, color="#ffd699", fontweight="bold", zorder=6, ha="center")
        labeled.add(ref)

# dam + gauge
ax.plot(101.0653, 14.3147, marker="^", ms=9, color="black", mec="white", zorder=8)
ax.annotate("เขื่อนขุนด่านปราการชล", (101.0653, 14.3147), xytext=(-8, 8),
            textcoords="offset points", ha="right", fontsize=9.5, fontweight="bold", zorder=8)
ax.plot(101.2148, 14.2079, marker="o", ms=6, color="#c10000", mec="white", zorder=8)
ax.annotate("สถานี Ny.7 (น้ำสูงสุด 9.23 ม.)", (101.2148, 14.2079), xytext=(8, -12),
            textcoords="offset points", ha="left", fontsize=9, color="#7a0000", zorder=8)

# scale bar (lon deg at 14.2N)
km10 = 10 / (111.32 * np.cos(np.radians(14.2)))
sx0, sy0 = x1 - km10 - 0.025, y0 + 0.016
ax.plot([sx0, sx0 + km10], [sy0, sy0], color="black", lw=3, zorder=8)
ax.text(sx0 + km10 / 2, sy0 + 0.004, "10 กม.", ha="center", fontsize=9, zorder=8)
ax.annotate("N", (x1 - 0.015, y0 + 0.052), fontsize=12, fontweight="bold", ha="center",
            arrowprops=dict(arrowstyle="-|>", color="black"), xytext=(x1 - 0.015, y0 + 0.036), zorder=8)

leg = [
    Patch(fc=(0.13, 0.44, 0.86, 0.62), ec="#0b3d91", label="น้ำท่วมช่วงน้ำสูงสุด 27 ก.ย. 2569 18:28 น. (509 ตร.กม.)"),
    Line2D([0], [0], color="#e07b00", lw=1.2, ls="--", label="น้ำค้าง 2 ต.ค. (วิธีเดียวกัน, 436 ตร.กม. · GISTDA=306.9)"),
    Line2D([0], [0], color="0.15", lw=1.4, label="เขตจังหวัดนครนายก (OSM)"),
]
ax.legend(handles=leg, loc="lower left", fontsize=9, framealpha=0.92)

ax.set_xlim(x0, x1)
ax.set_ylim(y0, y1)
ax.set_xlabel("ลองจิจูด (E)")
ax.set_ylabel("ลัติจูด (N)")
ax.set_title("ขอบเขตน้ำท่วมช่วงน้ำสูงสุด — อ.เมืองนครนายกและพื้นที่ใกล้เคียง 27 ก.ย. 2569 เวลา 18:28 น.",
             fontsize=13, fontweight="bold")
fig.text(0.5, 0.012,
         "ที่มา: Sentinel-1 S1D (27 ก.ย. vs 15 ก.ย. คู่วงโคจรเดียวกัน) ประมวลผลเอง — ΔVH≤−1 dB & ΔVV≤−2 dB & VH≤−18 dB "
         "· สอบเทียบวิธีกับ GISTDA บนฉาก 2 ต.ค. (P=0.60/R=0.84) · พื้นหลัง Copernicus DEM 30 ม.",
         ha="center", fontsize=7.8, color="0.25")
plt.tight_layout(rect=[0, 0.025, 1, 1])
out = Path(__file__).resolve().parent / "s1_peak_flood_map_27sep1828.png"  # อิง __file__
plt.savefig(out, dpi=160)
print("saved", out)
