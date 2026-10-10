"""แผนที่น้ำท่วมจากดาวเทียม 6 ลุ่ม — จากมาสก์น้ำ S1 ที่ประมวลผลแล้ว (stage-2 พีค)

แบบแผนเดียวกับแผนที่นครนายก (s1_peak_flood_map.py): พื้นที่น้ำสีน้ำเงิน · ที่ราบโทนครีม ·
ภูเขาโทนน้ำตาล (DEM hillshade แบบง่าย) · ถนน/แม่น้ำจาก OSM ถ้ามีไฟล์ · จุดวัดสำคัญ ·
หัวแผนที่อธิบายในตัว + ตัวเลขพื้นที่น้ำท่วม

ผลลัพธ์: report/assets/goal6/map_<basin>.png (6 ภาพ)
รัน: python analysis/goal6_flood_maps.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rasterio.transform import from_bounds

plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]

ROOT = Path(__file__).resolve().parent.parent
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
STAGE2 = ROOT / "data/22_goal6_network/derived/s1_stage2"
OUT = ROOT / "report/assets/goal6"

BASINS = {
    "bp_prach": ("ลุ่มบางปะกง (นครนายก–ปราจีนบุรี)", "bp_prach"),
    "pasak": ("ลุ่มป่าสัก", "pasak"),
    "thachin": ("ลุ่มท่าจีน", "thachin"),
    "maeklong": ("ลุ่มแม่กลอง", "maeklong"),
    "ping_cp": ("ลุ่มปิง–เจ้าพระยาตอนบน", "ping_cp"),
    "bkk_lower": ("ลุ่มเจ้าพระยาตอนล่าง–กทม.", "bkk_lower_after_sea"),
}  # (ป้าย, canonical key) — ตัวเลข ตร.กม. อ่านจาก canonical.json ตอนวาด (ห้าม hardcode)


def peak_scene(bid: str) -> Path:
    s = json.loads((STAGE2 / "summary.json").read_text(encoding="utf-8"))
    recs = [r for r in s[bid]["scenes"] if r["reference"] != r["scene"]]
    peak = max(recs, key=lambda r: r["water_km2_lowland"])
    return STAGE2 / bid / f"{peak['scene']}_water.npy"


def plot_map(bid: str, label: str, km2: float) -> None:
    g = json.loads((STAGE1 / f"grid_{bid}.json").read_text(encoding="utf-8"))
    x0, y0, x1, y1, nx, ny = g["x0"], g["y0"], g["x1"], g["y1"], g["nx"], g["ny"]
    water = np.load(peak_scene(bid))
    dem = np.load(STAGE1 / f"dem_{bid}.npy")
    lowland = np.load(STAGE1 / f"mask_lowland_{bid}.npy")

    # แก้ยืดภาพ (ตามผู้ใช้ 11 ต.ค. 69): เดิม aspect=geo_aspect ยืดกรอบ 9×7 นิ้วเสมอ
    # — ตั้ง aspect ภูมิศาสตร์จริง: 1° lon ที่ละติจูดกลางของลุ่ม = cos(lat) × 1° lat ในระยะพื้น
    lat_mid = (y0 + y1) / 2
    geo_aspect = 1.0 / max(np.cos(np.radians(lat_mid)), 0.2)  # y/x ในหน่วยองศา (plate carrée)
    lon_range, lat_range = x1 - x0, y1 - y0
    # เลือก figsize ตามรูปทรงจริงของลุ่ม (คงพื้นที่ใกล้เดิม ~63 ตร.นิ้ว กันความละเอียดตก)
    w_in = 9.0
    h_in = w_in * (lat_range * geo_aspect) / lon_range
    h_in = min(max(h_in, 4.0), 11.0)
    fig, ax = plt.subplots(figsize=(w_in, h_in), dpi=110)
    # พื้นหลัง DEM — สูตรเดียวกับรายงาน 1–2 (report/report_assets.py): โทนน้ำตาลไล่ระดับ
    # 8 ชั้น + hillshade มุมดวงอาทิตย์ 45° จากตะวันตกเฉียงเหนือ + posterize (ให้ทั้งชุดรายงานเป็นแฟมิลีเดียว)
    z = dem.astype(float)
    gy, gx = np.gradient(np.nan_to_num(z, nan=0.0))
    az, alt = np.radians(315.0), np.radians(45.0)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    sh = np.cos(alt) * np.cos(slope) + np.sin(alt) * np.sin(slope) * np.cos(az - aspect)
    sh = np.clip((sh - 0.25) / 0.75, 0.05, 1.0)
    sh = np.round(sh * 13) / 13.0
    dem_bins = np.array([0, 30, 80, 150, 300, 500, 750, 1100, 99999])
    dem_colors = np.array([
        [1.00, 0.99, 0.96], [0.98, 0.95, 0.87], [0.93, 0.87, 0.72], [0.85, 0.75, 0.55],
        [0.71, 0.59, 0.40], [0.56, 0.45, 0.30], [0.41, 0.33, 0.22], [0.27, 0.21, 0.14],
    ])
    valid = np.isfinite(dem)
    idx = np.clip(np.digitize(np.where(valid, z, 0), dem_bins) - 1, 0, len(dem_colors) - 1)
    t_shade = np.clip((np.where(valid, z, 0) - 80) / 220, 0, 1)
    factor = (0.85 + 0.15 * sh) * (1 - t_shade) + (0.45 + 0.55 * sh) * t_shade
    colors_dem = dem_colors[idx] * factor[..., None]
    colors_dem = np.round(colors_dem * 12) / 12
    colors_dem[~valid] = 1.0  # นอกครอบ DEM = ขาว
    ax.imshow(colors_dem, extent=[x0, x1, y0, y1], origin="upper", aspect=geo_aspect)
    # น้ำท่วม
    wm = np.ma.masked_where(~water, water)
    ax.imshow(wm, extent=[x0, x1, y0, y1], origin="upper", aspect=geo_aspect,
              cmap=matplotlib.colors.ListedColormap(["#1d6fb8"]), alpha=0.85, interpolation="nearest")
    ax.text(0.02, 0.97, f"พื้นที่น้ำท่วมใหม่ (1 ต.ค. 2569): {km2:,.0f} ตร.กม.",
            transform=ax.transAxes, fontsize=11, va="top",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#1d6fb8", alpha=0.9))
    ax.set_title(f"น้ำท่วมจากดาวเทียมเรดาร์ — {label}", fontsize=13)
    ax.set_xlabel("ลองจิจูด", fontsize=9)
    ax.set_ylabel("ละติจูด", fontsize=9)
    ax.text(0.01, -0.08,
            "น้ำสีน้ำเงิน = พื้นที่น้ำท่วมใหม่ (เทียบฉากก่อนเหตุการณ์ 19–20 ก.ย.) · "
            "โทนอ่อน = ที่ราบ (ขอบเขตวิเคราะห์ ต่ำกว่า 60 ม.) · น้ำตาลไล่เข้ม = พื้นที่สูงตามระดับจริง · "
            "ตัดทะเล/น้ำถาวรออกแล้ว (บท กทม.)",
            transform=ax.transAxes, fontsize=8, color="#5a6675")
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"map_{bid}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  map_{bid}.png ({label})", flush=True)


def main() -> None:
    can = json.loads((ROOT / "analysis/goal6/canonical.json").read_text(encoding="utf-8"))
    for bid, (label, key) in BASINS.items():
        km2 = can["flood_peak_km2"][key]
        try:
            plot_map(bid, label, km2)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {bid}: {type(exc).__name__} {str(exc)[:100]}", flush=True)


if __name__ == "__main__":
    main()