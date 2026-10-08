# แผนที่ทับซ้อน: จุดสังเกตจากภาพประชาชน (สแกน 234/666 ภาพ) บนแผนที่ช่วงสูงสุด 27 ก.ย.
# จุดจากแบตช์ 5-13 (ภาพ 65-222) — เขื่อนขุนด่านฯ (สปิลเวย์), ทล.305 กม.41+800 หน้า มศว.องครักษ์,
#   เทศบาล ต.บางสมบูรณ์ (แจกของ 3 ต.ค.) และ บ้านสร้าง (กำกวม — อ.บ้านสร้าง ปราจีนบุรี ใกล้นครนายก)
# แบตช์ 14 (ภาพ 223-234): ยังไม่เพิ่มหมุดใหม่ — แบตช์นี้ให้ "หลักฐานตัวเลข" (อินโฟกราฟิกเขื่อน 2 ต.ค. 12:00)
#   และ "ชื่อสถานที่ยืนยันได้แต่ยังไม่ยืนยันพิกัด" (วัดกลางคลองสามสิบ ต.บางปลากด อ.องครักษ์) จึงยังไม่ปักหมุดเพื่อไม่ให้พิกัดมั่ว
import sys, csv
sys.path.insert(0, "report")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from report_assets import draw_roads, draw_water   # noqa

DER = "data/13_sentinel1_copernicus/derived"
gr = __import__("json").load(open(f"{DER}/grid.json", encoding="utf-8"))
prov = np.load(f"{DER}/mask_province.npy")
mask = np.load(f"{DER}/flood_peak_27sep1828.npy")

# พิกัดจุดจากความมั่นใจสูง/ปานกลาง (lon, lat, ชื่อสั้น, สี)
pts = [
    (101.21931, 14.20048, "สพ.หน้าจวนผู้ว่าฯ (Ny.7)", "#ffffff"),
    (101.2345, 14.2065, "ประตูเมือง ถ.สุวินทวงศ์", "#ffd54f"),
    (101.2265, 14.2095, "ถ.พาณิชยกรรม (ย่านร้าน)", "#ffd54f"),
    (101.2265, 14.2030, "รพ.นครนายก", "#ff8a65"),
    (101.2280, 14.2155, "Lotus's นครนายก", "#ffd54f"),
    (101.2330, 14.1930, "ถ.ท่านบุญ (Makro)", "#ffd54f"),
    (101.2742, 14.2458, "Ny.1B บ้านเขานางบวช", "#4fc3f7"),
    (101.1678, 14.1658, "บ้านศรีดาสาย (พิกัดในภาพ)", "#81c784"),
    (101.28, 14.175, "อ.บ้านนา (GPS ในภาพ)", "#81c784"),
    (101.34, 14.10, "อบต.โพธิ์ไพรวัลย์ (ปตร.ช่วย)", "#81c784"),
    (101.21, 14.175, "ถ.เฉลิมพระเกียรติ กม.3", "#ff8a65"),
    (101.30, 14.16, "ถนน 3049/3239 ต.ศรีอุดม (ปิดทาง)", "#ff8a65"),
    (101.3214, 14.3147, "เขื่อนขุนด่านฯ (ระบายสปิลเวย์)", "#4fc3f7"),
    (100.984, 14.106, "ทล.305 กม.41+800 หน้า มศว.องครักษ์", "#ff8a65"),
    (101.1275, 14.0197, "เทศบาล ต.บางสมบูรณ์ (แจกของ 3 ต.ค.)", "#81c784"),
    (101.2478, 13.9941, "บ้านสร้าง (กำกวม — อ.บ้านสร้าง ปจ.)", "#ba68c8"),
]

fig, ax = plt.subplots(figsize=(7.6, 7.5), dpi=120)
ax.set_aspect(110.96 / (111.32 * np.cos(np.radians(14.24))))
ax.set_xlim(gr["x0"], gr["x1"]); ax.set_ylim(gr["y0"], gr["y1"])
ax.set_xticks([]); ax.set_yticks([])
show = np.where(mask & prov, 1.0, np.nan)
ax.imshow(show, extent=[gr["x0"], gr["x1"], gr["y0"], gr["y1"]], origin="upper",
          cmap=plt.matplotlib.colors.ListedColormap([(0.13, 0.44, 0.86, 0.75)]),
          vmin=0, vmax=1, interpolation="nearest", aspect="auto")
draw_water(ax); draw_roads(ax)
for lon, lat, name, c in pts:
    ax.plot(lon, lat, "o", ms=7, mfc=c, mec="#111", mew=0.8, zorder=8)
texts = [ax.annotate(name, xy=(lon, lat), xytext=(4, 4), textcoords="offset points",
                     fontsize=6.8, color="#fff", zorder=9,
                     bbox=dict(fc="#000000aa", ec="none", pad=0.8))
         for lon, lat, name, c in pts]
ax.set_title("จุดที่ระบุได้จากภาพประชาชน (สแกน 234/666 ภาพ) ทับขอบเขตน้ำท่วมช่วงน้ำสูงสุด 27 ก.ย. 69", fontsize=10.5)
fig.tight_layout()
fig.savefig("analysis/album_geotag_map.png", dpi=130)
print("saved analysis/album_geotag_map.png | จุด:", len(pts))
