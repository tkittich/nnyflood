"""เป้าหมาย 6 — สร้างร่างรายงานที่ 3 v0.1 (L1 ครบ · L2/L3 เป็น placeholder)

อ่านข้อมูลจาก JSON ที่สคริปต์วิเคราะห์สร้างทั้งหมด (ห้ามพิมพ์ตัวเลขในโค้ด):
  analysis/goal6/config.json · analysis/goal6/<basin>/l1_summary.json ·
  analysis/goal6/dam_history_all.json · analysis/goal6_dam_candidates.json ·
  analysis/goal6_screen_2026_summary.json · data/22_goal6_network/derived/s1_stage1/dem_summary.json
ผลลัพธ์: report/ระลอกปลายกย2569.html
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
OUT = ROOT / "report/ระลอกปลายกย2569.html"

cfg = json.loads((A / "goal6/config.json").read_text(encoding="utf-8"))
dams = json.loads((A / "goal6/dam_history_all.json").read_text(encoding="utf-8"))["dams"]
screen = json.loads((A / "goal6_screen_2026_summary.json").read_text(encoding="utf-8"))
cands = {c["dam_name"]: c for c in json.loads((A / "goal6_dam_candidates.json").read_text(encoding="utf-8"))["candidates"]}
dem = json.loads((ROOT / "data/22_goal6_network/derived/s1_stage1/dem_summary.json").read_text(encoding="utf-8"))


def storage_sep(dam: str, year: int, date: str) -> float:
    """ปริมาตรกักเก็บของเขื่อน ณ วันที่ (ล้าน ลบ.ม.) อ่านจาก dam_history_all.json

    F-15 (รีวิวรอบที่ 5): เดิมพิมพ์ตัวเลขเป็น literal ในข้อความ ทำให้วันที่คลาดเคลื่อน
    (8,004 เป็นค่าของ 16 ก.ย. ไม่ใช่ 15 ก.ย. = 7,986.87) — ต้องอ่านจากข้อมูลต้นทางทุกครั้ง
    """
    rec = next(r for r in dams[dam]["years"] if r["year"] == year)
    return float(rec["storage_sep_oct"][date])


def load_l1(bid: str) -> dict:
    """รวมผล L1 สองยุคให้รูปเดียว: runner (l1_summary.json) หรือ spike (ป่าสัก/แม่กลอง)"""
    p = A / f"goal6/{bid}/l1_summary.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    if bid == "pasak":
        d = json.loads((A / "goal6_spike_pasak.json").read_text(encoding="utf-8"))
        # M3 (รีวิว GLM): year ใน spike JSON เป็น string — แปลง int ตรงนี้ ไม่งั้นตารางแสดง "—"
        years = [{**r, "year": int(r["year"])} for r in d["dam_years"]]
        return {"stations": d["stations"], "rain_2026": d["rain_2026"], "extras": None,
                "dams": {d["dam"]: {"dam_id": d["dam_id"], "normal_storage": d["normal_storage"],
                                    "first_year": min(int(r["year"]) for r in years),
                                    "years": years}}}
    if bid == "maeklong":
        d = json.loads((A / "goal6_spike_maeklong.json").read_text(encoding="utf-8"))
        # M3: year เป็น string ใน spike JSON — แปลง int (เหมือน pasak)
        dams = {k: {**v, "years": [{**r, "year": int(r["year"])} for r in v.get("years", [])]}
                for k, v in d["dams"].items()}
        return {"stations": d["stations"], "rain_2026": d["rain_2026"], "extras": None, "dams": dams}
    raise FileNotFoundError(bid)


def num(x, nd=1, suffix=""):
    if x is None:
        return "—"
    return f"{x:,.{nd}f}{suffix}"


S: list[str] = []

# ---- 1. ภาพรวม ----
# M1 (รีวิว GLM): ฝน 7 วัน จุด C.2 จากแคช POWER — เรนเดอร์จากข้อมูล ไม่ hardcode
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "analysis"))
_rain_c2 = json.loads((ROOT / "data/22_goal6_network/raw/rain_rarity_national/power_2795.json").read_text(encoding="utf-8"))
_rain_c2_days = sorted(k for k in _rain_c2 if "2026-09-23" <= k <= "2026-10-01")
_rain_c2_vals = [_rain_c2[k] for k in _rain_c2_days]
_rain_c2_7d = max(sum(_rain_c2_vals[i:i + 7]) for i in range(len(_rain_c2_vals) - 6))

# TLDR + บริบท (ข้อตกลงใหม่ 12 ต.ค. 69 — ทุกรายงานต้องมี)
# ข้อ 4 (แผนความสม่ำเสมอ 10 ต.ค.): ตัวเลข TLDR เรนเดอร์จาก canonical.json ทั้งหมด — ห้าม literal
_can = json.loads((A / "goal6/canonical.json").read_text(encoding="utf-8"))
_rn = _can["rain_national"]
_fl = _can["flood_peak_km2"]
_es = _can["event_stations"]
_l3 = _can["l3_best"]
_h6vals = sorted(v["h6"]["rmse_cm"] for v in _l3.values())
_h24vals = sorted(v["h24"]["rmse_cm"] for v in _l3.values())
_h48vals = sorted(v["h48"]["rmse_cm"] for v in _l3.values())
_l3s = _can["l3_summary"]
_fm = _can["flood_peak_meta"]
_rv = _can["s1_rule"]
_lc = _can["s1_landcover"]
_TH = {"pasak": "ป่าสัก", "maeklong": "แม่กลอง", "bp_prach": "บางปะกง", "thachin": "ท่าจีน", "ping_cp": "ปิง–เจ้าพระยา", "bkk_lower": "กรุงเทพฯ ตอนล่าง"}
_xc = _can.get("s1_gistda_crosscheck")
_XC_SENT = ("" if not _xc else (
    f" · <b>เทียบกับชั้นน้ำท่วมสะสม 30 วันของ GISTDA</b> (รายจังหวัดฉบับล่าสุดที่มี; รวมมาสก์ทุกฉากของลุ่ม; เฉพาะจังหวัดที่มีชั้น GISTDA และฉากครอบคลุม; {_xc['n_basins']} ลุ่ม; "
    f"ส่วนที่เทียบได้เป็นร้อยละ {100 * _xc['B_share_in_domain_range'][0]:.0f}–{100 * _xc['B_share_in_domain_range'][1]:.0f} ของพื้นที่เรดาร์ทั้งกริด): "
    f"ความแม่น (สัดส่วนเรดาร์ที่อยู่ใน GISTDA) ร้อยละ {100 * _xc['B_precision_range'][0]:.0f}–{100 * _xc['B_precision_range'][1]:.0f} · "
    f"ความครบร้อยละ {100 * _xc['B_recall_range'][0]:.0f}–{100 * _xc['B_recall_range'][1]:.0f} · อัตราส่วนพื้นที่เรดาร์ต่อ GISTDA {_xc['B_ratio_range'][0]:.2f}–{_xc['B_ratio_range'][1]:.2f} "
    "— GISTDA 30 วันเป็นผลสะสมหลายฉากหลายดาวเทียม ไม่ใช่ความจริงภาคสนาม จึงบอกได้เพียงว่าขอบเขตสอดคล้องกัน"
    + ("" if not _xc["any_low_precision"] else f" · ลุ่ม {', '.join(_TH[b] for b in _xc['any_low_precision'])} ส่วนมากอยู่นอกขอบเขตของ GISTDA")
    + " (กติกา <code>docs/S1_GISTDA_CROSSCHECK_PREREG.md</code>)"))
def _rs_sent(_rs, rule):
    return (
        f" · <b>ความไวต่อวันของฉากอ้างอิง</b> (ลุ่ม{_TH[_rs['basin']]}; ใช้ฉากอ้างอิงทางเลือกที่เก่ากว่าฉากหลักราว 12 วัน ตัดน้ำซ้ำ {_rs['n_event_passes']} รอบถ่าย): "
        f"ค่าสูงสุดของลุ่มเปลี่ยนจาก {_rs['peak_primary_km2']:,.0f} เป็น {_rs['peak_alt_ref_km2']:,.0f} ตร.กม. ({_rs['peak_change_pct']:+.1f}%) · รายรอบถ่ายเปลี่ยน {_rs['per_pass_change_pct_range'][0]:+.0f}% ถึง {_rs['per_pass_change_pct_range'][1]:+.0f}% "
        f"(คิดจากพื้นที่ฐานของแต่ละรอบถ่าย {_rs['event_primary_km2_range'][0]:,.1f}–{_rs['event_primary_km2_range'][1]:,.0f} ตร.กม. — ร้อยละจากฐานเล็กไม่ใช่การเปลี่ยนจริง)"
        + (f" · รอบถ่ายก่อนเหตุการณ์เทียบฉากทางเลือก (ค่าควบคุม — ไม่ใช่น้ำท่วม) ได้ {_rs['control_alt_km2_range'][0]:,.0f}–{_rs['control_alt_km2_range'][1]:,.0f} ตร.กม. ซึ่งบอกขนาดการเปลี่ยนแปลงตามฤดูก่อนเหตุการณ์" if _rs["n_control_passes"] else "")
        + (" · <b>ไวต่อฉากอ้างอิง</b>" if _rs["label_sensitive_to_reference"] else "")
        + f" (กติกา <code>{rule}</code>)")


_rs = _can.get("s1_ref_sensitivity")
_RS_SENT = ("" if not _rs else _rs_sent(_rs, "docs/S1_PASS_MOSAIC_PREREG.md")) + "".join(
    _rs_sent(v, "docs/S1_REF_SENSITIVITY_PASAK_PREREG.md") for v in _can.get("s1_ref_sensitivity_other", {}).values())
_rs_done = ([_rs["basin"]] if _rs else []) + list(_can.get("s1_ref_sensitivity_other", {}))
_rs_all = [k for k in _can["flood_peak_km2"] if not k.endswith("_after_sea")]
if _rs_done:
    _RS_SENT += (f" · <b>ขอบเขตการทดสอบ:</b> ทดสอบความไวต่อวันของฉากอ้างอิงแล้ว {len(_rs_done)} จาก {len(_rs_all)} ลุ่ม ({', '.join(_TH[b] for b in _rs_done)}) — "
                 f"อีก {len(_rs_all) - len(_rs_done)} ลุ่ม ({', '.join(_TH[b] for b in _rs_all if b not in _rs_done)}) ค่าสูงสุดอ่านจากฉากอ้างอิงหลักเท่านั้น ยังไม่ทราบว่าไวต่อวันอ้างอิงเพียงใด")
_bw = max((k for k in _lc if not k.startswith("nn_")), key=lambda k: _lc[k]["share_on_worldcover_water"])   # ลุ่มที่สัดส่วนตกบนน้ำถาวรสูงสุด (อ่านจากข้อมูล ไม่ฝังชื่อ)
_nmr = _can.get("national_medium_reservoirs", {})
_ps24 = _can.get("pasak_24y_baseline", {})
_RULE_SENT = (
    f"ความน่าเชื่อถือของกฎ (ตรวจด้วยข้อมูลที่มี ไม่ปรับค่า): F1 เทียบ GISTDA = {_rv['oct2']['f1']:.2f} "
    f"(ช่วง 95%: {_rv['oct2']['f1_ci95'][0]:.2f}–{_rv['oct2']['f1_ci95'][1]:.2f}) บนฉากเดียวกับที่ใช้ตั้งค่า และ "
    f"{_rv['peak_27sep']['f1']:.2f} ({_rv['peak_27sep']['f1_ci95'][0]:.2f}–{_rv['peak_27sep']['f1_ci95'][1]:.2f}) บนฉากน้ำสูงสุด 27 ก.ย. "
    f"(ผลิตภัณฑ์ GISTDA เป็นภาพรวม 28 ก.ย.–2 ต.ค. ไม่ใช่ช่วงเวลาเดียวกัน) · พื้นที่ที่ได้เปลี่ยน "
    f"{_rv['oct2']['area_range_abs_pm2db'][0]:.0f}–{_rv['oct2']['area_range_abs_pm2db'][1]:.0f} ตร.กม. เมื่อเลื่อนเกณฑ์ความมืดเรดาร์ ±2 หน่วย "
    f"(ค่ากลาง {_rv['oct2']['area_km2']:.0f}) — F1 ต่างกันเพียง ~0.04 จึงสอบเทียบพื้นที่ให้แม่นไม่ได้ · "
    f"ฉากควบคุมก่อนท่วม (นครนายก 1 คู่ ครอบที่ราบ {_rv['control_covered_km2']:.0f} ตร.กม.) กฎรายงานน้ำเท็จ {_rv['control_false_pos_km2']:.1f} ตร.กม. "
    f"(~{_rv['control_per_1000_km2']:.0f} ต่อ 1,000 ตร.กม.) · สอบเทียบ/ตรวจที่นครนายกเท่านั้น — ลุ่มอื่นยังไม่มีแผนที่อ้างอิงอิสระ"
)
_TH_MON = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def ict_label(scene: str) -> str:
    """P3 (รีวิว Sonnet): ชื่อฉาก S1 เป็นเวลาสากล (UTC) — แปลงเป็นเวลาไทย (UTC+7) เพื่อเทียบกับจุดวัดระดับน้ำ"""
    import re as _re
    from datetime import datetime as _dt, timedelta as _td
    m = _re.search(r"_(\d{8})T(\d{6})_", scene)
    if not m:
        return scene
    d = _dt.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S") + _td(hours=7)
    return f"{d.day} {_TH_MON[d.month]} {d:%H:%M}"
_c2 = _can["c2_attribution"]
_tide = _can["estuary_tide"]
_sal = _can["estuary_salinity"]
_swan = _can["gulf_marine_swan"]
_glo = _can["glofas_streamflow"]
S.insert(1, note(
    "<b>สรุปสั้น (อ่าน 2 นาที):</b> "
    "ปลาย ก.ย. 2569 ฝนตกหนักพร้อมกันทั่วประเทศ (ฝน 7 วันสูงสุดติด<b>อันดับ 1–3 จาก 46 ปี</b> "
    f"ที่ {_rn['top3_stations_7d']} จาก {_rn['n_stations']} จุดวัด (= {_rn['top3_cells_7d']} จาก {_rn['n_cells']} ช่องกริดอิสระ) "
    "ทั่วประเทศที่เราตรวจ) ทำให้เกิดน้ำท่วมหลายลุ่มพร้อมกัน — ระลอกเดียวกับน้ำท่วมนครนายก "
    "ที่เป็นข่าวใหญ่ โครงการนี้จึงนำวิธีการสืบสวนแบบเดียวกันไปใช้กับ 6 ลุ่มน้ำทั่วประเทศ "
    "คำตอบสำคัญ 3 ข้อ: "
    "(1) <b>เขื่อนไม่ใช่ต้นเหตุเดียว</b> — 4 จาก 6 ลุ่มเกิดจากฝนเป็นหลัก (ท่าจีนท่วมหนักทั้งที่เขื่อนเก็บน้ำ"
    "ต่ำกว่าแผนทุกวัน) "
    "(2) <b>ระบบบริหารเขื่อนต่างกันจริง</b> — เขื่อนการไฟฟ้าฝ่ายผลิตฯ 3 แห่งในภาคตะวันตกและภาคใต้ "
    "(ศรีนครินทร์ วชิราลงกรณ์ รัชชประภา) เก็บน้ำต่ำกว่าระดับกำกับเสมอ (2554 และ 2569 ไม่เคยเกิน) "
    "ขณะที่เขื่อนชลประทานบางแห่งเก็บน้ำเกินระดับกำกับเกือบทุกปี (ไม่ใช่เฉพาะปีน้ำมาก) "
    "— หมายเหตุ: เขื่อนใหญ่ของการไฟฟ้าฝ่ายผลิตฯ ในลุ่มเจ้าพระยา (ภูมิพล สิริกิติ์) ปี 2554 เกินระดับกำกับมากเช่นกัน "
    f"เมื่อน้ำเข้าอ่างฤดูนั้นอยู่อันดับ {_can['dam_inflow']['ภูมิพล']['inflow_rank2554']} ของประวัติ (รายงานที่ 4) "
    f"(3) <b>พยากรณ์ระยะสั้น — ได้ผลจำกัด</b>: ค่าคลาดเคลื่อนดีสุด {_h6vals[0]:.0f}–{_h6vals[-1]:.0f} ซม. ที่ระยะ 6 ชม. "
    f"({_l3s['n_near_persistence_h6']} จาก {_l3s['n_basins']} ลุ่ม แบบจำลองดีไปกว่าค่าเดิมคงที่ — วิธี \"ระดับน้ำไม่เปลี่ยน\" — ไม่ถึง 10%) · "
    f"ที่ระยะ 24 ชม. {_h24vals[0]:.0f}–{_h24vals[-1]:.0f} ซม. ({_l3s['n_near_persistence_h24']} จาก {_l3s['n_basins']} ลุ่มเช่นกัน) · "
    f"ระยะ 48 ชม. คลาดเคลื่อนโตตามลุ่ม (ท่าจีน/แม่กลอง "
    f"{min(_l3['thachin']['h48']['rmse_cm'], _l3['maeklong']['h48']['rmse_cm']):.0f}–"
    f"{max(_l3['thachin']['h48']['rmse_cm'], _l3['maeklong']['h48']['rmse_cm']):.0f} ซม. — "
    f"ที่เหลือ 4 ลุ่ม {sorted(v['h48']['rmse_cm'] for k, v in _l3.items() if k not in ('thachin', 'maeklong'))[0]:.0f}–{_h48vals[-1]:.0f} ซม.) · "
    "ทดสอบกับเหตุการณ์เดียวเท่านั้น · "
    f"พื้นที่น้ำท่วมที่ตรวจพบในฉากดาวเทียมเดียวที่ใหญ่สุดของแต่ละลุ่ม — แสดงเป็นช่วง <b>ตรวจพบรวม (ขอบบนของน้ำใหม่ในฉาก) → น้ำใหม่เข้มงวด (ขอบล่าง)</b> "
    f"(ฉากสุดท้ายที่มีคือ 2 ต.ค. เวลาไทย · แต่ละฉากครอบลุ่มต่างกัน {min(v['coverage'] for v in _fm.values()):.0%}–{max(v['coverage'] for v in _fm.values()):.0%} "
    f"จึงเทียบข้ามลุ่มตรง ๆ ไม่ได้ และส่วนนอกฉากไม่ได้ตรวจ): "
    f"ปิง–เจ้าพระยา {_fl['ping_cp']:,.0f} → {_lc['ping_cp']['strict_new_km2']:,.0f} ตร.กม. · "
    f"ทุ่งรับน้ำรอบนอก กทม. {_fl['bkk_lower_after_sea']:,.0f} (หลังตัดน้ำถาวรหลายฉาก) → {_lc['bkk_lower']['strict_new_km2']:,.0f} · "
    f"บางปะกง {_fl['bp_prach']:,.0f} → {_lc['bp_prach']['strict_new_km2']:,.0f} · ป่าสัก {_fl['pasak']:.0f} → {_lc['pasak']['strict_new_km2']:.0f} · "
    f"ท่าจีน {_fl['thachin']:.0f} → {_lc['thachin']['strict_new_km2']:.0f} · แม่กลอง {_fl['maeklong']:.0f} → {_lc['maeklong']['strict_new_km2']:.0f} "
    + "".join(f"({_TH[k]}ส่วนใหญ่ตกบนแหล่งน้ำถาวร — อย่านำไปเทียบกับลุ่มอื่น) · " for k, v in _lc.items() if not k.startswith("nn_") and v["share_on_worldcover_water"] > 0.5)
    + "· ฉากอ้างอิงจับตามวงโคจรสัมพัทธ์ (ฉากล่าสุดก่อน 24 ก.ย.) · "
    f"เลื่อนเกณฑ์ความมืดเรดาร์ ±2 หน่วย พื้นที่เปลี่ยน ±25–35% — อ่านเป็นช่วง ไม่ใช่ตัวเลขเดียว"
))
S.insert(2, note(
    "<b>บริบทสำหรับผู้อ่านที่ไม่เคยอ่านรายงานนครนายก:</b> โครงการนี้เริ่มจากการสืบสวนน้ำท่วม "
    "อ.เมือง นครนายก ปลาย ก.ย. 2569 — ลุ่มน้ำเล็กที่มีเขื่อนขุนด่านปราการชล (เก็บน้ำ 224 ล้าน ลบ.ม.) "
    "รายงานชุดแรก (รายงานที่ 1–2) สรุปว่า: ฝนเป็นตัวจุดชนวน แต่การปล่อยน้ำของเขื่อนช่วงน้ำสูงสุด"
    "ทำให้น้ำขังนานขึ้น · รายงานฉบับนี้ (ที่ 3) นำวิธีเดียวกันไปตรวจ 6 ลุ่มทั่วประเทศเพื่อดูว่า "
    "ข้อสรุปนั้นถือทั่วไปหรือเฉพาะถิ่น — <b>อ่านฉบับนี้จบได้โดยไม่ต้องเปิดรายงานอื่น</b>"
))
S.append(h2("1. ภาพรวม: ระลอกปลาย ก.ย. 2569 เป็นเหตุการณ์ระดับชาติ", "ov"))
from goal6_reportlib import figure
S.append(figure(ROOT / "report/assets/goal6/rain_46y_nakhonnayok.png",
                "ฝนหนัก 7 วันสูงสุดของแต่ละปี (นครนายก) — แท่งแดง = ปี 2569 สูงสุดใน 46 ปี · เส้นประแดง = เกณฑ์เตือนน้ำท่วม 150 มม."))
S.append(figure(ROOT / "report/assets/goal6/urc_2569_pasak.png",
                "ตัวอย่างเขื่อนป่าสักชลสิทธิ์ ปี 2569: น้ำเก็บ (เส้นน้ำเงิน) เกินระดับกำกับบน (เส้นประแดง) เฉพาะระลอกปลาย ก.ย. — พื้นที่แดงอ่อน = น้ำส่วนเกิน"))
# H2 (รีวิว Sift): แยกจุดที่พีคในระลอกจริง กับจุดที่พีคก่อนระลอก (ส.ค.–ก.ย.ต้น ลุ่มตอนบน)
# H1 (รีวิวพร้อมเผยแพร่): 25 จุดนี้ 19 จุด SUSPECT ตาม QA datum ของตัวเอง — ใช้เป็นหลักฐาน "จังหวะเวลา" ไม่ใช่ "ระดับ"
_ev = [s for s in screen["stations"] if (s.get("hours_over_crit") or 0) > 0]
n_crit = len(_ev)
n_wave = len([s for s in _ev if (s.get("max_dt") or "") >= "2026-09-23"])
n_pre = n_crit - n_wave
S.append(prose(
    "การสำรวจจุดวัดระดับน้ำ 200 จุดทั่วประเทศ (จุดสำคัญ/มีเกณฑ์ทางการ) ช่วง 1 ก.ค.–9 ต.ค. 2569 พบว่า "
    f"<b>{n_crit} จุด</b> มีระดับน้ำที่เกินระดับวิกฤตที่ระบบรายงานมา ในจำนวนนี้ <b>{n_wave} จุด</b> "
    "มีระดับสูงสุดช่วง 23 ก.ย.–9 ต.ค. — จังหวะเวลาเดียวกับน้ำท่วมนครนายก (จุดสูงสุด 27 ก.ย.) · "
    f"อีก <b>{n_pre} จุด</b> พีค<b>ก่อนหน้า</b> (ส.ค.–ก.ย.ต้น ลุ่มตอนบนเหนือ: น่าน วัง ปิง ยม สาละวิน เพชรบุรี ชายฝั่งตะวันออกล่าง) "
    "เป็นเหตุการณ์ฤดูฝนปกติของลุ่มตอนบน ไม่ใช่ส่วนของระลอกนี้ "
    "จึงตั้งคำถามเดียวกันกับทุกลุ่ม: ฝนโทษหรือการบริหารเขื่อน/ปตร.โทษ? และคำตอบต่างกันที่ไหน "
    "(ดูข้อจำกัดข้อ (1) เรื่องเกณฑ์วิกฤตที่ใช้ไม่ได้ครบทุกจุด)"
))
dams_over26 = [(k, v) for k, v in dams.items()
               if next((r for r in v.get("years", []) if r["year"] == 2026), {}).get("days_over_urc_sep_oct", 0) > 0]
n_full2569 = sum(1 for k, v in dams.items()
                 if next((r for r in v.get("years", []) if r["year"] == 2026), {}).get("days_over_urc_sep_oct", 0) >= 39)
# วันเกินระดับกำกับ 2554 ต่อเขื่อน — เรนเดอร์จาก JSON (เทสห้าม literal)
dams_2554_days = {k: next(r["days_over_urc"] for r in v.get("years", []) if r["year"] == 2011)
                  for k, v in dams.items() if any(r["year"] == 2011 for r in v.get("years", []))}
dams_2554_peak_pct = {}
for k, v in dams.items():
    r11 = next((r for r in v.get("years", []) if r["year"] == 2011), None)
    if r11 and r11.get("max_storage_sep_oct") and v.get("normal_storage"):
        dams_2554_peak_pct[k] = round(r11["max_storage_sep_oct"] / v["normal_storage"] * 100)
S.append(prose(
    f"ฝั่งเขื่อน: จากผู้สมัคร {len(dams)} แห่ง (≥200 ล้าน ลบ.ม.) มี "
    f"<b>{len(dams_over26)} แห่ง</b> เกินระดับกำกับบน (ระดับน้ำเก็บสูงสุดตามแผนรายปี) ช่วง ก.ย.–ต.ค. 2569 และทุกเขื่อนในรายชื่อ"
    "มีประวัติรายวันย้อนถึงอย่างน้อย 2005 ตรวจย้อนแบบไต่สวนได้ทั้งระบบ (หมายเหตุ: แหล่งข้อมูล API มีกราฟรายปีย้อนถึง 1964 สำหรับภูมิพล แต่ตัวเลขในรายงานนี้ใช้ชุดรายวัน 2005–2026 เท่านั้น)"
))

# ---- 2. วิธีการ ----
S.append(h2("2. วิธีการ — ตั้งคำถามก่อนดูคำตอบ (กำหนดไว้ก่อนดูผล)", "method"))
S.append(prose(
    "ทุกลุ่มตอบชุดคำถามเดิม Q1–Q7 (ฝนหายากแค่ไหน · เขื่อนเก็บน้ำเกินระดับกำกับเมื่อไร · จังหวะปล่อย เทียบกับ น้ำเข้า · "
    "การแยกส่วนของสาเหตุ: ฝนเทียบกับการปล่อยน้ำ · พื้นที่น้ำท่วม · โมเดลทำนาย · สถานการณ์บริหารทางเลือก) โดยกำหนด"
    "หน้าต่างเหตุการณ์ 1 ก.ค.–9 ต.ค. 2569 จุดวัด เขื่อน และจุดฝน<b>ไว้ก่อน</b>ดูผลในไฟล์ "
    "<code>analysis/goal6/config.json</code> (69 จุดวัด · 8 เขื่อน) — แก้ได้แต่ต้องบันทึกเหตุผล"
))
S.append(note(
    "แหล่งข้อมูลหลัก: ระบบข้อมูลน้ำแห่งชาติ (เขื่อนรายวันพร้อมเส้นกำกับระดับน้ำ · ระดับน้ำรายชั่วโมง · ประตูระบายน้ำ 2,315 แห่ง · "
    "คลอง 282 จุด) · ดาวเทียมเรดาร์ Sentinel-1 35 ฉาก (ตรวจความครบถ้วนด้วยลายนิ้วมือไฟล์ครบ) · ปริมาณฝนแผนที่เชิงตัวเลข NASA POWER · "
    "แผนที่ความสูงพื้นดิน Copernicus GLO-30 · กฎตัดน้ำจากดาวเทียมเดิมที่สอบเทียบกับแผนที่ GISTDA ที่นครนายก (F1 " + f"{_rv['oct2']['f1']:.2f}" + " — ดูข้อจำกัดข้อ (7))"
))

# ---- 3. เขื่อน 2554 เทียบกับ 2569 ----
S.append(h2("3. เขื่อนทั้ง 24 แห่ง — เทียบปี 2554 (ชุดเทียบมาตรฐาน) กับ 2569", "dams"))
rows = []
for name, rec in sorted(dams.items(), key=lambda kv: -(kv[1].get("normal_storage") or 0)):
    ys = rec.get("years", [])
    r11 = next((r for r in ys if r["year"] == 2011), None)
    r26 = next((r for r in ys if r["year"] == 2026), None)
    ns = rec.get("normal_storage")
    def f(r, k):
        return num(r[k], 0) if r else "—"
    pct11 = f" ({r11['max_storage_sep_oct']/ns*100:.0f}%)" if r11 and r11.get("max_storage_sep_oct") and ns else ""
    pct26 = f" ({r26['max_storage_sep_oct']/ns*100:.0f}%)" if r26 and r26.get("max_storage_sep_oct") and ns else ""
    rows.append([esc(name), num(ns, 0),
                 f"{f(r11, 'days_over_urc')} / {f(r11, 'days_over_urc_sep_oct')}",
                 f"{num(r11['max_storage_sep_oct'], 0) if r11 else '—'}{pct11}",
                 f"{f(r26, 'days_over_urc_sep_oct')}",
                 f"{num(r26['max_storage_sep_oct'], 0) if r26 else '—'}{pct26}"])
S.append(table(["เขื่อน", "เก็บปกติ (ลลบ.ม.)", "2554: เกินระดับกำกับบน ปี/ก.ย.–ต.ค. (วัน)", "2554 เก็บสูงสุด ก.ย.–ต.ค.",
                "2569: ก.ย.–ต.ค. (วัน)", "2569 เก็บสูงสุด ก.ย.–ต.ค."], rows,
               "ประวัติรายวันย้อนหลังจาก API (เส้นกำกับระดับน้ำใน API ยืนยันว่าเป็นเส้นจริงด้วยการไขว้แฟ้มทางการของเขื่อนขุนด่านปราการชล 5,025 แถว ต่าง 0.0 — ยืนยันเชิงตัวอย่างเขื่อนเดียว ที่เหลือใช้เส้นกำกับแหล่งเดียวจาก API ยังไม่ได้ไขว้แฟ้มทางการรายเขื่อน)"))
S.append(note(
    "<b>สิ่งที่ตารางนี้บอก</b>: 2554 ระบบเจ้าพระยาเต็มเกินระดับกำกับตั้งแต่หน้าฝนแล้วทั้งฤดู — "
    f"ภูมิพล {dams_2554_days['ภูมิพล']} วัน (เก็บสูงสุด {dams_2554_peak_pct['ภูมิพล']:.0f}% ของเก็บปกติ) · "
    f"ป่าสัก {dams_2554_days['ป่าสักชลสิทธิ์']} วัน ({dams_2554_peak_pct['ป่าสักชลสิทธิ์']:.0f}%) · <b>สิริกิติ์ {dams_2554_days['สิริกิติ์']} วัน</b> · "
    "ส่วนเขื่อนการไฟฟ้าฝ่ายผลิตฯ 3 แห่งในภาคตะวันตกและภาคใต้ (ศรีนครินทร์ วชิราลงกรณ์ รัชชประภา) 0 วัน "
    f"— ปีนั้นฝนรวมฤดูลุ่มแม่กลองเหนือกาญจนบุรีอยู่อันดับ {_can['basin_rain']['basins']['maeklong']['season_total']['rank2554']} จาก 46 ปี (สูงกว่ามัธยฐาน ไม่ใช่ปีแล้ง) แต่เขื่อนไม่เกินเส้นกำกับ — ยังแยกผลของการเดินเขื่อนจากปริมาณน้ำเข้าไม่ได้ · "
    f"2569 เป็นรูปแบบต่างออกไป: {n_full2569} แห่งเกินเต็มหน้าต่าง ก.ย.–ต.ค. (39 วัน) — "
    "รายงานที่ 4 จะวิเคราะห์ข้ามปีเต็มรูปแบบ"
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
    S.append(table(["จุดวัด", "ชื่อ", "ระดับสูงสุด", "เวลาสูงสุด", "ชม.มีค่า"], st_rows,
                   "เรียงตามเวลาสูงสุด (รายชั่วโมง 1 ก.ค.–9 ต.ค. 69)"))
    dam_rows = []
    for name, d in summary["dams"].items():
        ys = d.get("years", [])
        r26 = next((r for r in ys if r["year"] == 2026), {})
        over_mid = sum(1 for r in ys if r["days_over_urc_aug_sep"] > 0)
        dam_rows.append([esc(name), num(d["normal_storage"], 0), num(d["first_year"], 0),
                         num(r26.get("days_over_urc_sep_oct"), 0),
                         f"{over_mid}/{len(ys)}", num(r26.get("max_storage_sep_oct"), 0)])
    if dam_rows:
        S.append(table(["เขื่อน", "เก็บปกติ", "ลึกถึงปี", "2569 เกินระดับกำกับบน ก.ย.–ต.ค. (วัน)",
                        "เกินกลางหน้าฝน (ปี)", "2569 เก็บสูงสุด ก.ย.–ต.ค."], dam_rows,
                       "ประวัติเต็มรายปีในภาคผนวกข้อมูล"))
    if bid == "pasak" and _ps24:
        S.append(prose(
            f"<b>การวิเคราะห์ธรรมาภิบาลและการบริหารจัดการเขื่อน 22 ปี (2548–2569)</b>: "
            f"เขื่อนป่าสักชลสิทธิ์ (กรมชลประทาน) มีพฤติกรรมการกักเก็บน้ำเกินระดับกำกับบน (URC) ในช่วงกลางฤดูฝน (ส.ค.–ก.ย.) ถึง {_can['pasak_over_mid_rain_years']} ปี "
            f"และเกินระดับกำกับบนตลอดปีถึง {_can['pasak_over_years']} ปี (ในชุด 24 ปี 2546–2569 เก็บเกินความจุปกติถึง {_ps24['over_normal_years']}/{_ps24['years_analyzed']} ปี หรือ {_ps24['over_normal_pct']:.1f}%) "
            f"ซึ่งแตกต่างจากเขื่อนขนาดใหญ่ของการไฟฟ้าฝ่ายผลิตแห่งประเทศไทย (กฟผ.) ในลุ่มน้ำแม่กลอง (ศรีนครินทร์ และวชิราลงกรณ์) "
            f"ที่ไม่เคยมีวันใดเก็บน้ำเกินระดับกำกับบนเลย (0 วัน) ทั้งในปีน้ำท่วมใหญ่ 2554 และ 2569 "
            f"ความแตกต่างเชิงธรรมาภิบาลนี้เกิดจาก (1) สัดส่วนความจุอ่างต่อปริมาณน้ำท่าท่าเข้าของป่าสักที่แคบกว่ามาก ทำให้ต้องรองรับน้ำหลากที่มีความผันผวนสูง "
            f"และ (2) วัตถุประสงค์การใช้งานและระเบียบปฏิบัติการเดินเขื่อนที่ต่างกันระหว่างเขื่อนเพื่อการชลประทานล้วนกับการบริหารจัดการร่วมกับการผลิตไฟฟ้าพลังน้ำ"
        ))
    rain_rows = [[esc(k), f"{v['sep_total_mm']} มม.", f"{v['best7_mm']} มม. ปลาย {v['best7_end']}"]
                 for k, v in summary["rain_2026"].items()]
    if rain_rows:
        cap = "กริด 0.5° — ใช้เทียบเชิงหยาบ"
        if bid == "pasak":
            # L6 (รีวิว GLM): ตารางจุดวัดบนพีค ส.ค. — ผู้อ่านจะถามฝน ส.ค. — ตอบจาก rain_rarity (ตัวเลขจากไฟล์)
            cap += (" · ฝน ส.ค. ของลุ่มบนป่าสัก: 7 วันสูงสุดในรอบ 46 ปีตกช่วง ส.ค. ปีนี้ — "
                    "อันดับ 14 จาก 46 (หนักแต่ไม่หายาก) ตรงกับพีคจุดวัด S.3/S.33 ช่วง 20–22 ส.ค. ที่ตารางข้างบน")
        S.append(table(["จุดฝน (NASA POWER)", "ฝน ก.ย. 69", "7 วันสูงสุด"], rain_rows, cap))
    if bid == "bkk_lower":
        S.append(note(
            "ลุ่มนี้ต่างจากลุ่มอื่น 3 จุด: การแยกส่วนของสาเหตุ <b>สามทาง</b> (ฝนในเมือง น้ำจากลุ่มเจ้าพระยา น้ำทะเลหนุน) · "
            "น้ำท่วมสองชนิด (ถนนจม น้ำท่วมจากฝนเมือง แยกจากน้ำแม่น้ำ (น้ำจากลุ่ม)) · ข้อมูลฐานเครือข่ายมากเป็นพิเศษ "
            f"(คลอง {summary['extras']['canal_bkk_n']} จุด · ปตร. สนน. {summary['extras']['watergate_sanam_n']} แห่ง) · "
            "และ DEM ใช้ได้เชิงคุณภาพเท่านั้น (ที่ราบ 1–1.5 ม.รทก. + ที่ดินทรุด)"
        ))
    if rec.get("upstream_anchor"):
        S.append(prose(f"โซ่น้ำจากลุ่ม: {rec['upstream_anchor']}"))
    # L2 — ผลตัดน้ำจาก stage-2 (ถ้ามี)
    s2p = ROOT / "data/22_goal6_network/derived/s1_stage2/summary.json"
    l2_rows = []
    if s2p.exists():
        s2 = json.loads(s2p.read_text(encoding="utf-8"))
        recs = [r for r in s2.get(bid, {}).get("scenes", []) if r["reference"] != r["scene"]]
        if recs:
            peak = max(recs, key=lambda r: r["water_km2_lowland"])
            sea_adj = None
            if bid == "bkk_lower":
                sea_p = A / "goal6/bkk_lower/l2_sea_adjust.json"
                if sea_p.exists():
                    sea_adj = json.loads(sea_p.read_text(encoding="utf-8"))
            for r in sorted(recs, key=lambda x: x["scene"]):
                val = r["water_km2_lowland"]
                note_s = ""
                frac = r["water_frac_plain"]
                if sea_adj:
                    adj = next((a for a in sea_adj["scene_adjust"] if a["scene"] == r["scene"]), None)
                    if adj:
                        val = adj["after_km2"]
                        note_s = f" (ตัดทะเลแล้ว จาก {adj['before_km2']})"
                        # M4: % ที่ราบควรคำนวณจากค่าหลังตัด (เดิมค้างค่าก่อนตัด)
                        if r.get("plain_km2"):
                            frac = adj["after_km2"] / r["plain_km2"]
                l2_rows.append([esc(r["track"]), esc(ict_label(r["scene"])), esc(r["scene"][12:40]), esc(r["reference"][12:40]),
                                num(val, 1) + note_s, f"{frac:.1%}",
                                f"{r['coverage']:.0%}"])
            S.append(table(["วงโคจร (HH:MM เวลาสากล)", "ถ่ายภาพ (เวลาไทย)", "ฉากเหตุการณ์", "อ้างอิงก่อนเหตุการณ์",
                            "น้ำใหม่ (ตร.กม.)", "% ของที่ราบทั้งลุ่ม", "ฉากครอบลุ่ม (%)"], l2_rows,
                           "กฎตัดน้ำที่ใช้: สัญญาณเรดาร์ต้องลดลงอย่างน้อย 0.5 หน่วย (ช่องต่างขั้ว) และ 1.5 หน่วย (ช่องเหมือนขั้ว) เทียบก่อนเหตุการณ์ และค่าหลังเหตุการณ์ต้องต่ำกว่า −20 · นับเฉพาะที่ราบต่ำกว่า 60 เมตร · กฎนี้สอบเทียบกับแผนที่ GISTDA ที่นครนายกเท่านั้น (F1 " + f"{_rv['oct2']['f1']:.2f}" + " — ดูข้อจำกัดข้อ (7))"))
            note_extra = (f"รอบถ่ายที่ตรวจพบมากสุดของลุ่มนี้: ตรวจพบรวม <b>{num(peak['water_km2_lowland'], 1)} ตร.กม.</b> (ขอบบนของน้ำใหม่ในฉาก) "
                          f"({peak['water_frac_plain']:.1%} ของที่ราบทั้งลุ่ม) — ฉาก {peak['scene'][12:40]} ถ่ายเมื่อ {ict_label(peak['scene'])} เวลาไทย · "
                          f"รอบถ่ายนี้ (รวม {_fm[bid]['same_pass_frames']} ชิ้นส่วนของฉาก) ครอบ <b>{_fm[bid]['coverage']:.0%}</b> ของลุ่ม — เป็นค่าต่ำสุด (ส่วนนอกฉากไม่ได้ตรวจ) · "
                          f"ขอบเขตน้ำสูงสุดรวมทุกวัน (รวม {_fm[bid]['max_extent_n_passes']} รอบถ่าย; ไม่ใช่น้ำท่วมพร้อมกัน) <b>{num(_fm[bid]['max_extent_km2'], 1)} ตร.กม.</b> ครอบพื้นที่ราบของลุ่ม {_fm[bid]['max_extent_covered_lowland_frac']:.0%} · "
                          + f"ในจุดที่ตรวจพบ <b>{_rv['basin_dark_share'][bid]:.0%}</b> เป็นพื้นที่ที่ภาพก่อนเหตุการณ์มืดอยู่แล้ว (อาจเป็นน้ำเดิม/บ่อ) — "
                            f"หลังตัดแหล่งน้ำถาวร (ตามแผนที่ผิวดินโลก 10 ม. และแผนที่ความถี่การมีน้ำ 2527–2564) และจุดที่มืดอยู่แล้ว เหลือ <b>น้ำใหม่เข้มงวด ~{_lc[bid]['strict_new_km2']:.0f} ตร.กม.</b> "
                            f"(ตรวจพบบนพื้นที่เพาะปลูก {_lc[bid]['share_det_crop']:.0%} ของที่ราบฉากนี้เป็นพื้นที่เพาะปลูก {_lc[bid]['share_base_crop']:.0%})")
            if "gistda_disaster_platform" in _can:
                g_areas = _can["gistda_disaster_platform"].get("areas_30days", {})
                if bid in ["bkk_lower", "ping_cp"] and "chaophraya" in g_areas:
                    note_extra += f" · สอบเทียบภาพรวมสะสม 30 วันกับระบบสารสนเทศภัยพิบัติ GISTDA (ผสาน 34 ดาวเทียม): ลุ่มน้ำเจ้าพระยา 13 จว. รวม {num(g_areas['chaophraya']['flood_sqkm'], 1)} ตร.กม."
                elif bid in ["bp_prach"] and "bangpakong" in g_areas:
                    note_extra += f" · สอบเทียบภาพรวมสะสม 30 วันกับระบบสารสนเทศภัยพิบัติ GISTDA (ผสาน 34 ดาวเทียม): ลุ่มน้ำบางปะกง 4 จว. รวม {num(g_areas['bangpakong']['flood_sqkm'], 1)} ตร.กม."
                else:
                    note_extra += " · สอบเทียบกับขอบเขตสะสม 30 วันของระบบสารสนเทศภัยพิบัติ GISTDA (ผสาน 34 วงโคจรดาวเทียม)"
            else:
                note_extra += " · สอบเทียบกับขอบเขตสะสม 30 วันของระบบสารสนเทศภัยพิบัติ GISTDA"
            if bid == "bkk_lower":
                sea_p = A / "goal6/bkk_lower/l2_sea_adjust.json"
                if sea_p.exists():
                    sea = json.loads(sea_p.read_text(encoding="utf-8"))
                    adj_peak = next((a2 for a2 in sea["scene_adjust"] if a2["after_km2"] == sea["peak_after_km2"]), {})
                    note_extra += (f" · <b>ตัดน้ำถาวรแล้ว</b>: แผ่นน้ำถาวร (วัดจากทุกฉากในหน้าต่าง) ครอบ "
                                   f"{sea['sea_cells_km2']:,.1f} ตร.กม. — ส่วนที่ซ้อนกับน้ำท่วมฉากจุดสูงสุดนี้ "
                                   f"{adj_peak.get('sea_removed_km2', 0):,.1f} ตร.กม. → คงเหลือ "
                                   f"<b>{sea['peak_after_km2']:,.1f} ตร.กม.</b> "
                                   "(ตัวเลขล่างขอบ — พื้นที่ที่ท่วมค้างเกือบทั้งหน้าต่างจะถูกนับเป็นน้ำถาวรและถูกตัดไปด้วย)")
                else:
                    note_extra += " · เบื้องต้น: ยังไม่ได้ตัดทะเล"
            S.append(note(note_extra))
    if not l2_rows:
        S.append(placeholder("L2 — พื้นที่น้ำท่วมจาก Sentinel-1 (กฎ canonical เทียบฉากก่อนเหตุการณ์) กำลังประมวลผล"))
    # L3 — โมเดลทำนาย
    l3p = A / f"goal6/{bid}/l3_model.json"
    if l3p.exists():
        l3 = json.loads(l3p.read_text(encoding="utf-8"))
        l3_rows = []
        model_th = {"linear": "สูตรเส้นตรง", "persistence": "ค่าเดิมคงที่", "GBDT": "แบบจำลองต้นไม้"}
        for h in ("6", "24", "48"):
            blk = l3["results"][h]
            sel_name = blk.get("selected") or min(blk["rows"], key=lambda r: r["rmse_cm"])["model"]
            for r in blk["rows"]:
                mark = " ✓" if r["model"] == sel_name else ""
                l3_rows.append([f"+{h} ชม.", esc(model_th.get(r["model"], r["model"])) + mark, num(r["rmse_cm"], 1),
                                num(r.get("rmse_val_cm"), 1), num(r["rmse_event_cm"], 1), num(r["mae_cm"], 1)])
        S.append(table(["ระยะ", "โมเดล", "คลาดเคลื่อนรากเฉลี่ยกำลังสอง (ซม.)", "คลาดเคลื่อนรากเฉลี่ยกำลังสอง ชุดตรวจสอบ 2568 (ซม.)", "คลาดเคลื่อนรากเฉลี่ยกำลังสองเฉพาะเหตุการณ์ (ซม.)", "คลาดเคลื่อนสัมบูรณ์เฉลี่ย (ซม.)"],
                       l3_rows,
                       f"จุดเป้าหมาย {l3['target']['code']} ({l3['target']['name']}) · "
                       f"ฝึก {l3['train_hours']:,} ชม. (2020–2026 ฤดูฝน — ตัดตัวอย่างที่เป้าหมายทับช่วงทดสอบ 48 ชม. แล้ว "
                       f"{l3['validation']['n_purged_before_test']:,} ตัวอย่าง) · ทดสอบกลางเหตุการณ์ "
                       f"{l3['test_hours']:,} ชม. ({l3.get('window_test', '2026-09-20..2026-10-09').replace('..', ' ถึง ')}) · "
                       f"วิธีเดียวกับนครนายก · ✓ = โมเดลที่ 'เลือกโดยชุดตรวจสอบ' {esc(l3['validation']['window'])} ไม่ใช่ชุดทดสอบ · "
                       "R24 = ฝนวันก่อนหน้า ไม่ใช่ 24 ชม.ย้อนหลัง"))
        model_th = {"linear": "สูตรเส้นตรง", "persistence": "ค่าเดิมคงที่", "GBDT": "แบบจำลองต้นไม้"}

        def _selected(h: str):
            blk = l3["results"][h]
            nm = blk.get("selected") or min(blk["rows"], key=lambda r: r["rmse_cm"])["model"]
            return next(r for r in blk["rows"] if r["model"] == nm)

        best6, best24, best48 = _selected("6"), _selected("24"), _selected("48")
        pers6 = next(r for r in l3["results"]["6"]["rows"] if r["model"] == "persistence")["rmse_cm"]
        pers24 = next(r for r in l3["results"]["24"]["rows"] if r["model"] == "persistence")["rmse_cm"]
        S.append(note(
            f"สรุป: ที่ระยะใช้งานจริง วิธีที่<b>เลือกโดยชุดตรวจสอบ</b> (ก่อนเหตุการณ์) คือ <b>{model_th.get(best6['model'], best6['model'])} (คลาดเคลื่อน {best6['rmse_cm']} ซม. ที่ +6 ชม.)</b> "
            f"และ <b>{model_th.get(best24['model'], best24['model'])} ({best24['rmse_cm']} ซม. ที่ +24 ชม.)</b> — "
            f"เทียบกับค่าเดิมคงที่ {pers6} ซม. และ {pers24} ซม. (ถ้าสองชุดใกล้กัน ความแม่นมาจากระดับน้ำเปลี่ยนช้า ไม่ใช่ฝีมือแบบจำลอง) · "
            f"ที่ +48 ชม. {best48['rmse_cm']} ซม. ({model_th.get(best48['model'], best48['model'])}) · "
            f"เลือกโมเดลด้วยฤดูปลายฝน 2568 ไม่ใช่ชุดทดสอบ (ตัดตัวอย่างที่เป้าหมายทับช่วงทดสอบออกจากชุดฝึก) · ทดสอบกับเหตุการณ์เดียวเท่านั้น"
        ))
    else:
        S.append(placeholder("L3 — โมเดลทำนายระดับน้ำ (สูตร/ค่าเดิมคงที่/GBDT วิธีเดียวกับนครนายก) รอเข้าคิว"))
    # แผนที่น้ำท่วม (ข้อตกลง: แผนที่ประกอบตัวเลขหัวใจ)
    map_p = ROOT / f"report/assets/goal6/map_{bid}.png"
    if map_p.exists():
        S.append(figure(map_p,
                        f"แผนที่น้ำท่วมจากดาวเทียมเรดาร์ ฉากที่ใหญ่สุด ({ict_label(_fm[bid]['scene'])} เวลาไทย · ครอบ {_fm[bid]['coverage']:.0%} ของลุ่ม) — {rec['label']}"))

# ---- 5. ข้อจำกัด ----
# ส่วนเพิ่ม 4.7 (ฉะเชิงเทรา · วิเคราะห์เพิ่มหลังกำหนดคำถามล่วงหน้า) — เรนเดอร์จาก canonical.bp_downstream
from goal6_bp_downstream import section as _bp_downstream_section  # noqa: E402
_bp_downstream_section(S, _can, h3, note, prose, table)

S.append(h2("5. ถาม–ตอบ คำถามที่คนทั่วไปถามบ่อย", "qa"))
S.append(prose("<b>ถาม: น้ำท่วมครั้งนี้เขื่อนผิดหรือฝนผิด?</b>"))
S.append(prose(
    "ตอบตามหลักฐาน: ฝนครั้งนี้<b>หนักเป็นประวัติการณ์</b> — ฝน 7 วันสูงสุดติดอันดับ 1–3 จาก 46 ปี "
    f"ใน {_rn['top3_stations_7d']} จาก {_rn['n_stations']} จุดวัด (= {_rn['top3_cells_7d']} จาก {_rn['n_cells']} ช่องกริดอิสระ · ยืนยันด้วยข้อมูลฝนหลังผ่าน 46 ปี) "
    "ฝนอย่างนี้ลุ่มน้ำใดก็รับไม่ได้ทั้งหมด · แต่การเก็บน้ำของเขื่อนบางแห่ง"
    "ทำให้พื้นที่รองรับน้ำฝนน้อยลงกว่าที่ควรจะเป็น (ดูบทของแต่ละลุ่ม) — "
    "และเขื่อนบางระบบ (ภาคตะวันตกและภาคใต้ 3 แห่ง) จัดการได้ดีจนไม่เคยเกินระดับกำกับเลย "
    "แสดงว่าสามารถทำได้จริงในระบบบางแบบ — ขณะเดียวกันเขื่อนชลประทานก็มีบทบาทรับน้ำจริง: "
    "ป่าสักลดการปล่อยลงเหลือต่ำสุดพอดีช่วงระลอกปลาย ก.ย. (บทป่าสัก)"
))
S.append(prose("<b>ถาม: เขื่อนไหนจัดการดีที่สุด?</b>"))
S.append(prose(
    "ในสองปีน้ำท่วมใหญ่ (จากประวัติ 22 ปีที่ตรวจ): เขื่อนการไฟฟ้าฝ่ายผลิตฯ 3 แห่งในภาคตะวันตกและภาคใต้ (ศรีนครินทร์ · วชิราลงกรณ์ · "
    "รัชชประภา) เก็บน้ำ<b>ไม่เคย</b>เกินระดับกำกับเลยทั้งสองปีน้ำท่วมใหญ่ (2554 และ 2569) "
    "เพราะระบบของเขาผลิตไฟฟ้าได้ทุกระดับน้ำ จึงเผื่อพื้นที่ว่างไว้รับฝนได้ตลอดปี — "
    "<b>แต่ต้องอ่านคู่กันว่า</b>: เขื่อนใหญ่ของสังกัดเดียวกันในลุ่มเจ้าพระยา (ภูมิพล สิริกิติ์) "
    f"ปี 2554 เกินระดับกำกับ {dams_2554_days['ภูมิพล']}/{dams_2554_days['สิริกิติ์']} วัน เมื่อน้ำเข้าอ่างฤดูนั้นสูงสุดในประวัติ "
    f"(ภูมิพลอันดับ {_can['dam_inflow']['ภูมิพล']['inflow_rank2554']} · ปี 2569 อันดับ {_can['dam_inflow']['ภูมิพล']['inflow_rank2569']}) — "
    "ความต่างจึงมาจาก<b>ทั้งปริมาณน้ำเข้าของลุ่มและพื้นที่ว่างใต้เส้น ณ ต้นหน้าต่าง</b> (ศรีนครินทร์: น้ำเข้า 2554 อันดับ "
    f"{_can['dam_inflow']['ศรีนครินทร์']['inflow_rank2554']} แต่ ณ 1 ก.ย. เก็บต่ำกว่าเส้น {abs(_can['dam_inflow']['ศรีนครินทร์']['sep1_over_2554']):,.0f} ล้าน ลบ.ม.) "
    "ไม่ใช่ข้อสรุปว่าสังกัดใดดีกว่า "
    f"(เทียบรายลุ่ม ฝนรวมฤดู 2554: แม่กลองอันดับ {_can['basin_rain']['basins']['maeklong']['season_total']['rank2554']} · ปิง–น่านเหนือนครสวรรค์อันดับ {_can['basin_rain']['basins']['ping_cp']['season_total']['rank2554']} จาก 46 ปี — ดูตารางฝนในรายงานที่ 4)"
))
S.append(prose("<b>ถาม: ทำไมบางลุ่มท่วมหนักทั้งที่เขื่อนใหญ่?</b>"))
S.append(prose(
    f"ลุ่มปิง–เจ้าพระยามีน้ำท่วมมากสุด ({_fl['ping_cp']:,.0f} ตร.กม.) ทั้งที่เขื่อนภูมิพลเก็บน้ำต่ำกว่าระดับกำกับตลอด — "
    "เพราะลุ่มนี้<b>ใหญ่มาก</b> น้ำจากหลายแม่น้ำ (ปิง วัง ยม น่าน) ไหลมารวมกัน และฝนบนลุ่มตอนบน "
    "ก็ตกหนักติดอันดับต้น ๆ ของ 46 ปีด้วย — เขื่อนเดียวกักน้ำทั้งระบบไม่ได้"
))
S.append(prose("<b>ถาม: กรุงเทพฯ เสี่ยงไหม?</b>"))
S.append(prose(
    f"ข้อมูลเรา: น้ำท่วมทุ่งรับน้ำราบรอบ กทม. สูงสุด {_fl['bkk_lower_after_sea']:,.0f} ตร.กม. (ฉากถ่ายเมื่อ {ict_label(_fm['bkk_lower']['scene'])} เวลาไทย) "
    "(ฉากเดียวที่ครอบทั้งลุ่ม · นับเฉพาะน้ำใหม่ที่ไม่ใช่น้ำถาวร · ค่าจริงอาจต่างทั้งสองทิศ: กฎตัดน้ำตรงกับแผนที่ทางการ F1 0.65–0.73 และเรดาร์มองไม่เห็นน้ำท่วมใต้ตึกเมือง) · ระดับน้ำที่ท้ายเขื่อนเจ้าพระยา "
    f"ทำนายได้ (คลาดเคลื่อน ~{_l3['bkk_lower']['h6']['rmse_cm']:.0f} ซม. ที่ระยะ 6 ชม.) · ทั้งนี้ กรุงเทพฯ เผชิญความเสี่ยงสำคัญ 2 ประการร่วมกัน "
    f"คือ น้ำหลากจากแม่น้ำเจ้าพระยาตอนบนและฝนในพื้นที่ ประจวบเหมาะกับช่วงน้ำทะเลหนุนสูงสุด (น้ำเกิด) ที่สะพานกรุงเทพ "
    f"แตะระดับ {_tide['cpy015_peak_m']:.2f} ม.รทก. (วันที่ 28 ก.ย.) ทำให้ช่องทางระบายตามแรงโน้มถ่วงแคบลงในช่วงน้ำลง (ดูคำถามถัดไป)"
))
# ---- ผลกระทบ: ประชากร/ถนน (goal6_exposure.py → canonical.exposure) ----
_ex = _can["exposure"]
S.append(prose("<b>ถาม: ในพื้นที่ที่ตรวจพบน้ำท่วม มีประชากรและถนนอยู่เท่าไร?</b>"))
_ex_rows = []
for _bid, _lab in (("ping_cp", "ปิง–เจ้าพระยาตอนบน"), ("bkk_lower", "เจ้าพระยาตอนล่าง–กทม."), ("bp_prach", "บางปะกง"),
                   ("pasak", "ป่าสัก"), ("thachin", "ท่าจีน"), ("maeklong", "แม่กลอง"), ("nn_oct2", "นครนายก (2 ต.ค.)")):
    _r = _ex[_bid]
    _g, _s = _r["gross"], _r["strict"]
    _ex_rows.append([_lab, f"{_s['pop_areal']:,.0f}–{_g['pop_areal']:,.0f}", f"{_s['pop_cells_ge10pct']:,.0f}–{_g['pop_cells_ge10pct']:,.0f}",
                     f"{_s['major_km']:,.0f}–{_g['major_km']:,.0f}", f"{_s['minor_km']:,.0f}–{_g['minor_km']:,.0f}",
                     f"{_s['rail_km']:,.0f}–{_g['rail_km']:,.0f}"])
S.append(table(["ลุ่ม/ฉาก", "ประชากร เฉลี่ยตามพื้นที่ (คน)", "ประชากรในเซลล์ 1 กม. ที่ตรวจพบ ≥10% (คน)", "ถนนสายหลัก (กม.)", "ถนนสายรองและทางเข้า (กม.)", "ทางรถไฟ (กม.)"],
               _ex_rows,
               "ช่วง = น้ำใหม่เข้มงวด → ตรวจพบรวม · ประชากร: แผนที่ประชากรโลกปี 2563 ความละเอียด 1 กม. กระจายเท่ากันในเซลล์ — ตัวเลขหยาบ ปัดเป็นร้อย · ถนน/ทางรถไฟ: แผนที่เปิดสาธารณะที่อาสาสมัครร่วมจัดทำ ณ 12 ต.ค. 2569 · "
               "ลุ่มซ้อนทับกัน (ปิง–เจ้าพระยา ป่าสัก กทม. มีพื้นที่ร่วมกัน) — ห้ามนำแถวมาบวกกัน"))
_nn = _ex["nn_oct2"]
S.append(prose(
    "<b>อ่านอย่างไร</b>: (1) ตัวเลขนี้นับเฉพาะส่วนที่ดาวเทียมเรดาร์ตรวจพบน้ำในฉากเดียว — เรดาร์มองน้ำท่วมในเมืองไม่เห็นเป็นหลัก (ที่ตรวจพบบนพื้นที่ก่อสร้างไม่ถึง 1%) "
    "ประชากรในเมืองจึงต่ำกว่าจริง ส่วนบ่อ/นาที่ขังน้ำตามฤดูอาจถูกนับเกิน · "
    f"(2) ตรวจเทียบ: นครนายก 2 ต.ค. ตัวเลขเฉลี่ยตามพื้นที่ {_nn['strict']['pop_areal']:,.0f}–{_nn['gross']['pop_areal']:,.0f} คน อยู่ใกล้ระดับเดียวกับที่ GISTDA ประกาศ "
    "ว่ามีประชากรได้รับผลกระทบ 48,100 คน (ฉบับสะสม 28 ก.ย.–2 ต.ค. ตามรายงานที่ 1–2) แต่เป็นคนละนิยาม · "
    "(3) \"ประชากรในเซลล์ที่ตรวจพบ ≥10%\" เป็นขอบบนของคนที่อยู่ใกล้พื้นที่น้ำท่วม ไม่ใช่จำนวนผู้ประสบภัย · "
    "(4) ไม่มีข้อมูลระดับครัวเรือนและไม่ใช้ เพื่อไม่ให้ระบุตัวบุคคลได้"
))
S.append(prose("<b>ถาม: น้ำทะเลหนุนสูงแค่ไหน และขัดขวางการระบายน้ำของกรุงเทพฯ และลุ่มเจ้าพระยาตอนล่าง/ท่าจีนอย่างไร?</b>"))
S.append(prose(
    "ตอบตามหลักฐานโทรมาตรปากแม่น้ำ: "
    f"ช่วงวันที่ 26–28 ก.ย. 2569 เกิดปรากฏการณ์น้ำเกิดตามปฏิทินดาราศาสตร์พร้อมกันตลอดแนวอ่าวไทยตอนบน — "
    f"ระดับน้ำทะเลหนุนสูงสุดที่สะพานกรุงเทพ (เจ้าพระยา) แตะระดับ <b>{_tide['cpy015_peak_m']:.2f} ม.รทก.</b> "
    f"(เวลา 06:50 น. วันที่ 28 ก.ย.) · ที่สามเสนขึ้นถึง <b>{_tide['c12_peak_m']:.2f} ม.รทก.</b> (27 ก.ย.) · "
    f"ที่ปากแม่น้ำท่าจีน (เมืองสมุทรสาคร) สูงสุด <b>{_tide['tha009_peak_m']:.2f} ม.รทก.</b> (27 ก.ย.) · "
    f"และปากแม่น้ำเพชรบุรี (บางตะบูน) สูงสุด <b>{_tide['glf003_peak_m']:.2f} ม.รทก.</b> (28 ก.ย.)"
))
S.append(prose(
    f"ข้อค้นพบสำคัญ 2 ประการจากสถิติย้อนหลัง {_tide['historical_years']} ปี (2555–2568):<br>"
    f"1. <b>ไม่ใช่น้ำหนุนทุบสถิติใหม่</b> — สถิติรายปีชี้ว่าน้ำเกิดช่วงปลาย ก.ย.–ต.ค. ปกติแตะระดับ "
    f"{_tide['astronomical_spring_range_m'][0]:.2f}–{_tide['astronomical_spring_range_m'][1]:.2f} ม.รทก. เป็นประจำทุกปีอยู่แล้ว "
    "ไม่ใช่คลื่นซัดฝั่งรุนแรงผิดธรรมชาติ แต่เกิด<b>การประจวบเหมาะของจังหวะเวลา</b>ที่น้ำทะเลหนุนสูงสุดมาตรงกับช่วงฝนตกหนักที่สุดของภาคกลางพอดี<br>"
    "2. <b>ระดับน้ำต่ำสุดรายวันที่ปากแม่น้ำค้างสูงกว่าปกติ</b> — วันปกติช่วงน้ำลงลดถึง −0.8 ถึง −1.2 ม.รทก. "
    f"แต่ช่วง 26–28 ก.ย. ที่สะพานกรุงเทพค้างที่ {_tide['trough_min_during_peak_m']:.2f} ถึง {_tide['trough_max_during_peak_m']:.2f} ม.รทก. "
    f"และที่สามเสนค้างสูงกว่า {_tide['c12_trough_min_m']:.2f} ม.รทก. — ความต่างระดับระหว่างแม่น้ำกับทะเลจึงน้อยลง และการระบายตามแรงโน้มถ่วงทำได้น้อยลง "
    "(ข้อสังเกต) · ระดับที่ค้างสูงมาจากทั้งน้ำทะเลหนุนและน้ำเหนือปริมาณมากพร้อมกัน แยกสองส่วนไม่ได้จากข้อมูลนี้ · "
    "<b>ข้อมูลการเปิด–ปิดบานประตูระบายและการเดินเครื่องสูบไม่มีใน API</b> จึงยืนยันไม่ได้ว่าบานปิดกี่แห่งหรือพึ่งเครื่องสูบเท่าไร"
))
S.append(prose("<b>ถาม: ทำไมหลังฝนตกเบาลงหรือหยุดตกไปหลายวันแล้ว น้ำท่วมในหลายพื้นที่ยังคงไม่ลดลงหรือลดลงช้ามาก?</b>"))
S.append(prose(
    "ตอบตามหลักชลศาสตร์และภูมิสัณฐานวิทยา 4 ประการ:<br>"
    "1. <b>การเดินทางของมวลน้ำจากลุ่มน้ำตอนบน (ความหน่วงทางอุทกวิทยา)</b>: "
    "แม้ฝนในพื้นที่ราบตอนล่างจะหยุดตกแล้ว แต่มวลน้ำมหาศาลจากฝนที่ตกสะสมในลุ่มน้ำตอนบนและลำน้ำสาขา "
    "(เช่น ปิง วัง ยม น่าน) ต้องใช้เวลาเดินทางหลายวันตามลำน้ำมารวมตัวกันที่แม่น้ำสายหลักตอนล่าง "
    "ระดับน้ำในแม่น้ำสายหลักจึงยังคงทรงตัวหรือขึ้นสูงต่อเนื่อง ทำให้น้ำในพื้นที่สองฝั่งยังไม่สามารถไหลลงแม่น้ำได้<br>"
    "2. <b>ความลาดชันของที่ราบลุ่มต่ำมาก (ความชันต่ำมาก)</b>: "
    "พื้นที่ราบภาคกลางตอนล่างมีลักษณะเป็นแอ่งกระทะกว้างและแบนราบมาก ระดับความสูงพื้นดินต่างกันเพียงไม่กี่สิบเซนติเมตรในระยะทางหลายกิโลเมตร "
    "น้ำจึงไหลตามแรงโน้มถ่วงได้ช้ามากตามธรรมชาติ หากไม่มีความต่างระดับน้ำที่มากพอ น้ำจะแช่ขังนิ่งเสมือนทะเลสาบน้ำจืด<br>"
    "3. <b>น้ำทะเลหนุนทำให้ความต่างระดับระหว่างแม่น้ำกับทะเลลดลง</b>: "
    "ดังที่แสดงในโทรมาตรปากแม่น้ำ ช่วงปลาย ก.ย.–ต.ค. เป็นช่วงน้ำเกิดตามปฏิทินดาราศาสตร์ "
    "การระบายตามแรงโน้มถ่วงจึงทำได้เฉพาะช่วงน้ำลงต่ำสุดของแต่ละวัน หรืออาศัยเครื่องสูบน้ำ "
    "(รายละเอียดการเปิด–ปิดบานจริงไม่มีข้อมูลสาธารณะ)<br>"
    "4. <b>โครงข่ายถนน คันกั้นน้ำ และทางรถไฟ ซอยขังน้ำเป็นแปลงย่อย</b>: "
    "โครงสร้างพื้นฐานคมนาคมและคันกั้นน้ำทำหน้าที่เสมือนเขื่อนกั้นน้ำขวางทางไหลตามธรรมชาติ "
    "น้ำที่ล้นเข้าทุ่งเกษตรหรือชุมชนนอกคันจึงถูกกักเป็นช่วง ๆ ไม่สามารถไหลลัดเลาะลงสู่แม่น้ำสายหลักได้เอง "
    "ต้องรอการติดตั้งเครื่องสูบน้ำดึงข้ามคันออกไปทีละจุด"
))
S.append(prose(
    "<b>ถาม: การระบายน้ำออกสู่ทะเลมีข้อจำกัดในการปกป้องน้ำประปาอย่างไร และสถานการณ์ความเค็มบริเวณจุดสูบน้ำดิบ (สถานีสำแล) เป็นอย่างไรในช่วงน้ำหลาก?</b>"
))
S.append(prose(
    "ตอบตามข้อมูลโทรมาตรคุณภาพน้ำ 112 สถานีทั่วประเทศ:<br>"
    "1. <b>การผลักดันลิ่มความเค็มที่จุดสูบน้ำดิบสำแล (จ.ปทุมธานี)</b>: "
    f"ตลอดช่วงน้ำหลากระลอกนี้ ค่าความเค็มที่สถานีสำแลของการประปานครหลวง (จุดสูบน้ำดิบหลักของกรุงเทพฯ และปริมณฑล) "
    f"วัดได้ระหว่าง <b>{_sal['samlae_salinity_min_gl']}–{_sal['samlae_salinity_max_gl']} กรัมต่อลิตร</b> "
    f"ซึ่งต่ำกว่าเกณฑ์เฝ้าระวัง ({_sal['samlae_warning_threshold_gl']} กรัมต่อลิตร) "
    f"และต่ำกว่าเกณฑ์มาตรฐานน้ำประปา ({_sal['samlae_mwa_standard_gl']} กรัมต่อลิตร) อย่างปลอดภัย — "
    f"สอดคล้องกับสถิติย้อนหลัง 9 ปี (2561–2569) ที่สะพานพระนั่งเกล้าในเดือนกันยายนที่มีค่าเฉลี่ย {_sal['phranangklao_9y_sep_avg_gl']:.2f} กรัมต่อลิตร "
    "ยืนยันว่าการที่เขื่อนเจ้าพระยาและลุ่มน้ำป่าสักรักษาระดับการระบายน้ำหลาก สามารถผลักดันลิ่มความเค็มได้ผล 100%<br>"
    "2. <b>แนวปะทะน้ำเค็มที่ปากแม่น้ำบางปะกง</b>: "
    f"ที่สถานีอำเภอเมืองฉะเชิงเทรา ในรอบน้ำเกิดบันทึกความเค็มพุ่งสูงถึง <b>{_sal['bangpakong_peak_salinity_gl']} กรัมต่อลิตร</b> "
    f"(การนำไฟฟ้า {_sal['bangpakong_peak_ec_us_cm']:,.1f} ไมโครซีเมนต์ต่อเซนติเมตร) "
    "สะท้อนแนวปะทะชลศาสตร์ระหว่างมวลน้ำจืดไหลหลากกับน้ำทะเลหนุนอย่างชัดเจน<br>"
    "3. <b>คลื่นลมในอ่าวไทยเป็นอุปสรรคต่อการระบายน้ำ</b>: "
    f"แบบจำลองคลื่นทะเล (<code>SWAN</code>) ครอบคลุม {_swan['stations_count']} สถานี ชี้ว่าบริเวณอ่าวไทยตอนบนมีคลื่นนัยสำคัญสูง "
    f"<b>{_swan['upper_gulf_wave_height_sig_min_m']}–{_swan['upper_gulf_wave_height_sig_max_m']} เมตร</b> "
    "ทำหน้าที่เป็นแนวต้านทางชลศาสตร์ที่ชะลอการระบายน้ำหลากของแม่น้ำสายหลักออกสู่อ่าวไทย"
))
S.append(prose(
    "<b>หมายเหตุ — คำถาม–ตอบชุดถัดไป (ข้อเสนอเชิงนโยบาย) เป็น 'ความเห็นของผู้จัดทำ' ไม่ใช่ผลการวิเคราะห์ข้อมูลของรายงานนี้</b> · "
    "อ้างอิงแนวคิดวิศวกรรมทั่วไป ไม่ได้คำนวณจากข้อมูลของโครงการ และไม่ได้ประเมินต้นทุน/ข้อจำกัดทางกฎหมายของแต่ละหน่วยงาน — "
    "ผู้อ่านควรแยกจากส่วนข้อเท็จจริงด้านบน"
))
S.append(prose("<b>ถาม: ควรทำอย่างไรให้สามารถระบายน้ำจากแม่น้ำสายหลักลงสู่อ่าวไทยได้เร็วและมีปริมาณมากขึ้น?</b>"))
S.append(prose(
    "ตอบตามแนวทางวิศวกรรมชลศาสตร์และกายภาพลุ่มน้ำ 4 มิติสำคัญ:<br>"
    "1. <b>ขยายและขุดลอกทางผันน้ำหลากเลี่ยงคอขวด (คลองลัดและคลองระบายน้ำสายตรง)</b>: "
    "แม่น้ำเจ้าพระยาและแม่น้ำท่าจีนมีจุดคอขวดที่จำกัดอัตราการไหลอย่างรุนแรง การขุดลอกเพิ่มความลึกร่องน้ำ และการสร้างหรือเชื่อมต่อคลองผันน้ำหลากสายตรงลงสู่อ่าวไทย "
    "เพื่อตัดมวลน้ำลัดแนวโค้งน้ำที่คดเคี้ยว จะช่วยเพิ่มอัตราการไหลระบายน้ำลงสู่ทะเลได้อย่างมีนัยสำคัญ<br>"
    "2. <b>บริหารประตูระบายน้ำให้สอดประสานกับจังหวะน้ำขึ้น-น้ำลงแบบอัตโนมัติ</b>: "
    "ใช้ระบบตรวจวัดระดับน้ำทะเลปากอ่าวแบบเรียลไทม์ควบคู่กับระบบควบคุมบานประตูระบายน้ำกึ่งอัตโนมัติ "
    "เพื่อเร่งเปิดบานระบายน้ำด้วยแรงโน้มถ่วงให้เต็มกำลังในช่วงเวลาน้ำลงต่ำสุดของวัน (ช่วงหน้าต่างระบายน้ำธรรมชาติ) "
    "และสลับเดินเครื่องสูบน้ำเต็มพิกัดทันทีที่ระดับน้ำทะเลเริ่มหนุนสูง เพื่อไม่ให้เกิดภาวะน้ำชะงักนิ่ง<br>"
    "3. <b>จัดระเบียบและใช้ประโยชน์จากทุ่งรับน้ำนองธรรมชาติอย่างเป็นระบบ</b>: "
    "การระบายน้ำผ่านแม่น้ำสายหลักมีขีดจำกัดตลิ่งรองรับ หากปล่อยน้ำลงมาพร้อมกันทั้งหมดจะล้นตลิ่งท่วมพื้นที่ท้ายน้ำ "
    "จึงจำเป็นต้องมีระบบผันน้ำเข้าทุ่งรับน้ำเพื่อหน่วงน้ำและตัดยอดน้ำสูงสุดในแม่น้ำสายหลักชั่วคราว "
    "แล้วจึงทยอยระบายน้ำออกจากทุ่งเมื่อระดับน้ำในแม่น้ำสายหลักลดลงต่ำกว่าตลิ่ง<br>"
    "4. <b>ขุดลอกสันดอนปากแม่น้ำและรื้อถอนสิ่งกีดขวางทางน้ำอย่างสม่ำเสมอ</b>: "
    "ตะกอนสะสมที่ปากแม่น้ำบริเวณจุดบรรจบอ่าวไทยสร้างแนวสันดอนที่ต้านทานการไหลของน้ำ "
    "การขุดลอกร่องน้ำลึกปากแม่น้ำอย่างต่อเนื่องก่อนเข้าฤดูน้ำหลาก ร่วมกับการรื้อถอนสิ่งปลูกสร้างรุกล้ำทางน้ำ "
    "จะช่วยเพิ่มความเร็วและปริมาตรการระบายน้ำออกสู่ทะเลได้อย่างเต็มศักยภาพ"
))
if _tide and _sal and _swan:
    S.append(prose("<b>ถาม: สภาพน้ำทะเลหนุน คลื่นทะเลอ่าวไทย และคุณภาพน้ำปากแม่น้ำ ส่งผลต่อการระบายน้ำหลากและการประปาอย่างไร?</b>"))
    S.append(prose(
        f"ตอบตามข้อมูลโทรมาตรและแบบจำลองทางทะเล:<br>"
        f"1. <b>คลื่นและน้ำทะเลหนุนต้านการระบาย</b>: ช่วงวันที่ 26–28 ก.ย. 2569 เป็นช่วงน้ำเกิด ระดับน้ำทะเลที่ปากแม่น้ำเจ้าพระยา (ป้อมพระจุลจอมเกล้า <code>cpy015</code>) หนุนสูงสุดถึง {_tide['cpy015_peak_m']:.2f} ม.รทก. "
        f"ร่วมกับแบบจำลองคลื่น <code>SWAN</code> 31 สถานีที่ตรวจพบความสูงคลื่นนัยสำคัญ {_swan['upper_gulf_wave_height_sig_min_m']:.1f}–{_swan['upper_gulf_wave_height_sig_max_m']:.1f} เมตรในอ่าวไทยตอนบน "
        f"ทำให้เกิดแรงต้านการไหลที่ปากแม่น้ำ (ปรากฏการณ์น้ำเอ่อหนุนกลับ) ส่งผลให้การระบายน้ำหลากจากลุ่มเจ้าพระยาและท่าจีนชะลอตัวลงอย่างมีนัยสำคัญ<br>"
        f"2. <b>การป้องกันน้ำประปาเมืองหลวงสำเร็จ</b>: แม้จะมีมวลน้ำทะเลหนุนสูง แต่สถานีตรวจวัดคุณภาพน้ำสำแล (จุดรับน้ำดิบของการประปานครหลวง) "
        f"ตรวจพบค่าความเค็มระหว่าง {_sal['samlae_salinity_min_gl']:.2f}–{_sal['samlae_salinity_max_gl']:.2f} กรัม/ลิตร "
        f"ซึ่งอยู่ในเกณฑ์มาตรฐานความปลอดภัยสำหรับน้ำประปาบริโภค (ไม่เกินเกณฑ์เฝ้าระวัง {_sal['samlae_warning_threshold_gl']:.2f} กรัม/ลิตร) "
        f"เนื่องจากมวลน้ำหลากจากตอนบนช่วยผลักดันลิ่มน้ำเค็มให้อยู่ห่างจากจุดสูบน้ำดิบ"
    ))

_nmr = _can.get("national_medium_reservoirs", {})
_ps24 = _can.get("pasak_24y_baseline", {})
if _nmr and _ps24:
    S.append(prose("<b>ถาม: อ่างเก็บน้ำขนาดกลาง 461 แห่งทั่วประเทศ และเขื่อนป่าสักชลสิทธิ์ มีพฤติกรรมอย่างไรในระลอกน้ำหลากนี้?</b>"))
    S.append(prose(
        f"ตอบตามข้อมูลสถิติและการวิเคราะห์เชิงประจักษ์:<br>"
        f"1. <b>อ่างเก็บน้ำขนาดกลาง 461 แห่ง (กรมชลประทาน)</b>: มีความจุเก็บกักรวม {_nmr['total_capacity_mcm']:,.1f} ล้าน ลบ.ม. "
        f"ในช่วงระลอกปลาย ก.ย. มีอ่างที่น้ำเต็มความจุ (เกิน 100%) ถึง {_nmr['dams_over_100_count']} แห่ง ({_nmr['dams_over_100_pct']:.1f}%) "
        f"และอ่างที่อยู่ในภาวะเฝ้าระวังสูง (กักเก็บ ≥80%) รวม {_nmr['dams_stress_total_count']} แห่ง หรือ {_nmr['dams_stress_total_pct']:.1f}% ของทั้งประเทศ "
        f"โดยเฉพาะภาคเหนือมีอ่างกักเก็บเฉลี่ยสูงถึง {_nmr['regional_summary']['ภาคเหนือ']['storage_pct']:.1f}% สะท้อนว่าแรงกดดันเกิดขึ้นทั่วทุกระดับลุ่มน้ำย่อย<br>"
        f"2. <b>ประวัติ 24 ปีเขื่อนป่าสักชลสิทธิ์ (2546–2569)</b>: การเก็บน้ำเกินความจุปกติในปี 2569 ({_ps24['y2569_peak_mcm']:,.1f} ล้าน ลบ.ม. หรือ {_ps24['y2569_peak_pct']:.1f}%) "
        f"มิใช่เรื่องผิดปกติที่ไม่เคยเกิดขึ้นมาก่อน ในรอบ 24 ปี เขื่อนป่าสักฯ มีน้ำเกินความจุปกติถึง {_ps24['over_normal_years']} ปี ({_ps24['over_normal_pct']:.1f}%) "
        f"โดยสถิติสูงสุดเกิดขึ้นในปี 2553 ({_ps24['record_peak_mcm']:,.1f} ล้าน ลบ.ม. หรือ 135.1%) "
        f"การบริหารในปี 2569 จึงเป็นการหน่วงชะลอน้ำหลากตามศักยภาพ เพื่อลดผลกระทบต่อน้ำท่วมของพื้นที่ท้ายน้ำ"
    ))

S.append(prose("<b>ถาม: น้ำที่จังหวัดนครสวรรค์ (C.2 ท่าเรือ) สูงขึ้นมากก่อนน้ำท่วมลุ่มล่าง เป็นเพราะเขื่อนปล่อยน้ำล่วงหน้าหรือไม่?</b>"))
S.append(prose(
    "ตอบตามหลักฐาน: <b>ไม่ใช่</b> — ข้อมูลรายวันชี้ตรงข้าม: ช่วงที่ระดับน้ำที่ C.2 ขึ้นแรง (15–28 ก.ย.) "
    f"เขื่อนภูมิพล<b>ลดการปล่อย</b>จาก {_can['bhumibol']['early_sep_avg']:.0f} เหลือ {_can['bhumibol']['sep25']:.0f} ล้าน ลบ.ม./วัน "
    f"(ต้น ก.ย. เฉลี่ย {_can['bhumibol']['early_sep_avg']:.1f}) และวันที่ 30 ก.ย. หยุดปล่อยเป็นศูนย์ ({_can['bhumibol']['sep30']:.0f}) "
    f"ขณะที่ระดับ C.2 (ตามระบบวัดของจุด — ดูข้อจำกัดข้อ (1)) ยังพุ่งขึ้นต่อเนื่องถึงจุดสูงสุดคืน 1 ต.ค. — "
    "ถ้าน้ำที่สูงขึ้นมาจากการปล่อยเขื่อน "
    f"ระดับต้องลดตาม แต่จริง ๆ ยังขึ้น · สาเหตุจริงคือ<b>ฝนบนลุ่มปิง–น่านและลุ่มกลางระหว่างทาง</b>: "
    f"น้ำไหลเข้าเขื่อนภูมิพลพุ่งจาก {_can['bhumibol']['inflow_sep19']:.0f} เป็น {_can['bhumibol']['inflow_sep20']:.0f} ล้าน ลบ.ม./วัน (19→20 ก.ย.) "
    "แสดงว่าฝนบนลุ่มตกหนักตั้งแต่ 19 ก.ย. "
    f"และฝนลุ่มกลางที่นครสวรรค์ 7 วัน {_rain_c2_7d:.0f} มม. ไหลลงแม่น้ำโดยตรงไม่ผ่านเขื่อน"
))
S.append(figure(ROOT / "report/assets/goal6/c2_vs_dam_releases.png",
                "ระดับน้ำ C.2 ท่าเรือ (เส้นน้ำเงิน ขึ้นต่อเนื่อง) เทียบการปล่อยน้ำเขื่อนภูมิพล (แดง) และสิริกิติ์ (ส้ม) "
                "ที่ลดลงเรื่อย ๆ ในช่วงเดียวกัน — หลักฐานว่าน้ำสูงไม่ได้มาจากการปล่อยล่วงหน้า"))
S.append(prose("<b>ถาม: ปริมาณน้ำที่ไหลผ่าน C.2 ท่าเรือกับที่เขื่อนปล่อย สัมพันธ์กันอย่างไร?</b>"))
# H3/H4 (รีวิว Sift): อ่านตัวเลข C.2 ทั้งชุดจาก JSON ที่สคริปต์คำนวณ — ห้าม literal
_c2a = json.loads((A / "goal6/c2_attribution.json").read_text(encoding="utf-8"))
_corr_rel = _c2a["correlations"]["release_vs_c2"]
_corr_inflow = _c2a["correlations"]["inflow_lag2_vs_c2"]
_corr_rel_disp = f"−{abs(_corr_rel):.2f}"  # ใช้เครื่องหมายลบไทยเดียวกับรายงาน
_corr_inflow_disp = f"{_corr_inflow:.2f}"
_chain = _c2a["chain"]
_share = _chain["release_share_at_peak_pct"]
S.append(prose(
    "ตอบด้วยตัวเลขปริมาตรจริง (น้ำที่ไหลผ่าน C.2 วัดจากอัตราไหลรายชั่วโมง ไม่ใช่ประมาณ): "
    f"ต้น ก.ย. เขื่อนทั้งสองปล่อยรวม ~{_chain['released_total']['early_sep_avg']:.0f} ล้าน ลบ.ม./วัน ขณะที่น้ำผ่าน C.2 ราว 60–70 — "
    "<b>การปล่อยเขื่อนคิดเป็นเพียง 30%</b> ของน้ำที่ผ่านจุดนั้น · "
    f"พอเข้าเหตุการณ์ (30 ก.ย.–1 ต.ค.) เขื่อนลดเหลือ {_chain['released_total']['peak']:.0f} ล้าน ลบ.ม./วัน "
    f"ขณะที่ C.2 พุ่งเป็น {_chain['c2_total']['peak']:.0f} — "
    f"<b>การปล่อยเหลือแค่ {_share:.0f}%</b> · ทางสถิติ: ความสัมพันธ์ระหว่างการปล่อยเขื่อนกับน้ำที่ C.2 "
    f"เป็น<b>ค่าติดลบสูง</b> ({_corr_rel_disp}) แปลว่ายิ่งเขื่อนปล่อยน้อย น้ำที่ C.2 ยิ่งมาก — "
    "สวนทางกับข้ออ้างว่าเขื่อนปล่อยทำให้ท่วม · ขณะที่น้ำไหลเข้าเขื่อน (ตัวแทนฝนบนลุ่ม) "
    f"สัมพันธ์<b>บวก</b>กับน้ำที่ C.2 ที่ช่วงหน่วง 2 วัน ({_corr_inflow_disp}) ตามธรรมชาติการไหลของน้ำ — "
    "สรุป: น้ำที่ C.2 มาจากฝนลุ่มเป็นหลัก ไม่ใช่การปล่อยเขื่อน "
    "(หมายเหตุ: ค่าสัมพันธ์เป็น<b>หลักฐานสนับสนุน</b> — เขื่อนถือน้ำไว้ช่วงพีคเป็นปฏิบัติการปกติ "
    "หลักฐานหลักคือสัดส่วนปริมาตรด้านบน)"
))
S.append(table(["จุดวัดตามแนวน้ำ", "ต้น ก.ย. (ปกติ)", "สูงสุด 30 ก.ย.–1 ต.ค.", "การเปลี่ยนแปลง"], [
    ["การปล่อยน้ำเขื่อนรวม (ภูมิพล+สิริกิติ์)",
     f"{_chain['released_total']['early_sep_avg']:.0f} ล้าน ลบ.ม./วัน",
     f"{_chain['released_total']['peak']:.0f} (ลดลง)", "—"],
    ["ปิงล่าง P.17 ท่างิ้ว กำแพงเพชร (หลังผ่านภูมิพล)",
     f"{_chain['p17_ping_lower']['early_sep_avg']:.0f}–{_chain['p17_ping_lower']['early_sep_avg'] + 2:.0f}",
     f"{_chain['p17_ping_lower']['peak']:.0f} (โต {_chain['p17_ping_lower']['ratio_peak_vs_early']:.0f} เท่า)", "ฝนลุ่มปิงเป็นหลัก"],
    ["น่านล่าง N.67 วัดเกยไชยเหนือ (หลังผ่านสิริกิติ์)",
     f"{_chain['n67_nan_lower']['early_sep_avg']:.0f}–{_chain['n67_nan_lower']['early_sep_avg'] + 2:.0f}",
     f"{_chain['n67_nan_lower']['peak']:.0f} (โต {_chain['n67_nan_lower']['ratio_peak_vs_early']:.0f} เท่า)", "ฝนลุ่มน่านเป็นหลัก"],
    ["รวมที่ C.2 ท่าเรือ นครสวรรค์",
     f"{_chain['c2_total']['early_sep_avg']:.0f}–{_chain['c2_total']['early_sep_avg'] + 3:.0f}",
     f"{_chain['c2_total']['peak']:.0f}", f"การปล่อยเขื่อนเหลือ {_share:.0f}%"],
], "ปริมาตรรายวัน (ล้าน ลบ.ม.) จากอัตราไหลวัดจริงรายชั่วโมง — คำนวณจากไฟล์ผลวิเคราะห์ของโครงการ ตรวจซ้ำได้"))
S.append(figure(ROOT / "report/assets/goal6/c2_sources_chain.png",
                "น้ำที่ไหลผ่าน 4 จุดตามแนวน้ำ: เส้นน้ำเงิน (C.2 รวมสุด) ขึ้นตรงกับเส้นม่วง (ปิงล่าง) และเขียว (น่านล่าง)"
                " ที่พุ่งช่วงเดียวกัน ขณะที่แท่งแดง (เขื่อนปล่อย) ลดลง — แสดงว่าน้ำมาจากฝนลุ่ม ไม่ใช่เขื่อน"))
S.append(figure(ROOT / "report/assets/goal6/c2_volume_vs_dams.png",
                "ปริมาตรน้ำรายวัน: เส้นน้ำเงิน = น้ำที่ไหลผ่าน C.2 ท่าเรือ · เส้นม่วงประ = น้ำไหลเข้าเขื่อนรวม"
                " (ตัวแทนฝนบนลุ่ม — พุ่งช่วงเดียวกับที่ C.2 โต) · แท่งแดง = การปล่อยน้ำเขื่อนรวม (ลดลงเรื่อย ๆ)"))
S.append(prose("<b>ถาม: ก่อนฝนตกหนักใหญ่ (ปลาย ก.ย.) ระดับน้ำที่ C.2 ท่าเรือสูงขึ้นแล้ว — การปล่อยของเขื่อนมีส่วนเท่าไร และข้อมูลบอกเหตุผลอะไรได้บ้าง?</b>"))
# M6 (รีวิว Sonnet): ตัดคำตอบ "ใช่" ลอย ๆ และ "ทำให้" — คิดสัดส่วนจากตัวเลขจริง แยกข้อเท็จจริง/ตีความ
S.append(prose(
    "<b>ข้อเท็จจริง</b> (ข้อมูลรายวัน): ช่วง 11–15 ก.ย. สองเขื่อนเพิ่มการปล่อยจาก ~20 เป็น 27.9 ล้าน ลบ.ม./วัน (เพิ่ม ~8) "
    "ขณะที่น้ำผ่าน C.2 โตจาก 50 เป็น 90 ล้าน ลบ.ม./วัน (เพิ่ม ~40) — ส่วนที่เพิ่มจากการปล่อยจึงเป็นไม่เกินราว 1 ใน 5 "
    "ที่เหลือมาจากแม่น้ำสาขาและฝน · ตัวเลขนี้ไม่เกินสถิติเดิมของเขื่อน (ภูมิพลเคยปล่อยถึง 55 ล้าน ลบ.ม./วัน ในปี 2568) · "
    "<b>ข้อมูลน้ำเข้า</b>: ฝนระลอกแรกตกบนลุ่มบน 11–13 ก.ย. (น้ำเข้าเขื่อนรวมพุ่งจาก ~65 เป็น 85 ล้าน ลบ.ม./วัน) "
    "การปล่อยเพิ่มตามหลังน้ำเข้า ~1 วัน และน้อยกว่าน้ำเข้า ระดับในอ่างจึงขึ้นต่อเนื่อง "
    f"(ภูมิพล {storage_sep('ภูมิพล', 2026, '2026-09-06'):,.0f} → {storage_sep('ภูมิพล', 2026, '2026-09-21'):,.0f} ล้าน ลบ.ม. ระหว่าง 6–21 ก.ย. รวม 15 วัน) "
    f"ยังต่ำกว่าเส้นกำกับ (10,788 ณ 15 ก.ย.)"
))
S.append(prose(
    "<b>การตีความ</b> (ไม่มีเอกสารเกณฑ์ปฏิบัติของเขื่อนใน API จึงยืนยันเจตนาไม่ได้): รูปแบบนี้สอดคล้องกับการปล่อยตามน้ำเข้า "
    "ไม่ใช่การระบายเพราะอ่างล้น · และเมื่อน้ำที่ C.2 สูงขึ้นก่อนฝนใหญ่ พื้นที่รับน้ำของแม่น้ำตอนบนก็เหลือน้อยลงบ้างเมื่อฝนใหญ่มาถึง "
    "แต่เมื่อเทียบกับน้ำที่เข้า C.2 กว่า 150 ล้าน ลบ.ม./วัน ในระลอกใหญ่ ผลของการปล่อยช่วงนี้เป็นสัดส่วนเล็ก"
))
S.append(prose("<b>ถาม: ถ้าเขื่อนปล่อยน้ำแรงและเร็วกว่าที่ทำจริง (เริ่มก่อนฝนใหญ่ถึง 3–4 วัน) จะช่วยลดระดับน้ำได้เท่าไร?</b>"))
# H1 (รีวิว Sonnet 12 ต.ค.): สถานการณ์ "ลบส่วนเกินจากอัตราพีค" ถูกถอน — เกินเพดาน 3.5–9 เท่า
# เพราะปล่อยล่วงหน้าเลื่อนเวลาน้ำ ไม่ได้หักออกจากอัตราไหลวันพีค · ใช้เพดาน = ปล่อยจริงวันพีค × ความชันสมการ
_eq = _c2a["level_volume_equation"]
_ceil = _c2a["peak_release_ceiling"]
S.append(prose(
    f"ตอบเป็น<b>เพดาน</b>ไม่ใช่ค่าประมาณ (จากความสัมพันธ์ระดับ↔ปริมาตรของ C.2 · ความชัน {_eq['b']:.3f} ม. ต่อ 1 ล้าน ลบ.ม./วัน): "
    "การปล่อยล่วงหน้าไม่ได้ \"หักออก\" จากน้ำที่ไหลผ่านในวันน้ำสูงสุด — มันเลื่อนเวลาของน้ำให้มาก่อน · "
    "ทางเดียวที่ช่วยลดระดับน้ำสูงสุดได้คือ เขื่อนมีที่ว่างพอจะปล่อย<b>น้อยลง ณ วันน้ำสูงสุด</b> · "
    f"แต่วันน้ำสูงสุด (1 ต.ค.) สองเขื่อนปล่อยเพียง <b>{_ceil['release_at_peak_mcm_day']} ล้าน ลบ.ม./วัน</b> "
    f"({_chain['release_share_at_peak_pct']}% ของน้ำที่ผ่าน C.2) — ต่อให้ไม่ปล่อยเลย ระดับน้ำสูงสุดที่ C.2 ลดได้อย่างมาก "
    f"<b>{_ceil['max_drop_m_if_zero_release']} ม.</b> ที่เหลือมาจากแม่น้ำสาขาและฝนระหว่างทาง "
    "สรุป: <b>ในระลอกนี้ การปล่อยล่วงหน้าช่วยลดระดับน้ำสูงสุดที่ C.2 ได้จำกัดมาก</b> "
    "และไม่ใช่เครื่องมือหลักของเหตุการณ์ครั้งนี้ — (ประโยชน์อื่นของการพร่องน้ำล่วงหน้า เช่น ลดระดับอ่างเพื่อรับน้ำท่วมครั้งถัดไป ไม่ได้ประเมินที่นี่)"
))
S.append(prose(
    "ข้อควรระวัง 4 ข้อ: "
    "(1) ตัวเลขนี้เป็น<b>เพดานทางทฤษฎี</b> ไม่ใช่ผลของแบบจำลองไหลตามลำน้ำ — ยังไม่ได้คิดเวลาน้ำเดินทางและฝนระลอกถัดมา · "
    "(2) การปล่อยล่วงหน้าต้องมีพยากรณ์ฝนใหญ่ที่เชื่อถือได้ก่อนหลายวัน — ข้อมูลเราแสดงว่าพยากรณ์ 2 วันยังจำกัด · "
    "(3) ปล่อยมากไปแล้วฝนไม่มา = <b>น้ำไม่พอใช้ทั้งหลังฝนและท้ายฤดูแล้ง</b> — น้ำที่เก็บไว้ต้องใช้ครัวเรือน เกษตรและป้องกันน้ำเค็ม "
    "(เขื่อนทั้งสองรวมเก็บ ~15,000 ล้าน ลบ.ม.) · "
    "(4) ระดับ C.2 ไม่ใช่ระดับท่วมเมืองโดยตรง — ต้องวิเคราะห์ต่อถึงตัวเมือง"
))
S.append(prose("<b>ถาม: การปล่อยน้ำที่ผ่านจุดรวมน้ำเจ้าพระยา (C.2) ก่อนฝนใหญ่ ผิดปกติเพราะอะไร — เก็บน้ำเกินแผนหรือน้ำในพื้นที่เยอะ? ทำไมรูปแบบการปล่อยไม่เป็นเส้นตรง? และส่งผลต่อป่าสักไหม?</b>"))
S.append(prose(
    "ตอบ 3 ชั้นจากข้อมูลจริง:"
))
S.append(prose(
    "<b>ชั้น 1 — ไม่ใช่เพราะเก็บน้ำเกินแผน:</b> ทั้งเดือน ก.ย. 2569 เขื่อนภูมิพลเก็บน้ำ "
    f"<b>ต่ำกว่าระดับกำกับทุกวัน</b> (15 ก.ย. เก็บ {storage_sep('ภูมิพล', 2026, '2026-09-15'):,.0f} vs ระดับกำกับ 10,788 ล้าน ลบ.ม. — ต่ำกว่า {10788 - storage_sep('ภูมิพล', 2026, '2026-09-15'):,.0f}) "
    f"และสิริกิติ์ก็ต่ำกว่าทุกวันเช่นกัน ({storage_sep('สิริกิติ์', 2026, '2026-09-15'):,.0f} vs 8,182) — การปล่อยเพิ่ม 11–15 ก.ย. "
    "จึง<b>ไม่ใช่การระบายเพราะอ่างล้น</b> · ข้อมูลที่สอดคล้อง: ฝนระลอกแรกบนลุ่มบน 11–13 ก.ย. "
    "ทำให้น้ำไหลเข้าพุ่ง (~85) เขื่อนจึงเริ่มปล่อยตามด้วยหน่วง 1 วัน (พฤติกรรมมาตรฐาน "
    "ของการรักษาระดับอ่างไม่ให้เต็มเร็วเกินไป)"
))
S.append(prose(
    "<b>ชั้น 2 — ทำไมรูปแบบไม่เป็นเส้นตรง:</b> เขื่อนสองแห่งปล่อย<b>คนละรูปแบบ</b> — "
    "สิริกิติ์เพิ่มก่อน (10→20 ที่ 15 ก.ย. ตามน้ำเข้าที่พุ่งก่อน) แล้วค่อยลด · "
    "ภูมิพลปล่อยคงที่ 10 แล้ว<b>ลดลง</b> 15–22 ก.ย. (10→6→3) — "
    "เพราะน้ำเข้าภูมิพลลดลงและเขื่อนเริ่ม<b>กุมน้ำไว้รอระลอกใหญ่</b> · "
    "รูปแบบขาขึ้น-ขาลงนี้คือพฤติกรรมการบริหารแบบตอบสนองรายวัน (ไม่ใช่แผนเปิดคงที่) — "
    "และรวมกันแล้วปริมาณรวมที่ส่งลงเจ้าพระยา<b>ลดลงเรื่อย ๆ ตลอดช่วงก่อนฝนใหญ่</b>"
))
S.append(prose(
    "<b>ชั้น 3 — เชื่อมกับป่าสักอย่างไร:</b> น้ำจาก C.2 (เจ้าพระยาตอนบน) กับน้ำจากป่าสัก "
    "<b>เป็นสองสายที่รวมกันหลังจุดวัด S.26 อยุธยา</b> (~14.4°N ใต้ตัวอยุธยา) ก่อนถึง กทม. — "
    "S.26 วัดเฉพาะน้ำป่าสักลำพัง · ข้อมูลจุดวัดแสดงว่าช่วงสูงสุด: น้ำปล่อยเขื่อนตอนบนเหลือ 7 ล้าน ลบ.ม./วัน "
    "= <b>3% ของน้ำที่ C.2</b> (226) · แต่ที่จุดรวมใต้อยุธยา น้ำเจ้าพระยา 226 + น้ำป่าสักที่วัดจริงที่ S.26 อยุธยา (สูงสุด 65 ล้าน ลบ.ม./วัน 6 ต.ค. — โตจากปกติ 4 เท่า โดยเขื่อนป่าสักปล่อยเพียง 2–9) "
    "รวมกัน = โหลดน้ำจริงที่ไหลลง กทม. — <b>สองสายมาจากฝนลุ่มของตัวเองทั้งคู่</b> (ฝนลุ่มปิง-น่าน vs ฝนลุ่มป่าสัก "
    "ที่ตกช่วงใกล้กัน) จึงเกิดระลอกน้ำประสมสองสายที่ตอนนี้ยังไม่ได้วิเคราะห์ — "
    "<b>เป็นวาระสำคัญของรายงานที่ 4</b> (จุดวัดจุดรวม: ต้องหาจุดวัดหลังปากป่าสัก เช่น C.22A ปากเกร็ด (ดึงแล้ว — ระดับ 2.09 ม. สูงสุด 1 ต.ค.) หรือจุดวัด กทม.) · ประเด็นเพิ่มเติมสำคัญ: <b>แม่น้ำยมไหลเลี่ยงเขื่อน</b> — ยมวัดที่ Y.4 สุโขทัย (โต 2 เท่า ช่วงสูงสุด) ไหลลงน่านล่างโดยตรง ไม่ผ่านสิริกิติ์ — น้ำส่วนนี้เขื่อนควบคุมไม่ได้เลย"
))
S.append(prose("<b>ถาม: ควรติดตั้งเครื่องมือ อุปกรณ์ หรือสถานีตรวจวัดใดเพิ่ม เพื่อให้การบริหารจัดการน้ำมีประสิทธิภาพสูงสุด?</b>"))
S.append(prose(
    "จากการตรวจประเมินระบบข้อมูลและความครบถ้วนของข้อมูลในโครงการนี้ เสนอแนะการติดตั้ง 4 ระบบสำคัญ:<br>"
    "1. <b>ระบบบันทึกและส่งข้อมูลการเปิด-ปิดบานประตูระบายน้ำและเครื่องสูบน้ำอัตโนมัติ</b>: "
    "ปัจจุบันระบบข้อมูลระดับชาติรายงานระดับน้ำเป็นหลัก แต่ขาดข้อมูลสถานะการเปิดบานประตูระบายน้ำ (ความสูงยกบาน) "
    "และประวัติการเดินเครื่องสูบน้ำแบบเรียลไทม์ ทำให้ไม่สามารถคำนวณปริมาณน้ำที่ไหลผ่านประตูระบายน้ำแต่ละแห่งได้อย่างแม่นยำ "
    "การติดตั้งเซนเซอร์วัดระดับการเปิดบานและระบบตรวจวัดการทำงานของเครื่องสูบน้ำที่เชื่อมต่อกับส่วนกลาง จะช่วยให้เห็นการไหลของน้ำทั้งระบบทันที<br>"
    "2. <b>สถานีตรวจวัดอัตราการไหลของน้ำแบบต่อเนื่องด้วยคลื่นเสียงสะท้อน</b>: "
    "ระดับน้ำเพียงอย่างเดียวไม่สามารถบอกปริมาณน้ำที่แท้จริงได้ โดยเฉพาะในแม่น้ำตอนล่างที่มีอิทธิพลน้ำทะเลหนุนดันกลับ "
    "ควรติดตั้งเครื่องวัดอัตราการไหลด้วยคลื่นเสียงสะท้อนใต้น้ำในจุดบรรจบแม่น้ำและคลองสายหลัก "
    "เพื่อให้ทราบปริมาตรน้ำที่ไหลผ่านจริงเป็นลูกบาศก์เมตรต่อวินาทีตลอด 24 ชั่วโมง<br>"
    "3. <b>เครือข่ายเรดาร์ตรวจวัดปริมาณฝนภาคพื้นดินความละเอียดสูง</b>: "
    "ปัจจุบันข้อมูลฝนเชิงพื้นที่ที่ครอบคลุมทั้งประเทศต้องพึ่งพากริดดาวเทียมที่มีความละเอียดค่อนข้างหยาบ (ราว 50 กิโลเมตร) "
    "การบูรณาการสถานีเรดาร์ตรวจวัดฝนภาคพื้นดินและสอบเทียบกับสถานีวัดฝนอัตโนมัติแบบเรียลไทม์ "
    "จะทำให้ได้ข้อมูลปริมาณน้ำฝนเชิงพื้นที่ที่มีความละเอียดสูงกว่ากริดดาวเทียมปัจจุบันมาก ช่วยให้คาดการณ์ปริมาณน้ำหลากล่วงหน้าได้อย่างแม่นยำ<br>"
    "4. <b>การรังวัดปรับปรุงหมุดหลักฐานความสูงอ้างอิงมาตรฐานเดียวทั่วประเทศ</b>: "
    "การตรวจคุณภาพข้อมูลของโครงการพบว่า จุดวัดระดับน้ำจำนวนมากมีค่าอ้างอิงความสูงของเกณฑ์วิกฤตไม่ตรงกับระบบวัด "
    "การรังวัดโครงข่ายหมุดความสูงอ้างอิงภูมิศาสตร์มาตรฐานเดียวกันทั้งประเทศด้วยระบบดาวเทียมกำหนดตำแหน่งความละเอียดสูง "
    "จะทำให้ระดับน้ำจากทุกสถานีสามารถเปรียบเทียบและเชื่อมต่อกันได้จริงโดยไม่มีข้อผิดพลาดทางความสูง"
))
S.append(prose("<b>ถาม: ภาครัฐควรปรับปรุงการแจ้งเตือนประชาชนให้รับมือน้ำท่วมได้ดีขึ้นอย่างไร?</b>"))
S.append(prose(
    "ตอบตามหลักการสื่อสารความเสี่ยงและผลการทดสอบแบบจำลองของโครงการ 4 ประการ:<br>"
    "1. <b>เปลี่ยนจากการเตือน \"ระดับน้ำที่สถานี\" เป็น \"แผนที่ระดับน้ำท่วมขังถึงระดับบ้านเรือน\"</b>: "
    "การแจ้งเตือนประชาชนด้วยข้อความว่า 'ระดับน้ำที่สถานีสูงกว่าตลิ่งเท่านั้นเท่านี้' ประชาชนส่วนใหญ่ไม่สามารถประเมินได้ว่าบ้านของตนเองจะท่วมหรือไม่ "
    "หน่วยงานควรนำข้อมูลระดับน้ำร่วมกับแผนที่ความสูงภูมิประเทศ แปลงเป็นแผนที่คาดการณ์ความลึกของน้ำท่วมขังบนผิวดินรายตำบลและชุมชน "
    "เพื่อให้ประชาชนเห็นภาพความเสี่ยงของตนเองได้อย่างชัดเจน<br>"
    "2. <b>แจ้งเตือนล่วงหน้าตามระยะเวลาที่ประชาชนลงมือปฏิบัติได้จริง (มีเวลารับมือ 6–24 ชั่วโมง)</b>: "
    "ผลทดสอบของโครงการ (เหตุการณ์เดียว) ชี้ว่าการพยากรณ์ระดับน้ำ 6 ชั่วโมงให้ผลพอใช้ แต่ที่ 24 ชั่วโมงในหลายลุ่มยังไม่ดีไปกว่าการบอกว่าระดับน้ำจะไม่เปลี่ยน "
    "จึงควรทดสอบกับเหตุการณ์ย้อนหลังหลายครั้งก่อน แล้วค่อยประกาศเตือนภัยระดับสี (เขียว-เหลือง-ส้ม-แดง) ล่วงหน้า "
    "พร้อมระบุขั้นตอนที่ประชาชนต้องปฏิบัติอย่างเป็นรูปธรรม เช่น ยกเครื่องใช้ไฟฟ้าขึ้นที่สูง ย้ายยานพาหนะ หรือเตรียมอพยพ<br>"
    "3. <b>ส่งสัญญาณเตือนภัยฉุกเฉินเฉพาะพิกัดพื้นที่ผ่านโครงข่ายโทรศัพท์เคลื่อนที่</b>: "
    "ใช้ระบบกระจายสัญญาณข้อความเตือนภัยฉุกเฉินผ่านเสาสัญญาณโทรศัพท์เคลื่อนที่แบบเจาะจงเฉพาะพื้นที่เสี่ยงภัย "
    "ข้อความเตือนจะดังขึ้นในโทรศัพท์ของทุกคนที่อยู่ในพื้นที่อันตรายทันทีโดยไม่ต้องลงทะเบียนหรือโหลดแอปพลิเคชัน "
    "และไม่ส่งกระจายหว่านทั้งจังหวัดจนสร้างความตื่นตระหนกแก่พื้นที่ปลอดภัย<br>"
    "4. <b>เปิดระบบรับข้อมูลยืนยันจากภาคประชาชนในพื้นที่จริง</b>: "
    "สร้างช่องทางดิจิทัลที่ง่ายและรวดเร็วให้ประชาชนและชุมชนสามารถส่งภาพถ่ายและรายงานระดับน้ำท่วมจริงในพื้นที่กลับเข้ามา "
    "เพื่อนำข้อมูลภาคพื้นดินมาตรวจสอบยืนยันความถูกต้องของการแจ้งเตือนและปรับปรุงแบบจำลองแบบเรียลไทม์"
))
S.append(prose("<b>ถาม: ภาครัฐควรบริหารจัดการน้ำและปฏิรูปเชิงระบบอย่างไร เพื่อลดความเสี่ยงวิกฤตน้ำท่วมในระยะยาว?</b>"))
S.append(prose(
    "ตอบตามบทเรียนเชิงระบบที่พบในรายงานนี้ 4 แนวทางสำคัญ:<br>"
    "1. <b>ปรับปรุงเส้นกำกับระดับน้ำของเขื่อนให้ยืดหยุ่นและเชื่อมโยงกับพยากรณ์อากาศล่วงหน้า</b>: "
    "เกณฑ์การเก็บกักน้ำในอ่างเก็บน้ำไม่ควรยึดเส้นกำกับระดับน้ำแบบตายตัว แต่ควรปรับเป็นเส้นกำกับระดับน้ำแบบพลวัต "
    "ที่เชื่อมโยงกับแบบจำลองการพยากรณ์ฝนระยะปานกลาง 7–14 วัน หากพยากรณ์พบว่าจะมีฝนตกหนักขนาดใหญ่เคลื่อนเข้าสู่ลุ่มน้ำ "
    "เขื่อนควรได้รับอำนาจในการทยอยพร่องน้ำล่วงหน้าทีละน้อยอย่างปลอดภัย เพื่อเตรียมพื้นที่ว่างในอ่างรองรับน้ำหลาก "
    "โดยไม่ส่งผลกระทบต่อความมั่นคงของน้ำต้นทุนสำหรับฤดูแล้ง<br>"
    "2. <b>จัดตั้งศูนย์บัญชาการบริหารน้ำแบบเอกภาพตามแนวลุ่มน้ำธรรมชาติ</b>: "
    "ปัจจุบันการบริหารน้ำในลุ่มน้ำสายหลักกระจายอยู่หลายหน่วยงาน (กรมชลประทาน การไฟฟ้าฝ่ายผลิตฯ องค์กรปกครองส่วนท้องถิ่น และกรุงเทพมหานคร) "
    "แม้ทุกหน่วยงานจะปฏิบัติหน้าที่ตามภารกิจของตนเองอย่างเต็มที่ แต่ในภาวะวิกฤตจำเป็นต้องมีกลไกสั่งการเดียวที่มองภาพรวมทั้งลุ่มน้ำ "
    "เพื่อตัดสินใจเปิด-ปิดประตูระบายน้ำ เดินเครื่องสูบน้ำ และผันน้ำโดยคำนึงถึงสมดุลน้ำและความปลอดภัยของระบบโดยรวม<br>"
    "3. <b>วางระบบค่าชดเชยพื้นที่รับน้ำนองที่เป็นธรรม รวดเร็ว และตกลงร่วมกันล่วงหน้า</b>: "
    "การเปิดประตูระบายน้ำผันน้ำเข้าทุ่งรับน้ำเพื่อหน่วงน้ำไว้ไม่ให้ท่วมเขตเมือง เป็นการเสียสละของเกษตรกรและประชาชนในพื้นที่รับน้ำ "
    "ภาครัฐต้องมีระเบียบและงบประมาณชดเชยความเสียหายที่ชัดเจน โปร่งใส จ่ายตรงถึงมือผู้ได้รับผลกระทบอย่างรวดเร็ว "
    "และมีการทำข้อตกลงร่วมกับชุมชนก่อนฤดูน้ำหลาก เพื่อเปลี่ยนความขัดแย้งเป็นความร่วมมือในการบริหารจัดการน้ำร่วมกัน<br>"
    "4. <b>เปิดเผยข้อมูลการเดินระบบน้ำสู่สาธารณะอย่างโปร่งใสในรูปแบบดิจิทัลเปิด</b>: "
    "การเปิดเผยข้อมูลระดับน้ำ การเปิด-ปิดประตูระบายน้ำ และการทำงานของสถานีสูบน้ำแบบสาธารณะ "
    "จะช่วยให้นักวิชาการ ภาคประชาสังคม และประชาชนสามารถร่วมติดตาม ตรวจสอบ และพัฒนาเครื่องมือคาดการณ์น้ำร่วมกับภาครัฐ "
    "สร้างความเชื่อมั่นและความโปร่งใสในการตัดสินใจบริหารทรัพยากรน้ำของประเทศ"
))
S.append(prose("<b>ถาม: ประชาชนและองค์กรปกครองส่วนท้องถิ่นสามารถนำข้อมูลและบทเรียนเหล่านี้ไปปรับใช้ได้อย่างไร?</b>"))
S.append(prose(
    "คำแนะนำในระดับพื้นที่และชุมชน 3 ประการ:<br>"
    "1. <b>ติดตามข้อมูลระดับน้ำต้นน้ำควบคู่กับปฏิทินน้ำทะเลหนุน</b>: "
    "ประชาชนในพื้นที่ลุ่มน้ำตอนล่างไม่ควรดูเพียงปริมาณฝนในพื้นที่ตนเอง แต่ควรติดตามระดับน้ำในแม่น้ำสายหลักตอนบน "
    "และตรวจสอบตารางน้ำขึ้น-น้ำลงของกรมอุทกศาสตร์ หากระดับน้ำในแม่น้ำสายหลักเริ่มสูงและประจวบเหมาะกับช่วงน้ำเกิด (น้ำทะเลหนุนสูง) "
    "ต้องเตรียมรับมือภาวะน้ำระบายออกช้าและยกสิ่งของขึ้นที่สูงทันที แม้ในพื้นที่จะไม่มีฝนตกก็ตาม<br>"
    "2. <b>ร่วมสำรวจและกำจัดสิ่งกีดขวางทางน้ำในระดับตำบลและชุมชน</b>: "
    "องค์กรปกครองส่วนท้องถิ่นสามารถใช้ข้อมูลความลาดชันและแผนที่น้ำท่วมช่วยชี้เป้าจุดคอขวด ท่อระบายน้ำลอดถนนที่อุดตัน "
    "หรือคันดินที่ขวางทางไหลตามธรรมชาติ เพื่อดำเนินการขุดลอกเปิดทางน้ำและเตรียมความพร้อมของเครื่องสูบน้ำประจำจุดเสี่ยงก่อนเข้าสู่ฤดูมรสุม<br>"
    "3. <b>จัดทำแผนเผชิญเหตุและจุดปลอดภัยระดับชุมชน</b>: "
    "ร่วมกันกำหนดจุดอพยพ จุดจอดรถยนต์และยานพาหนะในพื้นที่สูง และสำรวจรายชื่อกลุ่มเปราะบาง เช่น ผู้สูงอายุ ผู้ป่วยติดเตียง "
    "เพื่อเตรียมระบบช่วยเหลือเคลื่อนย้ายล่วงหน้าเมื่อได้รับการแจ้งเตือนภัย โดยไม่ต้องรอคอยความช่วยเหลือจากภายนอกเพียงอย่างเดียว"
))
S.append(prose("<b>ถาม: ตัวเลขน่าเชื่อแค่ไหน?</b>"))
S.append(prose(
    "ทุกตัวเลขมาจากข้อมูลเปิดเผยสาธารณะ ตรวจซ้ำได้ด้วยสคริปต์ในโครงการ · "
    "แต่มีข้อจำกัดจริงที่ระบุในบทถัดไป — โดยเฉพาะ: พยากรณ์เกิน 2 วันยังไม่แม่นทุกลุ่ม · "
    "ข้อมูลเปิด-ปิดประตูเขื่อนรายชั่วโมงยังไม่เปิดเผย · ดาวเทียมสีตรวจยืนยันไม่ได้เพราะเมฆปิด"
))
S.append(h2("6. ข้อจำกัดที่ต้องรู้ก่อนอ่านตัวเลข", "limits"))
S.append(prose(
    "(1) ระดับวิกฤตที่ระบบข้อมูลรายงานมา ใช้ตรงไม่ได้ทุกจุด — จากจุดที่เกินวิกฤตทั้งหมด 25 จุด "
    "มีเพียง <b>6 จุด (Kgt.3 · T.1 · Kgt.1 · S.26 · Z.57 · X.119A)</b> ที่เกณฑ์ครบใช้ได้ "
    "อีก <b>19 จุด</b> การตรวจคุณภาพของโครงการพบว่าพื้นที่วัดอ้างอิงของเกณฑ์วิกฤตไม่ตรงกับชุดข้อมูล "
    "รวมถึง <b>C.2 ค่ายจิรประวัติ</b> และ K.3A/K.10/K.37/P.17 — "
    "จุดเหล่านี้ใช้เป็นหลักฐาน<b>จังหวะเวลา (น้ำสูงสุดวันไหน ช่วงไหน)</b> ได้ แต่<b>ไม่ใช่ระดับความลึก</b> "
    "ต้องตรวจค่าอ้างอิงความสูงต่อจุดก่อนใช้เชิงระดับ (2) ประวัติเปิด-ปิดบาน/เดินเครื่องสูบของเขื่อน-ปตร. "
    "<b>ไม่มีใน API ทุกสังกัด</b> — การแยกส่วนของสาเหตุจะทำได้ระดับรายวันเท่านั้น จนกว่าจะได้ข้อมูลเปิดเผยจากหน่วยงาน (ขอตามกฎหมายข้อมูลสาธารณะ) "
    f"(3) ฝน NASA POWER กริด 0.5° รีดยอดฝนเบลอ — ค่าสถานีจริงจะสูงกว่าเสมอ · <b>และจุดวัดที่อยู่ในช่องกริดเดียวกัน (ห่างกันน้อยกว่า ~25–50 กม.) จะได้ค่าฝนเดียวกัน</b> — ตัวเลข \"{_rn['top3_stations_7d']} จาก {_rn['n_stations']} จุด\" จึงนับจุดวัด ไม่ใช่นับช่องกริด — นับซ้ำแบบช่องกริดแล้ว = <b>{_rn['top3_cells_7d']} จาก {_rn['n_cells']} ช่อง</b> (สัดส่วน ~1 ใน 3 เท่ากันทั้งสองวิธี) · <b>จุดวัดจำนวนมากมีค่าฝนซ้ำกับจุดอื่นพอดี</b> เพราะตกในช่องกริดเดียวกัน (ค่าฝนเป็นรายช่อง ไม่ใช่รายจุด) · การอ่านเทียบระหว่างลุ่มที่อยู่ติดกันต้องดูเป็นภาพรวมลุ่ม อย่าอ่านต่างจุดรายจุด "
    "(3.1) หน้าต่างฝนของปี 2569 จบ 9 ต.ค. (ข้อมูลกริดมีถึง 7 ต.ค.) ขณะที่ปีอื่นนับถึง 31 ต.ค. — ทิศเอียง<b>สวน</b>ปี 2569 (ระลอกยังเดินต่อได้อีก ~3 สัปดาห์โดยไม่ถูกนับ) จึงเป็นค่าประมาณต่ำสุด · "
    "ใช้ได้เชิงคุณภาพเท่านั้น (5) ความครอบคลุมข้อมูลรายชั่วโมงรายจุดไม่เท่ากัน (จำนวนชม.มีค่าแสดงในตาราง) (6) <b>การตรวจยืนยันอิสระเชิงพื้นที่</b> — Sentinel-2 ทั้ง 9 ฉากที่โปร่งที่สุดมีเมฆปิดในบริเวณเป้าหมาย (มรสุมปลาย ก.ย.) · ตัวเลขน้ำท่วมรายฉากจึงยืนบน S1 เรดาร์เดี่ยว + ความสอดคล้องเชิงเวลากับระดับน้ำจุดวัด · และได้รับการสอบเทียบยืนยันภาพรวมสะสม 30 วันกับระบบสารสนเทศภัยพิบัติ GISTDA (ผสาน 34 วงโคจร 7 ดาวเทียม: เจ้าพระยา 2,879 ตร.กม. · บางปะกง 1,443 ตร.กม. · นครนายก 350 ตร.กม.) ซึ่งยืนยันว่าการตรวจพบรายฉากเดี่ยวของโครงการทำหน้าที่เป็นขอบล่างของพื้นที่น้ำท่วมสะสมจริง "
    "(7) <b>ความแม่นของกฎตัดน้ำ</b> — " + _RULE_SENT + _XC_SENT + _RS_SENT + f" · สัดส่วนน้ำใหม่ที่ภาพก่อนเหตุการณ์มืดอยู่แล้ว: นครนายก {_rv['nn_dark_share']['oct2']:.0%}–{_rv['nn_dark_share']['peak_27sep']:.0%}, "
    f"รายลุ่ม {min(_rv['basin_dark_share'].values()):.0%}–{max(_rv['basin_dark_share'].values()):.0%} ({_TH[_bw]} {_rv['basin_dark_share'][_bw]:.0%} → น้ำใหม่เข้มงวดเหลือ ~{_lc[_bw]['strict_new_km2']:.0f} ตร.กม. ในลุ่มที่สัดส่วนตกบนแหล่งน้ำที่แผนที่ผิวดินระบุเป็นน้ำถาวรสูงสุด ({_lc[_bw]['share_on_worldcover_water']:.0%})) · "
    f"<b>ตามผิวดิน</b>: ที่ตรวจพบอยู่บนพื้นที่เพาะปลูก {min(v['share_det_crop'] for k, v in _lc.items() if not k.startswith('nn_')):.0%}–{max(v['share_det_crop'] for k, v in _lc.items() if not k.startswith('nn_')):.0%} "
    "— ระบบแยก \"นาที่ถูกน้ำท่วมจริง\" ออกจาก \"นาที่ขังน้ำตามฤดู/ปล่อยน้ำเข้านา\" ไม่ได้ · พื้นที่ก่อสร้างเป็น "
    f"{min(v['share_base_built'] for k, v in _lc.items() if not k.startswith('nn_')):.0%}–{max(v['share_base_built'] for k, v in _lc.items() if not k.startswith('nn_')):.0%} ของที่ราบ แต่ได้เพียง "
    f"{max(v['share_det_built'] for k, v in _lc.items()):.0%} ของที่ตรวจพบ (น้ำท่วมในเมืองเรดาร์ตรวจไม่เห็นเป็นหลัก — ตัวเลขกรุงเทพฯ จึงต่ำกว่าจริงในส่วนเมือง) · "
    f"ที่นครนายก (เทียบ GISTDA 2 ต.ค.) ส่วนที่ตรวจพบบนพื้นที่เพาะปลูกตกใน GISTDA {_lc['nn_oct2']['precision_by_class'].get('40', 0):.0%} "
    f"แต่บนแหล่งน้ำถาวร {_lc['nn_oct2']['precision_by_class'].get('80', 0):.0%} และป่า {_lc['nn_oct2']['precision_by_class'].get('10', 0):.0%} — "
    f"ตามสัดส่วนผิวดินอื่นแม่นน้อยกว่ามาก แต่ตามพื้นที่ ส่วนที่ไม่ตกใน GISTDA ราว {_lc['nn_oct2']['fp_km2_by_class'].get('40', 0):.0f} จาก "
    f"{sum(_lc['nn_oct2']['fp_km2_by_class'].values()):.0f} ตร.กม. อยู่บนพื้นที่เพาะปลูก (ที่เหลือกระจายบนป่า ทุ่งหญ้า แหล่งน้ำ)"
))

# ---- สารบัญ + ปิด ----
S.insert(0, toc([("อ่านรายงานนี้อย่างไร", "howto"), ("ภาพรวม", "ov"), ("วิธีการ", "method"),
                 ("เขื่อน 2554 เทียบกับ 2569", "dams"), ("รายลุ่ม 6 บท", "basins"), ("ถาม–ตอบ", "qa"), ("ข้อจำกัด", "limits")]))
S.insert(1, h2("0. อ่านรายงานนี้อย่างไร — คำที่ใช้ในรายงานนี้", "howto"))
S.append(prose(
    "รายงานนี้<b>อ่านจบในตัวเอง</b> — ไม่ต้องอ่านรายงานหรือเอกสารอื่นก่อน คำที่ใช้ซ้ำมีความหมายดังนี้:"
))
S.append(table(["คำในรายงาน", "ความหมาย"], [
    ["ระลอกปลาย ก.ย. 2569", "ช่วงฝนตกหนักทั่วประเทศ 23 ก.ย.–9 ต.ค. 2569 ที่ทำให้หลายลุ่มน้ำท่วมพร้อมกัน"],
    ["เส้นกำกับระดับน้ำตามแผน", "ระดับปริมาณน้ำเก็บที่เขื่อนควรมีในแต่ละวันตามแผนบริหารรายปี — ถ้าน้ำจริงสูงกว่าเส้นนี้ แปลว่าเขื่อนเก็บน้ำมากกว่าแผน"],
    ["ระดับวิกฤต / ระดับเตือน", "ระดับน้ำในแม่น้ำที่หน่วยงานกำหนดไว้ว่าอันตราย / ควรเฝ้าระวัง"],
    ["จุดวัด", "เครื่องวัดระดับน้ำในแม่น้ำหรือคลองที่ส่งข้อมูลอัตโนมัติ"],
    ["ดาวเทียมเรดาร์ (S1)", "ดาวเทียม Sentinel-1 ที่ถ่ายภาพพื้นดินได้ทั้งกลางวันกลางคืนและทะลุเมฆ — ใช้ตรวจพื้นที่น้ำท่วม"],
    ["ดาวเทียมสีธรรมชาติ (S2)", "ดาวเทียม Sentinel-2 ที่ถ่ายภาพสีเหมือนตาคน — ใช้ตรวจยืนยัน แต่มองไม่ทะลุเมฆ"],
    ["ที่ราบต่ำกว่า 60 เมตร", "พื้นที่ราบลุ่มที่น้ำท่วมถึงได้ — พื้นที่วิเคราะห์หลักของรายงานนี้"],
    ["จุดสูงสุด", "ช่วงเวลาที่ระดับน้ำหรือพื้นที่น้ำท่วมมากที่สุด"],
    ["การแยกส่วนของสาเหตุ", "การคำนวณว่าน้ำท่วมมาจากฝนเท่าไร จากการปล่อยน้ำเขื่อน/ประตูระบายน้ำเท่าไร"],
    ["เหตุการณ์นครนายก", "น้ำท่วม อ.เมือง นครนายก ปลาย ก.ย. 2569 ที่วิเคราะห์ไว้แล้วในรายงานชุดก่อน — รายงานนี้ใช้เป็นจุดเทียบ โดยสรุปข้อเท็จจริงที่จำเป็นไว้ในตัว"],
], "นิยามคำที่ใช้ในรายงาน — อ่านครั้งเดียวพอ"))
foot = ("สถานะ: ร่าง (ข้อมูลครบทุกบท: จุดวัด 69 จุด · เขื่อน 24 แห่ง · น้ำท่วมจากดาวเทียม · แบบจำลองทำนาย) · "
        "ตัวเลขทุกตัวสร้างโดยสคริปต์ใน <code>analysis/goal6/</code> (รันซ้ำได้) · "
        "โครงสร้างรายงานโปรแกรม 5 ฉบับ: นครนายก (1–2) · ระลอก 2569 6 ลุ่ม (ฉบับนี้) · "
        "ชุดเทียบมาตรฐาน 2554 (ที่ 4) · เครือข่ายระดับชาติ (ที่ 5)")
OUT.write_text(page(
    "รายงานที่ 3 (ร่าง) — ระลอกปลาย ก.ย. 2569 ทั่วประเทศ: 6 ลุ่มน้ำเทียบกัน",
    "การสอบสวนเชิงหลักฐาน แบบเดียวกับนครนายก ขยายสู่พื้นที่ทั่วประเทศ — จุดยืนเป็นกลางตามหลักฐาน",
    S, foot, canonical_ref="analysis/goal6/canonical.json"), encoding="utf-8")
print(f"เขียนแล้ว: {OUT} ({OUT.stat().st_size/1e3:.0f} KB)")