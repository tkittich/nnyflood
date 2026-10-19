"""เป้าหมาย 7 — สร้างแบบจำลอง 3 มิติของคลองเจ้าพระยา 2 (ป่าสัก–อ่าวไทย กม.0–135.9) จากตัวเลขมิติทางการ ใช้เปิดใน SketchUp

เนื้อหาแบบจำลอง (ทุกชิ้นอ้างตัวเลขทางการจาก analysis/goal7/official_geometry.json): รูปตัดคลอง 3 ช่วง (ตารางรูปที่ 2.3.2-11: ท้องคลอง ลาดใน/นอก ทางเลียบ ถนนบนสัน)
· ระดับท้องคลอง/ผิวน้ำ/สันคัน/ดินเดิมตามยาว (รูป 2.3.2-9) · ประตูระบายน้ำ 5 แห่ง (บานโค้ง 4 ช่อง 12.5×6.0 ม.) · สะพานรถยนต์ 42 · สะพานรถไฟ 2
· สะพานน้ำ 7 · ท่อรับน้ำ 4 · อาคารเชื่อมจุดตัดคลอง 39 (ไซฟอน + ท่อระบายน้ำ + ลำคลองเดิม)
ข้อสมมติที่ไม่ใช่ตัวเลขทางการ (ระบุไว้ในไฟล์ผลลัพธ์): ระดับท้องไซฟอน · ความสูงสะพาน/ตอม่อ/ช่วงสะพานน้ำ · ตำแหน่งแนวคลองจากหมุด กม. · เขตทาง (RL/RR) วัดจากขอบบนตลิ่ง
ผลลัพธ์: report/models/chaophraya2.obj (+.mtl) · chaophraya2_sketchup.rb (รันใน SketchUp: Window > Ruby Console หรือ Extensions > Developer) · chaophraya2_viewer.html (ดูในเบราว์เซอร์ ปรับความสูงเกินจริงได้)
ข้อจำกัด: ยังไม่ได้ทดสอบ .rb ใน SketchUp จริง (ตรวจเฉพาะโครงสร้าง/เรขาคณิต) · มาตราส่วนจริง 1:1 — คลองยาว 135.9 กม. สูง 7 ม. จึงแบนมากเมื่อดูทั้งเส้น ใช้ตัวเลือกความสูงเกินจริงใน viewer หรือ VERT_EXAG ใน .rb

รัน: python analysis/goal7_build_3d_model.py [--vexag 1.0]
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GEOM = ROOT / "analysis/goal7/official_geometry.json"
OUTD = ROOT / "report/models"
TILE_KM = 10.0
ROW_MARGIN_M = 60.0       # พื้นดินรอบแนวที่วาดนอกตีนลาดนอก (ทัศนียภาพ)

MATERIALS = {   # ชื่อ: (R,G,B,alpha)
    "water": (0.20, 0.45, 0.80, 0.55), "earth_lining": (0.55, 0.42, 0.28, 1), "concrete_lining": (0.70, 0.70, 0.72, 1),
    "road": (0.22, 0.22, 0.24, 1), "embankment": (0.45, 0.52, 0.30, 1), "ground": (0.62, 0.70, 0.45, 1),
    "gate": (0.85, 0.35, 0.10, 1), "pier": (0.60, 0.60, 0.60, 1), "road_bridge": (0.80, 0.80, 0.82, 1), "rail_bridge": (0.35, 0.30, 0.30, 1),
    "aqueduct": (0.45, 0.65, 0.78, 1), "culvert": (0.10, 0.55, 0.55, 1), "existing_canal": (0.30, 0.55, 0.85, 0.8), "row_line": (0.95, 0.80, 0.10, 1),
    "sea": (0.15, 0.35, 0.65, 0.4),
}


class Frame:
    """แปลง (กม., ระยะข้าง u, ความสูง z) → พิกัดท้องถิ่น (ม.) โดยมีจุดกำเนิดที่สถานี กม.0 · u>0 = ฝั่งซ้ายมือเมื่อมองตามทิศน้ำไหล (ไปทางอ่าวไทย)"""

    def __init__(self, stations):
        self.km = np.array([s["km"] for s in stations])
        self.x = np.array([s["x"] for s in stations]) - stations[0]["x"]
        self.y = np.array([s["y"] for s in stations]) - stations[0]["y"]
        self.h = np.radians(np.unwrap(np.radians([s["heading_deg"] for s in stations])) * 180 / np.pi) if False else np.unwrap(np.radians([s["heading_deg"] for s in stations]))

    def at(self, km, u, z, vexag=1.0):
        h = float(np.interp(km, self.km, self.h))
        x, y = float(np.interp(km, self.km, self.x)), float(np.interp(km, self.km, self.y))
        # ทิศการไหล = ทิศที่ กม. เพิ่ม (ทิศ heading ของ gradient) · ปกติซ้าย = (-sin h, cos h)
        return (x - u * math.sin(h), y + u * math.cos(h), z * vexag)

    def heading(self, km):
        return float(np.interp(km, self.km, self.h))


class Mesh:
    def __init__(self):
        self.polys: dict[str, list[list[tuple]]] = defaultdict(list)

    def quad(self, mat, a, b, c, d):
        self.polys[mat].append([a, b, c, d])

    def tri(self, mat, a, b, c):
        self.polys[mat].append([a, b, c])

    def box(self, mat, fr: Frame, km, u0, u1, z0, z1, along_m, vexag):
        """กล่องตั้งฉากกับแนวคลอง: ยาวตามแนวคลอง along_m (ม.) กว้างตามขวาง u0..u1 สูง z0..z1 — อ้างจุดกึ่งกลาง กม."""
        h = fr.heading(km)
        cx, cy, _ = fr.at(km, 0.0, 0.0, 1.0)
        tx, ty = math.cos(h), math.sin(h)
        nx, ny = -math.sin(h), math.cos(h)
        a = along_m / 2.0

        def p(t, u, z):
            return (cx + tx * t + nx * u, cy + ty * t + ny * u, z * vexag)
        v = {(i, j, k): p((-a, a)[i], (u0, u1)[j], (z0, z1)[k]) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
        for f in (((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), ((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)), ((0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)),
                  ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)), ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)), ((1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0))):
            self.quad(mat, *[v[i] for i in f])

    def box_across(self, mat, fr, km, u0, u1, z0, z1, width_along_m, vexag):
        self.box(mat, fr, km, u0, u1, z0, z1, width_along_m, vexag)


def section_params(km, table):
    r = next((x for x in table["reaches"] if x["km"][0] <= km < x["km"][1]), table["reaches"][-1])
    if isinstance(r["B"], list):                       # ช่วงปลายคลอง: ท้องกว้างขึ้น 51 → 380
        t = (km - r["km"][0]) / (r["km"][1] - r["km"][0])
        bw = r["B"][0] + (r["B"][1] - r["B"][0]) * t
    else:
        bw = r["B"]
    return {"B": bw, "z_in": r["Z1"], "z_out": r["Z2"], "berm": r["BmL"], "road": r["TL"], "row": r["RL"], "reach": table["reaches"].index(r) + 1}


def inner_profile(sp, bed, water, crest):
    """จุด (u,z) ฝั่งขวา (u>0) จากท้อง → ผิวน้ำ → สันคัน มีทางเลียบ (เบิร์ม) กลางความลึกเมื่อตารางระบุ"""
    d, z, b = water - bed, sp["z_in"], sp["B"] / 2.0
    pts = [(b, bed)]
    hb = d / 2.0                                       # ทางเลียบ (เบิร์ม) กลางความลึก — ถ้าตารางระบุ 0 ม. ใส่จุดซ้ำเพื่อให้โครงจุดเท่ากันทุกช่วง
    pts += [(b + z * hb, bed + hb), (b + z * hb + sp["berm"], bed + hb)]
    off = sp["berm"]
    pts += [(b + z * d + off, water), (b + z * (crest - bed) + off, crest)]
    return pts


def strip(mesh, mat, ring_a, ring_b):
    for j in range(len(ring_a) - 1):
        q = (ring_a[j], ring_a[j + 1], ring_b[j + 1], ring_b[j])
        a = np.linalg.norm(np.cross(np.subtract(q[1], q[0]), np.subtract(q[3], q[0]))) + np.linalg.norm(np.cross(np.subtract(q[1], q[2]), np.subtract(q[3], q[2])))
        if a > 1e-4:
            mesh.quad(mat, *q)


def build(vexag: float):
    g = json.loads(GEOM.read_text(encoding="utf-8"))
    st, structs, table = g["stations"], g["structures"], g["section_table"]
    fr = Frame(st)
    mesh = Mesh()
    rings = []
    for s in st:
        sp = section_params(s["km"], table)
        bed, water, crest, ground = s["bed"], s["water"], s["crest"], s["ground"]
        ip = inner_profile(sp, bed, water, crest)                       # ฝั่งขวา (u>0)
        u_c, road = ip[-1][0], sp["road"]
        toe = u_c + road + sp["z_out"] * abs(crest - ground)
        right_inner = ip
        left_inner = [(-u, z) for u, z in ip]
        lining = list(reversed(left_inner)) + right_inner                # ซ้ายสันคัน → ท้อง → ขวาสันคัน
        # หมายเหตุ: ลำดับ = จากซ้ายไปขวา; จุดท้องซ้ายและขวามาจาก (b, bed)
        left_chain = list(reversed(left_inner))
        ring = {
            "lining": [fr.at(s["km"], u, z, vexag) for u, z in left_chain + right_inner],
            "water": [fr.at(s["km"], -ip[-2][0], water, vexag), fr.at(s["km"], ip[-2][0], water, vexag)],
            "road_l": [fr.at(s["km"], -u_c, crest, vexag), fr.at(s["km"], -(u_c + road), crest, vexag)],
            "road_r": [fr.at(s["km"], u_c, crest, vexag), fr.at(s["km"], u_c + road, crest, vexag)],
            "slope_l": [fr.at(s["km"], -(u_c + road), crest, vexag), fr.at(s["km"], -toe, ground, vexag)],
            "slope_r": [fr.at(s["km"], u_c + road, crest, vexag), fr.at(s["km"], toe, ground, vexag)],
            "ground_l": [fr.at(s["km"], -toe, ground, vexag), fr.at(s["km"], -(toe + ROW_MARGIN_M), ground, vexag)],
            "ground_r": [fr.at(s["km"], toe, ground, vexag), fr.at(s["km"], toe + ROW_MARGIN_M, ground, vexag)],
            "row_l": [fr.at(s["km"], -(u_c + sp["row"]), ground + 0.2, vexag), fr.at(s["km"], -(u_c + sp["row"] + 1.5), ground + 0.2, vexag)],
            "row_r": [fr.at(s["km"], u_c + sp["row"], ground + 0.2, vexag), fr.at(s["km"], u_c + sp["row"] + 1.5, ground + 0.2, vexag)],
            "reach": sp["reach"], "u_c": u_c, "toe": toe, "z_bed": bed, "z_crest": crest, "z_ground": ground, "z_water": water,
        }
        rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        lin_mat = "earth_lining" if a["reach"] == 1 else "concrete_lining"
        strip(mesh, lin_mat, a["lining"], b["lining"])
        strip(mesh, "water", a["water"], b["water"])
        for k, m in (("road_l", "road"), ("road_r", "road"), ("slope_l", "embankment"), ("slope_r", "embankment"), ("ground_l", "ground"), ("ground_r", "ground"), ("row_l", "row_line"), ("row_r", "row_line")):
            strip(mesh, m, a[k], b[k])
    # ---- อาคารตามแนวคลอง ----
    by_km = {round(s["km"], 3): s for s in st}

    def sect_at(km):
        i = int(np.argmin(np.abs(np.array([s["km"] for s in st]) - km)))
        return rings[i], st[i]
    for o in structs:
        km = o["km"]
        r, s = sect_at(km)
        u_c, bed, crest, ground, water = r["u_c"], r["z_bed"], r["z_crest"], r["z_ground"], r["z_water"]
        kind = o["kind"]
        if kind == "gate":
            bw, n = o.get("bay_width_m", 12.5), o.get("bays", 4)
            total = bw * n
            pier_w = 3.0                                                       # ข้อสมมติ: ความหนาตอม่อ
            for i in range(n + 1):
                u = -total / 2 + i * bw
                mesh.box("pier", fr, km, u - pier_w / 2, u + pier_w / 2, bed, crest + 4.0, 16.0, vexag)
            for i in range(n):
                u0 = -total / 2 + i * bw + pier_w / 2
                mesh.box("gate", fr, km, u0, u0 + bw - pier_w, bed, bed + o.get("bay_height_m", 6.0), 1.0, vexag)
            mesh.box("road_bridge", fr, km, -total / 2 - pier_w / 2, total / 2 + pier_w / 2, crest + 3.0, crest + 4.0, 7.0, vexag)   # ทางสัญจรบนประตู (ข้อสมมติ)
        elif kind == "road_bridge":
            span, w = o.get("span_m") or 100.0, o.get("deck_width_m") or 7.0
            mesh.box("road_bridge", fr, km, -span / 2, span / 2, crest, crest + 1.0, w, vexag)                                       # ท้องสะพานอยู่ระดับสันคัน (ข้อสมมติ)
            mesh.box("pier", fr, km, -span / 2 - 1.0, -span / 2 + 1.0, crest - 1.0, crest + 1.0, w, vexag)
            mesh.box("pier", fr, km, span / 2 - 1.0, span / 2 + 1.0, crest - 1.0, crest + 1.0, w, vexag)
        elif kind == "rail_bridge":
            span = max(o.get("spans_m") or [100.0])
            width = 5.0 * len(o.get("spans_m") or [1])                          # รางละ 5 ม. (ข้อสมมติ)
            mesh.box("rail_bridge", fr, km, -span / 2, span / 2, crest, crest + 1.5, width, vexag)
        elif kind == "aqueduct":
            length, tw, dep = o.get("length_m", 100.0), o.get("trough_width_m", 2.6), o.get("water_depth_m", 0.8)
            zc = crest + 3.0                                                    # ข้อสมมติ: รางสะพานน้ำสูงเหนือสันคัน 3 ม.
            mesh.box("aqueduct", fr, km, -length / 2, length / 2, zc, zc + dep + 0.3, tw + 0.6, vexag)
            mesh.box("pier", fr, km, -length / 2, -length / 2 + 1.0, crest, zc, tw + 0.6, vexag)
            mesh.box("pier", fr, km, length / 2 - 1.0, length / 2, crest, zc, tw + 0.6, vexag)
        elif kind == "inlet":
            n, w, h, ln = o.get("n", 1), o.get("w_m", 1.0), o.get("h_m", 1.0), o.get("len_m", 15.0)
            z0 = crest - 2.0
            mesh.box("culvert", fr, km, u_c, u_c + ln, z0, z0 + h, w, vexag)    # ท่อรับน้ำฝั่งซ้าย ลอดคันออกไปด้านนอก
        elif kind == "crossing":
            sw, sh, sl = o.get("sip_w"), o.get("sip_h"), o.get("sip_len")
            if sw:
                z1 = bed - 1.0                                                  # ข้อสมมติ: ท้องไซฟอน — บนสุดอยู่ใต้ท้องคลอง 1 ม.
                for q in range(int(o.get("sip_n", 1))):
                    off = (q - (o.get("sip_n", 1) - 1) / 2) * (sw + 1.0)
                    mesh.box("culvert", fr, km + off / 1000.0, -sl / 2, sl / 2, z1 - sh, z1, sw, vexag)
            if o.get("cul_w"):
                ln = o.get("cul_len", 15.0)
                zc = ground
                for side in (-1, 1):
                    mesh.box("culvert", fr, km, side * (r["toe"] - ln), side * r["toe"], zc, zc + o["cul_h"], o["cul_w"], vexag)
            if o.get("canal_w"):
                cw = o["canal_w"]
                for side in (-1, 1):
                    a0, a1 = side * r["toe"], side * (r["toe"] + ROW_MARGIN_M * 2)
                    mesh.box("existing_canal", fr, km, min(a0, a1), max(a0, a1), ground - 0.05, ground + 0.02, cw, vexag)
    # ทะเล (น้ำหนุนสูง +2.0) ปลายคลอง
    last = st[-1]
    mesh.box("sea", fr, last["km"] + 0.3, -450.0, 450.0, -1.0, 2.0, 600.0, vexag)
    return mesh, fr, g


def make_labels(g: dict, fr: Frame) -> list[dict]:
    """ป้ายกำกับตำแหน่งสำคัญ: ต้น/ปลายคลอง · ประตูระบายน้ำ · สะพานรถไฟ · ทางหลวง/ทางพิเศษ · ลำน้ำใหญ่ · สะพานน้ำ · จุดเปลี่ยนรูปตัด · ระดับน้ำ/ท้อง/สันคัน · กม.ทุก 10"""
    st = g["stations"]
    kmv = np.array([s["km"] for s in st])

    def lv(km):
        i = int(np.argmin(np.abs(kmv - km)))
        return st[i]
    out = []

    def add(km, text, kind, dz=0.0, u=0.0):
        s = lv(km)
        x, y, z = fr.at(km, u, 0.0)
        out.append({"km": round(km, 3), "x": round(x, 1), "y": round(y, 1), "z": round(s["crest"] + dz, 2), "text": text, "kind": kind})
    add(0.0, "กม.0 ต้นคลอง (ฝั่งป่าสัก)", "end")
    add(135.9, "กม.135.9 ปลายคลอง → อ่าวไทย (น้ำหนุนสูง +2.0 ม.รทก.)", "end")
    add(23.0, "กม.23 เปลี่ยนรูปตัด: คลองดิน(จม) → คลองลอยดาดคอนกรีต", "reach", dz=2.0)
    add(134.0, "กม.134 เริ่มปากแตร (ท้องคลอง 51→380 ม.)", "reach", dz=2.0)
    for s in g["structures"]:
        k, n = s["kind"], s["name"]
        km = s["km"]
        if k == "gate":
            q = lv(km)
            add(km, f"ปตร. กม.{km:g} · 4 บาน {s.get('bay_width_m', 12.5):g}×{s.get('bay_height_m', 6.0):g} ม. · ท้อง {q['bed']:+.2f} น้ำ {q['water']:+.2f} สันคัน {q['crest']:+.2f} ม.รทก.", "gate", dz=6.0)
        elif k == "rail_bridge":
            add(km, f"สะพานรถไฟ กม.{km:g} (ยาว {max(s.get('spans_m') or [0]):g} ม.)", "rail", dz=5.0)
        elif k == "road_bridge" and any(w in n for w in ("ทางหลวง", "ทางพิเศษ", "มอเตอร์เวย์")):
            add(km, f"{n[:34]} กม.{km:g}", "highway", dz=4.0)
        elif k == "crossing" and ((s.get("canal_w") or 0) >= 30 or "แม่น้ำ" in n):
            add(km, f"{n[:28]} กม.{km:g} (กว้าง ~{s.get('canal_w', 0):g} ม.)", "river", dz=3.0)
        elif k == "aqueduct":
            add(km, f"สะพานน้ำ {n[:26]} กม.{km:g}", "aqueduct", dz=7.0)
    for km in range(10, 136, 10):
        q = lv(float(km))
        add(float(km), f"กม.{km} · ดินเดิม {q['ground']:+.1f} · น้ำ {q['water']:+.1f} · สันคัน {q['crest']:+.1f} ม.รทก.", "km", dz=1.0)
    return out


def section_area_check(g: dict) -> dict:
    """พื้นที่หน้าตัดน้ำที่แบบจำลองสร้าง (จากพารามิเตอร์ตาราง) เทียบค่า A ที่ตารางทางการพิมพ์"""
    out = {}
    for km, reach in ((10.0, 1), (60.0, 2)):
        s = min(g["stations"], key=lambda q: abs(q["km"] - km))
        sp = section_params(s["km"], g["section_table"])
        ip = [(u, z) for u, z in inner_profile(sp, s["bed"], s["water"], s["crest"]) if z <= s["water"] + 1e-9]
        poly = [(-u, z) for u, z in reversed(ip)] + ip
        a = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))) / 2.0
        off = g["section_table"]["reaches"][reach - 1]["A"]
        out[f"reach{reach}"] = {"model_area_m2": round(a, 1), "official_area_m2": off, "diff_pct": round(100.0 * (a - off) / off, 2)}
    return out


def write_obj(mesh: Mesh, path: Path):
    verts, index = [], {}
    lines_f = []
    for mat, polys in mesh.polys.items():
        lines_f.append(f"usemtl {mat}")
        for p in polys:
            ids = []
            for v in p:
                k = (round(v[0], 2), round(v[1], 2), round(v[2], 2))
                if k not in index:
                    index[k] = len(verts) + 1
                    verts.append(k)
                ids.append(index[k])
            lines_f.append("f " + " ".join(map(str, ids)))
    mtl = path.with_suffix(".mtl")
    mtl.write_text("\n".join(f"newmtl {n}\nKd {c[0]} {c[1]} {c[2]}\nd {c[3]}\n" for n, c in MATERIALS.items()), encoding="utf-8")
    # OBJ ใช้แกน Y เป็นแกนตั้งในหลายโปรแกรม — SketchUp นำเข้าเป็น Z ขึ้นตามค่าตั้งต้น จึงเขียนเป็น (x, y, z) ตรง ๆ
    body = ["# คลองเจ้าพระยา 2 กม.0–135.9 — แบบจำลองจากตัวเลขทางการ (หน่วยเมตร · x ตะวันออก · y เหนือ · z สูง)", f"mtllib {mtl.name}"]
    body += [f"v {x:.2f} {y:.2f} {z:.2f}" for x, y, z in verts] + lines_f
    path.write_text("\n".join(body), encoding="utf-8")
    return len(verts), sum(len(v) for v in mesh.polys.values())


def tiles(mesh: Mesh, fr: Frame):
    """แบ่งเป็นกระเบื้อง ~10 กม. (พิกัดท้องถิ่นของแต่ละกระเบื้อง) กัน SketchUp เพี้ยนเมื่ออยู่ไกลจุดกำเนิดหลายสิบกิโลเมตร"""
    out = defaultdict(lambda: defaultdict(list))
    for mat, polys in mesh.polys.items():
        for p in polys:
            c = np.mean(p, axis=0)
            kmi = float(np.interp(0, [0, 1], [0, 1]))
            i = int(np.argmin((fr.x - c[0]) ** 2 + (fr.y - c[1]) ** 2))
            out[int(fr.km[i] // TILE_KM)][mat].append(p)
    res = {}
    for t, mats in out.items():
        allv = np.array([v for ps in mats.values() for p in ps for v in p])
        o = (round(float(allv[:, 0].mean()), 0), round(float(allv[:, 1].mean()), 0))
        res[t] = {"origin": o, "mats": {m: [[(v[0] - o[0], v[1] - o[1], v[2]) for v in p] for p in ps] for m, ps in mats.items()}}
    return res


RUBY_HEAD = '''# encoding: utf-8
# คลองเจ้าพระยา 2 (ป่าสัก–อ่าวไทย) กม.0–135.9 — แบบจำลอง 3 มิติจากตัวเลขมิติทางการ (สร้างโดย analysis/goal7_build_3d_model.py)
# วิธีใช้: SketchUp > Window > Ruby Console แล้วพิมพ์  load "<พาธไฟล์นี้>"  (หรือ Extensions > Developer > Ruby Console)
# หน่วยในไฟล์เป็นเมตร (ใช้ .m แปลงเป็นหน่วยภายในของ SketchUp) · แบ่งเป็นกลุ่มละ ~10 กม. ตามกม. · ยังไม่ได้ทดสอบกับ SketchUp รุ่นจริง
# VERT_EXAG = ตัวคูณความสูง (1 = มาตราส่วนจริง · ลองใช้ 10–30 เพื่อดูภาพรวมทั้งเส้น) — ใช้กับ z ทุกจุด
# โหลดซ้ำในเซสชันเดิมได้โดยไม่มีคำเตือน (ลบค่าคงที่เก่าก่อน) และจะลบกลุ่มโมเดลเดิมแล้วสร้างใหม่ ไม่ซ้อนทับ
[:VERT_EXAG, :MATERIALS, :TILES, :LABELS].each { |c| Object.send(:remove_const, c) if Object.const_defined?(c) }
VERT_EXAG = 1.0
MATERIALS = %s
TILES = %s
LABELS = __LABELS__

def cpy2_material(model, name)
  m = model.materials[name] || model.materials.add(name)
  c = MATERIALS[name]
  m.color = Sketchup::Color.new((c[0]*255).to_i, (c[1]*255).to_i, (c[2]*255).to_i)
  m.alpha = c[3]
  m
end

model = Sketchup.active_model
model.start_operation("คลองเจ้าพระยา 2", true)
model.entities.grep(Sketchup::Group).select { |g| g.name == "คลองเจ้าพระยา2 กม.0-135.9" }.each(&:erase!)
root = model.entities.add_group
root.name = "คลองเจ้าพระยา2 กม.0-135.9"
TILES.sort_by { |k, _| k.to_i }.each do |tile, data|
  tg = root.entities.add_group
  tg.name = "กม. #{tile.to_i * %d}–#{tile.to_i * %d + %d}"
  ox, oy = data["origin"]
  tg.transformation = Geom::Transformation.new(Geom::Point3d.new(ox.m, oy.m, 0))
  data["mats"].each do |mat, polys|
    mg = tg.entities.add_group
    mg.name = mat
    pm = Geom::PolygonMesh.new
    polys.each do |p|
      idx = p.map { |x, y, z| pm.add_point(Geom::Point3d.new(x.m, y.m, (z * VERT_EXAG).m)) }
      begin
        pm.add_polygon(*idx)
      rescue ArgumentError
        next
      end
    end
    mat_obj = cpy2_material(model, mat)
    # ระบายสีทั้งด้านหน้าและด้านหลัง (กันหน้าที่หันกลับกลายเป็นสีเริ่มต้น/ฟ้า ดูเหมือนหายไป)
    mg.entities.add_faces_from_mesh(pm, 12, mat_obj, mat_obj)
  end
end
# ป้ายกำกับตำแหน่งสำคัญ (ข้อความพร้อมเส้นนำ อ่านได้จากทุกมุม) · เปิด/ปิดได้ที่แท็ก "ป้ายกำกับ"
lbl_layer = model.layers["ป้ายกำกับ"] || model.layers.add("ป้ายกำกับ")
lg = root.entities.add_group
lg.name = "ป้ายกำกับ"
lg.layer = lbl_layer
LABELS.each do |x, y, z, text|
  lift = 60 + 6 * VERT_EXAG
  lg.entities.add_text(text, Geom::Point3d.new(x.m, y.m, (z * VERT_EXAG).m), Geom::Vector3d.new(0, 0, lift.m))
end
model.commit_operation
Sketchup.status_text = "สร้างคลองเจ้าพระยา 2 เสร็จ"
'''


def write_ruby(mesh, fr, path: Path, vexag: float, labels=None):
    t = tiles(mesh, fr)
    def tris(ps):   # สี่เหลี่ยมที่ไม่อยู่ระนาบเดียว (บิดตามโค้งของแนวคลอง) SketchUp สร้างหน้าไม่ได้ — แตกเป็นสามเหลี่ยมทั้งหมด
        for q in ps:
            if len(q) == 4:
                yield [q[0], q[1], q[2]]
                yield [q[0], q[2], q[3]]
            else:
                yield q
    comp = {str(k): {"origin": v["origin"], "mats": {m: [[[round(c, 2) for c in pt] for pt in q] for q in tris(ps)] for m, ps in v["mats"].items()}} for k, v in sorted(t.items())}
    # z ในไฟล์ .rb เป็นค่าจริง (vexag=1) แล้วคูณด้วย VERT_EXAG ตอนรัน
    mat = {k: list(v) for k, v in MATERIALS.items()}
    ruby_hash = lambda o: json.dumps(o, ensure_ascii=False).replace('":', '" =>').replace("[", "[").replace("true", "true")  # noqa: E731
    src = RUBY_HEAD % (ruby_hash(mat), ruby_hash(comp), int(TILE_KM), int(TILE_KM), int(TILE_KM))
    lab = [[l["x"], l["y"], l["z"], l["text"]] for l in (labels or [])]
    src = src.replace("__LABELS__", ruby_hash(lab))
    path.write_text(src, encoding="utf-8")
    return len(comp)


VIEWER = """<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>แบบจำลอง 3 มิติ คลองเจ้าพระยา 2</title>
<style>
html,body{margin:0;height:100%%;font-family:'Leelawadee UI',Tahoma,sans-serif;background:#0f172a;color:#e2e8f0}
#c{position:fixed;inset:0}
#panel{position:fixed;top:10px;left:10px;width:300px;max-height:92%%;overflow:auto;background:#0b1220e6;border:1px solid #334155;border-radius:8px;padding:12px;font-size:13px;line-height:1.5}
#panel h1{font-size:16px;margin:0 0 6px}#panel label{display:block;margin:2px 0}
.sw{display:inline-block;width:11px;height:11px;margin-right:6px;border:1px solid #fff4;vertical-align:-1px}
small{color:#94a3b8}button,select,input[type=range]{width:100%%;margin:3px 0}
</style></head><body><canvas id="c"></canvas>
<div id="panel"><h1>คลองเจ้าพระยา 2 กม.0–135.9</h1>
<small>จากตัวเลขมิติทางการของรายงานผลกระทบสิ่งแวดล้อม · ลากเมาส์หมุน · ล้อเมาส์ซูม · คลิกขวาลากเลื่อน</small>
<hr><label>ความสูงเกินจริง ×<b id="vv">10</b><input id="vex" type="range" min="1" max="60" value="10"></label>
<label>ไปที่ กม. <select id="kmsel"></select></label>
<div id="legend"></div>
<hr><small id="note"></small></div>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const DATA=%s, MATS=%s, KMS=%s, NOTE=%s, LABELS=%s;
const scene=new THREE.Scene();scene.background=new THREE.Color(0x0f172a);
const cam=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,1,2e6);
const rend=new THREE.WebGLRenderer({canvas:document.getElementById('c'),antialias:true});rend.setSize(innerWidth,innerHeight);
const ctl=new THREE.OrbitControls(cam,rend.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x445566,0.9));const dl=new THREE.DirectionalLight(0xffffff,0.8);dl.position.set(1,-1,2);scene.add(dl);
// แกน: x ตะวันออก y เหนือ z สูง (ให้ z เป็นแกนตั้งของกล้อง)
cam.up.set(0,0,1);
const grp=new THREE.Group();scene.add(grp);const meshes={};
for(const [name,b64] of Object.entries(DATA)){
  const bin=atob(b64),buf=new ArrayBuffer(bin.length),u8=new Uint8Array(buf);for(let i=0;i<bin.length;i++)u8[i]=bin.charCodeAt(i);
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(buf),3));g.computeVertexNormals();
  const c=MATS[name];const m=new THREE.MeshLambertMaterial({color:new THREE.Color(c[0],c[1],c[2]),side:THREE.DoubleSide,transparent:c[3]<1,opacity:c[3]});
  const me=new THREE.Mesh(g,m);grp.add(me);meshes[name]=me;
}
const leg=document.getElementById('legend');
for(const name of Object.keys(DATA)){const c=MATS[name];const l=document.createElement('label');
  l.innerHTML='<input type="checkbox" checked> <span class="sw" style="background:rgb('+[0,1,2].map(i=>Math.round(c[i]*255))+')"></span>'+name;
  l.firstChild.onchange=e=>{meshes[name].visible=e.target.checked};leg.appendChild(l);}
const vex=document.getElementById('vex');
const lblGrp=new THREE.Group();scene.add(lblGrp);const lblSprites=[];
const KC={end:'#fde047',reach:'#f472b6',gate:'#fb923c',rail:'#cbd5e1',highway:'#f87171',river:'#60a5fa',aqueduct:'#67e8f9',km:'#e2e8f0'};
LABELS.forEach(l=>{const cv=document.createElement('canvas'),cx=cv.getContext('2d');const fs=34;cx.font=fs+'px Leelawadee UI, Tahoma, sans-serif';const w=Math.ceil(cx.measureText(l.text).width)+24;cv.width=w;cv.height=fs+18;
  cx.font=fs+'px Leelawadee UI, Tahoma, sans-serif';cx.fillStyle='rgba(11,18,32,0.82)';cx.fillRect(0,0,w,cv.height);cx.strokeStyle=KC[l.kind]||'#fff';cx.lineWidth=3;cx.strokeRect(1,1,w-2,cv.height-2);cx.fillStyle=KC[l.kind]||'#fff';cx.textBaseline='middle';cx.fillText(l.text,12,cv.height/2+2);
  const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(cv),depthTest:false,transparent:true}));sp.userData={l,ratio:w/cv.height};lblGrp.add(sp);lblSprites.push(sp);});
function placeLabels(){const v=+vex.value;lblSprites.forEach(sp=>{const l=sp.userData.l;sp.position.set(l.x,l.y,l.z*v+40+4*v);const d=cam.position.distanceTo(sp.position);const h=Math.max(d*0.03,10);sp.scale.set(h*sp.userData.ratio,h,1)})}
const lcb=document.createElement('label');lcb.innerHTML='<input type="checkbox" checked> ป้ายกำกับ';lcb.firstChild.onchange=e=>{lblGrp.visible=e.target.checked};document.getElementById('legend').before(lcb);
function setV(){grp.scale.z=+vex.value;document.getElementById('vv').textContent=vex.value;placeLabels()}
vex.oninput=setV;setV();
const sel=document.getElementById('kmsel');
KMS.forEach(k=>{const o=document.createElement('option');o.value=k.km;o.textContent='กม. '+k.km.toFixed(1)+(k.label?' · '+k.label:'');sel.appendChild(o)});
function go(km){const k=KMS.reduce((a,b)=>Math.abs(b.km-km)<Math.abs(a.km-km)?b:a);
  ctl.target.set(k.x,k.y,k.z*vex.value);cam.position.set(k.x+300,k.y-300,k.z*vex.value+250);ctl.update();}
sel.onchange=()=>go(+sel.value);
// มุมมองเริ่มต้น: ทั้งเส้น
const bb=new THREE.Box3().setFromObject(grp);const ctr=bb.getCenter(new THREE.Vector3()),sz=bb.getSize(new THREE.Vector3());
ctl.target.copy(ctr);cam.position.set(ctr.x+sz.x*0.2,ctr.y-sz.y*0.9,sz.y*0.7);ctl.update();
document.getElementById('note').innerHTML=NOTE;
addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();rend.setSize(innerWidth,innerHeight)});
(function loop(){requestAnimationFrame(loop);ctl.update();placeLabels();rend.render(scene,cam)})();
</script></body></html>"""


def write_viewer(mesh: Mesh, fr: Frame, g: dict, path: Path, labels=None):
    import base64
    data = {}
    for mat, polys in mesh.polys.items():
        tri = []
        for p in polys:
            for i in range(1, len(p) - 1):
                tri += [p[0], p[i], p[i + 1]]
        data[mat] = base64.b64encode(np.array(tri, dtype="<f4").tobytes()).decode()
    kms = []
    for s in g["structures"]:
        if s["kind"] in ("gate", "rail_bridge") or s["no"] % 10 == 0:
            x, y, z = fr.at(s["km"], 0.0, 0.0)
            kms.append({"km": s["km"], "x": x, "y": y, "z": float(np.interp(s["km"], [q["km"] for q in g["stations"]], [q["crest"] for q in g["stations"]])), "label": {"gate": "ประตูระบายน้ำ", "rail_bridge": "สะพานรถไฟ"}.get(s["kind"], s["name"][:24])})
    for q in g["stations"][::20]:
        x, y, z = fr.at(q["km"], 0.0, 0.0)
        kms.append({"km": q["km"], "x": x, "y": y, "z": q["crest"], "label": ""})
    kms.sort(key=lambda k: k["km"])
    note = ("<b>ข้อสมมติที่ไม่ใช่ตัวเลขทางการ:</b> " + " · ".join(g["assumptions_for_model"]) + "<br><b>ความสูงเกินจริง:</b> ดึงแถบ ×1 = มาตราส่วนจริง (คลองสูง 7 ม. ยาว 135.9 กม. จึงแบนมาก)")
    path.write_text(VIEWER % (json.dumps(data), json.dumps({k: list(v) for k, v in MATERIALS.items()}), json.dumps(kms, ensure_ascii=False), json.dumps(note, ensure_ascii=False), json.dumps(labels or [], ensure_ascii=False)), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vexag", type=float, default=1.0)
    a = ap.parse_args()
    OUTD.mkdir(parents=True, exist_ok=True)
    mesh, fr, g = build(1.0)    # ไฟล์ .obj/.rb เขียนที่มาตราส่วนจริงเสมอ — ความสูงเกินจริงเป็นตัวเลือกตอนดู
    nv, nf = write_obj(mesh, OUTD / "chaophraya2.obj")
    labels = make_labels(g, fr)
    nt = write_ruby(mesh, fr, OUTD / "chaophraya2_sketchup.rb", a.vexag, labels)
    write_viewer(mesh, fr, g, OUTD / "chaophraya2_viewer.html", labels)
    allv = np.array([v for ps in mesh.polys.values() for p in ps for v in p])
    summary = {"vertices": nv, "faces": nf, "tiles": nt, "materials": {m: len(p) for m, p in mesh.polys.items()}, "bbox_m": [allv.min(axis=0).round(1).tolist(), allv.max(axis=0).round(1).tolist()],
               "section_area_check": section_area_check(g), "labels": len(labels), "structures_modelled": {k: sum(1 for s in g["structures"] if s["kind"] == k) for k in sorted({s["kind"] for s in g["structures"]})}, "assumptions": g["assumptions_for_model"]}
    (OUTD / "chaophraya2_model_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False)[:900])


if __name__ == "__main__":
    main()
