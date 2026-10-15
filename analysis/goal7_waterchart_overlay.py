"""เป้าหมาย 7 — ซ้อนแนวคลองเจ้าพระยา2 กับ "ผังน้ำลุ่มน้ำบางปะกง" (สทนช.) และขอบเขตน้ำท่วมคาบอุบัติ/น้ำท่วมจริง

อินพุต: data/32_goal7_chaophraya2/official_onwr_waterchart/*.json (TopoJSON จาก waterchartmis.onwr.go.th/misbpk/json/…)
        data/32_goal7_chaophraya2/derived/centerline.geojson  (แนวไม่เป็นทางการ — ค่าที่ได้เป็น "ประมาณ")
เอาต์พุต: analysis/goal7/waterchart_overlay.json
ช่วงนครนายก = กม.38.6–73.2 (ตามแผนที่รายช่วง) — ใช้เส้นกลางส่วนนี้
"""
import json
import math
from pathlib import Path

from shapely.geometry import LineString, MultiPolygon, Polygon, shape
from shapely.ops import substring, transform, unary_union

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/32_goal7_chaophraya2/official_onwr_waterchart"
D7 = ROOT / "data/32_goal7_chaophraya2/derived"
OUT = ROOT / "analysis/goal7/waterchart_overlay.json"
LAT0, LON0 = 14.2, 100.9
KX = 111.32e3 * math.cos(math.radians(LAT0))
KY = 110.57e3


def to_m(g):
    return transform(lambda x, y, z=None: ((x - LON0) * KX, (y - LAT0) * KY), g)


def decode_topo(path):
    t = json.loads(Path(path).read_text(encoding="utf-8"))
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

    geoms = []
    for obj in t["objects"].values():
        for g in obj.get("geometries", []):
            props = g.get("properties") or {}
            if g["type"] == "Polygon":
                polys = [g["arcs"]]
            elif g["type"] == "MultiPolygon":
                polys = g["arcs"]
            else:
                continue
            ps = []
            for rings in polys:
                rs = [ring(r) for r in rings]
                try:
                    p = Polygon(rs[0], rs[1:]).buffer(0)
                except Exception:
                    continue
                if not p.is_empty:
                    ps.append(p)
            if ps:
                geoms.append((unary_union(ps), props))
    return geoms


def main():
    cl = json.loads((D7 / "centerline.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"]
    line_ll = LineString(cl)
    line = to_m(line_ll)                       # ทิศ: อ่าวไทย → ชัยนาท
    mk = json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]
    pts = sorted((f["properties"]["km"], *f["geometry"]["coordinates"]) for f in mk)
    from shapely.geometry import Point
    import numpy as np
    s = np.array([line.project(to_m(Point(p[1], p[2]))) for p in pts])
    kms = np.array([p[0] for p in pts])
    idx = np.argsort(kms)

    def s_of(km):
        return float(np.interp(km, kms[idx], s[idx]))

    a, b = sorted((s_of(38.6), s_of(73.2)))
    nn = substring(line, a, b)
    corr200 = nn.buffer(100)
    band5 = nn.buffer(5000)
    def km_intervals(g):
        inter = nn.intersection(g)
        segs = [inter] if inter.geom_type == "LineString" else list(getattr(inter, "geoms", []))
        out = []
        for sg in segs:
            if sg.is_empty or sg.geom_type != "LineString" or sg.length < 50:
                continue
            ss = sorted([line.project(Point(*sg.coords[0])), line.project(Point(*sg.coords[-1]))])
            so = np.argsort(s)
            k = [float(np.interp(v, s[so], kms[so])) for v in ss]
            out.append([round(min(k), 1), round(max(k), 1)])
        return sorted(out)

    res = {"note": "แนวคลองไม่เป็นทางการ (My Maps) · ช่วงนครนายก กม.38.6–73.2 · พื้นที่ ตร.กม. (1 ตร.กม. = 625 ไร่)",
           "nn_reach_len_km": round(nn.length / 1000, 1), "corridor_200m_km2": round(corr200.area / 1e6, 2), "band5km_km2": round(band5.area / 1e6, 1), "layers": {}}
    files = {"Floodway": "ผังน้ำ: พื้นที่ทางน้ำหลาก (ล.)", "FloodArea": "ผังน้ำ: พื้นที่น้ำนอง (น.)",
             "Flood_Tr2": "น้ำท่วมคาบอุบัติ 2 ปี", "Flood_Tr5": "น้ำท่วมคาบอุบัติ 5 ปี", "Flood_Tr10": "น้ำท่วมคาบอุบัติ 10 ปี",
             "Flood_Tr25": "น้ำท่วมคาบอุบัติ 25 ปี", "Flood_Tr50": "น้ำท่วมคาบอุบัติ 50 ปี", "Flood_Tr100": "น้ำท่วมคาบอุบัติ 100 ปี",
             "Flood_GISTDA2554": "น้ำท่วมจริง 2554 (GISTDA)", "Flood_GISTDA2564": "น้ำท่วมจริง 2564", "Flood_GISTDA2565": "น้ำท่วมจริง 2565",
             "Flood_GISTDA2566": "น้ำท่วมจริง 2566"}
    for k, label in files.items():
        f = SRC / f"{k}.json"
        if not f.exists():
            continue
        geoms = decode_topo(f)
        allg = unary_union([to_m(g) for g, _ in geoms])
        minx, miny, maxx, maxy = unary_union([g for g, _ in geoms]).bounds
        cover = (minx, miny, maxx, maxy)
        in_band = allg.intersection(band5)
        in_corr = allg.intersection(corr200)
        res["layers"][k] = {"label": label, "n_polygons": len(geoms), "bbox_lonlat": [round(v, 3) for v in cover],
                            "in_band5km_km2": round(in_band.area / 1e6, 2), "in_corridor200m_km2": round(in_corr.area / 1e6, 3),
                            "corridor_share_pct": round(in_corr.area / corr200.area * 100, 1),
                            "line_crosses_length_km": round(nn.intersection(allg).length / 1000, 2),
                            "km_intervals": km_intervals(allg)}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
