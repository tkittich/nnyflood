"""เป้าหมาย 7 — ตรวจว่าแนวคลอง (แนวไม่เป็นทางการ) อยู่ในลุ่มน้ำใดบ้าง ตามขอบเขต 22 ลุ่มน้ำของ สทนช.

อินพุต: data/32_goal7_chaophraya2/official_onwr_waterchart/miswc22.json (แฮชใน hashes.sha256)
        data/32_goal7_chaophraya2/derived/centerline.geojson
เอาต์พุต: analysis/goal7/basin_containment.json — ความยาวแนวคลองต่อลุ่ม (กม.) · ใช้ยืนยันข้อความ
        "แนวคลองอยู่ใน 3 ลุ่มน้ำที่ใช้ทั้งหมด" ในรายงาน (ส่วนผังน้ำ)
"""
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Polygon
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/32_goal7_chaophraya2/official_onwr_waterchart/miswc22.json"
CL = ROOT / "data/32_goal7_chaophraya2/derived/centerline.geojson"
OUT = ROOT / "analysis/goal7/basin_containment.json"
LAT0, LON0 = 14.2, 100.9
KX = 111.32e3 * math.cos(math.radians(LAT0))
KY = 110.57e3


def to_m(g):
    return transform(lambda x, y, z=None: ((x - LON0) * KX, (y - LAT0) * KY), g)


def main():
    t = json.loads(SRC.read_text(encoding="utf-8"))
    sc, tr = t["transform"]["scale"], t["transform"]["translate"]
    arcs = []
    for a in t["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)

    def ring(idx):
        pts = []
        for i in idx:
            seg = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(seg if not pts else seg[1:])
        return pts

    cl = json.loads(CL.read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"]
    line = to_m(LineString(cl))
    total = line.length / 1000
    res = []
    for g in t["objects"]["miswc22"]["geometries"]:
        pl = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"] if g["type"] == "MultiPolygon" else []
        polys = []
        for rings in pl:
            try:
                p = Polygon(ring(rings[0]), [ring(r) for r in rings[1:]])
                polys.append(to_m(p).buffer(0))
            except Exception:
                continue
        if not polys:
            continue
        km = line.intersection(unary_union(polys)).length / 1000
        if km > 0.01:
            res.append({"basin": g["properties"]["MBASIN_T"], "code": g["properties"]["MB_CODE"], "km": round(km, 1)})
    res.sort(key=lambda r: -r["km"])
    out = {"line_len_km": round(total, 1), "basins": res, "n_basins": len(res), "sum_km": round(sum(r["km"] for r in res), 1),
           "src": "ขอบเขต 22 ลุ่มน้ำ สทนช. (miswc22.json) ตัดกับแนวคลองไม่เป็นทางการ"}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
