"""วัดระยะตามลำน้ำนครนายก Ny.1B ถึง Ny.7 จากชั้นเส้นลำน้ำของมิตรเอิร์ธ (R7-23)

กติกาตั้งก่อนดูผล: docs/REACH_LENGTH_PREREG.md — ผลเป็นค่าประมาณจากชั้นเส้น ไม่ใช่ระยะสายทางทางการ
รัน: python analysis/goal7_reach_length.py
ผลลัพธ์: analysis/goal7/reach_length.json
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
from pyproj import Transformer
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import substring

ROOT = Path(__file__).resolve().parent.parent
SHP = ROOT / "data/10_mitrearth_gis/extracted_full/18 Major River.shp"
NODES = ROOT / "analysis/goal6/network_nodes.json"
OUT = ROOT / "analysis/goal7/reach_length.json"
RIVER_NAME = "แม่น้ำนครนายก"
TOLS_M = (10.0, 30.0, 100.0)
HEADLINE_TOL = 30.0
MAX_SNAP_M = 500.0
USED_REACH_KM = 18.3          # ระยะที่ใช้ในแบบจำลองมาแต่เดิม (ไม่มีที่มาที่ตรวจได้)


def _fix(s):
    """ชื่อใน dbf ถูกอ่านเป็น latin-1 เพี้ยน — แปลงกลับเป็นไทย"""
    return s.encode("latin1", errors="ignore").decode("utf-8", errors="ignore") if isinstance(s, str) else s


def load_lines(only_use1: bool):
    g = gpd.read_file(SHP)
    g["name"] = g["str_name_t"].map(_fix)
    g = g[g["name"] == RIVER_NAME]
    if only_use1:
        g = g[g["hy_use"].astype(int) == 1]
    tr = Transformer.from_crs(4326, 32647, always_xy=True)
    lines = []
    for geom in g.geometry:
        parts = list(geom.geoms) if isinstance(geom, MultiLineString) else [geom]
        for p in parts:
            xs, ys = tr.transform(*np.asarray(p.coords)[:, :2].T)
            lines.append(LineString(np.c_[xs, ys]))
    return lines, tr


def station_points(tr):
    n = json.loads(NODES.read_text(encoding="utf-8"))
    pts = {}
    for r in n["gauges"]:
        if r["code"] in ("Ny.1B", "Ny.7"):
            pts[r["code"]] = Point(*tr.transform(r["lon"], r["lat"]))
    return pts


def split_at(lines, pt):
    """ตัดเส้นที่ใกล้จุดที่สุดที่จุดฉาย · คืน (เส้นใหม่, พิกัดจุดบนเส้น, ระยะจุดถึงเส้น)"""
    d = [ln.distance(pt) for ln in lines]
    i = int(np.argmin(d))
    ln = lines[i]
    s = ln.project(pt)
    on = ln.interpolate(s)
    new = [x for k, x in enumerate(lines) if k != i]
    for a, b in ((0.0, s), (s, ln.length)):
        if b - a > 1e-6:
            new.append(substring(ln, a, b))
    return new, (on.x, on.y), float(d[i])


def path_length(lines, a_xy, b_xy, tol):
    ends = []
    for ln in lines:
        ends.append(ln.coords[0][:2])
        ends.append(ln.coords[-1][:2])
    ends = np.array(ends)
    tree = cKDTree(ends)
    pairs = tree.query_pairs(tol, output_type="ndarray")
    m = len(ends)
    adj = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(m, m)) if len(pairs) else coo_matrix((m, m))
    _, lab = connected_components(adj, directed=False)
    nn = lab.max() + 1
    rows, cols, w = [], [], []
    for k, ln in enumerate(lines):
        u, v = lab[2 * k], lab[2 * k + 1]
        if u != v:
            rows += [u, v]
            cols += [v, u]
            w += [ln.length, ln.length]
    g = coo_matrix((w, (rows, cols)), shape=(nn, nn)).tocsr()
    ia = int(lab[int(np.argmin(np.hypot(*(ends - a_xy).T)))])
    ib = int(lab[int(np.argmin(np.hypot(*(ends - b_xy).T)))])
    d = dijkstra(g, directed=False, indices=ia)[ib]
    return None if not np.isfinite(d) else float(d)


def measure(only_use1: bool, tol: float):
    lines, tr = load_lines(only_use1)
    pts = station_points(tr)
    lines, a_xy, da = split_at(lines, pts["Ny.1B"])
    lines, b_xy, db = split_at(lines, pts["Ny.7"])
    straight = pts["Ny.1B"].distance(pts["Ny.7"])
    L = path_length(lines, a_xy, b_xy, tol)
    return {"hy_use_only_1": only_use1, "tol_m": tol, "n_segments": len(lines), "snap_ny1b_m": round(da), "snap_ny7_m": round(db),
            "path_km": None if L is None else round(L / 1000, 2), "straight_km": round(straight / 1000, 2),
            "sinuosity": None if L is None else round(L / straight, 2)}


def main() -> None:
    rows = [measure(u, t) for u in (False, True) for t in TOLS_M]
    ok = [r for r in rows if r["path_km"] is not None and max(r["snap_ny1b_m"], r["snap_ny7_m"]) <= MAX_SNAP_M]
    res = {"rule": "docs/REACH_LENGTH_PREREG.md", "source": "ชั้น 18 Major River (มิตรเอิร์ธ) · ชื่อ " + RIVER_NAME, "cases": rows,
           "used_reach_km": USED_REACH_KM, "measurable": bool(ok)}
    if ok:
        lo, hi = min(r["path_km"] for r in ok), max(r["path_km"] for r in ok)
        head = next((r for r in ok if not r["hy_use_only_1"] and r["tol_m"] == HEADLINE_TOL), ok[0])
        mid = round((lo + hi) / 2, 2)
        res.update({"range_km": [lo, hi], "central_km": mid, "headline_case": head,
                    "diff_vs_used_pct": round(100 * (mid - USED_REACH_KM) / USED_REACH_KM, 1),
                    "consistent_within_20pct": abs(mid - USED_REACH_KM) / USED_REACH_KM <= 0.20})
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        print(r)
    print({k: v for k, v in res.items() if k not in ("cases", "headline_case")})


if __name__ == "__main__":
    main()
