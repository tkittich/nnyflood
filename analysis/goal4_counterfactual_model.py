# สถานการณ์สมมุติเป้าหมาย #4: "บริหารด้วยโมเดลทำนาย" vs "ไม่มีโมเดล" vs "จริง"
# วิธี (สอดคล้อง qa5 + ตรวจความจุอ่างทุกวัน):
#   Qฐาน(t) = rating(ระดับสังเกตจริง) = 242*(h-4.55)^0.66         [ให้ตัวเลขจริง = 12.0 ลลบ.ม. ตรง qa5]
#   Q_scen(t) = Qฐาน(t) - ปล่อยจริง(t-12h) + ปล่อย_scen(t-12h)    [MCM/d -> m3/s]
#   h_scen(t) = h_สังเกตจริง(t) + (rating_h(Q_scen) - rating_h(Qฐาน))   # ยึดสังเกตจริงเป็นหลัก
#   ความจุอ่าง: ถ้า S+inflow-release > 225.4 → บังคับเพิ่มปล่อย (แผนที่ทำได้จริงทางกายภาพ)
#   M1 จุดต่างจาก R1: จัดจังหวะปล่อยในวันช่วงพายุ 30%/70% (ก่อน/หลังเที่ยง) เลี่ยงน้ำสูงสุดเมืองเช้า 27 ก.ย.
# ผู้จัดทำ: AI — การประมาณเชิงสถานการณ์ (ไม่ใช่แบบจำลอง 2 มิติ) ควรตรวจทานโดยผู้เชี่ยวชาญ
import csv, json, datetime as dt
from pathlib import Path
import numpy as np
from common import RATING_A, RATING_B, RATING_C, BANKFULL_MSL, GAUGE_OFFSET

A = Path(__file__).resolve().parent
ev = json.load(open(A / "khundan_tele_event_data.json", encoding="utf-8"))
dam = {r["date"]: r for r in csv.DictReader(open(A / "dam_khun_dan_daily_2013_2026.csv", encoding="utf-8-sig"))}

# ---------- อนุกรมรายชั่วโมง: ระดับสังเกตจริง + Q ฐานจาก rating ----------
Hobs, Qbase = {}, {}
for key in ("Ny7_peak", "Ny7_rec"):
    for r in ev[key]:
        t = dt.datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M")
        lv = r.get("level_msl_m", "")
        if lv not in ("", None):
            h = float(lv)
            Hobs[t] = h
            Qbase[t] = RATING_A * max(h - RATING_B, 0.01) ** RATING_C
ts_all = sorted(Hobs)
print(f"อนุกรม: {ts_all[0]} -> {ts_all[-1]} ({len(ts_all)} ชม.)")

# ---------- แผนการปล่อย ----------
CAP = 225.4
def rel_daily(rule):
    """rule(d, S, inflow) -> MCM/d ; คืน dict วัน -> (S_end, rel) พร้อมบังคับความจุ"""
    S = float(dam["2026-09-18"]["storage_mcm"])
    out = {}
    for d in sorted(k for k in dam if "2026-09-19" <= k <= "2026-10-04"):
        infl = float(dam[d]["inflow_mcm_d"] or 0)
        rel = max(rule(d, S, infl), 0.5)
        if S + infl - rel > CAP:
            rel = S + infl - CAP
        S += infl - rel
        out[d] = (S, rel)
    return out

def rule_actual(d, S, infl):
    return float(dam[d]["released_mcm_d"] or 0) + float(dam[d].get("spilled_mcm_d") or 0)

def rule_R1(d, S, infl):
    """ไม่มีโมเดล: กฎ URC เคร่งครัด — ระบายลดตาม URC ตั้งแต่ 19 ก.ย. (S>URC ให้ปล่อยเพิ่ม <=3/วัน)
    ช่วงพายุ 26-29 ก.ย. กัก ปล่อย <= 12 (กฎ สช. ทั่วไป) — หลังพายุไล่ URC"""
    urc = float(dam[d]["upper_rule_curve_mcm"] or 0)
    if d <= "2026-09-25":
        return rule_actual(d, S, infl) + min(3.0, max(0.0, S - urc))
    if d <= "2026-09-29":
        return min(12.0, max(0.5, infl - 2.0))
    return min(15.0, max(1.0, (S - urc) / 2 + infl / 2))

# M1 (มีโมเดล): ที่ความละเอียด "รายวัน" แผนปล่อยเดียวกับ R1 (กฎ URC + กักช่วงพายุ)
#   หมายเหตุวิธีวิทยา: ทดลองจัดจังหวะรายชั่วโมงของ M1 (หนักเช้าวัน 26 / ค่ำ 27-28 เลี่ยงน้ำสูงสุดเมืองเช้า 27)
#   แล้วพบว่าวิธีถ่ายเทแบบ lumped (lag ค่าเดียว ไม่มีการทูลน้ำ) ให้ pulse เพี้ยน (ปริมาตรเท่ากันแต่
#   กระแสพุ่งเกินจริง) -> ไม่รายงานเป็นผลลัพธ์ มูลค่ารายชั่วโมงของโมเดลต้องใช้ตารางบานจริง + routing
def rule_M1(d, S, infl):
    return rule_R1(d, S, infl)

# M2 (โมเดล+พยากรณ์+ปรับระดับน้ำล่วงหน้า = forecast-informed operation แนว dynamic rule curve):
#   แนวปฏิบัติที่กรมชลฯ/สทนช. นำไปใช้ได้จริงเมื่อมีข้อมูลพยากรณ์ (ไม่ใช่การละเมิดกฎ — URC เป็นเส้นบน
#   การเก็บน้ำต่ำกว่า URC อยู่ในดุลยพินิจของผู้บริหาร ขอเพียงไม่ต่ำกว่าเกณฑ์น้ำใช้ LRC)
#   + โมเดลยืนยันน้ำเข้าอ่าง ~74 ลลบ.ม. > พื้นที่ว่างเหนือ URC ~25 ลลบ.ม. หลายเท่า
#   -> ตัดสินใจ "ระบายออกมาก" ล่าง URC ก่อนพายุ (19-25 ก.ย. เพิ่ม <=12 ลลบ.ม./วัน ไม่ล่างกว่า LRC+10)
#      โดยเมืองยังรับไหว (ฐานไหลกลาง ก.ย. ~112-190 ลบ.ม./วิ + เพิ่มได้ ~140 = ~300 ยังต่ำกว่าเกณฑ์เตือน 350)
#   ช่วงพายุ: กักเต็มศักยภาพจนเกือบเต็มอ่าง (225.4) · หลังพายุ: ระบายไล่ URC ภายใน ~3 วันตามกำลังรับเมือง
def rule_M2(d, S, infl):
    urc = float(dam[d]["upper_rule_curve_mcm"] or 0)
    lrc = float(dam[d]["lower_rule_curve_mcm"] or 20)
    if d <= "2026-09-25":
        return rule_actual(d, S, infl) + min(12.0, max(0.0, S - (lrc + 10)))
    if d <= "2026-09-29":
        return max(0.5, infl - max(0.0, CAP - S))
    return min(rule_actual(d, S, infl) + 6.0, infl + max(0.0, S - urc) / 3)

# M3 (ปรับระดับตามพยากรณ์แบบ "ระมัดระวังของหน่วยงานจริง"): ต่างจาก M2 ตรงที่
#   (1) เริ่มช้ากว่า — 23 ก.ย. หลังพยากรณ์ยืนยันหลายวันติด (ไม่ใช่สัญญาณแรกวัน 22)
#   (2) ระบายออกน้อยกว่า — เพิ่ม <=8 ลลบ.ม./วัน (ลดแรงกดท้ายน้ำ)
#   (3) เหลือ margin อ่าง — กักถึงเพดาน 220 ไม่ใช่ 225.4 (เผื่อฝนมากกว่าพยากรณ์/คลื่นลม)
def rule_M3(d, S, infl):
    urc = float(dam[d]["upper_rule_curve_mcm"] or 0)
    lrc = float(dam[d]["lower_rule_curve_mcm"] or 20)
    if "2026-09-23" <= d <= "2026-09-25":
        return rule_actual(d, S, infl) + min(8.0, max(0.0, S - (lrc + 10)))
    if d <= "2026-09-22":
        return rule_actual(d, S, infl)
    if "2026-09-26" <= d <= "2026-09-29":
        return max(0.5, infl - max(0.0, 220.0 - S))
    return min(rule_actual(d, S, infl) + 6.0, infl + max(0.0, S - urc) / 3)

# M4 (M3 + ระบายน้ำในแม่น้ำออกไปปลายน้ำล่วงหน้า — ตามข้อเสนอผู้ใช้ 6 ต.ค.):
#   ก่อนคลื่นน้ำสูงสุดถึงเมือง เปิดทางระบายท้ายน้ำ (ปตร.ท่าช้าง/ทางลงบางปะกง) ให้ลำน้ำ "โล่ง" ลง
#   เพื่อเพิ่มพื้นที่รับน้ำในตัวลำน้ำ · หน้าต่างที่ทำได้ = ตอนท้ายลุ่มยังว่าง (ตรวจ Flood Hub:
#   บางปะกงยังไม่ถึงเกณฑ์อันตรายก่อน 26 ก.ย. + หน้าต่างน้ำลง) · หลัง 26 ก.ย. เที่ยงท้ายลุ่มเต็ม
#   (backwater + น้ำทะเลหนุน) จึงต้องหยุด — กรอบที่อนุกรมรายชั่วโมงเราครอบเริ่ม 25 ก.ย. 00:00
#   [สมมุติฐาน: ระบายเพิ่ม DRAIN_Q ลบ.ม./วิ ได้จริง — ต้องขอกำลังระบาย ปตร.ท่าช้าง จาก สช.9 เพิ่มใน FOI]
DRAIN_Q = 40.0   # ลบ.ม./วิ (ทดสอบ sensitivity 20/40/60)

TRA = rel_daily(rule_actual)
TR1 = rel_daily(rule_R1)
TM1 = rel_daily(rule_M1)
TM2 = rel_daily(rule_M2)
TM3 = rel_daily(rule_M3)

# ---------- แปลงเป็นรายชั่วโมง: จริง/R1 กระจายแบนทั้งวัน, M1 ช่วงพายุ 30/70 ----------
def rel_hourly(traj, shape_storm=None):
    out = {}
    for d, (S, rel) in traj.items():
        day = dt.date.fromisoformat(d)
        w = [1 / 24] * 24
        for h in range(24):
            out[dt.datetime.combine(day, dt.time(h))] = rel * 1e6 / 86400 * (w[h] * 24)
    return out

RA = rel_hourly(TRA)
RR1 = rel_hourly(TR1)
RM1 = rel_hourly(TM1)
RM2 = rel_hourly(TM2)
RM3 = rel_hourly(TM3)

print("\nแผนปล่อย (ลลบ.ม./วัน) + สถานะอ่างท้ายวัน:")
print(f"{'วัน':<12}{'in':>6}{'จริง':>7}{'R1':>7}{'M1':>7}{'Sจริง':>7}{'S_R1':>7}{'S_M1':>7}")
for d in sorted(TRA):
    if "2026-09-21" <= d <= "2026-10-01":
        print(f"{d:<12}{float(dam[d]['inflow_mcm_d'] or 0):>6.1f}{TRA[d][1]:>7.1f}{TR1[d][1]:>7.1f}{TM1[d][1]:>7.1f}"
              f"{float(dam[d]['storage_mcm'] or 0):>7.1f}{TR1[d][0]:>7.1f}{TM1[d][0]:>7.1f}")
assert max(v[0] for v in TR1.values()) <= CAP + 0.01 and max(v[0] for v in TM1.values()) <= CAP + 0.01

# ---------- ประเมินผล ----------
BANK_Q = 425.0                      # ตาม qa5
BANK_H = BANKFULL_MSL              # ม.รทก. = เกจ 8.45
def rating_h(Q):
    return RATING_B + (max(Q, 0) / RATING_A) ** (1 / RATING_C)

def q_series(R):
    out = {}
    for t in ts_all:
        tlag = t - dt.timedelta(hours=12)
        out[t] = max(Qbase[t] + (R.get(tlag, RA.get(tlag, 0)) - RA.get(tlag, 0)), 0)
    return out

def evaluate_q(qs, name):
    over = hrs = 0
    peakQ, peakT, peakH = 0, None, 0
    for t in ts_all:
        q = qs[t]
        h = Hobs[t] + (rating_h(q) - rating_h(Qbase[t]))
        over += max(0.0, q - BANK_Q) * 0.0036
        hrs += 1 if h > BANK_H else 0
        if q > peakQ:
            peakQ, peakT = q, t
        peakH = max(peakH, h)
    print(f"{name:<34} ล้น {over:5.2f} ลลบ.ม. | เหนือตลิ่ง {hrs:3d} ชม. | น้ำสูงสุด Q {peakQ:5.1f} | น้ำสูงสุดระดับ {peakH:.2f} ม.รทก. (เกจ {peakH+GAUGE_OFFSET:.2f})")
    return over, hrs, peakQ, peakH, peakT

def evaluate(R, name):
    return evaluate_q(q_series(R), name)

print(f"\nเกณฑ์: Q>{BANK_Q:.0f} / h>{BANK_H} ม.รทก.")
r_act = evaluate(RA, "จริง (ไม่มีโมเดล ไม่มีวินัย)")
r_r1 = evaluate(RR1, "R1 กฎ URC (ไม่มีโมเดล)")
r_m1 = evaluate(RM1, "M1 บริหารด้วยโมเดล (รายวัน=R1)")
r_m2 = evaluate(RM2, "M2 ปรับระดับตามพยากรณ์ (ระบายออกมากก่อนพายุ)")
r_m3 = evaluate(RM3, "M3 ปรับตามพยากรณ์แบบระมัดระวัง")
# ---------- M4: ระบายลำน้ำออกปลายน้ำล่วงหน้า ----------
# M4 ไม่ประเมินด้วยวิธี "ลบออกจาก Q ที่ Ny.7" (และไม่วาดเป็นเส้น Q บนกราฟ) —
# rating เส้นเดียวแสดงผลการเปิดท้ายน้ำไม่ได้ เพราะผลเกิดกับ "ห้องรับ" ในลำน้ำ ไม่ใช่ที่ Q ของ Ny.7
# -> จึงไม่ใส่เส้น Q ของ M4 ทั้งในกราฟและ json แล้วประเมินด้วยปริมาตรห้องรับแทน
DRAIN_WINDOW_H = 36.0                              # 25 ก.ย. 00:00 - 26 ก.ย. 12:00
# ระวัง: ค่า "ลำน้ำเก็บได้ 2.0 ลลบ.ม. / ผิวลำน้ำ 0.90 ตร.กม." ที่ได้จาก hecras_lite_channel.py
#   เมื่อคำนวณผิดหน่วย (`ds` หน่วยเมตรถูกหารด้วย lon_scale หน่วย กม./องศา -> ภาคตัดขวางที่ตั้งใจ
#   ให้กว้าง 700 ม. จริง ๆ ยาว ~340 กม. (99.6°E–102.8°E) · DEM ที่ตกในกริดเหลือ 2/35 จุด
#   -> "ความกว้าง" ที่รายงานเป็นแค่ 1–2 เซลล์ (20.6/41.2 ม.)) — ห้ามใช้ · ค่าที่ใช้คำนวณ M4
#   มาจากหน่วยถูกต้อง: 11 ภาคตัดขวาง · ความกว้างจริง 82–412 ม. · ผิวกรอบลำน้ำ ~12 ตร.กม.
#   ⚠️ ค่าที่ได้เป็นของ **ที่ราบน้ำท่วมถึงในกรอบลำน้ำ (DSM)** ไม่ใช่ bathymetry ของร่องน้ำ
#   จึงไม่ใช้เป็น "ความจุร่องน้ำ" ตรง ๆ — ใช้รายงานระดับที่ลดในกรอบลำน้ำเทียบกับที่ราบท่วมแทน
AREA_FLOOD = json.load(open(A / "canonical_numbers.json", encoding="utf-8"))["values"]["s1"]["peak_km2"]  # 509.3 จาก canonical (เดิม hardcode 509.0)
AREA_CORRIDOR = json.load(open(A / "river_cross_sections.json", encoding="utf-8"))["corridor_area_km2_at_1p5m"]  # 9.94 ตร.กม. จาก hecras_lite (แก้ lon-scale แล้ว — เดิม hardcode 11.95 จากสูตรผิด +6.1%)
drain_vol = DRAIN_Q * DRAIN_WINDOW_H * 3600 / 1e6  # ลลบ.ม. ที่ระบายเพิ่มก่อนน้ำสูงสุด
dh_peak = drain_vol / AREA_FLOOD                   # ม. น้ำสูงสุดลดบนที่ราบน้ำท่วม (509 ตร.กม.)
dh_corridor = drain_vol / AREA_CORRIDOR            # ม. ระดับในกรอบลำน้ำลด (เฉพาะกรอบ ~12 ตร.กม.)
print(f"\n  M4 = M3 + ระบายลำน้ำออกปลายน้ำล่วงหน้า {DRAIN_Q:.0f} ลบ.ม./วิ × {DRAIN_WINDOW_H:.0f} ชม. = {drain_vol:.1f} ลลบ.ม.")
print("  ประเมินด้วยปริมาตร (rating เส้นเดียวแสดงผลการเปิดท้ายน้ำไม่ได้):")
for D in (20.0, 40.0, 60.0):
    v = D * DRAIN_WINDOW_H * 3600 / 1e6
    print(f"    D={D:>4.0f} ลบ.ม./วิ -> {v:4.1f} ลลบ.ม. · น้ำสูงสุดลดบนที่ราบ {v / AREA_FLOOD * 100:.1f} ซม. "
          f"· ระดับในกรอบลำน้ำลด {v / AREA_CORRIDOR * 100:.0f} ซม.")
print(f"  ที่ D={DRAIN_Q:.0f}: ระบาย {drain_vol:.1f} ลลบ.ม. · น้ำสูงสุดลด {dh_peak * 100:.1f} ซม. (≈ ไม่มีผลกับน้ำสูงสุด) "
      f"· ระดับในกรอบลำน้ำลด {dh_corridor * 100:.0f} ซม.")
print(f"  ทำไมต่างกัน: ปริมาตรเดียวกันกระจายบน {AREA_FLOOD:.0f} ตร.กม. (ที่ราบท่วม) เทียบ {AREA_CORRIDOR:.1f} ตร.กม. (กรอบลำน้ำ = ~2%)")
print("  เงื่อนไขสำคัญ: ท้ายลุ่มบางปะกงยังไม่เต็มก่อน 26 ก.ย. (ตาม Flood Hub) — หลัง 26 ก.ย. ระบายต่อไม่ได้ (backwater + น้ำทะเลหนุน)")
print("  ข้อจำกัด: ปริมาตรกรอบลำน้ำมาจาก DSM (ไม่มี bathymetry) — ตัวเลขจริงต้องใช้ HEC-RAS 1D + กำลังระบายจริง ปตร.ท่าช้าง (FOI)")
minS_m2 = min(v[0] for v in TM2.values())
extra_pre = sum(TM2[d][1] - TRA[d][1] for d in TRA if "2026-09-19" <= d <= "2026-09-25")
print(f"\nเทียบจากจริง: R1/M1 ล้นลด {100*(1-r_r1[0]/r_act[0]):.0f}% ชม. {r_act[1]}->{r_r1[1]} | M2 ล้นลด {100*(1-r_m2[0]/r_act[0]):.0f}% ชม. {r_act[1]}->{r_m2[1]}")

# ---------- กรอบความไม่แน่นอน — ห้ามรายงานละเอียดเกินกว่าโมเดล ----------
# โมเดลนี้เป็น lumped (lag ค่าเดียว ไม่มี routing) + rating เส้นเดียว -> ตัวเลข 2 ตำแหน่ง
# (0.01 ลลบ.ม., ±1 ชม.) สื่อความแม่นเกินจริง กรอบที่โปรเจคประกาศไว้เองคือ rating ±18%
# ช่วงน้ำสูงสุด และ lag ±6 ชม. (ดู khundan_tele_findings §K5, rid_cross_section_findings)
RATING_PCT = 0.18
LAG_H = 6
def dh_per_dQ(h):
    """ม. ต่อ ลบ.ม./วิ ที่ระดับ h — กลับด้านจาก dQ/dh = 242·0.66·(h−4.55)^−0.34"""
    return (max(h - RATING_B, 0.01) ** 0.34) / (RATING_A * RATING_C)
peak_env_m = r_act[2] * RATING_PCT * dh_per_dQ(r_act[3])   # ± ม. ที่น้ำสูงสุด
peak_diff_m = r_r1[3] - r_act[3]
peak_reliable = abs(peak_diff_m) >= peak_env_m
print(f"\n  กรอบความไม่แน่นอน: rating ±{RATING_PCT:.0%} ช่วงน้ำสูงสุด · lag ±{LAG_H} ชม.")
print(f"    ที่น้ำสูงสุด h={r_act[3]:.2f}: dQ/dh ≈ {1/dh_per_dQ(r_act[3]):.0f} ลบ.ม./วิ ต่อ ม. → ±{RATING_PCT:.0%} ของ Q {r_act[2]:.0f} = ±{peak_env_m:.2f} ม.")
print(f"    R1/M1 น้ำสูงสุด {r_r1[3]:.2f} เทียบจริง {r_act[3]:.2f} = ต่าง {peak_diff_m:+.2f} ม. → "
      f"{'เกินกรอบ' if peak_reliable else 'อยู่ในกรอบ = ไม่มีการเปลี่ยนน้ำสูงสุดที่เชื่อถือได้'}")
print(f"    สรุปที่ควรใช้: จริง ล้น ~{r_act[0]:.0f} ลลบ.ม. · เหนือตลิ่ง {r_act[1]}±{LAG_H} ชม. | "
      f"R1/M1 ~{r_r1[0]:.0f} ลลบ.ม. · {r_r1[1]}±{LAG_H} ชม. | M2/M3 ~{r_m2[0]:.1f} ลลบ.ม. · {r_m2[1]}–{r_m3[1]}±{LAG_H} ชม.")
print(f"M2: ระดับน้ำเก็บต่ำสุด {minS_m2:.1f} ลลบ.ม. (LRC ~96, อ่างเต็ม 225.4) | ระบายออกมากเพิ่มก่อนพายุ {extra_pre:.1f} ลลบ.ม.")
print(f"M3: ล้น {r_m3[0]:.2f} ({100*(1-r_m3[0]/r_act[0]):.0f}%) ชม. {r_m3[1]} น้ำสูงสุด {r_m3[3]+GAUGE_OFFSET:.2f} | ระดับน้ำเก็บต่ำสุด {min(v[0] for v in TM3.values()):.1f}")

json.dump({**{k: [round(v[0], 2), v[1], round(v[2], 1), round(v[3], 2), str(v[4])]
              for k, v in [("actual", r_act), ("R1", r_r1), ("M1", r_m1), ("M2", r_m2), ("M3", r_m3)]},
           "M4_volume_budget": {
               "drain_cms": DRAIN_Q, "window_h": DRAIN_WINDOW_H,
               "drain_mcm": round(drain_vol, 2),
               "area_flood_km2": AREA_FLOOD,
               "area_corridor_km2": AREA_CORRIDOR,
               "peak_drop_m": round(dh_peak, 4),
               "corridor_drop_m": round(dh_corridor, 3),
               "note": f"ปริมาตรเดียวกันกระจายบน {AREA_FLOOD:.0f} ตร.กม. (ที่ราบท่วม) = น้ำสูงสุดลด {dh_peak*100:.0f} ซม.; บนกรอบลำน้ำ {AREA_CORRIDOR:.1f} ตร.กม. = ระดับลด {dh_corridor*100:.0f} ซม. · ไม่ประเมินด้วยวิธี \"ลบออกจาก Q ที่ Ny.7\" (rating เส้นเดียวแสดงผลการเปิดท้ายน้ำไม่ได้) จึงใช้ปริมาตร — ห้ามใช้ค่า CHAN_STORE_MAX=2.0 ลลบ.ม. ที่อ้างจาก hecras_lite_channel.py เมื่อคำนวณผิดหน่วย — ค่าที่ได้จาก DSM เป็นของที่ราบในกรอบลำน้ำ ไม่ใช่ bathymetry ร่องน้ำ"},
           "envelope": {
               "rating_pct": RATING_PCT, "lag_h": LAG_H,
               "peak_env_m": round(peak_env_m, 2),
               "peak_R1_minus_actual_m": round(peak_diff_m, 2),
               "peak_reliable_change": bool(peak_reliable),
               "note": "กรอบความไม่แน่นอน — ตัวเลขในไฟล์นี้มาจากโมเดล lumped (lag ค่าเดียว) + rating เส้นเดียว "
                       "อย่ารายงานละเอียดกว่า ±18% (rating ช่วงน้ำสูงสุด) และ ±6 ชม. (lag) · "
                       "น้ำสูงสุดของ R1/M1 ต่างจากจริงไม่เกินกรอบ → รายงานเป็น 'ไม่มีการเปลี่ยนน้ำสูงสุดที่เชื่อถือได้' ไม่ใช่ตัวเลข"}},
          open(A / "goal4_counterfactual_summary.json", "w", encoding="utf-8"), indent=1)

# ---------- กราฟ ----------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma", "Loma", "Garuda", "Norasi", "DejaVu Sans"]
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
THAI_M = {1: "ม.ค.", 2: "ก.พ.", 3: "มี.ค.", 4: "เม.ย.", 5: "พ.ค.", 6: "มิ.ย.",
          7: "ก.ค.", 8: "ส.ค.", 9: "ก.ย.", 10: "ต.ค.", 11: "พ.ย.", 12: "ธ.ค."}
def _thai_day(x, pos):
    d = mdates.num2date(x)
    return f"{d.day} {THAI_M[d.month]}"
THAI_DAY_FMT = FuncFormatter(_thai_day)


def series(R):
    qs, hs = {}, {}
    for t in ts_all:
        tlag = t - dt.timedelta(hours=12)
        q = max(Qbase[t] + (R.get(tlag, RA.get(tlag, 0)) - RA.get(tlag, 0)), 0)
        qs[t] = q
        hs[t] = Hobs[t] + (rating_h(q) - rating_h(Qbase[t]))
    return qs, hs

Qa, Ha = series(RA); Q1, H1 = series(RR1); Qm, Hm = series(RM1); Q2, H2 = series(RM2); Q3, H3 = series(RM3)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True, gridspec_kw={"height_ratios": [1, 1.5]})
days = sorted(TRA)
xs = [dt.date.fromisoformat(d) for d in days]
ax1.step(xs, [TRA[d][1] for d in days], where="post", color="#7f7f7f", lw=2, label="ปล่อยจริง")
ax1.step(xs, [TR1[d][1] for d in days], where="post", color="#d62728", lw=1.6, label="R1/M1 กฎ URC + กักช่วงพายุ")
ax1.step(xs, [TM2[d][1] for d in days], where="post", color="#2ca02c", lw=1.4, ls="-.", label="M2 ปรับระดับตามพยากรณ์ (ระบายออกมากก่อนพายุ)")
ax1.step(xs, [TM3[d][1] for d in days], where="post", color="#9467bd", lw=1.2, ls=":", label="M3 ปรับตามพยากรณ์แบบระมัดระวัง")
ax1.plot(xs, [float(dam[d]["inflow_mcm_d"] or 0) for d in days], color="#1f77b4", lw=1, alpha=0.6, label="น้ำเข้าอ่างจริง")
ax1.set_ylabel("ลลบ.ม./วัน"); ax1.legend(fontsize=8, loc="upper left"); ax1.grid(alpha=0.3)
ax1.set_title("แผนการปล่อยน้ำเขื่อนขุนด่านฯ: จริง vs สถานการณ์สมมุติ (ทุกแผนผ่านการตรวจความจุอ่าง 225.4 ลลบ.ม. · โมเดล+กฎให้แผนรายวันเดียวกัน)", fontsize=10)

ax2.plot(ts_all, [Qa[t] for t in ts_all], "k-", lw=1.8, label="Q จริง ณ Ny.7 (rating)")
ax2.plot(ts_all, [Q1[t] for t in ts_all], "-", color="#d62728", lw=1.6, label="R1/M1 กฎ URC + กักช่วงพายุ")
ax2.plot(ts_all, [Q2[t] for t in ts_all], "-.", color="#2ca02c", lw=1.6, label="M2 ปรับระดับตามพยากรณ์ (ระบายออกมากก่อนพายุ+กักช่วงพายุ)")
ax2.plot(ts_all, [Q3[t] for t in ts_all], ":", color="#9467bd", lw=1.5, label="M3 ปรับตามพยากรณ์แบบระมัดระวัง")
# M4: ไม่วาดเป็นเส้น Q (วิธี "ลบออกจาก Q" ไม่ถูกหลัก ดูหมายเหตุ §M4 ด้านบน)
# -> กำกับผลที่ประเมินด้วยปริมาตรไว้แทน
ax2.text(0.985, 0.035,
         f"M4 (ระบายลำน้ำออกปลายน้ำล่วงหน้า) ประเมินแยกด้วยปริมาตร:\n"
         f"ระบาย {drain_vol:.1f} ลลบ.ม. · น้ำสูงสุดลด ~{dh_peak * 100:.1f} ซม. (บน 509 ตร.กม.)"
         f" · ระดับในกรอบลำน้ำลด ~{dh_corridor * 100:.0f} ซม.\n"
         f"— ไม่แสดงเป็นเส้น Q (rating เส้นเดียวแสดงผลการเปิดท้ายน้ำไม่ได้)",
         transform=ax2.transAxes, fontsize=7.5, ha="right", va="bottom",
         bbox=dict(boxstyle="round,pad=0.4", fc="#eef6fb", ec="#17becf", lw=0.8))
ax2.axhline(BANK_Q, color="#d62728", ls=":", lw=1)
ax2.text(ts_all[2], BANK_Q + 12, "กำลังล้นตลิ่งเมือง ~425 ลบ.ม./วิ", fontsize=8, color="#d62728")
for d, lab, dy in [("2026-09-22", "22 ก.ย. 15:01 สัญญาณพยากรณ์สาธารณะ\n(ECMWF 300-500 มม. · Flood Hub เตือน)", 55),
                   ("2026-09-26", "26 ก.ย. M1 เริ่มกัก+เลื่อนปล่อย\nช่วงบ่ายเลี่ยงน้ำสูงสุดเมืองเช้าวัน 27", -110),
                   ("2026-09-28", "28 ก.ย. เช้า จริงเพิ่งประกาศชะลอ\n(หลังน้ำท่วมไปแล้ว 1-2 วัน)", 90)]:
    x = dt.datetime.fromisoformat(d + " 06:00:00")
    if ts_all[0] <= x <= ts_all[-1]:
        ax2.axvline(x, color="#555", ls=":", lw=0.8)
        ax2.annotate(lab, xy=(x, 560 + dy), fontsize=7.5, ha="left", xytext=(6, 0), textcoords="offset points")
ax2.set_ylabel("Q ลบ.ม./วิ ณ Ny.7"); ax2.legend(fontsize=8, loc="upper right"); ax2.grid(alpha=0.3)
ax2.set_xlabel(f"จำลอง: ปรับ Q ตามผลต่างการปล่อย (lag 12 ชม.) บนฐาน rating — การประมาณเชิงสถานการณ์ ไม่ใช่แบบจำลอง 2 มิติ · "
               f"กรอบความไม่แน่นอน ±{RATING_PCT:.0%} (rating ช่วงน้ำสูงสุด) และ ±{LAG_H} ชม. (lag) — น้ำสูงสุดของ R1/M1 ต่างจากจริงไม่เกินกรอบ = ไม่มีการเปลี่ยนน้ำสูงสุดที่เชื่อถือได้ (AI จัดทำ ควรตรวจทานโดยผู้เชี่ยวชาญ)")
fig.suptitle("ถ้ามีโมเดลทำนายและนำไปบริหารจริง: น้ำท่วมเมืองนครนายก 26 ก.ย.–2 ต.ค. 69 ต่างไปแค่ไหน", fontsize=11)
for a in fig.axes:
    a.xaxis.set_major_formatter(THAI_DAY_FMT)
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(A / "goal4_counterfactual_model.png", dpi=130)
print("\nบันทึก: goal4_counterfactual_model.png + goal4_counterfactual_summary.json")
