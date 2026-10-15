"""เป้าหมาย 7 — ซ้อนแนวคลองเจ้าพระยา2 กับ "ผังน้ำ" และขอบเขตน้ำท่วมของ สทนช. (3 ลุ่มน้ำ: บางปะกง · เจ้าพระยา · ป่าสัก)

อินพุต: data/32_goal7_chaophraya2/official_onwr_waterchart/{*.json (บางปะกง), lcpy/*.json (เจ้าพระยา), psk/*.json (ป่าสัก)}
        — TopoJSON จาก waterchartmis.onwr.go.th/{misbpk,mislcpy,mispsk}/json/…  (ดึงจากสคริปต์ของหน้าเว็บ ไม่ใช่ KMZ)
        data/32_goal7_chaophraya2/derived/{centerline,km_markers}.geojson  (แนวไม่เป็นทางการ — ค่าที่ได้เป็น "ประมาณ")
เอาต์พุต: analysis/goal7/waterchart_overlay.json
ช่วง: นครนายก = กม.38.6–73.2 · ทั้งคลองใหม่ = กม.0–135.655
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import substring, transform, unary_union

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/32_goal7_chaophraya2/official_onwr_waterchart"
D7 = ROOT / "data/32_goal7_chaophraya2/derived"
OUT = ROOT / "analysis/goal7/waterchart_overlay.json"
LAT0, LON0 = 14.2, 100.9
KX = 111.32e3 * math.cos(math.radians(LAT0))
KY = 110.57e3
BASINS = [("บางปะกง", SRC), ("เจ้าพระยา", SRC / "lcpy"), ("ป่าสัก", SRC / "psk")]
LAYERS = {"Floodway": "ผังน้ำ: พื้นที่ทางน้ำหลาก (ล.)", "FloodArea": "ผังน้ำ: พื้นที่น้ำนอง (น.)",
          "Flood_Tr2": "น้ำท่วมคาบอุบัติ 2 ปี", "Flood_Tr5": "น้ำท่วมคาบอุบัติ 5 ปี", "Flood_Tr10": "น้ำท่วมคาบอุบัติ 10 ปี",
          "Flood_Tr25": "น้ำท่วมคาบอุบัติ 25 ปี", "Flood_Tr50": "น้ำท่วมคาบอุบัติ 50 ปี", "Flood_Tr100": "น้ำท่วมคาบอุบัติ 100 ปี",
          "Flood_GISTDA2554": "น้ำท่วมจริง 2554 (GISTDA)", "Flood_GISTDA2564": "น้ำท่วมจริง 2564", "Flood_GISTDA2565": "น้ำท่วมจริง 2565",
          "Flood_GISTDA2566": "น้ำท่วมจริง 2566"}


def to_m(g):
    return transform(lambda x, y, z=None: ((x - LON0) * KX, (y - LAT0) * KY), g)


def decode_topo(path, bbox):
    """ถอด TopoJSON เฉพาะรูปทรงที่ขอบเขตตัดกับ bbox (lon/lat) — เร็วกว่าถอดทั้งไฟล์"""
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
    x0, y0, x1, y1 = bbox

    def ring(idx):
        pts = []
        for i in idx:
            seg = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(seg if not pts else seg[1:])
        return pts

    polys = []
    total = 0
    for obj in t["objects"].values():
        for g in obj.get("geometries", []):
            if g["type"] == "Polygon":
                pl = [g["arcs"]]
            elif g["type"] == "MultiPolygon":
                pl = g["arcs"]
            else:
                continue
            for rings in pl:
                total += 1
                outer = ring(rings[0])
                xs = [p[0] for p in outer]
                ys = [p[1] for p in outer]
                if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
                    continue
                try:
                    pg = Polygon(outer, [ring(r) for r in rings[1:]]).buffer(0)
                except Exception:
                    continue
                if not pg.is_empty:
                    polys.append(pg)
    return polys, total


def main():
    cl = json.loads((D7 / "centerline.geojson").read_text(encoding="utf-8"))["features"][0]["geometry"]["coordinates"]
    line = to_m(LineString(cl))                       # ทิศ: อ่าวไทย → ชัยนาท
    mk = json.loads((D7 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]
    pts = sorted((f["properties"]["km"], *f["geometry"]["coordinates"]) for f in mk)
    s = np.array([line.project(to_m(Point(p[1], p[2]))) for p in pts])
    kms = np.array([p[0] for p in pts])
    so = np.argsort(s)
    ki = np.argsort(kms)

    def s_of(km):
        return float(np.interp(km, kms[ki], s[ki]))

    def km_of(sv):
        return float(np.interp(sv, s[so], kms[so]))

    reaches = {"nn": (38.6, 73.2), "all": (0.0, 135.655)}
    sub = {}
    for k, (k0, k1) in reaches.items():
        a, b = sorted((s_of(k0), s_of(k1)))
        ln = substring(line, a, b)
        sub[k] = {"line": ln, "corr": ln.buffer(100), "len_km": ln.length / 1000}
    bl = LineString(cl).bounds
    bbox = (bl[0] - 0.08, bl[1] - 0.08, bl[2] + 0.08, bl[3] + 0.08)

    def intervals(ln, g):
        inter = ln.intersection(g)
        segs = [inter] if inter.geom_type == "LineString" else [x for x in getattr(inter, "geoms", []) if x.geom_type == "LineString"]
        iv = []
        for sg in segs:
            if sg.is_empty or sg.length < 50:
                continue
            ss = sorted([line.project(Point(*sg.coords[0])), line.project(Point(*sg.coords[-1]))])
            k = sorted([km_of(ss[0]), km_of(ss[1])])
            iv.append([round(k[0], 1), round(k[1], 1)])
        iv.sort()
        merged = []
        for a_, b_ in iv:
            if merged and a_ <= merged[-1][1] + 0.1:
                merged[-1][1] = max(merged[-1][1], b_)
            else:
                merged.append([a_, b_])
        return merged

    res = {"note": "แนวคลองไม่เป็นทางการ (My Maps) · ช่วงนครนายก กม.38.6–73.2 · ทั้งคลองใหม่ กม.0–135.655 · พื้นที่ ตร.กม. (1 ตร.กม. = 625 ไร่) · "
                   "ข้อมูลจาก 3 แนวคลองอยู่ในทั้ง 3 ลุ่มน้ำนี้ทั้งหมด (ตรวจกับขอบเขต 22 ลุ่มน้ำของ สทนช. — ไม่มีลุ่มน้ำชายฝั่งทะเลตะวันออกอยู่บนแนว)",
           "nn_reach_len_km": round(sub["nn"]["len_km"], 1), "all_len_km": round(sub["all"]["len_km"], 1),
           "corridor_200m_km2": {k: round(v["corr"].area / 1e6, 2) for k, v in sub.items()}, "layers": {}}
    for k, label in LAYERS.items():
        per = {}
        allp = []
        for bname, d in BASINS:
            f = d / f"{k}.json"
            if not f.exists():
                continue
            polys, total = decode_topo(f, bbox)
            if not polys:
                per[bname] = {"n_polygons_near": 0, "n_polygons_total": total}
                continue
            from shapely.validation import make_valid
            g = unary_union([make_valid(to_m(p)).buffer(0) for p in polys])
            allp.append(g)
            per[bname] = {"n_polygons_near": len(polys), "n_polygons_total": total,
                          "cross_all_km": round(sub["all"]["line"].intersection(g).length / 1000, 2)}
        if not allp:
            continue
        u = unary_union(allp)
        rec = {"label": label, "per_basin": per}
        for rk in ("nn", "all"):
            ln, corr = sub[rk]["line"], sub[rk]["corr"]
            rec[rk] = {"cross_km": round(ln.intersection(u).length / 1000, 2),
                       "corridor_share_pct": round(corr.intersection(u).area / corr.area * 100, 1),
                       "km_intervals": intervals(ln, u)}
        # คงชื่อฟิลด์เดิมของช่วงนครนายก เพื่อให้ตัวสร้างรายงานเดิมใช้ได้
        rec["line_crosses_length_km"] = rec["nn"]["cross_km"]
        rec["corridor_share_pct"] = rec["nn"]["corridor_share_pct"]
        rec["km_intervals"] = rec["nn"]["km_intervals"]
        rec["in_band5km_km2"] = round(sub["nn"]["line"].buffer(5000).intersection(u).area / 1e6, 2)
        rec["n_polygons"] = sum(v.get("n_polygons_near", 0) for v in per.values())
        res["layers"][k] = rec
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in res["layers"].items():
        print(f"{k:18s} NN cross={v['nn']['cross_km']:5.2f} km share={v['nn']['corridor_share_pct']:5.1f}% {v['nn']['km_intervals']} | "
              f"ALL cross={v['all']['cross_km']:6.2f} km share={v['all']['corridor_share_pct']:5.1f}% n_iv={len(v['all']['km_intervals'])}")


if __name__ == "__main__":
    main()
