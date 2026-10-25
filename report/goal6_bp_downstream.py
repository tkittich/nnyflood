"""รายงานเป้าหมาย 6 ฉบับ 3 — ส่วนเพิ่ม "ท้ายน้ำบางปะกง: ทำไมฉะเชิงเทรา ท่วมหนักและนาน" (เรนเดอร์จาก canonical.json คีย์ bp_downstream เท่านั้น)
ส่วนนี้เป็นการวิเคราะห์เพิ่มหลังกำหนดคำถาม Q1–Q7 ล่วงหน้า (exploratory) — ติดป้ายในรายงานชัดเจน · ห้ามพิมพ์ตัวเลขตัวชี้วัดเป็น literal (ทุกค่ามาจาก canonical)
ใช้: from goal6_bp_downstream import section ; section(S, can, h3, note, prose, table)
"""
from __future__ import annotations

_MON = {"09": "ก.ย.", "10": "ต.ค."}
_SAT = {"S1C": "เซนทิเนล-1ซี", "S1D": "เซนทิเนล-1ดี", "rd2": "เรดาร์แซต-2", "cm2": "คอสโม-สกายเมด 2", "cm4": "คอสโม-สกายเมด 4", "TH2": "ธีออส-2", "S2B": "เซนทิเนล-2บี", "S2C": "เซนทิเนล-2ซี"}


def _d(date: str) -> str:
    return f"{int(date[8:10])} {_MON.get(date[5:7], date[5:7])}"


def _scene(code: str) -> str:
    k, _, hhmm = code.split("_")
    return f"{_SAT.get(k, 'ดาวเทียมอื่น')} {hhmm[:2]}:{hhmm[2:]}"


def _dem_band() -> str:
    """ความไม่แน่นอนของการปรับความสูง อ่านจากผลตัดทีละหน้าต่าง (ไม่พิมพ์ตัวเลขเอง)"""
    import json
    from pathlib import Path
    j = json.loads((Path(__file__).resolve().parent.parent / "analysis/goal7/dem_bias_correction.json").read_text(encoding="utf-8"))["leave_one_window_out"]
    return f"ค่าคลาดเฉลี่ยสัมบูรณ์รายหน้าต่าง {j['corrected_mae_range_m'][0]:.1f}–{j['corrected_mae_range_m'][1]:.1f} ม."


def _miss_txt(days) -> str:
    """วันที่ไม่มีคอลเลกชันระหว่างวันแรกกับวันสุดท้ายของตาราง (รีวิวรอบ 7: คำอธิบายเดิมไม่บอกวันที่ขาดกลางช่วง)"""
    import datetime as _dt
    ds = sorted({_dt.date.fromisoformat(x["date"]) for x in days})
    if len(ds) < 2:
        return ""
    miss = [ds[0] + _dt.timedelta(days=i) for i in range((ds[-1] - ds[0]).days + 1) if ds[0] + _dt.timedelta(days=i) not in ds]
    if not miss:
        return ""
    runs, cur = [], [miss[0]]
    for d in miss[1:]:
        if (d - cur[-1]).days == 1:
            cur.append(d)
        else:
            runs.append(cur); cur = [d]
    runs.append(cur)
    mon = {9: "ก.ย.", 10: "ต.ค."}
    txt = ", ".join(f"{r[0].day}" if len(r) == 1 else f"{r[0].day}–{r[-1].day}" for r in runs)
    return f" · ระหว่างวันที่ในตารางยังขาดวันที่ {txt} {mon.get(miss[0].month, miss[0].month)} (ไม่มีคอลเลกชันในคลัง)"


def section(S: list, can: dict, h3, note, prose, table) -> None:
    b = can.get("bp_downstream")
    if not b:
        return
    ba, tr, ga, sy, ff, er = b["basin"], b["terrain"], b["gauges"], b["story"], b["flood_freq"], b["event_rain"]
    ch = tr["provinces"]["ฉะเชิงเทรา"]
    low = ch["low2m"]
    ve = tr["variance_explained"]
    bpk = ga["BPK003"]
    ov = ba["overlap"]
    cover = sum(v["share_of_basin_pct"] for v in ov.values())
    sh_lo, sh_hi = min(v["share_of_province_in_basin_pct"] for v in ov.values()), max(v["share_of_province_in_basin_pct"] for v in ov.values())
    S.append(h3("4.7 ส่วนเพิ่ม: ท้ายน้ำบางปะกง — ระดับน้ำที่ฉะเชิงเทรายังสูงเหนือตลิ่ง และอะไรอธิบายพื้นที่ท่วม"))
    S.append(note(
        "<b>ป้ายสถานะ: วิเคราะห์เพิ่มหลังกำหนดคำถามล่วงหน้า (exploratory)</b> — หัวข้อนี้ไม่อยู่ในคำถาม Q1–Q7 ที่ตั้งไว้ก่อนดูผลของรายงานฉบับนี้ "
        "เพิ่มเมื่อ 25 ต.ค. 2569 หลังเห็นว่าฉะเชิงเทรายังท่วมอยู่ จึงอ่านเป็นเบาะแสและอาจเปลี่ยนเมื่อมีข้อมูลเพิ่ม · ตัวเลขทั้งหมดอ่านจากไฟล์ตัวเลขกลาง canonical.json (หมวดท้ายน้ำบางปะกง)"
    ))
    S.append(prose(
        "<b>ข้อเท็จจริง:</b> "
        f"(1) ลุ่มบางปะกง (ไล่ตามแปลงลุ่มน้ำย่อย {ba['n_subbasins']} แปลง) กว้าง {ba['area_km2']:,.0f} ตร.กม. ครอบคลุมนครนายก ปราจีนบุรีและฉะเชิงเทรา ร้อยละ {sh_lo:.0f}–{sh_hi:.0f} ของพื้นที่แต่ละจังหวัด "
        f"ข้อมูลภูมิประเทศและน้ำท่วมในส่วนนี้ครอบคลุมสามจังหวัด คิดเป็นร้อยละ {cover:.0f} ของทั้งลุ่ม · "
        f"พื้นที่รับน้ำเหนือสถานีบางน้ำเปรี้ยวมี {ba['upstream_of_bpk003_km2']:,.0f} ตร.กม. (ร้อยละ {100 * ba['upstream_of_bpk003_km2'] / ba['area_km2']:.0f} ของทั้งลุ่ม) ขณะที่ฉะเชิงเทรามี {ch['land_km2']:,.0f} ตร.กม. · "
        f"(2) ถ้าจัดเซลล์ตามชั้นความสูงพื้นดิน จะอธิบายความต่างของสัดส่วนน้ำท่วมได้ร้อยละ {100 * ve['by_elevation_zone']:.0f} แต่จัดตามจังหวัดอธิบายได้เพียงร้อยละ {100 * ve['by_province']:.1f} (ช่วงน้ำท่วม 30 วันของ GISTDA ที่ดึง 25 ต.ค.) · "
        f"ร้อยละ {low['land_pct']:.0f} ของฉะเชิงเทรามีพื้นต่ำกว่า 2 ม.รทก. และน้ำท่วมของจังหวัดตกบนพื้นชั้นนี้ราวร้อยละ {100 * low['flooded_km2'] / max(ch['flooded_km2_grid'], 1):.0f} · "
        f"(3) สถานีบางน้ำเปรี้ยว ({bpk['province']}) ระดับน้ำสูงกว่าตลิ่งต่อเนื่อง {bpk['run_above_bank_days_to_latest']:.0f} วันจนถึง {bpk['latest_time'][:10]} (ยังสูงกว่า {bpk['latest_minus_bank_m']:.2f} ม.) ยอดน้ำ {bpk['peak_m']:.2f} ม.รทก. เมื่อ {_d(bpk['peak_time'][:10])} "
        f"ช้ากว่ายอดแรกที่เหนือน้ำ {sy['lag_first_upstream_to_bpk003_days']:.0f} วัน และลดวันละราว {sy['bpk003_recession_m_per_day_last7d']:.2f} ม. (ถ้าลดเท่านี้ต่อไป ราว {sy['bpk003_days_to_bank_if_same_rate']:.0f} วันจึงต่ำกว่าตลิ่ง — คำนวณจากอัตราคงที่ ไม่ใช่การพยากรณ์) "
        f"ความชันผิวน้ำระหว่างบางน้ำเปรี้ยวกับสถานีท้ายน้ำไม่เกิน {sy['slope_m_per_km_upper_bound']:.2f} ม.ต่อ กม. (ระยะเส้นตรง) · "
        f"(4) รอบ 14 ปีที่ผ่านมา ฉะเชิงเทรามีพื้นที่เคยท่วม {ff['ฉะเชิงเทรา']['ever_flooded_km2']:,.0f} ตร.กม. และท่วมอย่างน้อย 3 ปี {ff['ฉะเชิงเทรา']['ge3_years_km2']:,.0f} ตร.กม. "
        f"ส่วนปราจีนบุรีท่วมซ้ำบ่อยกว่า (อย่างน้อย 5 ปี {ff['ปราจีนบุรี']['ge5_years_km2']:,.0f} ตร.กม. เทียบ {ff['ฉะเชิงเทรา']['ge5_years_km2']:,.0f} ตร.กม.) · "
        "(พื้นที่ในข้อ (4) วัดจากขอบรูปหลายเหลี่ยมของชั้นความถี่น้ำท่วม 14 ปี ซึ่งไม่มีค่าพื้นที่ท่วมสุทธิ จึงใหญ่กว่าตัวเลขข้ออื่นราวสองเท่า เทียบกันตรง ๆ ไม่ได้) · "
        f"(5) ข้อมูลประกอบนอกพื้นที่ฉะเชิงเทรา: สถานีวัดฝน {er['with_data']} แห่งรอบที่ราบองครักษ์–นครนายกรายงานฝนสะสม 20 ก.ย.–4 ต.ค. มัธยฐาน {er['station_total_mm']['median']:.0f} มม. สูงสุด {er['station_total_mm']['max']:.0f} มม."
    ))
    gcodes = ["Kgt.3", "Kgt.6", "PRC004", "Kgt.1", "BPK003", "BPK004", "BPK001"]
    rows = [[f"{ga[c]['name']} ({ga[c]['province']})", f"{ga[c]['bank_m']:.2f}", f"{ga[c]['latest_m']:.2f}", f"{ga[c]['latest_minus_bank_m']:+.2f}",
             f"{ga[c]['peak_m']:.2f} ({_d(ga[c]['peak_time'][:10])})", f"{ga[c]['hours_above_bank_30d']:.0f}", f"{ga[c]['run_above_bank_days_to_latest']:.1f}"] for c in gcodes if c in ga]
    S.append(table(["สถานี", "ตลิ่ง", "ล่าสุด", "ต่างจากตลิ่ง", "ยอดน้ำ (วันที่)", "ชม.เหนือตลิ่ง (30 วัน)", "วันต่อเนื่อง"], rows,
                   "ระดับน้ำสถานีโทรมาตรลุ่มบางปะกง เทียบตลิ่งฝั่งต่ำ (ม.รทก.) เรียงจากเหนือน้ำไปปลายน้ำ · ค่าศูนย์ของสถานีต่างกันได้เล็กน้อย จึงอ่านเป็นลำดับเวลา ไม่ใช่ความชันที่แม่นยำ"))
    dd = b.get("gistda_daily", [])
    if dd:
        drows = [[_d(x["date"]), ", ".join(_scene(s) for s in x["scenes"][:3]) + (" …" if len(x["scenes"]) > 3 else ""),
                  f"{x['chachoengsao_km2']:.0f}", f"{x['prachinburi_km2']:.0f}", f"{x['nakhonnayok_km2']:.0f}"] for x in dd]
        S.append(table(["วัน", "ฉากที่เผยแพร่ (ดาวเทียม เวลาท้องถิ่น)", "ฉะเชิงเทรา (ตร.กม.)", "ปราจีนบุรี (ตร.กม.)", "นครนายก (ตร.กม.)"], drows,
                       "พื้นที่น้ำท่วมจากผลิตภัณฑ์รายวันของ GISTDA (รวมทุกฉากที่เผยแพร่ในวันนั้น แนวครอบคลุมต่างกันตามดาวเทียม จึงเทียบข้ามวันตรง ๆ ไม่ได้ · ค่า 0 = ไม่มีฉากคลุมจังหวัดในวันนั้น ไม่ใช่ไม่ท่วม) · คลังไม่มีช่วง 16 ก.ย.–1 ต.ค. และมีถึง 17 ต.ค. เท่านั้น" + _miss_txt(dd)))
    S.append(prose(
        "<b>การตีความ:</b> ฉะเชิงเทรามีลักษณะปลายลุ่ม — รับน้ำจากพื้นที่เหนือน้ำกว้างมากผ่านแม่น้ำที่ผิวน้ำเกือบราบและตลิ่งต่ำ น้ำสูงสุดจึงมาถึงช้ากว่าต้นน้ำและลดลงช้า "
        "การแยกวิเคราะห์เป็นรายลุ่มและตามระดับความสูงจึงอธิบายได้ดีกว่าการแยกตามเส้นจังหวัด · "
        "<b>การประเมิน:</b> ยังสรุปไม่ได้ว่าน้ำทะเลหนุนมีส่วน เพราะสถานีท้ายน้ำต่ำกว่าตลิ่ง · แผนที่น้ำรายวันของ GISTDA ขาดช่วงน้ำสูงสุดและหลังวันที่เผยแพร่ล่าสุด จึงยืนยันไม่ได้ว่าทุ่งยังมีน้ำขังเท่าใด "
        f"(ระดับน้ำในแม่น้ำสูงกว่าตลิ่งไม่เท่ากับน้ำท่วมทั้งตำบล) · ความสูงพื้นดินมาจาก FABDEM ที่ปรับแบบต่อเนื่องด้วย DEM 5 ม. (ความไม่แน่นอนนอกหน้าต่างของ DEM 5 ม.: {_dem_band()})"
    ))
