"""ค่าคงที่กายภาพ + สูตรกลางของโปรเจกต์ — แหล่งเดียว ห้ามพิมพ์ literal ซ้ำในสคริปต์อื่น

ทำไมต้องมี: rating curve (242/4.55/0.66) · datum (1.59) · bankfull (6.86) · สูตรพื้นที่เซลล์
เคยถูกพิมพ์ซ้ำกระจาย 5–7 ไฟล์ และเคยทำให้เกิดบั๊กหน่วยจริง (ความจุลำน้ำ 2.0 MCM —
ดู goal4_counterfactual_model.py บันทึกท้ายไฟล์) — แก้โดยชี้มาที่ไฟล์นี้ที่เดียว

โครงสร้างที่ตั้งใจ:
- GAUGE_OFFSET / project_rating นิยามเดียวใน rid_cross_section_hydraulics.py (ผ่าน test_core)
- ไฟล์นี้ re-export + เพิ่มค่าคงที่ที่ใช้ข้ามสคริปต์ (RATING_*, BANKFULL_MSL, cell_km2)
- despike ของตระกูล goal4 ยังอยู่ในแต่ละไฟล์ (algoritเดียวกัน: กระโดด >0.5 ม./15 นาที
  แล้วกลับใน 3 ช่อง แต่ plumbing ต่างกันตามรูปทรงข้อมูล — v1 รับ (level,Q), ตัวอื่นรับ float;
  all_stations_network ใช้ rolling variant ต่างออกไปโดยเจตนา) — รวมเมื่อจำเป็นจริง
"""
import math

# re-export จากโมดูลที่ผ่านการทดสอบ — สคริปต์อื่น import จากที่นี่ได้เลย
from rid_cross_section_hydraulics import GAUGE_OFFSET, project_rating  # noqa: F401

# ---- rating curve Ny.7 (K5 khundan_tele_findings · ทดสอบใน test_core::project_rating) ----
RATING_A = 242.0   # ม³/วิ ที่ (h − RATING_B) = 1
RATING_B = 4.55    # ม.รทก. ระดับก้นน้ำอ้างอิง
RATING_C = 0.66    # เลขชี้กำลัง

# ---- ระดับล้นตลิ่ง/เริ่มท่วม ----
BANKFULL_MSL = 6.86    # ม.รทก. เริ่มท่วมที่ราบ (เกจ 8.45 − datum 1.59)


def cell_km2(res_deg: float) -> float:
    """พื้นที่ (ตร.กม.) ของเซลล์กริด S1 ขนาด res_deg องศา — ละติจูด 14.2 (ค่าที่ผลิต
    canonical numbers ทั้งหมด — ห้ามเปลี่ยนเพราะพื้นที่ 509.3/436.3 ผูกกับค่านี้)"""
    return res_deg * 111.32 * res_deg * 111.32 * math.cos(math.radians(14.2))
