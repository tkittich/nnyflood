"""ส่วนกลางของรายงานเจ้าพระยา2 (ฉบับประชาชน/ฉบับวิชาการ): ข้อมูลจาก canonical + กราฟ
อ่าน analysis/goal7/canonical.json เท่านั้น — ห้ามพิมพ์ตัวเลขวิเคราะห์เป็น literal ในรายงาน"""
from __future__ import annotations

import glob
import json
import math
import os
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapefile
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "report"))
from goal6_reportlib import figure, h2, h3, note, page, prose, table, toc  # noqa: E402

warnings.filterwarnings("ignore")
plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]
plt.rcParams["axes.unicode_minus"] = False
C = json.loads((ROOT / "analysis/goal7/canonical.json").read_text(encoding="utf-8"))
D7 = ROOT / "data/32_goal7_chaophraya2/derived"
WC = json.loads((ROOT / "analysis/goal7/waterchart_overlay.json").read_text(encoding="utf-8"))
ASSETS = ROOT / "report/assets"
F, ST, DEM, MN, C2, PD, CA, FB = (C[k] for k in ("facts", "structures", "dem", "manning", "c2", "pasak_dam", "corridor_area", "flood_band"))
NN = ST["nakhonnayok"]
SCENE = FB["scenes"]["S1D_20261002_0609"]

INK, BLUE, ORANGE, GREY = "#1c2b33", "#1d6fb8", "#a14a00", "#5a6b7b"   # ตัวอักษร ≥ 4.5 · แท่ง/เส้น ≥ 3.0 บนขาว


def fmt(x, nd=0):
    if isinstance(x, str):
        return x
    return f"{x:,.{nd}f}"


def tier(k):
    return f"ชั้น {F[k]['tier']}"



# ---------------- ภูมิประเทศ ถนน แม่น้ำลำคลอง (แบบเดียวกับรายงาน 1) ----------------
_DER13 = ROOT / "data/13_sentinel1_copernicus/derived"
_DEM_TILES = ROOT / "data/08_dem_topography/raw"
# ที่ราบภาคกลางสูงต่างกันไม่กี่เมตร จึงแบ่งระดับถี่ช่วงต่ำ (ต่างจากรายงาน 1 ที่แบ่งตั้งแต่ 30 ม.)
_ELEV_BINS = [-99, 1, 2, 3, 5, 10, 20, 50, 100, 99999]
_ELEV_COLORS = ["#e6f0e0", "#d6e8c8", "#e9efc6", "#f3ecb8", "#ecdba0", "#aa8636", "#ac8446", "#a07f50", "#7a5e3a"]
_ELEV_LABELS = ["ต่ำกว่า 1 ม.", "1–2 ม.", "2–3 ม.", "3–5 ม.", "5–10 ม.", "10–20 ม.", "20–50 ม.", "50–100 ม.", "สูงกว่า 100 ม."]


def _load_dem(x0, x1, y0, y1, step):
    import rasterio
    from rasterio.windows import from_bounds
    xs = np.arange(x0, x1, step)
    ys = np.arange(y1, y0, -step)
    out = np.full((len(ys), len(xs)), np.nan, dtype="float32")
    for lat in range(int(math.floor(y0)), int(math.floor(y1)) + 1):
        for lon in range(int(math.floor(x0)), int(math.floor(x1)) + 1):
            f = _DEM_TILES / f"Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM.tif"
            if not f.exists():
                continue
            bx0, bx1, by0, by1 = max(x0, lon), min(x1, lon + 1), max(y0, lat), min(y1, lat + 1)
            if bx0 >= bx1 or by0 >= by1:
                continue
            with rasterio.open(f) as ds:
                w = from_bounds(bx0, by0, bx1, by1, ds.transform)
                ny = max(1, int(round((by1 - by0) / step))); nx = max(1, int(round((bx1 - bx0) / step)))
                a = ds.read(1, window=w, out_shape=(ny, nx), resampling=rasterio.enums.Resampling.average, boundless=True).astype("float32")
            ix = int(round((bx0 - x0) / step)); iy = int(round((y1 - by1) / step))
            h = min(ny, out.shape[0] - iy); wv = min(nx, out.shape[1] - ix)
            if h > 0 and wv > 0:
                out[iy:iy + h, ix:ix + wv] = a[:h, :wv]
    return out


def draw_basemap(ax, x0, x1, y0, y1, step=0.0006, roads=True, water=True, legend=True):
    """ภูมิประเทศสีตามความสูง + ถนนสายหลัก + แม่น้ำลำคลอง (ถนนและลำน้ำมีเฉพาะในกรอบข้อมูลจังหวัดนครนายกของรายงาน 1)"""
    from matplotlib.colors import ListedColormap, BoundaryNorm
    z = _load_dem(x0, x1, y0, y1, step)
    cm = ListedColormap(_ELEV_COLORS); cm.set_bad("#ffffff")
    ax.imshow(np.ma.masked_invalid(z), extent=[x0, x1, y0, y1], origin="upper", cmap=cm,
              norm=BoundaryNorm(_ELEV_BINS, cm.N), interpolation="nearest", aspect="auto", zorder=0)
    if water:
        try:
            W = json.loads((_DER13 / "waterways.json").read_text(encoding="utf-8"))
            for wb in W.get("waters", []) + W.get("reservoir", []):
                c = np.array(wb["coords"])
                if c[:, 0].max() < x0 or c[:, 0].min() > x1 or c[:, 1].max() < y0 or c[:, 1].min() > y1:
                    continue
                ax.fill(c[:, 0], c[:, 1], color="#3895b4", lw=0, zorder=0.5)
            for cn in W.get("canals", []):
                c = np.array(cn["coords"]); ax.plot(c[:, 0], c[:, 1], color="#3f9bb0", lw=0.55, zorder=0.6, alpha=0.9)
            for rv in W.get("rivers", []):
                c = np.array(rv["coords"]); ax.plot(c[:, 0], c[:, 1], color="#136f8a", lw=1.2, zorder=0.7)
        except Exception:
            pass
    if roads:
        try:
            R = json.loads((_DER13 / "roads_major.json").read_text(encoding="utf-8"))
            st = {"motorway": ("#8a5000", 1.5), "trunk": ("#8a5000", 1.3), "primary": ("#6f6256", 1.0), "secondary": ("#8a7f75", 0.7), "tertiary": ("#95897d", 0.5)}
            for rd in R:
                col, lw = st.get(rd["cls"], ("#95897d", 0.5))
                c = np.array(rd["coords"]); ax.plot(c[:, 0], c[:, 1], color=col, lw=lw, zorder=0.8, solid_capstyle="round")
        except Exception:
            pass
    if legend:
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        h = [Patch(facecolor=c, edgecolor="#888", label=l) for c, l in zip(_ELEV_COLORS, _ELEV_LABELS)]
        if water:
            h += [Line2D([0], [0], color="#136f8a", lw=1.5, label="แม่น้ำ"), Line2D([0], [0], color="#3f9bb0", lw=0.8, label="คลอง")]
        if roads:
            h += [Line2D([0], [0], color="#8a5000", lw=1.5, label="ถนนสายหลัก")]
        return h
    return []

# ---------------- ภาพ ----------------
def fig_map():
    cl = json.loads((D7 / "centerline.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"]
    mk = json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]
    x0, x1, y0, y1 = 100.80, 101.12, 13.98, 14.36
    fig, ax = plt.subplots(figsize=(7.2, 7.6))
    base_h = draw_basemap(ax, x0, x1, y0, y1)
    p = ROOT / "data/manual/shp_S1D_20261002_0609/S1D_20261002_0609.shp"
    r = shapefile.Reader(str(p), encoding="latin-1")
    for sr in r.iterShapeRecords():
        g = shape(sr.shape.__geo_interface__)
        minx, miny, maxx, maxy = g.bounds
        if maxx < x0 or minx > x1 or maxy < y0 or miny > y1:
            continue
        for part in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            xs, ys = part.exterior.xy
            ax.fill(xs, ys, color="#1d6fb8", lw=0, alpha=.55, zorder=1)
    ax.plot([c[0] for c in cl], [c[1] for c in cl], color=INK, lw=2.2, zorder=3)
    for f in mk:
        km = f["properties"]["km"]
        lon, lat = f["geometry"]["coordinates"]
        if km == int(km) and int(km) % 10 == 0 and y0 < lat < y1:
            ax.plot(lon, lat, "o", color=INK, ms=4, zorder=4)
            ax.text(lon + .012, lat, f"กม.{int(km)}", fontsize=8, color=INK, zorder=5)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / math.cos(math.radians(14.2)))
    from matplotlib.patches import Patch
    ax.legend(handles=base_h + [Patch(color="#1d6fb8", alpha=.55, label="น้ำท่วม 2 ต.ค. 2569 (ดาวเทียม)")], loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, fontsize=7.5, frameon=True, title="สีพื้น = ความสูงพื้นผิว (ม.) · ถนนและลำน้ำแสดงในกรอบข้อมูลของรายงานน้ำท่วมนครนายก", title_fontsize=7.5)
    ax.set_xlabel("ลองจิจูด"); ax.set_ylabel("ละติจูด")
    ax.set_title("แนวคลองประมาณ (เส้นดำ) กับน้ำท่วมที่ดาวเทียมตรวจพบ 2 ต.ค. 2569 (สีฟ้า)", fontsize=10, color=INK)
    fig.tight_layout()
    path = ASSETS / "goal7_map_flood_line.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_ground():
    pr = DEM["profile_every_10km"]
    km = [p["km"] for p in pr]; z = [p["ground_m"] for p in pr]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.axvspan(NN["km_from"], NN["km_to"], color="#dbe9f6", zorder=0)
    ax.plot(km, z, "-o", color=BLUE, lw=2)
    ax.text((NN["km_from"] + NN["km_to"]) / 2, max(z) * .9, "ช่วงนครนายก", ha="center", color=INK, fontsize=9)
    ax.set_xlabel("ระยะตามแนวคลอง (กม.)"); ax.set_ylabel("ความสูงพื้นดินโดยประมาณ (ม.)")
    ax.set_title("พื้นดินตามแนวคลองลาดลงน้อยมาก (มัธยฐานรอบหมุด กม.)", fontsize=10, color=INK)
    ax.grid(alpha=.3); fig.tight_layout()
    path = ASSETS / "goal7_ground_profile.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_flood_frequency():
    """ร้อยละของแถบ 3 กม. สองข้างแนวคลองที่เคยท่วมอย่างน้อย 1 ปี (GISTDA 2548–2562) รายช่วง 10 กม. + จำนวนปีท่วมเฉลี่ย"""
    fr = C["mitrearth_national"]["gistda_corridor_2005_2019"]["by_10km"]
    labels = [k.replace("-", "–") for k in fr]
    ever = [v["ever_pct"] for v in fr.values()]
    yrs = [v["mean_years"] for v in fr.values()]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ax.bar(range(len(ever)), ever, color=BLUE, alpha=.85, label="เคยท่วมอย่างน้อย 1 ปี (%)")
    ax.set_ylim(0, 105)
    ax.set_xticks(range(len(ever)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("ช่วงตามแนวคลอง (กม.)"); ax.set_ylabel("ร้อยละของแถบที่เคยท่วม")
    ax2 = ax.twinx()
    ax2.plot(range(len(yrs)), yrs, "-o", color="#b45309", lw=2, label="จำนวนปีท่วมเฉลี่ย (จาก 15 ปี)")
    ax2.set_ylim(0, max(yrs) * 1.25); ax2.set_ylabel("ปีท่วมเฉลี่ย")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower center", fontsize=8, ncol=2)
    ax.set_title("แถบสองข้างแนวคลองท่วมบ่อยที่สุดช่วงกลางทุ่ง (GISTDA 2548–2562)", fontsize=10, color=INK)
    ax.grid(alpha=.3, axis="y"); fig.tight_layout()
    path = ASSETS / "goal7_flood_frequency.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_capacity():
    ys = sorted(int(y) for y, v in C2["years"].items() if v["n_days"] >= 200)
    v = [C2["years"][str(y)]["peak_daily_m3s"] for y in ys]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    cols = [ORANGE if y == 2026 else "#4d94c9" for y in ys]
    ax.bar([str(y + 543) for y in ys], v, color=cols)
    for lvl, lab in ((C2["canal_old_reach_m3s"], "ช่วงชัยนาท–ป่าสัก"), (C2["canal_new_reach_m3s"], "ช่วงป่าสัก–อ่าวไทย")):
        ax.axhline(lvl, color=INK, ls="--", lw=1.4)
        ax.text(-0.45, lvl + 30, f"ความจุตามที่รายงาน {fmt(lvl)} · {lab}", fontsize=8.5, color=INK,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=5)
    for i, x in enumerate(v):
        ax.text(i, x + 40, fmt(x), ha="center", fontsize=8.5, color=INK)
    ax.set_ylabel("ปริมาณน้ำสูงสุดรายวัน (ลบ.ม./วินาที)")
    ax.set_title("น้ำผ่านสถานี C.2 นครสวรรค์ เทียบความจุที่รายงานของคลอง", fontsize=10, color=INK)
    fig.tight_layout()
    path = ASSETS / "goal7_capacity_vs_c2.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_area():
    labs = ["ตามตัวแปรออกแบบ\nรายช่วง (220/170/160 ม.)", "ตามภาพแผนที่\n(170 ม. ถึง กม.23 แล้ว 200 ม.)", "200 ม.\nตลอดแนว"]
    vals = [CA["rai"]["design_2569_segments"], CA["rai"]["mixed"], CA["rai"]["all200"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.bar(labs, vals, color="#1d6fb8")
    lo, hi = CA["reported_rai"]["eia_2569_canal"], CA["reported_rai"]["rid_2569_sec2"]
    ax.axhspan(lo, hi, color=ORANGE, alpha=.9, zorder=4)
    ax.text(-0.45, hi + 450, f"ตัวเลขที่รายงาน: {fmt(lo)}–{fmt(hi)} ไร่ (รายงานผลกระทบสิ่งแวดล้อม · เอกสารกรมชลประทาน · ข่าว)", fontsize=9, color=INK,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=6)
    ax.set_ylim(0, hi * 1.25)
    for i, x in enumerate(vals):
        ax.text(i, x / 2, fmt(x), ha="center", color="white", fontsize=10, fontweight="bold")
    ax.set_ylabel("พื้นที่แถบคลอง (ไร่)")
    ax.set_title("พื้นที่แถบคลองตามสมมติฐานความกว้าง เทียบตัวเลขเวนคืน/ก่อสร้างที่รายงาน", fontsize=10, color=INK)
    fig.tight_layout()
    path = ASSETS / "goal7_corridor_area.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_overview():
    """ทั้งเส้น: เส้นกลาง + หมุด กม. + อาคารตัดคลองเดิม สีตามจังหวัด"""
    cl = json.loads((D7 / "centerline.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"]
    mk = json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]
    pts = sorted((f["properties"]["km"], *f["geometry"]["coordinates"]) for f in mk)
    fig, ax = plt.subplots(figsize=(5.6, 8.4))
    _ys = [c[1] for c in cl]
    base_h = draw_basemap(ax, 100.05, 101.15, min(_ys) - 0.03, max(_ys) + 0.03, step=0.002, roads=False, water=False)
    ax.plot([c[0] for c in cl], [c[1] for c in cl], color="#3b4a57", lw=1.2, zorder=1)
    pk = C["provinces_km"]
    cols = {"สระบุรี": "#a14a00", "นครนายก": "#1d6fb8", "ฉะเชิงเทรา": "#1b5e20", "สมุทรปราการ": "#6a1b9a"}
    for prov, (a, b) in pk.items():
        xs = [p[1] for p in pts if a <= p[0] <= b]; ys = [p[2] for p in pts if a <= p[0] <= b]
        if xs:
            ax.plot(xs, ys, "-", color=cols[prov], lw=3.4, label=f"{prov} (กม.{a:.0f}–{b:.0f})", zorder=2)
    for km, lon, lat in pts:
        if km == int(km) and int(km) % 20 == 0:
            ax.plot(lon, lat, "o", color=INK, ms=3.5, zorder=3)
            ax.text(lon + .02, lat, f"กม.{int(km)}", fontsize=8, color=INK)
    ax.set_aspect(1 / math.cos(math.radians(14.2)))
    ax.set_xlim(100.05, 101.15)
    _h, _l = ax.get_legend_handles_labels()
    ax.legend(handles=_h + base_h, loc="lower left", fontsize=7, frameon=True, ncol=1)
    ax.set_xlabel("ลองจิจูด"); ax.set_ylabel("ละติจูด")
    ax.set_title("ทั้งเส้นทาง: ชัยนาท (เหนือ) → อ่าวไทย (ใต้) ตามแผนที่ผู้ใช้สร้าง", fontsize=10, color=INK)
    fig.tight_layout()
    path = ASSETS / "goal7_overview.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_structs():
    bp = ST["by_province"]
    provs = list(bp)
    kinds = sorted({k for v in bp.values() for k in v["kinds"]})
    pal = ["#1d6fb8", "#a14a00", "#1b5e20", "#6a1b9a", "#5a6b7b", "#b3261e", "#00695c", "#7a5c00", "#3949ab", "#c2185b", "#37474f"]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    bottom = np.zeros(len(provs))
    for i, k in enumerate(kinds):
        v = np.array([bp[p]["kinds"].get(k, 0) for p in provs], float)
        ax.bar(provs, v, bottom=bottom, label=k, color=pal[i % len(pal)])
        bottom += v
    for i, tot in enumerate(bottom):
        ax.text(i, tot + .6, f"{int(tot)}", ha="center", fontsize=9, color=INK)
    ax.set_ylabel("จำนวนอาคาร/จุดตัด (จุด)")
    ax.set_title("อาคารและจุดตัดตามแนวคลอง แยกตามจังหวัดและชนิด", fontsize=10, color=INK)
    ax.set_ylim(0, max(bottom) * 1.12)
    ax.legend(fontsize=7.5, ncol=3, frameon=True, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    fig.tight_layout()
    path = ASSETS / "goal7_structs_by_province.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path

# ---------------- เนื้อหา ----------------
yrs = {int(y): v for y, v in C2["years"].items() if v["n_days"] >= 200}
y26 = yrs[2026]
BE26 = 2026 + 543
_rg = [t['range_m'] for t in DEM['ew_transects_range_m']]
RMIN, RMAX = min(_rg), max(_rg)
y_max = max(yrs, key=lambda y: yrs[y]["peak_daily_m3s"])
r_new = C2["canal_new_reach_m3s"] / y26["peak_daily_m3s"]
r_old = C2["canal_old_reach_m3s"] / y26["peak_daily_m3s"]
share_corr = SCENE["on_corridor_100m_rai"]
g40 = next(p["ground_m"] for p in DEM["profile_every_10km"] if p["km"] == 40)
g100 = next(p["ground_m"] for p in DEM["profile_every_10km"] if p["km"] == 100)
tot_flood = SCENE["west_rai"] + SCENE["east_rai"]
amp = SCENE["by_amphoe_rai"]
ong = amp.get("อ.องครักษ์", 0); bn = amp.get("อ.บ้านนา", 0)



def fig_xsection():
    """หน้าตัดคลองลอยตามรายงาน: ท้อง 51 ม. ลึกน้ำ 7 ม. ลาด 1:3 ด้านใน 1:2 ด้านนอก หลังคัน 10 ม. · วาดที่ค่าสูงสุดที่คำนวณจากรายงาน"""
    sec = C["eia_section"]
    EB = C["embankment"]
    z1, z2, road, D = sec["z1"], sec["z2"], sec["road_m"], sec["D_m"]
    b = sec["A_m2"] / D - z1 * D
    FB = EB["assumptions"]["freeboard_m"]
    H = EB["cases"][1]["crest_above_ground_m"]
    Hmax = H
    wl = H - FB
    bed = -(D + FB - H)
    xi_c = b / 2 + z1 * (D + FB)            # ขอบในที่ระดับสันคัน
    xo_c = xi_c + road                       # ขอบนอกของสันคัน
    xo_g = xo_c + z2 * H                     # ปลายลาดนอกที่พื้นเดิม
    xi_g = b / 2 + z1 * (-bed)               # ขอบในที่ระดับพื้นเดิม
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    for s in (1, -1):
        ax.fill([s * xi_g, s * xi_c, s * xo_c, s * xo_g], [0, H, H, 0], color="#c9d3dc", ec=INK, lw=1.2, zorder=2)
    xw = b / 2 + z1 * (wl - bed)
    ax.fill([-b / 2, b / 2, xw, -xw], [bed, bed, wl, wl], color=BLUE, ec=INK, lw=1.0, zorder=3)
    ax.plot([-xo_g - 25, xo_g + 25], [0, 0], color=ORANGE, lw=2.2, zorder=4)
    ax.plot([-xi_g, -b / 2, b / 2, xi_g], [0, bed, bed, 0], color=INK, lw=1.2, zorder=4)
    ax.text(0, (bed + wl) / 2, f"น้ำสูงสุดตามแบบ\nท้อง {b:.0f} ม. · ลึก {D:.0f} ม.", ha="center", va="center", fontsize=10, color="white", fontweight="bold", zorder=6)
    ax.annotate(f"สันคัน (ถนนกว้าง {road:.0f} ม.) สูงเหนือพื้นเดิม {H} ม.\n(ที่ กม.40 ตามรูปตัดตามยาว ราว 3.2–{Hmax} ม. ตลอดช่วงนครนายก)",
                xy=((xi_c + xo_c) / 2, H), xytext=(xo_c - 5, H + 4.2), fontsize=9, color=INK, ha="center",
                arrowprops=dict(arrowstyle="-", color=INK, lw=1), zorder=7)
    ax.annotate(f"ผิวน้ำสูงสุดสูงกว่าพื้นเดิม {wl:.1f} ม.\n(รายงานระบุ {C['eia_levels']['eia_range_water_above_ground_m'][0]}–{C['eia_levels']['eia_range_water_above_ground_m'][1]} ม.)",
                xy=(-xw + 2, wl), xytext=(-xo_g + 5, H + 4.2), fontsize=9, color=INK, ha="center", arrowprops=dict(arrowstyle="-", color=INK, lw=1), zorder=7)
    ax.text(xo_g + 22, -0.5, "พื้นเดิม", fontsize=9.5, color=ORANGE, ha="right", va="top", fontweight="bold")
    ax.text(0, bed - 0.7, f"ท้องคลองต่ำกว่าพื้นเดิม {-bed:.1f} ม.", fontsize=9, color=INK, ha="center", va="top")
    ax.set_xlim(-xo_g - 28, xo_g + 28); ax.set_ylim(bed - 3.0, H + 8.5)
    ax.set_xlabel("ระยะจากกึ่งกลางคลอง (ม.) — ภาพขยายความสูงให้เห็นชัด"); ax.set_ylabel("ความสูงเทียบพื้นเดิม (ม.)")
    ax.set_title("หน้าตัดคลองช่วง กม.23 เป็นต้นไป: ผิวน้ำและสันคันอยู่เหนือพื้นเดิม (คลองลอย)", fontsize=10, color=INK, pad=10)
    ax.grid(alpha=.25); fig.tight_layout()
    path = ASSETS / "goal7_xsection.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_sip_flow():
    ES = C["eia_structs"]["nn"]["crossings"]
    labs = [f"กม.{c['km']:.1f} {c['name']}" for c in ES]
    q_in = [c["q_in"] for c in ES]
    q_st = [c["q_struct"] for c in ES]
    y = np.arange(len(ES))
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.barh(y - 0.2, q_in, 0.38, color=BLUE, label="อัตราไหลของคลองเดิมตามตาราง")
    ax.barh(y + 0.2, q_st, 0.38, color=ORANGE, label="อาคารเชื่อมรับได้")
    for i, c in enumerate(ES):
        ax.text(c["q_in"] + 0.6, i - 0.2, f"{c['q_in']:.0f}", va="center", fontsize=8.5, color=INK)
        ax.text(c["q_struct"] + 0.6, i + 0.2, f"{c['q_struct']:.0f}" + (f"  ({c['ratio']*100:.0f}%)" if c["shortfall"] else ""), va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8.8)
    ax.invert_yaxis()
    ax.set_xlabel("อัตราไหล (ลบ.ม./วินาที)")
    ax.set_title("ช่วงนครนายก: อัตราไหลของคลองเดิมที่คลองใหม่ตัดผ่าน เทียบกับที่อาคารเชื่อมรับได้ (ตาราง 2.3.2-3)", fontsize=10, color=INK)
    ax.legend(loc="lower right", fontsize=8.5, frameon=True)
    ax.grid(axis="x", alpha=.3); fig.tight_layout()
    path = ASSETS / "goal7_siphon_vs_flood.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_wc_map():
    """ผังน้ำ/น้ำท่วมรอบ 100 ปีของ สทนช. ซ้อนแนวคลอง ช่วงนครนายก พร้อมจุดตัดคลองเดิม (แดง = อาคารรับได้น้อยกว่าน้ำหลากมาก)"""
    gj = json.loads((ROOT / "analysis/goal7/waterchart_clip.geojson").read_text(encoding="utf-8"))
    cl = json.loads((D7 / "centerline.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"]
    mk = sorted(((f["properties"]["km"], f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1])
                 for f in json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]))
    kmv = [m[0] for m in mk]
    lonv = [m[1] for m in mk]
    latv = [m[2] for m in mk]
    fig, ax = plt.subplots(figsize=(7.2, 8.4))
    _nn = ST["nakhonnayok"]
    _seg = [(lo, la) for k, lo, la in mk if _nn["km_from"] <= k <= _nn["km_to"]]
    _lo0 = min(t[0] for t in _seg) - .055; _lo1 = max(t[0] for t in _seg) + .055
    _la0 = min(t[1] for t in _seg) - .03; _la1 = max(t[1] for t in _seg) + .03
    base_h = draw_basemap(ax, _lo0, _lo1, _la0, _la1)
    names = {"Flood_Tr100": ("#4d94c9", "น้ำท่วมรอบ 100 ปี (ผังน้ำ สทนช.)"), "Floodway": ("#c76f10", "พื้นที่ทางน้ำหลาก (ผังน้ำ สทนช.)")}
    for key in ("Flood_Tr100", "Floodway"):
        for f in gj["features"]:
            if f["properties"]["layer"] != key:
                continue
            g = shape(f["geometry"])
            for part in (g.geoms if g.geom_type in ("MultiPolygon", "GeometryCollection") else [g]):
                if part.geom_type != "Polygon":
                    continue
                xs, ys = part.exterior.xy
                ax.fill(xs, ys, color=names[key][0], lw=0, alpha=.55 if key == "Flood_Tr100" else .75, zorder=1 if key == "Flood_Tr100" else 2)
    ax.plot([c[0] for c in cl], [c[1] for c in cl], color=INK, lw=2.4, zorder=4)
    # ช่วงนครนายก เส้นหนา
    nn = ST["nakhonnayok"]
    seg = [(lo, la) for k, lo, la in mk if nn["km_from"] <= k <= nn["km_to"]]
    for km in range(40, 75, 5):
        lo = float(np.interp(km, kmv, lonv)); la = float(np.interp(km, kmv, latv))
        ax.plot(lo, la, "o", color=INK, ms=4, zorder=5)
        ax.text(lo + .010, la, f"กม.{km}", fontsize=8.5, color=INK, zorder=6,
                bbox=dict(facecolor="white", edgecolor="none", pad=0.8, alpha=.85))
    for c in C["eia_structs"]["nn"]["crossings"]:
        lo = float(np.interp(c["km"], kmv, lonv)); la = float(np.interp(c["km"], kmv, latv))
        ax.plot(lo, la, "v", ms=12 if c["shortfall"] else 6.5, color="#8b0000" if c["shortfall"] else INK, mec="white", mew=0.8, zorder=7)
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    ax.legend(handles=base_h + [Patch(color="#4d94c9", alpha=.55, label=names["Flood_Tr100"][1]), Patch(color="#c76f10", label=names["Floodway"][1]),
                       Line2D([0], [0], color=INK, lw=2.4, label="แนวคลองประมาณ"),
                       Line2D([0], [0], marker="v", color="w", mfc="#8b0000", ms=9, label="คลองเดิมที่อาคารเชื่อมรับได้น้อยกว่า 1 ใน 4 ของอัตราไหลตามตาราง"),
                       Line2D([0], [0], marker="v", color="w", mfc=INK, ms=7, label="คลองเดิมที่ตัดผ่านจุดอื่น")],
              loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=3, fontsize=7.6, frameon=True)
    lo0 = min(s[0] for s in seg); lo1 = max(s[0] for s in seg); la0 = min(s[1] for s in seg); la1 = max(s[1] for s in seg)
    ax.set_xlim(lo0 - .055, lo1 + .055); ax.set_ylim(la0 - .03, la1 + .03)
    ax.set_aspect(1 / math.cos(math.radians(14.2)))
    ax.ticklabel_format(useOffset=False, style="plain")
    ax.set_xlabel("ลองจิจูด"); ax.set_ylabel("ละติจูด")
    ax.set_title("ผังน้ำของ สทนช. ซ้อนแนวคลอง ช่วงนครนายก พร้อมจุดที่คลองเดิมถูกตัด", fontsize=10, color=INK)
    fig.tight_layout()
    path = ASSETS / "goal7_waterchart_map.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_versions():
    rs = C["eia_versions"]["rounds"]
    labs = ["ส่ง พ.ย. 2561", "ชี้แจงครั้ง 1\nก.ย. 2564", "ชี้แจงครั้ง 2\nธ.ค. 2566", "ฉบับที่เห็นชอบ\n(2569)"]
    bc = [r["econ"]["bc12"] for r in rs]
    land = [r["land_rai"] for r in rs]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.4, 3.6))
    cols = [BLUE, BLUE, BLUE, ORANGE]
    a1.bar(labs, bc, color=cols)
    a1.axhline(1.0, color=INK, ls="--", lw=1.3)
    a1.text(3.45, 1.04, "คุ้มทุนพอดี = 1.0", fontsize=8.5, color=INK, ha="right", bbox=dict(facecolor="white", edgecolor="none", pad=1.2), zorder=6)
    for i, v in enumerate(bc):
        a1.text(i, v / 2, f"{v:.2f}", ha="center", va="center", fontsize=11, color="white", fontweight="bold", zorder=7)
    a1.set_ylim(0, max(bc) * 1.25)
    a1.set_title("ผลตอบแทนต่อต้นทุน ที่อัตราคิดลด 12%", fontsize=9.5, color=INK)
    a1.tick_params(axis="x", labelsize=7.8)
    a2.bar(labs, land, color=cols)
    for i, v in enumerate(land):
        a2.text(i, v / 2, f"{v:,}", ha="center", va="center", fontsize=10, color="white", fontweight="bold")
    a2.set_ylim(0, max(land) * 1.18)
    a2.set_title("ที่ดินที่ต้องเวนคืน (ไร่)", fontsize=9.5, color=INK)
    a2.tick_params(axis="x", labelsize=7.8)
    fig.suptitle("รายงานผลกระทบสิ่งแวดล้อมถูกส่งกลับแก้ 3 รอบ — ตัวเลขเปลี่ยนอย่างไร", fontsize=10, color=INK)
    fig.tight_layout()
    path = ASSETS / "goal7_eia_versions.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_profile():
    """รูปตัดตามยาววาดใหม่จากรูปที่ 2.3.2-9 (ค่าที่อ่านจากรูป ±0.2 ม.) — ไม่คัดลอกรูปต้นฉบับ"""
    PF = C["eia_profile"]
    gx = [g[0] for g in PF["ground_readings"]]
    gz = [g[1] for g in PF["ground_readings"]]
    kms = np.arange(0, 135.9, 0.5)
    bed, water, crest = [], [], []
    for km in kms:
        if km < 23:
            b = 1.75 - (km - 0.15) * 0.1
            w = b + 7.0
            cst = w + 1.5
        else:
            b = -1.05 - (km - 23) * 0.04
            w = b + 7.0
            cst = w + 1.5 if km <= 109 else 4.0
        bed.append(b); water.append(w); crest.append(cst)
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.axvspan(NN["km_from"], NN["km_to"], color="#dbe9f6", zorder=0)
    ax.plot(gx, gz, color=ORANGE, lw=2.2, label="พื้นดินเดิม (อ่านจากรูป)", zorder=3)
    ax.plot(kms, crest, color=INK, lw=2, label="สันคัน", zorder=3)
    ax.plot(kms, water, color=BLUE, lw=2, label="ระดับน้ำสูงสุดออกแบบ", zorder=3)
    ax.plot(kms, bed, color=GREY, lw=1.8, ls="--", label="ท้องคลอง", zorder=3)
    for gk in (23, 74, 102):
        ax.axvline(gk, color=GREY, lw=0.9, ls=":", zorder=1)
        ax.text(gk, 12.9, f"ประตูระบายน้ำ กม.{gk}", va="top", ha="center", fontsize=8, color=INK, bbox=dict(facecolor="white", edgecolor="none", pad=1))
    ax.text((NN["km_from"] + NN["km_to"]) / 2, 9.6, "ช่วงนครนายก", ha="center", fontsize=9, color=INK)
    ax.set_xlim(0, 136); ax.set_ylim(-7.5, 13)
    ax.set_xlabel("ระยะตามแนวคลอง (กม. นับจากฝั่งป่าสัก)"); ax.set_ylabel("ระดับ (ม.รทก.)")
    ax.set_title("รูปตัดตามยาวของคลอง (วาดใหม่จากรูปที่ 2.3.2-9 ของรายงานฯ): ผิวน้ำและสันคันอยู่เหนือพื้นเดิมตั้งแต่ กม.23", fontsize=9.5, color=INK)
    ax.legend(loc="lower left", fontsize=8.3, frameon=True, ncol=2)
    ax.grid(alpha=.3); fig.tight_layout()
    path = ASSETS / "goal7_profile.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_basins():
    B = C["basins_2569"]["rows"]
    col = {"floodway": "#1d6fb8", "connect": "#1d6fb8", "pump": "#5a6b7b", "siphon": "#a14a00"}
    labs = [f"พื้นที่ {b['id']} · {b['canal']}" for b in B]
    y = np.arange(len(B))
    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    ax.barh(y - 0.2, [b["q10"] for b in B], 0.38, color="#4d94c9", label="น้ำหลากรอบ 10 ปี (ฝนสูงสุด 5 วัน)")
    ax.barh(y + 0.2, [b["out_q"] for b in B], 0.38, color=ORANGE, label="อาคารระบาย/สูบที่ระบุ")
    for i, b in enumerate(B):
        ax.text(max(b["q10"], b["out_q"]) + 4, i, f"{b['cap_ratio']*100:.0f}%", va="center", fontsize=8.3, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8.2)
    ax.invert_yaxis()
    ax.set_xlabel("อัตราไหล (ลบ.ม./วินาที) · ตัวเลขท้ายแท่ง = อาคารระบาย ÷ น้ำหลาก")
    ax.set_title("พื้นที่รับน้ำย่อย 17 พื้นที่ ตามตาราง 2.3.2-1: น้ำหลากเทียบความสามารถระบาย/สูบ", fontsize=10, color=INK)
    ax.legend(loc="lower right", fontsize=8.5, frameon=True)
    ax.grid(axis="x", alpha=.3); fig.tight_layout()
    path = ASSETS / "goal7_basins.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_options():
    O = C["options"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.8))
    w = O["wide_canal"]
    a1.bar([f"สันคันสูง\n{x['crest_above_ground_m']} ม." for x in w], [x["land_vs_now_pct"] for x in w], color=BLUE)
    for i, x in enumerate(w):
        a1.text(i, x["land_vs_now_pct"] + 9, f"+{x['land_vs_now_pct']}%", ha="center", fontsize=10.5, color=INK, fontweight="bold")
        a1.text(i, x["land_vs_now_pct"] + 2, f"ท้อง {x['bottom_m']} ม.", ha="center", fontsize=8.3, color=INK)
    a1.set_ylim(0, max(x["land_vs_now_pct"] for x in w) * 1.3 + 5)
    a1.set_title("ทำคลองกว้างขึ้นเพื่อให้คันต่ำลง:\nที่ดินที่ใช้เพิ่มขึ้นเท่าใด", fontsize=9.5, color=INK)
    a1.set_ylabel("ที่ดินแถบคลองเพิ่มจากแบบปัจจุบัน (%)")
    a1.tick_params(axis="x", labelsize=8)
    o = O["outlet_pump"]
    a2.bar([f"ลดระดับน้ำ\n{x['lower_m']:.0f} ม." for x in o], [x["power_mw"] for x in o], color=ORANGE)
    for i, x in enumerate(o):
        a2.text(i, x["power_mw"] / 2, f"{x['power_mw']:.0f}", ha="center", color="white", fontsize=11, fontweight="bold")
        a2.text(i, x["power_mw"] + 0.6, f"คันที่ กม.40 = {x['crest_above_ground_km40_m']} ม.", ha="center", fontsize=8, color=INK)
    a2.set_ylim(0, max(x["power_mw"] for x in o) * 1.25)
    a2.set_title("ติดเครื่องสูบน้ำที่ปลายคลองผลักดันน้ำ 600 ลบ.ม./วินาที:\nกำลังไฟฟ้าที่ต้องใช้", fontsize=9.5, color=INK)
    a2.set_ylabel("เมกะวัตต์")
    a2.tick_params(axis="x", labelsize=8)
    fig.tight_layout()
    path = ASSETS / "goal7_options.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path




TEAL, PURPLE = "#0b6f6a", "#7a3b8f"


def fig_tide():
    """รูปตัดตามยาว + เส้นน้ำเท้อ/น้ำทะเลหนุนสูงสุด (คำนวณเอง จากหน้าตัดตามรายงาน)"""
    T = C["new_cases"]["tide"]
    PF = C["eia_profile"]
    gx = [g[0] for g in PF["ground_readings"]]
    gz = [g[1] for g in PF["ground_readings"]]
    kms = np.arange(23, 134.01, 1.0)
    bed = [-1.05 - (k - 23) * 0.04 for k in kms]
    crest = [(b + 7.0 + 1.5) if k <= 109 else 4.0 for k, b in zip(kms, bed)]
    water = [b + 7.0 for b in bed]
    cs = T["cases"]
    ks = sorted(int(k) for k in cs[1]["surface_msl"])
    fig, ax = plt.subplots(figsize=(7.8, 4.9))
    ax.axvspan(NN["km_from"], NN["km_to"], color="#dbe9f6", zorder=0)
    ax.plot(gx, gz, color=ORANGE, lw=2.2, label="พื้นดินเดิม", zorder=3)
    ax.plot(kms, crest, color=INK, lw=2, label="สันคัน", zorder=3)
    ax.plot(kms, water, color=BLUE, lw=2, label="ระดับน้ำสูงสุดตามแบบ (ปลายคลอง +1.5)", zorder=3)
    ax.plot(ks, [cs[1]["surface_msl"][str(k)] for k in ks], color=PURPLE, lw=2.2, label="น้ำเท้อ: อัดน้ำหลังประตู +2.5 · น้ำหลาก 600", zorder=4)
    ax.plot(ks, [cs[2]["surface_msl"][str(k)] for k in ks], color=TEAL, lw=2.2, ls="--", label="น้ำเท้อ: ผันน้ำน้อย 100 · ทะเลหนุน +2.49", zorder=4)
    ax.plot(kms, bed, color=GREY, lw=1.6, ls="--", label="ท้องคลอง", zorder=3)
    OF = T["official_fig"]
    ax.plot([p[0] for p in OF["points_max"]], [p[1] for p in OF["points_max"]], "s", color=INK, mfc="white", ms=7, zorder=6,
            label="รูปที่ 2.5.1-4 ของรายงานฯ: ทะเลขึ้นสูงสุด (อ่านจากรูป)")
    ax.plot([p[0] for p in OF["points_min"]], [p[1] for p in OF["points_min"]], "D", color=INK, mfc="white", ms=6, zorder=6,
            label="รูปที่ 2.5.1-4 ของรายงานฯ: ทะเลลงต่ำสุด (อ่านจากรูป)")
    ax.axhline(T["y2554_max_m"], color=PURPLE, lw=1.0, ls=":", zorder=2)
    ax.text(133, -0.2, f"เส้นประม่วง = น้ำทะเลหนุนสูงสุดที่ใช้ทดสอบ +{T['y2554_max_m']} ม.รทก. (ปี 2554)", fontsize=8.3, color=PURPLE, ha="right", bbox=dict(facecolor="white", edgecolor="none", pad=1))
    ax.axhline(T["y2554_min_m"], color=GREY, lw=0.9, ls=":", zorder=2)
    ax.text(133, T["y2554_min_m"] - 0.7, f"เส้นจุดเทา = น้ำทะเลลงต่ำสุด {T['y2554_min_m']} ม.รทก.", fontsize=8.3, color=GREY, ha="right", bbox=dict(facecolor="white", edgecolor="none", pad=1))
    for gk, lab in ((74, "ประตู\nกม.74"), (102, "ประตู\nกม.102"), (134, "ประตู\nปลายคลอง")):
        ax.axvline(gk, color=GREY, lw=0.9, ls=":", zorder=1)
        ax.text(gk, 9.4, lab, ha="right" if gk == 134 else "center", va="top", fontsize=8, color=INK, bbox=dict(facecolor="white", edgecolor="none", pad=1))
    ax.set_xlim(23, 136); ax.set_ylim(-7, 9.6)
    ax.set_xlabel("ระยะตามแนวคลอง (กม.)"); ax.set_ylabel("ระดับ (ม.รทก.)")
    ax.set_title("เส้นน้ำเท้อเมื่อน้ำทะเลหนุน: ที่ปลายคลองน้ำทะเลสูงกว่าพื้นดินเดิม 1–2 ม.", fontsize=10, color=INK)
    ax.legend(loc="lower left", fontsize=7.6, frameon=True)
    ax.grid(alpha=.3); fig.tight_layout()
    path = ASSETS / "goal7_tide.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_xsection_true():
    """หน้าตัดคลองมาตราส่วนจริง 1:1 (แกนนอน=แกนตั้ง) เทียบแบบตามรายงาน กับกรณีขุดลึกให้คันต่ำ"""
    sec = C["eia_section"]
    DC = C["new_cases"]["deep_cut"]
    z1, z2, road, D = sec["z1"], sec["z2"], sec["road_m"], sec["D_m"]
    b = sec["A_m2"] / D - z1 * D
    fig, axs = plt.subplots(2, 1, figsize=(7.8, 3.9), sharex=True)

    def panel(ax, H, wl, bed, title):
        xi_c = b / 2 + z1 * (H - bed)
        xo_c = xi_c + road
        xo_g = xo_c + z2 * H
        xi_g = b / 2 + z1 * (-bed)
        for s in (1, -1):
            ax.fill([s * xi_g, s * xi_c, s * xo_c, s * xo_g], [0, H, H, 0], color="#c9d3dc", ec=INK, lw=1.0, zorder=2)
        xw = b / 2 + z1 * (wl - bed)
        ax.fill_between([-110, 110], [-14, -14], [0, 0], color="#efe7d8", zorder=0)
        ax.fill([-b / 2, b / 2, xi_g, -xi_g], [bed, bed, 0, 0], color="#efe7d8", ec=INK, lw=0.9, zorder=2.5)
        ax.fill([-b / 2, b / 2, xw, -xw], [bed, bed, wl, wl], color=BLUE, ec=INK, lw=0.9, zorder=3)
        ax.plot([-110, 110], [0, 0], color=ORANGE, lw=2.0, zorder=4)
        hx = 82
        ax.add_patch(plt.Rectangle((hx, 0), 8, 7, fc="#ffffff", ec=INK, lw=1.0, zorder=5))
        ax.text(hx + 4, 3.5, "บ้าน\n2 ชั้น", ha="center", va="center", fontsize=7, color=INK, zorder=6)
        ax.add_patch(plt.Rectangle((hx + 11, 0), 0.6, 1.7, fc=INK, ec=INK, zorder=5))
        ax.text(hx + 11.3, 2.2, "คน", ha="left", fontsize=7, color=INK)
        ax.text(0, (bed + wl) / 2, f"น้ำลึก {wl - bed:.1f} ม.\nท้องกว้าง {b:.0f} ม.", ha="center", va="center", fontsize=8.5, color="white", fontweight="bold", zorder=6)
        ax.text(-108, 10.5, f"สันคันสูงเหนือพื้นเดิม {H:.1f} ม.", fontsize=8.5, color=INK, va="top")
        ax.text(-108, -0.6, "พื้นเดิม", fontsize=8.5, color=ORANGE, ha="left", va="top", fontweight="bold")
        ax.set_aspect("equal"); ax.set_ylim(-14, 11)
        ax.set_title(title, fontsize=8.2, color=INK, loc="left")
        ax.set_ylabel("ความสูง (ม.)"); ax.grid(alpha=.25)
        return 2 * xo_g

    t1 = 2 * (b / 2 + z1 * (4.8 + D - 3.3) + road + z2 * 4.8)
    panel(axs[0], 4.8, 3.3, -(D - 3.3), f"ก) ตามแบบในรายงาน (คลองลอย ที่ กม.40): น้ำสูงกว่าพื้น 3.3 ม. · กว้างรวมคันสองฝั่งราว {t1:.0f} ม.")
    t2 = 2 * (b / 2 + z1 * (DC["depth_m"] + 1.5) + road + z2 * 1.5)
    panel(axs[1], 1.5, 0.0, -DC["depth_m"], f"ข) กรณีขุดลึก: ผิวน้ำเสมอพื้นเดิม · คันสูง 1.5 ม. · กว้างรวมราว {t2:.0f} ม. · ดินขุดเพิ่มราว {DC['extra_spoil_mcm_km23_134']} ล้าน ลบ.ม.")
    axs[1].set_xlabel("ระยะจากกึ่งกลางคลอง (ม.) — แกนนอนกับแกนตั้งมาตราส่วนเดียวกัน (สัดส่วนจริง)")
    axs[0].set_xlim(-110, 110)
    fig.tight_layout()
    path = ASSETS / "goal7_xsection_true.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_energy():
    H = C["new_cases"]["hydro"]
    _dk = sorted(H["days_scenarios"], key=int)
    d60 = H["days_scenarios"][_dk[1]]
    mid_d = _dk[1]
    labs = ["แผงเซลล์แสงอาทิตย์ลอยน้ำ\n(ปกคลุม 20% ผิวน้ำ)", "แผงเซลล์แสงอาทิตย์ลอยน้ำ\n(ปกคลุม 10%)",
            f"กังหันที่ประตูปลายคลอง\n(ปีเฉลี่ย ผันเทียบเท่า {mid_d} วัน)", f"กังหันกลางน้ำ 55 สถานี\n({mid_d} วัน · ครอบ 20%)"]
    vals = [H["pv_gwh_per_year"][1], H["pv_gwh_per_year"][0], d60["gate_gwh"], d60["kinetic_gwh"][1]]
    cols = [ORANGE, ORANGE, BLUE, BLUE]
    fig, ax = plt.subplots(figsize=(7.6, 3.5))
    y = np.arange(len(vals))
    ax.barh(y, vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(v + 6, i, f"{v:,.1f} กิกะวัตต์-ชั่วโมง/ปี", va="center", fontsize=9, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8.8); ax.invert_yaxis()
    ax.set_xlim(0, max(vals) * 1.5); ax.set_xlabel("พลังงานไฟฟ้าต่อปี (กิกะวัตต์-ชั่วโมง)")
    ax.set_title("ไฟฟ้าจากน้ำไหลในคลอง เทียบกับแผงเซลล์แสงอาทิตย์ลอยน้ำ (ค่าคัดกรอง)", fontsize=10, color=INK)
    ax.grid(axis="x", alpha=.3); fig.tight_layout()
    path = ASSETS / "goal7_energy.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


def fig_land_dev():
    LD = C["new_cases"]["land_dev"]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    cols = ["#6c8fb5", BLUE, "#0f3f6e"]
    x = np.arange(3)
    for j, p in enumerate((1.0, 3.0, 5.0)):
        v = [next(s["cover_loan_pct"] for s in LD["scenarios"] if s["strip_m_each_side"] == w and s["net_mb_per_rai"] == p) for w in (100, 200, 300)]
        ax.bar(x + (j - 1) * 0.26, v, 0.26, color=cols[j], label=f"รายได้สุทธิ {p:g} ล้านบาท/ไร่")
        for xi, vv in zip(x, v):
            ax.text(xi + (j - 1) * 0.26, vv + 4, f"{vv}%", ha="center", fontsize=8.5, color=INK)
    ax.axhline(100, color=ORANGE, lw=1.8, ls="--")
    ax.text(2.45, 106, "ครอบคลุมเงินกู้พอดี", ha="right", fontsize=8.5, color=ORANGE)
    ax.set_xticks(x)
    ax.set_xticklabels([f"พัฒนาข้างละ {w} ม.\n({LD['scenarios'][i * 3]['rai']:,} ไร่)" for i, w in enumerate((100, 200, 300))], fontsize=9)
    ax.set_ylabel("สัดส่วนที่ครอบคลุมเงินกู้ (%)")
    ax.set_ylim(0, 290)
    ax.set_title("ขายพัฒนาที่ดินริมคลอง: ได้เงินเท่าไรเมื่อเทียบกับเงินกู้ในแผน", fontsize=10, color=INK)
    ax.legend(loc="upper left", fontsize=8.5); ax.grid(axis="y", alpha=.3); fig.tight_layout()
    path = ASSETS / "goal7_land_dev.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path


# ---- คำไทยเข้าใจง่ายแทนคำทับศัพท์/ศัพท์เทคนิค (ข้อตกลงภาษารายงาน 16 ต.ค. 69 — รายงาน 7 และ 8) ----
# เรียงจากยาวไปสั้น (กันคำสั้นกลืนคำยาว/คำประสม) · ใช้ตอนท้ายสร้าง HTML เท่านั้น ไม่แก้ข้อมูล
PLAIN_TH = [
    ("ท่อ/ไซฟอนที่ลอดใต้คลอง", "ท่อลอดใต้คลอง"),
    ("ท่อระบายน้ำและไซฟอน", "ท่อระบายน้ำและท่อลอด"),
    ("ปั๊มผลักดันน้ำ", "เครื่องสูบผลักดันน้ำ"),
    ("ไซฟอนลอดคลอง", "ท่อลอดคลอง"),
    ("โซลาร์ลอยน้ำ", "แผงเซลล์แสงอาทิตย์ลอยน้ำ"),
    ("ระบบโทรมาตร", "ระบบวัดและส่งข้อมูลระยะไกล"),
    ("ทางชลศาสตร์", "ด้านการไหลของน้ำ"),
    ("โซลาร์เซลล์", "แผงเซลล์แสงอาทิตย์"),
    ("ชั้นข้อมูล", "ชุดข้อมูล"),
    ("ชลศาสตร์", "การไหลของน้ำ"),
    ("โปรเจกต์", "งานวิเคราะห์"),
    ("สคริปต์", "โปรแกรมคำนวณ"),
    ("ออนไลน์", "บนอินเทอร์เน็ต"),
    ("โทรมาตร", "ระบบวัดและส่งข้อมูลระยะไกล"),
    ("p10–p90", "ช่วงกลางร้อยละ 80"),
    ("โซลาร์", "พลังงานแสงอาทิตย์"),
    ("ไซฟอน", "ท่อลอด"),
    ("ลิงก์", "ที่อยู่เว็บ"),
    ("ไฟล์", "แฟ้ม"),
    ("ปั๊ม", "เครื่องสูบน้ำ"),
    ("ปตร.", "ประตูระบายน้ำ"),
    ("โซน", "เขต"),
]


def plain(html: str) -> str:
    """แทนคำทับศัพท์ด้วยคำไทย + อธิบายคำใหม่ตอนใช้ครั้งแรก (ท่อลอด · ม.รทก.)
    เรียงแทนที่คำยาวก่อนสั้น และไม่แตะแท็ก HTML / code / style / script
    """
    body_start = html.find("<body")
    if body_start == -1:
        head, body = "", html
    else:
        head, body = html[:body_start], html[body_start:]

    import re as _re
    from goal6_reportlib import _text_segments

    rules = sorted(PLAIN_TH, key=lambda pair: len(pair[0]), reverse=True)

    out = []
    for is_text, chunk in _text_segments(body):
        if not is_text or "base64," in chunk:
            out.append(chunk)
            continue
        c = chunk
        for a, b in rules:
            c = c.replace(a, b)
        out.append(c)
    body = "".join(out)

    body = _re.sub(r'(?<!และ)(?<!")ท่อลอด', "ท่อลอด (ท่อให้น้ำของคลองเดิมไหลลอดใต้คลองใหญ่ไปอีกฝั่ง)", body, count=1)
    body = body.replace("ม.รทก.", "ม.รทก. (เมตรเหนือระดับน้ำทะเลปานกลาง)", 1)
    return head + body


# ---- ทะเบียนช่องว่างความรู้ (analysis/goal7/gaps.json) — ตัวป้องกันข้อความล้าสมัย ----
_GAPS = json.loads((ROOT / "analysis/goal7/gaps.json").read_text(encoding="utf-8"))
_TH_MON = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
_y, _m, _d = (int(x) for x in _GAPS["as_of"].split("-"))
GAP_FOOT = (f" · ข้อมูลล่าสุด {_d} {_TH_MON[_m - 1]} {_y + 543} · ช่องว่างความรู้ที่ยังเปิดอยู่ "
            f"{sum(1 for g in _GAPS['gaps'] if g['status'] == 'open')} ข้อ")
