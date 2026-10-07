# จับคู่จุดหักขอบจังหวัด: 3 GCP จากการอ่าน crop (_gc_town3) ↔ OSM ring แล้ว fit affine + คะแนน chamfer
import json
from pathlib import Path

import numpy as np
import cv2

ROOT = Path(__file__).resolve().parent.parent   # อิง __file__ ไม่ใช่ cwd
im = cv2.imread(str(ROOT / "data" / "08_dem_topography" / "satellite_gistda_28sep02oct"
                   / "S__5980182_gistda_28sep02oct.jpg"))
x0, x1, y0, y1 = 1610, 7500, 410, 4600
sub = im[y0:y1, x0:x1]
b, g, r = sub[..., 0].astype(int), sub[..., 1].astype(int), sub[..., 2].astype(int)
dark = ((b < 110) & (g < 110) & (r < 110)).astype(np.uint8)
k_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
k_h = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
lines = cv2.morphologyEx(dark, cv2.MORPH_OPEN, k_v) | cv2.morphologyEx(dark, cv2.MORPH_OPEN, k_h)
dist = cv2.distanceTransform((lines == 0).astype(np.uint8), cv2.DIST_L2, 3).astype(np.float32)

# GCP pixel จากการอ่าน crop (2300-3100, 2200-3000)
G = np.array([(2620, 2695), (2830, 2490), (2620, 3000)], float)   # A, B, C (px)
# รูปทรงสามเหลี่ยมของ GCP
vAB = G[1] - G[0]; vAC = G[2] - G[0]
r_AB = np.hypot(*vAB); r_AC = np.hypot(*vAC)
print(f"GCP: |AB|={r_AB:.0f}px |AC|={r_AC:.0f}px ratio={r_AC/r_AB:.2f}")

bnd = json.load(open(ROOT / "data" / "13_sentinel1_copernicus" / "derived" / "osm_nakhonnayok_boundary.json", encoding="utf-8"))["geojson"]
ring = np.array(bnd["coordinates"][0] if bnd["type"] == "Polygon" else bnd["coordinates"][0][0])

# จุดหักใน ring (ภูมิภาคขอบตะวันออกเฉียงใต้)
def corners(ring, ang_min=25):
    out = []
    n = len(ring)
    for i in range(n):
        p_prev, p_c, p_next = ring[(i - 4) % n], ring[i], ring[(i + 4) % n]
        v1 = p_c - p_prev; v2 = p_next - p_c
        a1 = np.degrees(np.arctan2(v1[1], v1[0])); a2 = np.degrees(np.arctan2(v2[1], v2[0]))
        d = abs((a2 - a1 + 180) % 360 - 180)
        if d > ang_min:
            out.append((i, p_c, d))
    return out

lat_mid = 14.15
cand = [c for c in corners(ring, 28) if 101.08 <= c[1][0] <= 101.32 and 14.00 <= c[1][1] <= 14.28]
print("จุดหักผู้สมัคร:", len(cand))

def fit_affine(src, dst):
    A = []
    for (u, v), (x, y) in zip(src, dst):
        A.append([u, v, 1, 0, 0, 0]); A.append([0, 0, 0, u, v, 1])
    A = np.array(A); bvec = np.array([p[0] for p in dst] + [p[1] for p in dst])
    coef, *_ = np.linalg.lstsq(A, bvec, rcond=None)
    return coef

def apply(coef, lon, lat):
    x = coef[0]*lon + coef[1]*lat + coef[2]
    y = coef[3]*lon + coef[4]*lat + coef[5]
    return x, y

MERC = 1.0 / np.cos(np.radians(14.24))
best = None
idxs = [c[0] for c in cand]
pts = {c[0]: c[1] for c in cand}
for ia in idxs:
    for ib in idxs:
        if ib == ia: continue
        pa, pb = pts[ia], pts[ib]
        # ระยะ |AB| ในองศา (คิด metric)
        dab = np.hypot((pb[0]-pa[0])*111.32*np.cos(np.radians(14.24)), (pb[1]-pa[1])*110.574)
        sx_ab = r_AB / dab if dab > 0 else 0
        if not (6500 < sx_ab < 11000): continue        # สเกล px/°lon ที่สมเหตุสมผล
        for ic in idxs:
            if ic in (ia, ib): continue
            pc = pts[ic]
            dac = np.hypot((pc[0]-pa[0])*111.32*np.cos(np.radians(14.24)), (pc[1]-pa[1])*110.574)
            if abs(dac/r_AB - r_AC/r_AB) > 0.12: continue
            coef = fit_affine([pa, pb, pc], G)
            # ตรวจสอบ: สเกล + ทิศ
            sx = coef[0]; sy = coef[4]
            if sx <= 0 or sy >= 0: continue
            if not (7000 < sx < 11000): continue
            if abs(abs(sy)/abs(sx) - MERC) > 0.06: continue
            lonl = ring[:, 0]; latl = ring[:, 1]
            px = coef[0]*lonl + coef[1]*latl + coef[2]
            py = coef[3]*lonl + coef[4]*latl + coef[5]
            ok = (px >= 0) & (px < sub.shape[1]) & (py >= 0) & (py < sub.shape[0])
            if ok.sum() < 300: continue
            d = dist[py[ok].astype(int), px[ok].astype(int)]
            score = float(np.median(d))
            if best is None or score < best[0]:
                best = (score, coef, (ia, ib, ic), ok.mean())
print("ผู้ชนะ:", round(best[0], 1), "px median | จุดหัก", best[2], "| ครอบ ring", round(best[3]*100), "%")
coef = best[1]
sx = coef[0]; sy = coef[4]
print(f"สเกล: {111320/sx:.2f} ม./px lon · {110574/abs(sy):.2f} ม./px lat")
json.dump({"coef": [float(c) for c in coef], "corners_osm_idx": best[2],
           "median_px": best[0], "gcp_px": G.tolist()},
          open(ROOT / "data" / "08_dem_topography" / "satellite_gistda_28sep02oct" / "_georef_fit.json", "w"), indent=1)
print("saved _georef_fit.json")
