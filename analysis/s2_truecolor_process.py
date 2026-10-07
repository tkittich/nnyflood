# Sentinel-2 L2A true color 3 วัน (27 ก.ย. / 29 ก.ย. / 2 ต.ค. 69) → เฟรมในกริดเดียวกับแผนที่รายงาน
# วิธี: อ่าน B04/B03/B02 (10 ม.) + SCL (20 ม. วัดเมฆ) ตัดกรอบจังหวัด (grid เดียวกับ S1) + ปรับความสว่าง
# ผู้จัดทำ: AI — Contains modified Copernicus Sentinel data (2026)/ESA
import glob, json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from rasterio.warp import reproject, Resampling as WarpRes
from rasterio.transform import from_origin
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]
ROOT = Path(__file__).resolve().parent.parent
S2D = ROOT / "data" / "18_sentinel2_copernicus"
DER = ROOT / "data" / "13_sentinel1_copernicus" / "derived"
OUT = ROOT / "report" / "assets"
gr = json.load(open(DER / "grid.json", encoding="utf-8"))
prov = np.load(DER / "mask_province.npy")

SCENES = [
    ("2026-09-27 10:35", "S2C_MSIL2A_20260927T033541", "27 ก.ย. 2569 10:35 น. (Sentinel-2 สีจริง 10 ม.)"),
    ("2026-09-29 10:41", "S2A_MSIL2A_20260929T034201", "29 ก.ย. 2569 10:41 น. (Sentinel-2 สีจริง 10 ม.)"),
    ("2026-10-02 10:35", "S2B_MSIL2A_20261002T033549", "2 ต.ค. 2569 10:35 น. (Sentinel-2 สีจริง 10 ม.)"),
]
W = 1400
H = int(W * (gr["y1"] - gr["y0"]) / (gr["x1"] - gr["x0"]) / (110.96 / (111.32 * np.cos(np.radians(14.24)))))
results = {}
for key, prefix, title in SCENES:
    b = {}
    for band in ("B04", "B03", "B02"):
        f = glob.glob(f"{S2D}/{prefix}*/GRANULE/*/IMG_DATA/**/T47PQR_*_{band}_*.jp2", recursive=True)[0]
        dst = np.zeros((H, W), np.float32)
        dst_tr = from_origin(gr["x0"], gr["y1"], (gr["x1"]-gr["x0"])/W, (gr["y1"]-gr["y0"])/H)
        with rasterio.open(f) as src:
            reproject(rasterio.band(src, 1), dst,
                      dst_transform=dst_tr, dst_crs="EPSG:4326",
                      resampling=WarpRes.bilinear, init_dest_nodata=True)
        b[band] = dst / 10000.0
    scl_f = glob.glob(f"{S2D}/{prefix}*/GRANULE/*/IMG_DATA/**/T47PQR_*_SCL_*.jp2", recursive=True)[0]
    scl_dst = np.zeros((H, W), np.uint8)
    scl_tr = from_origin(gr["x0"], gr["y1"], (gr["x1"]-gr["x0"])/W, (gr["y1"]-gr["y0"])/H)
    with rasterio.open(scl_f) as src:
        reproject(rasterio.band(src, 1), scl_dst,
                  dst_transform=scl_tr, dst_crs="EPSG:4326",
                  resampling=WarpRes.nearest, init_dest_nodata=True)
    scl = scl_dst
    nodata = (scl == 0).mean() * 100
    cloud = np.isin(scl, [8, 9, 10, 3]).mean() * 100 / max(1 - nodata / 100, 0.05)   # % ของพื้นที่ที่มีข้อมูล
    rgb = np.dstack([b["B04"], b["B03"], b["B02"]])
    rgb = np.clip(rgb * 3.2, 0, 1)                           # ปรับสว่างคร่าว ๆ
    results[key] = cloud
    fig, ax = plt.subplots(figsize=(7.6, 7.5), dpi=120)
    ax.set_aspect(110.96 / (111.32 * np.cos(np.radians(14.24))))
    ax.imshow(rgb, extent=[gr["x0"], gr["x1"], gr["y0"], gr["y1"]], origin="upper", aspect="auto")
    ax.set_xlim(gr["x0"], gr["x1"]); ax.set_ylim(gr["y0"], gr["y1"])
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{title} — เมฆ/เงา ~{cloud:.0f}% ของพื้นที่", fontsize=12.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / f"s2_{key[:10].replace('-', '')}.png")
    plt.close(fig)
    print(f"{key}: เมฆ {cloud:.1f}% (nodata {nodata:.0f}%) -> s2_{key[:10].replace(chr(45),chr(0))[0:0]}{key[:10].replace('-','')}.png")
json.dump(results, open(ROOT / "analysis" / "s2_cloud_pct.json", "w"), indent=1)
