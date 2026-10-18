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


def tbl_nuclear_point() -> str:
    P = C["nuclear_site"]["point"]
    rows = []
    for x in P["flood_passes"]:
        rows.append(["<code>"+x["pass"]+"</code>", "อยู่ในพื้นที่น้ำท่วม" if x["inside"] else "ไม่อยู่ในพื้นที่น้ำท่วม", "—" if x["inside"] else f"{x['nearest_flood_m']:,}"])
    return table(["ภาพดาวเทียม (วันที่_เวลา)", f"หมุดศูนย์ ({P['lat']:.4f}, {P['lon']:.4f})", "น้ำท่วมที่ใกล้ที่สุด (ม.)"], rows,
                 P["src"] + " · ภาพเรดาร์อาจไม่เห็นน้ำใต้ต้นไม้/อาคาร · ภาพชุด S1C_20260928_0550 และ S1D_20260929_1812 ไม่ครอบคลุมพื้นที่นี้ (ระยะหลายร้อยกิโลเมตร)")


def tbl_dev_mix() -> str:
    M = _L["mix"]
    rows = [[r["use"], r["share_pct"], f"{r['rai']:,}", r["net_mb_per_rai"], f"{r['total_mb']:,}", r["note"]] for r in M["rows"]]
    rows.append(["รวม (เฉลี่ยถ่วงน้ำหนัก)", 100, f"{M['rai']:,}", M["blend_mb_per_rai"], f"{M['total_mb']:,}", f"เท่ากับร้อยละ {M['cover_loan_pct']} ของเงินกู้"])
    return table(["การใช้ที่ดิน (ตัวอย่าง)", "สัดส่วนพื้นที่ (%)", "พื้นที่ (ไร่)", "รายได้สุทธิ (ล้านบาท/ไร่)", "รวม (ล้านบาท)", "เงื่อนไขสำคัญ"], rows,
                 f"สมมติฐานของผู้จัดทำ ไม่ใช่ข้อมูลตลาด · แถบข้างละ {M['strip_m_each_side']} ม. ตลอดแนวคลอง · ต้องแก้ตัวเลขตามราคาที่ดินจริงก่อนใช้ตัดสินใจ")


def tbl_construction_phases() -> str:
    EC = C["eia_construction"]
    rows = []
    for r in EC["contracts_table"]:
        rows.append([r["phase"], r["contract"], r["reach"], r["km"], f"พ.ศ. {r['start_fy']}–{r['end_fy']}", r["scope"]])
    cap = (
        f"แหล่ง: {EC['src']} · ลำดับงานก่อสร้าง: <b>{EC['direction']}</b> — {EC['rationale']} · "
        f"ระยะเวลาก่อสร้าง {EC['duration_years_eia']} ปี (พ.ศ. {EC['fiscal_years_eia']}) ตามรายงานผลกระทบสิ่งแวดล้อม หรือ {EC['duration_years_cabinet']} ปี (พ.ศ. {EC['fiscal_years_cabinet']}) ตามกรอบมติ ครม."
    )
    return table(["ระยะการก่อสร้าง", "สัญญา", "ช่วงพื้นที่", "หลัก กม.", "ปีงบประมาณ", "ขอบเขตงานสำคัญ"], rows, cap)


def tbl_ongkharak_oct2026_status() -> str:
    OF = C["ongkharak_flood"]
    st = OF["stations_oct2026"]
    rows = [
        [f"สถานี {st['atg101_chula']['code']} ({st['atg101_chula']['name']})", f"นอก ปตร. (เจ้าพระยา) {st['atg101_chula']['watergate_out_msl']:.2f} / ในคลอง {st['atg101_chula']['watergate_in_msl']:.2f} ม.รทก.", "เจ้าพระยาสูงกว่าในคลอง 1.0 ม.", st['atg101_chula']['status']],
        [f"สถานี {st['atg08_dhammaraja']['code']} ({st['atg08_dhammaraja']['name']})", f"เหนือน้ำ {st['atg08_dhammaraja']['watergate_in_msl']:.2f} / ท้ายน้ำ {st['atg08_dhammaraja']['watergate_out_msl']:.2f} ม.รทก.", "สูบและผลักน้ำข้าม ปตร. ไปทิศตะวันออก", st['atg08_dhammaraja']['status']],
        ["อ.องครักษ์ (พื้นที่ลุ่มต่ำท้ายลุ่ม / TNy10)", f"มัธยฐาน DEM {OF['dem_median_m']['องครักษ์']} ม.รทก. (น้ำคลอง {st['tny10_ongkharak']['level_m_oct17']:.2f} ม.)", "น้ำยังท่วมขังต่อเนื่องถึงกลาง ต.ค. 2569", f"หมู่บ้าน {OF['low_villages_count']} แห่งในโซนท้ายลุ่ม ระดับดินต่ำ 1.0–2.5 ม.รทก. ขังค้างในแอ่ง"],
        [f"สถานี {st['ny7_mueang']['code']} ({st['ny7_mueang']['name']})", f"ระดับน้ำ {st['ny7_mueang']['level_m_oct17']:.2f} ม. (ระดับตลิ่ง {st['ny7_mueang']['bank_m']} ม.)", "ลดลงสู่ระดับปกติแล้ว", st['ny7_mueang']['status']],
        [f"สถานี {st['bpk003_bangnampriao']['code']} ({st['bpk003_bangnampriao']['name']})", f"ระดับน้ำ {st['bpk003_bangnampriao']['level_m_oct17']:.2f} ม.รทก. (ช่วง {st['bpk003_bangnampriao']['oct17_range_m'][0]:.2f}–{st['bpk003_bangnampriao']['oct17_range_m'][1]:.2f} ม.)", "ทรงตัวสูงต่อเนื่อง", st['bpk003_bangnampriao']['status']],
        [f"สถานี {st['bpk001_bangpakong']['code']} ({st['bpk001_bangpakong']['name']})", f"น้ำขึ้นสูงสุด +{st['bpk001_bangpakong']['high_tide_m']:.2f} / น้ำลงต่ำสุด {st['bpk001_bangpakong']['low_tide_m']:.2f} ม.รทก.", f"แกว่งตัววันละ {st['bpk001_bangpakong']['swing_m']:.2f} ม.", st['bpk001_bangpakong']['status']],
    ]
    cap = (
        f"สถานะ ณ {OF['status_as_of']} · ความลาดชันชลศาสตร์ระหว่างทุ่งองครักษ์กับปลายน้ำ: {OF['hydraulic_gradient']} · "
        f"ลักษณะดิน: {OF['soil_property']} · ภาระรับน้ำ: {OF['retardation_dual']}"
    )
    return table(["จุดสังเกตการณ์ / สถานี", "ระดับน้ำ / ความสูงพื้นดิน", "สถานะน้ำท่วม", "กลไกและการระบาย"], rows, cap)


def tbl_ongkharak_water_balance() -> str:
    H = C.get("ongkharak_hydraulics", {}).get("water_balance", {})
    if not H:
        return ""
    inf = H["inflows_mcm_day"]
    outf = H["outflows_mcm_day"]
    rows = [
        ["1. การสูบและผลักดันน้ำจากทุ่งรังสิต (คลอง 13)", f"{inf['rangsit_pumped_inflow']:.2f} ล้าน ลบ.ม./วัน", f"{H['attribution_shares']['hypothesis_1_rangsit_pumping']}", "สูบข้าม ปตร.พระธรรมราชา มุ่งหน้าทิศตะวันออก"],
        ["2. น้ำหลากตกค้างจากต้นน้ำ (อ.เมือง/บ้านนา)", f"{inf['upstream_residual_runoff']:.2f} ล้าน ลบ.ม./วัน", f"{H['attribution_shares']['hypothesis_2_upstream_estuary_bottleneck'].split(' ')[0]} (ร่วมกับปากอ่าว)", "น้ำหลากค้างทุ่งไหลหลากลงสู่พื้นที่ลุ่มต่ำ"],
        ["3. ฝนตกสะสมในพื้นที่ทุ่งองครักษ์", f"{inf['local_rainfall']:.2f} ล้าน ลบ.ม./วัน", "-", "ฝนตกบนพื้นที่รับน้ำ 286 ตร.กม."],
        ["<b>รวมน้ำไหลเข้าทุ่งทั้งหมด</b>", f"<b>{inf['total_inflow']:.2f} ล้าน ลบ.ม./วัน</b>", "100.0%", "อัตราการเติมน้ำเข้าแอ่งก้นกระทะ"],
        ["4. อัตราการระบายออกจริงสู่อ่าวไทย", f"<b>{outf['effective_gravity_and_pump']:.2f} ล้าน ลบ.ม./วัน</b>", "-", f"ติดน้ำทะเลหนุน ระบายได้เฉลี่ยวันละ {outf['effective_hours_per_day']} ชม. (สัดส่วน {outf['tide_gate_open_ratio']*100:.0f}%)"],
        ["<b>สมดุลมวลน้ำสุทธิสะสม</b>", f"<b>+{H['net_balance_mcm_day']:.2f} ล้าน ลบ.ม./วัน</b>", "-", f"น้ำท่วมขังสะสมในแอ่ง {H['total_stored_water_mcm']} ล้าน ลบ.ม. ต้องใช้เวลาระบาย {H['drain_duration_days_estimate']} วัน"],
    ]
    cap = (
        f"การคำนวณสมดุลมวลน้ำทุ่งองครักษ์ (พื้นที่ลุ่มต่ำ {H['basin_area_sqkm']} ตร.กม. น้ำท่วมขัง {H['inundated_area_sqkm']} ตร.กม. ลึกเฉลี่ย {H['avg_depth_m']*100:.0f} ซม.) · "
        f"ข้อสรุป: {H['conclusion']}"
    )
    return table(["องค์ประกอบสมดุลมวลน้ำ", "ปริมาณน้ำต่อวัน", "สัดส่วนสาเหตุ", "รายละเอียดและกลไกชลศาสตร์"], rows, cap)


def tbl_reach_hydraulic_vectors() -> str:
    vecs = C.get("ongkharak_hydraulics", {}).get("reach_vectors", [])
    if not vecs:
        return ""
    rows = []
    for v in vecs:
        rows.append([
            f"{v['reach_id']}: {v['name']}",
            f"{v['upstream_stage_m']:.2f} vs {v['downstream_stage_m']:.2f} ม.",
            f"{v['head_diff_m']:+.2f} ม. ({v['slope_cm_per_km']:+.2f} ซม./กม.)",
            v['net_flow_direction'],
            f"{v['velocity_ms']:.2f} ม./วิ ({v['discharge_cms']:.1f} ลบ.ม./วิ)",
        ])
    cap = "เวกเตอร์ความลาดเทผิวน้ำ ทิศทางการไหล และความเร็วชลศาสตร์ (คำนวณตามสมการแมนนิ่ง สภาพคลองดินมีวัชพืช รัศมีชลศาสตร์ 2.0 ม.)"
    return table(["ช่วงลำน้ำและคลองระบาย", "ระดับน้ำต้นทาง vs ปลายทาง", "ความต่างระดับ (ความลาดชัน)", "ทิศทางการไหลสุทธิ", "ความเร็วชลศาสตร์ (อัตราการไหล)"], rows, cap)


def tbl_dam_to_gulf_corridors() -> str:
    C_data = C.get("dam_to_gulf_corridors", {})
    if not C_data:
        return ""
    rows = []
    for ckey, clabel in [
        ("corridor_1_khundan", "1. นครนายก–บางปะกง (เขื่อนขุนด่านฯ)"),
        ("corridor_2_pasak", "2. ป่าสัก–เจ้าพระยา2 (เขื่อนป่าสักฯ)"),
        ("corridor_3_chaophraya", "3. เจ้าพระยาสายหลัก (เขื่อนเจ้าพระยา)"),
    ]:
        c = C_data.get(ckey, {})
        if not c:
            continue
        for s in c["segments"]:
            rows.append([
                clabel,
                s["segment_name"],
                f"{s['dist_km']:.1f} กม.",
                f"{s['head_diff_m']:+.2f} ม. ({s['slope_cm_per_km']:+.2f} ซม./กม.)",
                f"{s['velocity_ms']:.2f} ม./วิ",
                f"{s['travel_hours']:.1f} ชม.",
                s["flow_regime"].split("(")[0].strip(),
            ])
    cap = (
        f"การวิเคราะห์เปรียบเทียบชลศาสตร์และเวลาเดินทางน้ำหลากจากแหล่งต้นน้ำ (เขื่อน) สู่ปากอ่าวไทย 3 ระเบียงหลัก · "
        f"ระเบียงนครนายก (132 กม. รวม {C_data['corridor_1_khundan']['total_travel_days']} วัน) ติดคอขวดที่ช่วงองครักษ์–บางน้ำเปรี้ยว · "
        f"ระเบียงป่าสัก–คลองใหม่ (182 กม. รวม {C_data['corridor_2_pasak']['total_travel_days']} วัน) · "
        f"ระเบียงเจ้าพระยาสายหลัก (235 กม. รวม {C_data['corridor_3_chaophraya']['total_travel_days']} วัน)"
    )
    return table(["ระเบียงชลศาสตร์", "ช่วงเส้นทางลำน้ำ", "ระยะทาง", "ความต่างระดับ (ความลาดชัน)", "ความเร็วผิวน้ำ", "เวลาเดินทาง", "ลักษณะการไหล"], rows, cap)


def tbl_dam_to_gulf_accuracy_assessment() -> str:
    C_data = C.get("dam_to_gulf_corridors", {})
    acc = C_data.get("boundary_and_accuracy_assessment", {})
    if not acc:
        return ""

    rows_acc = []
    for item in acc.get("accuracy_summary", []):
        rows_acc.append([
            item["aspect"],
            item["accuracy_level"],
            item["basis"],
        ])
    t1 = table(["มิติการวิเคราะห์ชลศาสตร์", "ระดับความแม่นยำ", "เกณฑ์และหลักฐานเชิงประจักษ์"], rows_acc, "การประเมินความแม่นยำของการวิเคราะห์เวกเตอร์การไหลและสมดุลน้ำ")

    rows_sources = []
    for s in acc.get("sources_included", []):
        rows_sources.append([
            "รวมอยู่ในการวิเคราะห์แล้ว",
            s["category"],
            s["inclusion_type"],
            s["detail"],
        ])
    for s in acc.get("sources_to_be_included", []):
        rows_sources.append([
            "ข้อเสนอเพิ่มเติมเพื่อความสมบูรณ์",
            s["category"],
            s["needed_model"],
            s["importance"],
        ])
    t2 = table(["สถานะการผสานข้อมูล", "องค์ประกอบแหล่งน้ำและขอบเขต", "วิธีการ/แบบจำลอง", "คำอธิบายเชิงวิศวกรรม"], rows_sources, "การจำแนกแหล่งน้ำ ข้อมูลระดับความสูงภูมิประเทศ (DEM) และเงื่อนไขขอบเขตชลศาสตร์")

    return t1 + "\n" + t2


def tbl_bangban_bangsai_comparison() -> str:
    C_data = C.get("bangban_bangsai_case", {})
    if not C_data:
        return ""
    bb = C_data.get("bangban_profile", {})
    cp2 = C_data.get("chaophraya2_profile", {})
    r = C_data.get("ratios", {})
    if not bb or not cp2:
        return ""

    rows = [
        ["ระยะทางรวมของคลอง", f"{bb['length_km']:.1f} กม.", f"{cp2['length_km']:.1f} กม.", f"เจ้าพระยา 2 ยาวกว่า {r['length_ratio_cp2_to_bb']} เท่า"],
        ["อัตราการผันน้ำหลากออกแบบ", f"{bb['capacity_m3s']:,.0f} ลบ.ม./วินาที", f"{cp2['capacity_m3s']:,.0f} ลบ.ม./วินาที", "บางบาลระบายน้ำตัดยอดสูงกว่า 2 เท่า"],
        ["ความกว้างก้นคลอง / รูปตัด", f"110–200 ม. (คลองดินลาดหญ้า)", f"100–160 ม. (ดาดคอนกรีต <code>U-Shape</code> กม.81–135)", "เจ้าพระยา 2 ปรับลดเขตทางเพื่อเลี่ยงเวนคืน"],
        ["ความลึกคลอง", f"{bb['depth_m']:.1f} ม.", f"{cp2['depth_m']:.1f}–18.0 ม. (ช่วงตัดคันเขา)", "เจ้าพระยา 2 ขุดลึกกว่ามากในเขตดอน"],
        ["กรอบงบประมาณเริ่มต้น", f"{bb['initial_budget_mb']:,.0f} ล้านบาท", f"— (ตั้งต้น 1.6 แสนล้าน)", "—"],
        ["กรอบงบประมาณที่อนุมัติ/ประเมิน", f"{bb['approved_budget_mb']:,.0f} ล้านบาท", f"{cp2['baseline_budget_mb']:,.0f} ล้านบาท", f"เจ้าพระยา 2 งบประมาณสูงกว่า {r['budget_ratio_cp2_to_bb']} เท่า"],
        ["ต้นทุนก่อสร้างเฉลี่ยต่อกิโลเมตร", f"{bb['cost_per_km_revised_mb']:,.1f} ล้านบาท/กม.", f"{cp2['cost_per_km_baseline_mb']:,.1f} ล้านบาท/กม.", f"ใกล้เคียงกัน (ต่างกันเพียง {r['cost_per_km_diff_pct']:+.1f}%)"],
        ["พื้นที่เวนคืนที่ดิน", f"~{bb['land_expropriation_rai']:,.0f} ไร่ (740 แปลง)", f"{cp2['land_expropriation_rai']:,.0f} ไร่ (1,378 หลัง)", f"เจ้าพระยา 2 ใช้ที่ดินมากกว่า {r['land_ratio_cp2_to_bb']} เท่า"],
        ["ขอบเขตการปกครองที่พาดผ่าน", f"1 จังหวัด 2 อำเภอ (อยุธยา)", f"5 จังหวัด 11 อำเภอ", "เจ้าพระยา 2 ซับซ้อนข้ามหลายเขตการปกครอง"],
        ["กรอบเวลาก่อสร้างเดิม", f"{bb['planned_duration_years']:.0f} ปี (2562–2566)", f"{cp2['planned_duration_years']:.0f} ปี (2570–2577)", "บางบาลตั้งเป้าเดิม 5 ปี"],
        ["ระยะเวลาก่อสร้างจริง / มติ ครม. ล่าสุด", f"{bb['actual_duration_years']:.1f} ปี (ขีดเส้นตาย ก.ค. 2571)", f"— (ตามแผน ครม. 8 ปี)", f"บางบาลยืดเยื้อเพิ่มขึ้น +{bb['time_overrun_pct']:.0f}%"],
        ["จำนวนสัญญาจ้างงานโยธาหลัก", f"อย่างน้อย 7 สัญญา (+อาคาร 2 แห่ง)", f"คาดการณ์ 25–35 สัญญา", "เจ้าพระยา 2 เสี่ยงปัญหาจุดเชื่อมต่อระหว่างสัญญา"],
        ["อุปสรรคธรณีวิทยาและสิ่งแวดล้อม", "ดินเหนียวอ่อน + น้ำท่วมไซต์งานฤดูฝน", "ดินเหนียวอ่อน + ดินกรด 54% + รอยเลื่อนองครักษ์", "เจ้าพระยา 2 มีความเสี่ยงทางเคมีและธรณีซับซ้อนกว่า"],
    ]
    cap = (
        "ตารางเปรียบเทียบเชิงวิศวกรรมและเศรษฐศาสตร์: คลองระบายน้ำหลากบางบาล–บางไทร (อยุธยา) "
        "เทียบกับ คลองระบายน้ำหลากชัยนาท–ป่าสัก–อ่าวไทย (เจ้าพระยา 2) · แหล่งข้อมูล: มติ ครม. (2562, 2567, 29 ก.ย. 2569) และรายงานผลกระทบสิ่งแวดล้อม"
    )
    return table(["มิติการเปรียบเทียบ", "คลองบางบาล–บางไทร (22.5 กม.)", "คลองเจ้าพระยา 2 (135.7 กม.)", "ข้อสังเกตเชิงระบบ"], rows, cap)


def tbl_bangban_bangsai_scenarios() -> str:
    C_data = C.get("bangban_bangsai_case", {})
    if not C_data:
        return ""
    sc = C_data.get("scenarios", {})
    if not sc:
        return ""

    rows = []
    for skey in ["baseline_official", "scenario_a_bangban_factor", "scenario_b_acid_soil_and_megascale"]:
        s = sc.get(skey, {})
        if not s:
            continue
        rows.append([
            s["title"],
            f"{s['duration_years']:.1f} ปี (เสร็จ พ.ศ. {s['completion_year']})",
            f"{s['budget_mb']:,.0f} ล้านบาท",
            f"{s.get('additional_cost_mb', 0):+,.0f} ล้านบาท" if s.get("additional_cost_mb") else "— (ตามกรอบ)",
            f"{s['cost_per_km_mb']:,.1f} ล้านบาท/กม.",
            s["description"],
        ])

    cap = (
        "แบบจำลองฉากทัศน์กรอบเวลาและงบประมาณของคลองเจ้าพระยา 2 หากเผชิญปัญหาความล่าช้าและการบานปลายของต้นทุนตามบทเรียนจริงของคลองบางบาล–บางไทร"
    )
    return table(["ฉากทัศน์การประเมิน", "ระยะเวลาก่อสร้าง (ปีแล้วเสร็จ)", "งบประมาณรวม", "ส่วนต่างงบประมาณที่เพิ่มขึ้น", "ต้นทุนเฉลี่ยต่อ กม.", "เงื่อนไขและข้อสมมติ"], rows, cap)


# ---------- หน้าต่างการใช้งานจริง เศรษฐศาสตร์ และคอขวดอาคารตัดขวาง (operational_economics) ----------
def tbl_s26_operational_economics() -> str:
    OE = C.get("operational_economics", {})
    if not OE:
        return ""
    prof = OE["s26_operational_profile"]
    rows = [
        ["ปริมาณน้ำท่ารายปีต่ำสุด (ปีน้ำแล้ง)", f"{prof['annual_min_mcm']:,.0f} ล้าน ลบ.ม.", f"{prof['days_dry_year']} วัน", "เปิดผันน้ำได้น้อยมาก"],
        ["ปริมาณน้ำท่าเฉลี่ยช่วงน้ำหลาก (ส.ค.–พ.ย.)", f"{prof['flood_season_mean_mcm']:,.0f} ล้าน ลบ.ม.", f"{prof['days_average_year']} วัน", f"เฉลี่ยคิดเป็นร้อยละ {prof['annual_utilization_avg_pct']}% ของทั้งปี"],
        ["ปริมาณน้ำท่ารายปีสูงสุด (มหาอุทกภัย 2554)", f"{prof['annual_max_mcm']:,.0f} ล้าน ลบ.ม.", f"{prof['days_extreme_flood_year']} วัน", "ผันน้ำต่อเนื่องเต็มอัตราออกแบบ"],
    ]
    cap = (
        f"สถิติน้ำท่าสถานี {prof['station_code']} ({prof['station_name']}) รอบ 39 ปี (พ.ศ. {prof['record_years']}) "
        f"เทียบกับขีดความสามารถการผันน้ำ 600 ลบ.ม./วินาที ({prof['canal_capacity_mcm_per_day']} ล้าน ลบ.ม./วัน) · "
        f"{prof['summary_th']}"
    )
    return table(["สถานการณ์น้ำท่า (ท้ายเขื่อนพระรามหก)", "ปริมาณน้ำท่า", "จำนวนวันผันน้ำเต็มกำลังเทียบเท่า", "ลักษณะการใช้งานจริง"], rows, cap)


def tbl_lifecycle_economics() -> str:
    OE = C.get("operational_economics", {})
    if not OE:
        return ""
    le = OE["lifecycle_economics"]
    rows_disc = []
    for s in le["discount_scenarios"]:
        rows_disc.append([
            f"คิดลด {s['discount_rate_pct']:.0f}%",
            f"{s['crf']:.6f}",
            f"{s['annualized_capital_mb']:,.1f} ล้านบาท/ปี",
            f"{s['total_annual_cost_mb']:,.1f} ล้านบาท/ปี",
            f"{s['cost_per_m3_diverted_baht']:.2f} บาท/ลบ.ม.",
        ])
    t1 = table(["อัตราคิดลด", "สัมประสิทธิ์คืนทุน", "ภาระเงินลงทุนรายปี (30 ปี)", "ภาระค่าใช้จ่ายรวมรายปี (รวมค่าบำรุงรักษา)", "ต้นทุนต่อน้ำผันจริง"],
               rows_disc, f"การคำนวณต้นทุนวงจรชีวิตโครงการ วงเงินลงทุน {le['capex_mb']:,.0f} ล้านบาท ค่าบำรุงรักษา {le['opex_annual_mb']:,.0f} ล้านบาท/ปี ผันน้ำเฉลี่ย {le['annual_diverted_mcm']:,.0f} ล้าน ลบ.ม./ปี")

    rows_alt = []
    for a in le["alternatives_benchmark"]:
        rows_alt.append([
            a["measure"],
            a["cost_per_m3_baht"],
            a["type"],
            a["risk_profile"],
        ])
    t2 = table(["มาตรการบริหารจัดการน้ำหลาก", "ต้นทุนต่อ ลบ.ม. น้ำ", "รูปแบบวิศวกรรม", "ลักษณะความเสี่ยงและการบริหาร"], rows_alt, "การเปรียบเทียบต้นทุนต่อหน่วยน้ำผัน/หน่วงหลาก ระหว่างคลองเจ้าพระยา 2 กับมาตรการทางเลือก")
    return t1 + "\n\n" + t2


def tbl_eia_rejection_history() -> str:
    OE = C.get("operational_economics", {})
    if not OE:
        return ""
    rounds = OE.get("eia_rejection_history", [])
    rows = []
    for r in rounds:
        objs = " • ".join(f"<b>{o['section']}</b>: {o['issue']} ({o['detail']})" for o in r["key_objections"])
        detail_fold = (
            f"<details style='margin-top:4px'><summary style='cursor:pointer;color:#0284c7;font-size:0.85em'>📄 ข้อความจากหนังสือราชการจริง</summary>"
            f"<div style='font-size:0.82em;background:#f8fafc;padding:6px 10px;border-left:3px solid #0284c7;margin-top:4px'>"
            f"มติ คชก. ด้านพัฒนาแหล่งน้ำ: มีมติให้กรมชลประทานจัดทำรายงานใหม่ให้ครบถ้วนตามประเด็นที่กำหนด (หนังสือทางการ: {r['official_letter']})"
            f"</div></details>"
        )
        rows.append([
            f"รอบที่ {r['round_no']} ({r['submission_date']})",
            f"{r['resolution_date']}<br>{r['official_letter']}",
            f"{r['resolution']}{detail_fold}",
            objs,
            r["outcome_th"],
        ])
    cap = "ประวัติการพิจารณารายงานผลกระทบสิ่งแวดล้อม (<code>EIA</code>) และมติคณะกรรมการผู้ชำนาญการฯ (คชก.) สำนักงานนโยบายและแผนทรัพยากรธรรมชาติและสิ่งแวดล้อม (สผ.) ทั้ง 3 รอบ"
    return table(["รอบการยื่นรายงาน", "วันที่มีมติและหนังสือแจ้ง", "มติ คชก.", "ข้อท้วงติงสำคัญและข้อสั่งการ", "ผลลัพธ์และการปรับปรุง"], rows, cap)


def tbl_cross_drainage_bottlenecks() -> str:
    OE = C.get("operational_economics", {})
    if not OE:
        return ""
    cd = OE.get("cross_drainage_bottlenecks", {})
    rows = []
    for b in cd.get("critical_bottleneck_canals", []):
        rows.append([
            b["canal_name"],
            f"กม. {b['km']:.1f}",
            b["province"],
            b["type"],
            b["risk"],
        ])
    cap = (
        f"คลังข้อมูลอาคารตัดขวางคลองระบายน้ำหลากเจ้าพระยา 2 รวม {cd['total_crossing_structures']} แห่ง "
        f"(ท่อลอด/ไซฟอนหลัก {cd['eia_primary_siphons_and_culverts']} แห่ง สะพานรถยนต์ {cd['road_bridges']} แห่ง ประตูเรือ {cd['navigation_locks']} แห่ง) "
        f"และจุดคอขวดเสี่ยงน้ำท่วมขังข้างแนวคลอง · {cd['siphon_siltation_risk_assessment']}"
    )
    return table(["ลำคลองที่ถูกตัดขวาง", "หลัก กม.", "จังหวัด", "ประเภทอาคารเชื่อมต่อ", "ความเสี่ยงชลศาสตร์และตะกอนทับถม"], rows, cap)


def tbl_ongkharak_2d_hypsometric() -> str:
    dep = C.get("ongkharak_2d_depression", {})
    if not dep:
        return ""
    curve = dep.get("hypsometric_curve", [])
    target_stages = {1.0, 1.5, 2.0, 2.4, 2.5, 3.0, 3.2, 3.5, 4.0, 4.5}
    rows = []
    for pt in curve:
        stg = round(pt["stage_msl_m"], 1)
        if stg in target_stages:
            desc = "ระดับน้ำในแอ่งลุ่มต่ำ"
            if stg == 2.4:
                desc = "<b>ระดับน้ำจริงในคลอง (ต.ค. 2569)</b>: ขังค้างในพื้นที่ลุ่มต่ำทุ่งองครักษ์"
            elif stg == 2.5:
                desc = "<b>เกณฑ์น้ำล้นตลิ่งลำคลองธรรมชาติ</b>: น้ำเริ่มแผ่กว้างเข้าสู่พื้นที่เกษตรกรรม"
            elif stg == 3.2:
                desc = "🚨 <b>จุดเปลี่ยนวิกฤต (<code>Tipping Point</code>) — คันทางหลวง 305 ถูกน้ำบ่าข้าม</b>: ปริมาตรน้ำสะสมเกิน 126 ล้าน ลบ.ม. น้ำบ่าข้ามถนนรังสิต–นครนายก สู่โครงข่ายคลองรังสิตโดยตรง"
            elif stg >= 4.0:
                desc = "สภาวะน้ำท่วมเต็มพื้นที่ราบทั้งอำเภอองครักษ์"
            rows.append([
                f"{stg:.1f} ม.รทก.",
                f"{pt['inundated_area_km2']:.1f}",
                f"{pt['inundated_share_pct']:.1f}%",
                f"{pt['storage_volume_mcm']:.2f}",
                f"{pt['mean_depth_m']:.2f}",
                desc,
            ])
    cap = (
        f"เส้นความสัมพันธ์ระดับ–พื้นที่–ปริมาตร 2 มิติ (<code>2D Hypsometric</code>) ของแอ่งก้นกระทะ อ.องครักษ์ "
        f"(พื้นที่รวม {dep.get('total_area_km2', 513.1):.1f} ตร.กม. มัธยฐานความสูง {dep.get('elevation_stats_m', {}).get('median', 3.19):.2f} ม.รทก.) "
        f"วิเคราะห์จากแบบจำลองระดับความสูงภูมิประเทศ 1 ม. (<code>LiDAR</code> ผสาน <code>FABDEM</code> และ <code>Copernicus</code> 30 ม.) — ชี้ชัดจุดเปลี่ยนวิกฤตที่ระดับ +3.20 ม.รทก."
    )
    return table(["ระดับผิวน้ำ", "พื้นที่น้ำท่วม (ตร.กม.)", "สัดส่วนพื้นที่อำเภอ (%)", "ปริมาตรน้ำสะสม (ล้าน ลบ.ม.)", "ความลึกเฉลี่ย (ม.)", "นัยสำคัญทางชลศาสตร์และการบ่าข้าม"], rows, cap)


def box_canal_active_storage_reality() -> str:
    OE = C.get("operational_economics", {})
    csr = OE.get("canal_storage_reality", {})
    if not csr:
        return ""
    return (
        f"<div class='info-box' style='background:#f0f9ff;border:1px solid #bae6fd;border-left:5px solid #0284c7;padding:16px 20px;border-radius:6px;margin:16px 0'>"
        f"<h4 style='margin:0 0 8px 0;color:#0369a1'>📊 การวิเคราะห์ความจุเก็บกักใช้การจริงของคลอง (<code>Active Storage</code>)</h4>"
        f"<p style='margin:0 0 10px 0;line-height:1.6'>"
        f"จากการคำนวณมิติคลองรูปตัดสี่เหลี่ยมคางหมูตลอดความยาว {csr['canal_length_km']} กม. ความลึกน้ำออกแบบ {csr['design_depth_m']:.1f} ม. ท้องคลองกว้าง {csr['bed_width_m']:.1f} ม.:<br>"
        f"• <b>ความจุกักเก็บรวมทั้งลำคลอง (<code>Total Storage</code>)</b>: <b>{csr['total_storage_mcm']:.1f} ล้าน ลบ.ม.</b><br>"
        f"• <b>น้ำกักเก็บก้นคลองที่สูบออกไม่ได้ (น้ำก้นคลอง/<code>Dead Storage</code>) ที่ระดับ 2.0 ม.</b>: <b>{csr['dead_storage_mcm']:.1f} ล้าน ลบ.ม.</b> "
        f"(จำเป็นต้องคงไว้เพื่อสร้างแรงดันต้านทานการพังทลายของลาดตลิ่งดินเหนียวอ่อนกรุงเทพฯ และหลีกเลี่ยงการทรุดตัว)<br>"
        f"• <b>ความจุกักเก็บใช้การจริง (<code>Active Storage</code>)</b>: เหลือเพียง <b>{csr['active_storage_mcm']:.1f} ล้าน ลบ.ม.</b> เท่านั้น<br>"
        f"• <b>ระยะเวลารองรับน้ำหลาก (<code>Buffer Duration</code>)</b>: ที่อัตราการผันน้ำออกแบบ {csr['design_discharge_m3s']:.0f} ลบ.ม./วินาที ({csr['design_discharge_mcm_day']:.2f} ล้าน ลบ.ม./วัน) "
        f"ความจุใช้การ {csr['active_storage_mcm']:.1f} ล้าน ลบ.ม. สามารถรองรับน้ำหลากได้เพียง <b>{csr['buffer_duration_hours']:.1f} ชั่วโมง (ไม่ถึง 1 วัน)</b>"
        f"</p>"
        f"<p style='margin:0;font-size:0.92em;color:#475569;line-height:1.5'>"
        f"<b>ข้อสรุปเชิงนโยบายและวิศวกรรม</b>: {csr['assessment']}"
        f"</p>"
        f"</div>"
    )






