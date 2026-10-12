"""ชั้นผลกระทบ: ประชากรและถนน/ทางรถไฟในพื้นที่ที่ตรวจพบ (รวม = ขอบบน · เข้มงวด = ขอบล่างของ "น้ำใหม่ในฉาก")
— รีวิว Sonnet 12 ต.ค. 69 · suggestion C6 (aggregate เท่านั้น ไม่ระดับครัวเรือน — PDPA)

ข้อมูล: WorldPop 2020 UN-adjusted 1 กม. (ประชากรต่อเซลล์) · OpenStreetMap Geofabrik (ถนน highway=*, ทางรถไฟ railway=rail)
        · มาสก์ตรวจพบรวม/เข้มงวด จาก goal6_s1_landcover.py (derived, disk-only)
ตัวชี้:
  ประชากร (A) เฉลี่ยตามพื้นที่ = Σ ประชากรเซลล์ × สัดส่วนพื้นที่เซลล์ที่ตรวจพบน้ำ (สมมุติกระจายเท่ากันในเซลล์ 1 กม. —
            ประชากรจริงกระจุกในหมู่บ้าน จึงเป็นตัวเลขหยาบ)
  ประชากร (B) ในเซลล์ 1 กม. ที่ตรวจพบน้ำ ≥ 10% ของเซลล์ = "อยู่ในบริเวณที่มีน้ำท่วมใกล้ตัว" (ขอบบนของคนที่ได้รับผลกระทบ)
  ถนนหลัก (motorway–tertiary) / ถนนรอง (unclassified, residential, service, track) / ทางรถไฟ: ความยาว (กม.) ที่ตกบนพิกเซลที่ตรวจพบ
เรดาร์มองไม่เห็นน้ำท่วมใต้ตึก/ในเมือง → ตัวเลขเมืองต่ำกว่าจริง (ดู s1_landcover)
ผลลัพธ์: analysis/goal6/exposure.json/.md
รัน: python analysis/goal6_exposure.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import osmium
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject
from rasterio.windows import from_bounds as win_from_bounds

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/31_external_landcover/raw"
DER = ROOT / "data/31_external_landcover/derived"
S1D = ROOT / "data/13_sentinel1_copernicus/derived"
ST1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
OUT_JSON = ROOT / "analysis/goal6/exposure.json"
OUT_MD = ROOT / "analysis/goal6/exposure.md"
ROADS_CACHE = DER / "osm_lines.npz"
BBOX = (98.2, 12.5, 102.5, 19.6)  # lon0, lat0, lon1, lat1 ครอบทุกลุ่ม
MAJOR = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link",
         "tertiary", "tertiary_link"}
MINOR = {"unclassified", "residential", "service", "living_street", "track"}
STEP_M = 30.0


class Lines(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.pts = {"major": [], "minor": [], "rail": []}

    def way(self, w):
        t = w.tags
        hw, rw = t.get("highway"), t.get("railway")
        if hw in MAJOR:
            cls = "major"
        elif hw in MINOR:
            cls = "minor"
        elif rw == "rail":
            cls = "rail"
        else:
            return
        try:
            xy = np.array([(n.lon, n.lat) for n in w.nodes if n.location.valid()])
        except osmium.InvalidLocationError:
            return
        if len(xy) < 2:
            return
        if xy[:, 0].max() < BBOX[0] or xy[:, 0].min() > BBOX[2] or xy[:, 1].max() < BBOX[1] or xy[:, 1].min() > BBOX[3]:
            return
        # เติมจุดทุก ~30 ม. ตามเส้น
        seg = np.diff(xy, axis=0)
        km_lat, km_lon = 111.0, 111.0 * np.cos(np.radians(xy[:, 1].mean()))
        dist = np.hypot(seg[:, 0] * km_lon, seg[:, 1] * km_lat) * 1000
        out = [xy[:1]]
        for i, d in enumerate(dist):
            n = max(int(np.ceil(d / STEP_M)), 1)
            f = (np.arange(1, n + 1) / n)[:, None]
            out.append(xy[i] + f * seg[i])
        self.pts[cls].append(np.vstack(out))


def load_lines() -> dict[str, np.ndarray]:
    if ROADS_CACHE.exists():
        z = np.load(ROADS_CACHE)
        return {k: z[k] for k in ("major", "minor", "rail")}
    h = Lines()
    h.apply_file(str(RAW / "thailand-latest.osm.pbf"), locations=True)
    out = {k: (np.vstack(v) if v else np.zeros((0, 2))) for k, v in h.pts.items()}
    DER.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(ROADS_CACHE, **out)
    return out


def pop_fraction(pop_ds, mask: np.ndarray, grid: dict):
    """ส่งคืน (ประชากรต่อเซลล์ 1 กม. ในกรอบ, สัดส่วนพื้นที่เซลล์ที่เป็น True ของ mask)"""
    b = (grid["x0"], grid["y0"], grid["x1"], grid["y1"])
    win = win_from_bounds(*b, transform=pop_ds.transform).round_offsets().round_lengths()
    win = rasterio.windows.Window(max(win.col_off, 0), max(win.row_off, 0), win.width + 1, win.height + 1)
    pop = pop_ds.read(1, window=win).astype("float64")
    pop[pop < 0] = 0
    tr = pop_ds.window_transform(win)
    frac = np.zeros(pop.shape, np.float32)
    reproject(mask.astype(np.float32), frac, src_transform=from_bounds(*b, grid["nx"], grid["ny"]), src_crs="EPSG:4326",
              dst_transform=tr, dst_crs="EPSG:4326", resampling=Resampling.average)
    return pop, frac


def line_length_km(pts: np.ndarray, mask: np.ndarray, grid: dict, lowland: np.ndarray | None = None):
    x0, y0, x1, y1, nx, ny = (grid[k] for k in ("x0", "y0", "x1", "y1", "nx", "ny"))
    sel = (pts[:, 0] >= x0) & (pts[:, 0] < x1) & (pts[:, 1] > y0) & (pts[:, 1] <= y1)
    p = pts[sel]
    j = ((p[:, 0] - x0) / (x1 - x0) * nx).astype(int).clip(0, nx - 1)
    i = ((y1 - p[:, 1]) / (y1 - y0) * ny).astype(int).clip(0, ny - 1)
    hit = mask[i, j]
    tot = np.ones(len(p), bool) if lowland is None else lowland[i, j]
    return float(hit.sum() * STEP_M / 1000), float(tot.sum() * STEP_M / 1000)


def main() -> None:
    lines = load_lines()
    print({k: len(v) for k, v in lines.items()}, flush=True)
    pop_ds = rasterio.open(RAW / "tha_ppp_2020_1km_Aggregated.tif")
    scenes = {
        "nn_oct2": (json.load(open(S1D / "grid.json")), np.load(S1D / "mask_lowland.npy")),
        "nn_peak_27sep": (json.load(open(S1D / "grid.json")), np.load(S1D / "mask_lowland.npy")),
    }
    for bid in ("pasak", "maeklong", "bp_prach", "thachin", "ping_cp", "bkk_lower"):
        scenes[bid] = (json.loads((ST1 / f"grid_{bid}.json").read_text(encoding="utf-8")),
                       np.load(ST1 / f"mask_lowland_{bid}.npy"))
    res = {"source": "WorldPop 2020 1 กม. + OSM Geofabrik 12 ต.ค. 2569 · มาสก์: ตรวจพบรวม/เข้มงวด (goal6_s1_landcover)",
           "scenes": {}}
    for tag, (grid, low) in scenes.items():
        gross = np.load(DER / f"gross_{tag}.npy")
        strict = np.load(DER / f"strict_{tag}.npy")
        r: dict = {}
        for name, m in (("gross", gross), ("strict", strict)):
            pop, frac = pop_fraction(pop_ds, m, grid)
            r[name] = {
                "pop_areal": int(round(float((pop * frac).sum()), -2)),
                "pop_cells_ge10pct": int(round(float(pop[frac >= 0.10].sum()), -2)),
            }
            for cls in ("major", "minor", "rail"):
                km, tot = line_length_km(lines[cls], m, grid, low)
                r[name][f"{cls}_km"] = round(km, 1)
                r.setdefault("lowland_" + cls + "_km", round(tot, 1))
        # ประชากรทั้งหมดในที่ราบของฉาก (บริบท)
        pop, frac = pop_fraction(pop_ds, low, grid)
        r["pop_lowland_covered"] = int(round(float((pop * frac).sum()), -3))
        res["scenes"][tag] = r
        print(tag, r, flush=True)
    OUT_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# ผลกระทบ: ประชากรและถนนในพื้นที่ที่ตรวจพบ (รวม = ขอบบน · เข้มงวด = ขอบล่าง)", "",
          "> WorldPop 2020 (1 กม.) + OSM · ปัดเลขประชากรเป็นร้อย · สมมุติกระจายเท่ากันในเซลล์ — **ตัวเลขหยาบ** · เรดาร์มองไม่เห็นน้ำในเมือง", "",
          "| ฉาก | ประชากรในที่ราบของฉาก | (A) เฉลี่ยตามพื้นที่ รวม–เข้มงวด | (B) ในเซลล์ที่ท่วม ≥10% รวม–เข้มงวด | ถนนหลัก กม. รวม–เข้มงวด | ถนนรอง กม. | ทางรถไฟ กม. |",
          "|---|---|---|---|---|---|---|"]
    for tag, r in res["scenes"].items():
        g, s = r["gross"], r["strict"]
        md.append(f"| {tag} | {r['pop_lowland_covered']:,} | {g['pop_areal']:,}–{s['pop_areal']:,} | "
                  f"{g['pop_cells_ge10pct']:,}–{s['pop_cells_ge10pct']:,} | {g['major_km']:,}–{s['major_km']:,} | "
                  f"{g['minor_km']:,}–{s['minor_km']:,} | {g['rail_km']}–{s['rail_km']} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(OUT_MD.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
