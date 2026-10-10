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
    colors = ["#e74c3c" if y == 2026 else "#4d94c9" for y in years]
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
    plot_c2_volume_vs_dams()



def plot_c2_volume_vs_dams() -> None:
    """ปริมาตรรายวัน: น้ำที่ผ่าน C.2 vs ปล่อยรวม 2 เขื่อน vs น้ำเข้ารวม (ตัวแทนฝนลุ่นบน)"""
    src = json.loads((ROOT / 'data/22_goal6_network/raw/spike_ping_cp/c2_discharge_daily_sep2026.json').read_text(encoding='utf-8'))
    dates = sorted(src['C2_daily_volume_max_mcm'])
    xs = list(range(len(dates)))
    c2 = [src['C2_daily_volume_max_mcm'][x] for x in dates]
    rel = [(src['bhumibol_released'].get(x, 0) or 0) + (src['sirikit_released'].get(x, 0) or 0) for x in dates]
    inflow = [(src['bhumibol_inflow'].get(x, 0) or 0) + (src['sirikit_inflow'].get(x, 0) or 0) for x in dates]
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=110)
    ax.plot(xs, c2, color='#1d6fb8', lw=2.2, label='น้ำที่ไหลผ่าน C.2 ท่าเรือ')
    ax.plot(xs, inflow, color='#7d3c98', lw=1.6, ls='--', label='น้ำไหลเข้าเขื่อนรวม (ตัวแทนฝนลุ่มบน)')
    ax.bar(xs, rel, color='#c0392b', alpha=0.5, width=0.7, label='การปล่อยน้ำเขื่อนรวม')
    ax.set_xticks(xs[::3])
    ax.set_xticklabels([f"{d[8:]}/{d[5:7]}" for d in dates[::3]], fontsize=9)
    ax.set_ylabel('ล้าน ลบ.ม./วัน', fontsize=10)
    ax.set_xlabel('วันที่ กันยายน–ตุลาคม 2569', fontsize=10)
    ax.set_title('ปริมาตรน้ำรายวันที่ C.2 ท่าเรือ — โตตามฝนลุ่มบน ขณะที่เขื่อนลดการปล่อยลง', fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / 'c2_volume_vs_dams.png', bbox_inches='tight')
    plt.close(fig)
    print('  c2_volume_vs_dams.png')

if __name__ == "__main__":
    main()

def plot_c2_vs_releases() -> None:
    """กราฟคู่: การปล่อยเขื่อน (ลดลง) vs ระดับ C.2 (ขึ้น) — หลักฐาน 'ไม่ใช่น้ำปล่อยล่วงหน้า'"""
    d = json.loads((ROOT / 'data/22_goal6_network/raw/spike_ping_cp/c2_vs_dam_releases_sep2026.json').read_text(encoding='utf-8'))
    dates = sorted(d['C2_daily_max'])
    xs = list(range(len(dates)))
    c2 = [d['C2_daily_max'][x] for x in dates]
    bhum = [d['bhumibol_released'].get(x) for x in dates]
    siri = [d['sirikit_released'].get(x) for x in dates]

    fig, ax1 = plt.subplots(figsize=(11, 4.6), dpi=110)
    ax1.plot(xs, c2, color='#1d6fb8', lw=2.2, marker='o', ms=3, label='ระดับน้ำที่ C.2 ท่าเรือ (สูงสุดรายวัน)')
    ax1.set_ylabel('ระดับน้ำ (ม.รทก.)', color='#1d6fb8', fontsize=10)
    ax1.tick_params(axis='y', labelcolor='#1d6fb8')
    ax2 = ax1.twinx()
    ax2.plot(xs, bhum, color='#c0392b', lw=1.6, marker='s', ms=3, label='เขื่อนภูมิพลปล่อย')
    ax2.plot(xs, siri, color='#e67e22', lw=1.6, marker='^', ms=3, label='เขื่อนสิริกิติ์ปล่อย')
    ax2.set_ylabel('การปล่อยน้ำ (ล้าน ลบ.ม./วัน)', color='#8a2b2b', fontsize=10)
    ax2.tick_params(axis='y', labelcolor='#8a2b2b')
    tick_idx = [i for i in range(0, len(dates), 3)]
    ax1.set_xticks(tick_idx)
    ax1.set_xticklabels([f"{dates[i][8:]}" for i in tick_idx], fontsize=9)
    ax1.set_xlabel('วันที่ กันยายน–ตุลาคม 2569', fontsize=10)
    ax1.axhline(25.7, color='#888', ls=':', lw=1)  # min_bank ตลิ่ง
    ax1.text(1, 25.85, 'ระดับตลิ่ง 25.7 ม.', fontsize=8, color='#888')
    ax1.set_title('ระดับน้ำที่ C.2 ท่าเรือ ขึ้นพร้อมกับที่เขื่อนลดการปล่อยลง —\nไม่ใช่น้ำที่เขื่อนปล่อยล่วงหน้า (ปิง–เจ้าพระยาตอนบน)', fontsize=12)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8.5, loc='upper left')
    ax1.grid(alpha=0.25)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / 'c2_vs_dam_releases.png', bbox_inches='tight')
    plt.close(fig)
    print('  c2_vs_dam_releases.png')
