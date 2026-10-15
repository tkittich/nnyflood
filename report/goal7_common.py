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
    fig, ax = plt.subplots(figsize=(7.2, 7.8))
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
                ax.fill(xs, ys, color=names[key][0], lw=0, zorder=1 if key == "Flood_Tr100" else 2)
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
    ax.legend(handles=[Patch(color="#4d94c9", label=names["Flood_Tr100"][1]), Patch(color="#c76f10", label=names["Floodway"][1]),
                       Line2D([0], [0], color=INK, lw=2.4, label="แนวคลองประมาณ"),
                       Line2D([0], [0], marker="v", color="w", mfc="#8b0000", ms=9, label="คลองเดิมที่อาคารเชื่อมรับได้น้อยกว่า 1 ใน 4 ของอัตราไหลตามตาราง"),
                       Line2D([0], [0], marker="v", color="w", mfc=INK, ms=7, label="คลองเดิมที่ตัดผ่านจุดอื่น")],
              loc="upper center", bbox_to_anchor=(0.5, -0.09), fontsize=8.3, frameon=True)
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
        ax.text(gk, 12.9, f"ปตร. กม.{gk}", va="top", ha="center", fontsize=8, color=INK, bbox=dict(facecolor="white", edgecolor="none", pad=1))
    ax.text((NN["km_from"] + NN["km_to"]) / 2, 9.6, "ช่วงนครนายก", ha="center", fontsize=9, color=INK)
    ax.set_xlim(0, 136); ax.set_ylim(-7.5, 13)
    ax.set_xlabel("ระยะตามแนวคลอง (กม. นับจากฝั่งป่าสัก)"); ax.set_ylabel("ระดับ (ม.รทก.)")
    ax.set_title("รูปตัดตามยาวของคลอง (วาดใหม่จากรูปที่ 2.3.2-9 ของรายงานฯ): ผิวน้ำและสันคันอยู่เหนือพื้นเดิมตั้งแต่ กม.23", fontsize=9.5, color=INK)
    ax.legend(loc="lower left", fontsize=8.3, frameon=True, ncol=2)
    ax.grid(alpha=.3); fig.tight_layout()
    path = ASSETS / "goal7_profile.png"
    fig.savefig(path, dpi=130); plt.close(fig)
    return path
