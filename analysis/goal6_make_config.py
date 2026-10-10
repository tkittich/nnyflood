"""เป้าหมาย 6 — สร้าง analysis/goal6/config.json (ข้อตกลง pre-register ต่อลุ่ม)

ดึงรายการจากข้อมูลที่มีอยู่แล้วเท่านั้น: goal6_basin_readiness.json (จุดวัด key รายลุ่ม) ·
goal6_dam_candidates.json (เขื่อน + เก็บปกติ) · waterlevel_load/watergate_load snapshot (กทม.) ·
หน้าต่างเวลา/จุดฝนกำหนดตามแผน — รันครั้งเดียวเมื่อ 10 ต.ค. 69 แล้ว config เป็นข้อตกลง แก้ต้องเจตนา
รัน: python analysis/goal6_make_config.py
"""

from __future__ import annotations

import json
from pathlib import Path

import goal6_screen_basins as g6

ROOT = Path(__file__).resolve().parent.parent
READINESS = ROOT / "analysis/goal6_basin_readiness.json"
CANDIDATES = ROOT / "analysis/goal6_dam_candidates.json"
LOAD = g6.LOAD_SNAPSHOT
OUT = ROOT / "analysis/goal6/config.json"

WINDOW = ["2026-07-01", "2026-10-09"]

# (basin_id, label, basin_names ในทะเบียน, เขื่อน [ชื่อ, dam_id], จุดฝน, พิเศษ)
SPECS = {
    "pasak": {
        "label": "ป่าสัก",
        "basin_names": ["ลุ่มน้ำป่าสัก"],
        "dams": [["ป่าสักชลสิทธิ์ (พระรามหก)", 11]],
        "rain_points": {"ลุ่มบนป่าสัก": [100.9, 15.75], "อยุธยา": [100.55, 14.35]},
        "done_by_spike": "analysis/goal6_spike_pasak_findings.md",
    },
    "maeklong": {
        "label": "แม่กลอง",
        "basin_names": ["ลุ่มน้ำแม่กลอง"],
        "dams": [["แก่งกระจาน", 13], ["ศรีนครินทร์", 14], ["วชิราลงกรณ", 15]],
        "rain_points": {"ลุ่มบนแม่กลอง": [98.9, 14.6], "กาญจนบุรี": [99.14, 14.02]},
        "done_by_spike": "analysis/goal6_spike_maeklong_findings.md",
    },
    "bp_prach": {
        "label": "ลุ่มบางปะกง (นครนายก–ปราจีนบุรี)",
        "basin_names": ["ลุ่มน้ำบางปะกง"],
        "dams": [["ขุนด่านปราการชล", 32], ["คลองสียัด", 30], ["นฤบดินทรจินดา", 37]],
        "rain_points": {"ลุ่มบนปราจีนบุรี/สระแก้ว": [101.9, 13.9], "นครนายก": [101.22, 14.2],
                        "ปราจีนบุรี": [101.37, 14.05]},
        "notes": "นครนายก = ฐานอ้างอิง canonical (รายงาน 1–2) — อย่าวิเคราะห์ซ้ำ",
    },
    "thachin": {
        "label": "ท่าจีน",
        "basin_names": ["ลุ่มน้ำท่าจีน"],
        "dams": [["กระเสียว", 17]],
        "rain_points": {"ลุ่มบนท่าจีน": [99.7, 14.9], "นครชัยศรี": [100.18, 13.79]},
    },
    "ping_cp": {
        "label": "ปิง–เจ้าพระยาตอนบน",
        "basin_names": ["ลุ่มน้ำปิง", "ลุ่มน้ำเจ้าพระยา"],
        "dams": [["ภูมิพล", 43]],
        "rain_points": {"ลุ่มบนปิง": [99.0, 17.5], "นครสวรรค์ (C.2)": [100.11, 15.67]},
        "upstream_anchor": "เขื่อนสิริกิติ์ (ลุ่มน่าน) ระบายน้ำผ่านแม่น้ำยมเข้าจุด C.2 ด้วย — ใช้เป็นข้อมูลบริบท ไม่วิเคราะห์รายเขื่อน",
    },
    "bkk_lower": {
        "label": "ลุ่มเจ้าพระยาตอนล่าง–กทม.–สมุทรปราการ",
        "basin_names": [],
        "dams": [],
        "rain_points": {"กรุงเทพกลาง": [100.52, 13.75], "ปากน้ำ": [100.6, 13.55]},
        "station_filter": {"provinces": ["กรุงเทพมหานคร", "นนทบุรี", "ปทุมธานี", "สมุทรปราการ"]},
        # เพิ่ม 11 ต.ค. 69 (ผ่านบันทึกเหตุผล): จุดควบคุมเหนือขอบ 4 จังหวัด — อธิบายน้ำจากลุ่มได้
        "extra_stations": [
            {"id": 2744, "code": "C.13", "name": "ท้ายเขื่อนเจ้าพระยา (ชัยนาท)"},
            {"id": 1574215, "code": "C.22A", "name": "ปากเกร็ด (นนทบุรี ทางเข้า กทม.)"},
        ],
        "upstream_anchor": "จุดวัด C.2 ท่าเรือ นครสวรรค์ (ข้อมูลตั้งแต่ 2019–2026 เก็บไว้แล้วในโฟลเดอร์หลักฐานของโครงการ) ต่อด้วย C.22A ปากเกร็ด แล้วถึงกรุงเทพฯ",
        "extras": ["watergate_snapshot", "canal_snapshot"],
        "notes": "attribution สามทาง (ฝนเมือง/น้ำลุ่ม/ทะเล) · DEM ใช้ได้เชิงคุณภาพเท่านั้น (§5.1)",
    },
}


def stations_from_readiness(basin_names: list[str]) -> list[dict]:
    rd = json.loads(READINESS.read_text(encoding="utf-8"))["basins"]
    out = []
    for rec in rd.values():
        for st in rec.get("stations", []):
            if st.get("basin") in basin_names:
                out.append({"id": st["id"], "code": st["code"], "name": st["name"]})
    # ตัดซ้ำ (จุดคลองข้ามลุ่ม)
    seen, uniq = set(), []
    for st in out:
        if st["id"] not in seen:
            seen.add(st["id"])
            uniq.append(st)
    return sorted(uniq, key=lambda x: x["code"])


def stations_from_provinces(provinces: list[str]) -> list[dict]:
    payload = json.loads(LOAD.read_text(encoding="utf-8"))
    wl = payload["waterlevel_data"]
    rows = wl.get("data", wl) if isinstance(wl, dict) else wl
    out = []
    for r in rows:
        st = r.get("station") or {}
        prov = (r.get("geocode") or {}).get("province_name", {}).get("th")
        if prov not in provinces:
            continue
        name = st.get("tele_station_name") or {}
        out.append({
            "id": st.get("id"),
            "code": st.get("tele_station_oldcode") or str(st.get("id")),
            "name": name.get("th") or name.get("en") or str(st.get("id")),
            "province": prov,
            "key": bool(st.get("is_key_station")),
        })
    return sorted(out, key=lambda x: (x["province"], x["code"]))


def normal_storage(dam_id: int) -> float | None:
    c = json.loads(CANDIDATES.read_text(encoding="utf-8"))["candidates"]
    for r in c:
        if dam_id in r["dam_ids"]:
            return r["normal_storage"]
    return None


def main() -> None:
    basins = {}
    for bid, spec in SPECS.items():
        rec = dict(spec)
        rec["window"] = WINDOW
        if rec.get("station_filter"):
            rec["stations"] = stations_from_provinces(rec["station_filter"]["provinces"])
        else:
            rec["stations"] = stations_from_readiness(rec["basin_names"])
        for extra in rec.get("extra_stations", []):
            rec["stations"].append({**extra, "extra": "จุดควบคุมเหนือขอบจังหวัดที่กรอง"})
        rec["dams"] = [
            {"name": n, "dam_id": d, "normal_storage": normal_storage(d)} for n, d in rec["dams"]
        ]
        basins[bid] = rec
    cfg = {"schema": "goal6.l1.v1", "created": "2026-10-10",
           "note": "ข้อตกลง pre-register ต่อลุ่ม — แก้ค่าต้องมีเหตุผลเขียนลง manifest",
           "basins": basins}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    for bid, rec in basins.items():
        print(f"{bid} ({rec['label']}): จุดวัด {len(rec['stations'])} · เขื่อน {len(rec['dams'])} · "
              f"{'skip (spike แล้ว)' if rec.get('done_by_spike') else 'ทำต่อ'}")


if __name__ == "__main__":
    main()