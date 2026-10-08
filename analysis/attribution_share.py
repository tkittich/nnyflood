# สัดส่วนน้ำ "เขื่อน vs ฝน/ลุ่มกลาง" ต่อปริมาตรที่ไหลผ่าน Ny.7 — สคริปต์คำนวณหลัก
# คำนวณ 2 หน้าต่าง: P1 = 26 ก.ย. 12:00–27 ก.ย. 12:00 (เริ่มท่วม) · P2 = 27 ก.ย. 12:00–29 ก.ย. 00:00 (น้ำขัง)
# ปริมาตรรวม 2 แบบ: (ก) Q วัดจริงจาก khundan-tele [ตัวหลัก] (ข) Q จาก rating curve [ตัวเปรียบเทียบ]
#   ทั้งคู่อินทิเกรตจากข้อมูล 15 นาที (ไม่ใช่ค่าเฉลี่ยรายชั่วโมง — ซึ่งฟันน้ำสูงสุดหลุด ~20% บนไฮโดรกราฟคม)
# ปริมาตรเขื่อน: อัตราปล่อยรายวัน (ลลบ.ม./วัน) เลื่อน lag 12 ชม. (ความละเอียดรายวัน = ข้อจำกัดเดิม)
# ผล: analysis/attribution_share.json — อ้างอิงโดย khundan_tele_findings.md K3 + รายงานวิชาการ §4B
import csv, json, datetime as dt
from pathlib import Path
import numpy as np
from common import RATING_A, RATING_B, RATING_C

BASE = Path(__file__).resolve().parent
D16 = BASE.parent / "data" / "16_training_data"
P1 = (dt.datetime(2026, 9, 26, 12), dt.datetime(2026, 9, 27, 12))
P2 = (dt.datetime(2026, 9, 27, 12), dt.datetime(2026, 9, 29, 0))

# ---------- Q วัดจริง 15 นาที (khundan-tele) ----------
q_meas = {}
for r in csv.reader(open(D16 / "khundan_15min_Ny7_Jun-Oct2026.csv", encoding="utf-8")):
    if r[0] == "datetime" or not r[0] or r[2] in ("", "-"):
        continue
    q_meas[dt.datetime.fromisoformat(r[0])] = float(r[2])

# ---------- Q จาก rating: ระดับ 15 นาที → เกจ−1.59 → rating ----------
lvl = {}
for r in csv.reader(open(D16 / "khundan_15min_Ny7_Jun-Oct2026.csv", encoding="utf-8")):
    if r[0] == "datetime" or not r[0] or r[1] in ("", "-"):
        continue
    h = float(r[1])                     # ไฟล์นี้เป็น ม.รทก. อยู่แล้ว
    lvl[dt.datetime.fromisoformat(r[0])] = RATING_A * (h - RATING_B) ** RATING_C if h > RATING_B else 0.0
q_rating = lvl

# ---------- ปล่อยรายวัน (ลลบ.ม./วัน) → อัตรารายชั่วโมง เลื่อน lag 12 ชม. ----------
rel = {}
for r in csv.DictReader(open(BASE / "dam_khun_dan_daily_2013_2026.csv", encoding="utf-8-sig")):
    if r["released_mcm_d"]:
        rel[dt.date.fromisoformat(r["date"])] = float(r["released_mcm_d"])

def integrate(series, w):
    """อินทิกราลรายชั่วโมง (q_cms × 1 ชม.) → ล้าน ลบ.ม. · ช่องขาด = อัตราเฉลี่ยเพื่อนบ้าน"""
    ts = sorted(series)
    vals = []
    t = w[0]
    while t < w[1]:
        if t in series:
            v = series[t]
        else:
            prev = max((s for s in ts if s <= t), default=None)
            nxt = min((s for s in ts if s > t), default=None)
            v = np.mean([x for x in (series.get(prev), series.get(nxt)) if x is not None])
        vals.append((t, v))
        t += dt.timedelta(hours=1)
    total = sum(v for _, v in vals) * 3600 / 1e6
    return total, vals

def dam_mcm(w):
    """ปล่อยรายวัน (ลลบ.ม./วัน) เลื่อน lag 12 ชม. → อัตรารายชั่วโมง (ลลบ.ม./ชม. = /24)"""
    total, n = 0.0, 0
    t = w[0]
    while t < w[1]:
        day = (t - dt.timedelta(hours=12)).date()
        if day in rel:
            total += rel[day] / 24
            n += 1
        t += dt.timedelta(hours=1)
    return total, n

out = {"method": "อินทิกราลข้อมูล 15 นาทีของ Q ที่ Ny.7 · เขื่อน = ปล่อยรายวัน×lag 12 ชม. (ไม่รวมการอุปโภค/ท่อส่งน้ำ) · "
                 "หน้าต่าง P1 = 26 ก.ย. 12:00–27 ก.ย. 12:00 · P2 = 27 ก.ย. 12:00–29 ก.ย. 00:00",
       "windows": {}}
for name, w in (("P1_onset", P1), ("P2_sustained", P2)):
    meas, _ = integrate(q_meas, w)
    rat, _ = integrate(q_rating, w)
    dam, n = dam_mcm(w)
    out["windows"][name] = {
        "window": [w[0].isoformat(), w[1].isoformat()],
        "total_measured_mcm": round(meas, 1),
        "total_rating_mcm": round(rat, 1),
        "dam_release_mcm": round(dam, 1),
        "dam_hours_counted": n,
        "dam_share_measured_pct": round(dam / meas * 100, 1),
        "dam_share_rating_pct": round(dam / rat * 100, 1),
    }
    print(f"{name}: รวม(Q วัดจริง) {meas:.1f} · (rating) {rat:.1f} ลลบ.ม. · เขื่อน {dam:.1f} ลลบ.ม. "
          f"({n} ชม.) → สัดส่วนเขื่อน {dam/meas*100:.0f}% (วัดจริง) / {dam/rat*100:.0f}% (rating)")

json.dump(out, open(BASE / "attribution_share.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("saved:", BASE / "attribution_share.json")
