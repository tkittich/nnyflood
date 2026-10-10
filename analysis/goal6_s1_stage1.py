"""เป้าหมาย 6 — L2 ขั้นที่ 1: geocode + calibrate ฉาก S1 ทุกฉากบนกริด 30 ม.ต่อลุ่ม (ขนาน)

ใช้ฟังก์ชัน geocode/calibrate เดียวกันกับ pipeline นครนายก (s1_process.py — ผ่านรีวิว 5 รอบ)
แต่กริดต่อลุ่มจาก config (จุดวัด/เขื่อน/จุดฝน + pad 0.15°) — **ยังไม่ตัดน้ำ** (ขั้น 2 ใช้กฎ canonical
ΔVH≤−0.5/ΔVV≤−1.5/VH≤−20 เทียบฉากก่อนเหตุการณ์ แบบ s1_change_detect.py)

ผลลัพธ์: data/22_goal6_network/derived/s1_stage1/grid_<basin>.json ·
         derived/s1_stage1/<basin>/<scene>_<pol>_db.npy + <scene>_stats.json
ทำซ้ำ/ต่อ: ไฟล์ที่มีแล้วข้าม · รันซ้ำคือ resume
ต้องการ: ฉากจาก goal6_s1_download.py + config.json
รัน: python analysis/goal6_s1_stage1.py [--basin id] [--limit N] [--workers 8] [--job basin:scene]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from rasterio.transform import from_bounds
from scipy.ndimage import map_coordinates, uniform_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s1_process import build_geocode, parse_cal_lut  # noqa: E402 — ฟังก์ชันเดิม pipeline นครนายก

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "analysis/goal6/config.json"
LOAD = ROOT / "data/02_thaiwater/raw/2026-10-10_waterlevel_load.json"
CAND = ROOT / "analysis/goal6_dam_candidates.json"
RAW_S1 = ROOT / "data/22_goal6_network/raw/s1_2026"
QUEUE = ROOT / "data/22_goal6_network/raw/s1_queue/s1_queue.json"
OUT = ROOT / "data/22_goal6_network/derived/s1_stage1"
PAD = 0.15
RES_M = 30.0
# คิว S1 (goal6_s1_queue.py) ใช้ label ภาษาไทย — config ใช้ id; ตารางแปลง (ค่าคงที่ตามคิวที่ commit)
QUEUE_TO_ID = {
    "ป่าสัก": "pasak",
    "แม่กลอง": "maeklong",
    "ปิง–เจ้าพระยาตอนบน": "ping_cp",
    "ท่าจีน": "thachin",
    "ลุ่มบางปะกง (นครนายก–ปราจีนบุรี)": "bp_prach",
    "ลุ่มเจ้าพระยาตอนล่าง–กทม.–สมุทรปราการ": "bkk_lower",  # เพิ่ม 10 ต.ค. 69 — 4 ฉาก มีบนดิสก์แล้ว
}


def basin_aoi(bid: str, rec: dict) -> tuple[float, float, float, float]:
    lats, lons = [], []
    payload = json.loads(LOAD.read_text(encoding="utf-8"))
    wl = payload["waterlevel_data"]
    rows = wl.get("data", wl) if isinstance(wl, dict) else wl
    by_id = {}
    for r in rows:
        st = r.get("station") or {}
        if st.get("id") is not None:
            by_id[st["id"]] = (st.get("tele_station_lat"), st.get("tele_station_long"))
    for st in rec["stations"]:
        lat, lon = by_id.get(st["id"], (None, None))
        if lat and lon:
            lats.append(lat)
            lons.append(lon)
    cand = {c["dam_name"]: c for c in json.loads(CAND.read_text(encoding="utf-8"))["candidates"]}
    for d in rec["dams"]:
        c = cand.get(d["name"])
        if c and c.get("lat") and c.get("long"):
            lats.append(c["lat"])
            lons.append(c["long"])
    for _label, (lon, lat) in rec["rain_points"].items():
        lats.append(lat)
        lons.append(lon)
    return min(lons) - PAD, min(lats) - PAD, max(lons) + PAD, max(lats) + PAD


def make_grid(bid: str, rec: dict) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    gpath = OUT / f"grid_{bid}.json"
    if gpath.exists():
        return json.loads(gpath.read_text(encoding="utf-8"))
    x0, y0, x1, y1 = basin_aoi(bid, rec)
    mid = (y0 + y1) / 2
    dlat = RES_M / 111_320.0
    dlon = RES_M / (111_320.0 * math.cos(math.radians(mid)))
    ny = int(round((y1 - y0) / dlat))
    nx = int(round((x1 - x0) / dlon))
    g = {"basin": bid, "x0": round(x0, 6), "y0": round(y0, 6), "x1": round(x1, 6),
         "y1": round(y1, 6), "res": RES_M, "nx": nx, "ny": ny}
    gpath.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"กริด {bid}: {nx}×{ny} = {nx * ny / 1e6:.0f} ล้านเซลล์ · {nx * ny * RES_M ** 2 / 1e6:.0f} ตร.กม.ครอบ", flush=True)
    return g


def process_job(basin: str, scene: str) -> str:
    """ทำ 1 job = ฉาก 1 บนกริดลุ่ม 1 — คืนสรุปสั้น"""
    out_dir = OUT / basin
    out_dir.mkdir(parents=True, exist_ok=True)
    g = json.loads((OUT / f"grid_{basin}.json").read_text(encoding="utf-8"))
    x0, y0, x1, y1, nx, ny = g["x0"], g["y0"], g["x1"], g["y1"], g["nx"], g["ny"]

    safe = RAW_S1 / scene
    tag = scene.replace(".SAFE", "")
    npx_path = out_dir / f"{tag}_vv_db.npy"
    stats_path = out_dir / f"{tag}_stats.json"
    if npx_path.exists() and stats_path.exists():
        return f"skip {basin}/{tag[:40]}"

    ann_files = sorted((safe / "annotation").glob("s1*-iw-grd-v*-cog.xml"))
    ann = [p for p in ann_files if "-vv-" in p.name][0].read_text(encoding="utf-8")
    invert, err = build_geocode(ann)
    glon, glat = np.meshgrid(
        x0 + (np.arange(nx) + 0.5) * (x1 - x0) / nx,
        y1 - (np.arange(ny) + 0.5) * (y1 - y0) / ny,
    )
    lr, pr = invert(glon, glat)

    stats = {"basin": basin, "scene": scene, "geocode_err_px": round(err, 2)}
    for pol in ("vh", "vv"):
        ann_pol = [p for p in ann_files if f"-{pol}-" in p.name][0]
        cal_pol = [c for c in (safe / "annotation" / "calibration").glob(f"calibration-*-{pol}-*.xml")][0]
        spl = parse_cal_lut(cal_pol.read_text(encoding="utf-8"))
        tif = [m for m in (safe / "measurement").glob(f"*-{pol}-*cog.tiff")][0]
        import rasterio

        with rasterio.open(tif) as ds:
            H, W = ds.height, ds.width
            dn = ds.read(1).astype(np.float32)
        valid = (lr >= 1) & (lr <= H - 2) & (pr >= 1) & (pr <= W - 2)
        coords = np.stack([np.clip(lr, 0, H - 1), np.clip(pr, 0, W - 1)])
        sampled = map_coordinates(dn, coords, order=1, mode="nearest")
        a_lut = spl.ev(lr, pr).astype(np.float32)
        sig = np.where((sampled > 0) & (a_lut > 0), sampled ** 2 / np.maximum(a_lut, 1e-6) ** 2, np.nan)
        db = (10.0 * np.log10(sig)).astype(np.float32)
        fill = np.nanmedian(db[valid]) if valid.any() else -20.0
        db_f = np.where(np.isfinite(db), db, fill)  # กัน NaN แพร่ใน uniform_filter (บั๊ก GL-12)
        db_s = uniform_filter(db_f, size=5)
        db_s = np.where(valid, db_s, np.nan).astype(np.float32)
        np.save(out_dir / f"{tag}_{pol}_db.npy", db_s)
        stats[f"{pol}_median_db"] = round(float(np.nanmedian(db_s)), 1)
        stats[f"{pol}_valid_frac"] = round(float(valid.mean()), 3)
        del dn, sampled, sig, db, db_f, db_s
    stats_path.write_text(json.dumps(stats, ensure_ascii=False), encoding="utf-8")
    return f"done {basin}/{tag[:40]} valid_vh={stats['vh_valid_frac']}"


def worker(args: tuple[str, str]) -> str:
    basin, scene = args
    try:
        return process_job(basin, scene)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR {basin}/{scene[:40]}: {type(exc).__name__} {str(exc)[:120]}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--basin", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--job", default=None, help="basin:scene — ทำ job เดียว (smoke test)")
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    q = json.loads(QUEUE.read_text(encoding="utf-8"))

    jobs: list[tuple[str, str]] = []
    for basin_label, prods in q["basins"].items():
        basin = QUEUE_TO_ID.get(basin_label, basin_label)
        if basin not in cfg["basins"]:
            print(f"ข้าม {basin_label} (ไม่มีใน config)", flush=True)
            continue
        if args.basin and basin != args.basin:
            continue
        make_grid(basin, cfg["basins"][basin])
        for p in prods:
            safe = RAW_S1 / p["name"]
            if not safe.exists():
                continue
            jobs.append((basin, p["name"]))
    if args.job:
        b, s = args.job.split(":", 1)
        b = QUEUE_TO_ID.get(b, b)
        if b not in cfg["basins"]:
            raise SystemExit(f"ไม่รู้จักลุ่ม: {b}")
        jobs = [(b, s if s.endswith(".SAFE") else s + ".SAFE")]
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"jobs: {len(jobs)} (workers {args.workers})", flush=True)

    from multiprocessing import Pool

    with Pool(args.workers) as pool:
        for res in pool.imap_unordered(worker, jobs):
            print(res, flush=True)


if __name__ == "__main__":
    main()