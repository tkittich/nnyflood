"""แผนที่น้ำเรดาร์ Sentinel-1 ของฉะเชิงเทรา 4–22 ต.ค. 2569 ด้วยกฎตรึงเดิม (R7-22)

กติกาตั้งก่อนดูผล: docs/S1_CHACHOENGSAO_RECENT_PREREG.md · ขั้นตอน:
  queue   ค้นคลัง CDSE (ไม่ต้องใช้กุญแจ) แล้วเขียนคิวฉากใหม่ + ฉากอ้างอิงที่ยังไม่มี
  process ลงพิกัด/คาลิเบรตฉากใหม่ (ฟังก์ชันเดิมของ goal6_s1_stage1) แล้วตัดน้ำด้วย s1_change_detect.detect
ดาวน์โหลดฉากด้วย: python analysis/goal6_s1_download.py --queue <คิวที่ได้> --dest data/22_goal6_network/raw/s1_recent
รัน: python analysis/goal7_s1_chachoengsao_recent.py queue | process
ผลลัพธ์: data/22_goal6_network/raw/s1_recent/s1_recent_queue.json · analysis/goal7/s1_chachoengsao_recent.json
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
RAW_OLD = ROOT / "data/22_goal6_network/raw/s1_2026"
RAW_NEW = ROOT / "data/22_goal6_network/raw/s1_recent"
QUEUE = RAW_NEW / "s1_recent_queue.json"
ST1_OLD = ROOT / "data/22_goal6_network/derived/s1_stage1"
ST1_NEW = ROOT / "data/22_goal6_network/derived/s1_recent_stage1"
OUT = ROOT / "analysis/goal7/s1_chachoengsao_recent.json"
BOUND = ROOT / "data/10_mitrearth_gis/provinces/chachoengsao_10/2 Boundary and Point/10 pbound.shp"   # ชั้น bound เป็นเขตรวมเพื่อนบ้าน 12,900 ตร.กม. ไม่ใช่จังหวัด — ใช้ pbound เลือก CHACHOENGSAO
ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
BASIN = "bp_prach"
AOI_WKT = "POLYGON((101.0 13.45, 101.6 13.45, 101.6 13.95, 101.0 13.95, 101.0 13.45))"
NEW_FROM, NEW_TO = "2026-10-04T00:00:00.000Z", "2026-10-28T00:00:00.000Z"
REF_BEFORE = "2026-09-24T00:00:00"          # ฉากอ้างอิง = ถ่ายก่อนเวลานี้ (UTC)
CELL_KM2 = 0.0009
OFFSET = {"A": 73, "B": 27, "C": 172, "D": 73}   # ค่าชดเชยเลขวงโคจรสัมบูรณ์ → สัมพัทธ์ (S1C, S1D ใช้วงเดียวกันได้)


def rel_orbit(name: str) -> int:
    ab = int(re.search(r"_(\d{6})_[0-9A-F]{6}_", name).group(1))
    return (ab - OFFSET[name[2]]) % 175 + 1


def start_of(name: str) -> str:
    m = re.search(r"_(\d{8})T(\d{6})_", name)
    d, t = m.group(1), m.group(2)
    return f"{d[:4]}-{d[4:6]}-{d[6:]}T{t[:2]}:{t[2:4]}:{t[4:]}"


def query_aoi(wkt: str, a: str, b: str) -> list[dict]:
    """ค้นคลัง CDSE (ไม่ต้องใช้กุญแจ): ฉาก IW GRDH แบบ COG ที่ทับรูปหลายเหลี่ยม wkt และเริ่มถ่ายระหว่าง a ถึง b"""
    filt = ("Collection/Name eq 'SENTINEL-1' and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}') and "
            f"ContentDate/Start gt {a} and ContentDate/Start lt {b}")
    url = ODATA + "?$filter=" + urllib.parse.quote(filt, safe="'(),=") + "&$top=200"
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal7/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        v = json.load(r)["value"]
    return [p for p in v if "_COG" in p["Name"] and "GRDH" in p["Name"]]


def query(a: str, b: str) -> list[dict]:
    return query_aoi(AOI_WKT, a, b)


def build_queue() -> None:
    new = query(NEW_FROM, NEW_TO)
    old = query("2026-08-25T00:00:00.000Z", "2026-09-24T00:00:00.000Z")
    have = {p.name for p in RAW_OLD.glob("*.SAFE")} | {p.name for p in RAW_NEW.glob("*.SAFE")}
    # ฉากอ้างอิง: ต่อวงโคจรสัมพัทธ์ ใช้ฉากล่าสุดก่อน 24 ก.ย. (ทุกชิ้นส่วนของวันนั้น)
    by_rel = defaultdict(list)
    for p in old:
        by_rel[rel_orbit(p["Name"])].append(p)
    refs = []
    for rel, ps in by_rel.items():
        day = max(start_of(p["Name"])[:10] for p in ps)
        refs += [p for p in ps if start_of(p["Name"])[:10] == day]
    pick = {p["Name"]: p for p in new + refs}
    prods = [{"name": n, "start": start_of(n), "rel_orbit": rel_orbit(n), "role": "new" if p in new else "reference",
              "content_length_mb": round(p.get("ContentLength", 0) / 1e6), "on_disk_already": n in have}
             for n, p in sorted(pick.items(), key=lambda kv: kv[0][17:])]
    RAW_NEW.mkdir(parents=True, exist_ok=True)
    todo = [x for x in prods if not x["on_disk_already"]]
    q = {"window": [NEW_FROM, NEW_TO], "note": "คิวตามกติกา docs/S1_CHACHOENGSAO_RECENT_PREREG.md",
         "basins": {"ฉะเชิงเทรา": [{"name": x["name"], "start": x["start"], "content_length_mb": x["content_length_mb"]} for x in todo]},
         "all_selected": prods}
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ฉากที่เลือก {len(prods)} (ต้องโหลดเพิ่ม {len(todo)} · {sum(x['content_length_mb'] for x in todo) / 1e3:.1f} GB)")
    for x in prods:
        print(x["role"], x["start"], "rel", x["rel_orbit"], x["name"][:3], "disk" if x["on_disk_already"] else "TODO")


def province_mask(g: dict) -> np.ndarray:
    import geopandas as gpd
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds
    b = gpd.read_file(BOUND).to_crs(4326)
    b = b[b["PROV_NAME"] == "CHACHOENGSAO"]
    assert len(b) == 1
    tr = from_bounds(g["x0"], g["y0"], g["x1"], g["y1"], g["nx"], g["ny"])
    return rasterize([(geom, 1) for geom in b.geometry], out_shape=(g["ny"], g["nx"]), transform=tr, fill=0, dtype="uint8").astype(bool)


def load_db(tag: str, pol: str):
    for d in (ST1_NEW / BASIN, ST1_OLD / BASIN):
        p = d / f"{tag}_{pol}_db.npy"
        if p.exists():
            return np.load(p)
    return None


def mosaic(tags: list[str], pol: str):
    out = None
    for t in tags:
        a = load_db(t, pol)
        if a is None:
            return None
        out = a if out is None else np.where(np.isfinite(out), out, a)
    return out


def process() -> None:
    import goal6_s1_stage1 as s1
    from s1_change_detect import detect
    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    sel = q["all_selected"]
    (ST1_NEW / BASIN).mkdir(parents=True, exist_ok=True)
    if not (ST1_NEW / f"grid_{BASIN}.json").exists():
        shutil.copy(ST1_OLD / f"grid_{BASIN}.json", ST1_NEW / f"grid_{BASIN}.json")
    s1.OUT = ST1_NEW
    s1.RAW_S1 = RAW_NEW
    g = json.loads((ST1_NEW / f"grid_{BASIN}.json").read_text(encoding="utf-8"))
    for x in sel:                                   # ลงพิกัดเฉพาะฉากที่ยังไม่มีผลขั้นที่ 1
        tag = x["name"].replace(".SAFE", "")
        if load_db(tag, "vh") is None and (RAW_NEW / x["name"]).exists():
            print(s1.process_job(BASIN, x["name"]), flush=True)
    lowland = np.load(ST1_OLD / f"mask_lowland_{BASIN}.npy")
    prov = province_mask(g)
    # ฉากช่วงเหตุการณ์ที่มีบนดิสก์แล้ว (26 ก.ย.–2 ต.ค.) ที่ทับพื้นที่ศึกษา — รวมในอนุกรมด้วยกติกาเดียวกัน
    event = [p.name for p in ST1_OLD.joinpath(BASIN).glob("*_stats.json")]
    event = [e.replace("_stats.json", "") for e in event if "2026-09-24" < start_of(e) < "2026-10-04"]
    tags = {x["name"].replace(".SAFE", ""): x for x in sel if x["role"] == "new"}
    refs = defaultdict(list)
    for x in sel:
        if x["role"] == "reference":
            refs[x["rel_orbit"]].append(x["name"].replace(".SAFE", ""))
    for e in event:                                # ถ้าวงโคจรของฉากเหตุการณ์ยังไม่มีอ้างอิงในคิว ใช้ฉากก่อน 24 ก.ย. บนดิสก์
        r = rel_orbit(e)
        if r not in refs:
            pre = [p.name.replace("_stats.json", "") for p in ST1_OLD.joinpath(BASIN).glob("*_stats.json")]
            pre = [t for t in pre if rel_orbit(t) == r and start_of(t) < REF_BEFORE]
            if pre:
                day = max(start_of(t)[:10] for t in pre)
                refs[r] = [t for t in pre if start_of(t)[:10] == day]
    scenes = defaultdict(list)                     # (วันที่, วงโคจร) → ชิ้นส่วนฉาก
    for t in list(tags) + event:
        scenes[(start_of(t)[:10], rel_orbit(t))].append(t)
    prov_km2 = float(prov.sum()) * CELL_KM2
    rows = []
    for (day, r), parts in sorted(scenes.items()):
        rec = {"date": day, "rel_orbit": r, "satellite": sorted({p[:3] for p in parts}), "n_slices": len(parts),
               "role": "event_on_disk" if parts[0] in event else "new"}
        if r not in refs or any(load_db(t, "vh") is None for t in parts):
            rec.update({"reference": None, "status": "no_reference_or_not_processed"})
            rows.append(rec)
            continue
        pre_vh, pre_vv = mosaic(refs[r], "vh"), mosaic(refs[r], "vv")
        post_vh, post_vv = mosaic(parts, "vh"), mosaic(parts, "vv")
        w = detect(pre_vh, post_vh, pre_vv, post_vv, lowland)
        cover = np.isfinite(post_vh) & np.isfinite(pre_vh) & prov
        rec.update({"reference": sorted(x[17:32] for x in refs[r]), "status": "ok",
                    "water_km2_lowland_grid": round(float(w.sum()) * CELL_KM2, 1),
                    "water_km2_in_province": round(float((w & prov).sum()) * CELL_KM2, 1),
                    "province_coverage_frac": round(float(cover.sum()) / max(float(prov.sum()), 1), 3),
                    "water_frac_of_covered_province": round(float((w & cover).sum() / max(cover.sum(), 1)), 4)})
        rows.append(rec)
        print(rec, flush=True)
    res = {"rule": "docs/S1_CHACHOENGSAO_RECENT_PREREG.md", "detect_rule": "s1_change_detect.detect (ตรึงเดิม)",
           "province_km2_on_grid": round(prov_km2, 1), "scenes": rows,
           "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("เขียน", OUT)


if __name__ == "__main__":
    {"queue": build_queue, "process": process}[sys.argv[1]]()
