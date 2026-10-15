"""เป้าหมาย 7 — ทำความสะอาดแนวคลองเจ้าพระยา2 จาก My Maps (ผู้ใช้สร้าง)

อินพุต: data/32_goal7_chaophraya2/raw/*_mymaps_chaophraya2.kml
 - LineString เดียวปิดวง = ขอบ 2 ฝั่งต่อกัน (รวมคลองเดิมชัยนาท–ป่าสัก) · หมุด กม. 141 จุด
เอาต์พุต (derived/): centerline.geojson · corridor.geojson · km_markers.geojson · alignment_qa.json
วิธี: แยกวงที่จุดเหนือสุด/ใต้สุด -> 2 ฝั่ง -> เส้นกลาง = จุดกึ่งกลางคู่ใกล้สุด -> ความกว้าง = ระยะคู่
ไม่ฝังตัวตรวจ — ตัวเลข QA เขียนลง JSON ให้ขั้นตอนแยกอ่าน
"""
import json, math, re
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/32_goal7_chaophraya2"
KML = next((OUT / "raw").glob("*_mymaps_chaophraya2.kml"))
NS = {"k": "http://www.opengis.net/kml/2.2"}
LAT0, LON0 = 14.2, 100.9
KX = 111.32e3 * math.cos(math.radians(LAT0)); KY = 110.57e3

def to_m(lon, lat): return np.c_[(np.asarray(lon) - LON0) * KX, (np.asarray(lat) - LAT0) * KY]
def to_ll(xy): return np.c_[xy[:, 0] / KX + LON0, xy[:, 1] / KY + LAT0]

def read_kml():
    ring, marks = None, []
    for p in ET.parse(KML).getroot().iterfind(".//k:Placemark", NS):
        c = [tuple(map(float, s.split(",")[:2])) for s in p.find(".//k:coordinates", NS).text.split()]
        if p.find(".//k:LineString", NS) is not None:
            ring = np.array(c)
        else:
            n = p.find("k:name", NS).text or ""
            m = re.match(r"กม\.(\d+)\+(\d+)", n)
            if m: marks.append((int(m[1]) + int(m[2]) / 1000, c[0][0], c[0][1]))
    return ring, sorted(marks)

def dedupe(xy):
    keep = [0]
    for i in range(1, len(xy)):
        if np.hypot(*(xy[i] - xy[keep[-1]])) > 1.0: keep.append(i)
    return xy[keep]

def resample(xy, step=100.0):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    s = np.arange(0, d[-1], step)
    return np.c_[np.interp(s, d, xy[:, 0]), np.interp(s, d, xy[:, 1])]

def main():
    ring_ll, marks = read_kml()
    xy = to_m(ring_ll[:, 0], ring_ll[:, 1])
    ia, ib = int(np.argmax(xy[:, 1])), int(np.argmin(xy[:, 1]))  # ชัยนาท / อ่าวไทย
    lo, hi = sorted((ia, ib))
    # ring = start..lo (c0) , lo..hi (c1) , hi..end (c2): c1 = ฝั่ง Y ; c2+c0 = ฝั่ง X
    c0, c1, c2 = xy[:lo + 1], xy[lo:hi + 1], xy[hi:]
    bank_y = c1; bank_x = np.vstack([c2, c0]) if ib > ia else np.vstack([c2, c0])
    # ให้ทั้งสองฝั่งเรียงจากอ่าวไทยไปชัยนาท
    def orient(b): return b if b[0, 1] < b[-1, 1] else b[::-1]
    bank_x, bank_y = orient(dedupe(bank_x)), orient(dedupe(bank_y))
    ry = resample(bank_y); rx = resample(bank_x)
    tx = cKDTree(rx); dy, ix = tx.query(ry)
    mid = (ry + rx[ix]) / 2
    ty = cKDTree(ry); dx, iy = ty.query(rx)
    # เส้นกลาง: เรียงตามระยะบนฝั่ง Y แล้วเกลี่ยด้วยค่าเฉลี่ยเลื่อน 5 จุด
    k = 5; pad = np.pad(mid, ((k // 2, k // 2), (0, 0)), mode="edge")
    sm = np.c_[np.convolve(pad[:, 0], np.ones(k) / k, "valid"), np.convolve(pad[:, 1], np.ones(k) / k, "valid")]
    center = LineString(sm)
    # chainage ตามหมุด กม. (กม.0 = หัวงานป่าสัก ... กม.135 = อ่าวไทย)
    mk = np.array([(m[0], *to_m([m[1]], [m[2]])[0]) for m in marks])
    mk_line = LineString(mk[:, 1:])
    seg_s = np.array([center.project(__import__("shapely").geometry.Point(*p)) for p in mk[:, 1:]])
    off = np.array([center.distance(__import__("shapely").geometry.Point(*p)) for p in mk[:, 1:]])
    ring_poly = Polygon(xy)
    qa = {
        "ring_points": int(len(ring_ll)), "ring_closed": bool(np.allclose(ring_ll[0], ring_ll[-1])),
        "unique_points": int(len({tuple(r) for r in ring_ll})),
        "bank_len_km": [round(LineString(bank_x).length / 1e3, 1), round(LineString(bank_y).length / 1e3, 1)],
        "centerline_len_km": round(center.length / 1e3, 1),
        "centerline_pts": int(len(sm)),
        "width_m": {"median": round(float(np.median(dy)), 0), "p10": round(float(np.percentile(dy, 10)), 0),
                    "p90": round(float(np.percentile(dy, 90)), 0), "max": round(float(dy.max()), 0)},
        "ring_area_rai": round(Polygon(xy).buffer(0).area / 1600, 0),
        "markers": len(marks), "marker_km_min": marks[0][0], "marker_km_max": marks[-1][0],
        "marker_offset_from_centerline_m": {"median": round(float(np.median(off)), 0), "max": round(float(off.max()), 0)},
        "extent": {"lat": [float(ring_ll[:, 1].min()), float(ring_ll[:, 1].max())],
                   "lon": [float(ring_ll[:, 0].min()), float(ring_ll[:, 0].max())]},
    }
    # km จากหมุดตามเส้นกลาง: เทียบความยาวเส้นกลางกับ กม. ที่หมุดบอก
    ok = off < 3000
    slope = np.polyfit(seg_s[ok] / 1e3, mk[ok, 0], 1)
    qa["km_vs_centerline_fit"] = {"slope_marker_km_per_centerline_km": round(float(slope[0]), 3),
                                  "intercept_km": round(float(slope[1]), 1), "n": int(ok.sum())}
    def gj(feats): return {"type": "FeatureCollection", "features": feats}
    ll = to_ll(sm)
    (OUT / "derived/centerline.geojson").write_text(json.dumps(gj([{
        "type": "Feature", "properties": {"name": "เส้นกลางแนวคลองเจ้าพระยา2 (ประมาณจากขอบ 2 ฝั่ง)", "from": "gulf", "to": "chainat"},
        "geometry": {"type": "LineString", "coordinates": ll.round(6).tolist()}}]), ensure_ascii=False))
    corridor = np.vstack([to_ll(rx), to_ll(ry)[::-1]])
    (OUT / "derived/corridor.geojson").write_text(json.dumps(gj([{
        "type": "Feature", "properties": {"name": "ขอบเขตแนว (2 ฝั่ง)", "width_median_m": qa["width_m"]["median"]},
        "geometry": {"type": "Polygon", "coordinates": [corridor.round(6).tolist() + [corridor[0].round(6).tolist()]]}}]), ensure_ascii=False))
    (OUT / "derived/km_markers.geojson").write_text(json.dumps(gj([{
        "type": "Feature", "properties": {"km": m[0]},
        "geometry": {"type": "Point", "coordinates": [m[1], m[2]]}} for m in marks]), ensure_ascii=False))
    (OUT / "derived/alignment_qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=1))
    print(json.dumps(qa, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
