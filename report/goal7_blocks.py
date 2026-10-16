"""ชิ้นส่วนร่วมของรายงาน 7 (ประชาชน) และรายงาน 8 (วิชาการ) — ตารางที่สองฉบับต้องตรงกันเสมอ

กติกา (docs/REPORT_CONVENTIONS.md §3): ตารางที่ปรากฏในทั้งสองฉบับเขียนที่นี่ที่เดียว · ฉบับเรียกใช้ด้วยฟังก์ชัน
จะต่างกันได้เฉพาะ caption (บริบทของฉบับ) · ห้ามคัดลอกโค้ดตารางไปวางใน builder
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal6_reportlib import table  # noqa: E402
from goal7_common import C, fmt  # noqa: E402

_NC = C["new_cases"]
_T, _D, _L, _TO, _HY = _NC["tide"], _NC["deep_cut"], _NC["land_dev"], _NC["tourism"], _NC["hydro"]
_EMB = C["embankment"]["cases"][1]


# ---------- กรณีใหม่ (new_cases) ----------
def tbl_tide_cases() -> str:
    return table(["กรณี", "ความลึกน้ำปกติ (ม.)", "สูงขึ้นที่ปลายคลอง (ม.)", "ที่ กม.102", "ที่ กม.74", "ที่ กม.40", "ช่วงที่สูงขึ้นเกิน 0.25 ม. (กม.)"],
                 [[c["label"], c["normal_depth_m"], c["rise_m"]["134"], c["rise_m"]["102"], c["rise_m"]["74"], c["rise_m"]["40"],
                   f"{c['length_rise_gt_025_km']:.0f}"] for c in _T["cases"]], _T["src"])


def tbl_tide_storage() -> str:
    return table(["ช่วงประตู", "ปริมาตรเก็บต่อผิวน้ำสูงขึ้น 1 ม. (ล้าน ลบ.ม.)", "ชั่วโมงที่ปิดประตูได้ที่น้ำ 600"],
                 [[k.replace("km", "กม.").replace("_", "–"), v["mcm_per_m_rise"], v["hours_at_600_per_m"]] for k, v in _T["storage"].items()],
                 f"ความกว้างผิวน้ำ {_T['water_width_m']} ม. คงที่ (ไม่ปรับตามระดับ) — ค่าคัดกรอง")


def tbl_deep_cut() -> str:
    c2 = _T["cases"][1]
    rows = [
        ["ผิวน้ำที่ กม.40 (ม.รทก.)", "5.25 (สูงกว่าพื้น 3.3 ม.)", f"{_D['water_at_ground_km40_m']} (เสมอพื้น)"],
        ["ลาดผิวน้ำ", "1:25,000", f"1:{_D['slope_1_n']:,}"],
        ["น้ำลึก (ม.)", "7.0", _D["depth_m"]],
        ["พื้นที่หน้าตัดน้ำ (ตร.ม.)", "504", f"{_D['area_m2']:,}"],
        ["ส่วนที่อยู่ต่ำกว่าพื้นเดิม (ตร.ม./หน้าตัด)", f"{_D['area_now_below_ground_m2']}", f"{_D['area_m2']:,}"],
        ["คันเหนือพื้นเดิม ช่วงนครนายก (ม.)", f"สูงสุด {_EMB['crest_above_ground_m']}", f"สูงสุด {_D['crest_above_ground_nn_max_m']}"],
        ["คันเหนือพื้นเดิม ทั้ง กม.38–134 (ม.)", "สูงสุด 4.8", f"สูงสุด {_D['crest_above_ground_max_m']}"],
        ["ดินถมคัน (ตร.ม./หน้าตัด)", f"{_D['bank_fill_now_m2']}", f"{_D['bank_fill_deep_m2']}"],
        ["ดินขุดเพิ่ม กม.23–134 (ล้าน ลบ.ม.)", "—", f"{_D['extra_spoil_mcm_km23_134']}"],
        ["ค่าขุดเพิ่ม (ล้านบาท) ที่ 60–150 บาท/ลบ.ม. (สมมติ)", "—", f"{_D['extra_cut_cost_mb'][0]:,}–{_D['extra_cut_cost_mb'][1]:,}"],
        ["น้ำทะเลหนุนสูงขึ้น 1 ม. ที่ปลายคลอง ผิวน้ำสูงขึ้นที่ กม.102 / 74 / 40 (ม.)",
         " / ".join(str(c2["rise_m"][k]) for k in ("102", "74", "40")), " / ".join(str(_D["tide_rise_m"][k]) for k in ("102", "74", "40"))],
        ["ช่วงที่ผิวน้ำสูงขึ้นเกิน 0.25 ม. จากปลายคลอง (กม.)", f"{c2['length_rise_gt_025_km']:.0f}", f"{_D['tide_rise_len_gt_025_km']:.0f}"],
        ["ปริมาตรเก็บต่อผิวน้ำสูงขึ้น 1 ม. กม.74–134 (ล้าน ลบ.ม.)", _T["storage"]["km74_134"]["mcm_per_m_rise"], _D["storage_mcm_per_m_rise_km74_134"]],
    ]
    return table(["ค่า", "แบบตามรายงาน", "กรณีขุดลึก (คำนวณ)"], rows,
                 "ข้อจำกัด: ไม่ตรวจเสถียรภาพลาดดินเหนียวอ่อนที่ความลึกนี้ · ไม่คิดน้ำใต้ดิน/ความเค็ม · ไม่คิดการต่อกับประตูปลายคลองเดิม")


def tbl_land_dev() -> str:
    return table(["ความกว้างแถบต่อฝั่ง (ม.)", "พื้นที่รวม (ไร่)", "รายได้สุทธิ (ล้านบาท/ไร่)", "รวม (ล้านบาท)", "ร้อยละของเงินกู้"],
                 [[s["strip_m_each_side"], f"{s['rai']:,}", s["net_mb_per_rai"], f"{s['total_mb']:,}", s["cover_loan_pct"]] for s in _L["scenarios"]],
                 f"เงินกู้ {_L['loan_mb']:,} ล้านบาท · งบแผ่นดิน {_L['state_mb']:,} (ชั้น C — ตามที่สมาคมพลเมืองนครนายกอ้าง) · "
                 "ราคาสุทธิที่ทดแทนเงินกู้ทั้งก้อน (ล้านบาท/ไร่): " + " · ".join(f"{k} ม. = {v}" for k, v in _L["breakeven_mb_per_rai_for_loan"].items()))


def tbl_tourism_numbers() -> str:
    return table(["ค่า", "ผล"], [
        ["พื้นที่ผิวน้ำ กม.23–134 (ตร.กม.)", _TO["water_area_km2"]],
        ["แพขนาด 600 ตร.ม. ที่ใช้ผิวน้ำ 1%", f"{_TO['rafts_per_pct_surface']:,}"],
        ["ท้องคลองลาดลงรวม กม.23–134 (ม.)", _TO["bed_fall_km23_134_m"]],
        ["เวลาลอยตามน้ำ 111 กม. ที่ 1.2 ม./วินาที (ชม.)", _TO["drift_hours_111km"]],
        ["ผู้ใช้ที่ต้องมีเพื่อชดเชยค่าดำเนินการ 519 ล้านบาท/ปี (ล้านคน-ครั้ง) ที่กำไร 100/200/400 บาท",
         " / ".join(str(_TO["visitors_to_cover_om_m"][k]) for k in ("100", "200", "400"))],
    ], "แหล่งสนามล่องแก่งเทียม: " + _TO["src_ww"])


def tbl_hydro_days() -> str:
    K = _HY["days_scenarios"]
    return table(["ปีน้ำ", "วันผันน้ำเต็มกำลังเทียบเท่า", "กังหันที่ประตูปลายคลอง (กิกะวัตต์-ชม./ปี)", "กังหันกลางน้ำ 55 สถานี (กิกะวัตต์-ชม./ปี)",
                  "แผงเซลล์แสงอาทิตย์ลอยน้ำ 10–20% (กิกะวัตต์-ชม./ปี)"],
                 [[K[d]["label"], d, K[d]["gate_gwh"], f"{K[d]['kinetic_gwh'][0]}–{K[d]['kinetic_gwh'][1]}",
                   f"{_HY['pv_gwh_per_year'][0]:,.0f}–{_HY['pv_gwh_per_year'][1]:,.0f}"] for d in sorted(K, key=int)],
                 _HY["assumptions"] + " · วันผันน้ำเป็นขอบบน (รายงานผลกระทบสิ่งแวดล้อมระบุผันราว 1–2 เดือนต่อปี) และแผนเดินประตูเชิงตัวเลขของคลองป่าสัก–อ่าวไทยยังไม่พบ")  # gap: gate_rules


def tbl_hydro_params() -> str:
    return table(["ค่า", "ผล"], [
        ["กำลังต่อพื้นที่หน้าตัดกังหัน (วัตต์/ตร.ม.)", _HY["power_density_w_m2"]],
        ["กังหันกลางน้ำครอบ 10% / 20% ของหน้าตัด (กิโลวัตต์/สถานี)", f"{_HY['kinetic'][0]['kw_per_station']} / {_HY['kinetic'][1]['kw_per_station']}"],
        ["55 สถานี (เมกะวัตต์)", f"{_HY['kinetic'][0]['mw_55_stations']} / {_HY['kinetic'][1]['mw_55_stations']}"],
        ["ผลต่างระดับเฉลี่ยที่ประตูปลายคลอง (ม.)", _HY["gate_head_avg_m"]],
        ["สัดส่วนเวลาที่น้ำทะเลต่ำกว่าน้ำในคลอง", _HY["gate_open_fraction"]],
        ["กำลังเฉลี่ยที่ประตูปลายคลองตอนผันน้ำ 600 (เมกะวัตต์)", _HY["gate_power_mw_avg"]],
    ], _HY["assumptions"])


# ---------- ตารางเดิมที่เคยซ้ำสองฉบับ ----------
def tbl_meeting_concerns(caption: str) -> str:
    MT = C["meeting_20260909"]
    return table(["ข้อ", "หัวข้อ", "ข้อกังวล/คำถามที่บันทึก"], [[k["n"], k["topic"], k["text"]] for k in MT["concerns"]], caption)  # gap: n/a


def tbl_design_history(caption: str | None = None) -> str:
    return table(["ปี", "เหตุการณ์", "ชั้น"], [[d["year"], d["event"], d["tier"]] for d in C["design_history"]], caption)


def tbl_participation(caption: str) -> str:
    PART = C["participation"]
    return table(["วันที่", "การประชุม", "ผู้เข้าร่วม (คน)", "เวทีในนครนายก", "หมายเหตุ"],
                 [[x["date"], x["event"], ("—" if x["n"] is None else fmt(x["n"])), {True: "มี", False: "ไม่มี", None: "ไม่ทราบ"}[x["nn_venue"]], x["note"]]
                  for x in PART], caption)


def tbl_econ_rounds(extra_caption: str = "") -> str:
    EE = C["eia_econ"]
    e60 = EE["earlier_2560"]
    return table(["อัตราคิดลด (%)", "ผลตอบแทนทางเศรษฐกิจ (%)", "อัตราส่วนผลประโยชน์ต่อต้นทุน", "มูลค่าปัจจุบันสุทธิ (ล้านบาท)"],
                 [[r["discount"], r["eirr"], r["bcr"], fmt(r["npv_mb"])] for r in EE["rows"]] +
                 [[f"{e60['discount']} (ข้อมูลปี 2560)", e60["eirr"], e60["bcr"], fmt(e60["npv_mb"])]],
                 f"{EE['src']} · {EE['verdict']} · แถวสุดท้ายคือตัวเลขที่ชี้แจงในประชุมสาธารณะ มี.ค. 2560 (ราคาคงที่ปี 2560) ซึ่งคุ้มค่าที่ 12% — ฉบับ 2569 ต่ำลง{extra_caption}")


def tbl_land_by_province(per_rai: bool, caption: str) -> str:
    """ที่ดินเวนคืนรายจังหวัด (ตาราง รายงานผลกระทบสิ่งแวดล้อม เล่ม 2) — ฉบับวิชาการเพิ่มคอลัมน์ ล้านบาท/ไร่"""
    EL2 = C["eia_land"]
    t = EL2["total"]
    head = ["จังหวัด", "ผู้ถือครอง (ราย)", "แปลง", "เนื้อที่ (ไร่)", "ค่าชดเชยที่ดิน (ล้านบาท)"] + (["ค่าชดเชย (ล้านบาท/ไร่)"] if per_rai else [])
    rows = [[r["province"], fmt(r["owners"]), fmt(r["plots"]), fmt(r["rai"]), fmt(r["mb"], 1)] + ([f"{r['mb'] / r['rai']:.2f}"] if per_rai else [])
            for r in EL2["rows"]]
    rows.append(["รวม", fmt(t["owners"]), fmt(t["plots"]), fmt(t["rai"]), fmt(t["mb"], 1)] + ([f"{t['mb'] / t['rai']:.2f}"] if per_rai else []))
    return table(head, rows, caption)


def tbl_civic_concerns(checks: dict | None, caption: str) -> str:
    """ข้อห่วงกังวล 13 ข้อของสมาคมพลเมืองนครนายก (ชั้น C) — ฉบับวิชาการใส่คอลัมน์ผลตรวจ (checks: เลขข้อ → ข้อความ)"""
    head = ["ข้อ", "หัวข้อ", "สิ่งที่ผู้ยื่นระบุ"] + (["ตรวจกับรายงานผลกระทบสิ่งแวดล้อมฉบับ 2569"] if checks is not None else [])
    rows = [[k["n"], k["topic"], k["claim"]] + ([checks.get(str(k["n"]), "ยังไม่ได้ตรวจ")] if checks is not None else [])  # gap: concern_checks_pending
            for k in C["concerns"]]
    return table(head, rows, caption)


# ---------- ดินเปรี้ยว (acid_soil) ----------
_AS = C["acid_soil"]


def tbl_acid_areas() -> str:
    A = _AS["areas"]
    rows = []
    for code in ("Ok", "Rs", "Bp"):
        s = _AS["series"][code]
        a1, a2 = A["km23_110"].get(code, 0), A["km110_135"].get(code, 0)
        rows.append([f"{s['name']} (<code>{code}</code>)", s["ph"], f"{a1:,} ({a1 / A['km23_110']['total'] * 100:.1f}%)",
                     f"{a2:,} ({a2 / A['km110_135']['total'] * 100:.1f}%)" if a2 else "—", s["note"]])
    rows.append(["รวม 3 ชุดดินกรด", "", f"{sum(A['km23_110'].get(k, 0) for k in ('Ok', 'Rs', 'Bp')):,} ({_AS['acid_share_km23_110']}%)",
                 f"{A['km110_135']['Bp']:,} ({_AS['acid_share_km110_135']}%)", f"ทั้งแนว {_AS['acid_rai_all']:,} จาก {_AS['soil_rai_all']:,} ไร่ ({_AS['acid_share_all']}%)"])
    return table(["ชุดดิน", "ความเป็นกรด-ด่างตามรายงาน", "กม.23–110 ไร่ (ร้อยละ)", "กม.110–135 ไร่ (ร้อยละ)", "ลักษณะสำคัญ"], rows,
                 _AS["src"] + f" · ชุดดินองครักษ์อยู่เฉพาะ กม.23–110 (อ่านจากแผนที่ ราว กม.{_AS['ok_km_map'][0][0]}–{_AS['ok_km_map'][0][1]} และ {_AS['ok_km_map'][1][0]}–{_AS['ok_km_map'][1][1]} ±2 กม.)")


def tbl_acid_lime() -> str:
    L, V = _AS["lime_mt"], _AS["excavation_acid_mcm"]
    rows = [[("ตามแบบในรายงาน (ขุดต่ำกว่าพื้นเดิมราว 3.7 ม.)" if k == "design" else "กรณีขุดลึก (ราว 12 ม.)"), V[k],
             L[k]["0.2"], L[k]["0.5"], L[k]["1.0"], f"{_AS['lime_cost_mb'][k][0]:,}–{_AS['lime_cost_mb'][k][1]:,}"] for k in ("design", "deep")]
    a = _AS["assumptions"]
    return table(["กรณี", "ดินที่ขุดในชุดดินกรด (ล้าน ลบ.ม.)", "ปูนที่ต้องใช้ ถ้ากำมะถัน 0.2% (ล้านตัน)", "ถ้า 0.5%", "ถ้า 1.0%", "ค่าปูนที่ 0.5% (ล้านบาท)"], rows,
                 f"สมมติฐาน: ความหนาแน่นดิน {a['bulk_density_t_m3']} ตัน/ลบ.ม. · ปูน {a['caco3_kg_per_t_per_pct_s']} กก./ตันดิน ต่อกำมะถัน 1% × เผื่อ {a['safety']} เท่า · "
                 f"ราคาปูน {_AS['lime_price_baht_per_t'][0]:,}–{_AS['lime_price_baht_per_t'][1]:,} บาท/ตัน · {a['note']}")


def tbl_nn_water_users() -> str:
    W = C["nn_water_users"]
    return table(["ประเด็นที่ผู้แทนผู้ใช้น้ำนครนายกกังวล", "มาตรการที่รายงานระบุ"], W["pairs"],
                 f"ประชุมกลุ่มย่อยผู้ใช้น้ำ {W['date']} ณ {W['place']} (ผู้แทนนครนายก {W['n_reps']} คน) · {W['src']}")


def tbl_nn_venues_2566() -> str:
    V = C["nn_venues_2566"]
    rows = [[f"เวทีที่ {r['venue']}", r["when"], r["area"], r["place"], " · ".join(r["topics"])] for r in V["rows"]]
    tc, al = V["topic_counts"], V["all_total"]
    top = sorted(tc.items(), key=lambda kv: -kv[1])[:4]
    cap = (V["src"] + " · สรุป " + str(V["n_venues"]) + " เวทีที่เกี่ยวกับนครนายก: " +
           " · ".join(f"{k} {v} เวที (ทั้งโครงการ {al[k]} จาก 32)" for k, v in top if v) + " · " + V["banna_note"])
    return table(["เวที", "วัน-เวลา", "พื้นที่ (ตำบล)", "สถานที่", "ประเด็นที่เวทีให้ความสำคัญ"], rows, cap)


def tbl_nuclear_villages() -> str:
    N = C["nuclear_site"]
    rows = [[v["village"], v["dist_km"], v["side"], f"{v['canal_km']:.0f}", v["dem_m"] if v["dem_m"] is not None else "—"] for v in N["villages"]]
    return table(["หมู่บ้านในตำบลทรายมูล (อ.องครักษ์)", "ห่างแนวคลอง (กม.)", "ฝั่งของคลอง", "ตรงกับคลอง กม.", "ความสูงผิวพื้น (ม.รทก.)"], rows,
                 "แนวคลองไม่เป็นทางการ · พิกัดหมู่บ้านและความสูงผิวพื้นจากข้อมูลของโปรเจกต์ (±2–4 ม.) · ที่ตั้งศูนย์วิจัยนิวเคลียร์อยู่ในตำบลนี้ (หมู่ 7) แต่ไม่มีพิกัดแน่ชัด")
