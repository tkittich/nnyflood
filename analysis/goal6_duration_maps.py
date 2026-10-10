"""แผนที่ระยะเวลาน้ำค้าง (หยาบ) — นับสัดส่วนฉากที่พิกัดมีน้ำ (น้ำรวม VH≤−20 ในที่ราบ)

⚠️ ใช้ "น้ำรวม" (absolute) จาก stage-1 VH — ไม่ใช่มาสก์ Δ ของ stage-2 (คนละวงโคจรเทียบไม่ได้
จึงเป็น 0 เปล่าใน stage-2 · บทเรียน 12 ต.ค.) · ข้อจำกัด: ฉาก S1 ห่างกัน 1–3 วัน = หยาบ ไม่เทียบ RODDSS
รัน: python analysis/goal6_duration_maps.py
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = ["Leelawadee UI", "Tahoma"]
ROOT = Path(__file__).resolve().parent.parent
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
OUT = STAGE1 / "duration_maps"
OUT.mkdir(parents=True, exist_ok=True)
VH_WATER = -20.0

summary = {}
for stage1_dir in sorted(STAGE1.iterdir()):
    if not stage1_dir.is_dir():
        continue
    bid = stage1_dir.name
    vh_files = sorted(stage1_dir.glob('*_vh_db.npy'))
    lowland_p = STAGE1 / f"mask_lowland_{bid}.npy"
    if not vh_files or not lowland_p.exists():
        continue
    g = json.loads((STAGE1 / f"grid_{bid}.json").read_text(encoding='utf-8'))
    lowland = np.load(lowland_p)
    wet_count = np.zeros((g['ny'], g['nx']), np.float32)
    covered = np.zeros((g['ny'], g['nx']), np.float32)
    for f in vh_files:
        v = np.load(f)
        c = np.isfinite(v) & lowland
        covered += c
        wet_count += ((v <= VH_WATER) & c).astype(np.float32)
    valid = covered >= 2
    frac = np.where(valid, wet_count / np.maximum(covered, 1), np.nan)
    np.save(OUT / f"duration_{bid}.npy", frac)
    fig, ax = plt.subplots(figsize=(9, 7), dpi=100)
    im = ax.imshow(frac, extent=[g['x0'], g['x1'], g['y0'], g['y1']],
                   origin='upper', aspect='auto', cmap='YlGnBu', vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label='สัดส่วนฉากที่มีน้ำ (จากฉากที่ครอบจุดนั้น)')
    ax.set_title(f"ระยะเวลาน้ำค้าง (หยาบ) — {bid}\n{len(vh_files)} ฉาก S1 ห่างกัน 1–3 วัน · น้ำรวม VH≤−20 ในที่ราบ", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / f"duration_{bid}.png", bbox_inches='tight')
    plt.close(fig)
    hi = float(((frac >= 0.5) & valid).sum()) * 0.0009
    summary[bid] = {'n_scenes': len(vh_files), 'area_wet_50pct_km2': round(hi, 1)}
    print(f"{bid}: {len(vh_files)} ฉาก · พื้นที่น้ำ ≥50% = {hi:.0f} ตร.กม.", flush=True)

(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding='utf-8')
print('เขียนแล้ว:', OUT / 'summary.json')
