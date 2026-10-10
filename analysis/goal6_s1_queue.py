"""เป้าหมาย 6 — คิวดาวน์โหลด Sentinel-1 GRDH ช่วงเหตุการณ์ 23 ก.ย.–2 ต.ค. 69 ครบ 5 ลุ่มรอบแรก

ค้นจาก CDSE OData catalog (ค้นไม่ต้อง auth — ดาวน์โหลดผู้ใช้ล็อกอินเอง ตามนโยบาย repo)
window เวลาสัมผัส: 2026-09-19..2026-10-03 (ครอบรอบ 12 วันทั้ง 2 ด้านของระลอกพีค 26–27 ก.ย.)
ชื่อผลิตภัณฑ์กรอง contains 'GRDH' (แบบเดียวกับที่ใช้จริงในนครนายก — GRDH COG)

ผลลัพธ์: analysis/goal6_s1_queue.md + data/22_goal6_network/raw/s1_queue/s1_queue.json
รัน: python analysis/goal6_s1_queue.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_MD = ROOT / "analysis/goal6_s1_queue.md"
OUT_JSON = ROOT / "data/22_goal6_network/raw/s1_queue/s1_queue.json"
ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

# bbox (lon_min, lat_min, lon_max, lat_max) — ครอบ เขื่อน/ลุ่มบน → เมือง → ปลายน้ำ ของแต่ละบท
BASINS = {
    "ป่าสัก": (100.45, 14.25, 101.30, 15.95),
    "แม่กลอง": (98.50, 12.80, 100.10, 14.90),
    "ปิง–เจ้าพระยาตอนบน": (98.85, 15.55, 100.35, 17.35),
    "ท่าจีน": (99.55, 13.65, 100.30, 14.95),
    "ลุ่มบางปะกง (นครนายก–ปราจีนบุรี)": (100.90, 13.35, 101.75, 14.45),
    # เพิ่ม 10 ต.ค. 69 — ลุ่มที่ 6 (ผู้ใช้ขอ): เจ้าพระยาผ่าน กทม. → ปากน้ำ (ช่อง 100.30–100.45
    # ระหว่าง bbox ท่าจีน/ป่าสักเดิมไม่มีฉากครอบ)
    "ลุ่มเจ้าพระยาตอนล่าง–กทม.–สมุทรปราการ": (100.00, 13.35, 100.95, 14.15),
}
WINDOW = ("2026-09-19T00:00:00.000Z", "2026-10-03T23:59:59.999Z")


def polygon_wkt(bbox) -> str:
    lon1, lat1, lon2, lat2 = bbox
    pts = [(lon1, lat1), (lon2, lat1), (lon2, lat2), (lon1, lat2), (lon1, lat1)]
    return "POLYGON((" + ", ".join(f"{lon} {lat}" for lon, lat in pts) + "))"


def query_bbox(bbox) -> list[dict]:
    wkt = polygon_wkt(bbox)
    filt = (
        "Collection/Name eq 'SENTINEL-1' and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{wkt}') and "
        f"ContentDate/Start gt {WINDOW[0]} and ContentDate/Start lt {WINDOW[1]}"
    )
    url = ODATA + "?$filter=" + urllib.parse.quote(filt, safe="'(),=") + "&$top=200"
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.load(resp)
    out = []
    for p in d.get("value", []):
        name = p.get("Name", "")
        # ตัวแปรเดียวต่อฉาก: COG (แบบที่ใช้จริงในนครนายก — ชื่อท้าย _COG) ตัดตัวแปรต้นฉบับทิ้ง
        if "_COG" not in name:
            continue
        out.append(
            {
                "name": name,
                "start": (p.get("ContentDate") or {}).get("Start"),
                "content_length_mb": round((p.get("ContentLength") or 0) / 1e6, 0),
            }
        )
    seen, uniq = set(), []
    for p in sorted(out, key=lambda x: (x["start"] or "", x["name"])):
        if p["name"] not in seen:
            seen.add(p["name"])
            uniq.append(p)
    return uniq


def main() -> None:
    results = {}
    for label, bbox in BASINS.items():
        prods = query_bbox(bbox)
        prods.sort(key=lambda x: (x["start"] or "", x["name"]))
        results[label] = prods
        total = sum(p["content_length_mb"] for p in prods)
        print(f"{label}: {len(prods)} ฉาก · ~{total / 1000:.1f} GB")
        for p in prods:
            print(f"   {p['start']} · {p['name'][:60]} · {p['content_length_mb'] / 1000:.2f} GB")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {"window": WINDOW, "note": "ค้นจาก CDSE OData (anonymous) — ดาวน์โหลดผู้ใช้ล็อกอินเอง · กรอง GRDH",
             "basins": results},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )

    lines = [
        "# คิวดาวน์โหลด S1 รอบแรก 5 ลุ่ม — ช่วงระลอกพีค 26–27 ก.ย. 69",
        "",
        f"> ค้นจาก CDSE OData catalog (ค้นไม่ต้องล็อกอิน) · หน้าต่างสัมผัส {WINDOW[0][:10]}..{WINDOW[1][:10]} · "
        "กรอง **GRDH** (แบบเดียวกับที่ใช้จริงในนครนายก) · ดาวน์โหลด = ผู้ใช้ล็อกอินเอง",
        "",
    ]
    for label, prods in results.items():
        total = sum(p["content_length_mb"] for p in prods)
        lines.append(f"## {label} — {len(prods)} ฉาก · ~{total / 1000:.1f} GB")
        lines.append("")
        lines.append("| สัมผัส (UTC) | ผลิตภัณฑ์ | ขนาด |")
        lines.append("|---|---|---|")
        for p in prods:
            lines.append(f"| {p['start']} | `{p['name']}` | {p['content_length_mb'] / 1000:.2f} GB |")
        lines.append("")
    lines += [
        "## หมายเหตุ",
        "",
        "- ผลิตภัณฑ์เดียวกันอาจครอบหลายลุ่ม (บางปะกง/ป่าสัก ติดกัน) — ดึงครั้งเดียวใช้ร่วมได้",
        "- หน้าต่างนี้ครอบรอบสัมผัส 12 วันก่อน-หลังพีค 26–27 ก.ย. · ถ้าต้องการเทียบก่อนเหตุการณ์ (ฝน ส.ค. ของป่าสัก) ให้ขยายหน้าต่าง",
        "- รวมคิวทุกลุ่ม (ชนกันด้วย footprint) ประมาณการจากตารางข้างบน — ตรวจแฮชหลังดาวน์โหลดตาม manifest เดิม",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD}")


if __name__ == "__main__":
    main()