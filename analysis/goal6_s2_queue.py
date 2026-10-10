"""เป้าหมาย 6 — คิว Sentinel-2 L2A (ตรวจยืนยนอิสระ + ภาพสีจริง) ต่อลุ่ม — ค้นจาก CDSE OData

บทบาทแบบนครนายก: S2 = ตรวจ optical อิสระ (MNDWI) + ภาพสีจริงประกอบรายงาน — ไม่ใช่ตัวหลักตัดน้ำ
ค้นหน้าต่าง: ก่อนเหตุการณ์ (15–20 ก.ย.) + ระลอกพีค (26–28 ก.ย.) + หลัง (29 ก.ย.–2 ต.ค.) ·
กรองเมฆ: cloudCover < 30% (attribute ใน catalog) · tile ตรวจด้วย footprint intersection
ผลลัพธ์: data/22_goal6_network/raw/s2_queue/s2_queue.json + analysis/goal6_s2_queue.md
ดาวน์โหลดภายหลังด้วย goal6_s1_download.py --queue s2_queue.json (S3 pipeline เดียวกัน)
รัน: python analysis/goal6_s2_queue.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "data/22_goal6_network/raw/s2_queue/s2_queue.json"
OUT_MD = ROOT / "analysis/goal6_s2_queue.md"
ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

# bbox ต่อลุ่ม (เดียวกับ S1 queue — ย่อให้แคบลงเฉพาะพื้นที่ที่ราบสำคัญของบท)
BASINS = {
    "ป่าสัก": (100.45, 14.25, 101.30, 15.95),
    "แม่กลอง": (99.10, 13.20, 100.10, 14.30),
    "ปิง–เจ้าพระยาตอนบน": (99.60, 15.55, 100.35, 16.90),
    "ท่าจีน": (99.70, 13.65, 100.30, 14.60),
    "ลุ่มบางปะกง (นครนายก–ปราจีนบุรี)": (100.90, 13.35, 101.75, 14.45),
    "ลุ่มเจ้าพระยาตอนล่าง–กทม.–สมุทรปราการ": (100.10, 13.35, 100.95, 14.15),
}
WINDOWS = [("ก่อนเหตุการณ์", "2026-09-15T00:00:00.000Z", "2026-09-21T00:00:00.000Z"),
           ("ระลอกพีค", "2026-09-25T00:00:00.000Z", "2026-09-29T00:00:00.000Z"),
           ("หลังเหตุการณ์", "2026-09-29T00:00:00.000Z", "2026-10-03T00:00:00.000Z")]


def polygon_wkt(bbox) -> str:
    lon1, lat1, lon2, lat2 = bbox
    pts = [(lon1, lat1), (lon2, lat1), (lon2, lat2), (lon1, lat2), (lon1, lat1)]
    return "POLYGON((" + ", ".join(f"{lon} {lat}" for lon, lat in pts) + "))"


def query(bbox, w_start, w_end) -> list[dict]:
    wkt = polygon_wkt(bbox)
    cloud = ("Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' "
             "and att/OData.CSC.DoubleAttribute/Value lt 30)")
    filt = (f"Collection/Name eq 'SENTINEL-2' and contains(Name,'L2A') and "
            f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}') and "
            f"ContentDate/Start gt {w_start} and ContentDate/Start lt {w_end} and {cloud}")
    url = ODATA + "?$filter=" + urllib.parse.quote(filt, safe="'(),=") + "&$top=60"
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.load(resp)
    return [{"name": p["Name"], "start": (p.get("ContentDate") or {}).get("Start"),
             "cloud": next((a["Value"] for a in p.get("Attributes", [])
                            if a.get("Name") == "cloudCover"), None),
             "mb": round((p.get("ContentLength") or 0) / 1e6)} for p in d.get("value", [])]


def main() -> None:
    out = {"windows": [[w[0], w[1], w[2]] for w in WINDOWS], "basins": {}}
    md = ["# คิว Sentinel-2 L2A (เมฆ <30%) — ตรวจยืนยันอิสระ + ภาพสีจริง", "",
          "> ค้น CDSE OData · ดาวน์โหลดภายหลังด้วย S3 pipeline เดิม (goal6_s1_download.py --queue ไฟล์นี้)", ""]
    for label, bbox in BASINS.items():
        entries = []
        for wname, ws, we in WINDOWS:
            for p in query(bbox, ws, we):
                entries.append({"window": wname, **p})
        entries.sort(key=lambda x: (x["window"], x["start"] or ""))
        out["basins"][label] = entries
        md.append(f"## {label} — {len(entries)} ฉาก")
        md.append("")
        md.append("| หน้าต่าง | สัมผัส (UTC) | เมฆ % | ขนาด | ผลิตภัณฑ์ |")
        md.append("|---|---|---|---|---|")
        for p in entries:
            cloud = f"{p['cloud']:.0f}" if p.get("cloud") is not None else "—"
            md.append(f"| {p['window']} | {p['start']} | {cloud} | {p['mb']/1000:.1f} GB | `{p['name']}` |")
        md.append("")
        print(f"{label}: {len(entries)} ฉาก", flush=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()