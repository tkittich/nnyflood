"""กราฟหัวใจรายงาน 3+4 — ระดับน้ำเก็บเขื่อนเทียบเส้นกำกับ (rule curve) ปี 2554 และ 2569

แบบแผนกราฟ: ภาษาไทย (Leelawadee UI) · เส้นกำกับบน/ล่างเป็นเส้นประ · พื้นที่เกิน = แดงอ่อน
· ชื่อกราฟอธิบายเอง (ผู้อ่านไม่ต้องเปิดเอกสารอื่น) · ตัวเลขกำกับจุดสูงสุด

ผลลัพธ์: report/assets/goal6/
  - urc_2554_pasak.png + urc_2554_bhumibol.png   (2554: ตัวอย่างเขื่อนที่เกินหนัก)
  - urc_2569_pasak.png                            (2569: ระลอกเดียว)
  - rain_46y_ayutthaya.png                        (ฝน 46 ปี — 2569 อันดับ 1)
รัน: python analysis/goal6_report_charts.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report/assets/goal6"
DAM_HIST = ROOT / "data/22_goal6_network/raw/dam_history_all"
RAW_RAIN = ROOT / "data/22_goal6_network/raw/rain_rarity"


def plot_urc_year(dam_name: str, year: int, out_png: Path, subtitle: str) -> None:
    rec = json.loads((DAM_HIST / f"dam_{json.loads((ROOT / 'analysis/goal6/dam_history_all.json').read_text(encoding='utf-8'))['dams'][dam_name]['dam_id_used']}.json").read_text(encoding="utf-8"))
    # ประวัติเต็มเก็บใน raw (storage_all ไม่ได้เซฟ — ใช้แถวรายวันจาก years + URC จาก urc_mmdd)
    urc = rec["urc_mmdd"]
    rows = next(r for r in rec["years"] if r["year"] == year)
    # จำเป็นต้องมีค่ารายวันจริง — ดึงจาก API ใหม่ถ้าไม่มีในแคช
    cache = ROOT / f"data/22_goal6_network/raw/dam_history_all/dam{rec['dam_id_used']}_daily_{year}.json"
    if cache.exists():
        daily = json.loads(cache.read_text(encoding="utf-8"))
    else:
        import goal6_screen_basins as g6
        pairs = g6.fetch_dam_series(rec["dam_id_used"], "dam_storage", str(year))
        daily = {dt: v for dt, v in pairs or []}
        cache.write_text(json.dumps(daily, ensure_ascii=False), encoding="utf-8")
    dates = sorted(d for d in daily if daily[d] is not None)
    vals = [daily[d] for d in dates]
    xs = list(range(len(dates)))
    urc_line = [urc.get(d[5:], None) for d in dates]
    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=110)
    ax.plot(xs, vals, color="#1e6fb8", lw=1.4, label="ปริมาณน้ำเก็บจริง")
    # เส้นกำกับบน/ล่าง
    urc_arr = np.array([u if u is not None else np.nan for u in urc_line], dtype=float)
    ax.plot(xs, urc_arr, color="#c0392b", lw=1.6, ls="--", label="ระดับกำกับบน (เพดานตามแผนประจำปี)")
    over = np.where(np.array(vals, dtype=float) > urc_arr)[0]
    if len(over):
        ax.fill_between(xs, urc_arr, np.array(vals, dtype=float), where=np.array(vals) > urc_arr,
                        color="#e74c3c", alpha=0.25, label="เก็บเกินระดับกำกับ")
        imax = int(np.nanargmax(np.array(vals, dtype=float)))
        ax.annotate(f"สูงสุด {vals[imax]:,.0f}\n{dates[imax][5:]}",
                    xy=(imax, vals[imax]), fontsize=9, color="#8a2b2b",
                    xytext=(imax - 30, vals[imax] * 1.02))
    tick_idx = [i for i in range(0, len(dates), 61)]
    ax.set_xticks(tick_idx)
    ax.set_xticklabels([f"{dates[i][5:7]}/{dates[i][2:4]}" for i in tick_idx], fontsize=9)
    ax.set_ylabel("ล้าน ลบ.ม.", fontsize=10)
    ax.set_title(f"{dam_name} ปี {year + 543} — ปริมาณน้ำเก็บเทียบระดับกำกับ", fontsize=13)
    ax.text(0.01, -0.18, subtitle, transform=ax.transAxes, fontsize=8.5, color="#5a6675")
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    print(f"  {out_png.name}")


def plot_rain_46y() -> None:
    d = json.loads((ROOT / "analysis/goal6/rain_rarity.json").read_text(encoding="utf-8"))
    pt = d["points"]["bp_prach_นครนายก"]["best7"]["annual_series"]
    years = sorted(int(y) for y in pt)
    vals = [pt[str(y)][0] or 0 for y in years]
    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=110)
    colors = ["#e74c3c" if y == 2026 else "#9bb7c9" for y in years]
    ax.bar([y + 543 for y in years], vals, color=colors)
    ax.axhline(150, color="#c0392b", ls="--", lw=1.2)
    ax.text(years[0] + 543, 155, "เกณฑ์เตือนน้ำท่วม 150 มม./7 วัน", fontsize=9, color="#c0392b")
    ax.annotate(f"2569 = {vals[years.index(2026)]:.0f} มม.\nอันดับ 1 จาก {len(years)} ปี",
                xy=(2026 + 543, vals[years.index(2026)]), fontsize=10, color="#8a2b2b",
                xytext=(2026 + 543 - 12, vals[years.index(2026)] * 0.9))
    ax.set_ylabel("ฝนสะสม 7 วันสูงสุด (มม.)", fontsize=10)
    ax.set_title("ฝนหนัก 7 วันสูงสุดของแต่ละปี (นครนายก) — ปี 2569 สูงสุดใน 46 ปี", fontsize=13)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "rain_46y_nakhonnayok.png", bbox_inches="tight")
    plt.close(fig)
    print("  rain_46y_nakhonnayok.png")


def main() -> None:
    print("กราฟระดับกำกับ:")
    plot_urc_year("ป่าสักชลสิทธิ์", 2011, OUT / "urc_2554_pasak.png",
                  "2554: เก็นน้ำเกินระดับกำกับต่อเนื่องกลางฤดู — 241 วันทั้งปี (ปกติของระบบเขื่อนนี้)")
    plot_urc_year("ภูมิพล", 2011, OUT / "urc_2554_bhumibol.png",
                  "2554: เขื่อนใหญ่สุดเก็บเต็มเกินระดับกำกับ 127 วัน — ระบายหนักลงเจ้าพระยา")
    plot_urc_year("ป่าสักชลสิทธิ์", 2026, OUT / "urc_2569_pasak.png",
                  "2569: เกินเฉพาะระลอกปลาย ก.ย. (39 วัน) — พอดีช่วงน้ำท่วมท้ายลุ่ม")
    print("กราฟฝน 46 ปี:")
    plot_rain_46y()


if __name__ == "__main__":
    main()