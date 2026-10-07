# HEC-RAS-lite: ภูมิศาสตร์ช่องทางลำน้ำนครนายกจาก DEM + stage-storage + ตรวจยืนยัน M4
# วิธี: ตัดภาพตัดขวางตั้งฉากแนวแม่น้ำ (จาก OSM waterways) จาก DEM 30 ม. ทุก ~3 กม.
#       → ความกว้างช่องทาง/พื้นที่ผิวน้ำ/ปริมาตรเก็บตามระดับ → ตรวจ M4 (ระบายล่วงหน้า 5.2 ลลบ.ม. = ระดับต่ำลงเท่าไร)
# ข้อจำกัด: DEM = DSM (ผิวน้ำขณะถ่าย ไม่ใช่ท้องน้ำจริง) — ใช้เป็นตัวแทนผิวน้ำและธนาคารลำน้ำ ประมาณการอันดับแรก
# ผู้จัดทำ: AI — ควรตรวจทานโดยผู้เชี่ยวชาญ
import json
import math
import numpy as np
import rasterio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DER = ROOT / "data" / "13_sentinel1_copernicus" / "derived"

gr = json.load(open(DER / "grid.json", encoding="utf-8"))
dem = np.load(DER / "dem_30m.npy")
prov = np.load(DER / "mask_province.npy")
W = json.load(open(DER / "waterways.json", encoding="utf-8"))

# 1) แนวแม่น้ำนครนายก (สายหลัก)
main = max((r for r in W["rivers"] if r["name"] == "แม่น้ำนครนายก"), key=lambda r: r["km"])
line = np.array(main["coords"])   # lon/lat เรียงจากต้นน้ำ(?) ไปปลายน้ำ
print(f"แม่น้ำนครนายก: {len(line)} จุด · ยาว ~{main['km']:.0f} กม. · จาก ({line[0][0]:.3f},{line[0][1]:.3f}) ถึง ({line[-1][0]:.3f},{line[-1][1]:.3f})")

# ระยะสะสม (กม. โดยประมาณ)
lat_scale = 111.32; lon_scale = 110.96 / np.cos(np.radians(14.24))
seg = np.diff(line, axis=0)
dist = np.cumsum(np.hypot(seg[:, 0] * lon_scale, seg[:, 1] * lat_scale))
dist = np.concatenate([[0], dist])

# 2) ตำแหน่งตัดขวางทุก ~3 กม. (ตั้งแต่ 3 กม.หลังเขื่อนถึงช่วงท้าย)
sec_idx = []
target = 3.0
for i in range(1, len(line)):
    if dist[i] >= target:
        sec_idx.append(i); target = dist[i] + 3.0
print(f"ตำแหน่งตัดขวาง {len(sec_idx)} จุด (ทุก ~3 กม.)")

def dem_at(lon, lat):
    """ค่า DEM ที่พิกัด (ออกนอกกริด = nan)"""
    c = int((lon - gr["x0"]) / (gr["x1"] - gr["x0"]) * dem.shape[1])
    r = int((gr["y1"] - lat) / (gr["y1"] - gr["y0"]) * dem.shape[0])
    if 0 <= r < dem.shape[0] and 0 <= c < dem.shape[1]:
        z = dem[r, c]
        return z if z > 0 else np.nan
    return np.nan

def cross_section(i, half=350.0, n=35):
    """ตัดขวางตั้งฉากกว้าง 700 ม. ที่จุด i — คืน (ระยะจากศูนย์กลาง ม., ระดับ ม.รทก.)"""
    # ทิศตั้งฉากกับแนวแม่น้ำ
    a, b = line[max(i - 3, 0)], line[min(i + 3, len(line) - 1)]
    dx = (b[0] - a[0]) * lon_scale; dy = (b[1] - a[1]) * lat_scale
    L = math.hypot(dx, dy) if (dx or dy) else 1.0
    px, py = -dy / L, dx / L          # ตั้งฉาก (หน่วย ม./หนึ่งหน่วย lon,lat-scaled)
    ds = np.linspace(-half, half, n)
    # ระวังหน่วย: ds เป็น "เมตร" แต่ lon_scale/lat_scale เป็น "กม./องศา" — ห้ามหารตรง ๆ
    #   ถ้าใช้ ds*px/lon_scale -> 350 ม. จะกลายเป็น 3.07 องศา (~340 กม.) ภาคตัดขวางกวาด
    #   จาก 99.6°E ถึง 102.8°E · DEM ในกริดจะเหลือแค่ 2/35 จุด -> "ความกว้าง" ที่รายงานเป็น
    #   แค่ 1–2 เซลล์ (20.6/41.2 ม.) ตลอด ทำให้ stage-storage ต่ำกว่าจริงมาก
    #   ต้องหารด้วย "เมตร/องศา" = lon_scale*1000
    xs = line[i][0] + ds * px / (lon_scale * 1000.0)
    ys = line[i][1] + ds * py / (lat_scale * 1000.0)
    zs = np.array([dem_at(x, y) for x, y in zip(xs, ys)])
    return ds, zs

sections = []
for i in sec_idx:
    ds, zs = cross_section(i)
    if np.isnan(zs).all():
        continue
    z_th = np.nanmin(zs)                          # จุดต่ำสุด ≈ ผิวน้ำ/ท้องน้ำ
    z_bank = np.nanpercentile(zs, 90)             # ขอบตลิ่ง (ประมาณ)
    # ความกว้างช่องทางที่ระดับสูงขึ้นจากจุดต่ำสุด d ม.: จำนวนจุดที่ระดับ < z_th + d
    widths = {}
    for d in (0.5, 1.0, 1.5, 2.0, 3.0):
        widths[d] = float((zs < z_th + d).sum()) * (700.0 / (len(ds) - 1))
    if z_bank > 30:   # ภูเขา/ป่า — ไม่ใช่ลำน้ำที่ราบ (ข้าม)
        continue
    sections.append({"km": float(dist[i]), "lon": float(line[i][0]), "lat": float(line[i][1]),
                     "z_thalweg": float(z_th), "z_bank": float(z_bank),
                     "width_m": widths})
    print(f"  กม.{dist[i]:5.1f} ({line[i][0]:.3f},{line[i][1]:.3f}) ผิวน้ำ~{z_th:.1f} ตลิ่ง~{z_bank:.1f} "
          f"กว้าง@+1ม={widths[1.0]:.0f}ม @+2ม={widths[2.0]:.0f}ม")

# 3) stage-storage ของช่วงแม่น้ำ (เขื่อน→ท้ายจังหวัด)
print("\n--- stage-storage (ปริมาตรเก็บในช่องทาง เทียบจุดต่ำสุดของแต่ละภาคตัดขวาง) ---")
dx_step = np.diff([s["km"] for s in sections] + [sections[-1]["km"] + 3.0])
rows = []
for d in (0.5, 1.0, 1.5, 2.0, 3.0):
    vol = 0.0
    for s, dx in zip(sections, dx_step):
        vol += s["width_m"][d] * dx * 1000 * d        # ม.กว้าง × ม.ยาว × ม.ลึก
    rows.append((d, vol / 1e6))
    print(f"  ลึก {d:.1f} ม.จากจุดต่ำสุดทุกภาค: ปริมาตรเก็บ ≈ {vol/1e6:6.1f} ลลบ.ม.")

# 4) ตรวจ M4: ระบายล่วงหน้า 5.2 ลลบ.ม. → ระดับลำน้ำลดเท่าไร
print("\n--- ตรวจยืนยัน M4 (ระบายล่วงหน้า ~5.2 ลลบ.ม. ในหน้าต่าง 36 ชม.) ---")
v50, v100, v150, v200, v300 = [r[1] for r in rows]
w_avg = float(np.mean([s["width_m"][1.5] for s in sections])) if sections else 0.0
L_total = (sections[-1]["km"] - sections[0]["km"]) * 1000 if len(sections) > 1 else 0
surf_km2 = w_avg * L_total / 1e6
print(f"  ผิวน้ำลำน้ำช่วงที่ราบ ({len(sections)} ภาคตัดขวาง, ยาว {L_total/1000:.0f} กม., กว้างเฉลี่ย@+1.5ม = {w_avg:.0f} ม.) ≈ {surf_km2:.2f} ตร.กม.")
dv = 5.2
dd = dv * 1e6 / (w_avg * L_total)
print(f"  M4 ระบายล่วงหน้า {dv} ลลบ.ม.: ลำน้ำเก็บได้เพียง ~{v200:.1f} ลลบ.ม. (+2ม. ทุกภาค)")
print(f"  → ระบาย 5.2 ลลบ.ม.: ~{min(dv, v200):.1f} ลลบ.ม. ลดระดับลำน้ำ (~{min(dv, v200)*1e6/(w_avg*L_total)*100:.0f} ซม.) ส่วนที่เหลือ {max(0, dv-v200):.1f} ลลบ.ม. ไหลออกปลายน้ำต่อ")
print("  → ข้อสรุป M4: ผลหลักคือ 'ส่งน้ำออกจากระบบลุ่มก่อนพีค' + ลำน้ำต่ำลงชั่วคราว ไม่ใช่เก็บในลำน้ำได้มาก")

json.dump(sections, open(ROOT / "analysis" / "river_cross_sections.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nบันทึก: analysis/river_cross_sections.json")
