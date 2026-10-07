"""หน้าต่างฝนสะสม n วัน สำหรับโมเดลทำนายระดับน้ำ Ny.7 — รวมตรรกะไว้ไฟล์เดียว

ระวังการเขียนหน้าต่างฝนผิด 2 ระดับ (ถ้าเขียน `roll()` เอง):

  1) ถ้าคืน "ผลรวมสะสม" (cumsum เลื่อน n ช่อง) จะไม่ใช่ "หน้าต่าง n วัน"
     -> โตแบบ quadratic: roll([0,1,2,3,4,5], 3) = [0,1,3,6,10,15] (ควรเป็น [0,1,3,6,9,12])
     -> corr(R24, R72) = 0.9996 -> สามฟีเจอร์เป็นตัวเดียวกันจริง ๆ ไม่ใช่ 3 ตัว
  2) ถ้าคำนวณบนกริด "รายชั่วโมง" ที่ฝนรายวันถูกทำซ้ำ 24 ช่อง
     -> ช่อง "เมื่อวาน" (t-24) มีฝนของ "วันนี้" ปนอยู่ 23/24 ชั่วโมง
     -> ข้อมูลอนาคตรั่วเข้าโมเดลที่อ้างว่าเป็น forecast

วิธีที่ถูก: รวมบนอนุกรม "รายวัน" และรวมเฉพาะวันก่อนหน้าวันปัจจุบัน (D-n .. D-1)
ค่าที่ได้จึงเป็น "ฝนสะสม n วัน ถึงสิ้นสุดเมื่อวาน"

ใช้ร่วมกันโดย: goal4_model_v1.py · goal4_model_rainfcst_test.py · goal4_model_moisture_test.py
"""
import numpy as np


def day_window(daily, days):
    """ผลรวม `days` วัน สิ้นสุดเมื่อวาน — ดัชนี i ได้ผลรวมของวัน i-days .. i-1 (ไม่รวมวัน i)

    รับ `daily` = อนุกรมรายวัน (np.array ของฝน มม./วัน) เรียงตามเวลา
    คืน array ยาวเท่ากัน โดยช่องที่ยังไม่มีวันก่อนหน้าเต็มจะได้ผลรวมเท่าที่มี
    """
    c = np.concatenate([[0.0], np.cumsum(daily)])
    return np.array([c[i] - c[max(0, i - days)] for i in range(len(daily))])


def windows_for_grid(daily_map, grid, spans=(1, 3, 7)):
    """คืน dict {span: np.array ยาว len(grid)} — ค่าคงที่ทั้งวัน = ผลรวม `span` วัน ถึงสิ้นสุดเมื่อวาน

    `daily_map` = dict {"YYYYMMDD": ฝน มม./วัน} · `grid` = ลำดับ datetime รายชั่วโมง
    """
    day_of = np.array([t.strftime("%Y%m%d") for t in grid])
    uniq_days = list(dict.fromkeys(day_of))
    daily = np.array([daily_map.get(d, 0.0) for d in uniq_days])
    idx = {d: i for i, d in enumerate(uniq_days)}
    out = {}
    for n in spans:
        w = day_window(daily, n)
        out[n] = np.array([w[idx[d]] for d in day_of])
    return out
