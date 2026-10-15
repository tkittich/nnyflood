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


# ---------------- ภาพ ----------------
def fig_map():
    cl = json.loads((D7 / "centerline.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"]
    mk = json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]
    x0, x1, y0, y1 = 100.80, 101.12, 13.98, 14.36
    fig, ax = plt.subplots(figsize=(7.2, 7.6))
    p = ROOT / "data/manual/shp_S1D_20261002_0609/S1D_20261002_0609.shp"
    r = shapefile.Reader(str(p), encoding="latin-1")
    for sr in r.iterShapeRecords():
        g = shape(sr.shape.__geo_interface__)
        minx, miny, maxx, maxy = g.bounds
        if maxx < x0 or minx > x1 or maxy < y0 or miny > y1:
            continue
        for part in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            xs, ys = part.exterior.xy
            ax.fill(xs, ys, color="#4d94c9", lw=0, alpha=.9, zorder=1)
    ax.plot([c[0] for c in cl], [c[1] for c in cl], color=INK, lw=2.2, zorder=3)
    for f in mk:
        km = f["properties"]["km"]
        lon, lat = f["geometry"]["coordinates"]
        if km == int(km) and int(km) % 10 == 0 and y0 < lat < y1:
            ax.plot(lon, lat, "o", color=INK, ms=4, zorder=4)
            ax.text(lon + .012, lat, f"กม.{int(km)}", fontsize=8, color=INK, zorder=5)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / math.cos(math.radians(14.2)))
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
    ax.bar(labs, vals, color="#4d94c9")
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
    ax.plot([c[0] for c in cl], [c[1] for c in cl], color="#8aa0b3", lw=1.2, zorder=1)
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
    ax.legend(loc="upper left", fontsize=8, frameon=True)
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

