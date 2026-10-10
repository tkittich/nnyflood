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
    "bp_prach": ("ลุ่มบางปะกง (นครนายก–ปราจีนบุรี)", 1281.6),
    "pasak": ("ลุ่มป่าสัก", 521.0),
    "thachin": ("ลุ่มท่าจีน", 160.4),
    "maeklong": ("ลุ่มแม่กลอง", 73.0),
    "ping_cp": ("ลุ่มปิง–เจ้าพระยาตอนบน", 2263.6),
    "bkk_lower": ("ลุ่มเจ้าพระยาตอนล่าง–กทม.", 1199.8),
}


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

    fig, ax = plt.subplots(figsize=(9, 7), dpi=110)
    # พื้นหลัง DEM: ที่ราบครีม · ภูเขาน้ำตาล (hillshade แบบง่าย: ความชันจาก gradient)
    dem_m = np.ma.masked_invalid(dem)
    gy, gx = np.gradient(dem_m.filled(0))
    slope = np.hypot(gy, gx)
    hillshade = 1.0 - np.clip(slope / 0.35, 0, 1)  # ยิ่งชันยิ่งมืด
    colors_dem = np.zeros((ny, nx, 3), float)
    land = np.isfinite(dem)
    high = land & (dem > 60)
    colors_dem[land & ~high] = np.array([0.96, 0.93, 0.84])  # ครีม = ที่ราบ
    colors_dem[high] = np.array([0.72, 0.60, 0.47]) * hillshade[high, None]  # น้ำตาล shade
    colors_dem[high] = np.clip(colors_dem[high], 0.35, 0.85)
    ax.imshow(colors_dem, extent=[x0, x1, y0, y1], origin="upper", aspect="auto")
    # น้ำท่วม
    wm = np.ma.masked_where(~water, water)
    ax.imshow(wm, extent=[x0, x1, y0, y1], origin="upper", aspect="auto",
              cmap=matplotlib.colors.ListedColormap(["#1d6fb8"]), alpha=0.85, interpolation="nearest")
    ax.text(0.02, 0.97, f"พื้นที่น้ำท่วมใหม่ (1 ต.ค. 2569): {km2:,.0f} ตร.กม.",
            transform=ax.transAxes, fontsize=11, va="top",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#1d6fb8", alpha=0.9))
    ax.set_title(f"น้ำท่วมจากดาวเทียมเรดาร์ — {label}", fontsize=13)
    ax.set_xlabel("ลองจิจูด", fontsize=9)
    ax.set_ylabel("ละติจูด", fontsize=9)
    ax.text(0.01, -0.08,
            "น้ำสีน้ำเงิน = พื้นที่น้ำท่วมใหม่ (เทียบฉากก่อนเหตุการณ์ 19–20 ก.ย.) · "
            "ครีม = ที่ราบต่ำกว่า 60 ม. · น้ำตาล = พื้นที่สูง · "
            "ตัดทะเล/น้ำถาวรออกแล้ว (บท กทม.)",
            transform=ax.transAxes, fontsize=8, color="#5a6675")
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"map_{bid}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  map_{bid}.png ({label})", flush=True)


def main() -> None:
    for bid, (label, km2) in BASINS.items():
        try:
            plot_map(bid, label, km2)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {bid}: {type(exc).__name__} {str(exc)[:100]}", flush=True)


if __name__ == "__main__":
    main()