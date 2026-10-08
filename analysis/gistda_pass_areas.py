"""สรุปพื้นที่น้ำท่วมจาก attribute ของ shapefile GISTDA ราย pass → analysis/gistda_pass_areas_nn.json

นี่คือ **producer** ของตัวเลข GISTDA canonical (build_canonical_numbers.py อ่านไฟล์ JSON นี้)
— ก่อนหน้านี้ JSON เป็น orphan constant ไม่มีสคริปต์สร้าง (ผลรีวิว GLM GL-04)

วิธี: อ่านทุก polygon ตำบลของ pass, กรอง PV_IDN == 26 (นครนายก — กรองด้วยรหัสตัวเลข
เพราะ encoding ของ dbf ต่างกันรายไฟล์: บาง pass utf-8 บาง pass iso-8859-11/tis-620
= ตรงบันทึก METHODS §7), ผลรวมฟิลด์ `flood_area` (หน่วย **ไร่**) ÷ 625 ไร่/ตร.กม.

ผลตรวจ 8 ต.ค. 69: reproduce ค่าเดิมทุก pass (11.8 / 8.3 / 0.0×3 / 306.9)
"""
import json
from pathlib import Path

import shapefile

PROJ = Path(__file__).resolve().parent.parent
MANUAL = PROJ / "data" / "manual"
OUT = PROJ / "analysis" / "gistda_pass_areas_nn.json"

# ชื่อ pass → ชื่อโฟลเดอร์ shp ใต้ data/manual/ (คีย์ตรงตามที่ canonical อ่าน)
PASSES = [
    "rd2_20260924_1815",
    "S1D_20260927_0601",
    "S1C_20260928_0550",
    "S1C_20260928_1819",
    "S1D_20260929_1812",
    "S1D_20261002_0609",
]

RAI_PER_KM2 = 625.0


def pass_area_km2(shp_path):
    try:
        r = shapefile.Reader(str(shp_path))   # ใช้ .cpg ของไฟล์เอง
    except LookupError:
        # บาง pass มี .cpg พิมพ์ผิด ("iso 885911" ไม่มีขีด) → ตัวอักษรไทยใช้ cp874 เท่ากัน
        # (เราอ่านเฉพาะฟิลด์ตัวเลข PV_IDN/flood_area — encoding กระทบแค่ฟิลด์ข้อความ)
        r = shapefile.Reader(str(shp_path), encoding="cp874")
    tot = 0.0
    for sr in r.iterShapeRecords():
        if sr.record["PV_IDN"] != 26:
            continue
        tot += float(sr.record["flood_area"])
    return tot / RAI_PER_KM2, tot


def main():
    out = {}
    for p in PASSES:
        d = MANUAL / f"shp_{p}"
        shps = sorted(d.glob("*.shp"))
        if not shps:
            raise FileNotFoundError(f"ไม่พบ .shp ใน {d}")
        km2, rai = pass_area_km2(shps[0])
        out[p] = round(km2, 1)
        print(f"{p}: ผลรวม {rai:,.1f} ไร่ = {km2:.2f} ตร.กม. → {out[p]}")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved:", OUT)


if __name__ == "__main__":
    main()
