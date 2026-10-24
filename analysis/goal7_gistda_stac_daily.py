"""ดึงผลิตภัณฑ์น้ำท่วม "รายวัน/รายฉาก" ของ GISTDA จากคลัง STAC (api-gateway.gistda.or.th/.../stac/flood) แล้วสรุปพื้นที่น้ำท่วมต่อวัน ต่อฉาก ต่อจังหวัด/อำเภอ
วิธี (ตามคำอธิบายชุดข้อมูล "[Disaster Platform] ข้อมูลภัยพิบัติน้ําท่วม" ในบัญชีข้อมูล opendata.gistda.or.th): แคตตาล็อกปี → ไตรมาส → เดือน → คอลเลกชันรายวัน flood_r2_<YYYYMMDD> → รายการ (item) → asset "data" (GeoJSON)
การยืนยันตัวตน: พารามิเตอร์ api_key= (คีย์ในไฟล์ gitignored data/12_gistda_flood/.gistda_api.json — ห้ามพิมพ์ค่า) · ผลตอบกลับฝังคีย์ในลิงก์จึงปิดบังก่อนแสดงเสมอ
ตั้งไว้ก่อนดูผล: นับเฉพาะพื้นที่ f_area (ไม่รวมแหล่งน้ำถาวร) · เทียบข้ามวันได้เฉพาะฉากที่ผ่านแนวโคจรเดียวกัน (รหัสฉากเดียวกันเวลาเดียวกัน เช่น S1D_..._1819) เพราะแนวครอบคลุมต่างกันตามดาวเทียม
ข้อจำกัด: คลังรายวันไม่ครบทุกวัน (ช่วง 16 ก.ย.–1 ต.ค. 69 ไม่มีคอลเลกชัน) · เผยแพร่ล่าช้าราว 2 วัน · เป็นขอบเขตน้ำท่วมของ GISTDA (ผ่านการจำแนกของผู้ให้บริการ) ไม่ใช่ภาพดิบ
รัน: python analysis/goal7_gistda_stac_daily.py
ผลลัพธ์: data/12_gistda_flood/stac_daily/<YYYYMMDD>.geojson (disk-only) · analysis/goal7/gistda_stac_daily.json
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal6_fetch_gistda_flood as g  # noqa: E402  (reuse-first: อ่านคีย์จากไฟล์ gitignored)

BASE = "https://api-gateway.gistda.or.th/api/2.0/resources/stac/flood/"
RAW = ROOT / "data/12_gistda_flood/stac_daily"
OUT = ROOT / "analysis/goal7/gistda_stac_daily.json"
PROVS = ("จ.ฉะเชิงเทรา", "จ.ปราจีนบุรี", "จ.นครนายก", "จ.สระแก้ว", "จ.ชลบุรี", "จ.ปทุมธานี", "จ.สมุทรปราการ", "จ.กรุงเทพมหานคร")
KEY = g.load_api_key()


def mask(s: str) -> str:
    return re.sub(r"(api_key|token)=[A-Za-z0-9_\-]+", r"\1=<KEY>", s)


def get(path: str) -> dict:
    url = BASE + path + ("&" if "?" in path else "?") + urllib.parse.urlencode({"api_key": KEY})
    for k in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "nnyflood-research/1.0"}), timeout=120))
        except Exception:   # noqa: BLE001
            time.sleep(2 + 2 * k)
    raise RuntimeError("STAC " + mask(path))


def day_collections(year: int = 2026) -> list[str]:
    ids = []
    for q in get(f"catalogs/flood_r2_{year}/children").get("children", []):
        for m in get(f"catalogs/{q['id']}/children").get("children", []):
            ids += [c["id"] for c in get(f"catalogs/{m['id']}/children").get("children", [])]
    return sorted(set(ids))


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    cols = day_collections()
    days = {}
    for c in cols:
        day = c.split("_")[-1]
        f = RAW / f"{day}.geojson"
        if not f.exists():
            feats = []
            for it in get(f"collections/{c}/items").get("features", []):
                href = (it.get("assets", {}).get("data") or {}).get("href")
                if not href:
                    continue
                off = 0
                while True:                                  # ชั้นข้อมูลแบ่งหน้า (ค่าเริ่มต้น 10 รายการ) — ดึงทีละ 1,000 จนครบ numberMatched
                    gj = json.load(urllib.request.urlopen(urllib.request.Request(href + f"&limit=1000&offset={off}", headers={"User-Agent": "nnyflood-research/1.0"}), timeout=300))
                    got = gj.get("features", [])
                    feats += got
                    off += len(got)
                    if not got or off >= int(gj.get("numberMatched") or 0):
                        break
                    time.sleep(0.2)
            f.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False), encoding="utf-8")
        feats = json.loads(f.read_text(encoding="utf-8"))["features"]
        by = defaultdict(lambda: defaultdict(lambda: {"km2": 0.0, "n": 0}))
        amph = defaultdict(lambda: defaultdict(float))
        for ft in feats:
            p = ft["properties"]
            scenes = [s for s in re.split(r"[,\s]+", p.get("file_name") or "") if s]
            key = "+".join(sorted(set(scenes))) or "?"
            v = by[key][p.get("pv_tn")]
            v["km2"] += (p.get("f_area") or 0) / 1e6
            v["n"] += 1
            if p.get("pv_tn") == "จ.ฉะเชิงเทรา":
                amph[key][p.get("ap_tn")] += (p.get("f_area") or 0) / 1e6
        days[day] = {"features": len(feats), "scenes": {k: {pv: {"km2": round(x["km2"], 1), "features": x["n"]} for pv, x in v.items() if pv in PROVS} for k, v in by.items()},
                     "chachoengsao_by_amphoe": {k: {a: round(x, 1) for a, x in sorted(v.items(), key=lambda kv: -kv[1])} for k, v in amph.items()}}
    OUT.write_text(json.dumps({"note": "ผลิตภัณฑ์น้ำท่วมรายวัน/รายฉากของ GISTDA (STAC) — พื้นที่ f_area ต่อฉาก ต่อจังหวัด · เทียบข้ามวันเฉพาะฉากแนวโคจรเดียวกัน", "collections": len(cols), "first": cols[0], "last": cols[-1], "days": days}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(cols), "วัน ·", cols[0], "→", cols[-1])
    for d, v in days.items():
        if d >= "20260902":
            print(d, v["features"], {k: {pv.replace("จ.", ""): x["km2"] for pv, x in s.items() if pv in PROVS[:3]} for k, s in v["scenes"].items()})


if __name__ == "__main__":
    main()
