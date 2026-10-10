"""เป้าหมาย 6 — N1/N2 ฐาน: ผูก node ทั้งประเทศ (จุดวัด 199 + ปตร. 2,315) เข้าลุ่มย่อย HydroBASINS

หลักการ pre-register (ประกาศก่อนดูผล):
- ลุ่มย่อย = HydroBASINS lev08 (ละเอียดพอ ๆ กับลุ่มย่อยไทย โดยเฉลี่ย ~180 ตร.กม./ลุ่ม)
- จุด→ลุ่มย่อย = point-in-polygon (shapely, STRtree) ตามพิกัด API — ห้ามเลื่อนพิกัดเอง
- จุดที่หาลุ่มไม่ได้ (หลุดขอบ/พิกัดคลาด) = นับ "ไม่ผูกได้" อย่าซ่อน — เป็นตัวชี้คุณภาพพิกัด
- ผลเชื่อมโยง: เขื่อน (dam_history_all) → HYBAS_ID → ลุ่มย่อยท้ายน้ำเดียวกันกับจุดวัด/ปตร. ใดบ้าง
  (เฉพาะ topology: เขื่อนไม่มีพิกัดใน API — ใช้ตำแหน่งที่รู้จาก dam_history_all ถ้ามี, ไม่มี = ข้าม)

ผลลัพธ์: analysis/goal6/network_nodes.json/.md
ทำซ้ำได้ · รัน: python analysis/goal6_network_nodes.py
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

import shapefile
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent.parent
HB_ZIP = ROOT / "data/22_goal6_network/raw/hydrobasins/hybas_as_lev08_v1c.zip"
GATES = ROOT / "data/02_thaiwater/raw/2026-10-09_watergate_load.json"
WL_DIR = ROOT / "data/30_national_warehouse/waterlevels"
STATION_ALL = ROOT / "data/02_thaiwater/raw/station_all.json"
OUT_JSON = ROOT / "analysis/goal6/network_nodes.json"
OUT_MD = ROOT / "analysis/goal6/network_nodes.md"


def load_hybas() -> tuple[STRtree, list]:
    z = zipfile.ZipFile(HB_ZIP)
    tmp = Path(tempfile.mkdtemp())
    for n in z.namelist():
        (tmp / n).write_bytes(z.read(n))
    r = shapefile.Reader(str(tmp / "hybas_as_lev08_v1c"))
    names = [f[0] for f in r.fields[1:]]
    geoms, meta = [], []
    for i in range(len(r)):
        rec = r.record(i)
        m = dict(zip(names, rec))
        geoms.append(shape(r.shape(i).__geo_interface__))
        meta.append(m)
    return STRtree(geoms), meta


def assign(geoms_tree: STRtree, meta: list, lon: float, lat: float) -> int | None:
    idxs = geoms_tree.query(Point(lon, lat))
    for i in idxs:
        if geoms_tree.geometries[i].covers(Point(lon, lat)):
            return int(meta[i]["HYBAS_ID"])
    return None


def main() -> None:
    tree, meta = load_hybas()
    print(f"lev08: {len(meta)} ลุ่มย่อย", flush=True)

    # ---- จุดวัด 199 (คลังระดับชาติ) ----
    sa = json.loads(STATION_ALL.read_text(encoding="utf-8"))["data"]
    by_id = {r["station_id"]: r for r in sa}
    gauges = []
    unbound = {"gauge": 0, "gate": 0}
    for p in sorted(WL_DIR.glob("*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        st = by_id.get(rec["station_id"], {})
        lat, lon = st.get("station_lat"), st.get("station_long")
        if lat is None or lon is None:
            unbound["gauge"] += 1
            continue
        hb = assign(tree, meta, lon, lat)
        if hb is None:
            unbound["gauge"] += 1
        gauges.append({"id": rec["station_id"], "code": rec.get("code", ""), "name": rec.get("name", ""),
                       "lat": lat, "lon": lon, "hybas_id": hb})

    # ---- ปตร. (snapshot 9 ต.ค.) · 構造: province単位のリスト ----
    g = json.loads(GATES.read_text(encoding="utf-8"))["station"]["data"]
    gates = []
    for entry in g:
        prov = entry.get("province_name", {}).get("th", "")
        for s in entry.get("station", []):
            lat, lon = s.get("station_lat"), s.get("station_long")
            if lat is None or lon is None:
                unbound["gate"] += 1
                continue
            hb = assign(tree, meta, lon, lat)
            if hb is None:
                unbound["gate"] += 1
            gates.append({"id": s.get("station_id"), "code": s.get("station_oldcode", ""),
                          "name": (s.get("station_name") or {}).get("th", ""), "prov": prov,
                          "lat": lat, "lon": lon, "hybas_id": hb})

    # ---- สรุป ----
    from collections import Counter
    hb_gauge = Counter(x["hybas_id"] for x in gauges if x["hybas_id"])
    hb_gate = Counter(x["hybas_id"] for x in gates if x["hybas_id"])
    shared = set(hb_gauge) & set(hb_gate)
    out = {
        "note": "ผูก node→ลุ่มย่อย lev08 แบบ point-in-polygon ตามพิกัด API (ไม่เลื่อนพิกัด) · จุดหลุด = นับไม่ผูกได้",
        "unbound": unbound,
        "gauge_n": len(gauges), "gate_n": len(gates),
        "subbasins_with_gauge": len(hb_gauge), "subbasins_with_gate": len(hb_gate),
        "subbasins_both": len(shared),
        "gauges": gauges, "gates": gates,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = ["# ฐานเครือข่ายระดับชาติ — node ผูกลุ่มย่อย (N1/N2 ขั้นฐาน)", "",
             "> ลุ่มย่อย = HydroBASINS lev08 · ผูกแบบ point-in-polygon ตามพิกัด API เดิม (ไม่เลื่อนพิกัด) · "
             "จุดที่ผูกไม่ได้ = นับเปิดเผย ไม่ซ่อน", "",
             "| กลุ่ม node | จำนวน | ผูกได้ | ผูกไม่ได้ | ครอบลุ่มย่อย |", "|---|---|---|---|---|",
             f"| จุดวัด (คลัง 199) | {len(gauges)} | {len(gauges)-unbound['gauge']} | {unbound['gauge']} | {len(hb_gauge)} |",
             f"| ปตร. (snapshot 9 ต.ค.) | {len(gates)} | {len(gates)-unbound['gate']} | {unbound['gate']} | {len(hb_gate)} |",
             f"| ลุ่มย่อยที่มีทั้งจุดวัดและ ปตร. | — | — | — | {len(shared)} |", "",
             "อ่านต่อ: ตัวเลขนี้คือฐานของ N1 (จุดบอด) และ N2 (cascade เขื่อน→ปตร.→เมือง) — "
             "การจัดเต็มทำในรายงานที่ 5", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"จุดวัด {len(gauges)} (ไม่ผูกได้ {unbound['gauge']}) · ปตร. {len(gates)} (ไม่ผูกได้ {unbound['gate']}) · "
          f"ลุ่มย่อยทั้งสองชนิด {len(shared)}", flush=True)


if __name__ == "__main__":
    main()
