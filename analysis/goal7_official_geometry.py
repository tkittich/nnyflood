"""เป้าหมาย 7 — รวมตัวเลขมิติทางการของคลองเจ้าพระยา 2 (รูปตัด · ระดับตามยาว · อาคาร · แนวคลอง) เป็นไฟล์เดียวสำหรับสร้างแบบจำลอง 3 มิติ

ลำดับความเชื่อถือ: ตัวเลขที่รายงานผลกระทบสิ่งแวดล้อมพิมพ์ไว้ (ตารางรูปตัด · ตาราง 2.3.2-3 · ค่ากำกับบนรูป 2.3.2-9) ชนะค่าที่คำนวณย้อน
ทุกค่าติดป้าย official (ตารางพิมพ์) · figure (อ่านจากรูปตามยาว ±0.2 ม.) · derived (คำนวณจากค่าทางการด้วยสูตรที่ตรงกับป้ายบนรูป) · assumed (ไม่มีในรายงาน — แสดงเป็นข้อสมมติ ไม่ใช่ตัวเลขทางการ)
แนวคลอง (พิกัด) ประมาณจากหมุด กม. ในแผนที่ KML ของโครงการ: ตัดหมุดที่กระโดดออกนอกแนว · กม.0–4 ต่อเส้นตรงถอยหลังจากแนวหลัก (หมุดช่วงนี้ไม่ต่อเนื่อง) · ไม่ใช่แนวกึ่งกลางตามแบบก่อสร้าง
ไม่มีในรายงาน (จึงเป็นข้อสมมติเมื่อสร้างแบบจำลอง): ระดับท้องไซฟอน · ความสูงสะพาน · รูปร่างตอม่อ

รัน: python analysis/goal7_official_geometry.py
ผลลัพธ์: analysis/goal7/official_geometry.json
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

import numpy as np
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
from goal7_source_constants import record  # noqa: E402  (reuse-first: ค่าคงที่ที่มีแหล่งอ้างอิง)

D32 = ROOT / "data/32_goal7_chaophraya2/derived"
OUT = ROOT / "analysis/goal7/official_geometry.json"
CANON = ROOT / "analysis/goal7/canonical.json"
STRUCTS = ROOT / "analysis/goal7/eia_structs.json"
STEP_KM = 0.5
L_END = 135.9
FREEBOARD_M = 1.5          # ระยะเผื่อพ้นน้ำ (ค่ากำกับบนรูป 2.3.2-9: สันคัน = ระดับน้ำ + 1.5)
TO_UTM = Transformer.from_crs(4326, 32647, always_xy=True)
TO_WGS = Transformer.from_crs(32647, 4326, always_xy=True)


def clean_alignment() -> tuple[np.ndarray, dict]:
    """คืนอาร์เรย์ (km, x, y) เมตร UTM 47N ทุก STEP_KM กม. จากหมุด กม. ที่ทำความสะอาดแล้ว"""
    feats = json.loads((D32 / "km_markers.geojson").read_text(encoding="utf-8"))["features"]
    g = collections.defaultdict(list)
    for f in feats:
        g[f["properties"]["km"]].append(TO_UTM.transform(*f["geometry"]["coordinates"]))
    kms = sorted(g)
    pts = {km: np.mean(v, axis=0) if len(v) == 1 else None for km, v in g.items()}
    for km in kms:   # หมุดซ้ำ → เลือกอันที่ใกล้จุดกลางของเพื่อนบ้านที่สุด
        if pts[km] is None:
            prev = max((x for x in kms if x < km and pts[x] is not None), default=None)
            nxt = min((x for x in kms if x > km and pts[x] is not None), default=None)
            ref = (pts[prev] + pts[nxt]) / 2 if prev is not None and nxt is not None else pts[prev if prev is not None else nxt]
            pts[km] = min(g[km], key=lambda p: np.hypot(p[0] - ref[0], p[1] - ref[1]))
    a = np.array([(km, *pts[km]) for km in kms])
    # ตัดหมุดกระโดด: ระยะถึงเพื่อนบ้านทั้งสองข้างต่างจาก Δกม. เกิน 40% (ใช้เฉพาะ กม. ≥ 4 ซึ่งเป็นแนวหลัก)
    keep = [True] * len(a)
    removed = []
    for i in range(1, len(a) - 1):
        if a[i, 0] < 4.0:
            continue
        dl = np.hypot(*(a[i, 1:] - a[i - 1, 1:])) / ((a[i, 0] - a[i - 1, 0]) * 1000)
        dr = np.hypot(*(a[i + 1, 1:] - a[i, 1:])) / ((a[i + 1, 0] - a[i, 0]) * 1000)
        if abs(dl - 1) > 0.4 and abs(dr - 1) > 0.4:
            keep[i] = False
            removed.append(float(a[i, 0]))
    main = a[[i for i in range(len(a)) if keep[i] and a[i, 0] >= 4.0]]
    # ทำให้เรียบ (เฉลี่ยเคลื่อนที่ 5 หมุด คงปลาย)
    sm = main.copy()
    for j in (1, 2):
        sm[:, j] = np.convolve(np.pad(main[:, j], 2, mode="edge"), np.ones(5) / 5, mode="valid")
    sm[0], sm[-1] = main[0], main[-1]
    # ต่อถอยหลัง กม.0–4 ด้วยเส้นตรงตามทิศของ 2 กม.แรกของแนวหลัก
    d0 = sm[min(2, len(sm) - 1), 1:] - sm[0, 1:]
    u0 = d0 / np.hypot(*d0)
    back = np.array([(k, *(sm[0, 1:] - u0 * (sm[0, 0] - k) * 1000)) for k in np.arange(0.0, sm[0, 0], 0.5)])
    full = np.vstack([back, sm])
    # สถานีเพิ่ม กม.22.999 เพื่อให้เห็นขั้นท้องคลองหน้าประตู กม.23 เป็นขั้นชัน (ค่ากำกับรูป 2.3.2-9: ผิวน้ำ 6.45 → 5.95 ม.รทก.)
    grid = np.array(sorted(set(np.round(np.arange(0.0, L_END + 1e-9, STEP_KM), 3).tolist()) | {22.999}))
    gx = np.interp(grid, full[:, 0], full[:, 1])
    gy = np.interp(grid, full[:, 0], full[:, 2])
    info = {"pins": len(kms), "removed_outlier_km": removed, "extrapolated_km": [0.0, float(sm[0, 0])], "extrapolation_note": "หมุด กม.0–3.5 อยู่คนละสายกับ กม.4 ขึ้นไป (ห่าง ~4 กม.) จึงต่อเส้นตรง"}
    return np.column_stack([grid, gx, gy]), info


def longitudinal_profile(km: float, ground_pts: list[tuple[float, float]]) -> dict:
    """ระดับ ม.รทก. ที่ กม. นั้น: ท้องคลอง/ผิวน้ำ/สันคัน (ทางการ-อนุมานจากค่ากำกับรูป) + พื้นดินเดิม (อ่านจากรูป)"""
    ground = float(np.interp(km, [p[0] for p in ground_pts], [p[1] for p in ground_pts]))
    if km < 23.0:
        # ช่วง 1: ท้องคลองยึดค่ากำกับ กม.0.15 (+1.75) และ กม.22.9 (ผิวน้ำ 6.45 − ลึก 7 = −0.55) → ลาด ~1:9,900 ตรงกับตาราง 1:10,000
        bed = 1.75 + (-0.55 - 1.75) * (km - 0.15) / (22.9 - 0.15)
        water = bed + 7.0
    elif km <= 134.0:
        bed = -1.05 - (km - 23.0) / 25.0                          # ลาดท้อง 1:25,000 ตามตารางรูปตัด
        water = bed + 7.0
    else:
        t = (km - 134.0) / (L_END - 134.0)
        bed = -5.504 + (5.504 + 0.04) * t                          # ท้องยกขึ้นจนปลายคลอง (ตาราง: ลาด 1:-342.857)
        water = 1.498 + (2.5 - 1.498) * t                          # ระดับน้ำปลายคลอง: 1.498 (กม.134) → 2.5 (น้ำหนุน)
    crest = water + FREEBOARD_M if km <= 134.0 else 3.0
    return {"ground": round(ground, 2), "bed": round(bed, 2), "water": round(water, 2), "crest": round(crest, 2)}


def parse_structs() -> list[dict]:
    rows = json.loads(STRUCTS.read_text(encoding="utf-8"))["versions"]["2569"]["rows"]
    out = []
    num = r"([\d.]+)"
    for r in rows:
        raw, o = r["raw"], {"no": r["no"], "km": r["km"], "kind": r["kind"], "name": r["name"], "lock": r.get("lock", False), "basis": "official (ตาราง 2.3.2-3)"}
        if r["kind"] == "road_bridge":
            w = re.search(r"สะพานรถยนต์\s*\|\s*กว้าง\s*" + num + r"\s*ม\.\s*ยาว\s*" + num, raw)
            o["deck_width_m"], o["span_m"] = (float(w[1]), float(w[2])) if w else (None, None)
            lane = re.search(r"2 ช่องจราจร กว้าง 2 - ([\d.]+) ม\. ไหล่ทาง 2 - ([\d.]+)", raw)
            o["lane_m"], o["shoulder_m"] = (float(lane[1]), float(lane[2])) if lane else (3.5, 1.5)
        elif r["kind"] == "rail_bridge":
            o["spans_m"] = [float(x) for x in re.findall(r"ยาว\s*" + num + r"\s*ม", raw)]
        elif r["kind"] == "gate":
            g = re.search(r"บ[าา้]*น?โค้ง\s*(\d+)\s*-\s*[*□]?\s*" + num + r"\s*x\s*" + num, raw)
            if g:
                o["bays"], o["bay_width_m"], o["bay_height_m"] = int(g[1]), float(g[2]), float(g[3])
        elif r["kind"] == "aqueduct":
            a = re.search(r"กว้าง\s*" + num + r"\s*ม\.\s*ความลึกน้ำ\s*" + num + r"\s*ม\.\s*ยาว\s*" + num, raw)
            if a:
                o["trough_width_m"], o["water_depth_m"], o["length_m"] = float(a[1]), float(a[2]), float(a[3])
            bw = re.search(r"ท้องคลองกว้าง\s*" + num, raw)
            o["canal_bed_width_m"] = float(bw[1]) if bw else None
        elif r["kind"] == "inlet":
            i = re.search(r"(\d+)\s*-\s*□\s*" + num + r"\s*x\s*" + num + r"\s*x\s*" + num, raw)
            if i:
                o["n"], o["w_m"], o["h_m"], o["len_m"] = int(i[1]), float(i[2]), float(i[3]), float(i[4])
        else:
            for k in ("canal_w", "sip_n", "sip_w", "sip_h", "sip_len", "cul_n", "cul_w", "cul_h"):
                if r.get(k) is not None:
                    o[k] = r[k]
            cl = re.search(r"ท่อระบายน้ำ\s*\d+\s*-\s*□\s*[\d.]+\s*x\s*[\d.]+\s*x\s*" + num, raw)
            if cl:
                o["cul_len"] = float(cl[1])
        out.append(o)
    return out


def main() -> None:
    table = record("eia_section_table")["value"]
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    ground_pts = [tuple(p) for p in canon["eia_profile"]["ground_readings"]]
    al, info = clean_alignment()
    # ทิศแนว (องศา จากแกน x ทวนเข็ม) หาจากผลต่างกลาง
    dx, dy = np.gradient(al[:, 1]), np.gradient(al[:, 2])
    head = np.degrees(np.arctan2(dy, dx))
    stations = []
    for i, (km, x, y) in enumerate(al):
        lon, lat = TO_WGS.transform(float(x), float(y))
        stations.append({"km": float(km), "x": round(float(x), 1), "y": round(float(y), 1), "heading_deg": round(float(head[i]), 2), "lon": round(lon, 6), "lat": round(lat, 6),
                         **longitudinal_profile(float(km), ground_pts)})
    structs = parse_structs()
    for s in structs:
        s["x"] = round(float(np.interp(s["km"], al[:, 0], al[:, 1])), 1)
        s["y"] = round(float(np.interp(s["km"], al[:, 0], al[:, 2])), 1)
        s["heading_deg"] = round(float(np.interp(s["km"], al[:, 0], head)), 2)
    out = {
        "_doc": __doc__.split("\n\n")[0] + " · " + __doc__.split("\n\n")[1].replace("\n", " "),
        "section_table": table,
        "profile_rules": {"reach1_bed": "เส้นตรงระหว่างค่ากำกับบนรูป กม.0.15 (+1.75) และ กม.22.9 (ผิวน้ำ 6.45 − 7 = −0.55) · ที่ กม.23 ท้องคลองลดฉับพลันเป็น −1.05 (ขั้นหน้าประตู 0.5 ม.)", "reach2_bed": "−1.05 − (กม.−23)/25 ม. (ลาด 1:25,000)", "water": "ท้อง + 7.0 ม. (กม.0–134)", "crest": "ผิวน้ำ + 1.5 ม. (กม.0–134)",
                          "reach3": "ท้องยกจาก −5.504 ไปปลายคลอง · ผิวน้ำ 1.498→2.5 (น้ำหนุน) · สันคัน 3.0 (ค่ากำกับบนรูป กม.134)", "ground": "ค่าอ่านจากเส้นระดับดินธรรมชาติในรูป 2.3.2-9 (±0.2 ม.)", "source": canon["eia_profile"]["src"]},
        "alignment": {"crs": "EPSG:32647 (UTM 47N) เมตร", "step_km": STEP_KM, **info},
        "stations": stations,
        "structures": structs,
        "assumptions_for_model": ["ระดับท้องไซฟอน (ไม่มีในตาราง 2.3.2-3)", "ความสูงใต้ท้องสะพาน/ตอม่อ (ไม่มีในตาราง)", "แนวคลองจากหมุด กม. ไม่ใช่แนวกึ่งกลางตามแบบ", "ความกว้างเขตทาง (RL/RR) ใช้ตามตารางรูปตัด"],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = collections.Counter(s["kind"] for s in structs)
    print("stations", len(stations), "structs", len(structs), dict(kinds), "removed pins", info["removed_outlier_km"])
    miss = [s["no"] for s in structs if (s["kind"] == "road_bridge" and s.get("span_m") is None) or (s["kind"] == "gate" and "bays" not in s) or (s["kind"] == "aqueduct" and "trough_width_m" not in s)]
    print("missing parses", miss)


if __name__ == "__main__":
    main()
