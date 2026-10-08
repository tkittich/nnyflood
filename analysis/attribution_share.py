# สัดส่วนน้ำ "เขื่อน vs ฝน/ลุ่มกลาง" ต่อปริมาตรที่ไหลผ่าน Ny.7 — สคริปต์คำนวณหลัก
# คำนวณ 2 หน้าต่าง: P1 = 26 ก.ย. 12:00–27 ก.ย. 12:00 (เริ่มท่วม) · P2 = 27 ก.ย. 12:00–29 ก.ย. 00:00 (น้ำขัง)
# ปริมาตรรวม 2 แบบ: (ก) Q วัดจริงจาก khundan-tele [ตัวหลัก] (ข) Q จาก rating curve [ตัวเปรียบเทียบ]
#   ทั้งคู่อินทิเกรตที่ความละเอียดข้อมูลจริง 15 นาที (ผลรวมไรมันน์ q×900 วิ — รุ่นก่อน 8 ต.ค. 69
#   ก้าวทีละ 1 ชม. ทั้งที่ป้ายบอก 15 นาที = หลุดพีคครึ่งชั่วโมง; ผลรีวิว GLM GL-01)
# ปริมาตรเขื่อน: อัตราปล่อยรายวัน (ลลบ.ม./วัน) เลื่อน lag 12 ชม. (ความละเอียดรายวัน = ข้อจำกัดเดิม)
#   + ตารางความอ่อนไหว lag 6/9/12/18 ชม. (lag วัดได้จริง 9–18 ชม. — ตารางแสดงว่า P1 แกว่งแค่ไหน,
#     GL-14; P2 แข็งแรง)
# ผล: analysis/attribution_share.json — อ้างอิงโดย khundan_tele_findings.md K3 + รายงานวิชาการ §4B
import csv, json, datetime as dt
from pathlib import Path
import numpy as np
from common import RATING_A, RATING_B, RATING_C

BASE = Path(__file__).resolve().parent
D16 = BASE.parent / "data" / "16_training_data"
P1 = (dt.datetime(2026, 9, 26, 12), dt.datetime(2026, 9, 27, 12))
P2 = (dt.datetime(2026, 9, 27, 12), dt.datetime(2026, 9, 29, 0))
WINDOWS = (("P1_onset", P1), ("P2_sustained", P2))
STEP_MIN = 15          # ความละเอียดข้อมูลโทรมาตร — อินทิเกรตที่นิยามนี้ (ไม่ใช่รายชั่วโมง)
LAG_H = 12             # lag กลางที่รายงานใช้ (พิสัยวัดได้ 9–18 ชม. → ดู lag_sensitivity)


def load_q():
    """Q วัดจริง 15 นาที + Q จาก rating (ระดับ 15 นาที → ม.รทก. → rating)"""
    q_meas, q_rating = {}, {}
    for r in csv.reader(open(D16 / "khundan_15min_Ny7_Jun-Oct2026.csv", encoding="utf-8")):
        if r[0] == "datetime" or not r[0]:
            continue
        t = dt.datetime.fromisoformat(r[0])
        if r[2] not in ("", "-"):
            q_meas[t] = float(r[2])
        if r[1] not in ("", "-"):
            h = float(r[1])             # ไฟล์นี้เป็น ม.รทก. อยู่แล้ว
            q_rating[t] = RATING_A * (h - RATING_B) ** RATING_C if h > RATING_B else 0.0
    return q_meas, q_rating


def load_releases():
    rel = {}
    for r in csv.DictReader(open(BASE / "dam_khun_dan_daily_2013_2026.csv", encoding="utf-8-sig")):
        if r["released_mcm_d"]:
            rel[dt.date.fromisoformat(r["date"])] = float(r["released_mcm_d"])
    return rel


def integrate(series, w, step_min=STEP_MIN):
    """อินทิกราลไรมันน์ q_cms × step นาที → ล้าน ลบ.ม. · ช่องขาด = อัตราเฉลี่ยเพื่อนบ้าน"""
    sec = step_min * 60
    ts = sorted(series)
    total, n = 0.0, 0
    t = w[0]
    while t < w[1]:
        if t in series:
            v = series[t]
        else:
            prev = max((s for s in ts if s <= t), default=None)
            nxt = min((s for s in ts if s > t), default=None)
            v = np.mean([x for x in (series.get(prev), series.get(nxt)) if x is not None])
        total += v * sec / 1e6
        n += 1
        t += dt.timedelta(minutes=step_min)
    return total, n


def dam_mcm(w, rel, lag_h=LAG_H):
    """ปล่อยรายวัน (ลลบ.ม./วัน) เลื่อน lag → อัตราเฉลี่ยรายชั่วโมง (ลลบ.ม./ชม. = /24)"""
    total, n = 0.0, 0
    t = w[0]
    while t < w[1]:
        day = (t - dt.timedelta(hours=lag_h)).date()
        if day in rel:
            total += rel[day] / 24
            n += 1
        t += dt.timedelta(hours=1)
    return total, n


def compute(rel, q_meas, q_rating, lag_h=LAG_H):
    out = {}
    for name, w in WINDOWS:
        meas, _ = integrate(q_meas, w)
        rat, _ = integrate(q_rating, w)
        dam, n = dam_mcm(w, rel, lag_h)
        out[name] = {
            "window": [w[0].isoformat(), w[1].isoformat()],
            "total_measured_mcm": round(meas, 1),
            "total_rating_mcm": round(rat, 1),
            "dam_release_mcm": round(dam, 1),
            "dam_hours_counted": n,
            "dam_share_measured_pct": round(dam / meas * 100, 1),
            "dam_share_rating_pct": round(dam / rat * 100, 1),
        }
        print(f"[lag {lag_h:2d}ชม.] {name}: รวม(Q วัดจริง) {meas:.1f} · (rating) {rat:.1f} ลลบ.ม. · เขื่อน {dam:.1f} ลลบ.ม. "
              f"({n} ชม.) → สัดส่วนเขื่อน {dam/meas*100:.0f}% (วัดจริง) / {dam/rat*100:.0f}% (rating)")
    return out


def main():
    q_meas, q_rating = load_q()
    rel = load_releases()

    out = {"method": "อินทิกราลข้อมูล 15 นาทีของ Q ที่ Ny.7 (ผลรวมไรมันน์ q×900 วิ) · "
                     "เขื่อน = ปล่อยรายวัน×lag 12 ชม. (ไม่รวมการอุปโภค/ท่อส่งน้ำ; ความอ่อนไหวต่อ lag ดูคีย์ lag_sensitivity) · "
                     "หน้าต่าง P1 = 26 ก.ย. 12:00–27 ก.ย. 12:00 · P2 = 27 ก.ย. 12:00–29 ก.ย. 00:00",
           "windows": compute(rel, q_meas, q_rating)}

    # ---- ความอ่อนไหวต่อ lag (lag วัดได้จริง 9–18 ชม.; ค่ากลาง 12 ชม.) ----
    sens = {}
    for lag in (6, 9, 12, 18):
        w = compute(rel, q_meas, q_rating, lag)
        sens[str(lag)] = {k: w[k]["dam_share_measured_pct"] for k in ("P1_onset", "P2_sustained")}
    out["lag_sensitivity"] = {"unit": "dam_share_measured_pct", "note": "lag วัดจริง 9–18 ชม. — "
                              "สัดส่วน P1 แกว่งตาม lag เพราะปล่อยรายวันถูกตัดที่ขอบหน้าต่าง 27 ก.ย. 12:00; P2 แข็งแรง",
                              "pct_by_lag_h": sens}

    json.dump(out, open(BASE / "attribution_share.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("saved:", BASE / "attribution_share.json")


if __name__ == "__main__":
    main()
