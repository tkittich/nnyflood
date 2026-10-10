"""เป้าหมาย 6 — L2 ขั้นที่ 2: ตัดน้ำด้วยกฎ canonical (เทียบฉากก่อนเหตุการณ์ วงโคจรเดียวกัน)

กฎ pipeline นครนายก (คาลิเบรต F1=0.727 — import จาก s1_change_detect.detect):
    น้ำ = (ΔVH ≤ −0.5) & (ΔVV ≤ −1.5) & (VHหลัง ≤ −20) + opening 3×3 — ใน lowland <60 ม.

วิธีจับคู่: กลุ่มฉากในลุ่มตามเวลาสัมผัส HH:MM (พรอกซีวงโคจร — บทเรียน Δ ต้องคู่วงโคจรเดียวกัน;
S1C/S1D วงเดียวกันใช้คู่กันได้ — จดสังกัดดาวเทียวในสถิติ) · อ้างอิง = ฉากเร็วสุดของวงในหน้าต่าง
(คาดว่า ≤24 ก.ย. = ก่อนระลอก) · ทุกฉากอื่นของวงนั้นตัดน้ำเทียบอ้างอิง

ผลลัพธ์: derived/s1_stage2/<basin>/<scene>_water.npy + stats · analysis/goal6/s1_stage2_summary.json/.md
รัน: python analysis/goal6_s1_stage2_water.py [--basin id]
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

sys_path = Path(__file__).resolve().parent
import sys  # noqa: E402

sys.path.insert(0, str(sys_path))
from s1_change_detect import detect  # noqa: E402 — กฎ canonical นครนายก

ROOT = Path(__file__).resolve().parent.parent
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
STAGE2 = ROOT / "data/22_goal6_network/derived/s1_stage2"
CONFIG = ROOT / "analysis/goal6/config.json"
CELL_KM2 = 0.0009  # 30 ม. × 30 ม.


def scenes_in_basin(bid: str) -> list[Path]:
    return sorted(STAGE1.joinpath(bid).glob("*_stats.json"))


def hhmm(scene: str) -> str:
    m = re.search(r"T(\d{6})", scene)
    return f"{m.group(1)[:2]}:{m.group(1)[2:4]}" if m else "?"


def load_db(bid: str, tag: str, pol: str) -> np.ndarray:
    return np.load(STAGE1 / bid / f"{tag}_{pol}_db.npy")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--basin", default=None)
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    (STAGE2).mkdir(parents=True, exist_ok=True)
    basins = [args.basin] if args.basin else list(cfg["basins"].keys())

    summary = {}
    for bid in basins:
        out_dir = STAGE2 / bid
        out_dir.mkdir(parents=True, exist_ok=True)
        lowland_p = STAGE1 / f"mask_lowland_{bid}.npy"
        if not lowland_p.exists():
            print(f"ข้าม {bid} (ไม่มี mask ที่ราบ — รัน goal6_s1_dem.py ก่อน)", flush=True)
            continue
        lowland = np.load(lowland_p)
        stats_files = scenes_in_basin(bid)
        if len(stats_files) < 2:
            print(f"ข้าม {bid} (ฉาก <2)", flush=True)
            continue
        tags = [(sf.stem.replace("_stats", ""), json.loads(sf.read_text(encoding="utf-8"))) for sf in stats_files]
        # กลุ่มวงโคจร (HH:MM) → อ้างอิงเร็วสุด
        tracks = defaultdict(list)
        for tag, st in tags:
            tracks[hhmm(tag)].append((tag, st))
        summary[bid] = {"tracks": {}, "scenes": []}
        for hh, group in sorted(tracks.items()):
            group.sort(key=lambda x: x[0])
            ref_tag = group[0][0]
            pre_vh, pre_vv = load_db(bid, ref_tag, "vh"), load_db(bid, ref_tag, "vv")
            for tag, st in group:
                post_vh, post_vv = load_db(bid, tag, "vh"), load_db(bid, tag, "vv")
                w = detect(pre_vh, post_vh, pre_vv, post_vv, lowland)
                km2 = round(float(w.sum()) * CELL_KM2, 1)
                plain_km2 = round(float(lowland.sum()) * CELL_KM2, 1)
                np.save(out_dir / f"{tag}_water.npy", w)
                rec = {"basin": bid, "track": hh, "reference": ref_tag, "scene": tag,
                       "water_km2_lowland": km2, "plain_km2": plain_km2,
                       "water_frac_plain": round(km2 / plain_km2, 4) if plain_km2 else None,
                       "coverage": st.get("vh_valid_frac"), "satellite": tag[:3]}
                summary[bid]["tracks"][hh] = summary[bid]["tracks"].get(hh, {}) | {"reference": ref_tag}
                summary[bid]["scenes"].append(rec)
                (out_dir / f"{tag}_stats.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
                print(f"  {bid} [{hh}] {tag[12:26]} ref={ref_tag[12:26]} · น้ำ {km2} ตร.กม. "
                      f"({rec['water_frac_plain']:.1%} ที่ราบ)", flush=True)
        # MD สั้น
        lines = [f"# น้ำท่วม S1 — {bid} (กฎ canonical)", "",
                 f"> อ้างอิงต่อวงโคจร (HH:MM) = ฉากเร็วสุด · กฎ ΔVH≤−0.5/ΔVV≤−1.5/VH≤−20 + opening 3×3 ใน lowland <60 ม.",
                 "", "| วง | ฉาก | น้ำ (ตร.กม.) | % ที่ราบ | ครอบกริด | ดาวเทียม |", "|---|---|---|---|---|---|"]
        for rec in sorted(summary[bid]["scenes"], key=lambda r: (r["track"], r["scene"])):
            lines.append(f"| {rec['track']} | {rec['scene'][12:40]} | {rec['water_km2_lowland']} | "
                         f"{rec['water_frac_plain']:.1%} | {rec['coverage']:.0%} | {rec['satellite']} |")
        lines.append("")
        (ROOT / "analysis/goal6" / f"s1_stage2_{bid}.md").write_text("\n".join(lines), encoding="utf-8")

    (STAGE2 / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"เขียนแล้ว: {STAGE2 / 'summary.json'}", flush=True)


if __name__ == "__main__":
    main()