"""เป้าหมาย 6 — L2 ขั้นที่ 2: ตัดน้ำด้วยกฎ canonical (เทียบฉากก่อนเหตุการณ์ วงโคจรเดียวกัน)

กฎ pipeline นครนายก (คาลิเบรต F1=0.727 — import จาก s1_change_detect.detect):
    น้ำ = (ΔVH ≤ −0.5) & (ΔVV ≤ −1.5) & (VHหลัง ≤ −20) + opening 3×3 — ใน lowland <60 ม.

วิธีจับคู่ (ปรับ 27 ต.ค. 69 ตามผลตรวจ docs/S1_REFERENCE_AUDIT_PREREG.md): จับตามเลขวงโคจรสัมพัทธ์ (ไม่ใช้เวลา HH:MM เป็นตัวแทนอีก)
อ้างอิง = ทุกชิ้นส่วนของวันล่าสุดของวงนั้นที่ถ่ายก่อน 24 ก.ย. 2569 00:00 UTC รวมเป็นภาพเดียว · S1C/S1D วงเดียวกันใช้คู่กันได้
ฉากอ้างอิงเองไม่นับเป็นน้ำ (reference == scene) · วงที่ไม่มีฉากอ้างอิงก่อนเหตุการณ์ไม่ถูกตัดน้ำ (บันทึกใน unpaired)
ฉากอ้างอิงเสริมที่ถ่ายก่อน 19 ก.ย. อยู่ใน derived/s1_audit_stage1 (ดึงโดย goal6_s1_reference_audit.py)

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
from s1_orbit import EVENT_START, rel_orbit, start_of  # noqa: E402 — เลขวงโคจรสัมพัทธ์ (ใช้จับคู่ฉากอ้างอิง)

ROOT = Path(__file__).resolve().parent.parent
STAGE1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
STAGE1_EXTRA = ROOT / "data/22_goal6_network/derived/s1_audit_stage1"   # ฉากอ้างอิงก่อนเหตุการณ์เสริม (ถ่าย 12–16 ก.ย.) จาก goal6_s1_reference_audit.py
STAGE1_EXTRA2 = ROOT / "data/22_goal6_network/derived/s1_recent_stage1"   # ฉากอ้างอิงเสริมของลุ่มบางปะกง–ปราจีนบุรีจาก goal7_s1_chachoengsao_recent.py
STAGE2 = ROOT / "data/22_goal6_network/derived/s1_stage2"
CONFIG = ROOT / "analysis/goal6/config.json"
CELL_KM2 = 0.0009  # 30 ม. × 30 ม.


def scenes_in_basin(bid: str) -> list[Path]:
    return sorted(STAGE1.joinpath(bid).glob("*_stats.json"))


def hhmm(scene: str) -> str:
    m = re.search(r"T(\d{6})", scene)
    return f"{m.group(1)[:2]}:{m.group(1)[2:4]}" if m else "?"


def load_db(bid: str, tag: str, pol: str) -> np.ndarray:
    for d in (STAGE1 / bid, STAGE1_EXTRA / bid, STAGE1_EXTRA2 / bid):
        p = d / f"{tag}_{pol}_db.npy"
        if p.exists():
            return np.load(p)
    raise FileNotFoundError(f"{bid}/{tag}_{pol}_db.npy")


def pre_event_references(bid: str) -> dict[int, list[str]]:
    """ฉากอ้างอิงต่อเลขวงโคจรสัมพัทธ์ = ทุกชิ้นส่วนของวันล่าสุดที่ถ่ายก่อน EVENT_START (S1C/S1D วงเดียวกันใช้ร่วม)
    — แทนวิธีเดิม "ฉากเร็วสุดของกลุ่ม HH:MM" ที่บางวงได้ฉากระหว่างเหตุการณ์ (ดู docs/S1_REFERENCE_AUDIT_PREREG.md)"""
    pre = defaultdict(list)
    for d in (STAGE1 / bid, STAGE1_EXTRA / bid, STAGE1_EXTRA2 / bid):
        for sf in (sorted(d.glob("*_stats.json")) if d.exists() else []):
            tag = sf.stem.replace("_stats", "")
            if start_of(tag) < EVENT_START and tag not in pre[rel_orbit(tag)]:
                pre[rel_orbit(tag)].append(tag)
    refs = {}
    for r, tags in pre.items():
        day = max(start_of(x)[:10] for x in tags)
        refs[r] = sorted(x for x in tags if start_of(x)[:10] == day)
    return refs


def mosaic_db(bid: str, tags: list[str], pol: str) -> np.ndarray:
    out = None
    for t in tags:
        a = load_db(bid, t, pol)
        out = a if out is None else np.where(np.isfinite(out), out, a)
    return out


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
        # จับคู่ตามเลขวงโคจรสัมพัทธ์: อ้างอิง = ฉากล่าสุดของวงนั้นก่อน EVENT_START (รวมทุกชิ้นส่วนของวันนั้นเป็นภาพเดียว)
        refs = pre_event_references(bid)
        tracks = defaultdict(list)
        for tag, st in tags:
            tracks[rel_orbit(tag)].append((tag, st))
        summary[bid] = {"tracks": {}, "scenes": [], "unpaired": []}
        plain_km2 = round(float(lowland.sum()) * CELL_KM2, 1)
        for rel, group in sorted(tracks.items()):
            group.sort(key=lambda x: x[0])
            if rel not in refs:
                summary[bid]["unpaired"] += [g[0] for g in group]
                print(f"  {bid} [วง {rel}] ไม่มีฉากอ้างอิงก่อนเหตุการณ์ — ข้าม {len(group)} ฉาก", flush=True)
                continue
            ref_tags = refs[rel]
            pre_vh, pre_vv = mosaic_db(bid, ref_tags, "vh"), mosaic_db(bid, ref_tags, "vv")
            summary[bid]["tracks"][str(rel)] = {"reference": ref_tags[0], "reference_all": ref_tags}
            for tag, st in group:
                is_ref = tag in ref_tags              # ฉากอ้างอิงเอง = ไม่นับเป็นน้ำ (reference == scene ตามข้อตกลงเดิม)
                if is_ref:
                    w = np.zeros(lowland.shape, bool)
                else:
                    post_vh, post_vv = load_db(bid, tag, "vh"), load_db(bid, tag, "vv")
                    w = detect(pre_vh, post_vh, pre_vv, post_vv, lowland)
                km2 = round(float(w.sum()) * CELL_KM2, 1)
                np.save(out_dir / f"{tag}_water.npy", w)
                rec = {"basin": bid, "track": str(rel), "hhmm": hhmm(tag), "reference": tag if is_ref else ref_tags[0], "scene": tag,
                       "reference_all": ref_tags, "water_km2_lowland": km2, "plain_km2": plain_km2,
                       "water_frac_plain": round(km2 / plain_km2, 4) if plain_km2 else None,
                       "coverage": st.get("vh_valid_frac"), "satellite": tag[:3]}
                summary[bid]["scenes"].append(rec)
                (out_dir / f"{tag}_stats.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
                print(f"  {bid} [วง {rel}] {tag[12:26]} ref={ref_tags[0][12:26]} · น้ำ {km2} ตร.กม. "
                      f"({rec['water_frac_plain']:.1%} ที่ราบ)", flush=True)
        # MD สั้น
        lines = [f"# น้ำท่วม S1 — {bid} (กฎ canonical)", "",
                 f"> อ้างอิงต่อวงโคจรสัมพัทธ์ = ฉากล่าสุดก่อน 24 ก.ย. (ไม่ใช้ HH:MM เป็นตัวแทน) · กฎ ΔVH≤−0.5/ΔVV≤−1.5/VH≤−20 + opening 3×3 ใน lowland <60 ม.",
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