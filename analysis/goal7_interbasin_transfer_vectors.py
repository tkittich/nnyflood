#!/usr/bin/env python3
"""analysis/goal7_interbasin_transfer_vectors.py — ระดับน้ำหน้า/หลังประตูระบายหลักของคลองเชื่อมลุ่มป่าสัก–รังสิต–เจ้าพระยา (ภาพ ณ เวลาเดียว 9 ต.ค. 2569)

เก็บเฉพาะที่ตรวจย้อนได้จากไฟล์โทรมาตรประตูระบายน้ำ (สสน.) : ระดับหน้า/หลังประตูของ 5 ประตู เวลาตามที่ระบบบันทึก และผลต่างระดับ
ไม่คำนวณความลาดชลศาสตร์ ทิศการไหล หรือสภาพ "ติดน้ำเทิน" — เพราะ (1) ระยะทางระหว่างประตูไม่มีแหล่งอ้างอิง
(2) ไม่มีข้อมูลสถานะบานประตู/เครื่องสูบ (ฟิลด์ pump_on / floodgate_open เป็นค่าว่างทุกประตู) (3) ระดับ TNy10 ที่เคยใช้เป็นค่าเฉลี่ยเดือนกันยายน
ไม่ใช่ค่า ณ เวลาเดียวกับระดับประตู จึงเทียบกันไม่ได้ (แก้ 28 ต.ค. 69 หลังตรวจก่อนลงรายงาน)

ที่มา: data/02_thaiwater/raw/2026-10-09_watergate_load.json (แฮชและวิธีดึงอยู่ใน data/02_thaiwater/manifest.md)

รัน: python analysis/goal7_interbasin_transfer_vectors.py
ผลลัพธ์: analysis/goal7/interbasin_transfer_summary.json · analysis/goal7/interbasin_transfer_findings.md · แนบลง analysis/goal7/canonical.json
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATERGATE_FILE = ROOT / "data/02_thaiwater/raw/2026-10-09_watergate_load.json"
CANONICAL_FILE = ROOT / "analysis/goal7/canonical.json"
OUT_JSON = ROOT / "analysis/goal7/interbasin_transfer_summary.json"
OUT_MD = ROOT / "analysis/goal7/interbasin_transfer_findings.md"

SNAPSHOT_DATE = "2026-10-09"
KEY_GATES = {
    "ATG05": "ปตร.พระนารายน์ (คลองระพีพัฒน์แยกตก/ใต้)",
    "ATG07": "ปตร.พระศรีศิลป์ (คลองระพีพัฒน์แยกใต้)",
    "ATG08": "ปตร.พระธรรมราชา (คลอง 13 สายล่าง)",
    "ATG09": "ปตร.พระอินทราชา (คลองระพีพัฒน์แยกตก)",
    "ATG101": "ปตร.จุฬาลงกรณ์ (รังสิตสู่แม่น้ำเจ้าพระยา)",
}


def analyze_interbasin_vectors():
    wg_raw = json.loads(WATERGATE_FILE.read_text(encoding="utf-8"))
    gates_data = {
        x["station"].get("tele_station_oldcode"): x
        for x in wg_raw.get("watergate_data", {}).get("data", [])
        if x.get("station") and x["station"].get("tele_station_oldcode")
    }

    gate_snapshots = {}
    for code, name in KEY_GATES.items():
        g = gates_data[code]  # ไม่มีค่าสำรอง: ถ้าประตูหายจากไฟล์ให้ล้มทันที
        # ค่าที่เวลาบันทึกไม่ตรงวันของภาพเป็นค่าค้างเก่า ไม่ใช้ (ATG07 หน้าประตู: ค่าว่าง เวลาค้าง 2017-12-27)
        stale_in = g["watergate_datetime_in"] is None or g["watergate_datetime_in"][:10] != SNAPSHOT_DATE
        stale_out = g["watergate_datetime_out"] is None or g["watergate_datetime_out"][:10] != SNAPSHOT_DATE
        w_in = None if stale_in else g["watergate_in"]
        w_out = None if stale_out else g["watergate_out"]
        gate_snapshots[code] = {
            "name": name,
            "basin": g["basin"]["basin_name"]["th"],
            "lat": g["station"]["tele_station_lat"],
            "lon": g["station"]["tele_station_long"],
            "time_in": g["watergate_datetime_in"],
            "time_out": g["watergate_datetime_out"],
            "stale_in": stale_in,
            "stale_out": stale_out,
            "water_in_msl_m": w_in,
            "water_out_msl_m": w_out,
            "head_diff_m": round(w_in - w_out, 3) if w_in is not None and w_out is not None else None,
            "gate_state_reported": any(g.get(k) is not None for k in ("pump_on", "pump", "floodgate_open", "floodgate", "floodgate_height")),
        }

    summary = {
        "title": "ระดับน้ำหน้า/หลังประตูระบายหลักของคลองเชื่อมลุ่ม ณ เวลาเดียว (โทรมาตร สสน.)",
        "timestamp_analyzed": "2026-10-09 Snapshot",
        "source_file": "data/02_thaiwater/raw/2026-10-09_watergate_load.json",
        "key_gate_snapshots": gate_snapshots,
        "limits": [
            "ภาพชั่วขณะเดียว ไม่ใช่อนุกรมเวลา",
            "ค่าที่เวลาบันทึกไม่ตรงวันของภาพถูกตัดออก — ATG07 ไม่มีค่าหน้าประตูล่าสุด (ค่าว่าง เวลาค้างที่ 27 ธ.ค. 2560) จึงไม่มีผลต่างระดับ",
            "ระดับหน้า/หลังประตูเป็นค่าโทรมาตรตามที่รายงาน ยังไม่ได้ตรวจค่าอ้างอิงความสูงของเกจแต่ละประตูกับ ม.รทก.",
            "ไม่มีข้อมูลสถานะบานประตูและเครื่องสูบ จึงบอกไม่ได้ว่าประตูเปิดหรือปิด หรือมีการสูบน้ำอยู่",
            "ผลต่างระดับบอกทิศที่น้ำมีแนวโน้มไหลตามแรงโน้มถ่วงเมื่อประตูเปิดเท่านั้น ไม่ใช่อัตราการไหล",
        ],
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ บันทึกสรุประดับประตูลง {OUT_JSON.name}")

    if CANONICAL_FILE.exists():
        cdata = json.loads(CANONICAL_FILE.read_text(encoding="utf-8"))
        cdata["interbasin_transfer_vectors"] = summary
        CANONICAL_FILE.write_text(json.dumps(cdata, ensure_ascii=False, indent=1), encoding="utf-8")
        print("✅ อัปเดต canonical.json เรียบร้อย")

    md = ["# ระดับน้ำหน้า/หลังประตูระบายหลักของคลองเชื่อมลุ่ม (ภาพ ณ 9 ต.ค. 2569)", "",
          "> ที่มา: โทรมาตรประตูระบายน้ำ สสน. (ไฟล์ดิบตามแฮชใน data/02_thaiwater/manifest.md) · ข้อจำกัดดูในไฟล์ JSON ฟิลด์ limits", "",
          "| ประตู | เวลาบันทึกหลังประตู | ระดับหน้า (ม.รทก.) | ระดับหลัง (ม.รทก.) | ผลต่าง (ม.) |", "|---|---|---:|---:|---:|"]
    for code, g in gate_snapshots.items():
        f = lambda v: "—" if v is None else f"{v:.3f}"
        md.append(f"| {code} {g['name']} | {g['time_out']} | {f(g['water_in_msl_m'])} | {f(g['water_out_msl_m'])} | {f(g['head_diff_m'])} |")
    md += ["", "## ข้อจำกัด"] + [f"- {x}" for x in summary["limits"]]
    OUT_MD.write_text(chr(10).join(md) + chr(10), encoding="utf-8")
    print(f"✅ บันทึก {OUT_MD.name}")
    return summary


if __name__ == "__main__":
    analyze_interbasin_vectors()
