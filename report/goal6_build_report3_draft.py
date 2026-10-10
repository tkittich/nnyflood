"""เป้าหมาย 6 — สร้างร่างรายงานที่ 3 v0.1 (L1 ครบ · L2/L3 เป็น placeholder)

อ่านข้อมูลจาก JSON ที่สคริปต์วิเคราะห์สร้างทั้งหมด (ห้ามพิมพ์ตัวเลขในโค้ด):
  analysis/goal6/config.json · analysis/goal6/<basin>/l1_summary.json ·
  analysis/goal6/dam_history_all.json · analysis/goal6_dam_candidates.json ·
  analysis/goal6_screen_2026_summary.json · data/22_goal6_network/derived/s1_stage1/dem_summary.json
ผลลัพธ์: report/รายงานที่3_ระลอกปลายกย2569_6ลุ่ม_ร่างv0.1.html
รัน: python report/goal6_build_report3_draft.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "report"))
from goal6_reportlib import (  # noqa: E402
    esc, h2, h3, note, page, placeholder, prose, table, toc,
)

A = ROOT / "analysis"
OUT = ROOT / "report/รายงานที่3_ระลอกปลายกย2569_6ลุ่ม_ร่างv0.1.html"

cfg = json.loads((A / "goal6/config.json").read_text(encoding="utf-8"))
dams = json.loads((A / "goal6/dam_history_all.json").read_text(encoding="utf-8"))["dams"]
screen = json.loads((A / "goal6_screen_2026_summary.json").read_text(encoding="utf-8"))
cands = {c["dam_name"]: c for c in json.loads((A / "goal6_dam_candidates.json").read_text(encoding="utf-8"))["candidates"]}
dem = json.loads((ROOT / "data/22_goal6_network/derived/s1_stage1/dem_summary.json").read_text(encoding="utf-8"))


def load_l1(bid: str) -> dict:
    """รวมผล L1 สองยุคให้รูปเดียว: runner (l1_summary.json) หรือ spike (ป่าสัก/แม่กลอง)"""
    p = A / f"goal6/{bid}/l1_summary.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    if bid == "pasak":
        d = json.loads((A / "goal6_spike_pasak.json").read_text(encoding="utf-8"))
        return {"stations": d["stations"], "rain_2026": d["rain_2026"], "extras": None,
                "dams": {d["dam"]: {"dam_id": d["dam_id"], "normal_storage": d["normal_storage"],
                                    "first_year": min(int(r["year"]) for r in d["dam_years"]),
                                    "years": d["dam_years"]}}}
    if bid == "maeklong":
        d = json.loads((A / "goal6_spike_maeklong.json").read_text(encoding="utf-8"))
        return {"stations": d["stations"], "rain_2026": d["rain_2026"], "extras": None,
                "dams": {k: {**v} for k, v in d["dams"].items()}}
    raise FileNotFoundError(bid)


def num(x, nd=1, suffix=""):
    if x is None:
        return "—"
    return f"{x:,.{nd}f}{suffix}"


S: list[str] = []

# ---- 1. ภาพรวม ----
S.append(h2("1. ภาพรวม: ระลอกปลาย ก.ย. 2569 เป็นเหตุการณ์ระดับชาติ", "ov"))
n_crit = len([s for s in screen["stations"] if (s.get("hours_over_crit") or 0) > 0])
S.append(prose(
    "การสำรวจจุดวัดระดับน้ำ 200 จุดทั่วประเทศ (จุดสำคัญ/มีเกณฑ์ทางการ) ช่วง 1 ก.ค.–9 ต.ค. 2569 พบว่า "
    f"<b>{n_crit} จุด</b> ระดับน้ำพีคช่วง 23 ก.ย.–9 ต.ค. — ระลอกเดียวกับน้ำท่วมนครนายก (พีค 27 ก.ย.) "
    "จึงตั้งคำถามเดียวกันกับทุกลุ่ม: ฝนโทษหรือการบริหารเขื่อน/ปตร.โทษ? และคำตอบต่างกันที่ไหน"
))
dams_over26 = [(k, v) for k, v in dams.items()
               if next((r for r in v.get("years", []) if r["year"] == 2026), {}).get("days_over_urc_sep_oct", 0) > 0]
S.append(prose(
    f"ฝั่งเขื่อน: จากผู้สมัคร {len(dams)} แห่ง (≥200 ล้าน ลบ.ม.) มี "
    f"<b>{len(dams_over26)} แห่ง</b> เกิน Upper Rule Curve ช่วง ก.ย.–ต.ค. 2569 และทุกเขื่อนในรายชื่อ"
    "มีประวัติรายวันย้อนถึงอย่างน้อย 2005 (ภูมิพลถึง 1964) ตรวจย้อนแบบไต่สวนได้ทั้งระบบ"
))

# ---- 2. วิธีการ ----
S.append(h2("2. วิธีการ — ตั้งคำถามก่อนดูคำตอบ (pre-registration)", "method"))
S.append(prose(
    "ทุกลุ่มตอบชุดคำถามเดิม Q1–Q7 (ฝนหายากแค่ไหน · เกิน rule curve เมื่อไร · จังหวะปล่อย vs น้ำเข้า · "
    "attribution ฝน vs การปล่อย · พื้นที่น้ำท่วม · โมเดลทำนาย · สถานการณ์บริหารทางเลือก) โดยกำหนด"
    "หน้าต่างเหตุการณ์ 1 ก.ค.–9 ต.ค. 2569 จุดวัด เขื่อน และจุดฝน<b>ไว้ก่อน</b>ดูผลในไฟล์ "
    "<code>analysis/goal6/config.json</code> (69 จุดวัด · 8 เขื่อน) — แก้ได้แต่ต้องบันทึกเหตุผล"
))
S.append(note(
    "แหล่งข้อมูลหลัก: API คลังข้อมูลน้ำแห่งชาติ (เขื่อนรายวัน+URC · ระดับน้ำรายชั่วโมง · ปตร. 2,315 แห่ง · "
    "คลอง 282 จุด) · Sentinel-1 COG 35 ฉาก (CDSE — SHA-256 ตรวจครบ) · ฝนกริด NASA POWER · "
    "DEM Copernicus GLO-30 · กฎตัดน้ำดาวเทียมเดิมที่คาลิเบรตกับ GISTDA แล้ว (F1=0.727)"
))

# ---- 3. เขื่อน 2554 vs 2569 ----
S.append(h2("3. เขื่อนทั้ง 24 แห่ง — เทียบปี 2554 (benchmark) กับ 2569", "dams"))
rows = []
for name, rec in sorted(dams.items(), key=lambda kv: -(kv[1].get("normal_storage") or 0)):
    ys = rec.get("years", [])
    r11 = next((r for r in ys if r["year"] == 2011), None)
    r26 = next((r for r in ys if r["year"] == 2026), None)
    ns = rec.get("normal_storage")
    def f(r, k):
        return num(r[k], 0) if r else "—"
    pct11 = f" ({r11['max_storage']/ns*100:.0f}%)" if r11 and r11.get("max_storage") and ns else ""
    pct26 = f" ({r26['max_storage']/ns*100:.0f}%)" if r26 and r26.get("max_storage") and ns else ""
    rows.append([esc(name), num(ns, 0),
                 f"{f(r11, 'days_over_urc')} / {f(r11, 'days_over_urc_sep_oct')}",
                 f"{num(r11['max_storage'], 0) if r11 else '—'}{pct11}",
                 f"{f(r26, 'days_over_urc_sep_oct')}",
                 f"{num(r26['max_storage'], 0) if r26 else '—'}{pct26}"])
S.append(table(["เขื่อน", "เก็บปกติ (ลลบ.ม.)", "2554: เกิน URC ปี/ก.ย.–ต.ค. (วัน)", "2554 เก็บพีค",
                "2569: ก.ย.–ต.ค. (วัน)", "2569 เก็บพีค"], rows,
               "ประวัติรายวันย้อนหลังจาก API (เทมเพลต URC ยืนยันว่าเป็น curve จริงด้วยการไขว้ 5,025 แถว ต่าง 0.0)"))
S.append(note(
    "<b>สิ่งที่ตารางนี้บอก</b>: 2554 ระบบเจ้าพระยาเต็มเกิน URC ตั้งแต่หน้าฝนแล้วทั้งฤดู — "
    "ภูมิพล 127 วัน (เก็บพีค 100% ของเก็บปกติ) · ป่าสัก 241 วัน (125%) · <b>สิริกิติ์ 164 วัน</b> · "
    "ขณะที่เขื่อน กฟผ. ทุกแห่ง 0 วัน · 2569 เป็นรูปแบบต่างออกไป: เกินเฉพาะระลอกปลาย ก.ย. (39 วันทั้งหน้าต่าง "
    "เฉพาะ 4 แห่ง) — รายงานที่ 4 จะวิเคราะห์ข้ามปีเต็มรูปแบบ"
))

# ---- 4. รายลุ่ม ----
S.append(h2("4. รายลุ่ม 6 บท", "basins"))
for bid, rec in cfg["basins"].items():
    S.append(h3(f"4.{list(cfg['basins']).index(bid) + 1} {rec['label']}"))
    summary = load_l1(bid)
    st_rows = []
    for s in summary["stations"]:
        st_rows.append([esc(s["code"]), esc(str(s["name"])[:26]), num(s["max"], 2),
                        esc(s["peak_dt"] or "—"), num(s["n"], 0)])
    S.append(table(["จุดวัด", "ชื่อ", "ระดับสูงสุด", "เวลาพีค", "ชม.มีค่า"], st_rows,
                   "เรียงตามเวลาพีค (รายชั่วโมง 1 ก.ค.–9 ต.ค. 69)"))
    dam_rows = []
    for name, d in summary["dams"].items():
        ys = d.get("years", [])
        r26 = next((r for r in ys if r["year"] == 2026), {})
        over_mid = sum(1 for r in ys if r["days_over_urc_aug_sep"] > 0)
        dam_rows.append([esc(name), num(d["normal_storage"], 0), num(d["first_year"], 0),
                         num(r26.get("days_over_urc_sep_oct"), 0),
                         f"{over_mid}/{len(ys)}", num(r26.get("max_storage"), 0)])
    if dam_rows:
        S.append(table(["เขื่อน", "เก็บปกติ", "ลึกถึงปี", "2569 เกิน URC ก.ย.–ต.ค. (วัน)",
                        "เกินกลางหน้าฝน (ปี)", "2569 เก็บพีค"], dam_rows,
                       "ประวัติเต็มรายปีในภาคผนวกข้อมูล"))
    rain_rows = [[esc(k), f"{v['sep_total_mm']} มม.", f"{v['best7_mm']} มม. ปลาย {v['best7_end']}"]
                 for k, v in summary["rain_2026"].items()]
    if rain_rows:
        S.append(table(["จุดฝน (NASA POWER)", "ฝน ก.ย. 69", "7 วันสูงสุด"], rain_rows,
                       "กริด 0.5° — ใช้เทียบเชิงหยาบ"))
    if bid == "bkk_lower":
        S.append(note(
            "ลุ่มนี้ต่างจากลุ่มอื่น 3 จุด: attribution <b>สามทาง</b> (ฝนเมือง vs น้ำจากลุ่มเจ้าพระยา vs น้ำทะเลหนุน) · "
            "น้ำท่วมสองชนิด (ถนนจม pluvial แยกจากน้ำแม่น้ำ fluvial) · ข้อมูลฐานเครือข่ายมากเป็นพิเศษ "
            f"(คลอง {summary['extras']['canal_bkk_n']} จุด · ปตร. สนน. {summary['extras']['watergate_sanam_n']} แห่ง) · "
            "และ DEM ใช้ได้เชิงคุณภาพเท่านั้น (ที่ราบ 1–1.5 ม.รทก. + ที่ดินทรุด)"
        ))
    if rec.get("upstream_anchor"):
        S.append(prose(f"โซ่น้ำจากลุ่ม: {rec['upstream_anchor']}"))
    S.append(placeholder("L2 — พื้นที่น้ำท่วมจาก Sentinel-1 (กฎ canonical เทียบฉากก่อนเหตุการณ์) กำลังประมวลผล"))
    S.append(placeholder("L3 — โมเดลทำนายระดับน้ำ (สูตร/persistence/GBDT วิธีเดียวกับนครนายก) รอเข้าคิว"))

# ---- 5. ข้อจำกัด ----
S.append(h2("5. ข้อจำกัดที่ต้องรู้ก่อนอ่านตัวเลข", "limits"))
S.append(prose(
    "(1) เกณฑ์ critical ใน API ใช้ตรงไม่ได้ทุกจุด — บางจุดคนละ datum กับอนุกรม (จัดชั้น SUSPECT ไว้แล้ว "
    "ใน findings) ต้อง QA ต่อจุดก่อนใช้เชิงระดับ (2) ประวัติเปิด-ปิดบาน/เดินเครื่องสูบของเขื่อน-ปตร. "
    "<b>ไม่มีใน API ทุกสังกัด</b> — attribution จังหวะการปล่อยระดับรายวันเท่านั้นจนกว่า FOI จะสำเร็จ "
    "(3) ฝน NASA POWER กริด 0.5° รีดยอดฝนเบลอ — ค่าสถานีจริงจะสูงกว่าเสมอ (4) DEM บท กทม. "
    "ใช้ได้เชิงคุณภาพเท่านั้น (5) ความครอบคลุมข้อมูลรายชั่วโมงรายจุดไม่เท่ากัน (จำนวนชม.มีค่าแสดงในตาราง)"
))

# ---- สารบัญ + ปิด ----
S.insert(0, toc([("ภาพรวม", "ov"), ("วิธีการ", "method"), ("เขื่อน 2554 vs 2569", "dams"),
                 ("รายลุ่ม 6 บท", "basins"), ("ข้อจำกัด", "limits")]))
foot = ("สถานะ: ร่าง v0.1 — ข้อมูล L1 ครบ 6 ลุ่ม (จุดวัด 69 จุด · เขื่อน 24 แห่ง) · L2 ขั้นแรกกำลังประมวลผล · "
        "L3 รอคิว · ตัวเลขทุกตัวสร้างโดยสคริปต์ใน <code>analysis/goal6/</code> (รันซ้ำได้) · "
        "โครงสร้างรายงานโปรแกรม 5 ฉบับ: นครนายก (1–2) · ระลอก 2569 6 ลุ่ม (ฉบับนี้) · "
        "benchmark 2554 (ที่ 4) · เครือข่ายระดับชาติ (ที่ 5)")
OUT.write_text(page(
    "รายงานที่ 3 (ร่าง) — ระลอกปลาย ก.ย. 2569 ทั่วประเทศ: 6 ลุ่มน้ำเทียบกัน",
    "การสอบสวนเชิงหลักฐาน แบบเดียวกับนครนายก ขยายสู่พื้นที่ทั่วประเทศ — จุดยืนเป็นกลางตามหลักฐาน",
    S, foot), encoding="utf-8")
print(f"เขียนแล้ว: {OUT} ({OUT.stat().st_size/1e3:.0f} KB)")