"""ตรวจความถูกต้องของกฎตัดน้ำ Sentinel-1 (รีวิว Sonnet 12 ต.ค. 69 · M1/R9) — ไม่ใช้ข้อมูลใหม่

คำถามที่ตอบ (ใช้กฎแช่แข็งเดิม ΔVH≤−0.5 & ΔVV≤−1.5 & VH≤−20 + opening 3×3 ใน lowland <60 ม. — ไม่ปรับค่า):
  A. ฉากควบคุม "ไม่ท่วม": คู่วงโคจรเดียวกันก่อนเหตุการณ์ (นครนายก 10→22 ก.ย. · ลุ่มอื่น 19→24 ก.ย.)
     ถ้ากฎรายงานน้ำ = ผลบวกเท็จ → พื้นที่ผลบวกเท็จต่อ 1,000 ตร.กม. ที่ฉากครอบ
  B. สัดส่วน "น้ำใหม่" ที่ฉากอ้างอิงมืดอยู่แล้ว (VH ≤ −20) = น้ำถาวร/น้ำที่มีอยู่เดิมที่หลุดเข้ามา
  C. ความไวต่อค่าเกณฑ์: เปลี่ยน ΔVH/ΔVV/VH เป็นช่วง → พื้นที่และ F1 เทียบ GISTDA เปลี่ยนเท่าไร
  D. ช่วงความไม่แน่นอนของ F1 (bootstrap เป็นแปลงเชิงพื้นที่ ~6×6 กม.)
ผลลัพธ์: analysis/goal6/s1_rule_validation.json + .md
รัน: python analysis/goal6_s1_rule_validation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import cell_km2  # noqa: E402
from s1_change_detect import detect, load_gistda_mask, prf  # noqa: E402
from goal6_s1_stage2_water import mosaic_db  # noqa: E402 — ภาพอ้างอิงรวมชิ้นส่วนของวันอ้างอิง (จับคู่ตามวงโคจรสัมพัทธ์)

ROOT = Path(__file__).resolve().parent.parent
DER = ROOT / "data/13_sentinel1_copernicus/derived"
ST1 = ROOT / "data/22_goal6_network/derived/s1_stage1"
ST2 = ROOT / "data/22_goal6_network/derived/s1_stage2"
OUT_JSON = ROOT / "analysis/goal6/s1_rule_validation.json"
OUT_MD = ROOT / "analysis/goal6/s1_rule_validation.md"


def L(name: str) -> np.ndarray:
    return np.load(DER / name)


def pair(pre: str, post: str, low: np.ndarray, **kw) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """คืน (mask, ฉากครอบ (ไม่นับ lowland), pre_vh)"""
    pv, qv = L(f"{pre}_vh_db.npy"), L(f"{post}_vh_db.npy")
    pw, qw = L(f"{pre}_vv_db.npy"), L(f"{post}_vv_db.npy")
    cover = np.isfinite(pv) & np.isfinite(qv) & np.isfinite(pw) & np.isfinite(qw)
    return detect(pv, qv, pw, qw, low, **kw), cover, pv


def union_ab(pre: str, post: str, low, **kw):
    """ฉากสองชิ้น (a,b) — รวมผลของแต่ละคู่ที่มีทั้ง pre/post"""
    w = cover = pv = None
    for sa in ("a", "b"):          # ทุกคู่ชิ้น (ก่อน × หลัง) — ชิ้น a/b ของแต่ละวันครอบพื้นที่ต่างกัน
        for sb in ("a", "b"):
            try:
                wi, ci, pi = pair(pre.format(sa), post.format(sb), low, **kw)
            except FileNotFoundError:
                continue
            w = wi if w is None else (w | wi)
            cover = ci if cover is None else (cover | ci)
            pv = pi if pv is None else np.where(np.isfinite(pi), pi, pv)
    return w, cover, pv


def block_bootstrap_f1(w, gis, cover, block=200, n=300, seed=0):
    """F1 + ช่วง 95% จากการสุ่มแปลงเชิงพื้นที่ (ลดการเกาะกลุ่มของพิกเซล)"""
    rng = np.random.default_rng(seed)
    ny, nx = w.shape
    by, bx = ny // block + 1, nx // block + 1
    tp = np.zeros((by, bx)); fp = np.zeros((by, bx)); fn = np.zeros((by, bx))
    for i in range(by):
        for j in range(bx):
            sl = (slice(i * block, (i + 1) * block), slice(j * block, (j + 1) * block))
            c = cover[sl]
            ww, gg = w[sl] & c, gis[sl] & c
            tp[i, j] = (ww & gg).sum(); fp[i, j] = (ww & ~gg).sum(); fn[i, j] = (~ww & gg & c).sum()
    ok = (tp + fp + fn) > 0
    idx = np.argwhere(ok)
    f1s = []
    for _ in range(n):
        s = idx[rng.integers(0, len(idx), len(idx))]
        t, f, m = tp[s[:, 0], s[:, 1]].sum(), fp[s[:, 0], s[:, 1]].sum(), fn[s[:, 0], s[:, 1]].sum()
        p, r = t / max(t + f, 1), t / max(t + m, 1)
        f1s.append(2 * p * r / max(p + r, 1e-9))
    return float(np.percentile(f1s, 2.5)), float(np.percentile(f1s, 97.5))


def main() -> None:
    g = json.load(open(DER / "grid.json"))
    cell = cell_km2(g["res"])
    low = L("mask_lowland.npy")
    gis = load_gistda_mask(g)
    res: dict = {"rule": "ΔVH≤−0.5 & ΔVV≤−1.5 & VH≤−20 + opening 3×3, lowland<60 ม. (แช่แข็ง)", "nakhonnayok": {}, "basins": {}}

    # ---- A. ควบคุมนครนายก ----
    # คู่ก่อนท่วมที่ครอบที่ราบจริงมีคู่เดียว: S1D 15 ก.ย. 06:00 → S1C 21 ก.ย. 06:00 (วงโคจรเดียวกัน ห่าง 6 วัน
    # ฝนปานกลางเข้าสู่ช่วงอิ่มตัว · GISTDA 22 ก.ย. = ไม่มีน้ำท่วม) — คู่ 18:20 ครอบเฉพาะภูเขา (ที่ราบ 0%)
    ctrl = {}
    w, cover, pv = pair("s1d_20260915_0600_a", "s1c_20260921_0600", low)
    cl = float((cover & low).sum() * cell)
    ctrl["S1D 15 ก.ย. 06:00 → S1C 21 ก.ย. 06:00 (ก่อนท่วม)"] = {
        "false_pos_km2": round(float(w.sum() * cell), 2), "covered_lowland_km2": round(cl, 1),
        "per_1000_km2": round(float(w.sum() * cell) / max(cl, 1) * 1000, 2),
        "note": "ฉากควบคุมที่ครอบที่ราบมีคู่เดียว (~19% ของที่ราบ) — คู่ 10→22 ก.ย. 18:20 ครอบเฉพาะภูเขา"}
    res["nakhonnayok"]["control_pairs"] = ctrl

    # ---- ฉากน้ำท่วม 2 คู่ ----
    flood_pairs = {
        "peak_27sep": ("s1d_20260915_1828_full", "s1d_20260927_1828_full"),
        "oct2": ("s1d_20260920_0609", "s1d_20261002_0609"),
    }
    sens_rows = []
    for key, (pre, post) in flood_pairs.items():
        w, cover, pv = pair(pre, post, low)
        area = float(w.sum() * cell)
        dark_share = float((w & (pv <= -20.0)).sum() / max(w.sum(), 1))
        pr, rc, f1 = prf(w & cover, gis & cover)
        lo, hi = block_bootstrap_f1(w, gis, cover)
        res["nakhonnayok"][key] = {
            "area_km2": round(area, 1), "precision": round(float(pr), 3), "recall": round(float(rc), 3), "f1": round(float(f1), 3),
            "f1_ci95": [round(lo, 3), round(hi, 3)],
            "area_ratio_vs_gistda_pass": round(area / float((gis & cover).sum() * cell), 2),
            "share_new_water_already_dark_in_reference": round(dark_share, 3),
        }
        # ---- C. ความไว ----
        for dvh in (0.0, 0.5, 1.0, 2.0, 3.0):
            for dvv in (0.5, 1.5, 3.0):
                for ab in (-18.0, -20.0, -22.0):
                    ws, _, _ = pair(pre, post, low, drop_vh=dvh, drop_vv=dvv, abs_vh=ab)
                    p2, r2, f2 = prf(ws & cover, gis & cover)
                    sens_rows.append({"scene": key, "drop_vh": dvh, "drop_vv": dvv, "abs_vh": ab,
                                      "area_km2": round(float(ws.sum() * cell), 1), "f1": round(float(f2), 3)})
    res["nakhonnayok"]["sensitivity"] = sens_rows
    for key in flood_pairs:
        rows = [r for r in sens_rows if r["scene"] == key]
        res["nakhonnayok"][key]["sensitivity_area_range_km2"] = [min(r["area_km2"] for r in rows), max(r["area_km2"] for r in rows)]
        res["nakhonnayok"][key]["sensitivity_f1_range"] = [min(r["f1"] for r in rows), max(r["f1"] for r in rows)]
        best = max(rows, key=lambda r: r["f1"])
        res["nakhonnayok"][key]["best_f1_setting"] = best

    # ---- ลุ่มอื่น (stage-2): ฉากควบคุม 24 ก.ย. + สัดส่วนน้ำที่มืดอยู่แล้วในฉากอ้างอิง ----
    summ = json.loads((ST2 / "summary.json").read_text(encoding="utf-8"))
    for bid, rec in summ.items():
        grid = json.loads((ST1 / f"grid_{bid}.json").read_text(encoding="utf-8"))
        cb = cell_km2(grid.get("res", 0.00027)) if "res" in grid else 0.0009
        lowb = np.load(ST1 / f"mask_lowland_{bid}.npy")
        scenes = [r for r in rec["scenes"] if r["reference"] != r["scene"]]
        out = {"controls": [], "events": []}
        for r in scenes:
            water_p = ST2 / bid / f"{r['scene']}_water.npy"
            if not water_p.exists():
                continue
            w = np.load(water_p)
            post, pre = mosaic_db(bid, r["slices"], "vh"), mosaic_db(bid, r["reference_all"], "vh")
            cov_low = float((np.isfinite(post) & np.isfinite(pre) & lowb).sum() * 0.0009)
            entry = {"scene": r["scene"][12:40], "water_km2": round(float(w.sum() * 0.0009), 1),
                     "covered_lowland_km2": round(cov_low, 1),
                     "share_already_dark_in_reference": round(float((w & (pre <= -20.0)).sum() / max(w.sum(), 1)), 3)
                     if w.sum() else None}
            date = r["scene"][17:25]
            entry["date"] = date
            entry["net_new_km2"] = round(entry["water_km2"] * (1 - (entry["share_already_dark_in_reference"] or 0)), 1)
            # ฉากควบคุม = ก่อนเหตุการณ์ใหญ่ (≤ 24 ก.ย.) และมีฉากครอบที่ราบจริง
            (out["controls"] if date <= "20260924" and cov_low > 0 else out["events"]).append(entry)
        cc = sum(c["covered_lowland_km2"] for c in out["controls"])
        out["control_summary"] = {"frames": len(out["controls"]), "covered_lowland_km2": round(cc, 1),
                                  "false_pos_km2": round(sum(c["water_km2"] for c in out["controls"]), 2),
                                  "per_1000_km2": round(sum(c["water_km2"] for c in out["controls"]) / cc * 1000, 3) if cc else None}
        res["basins"][bid] = out

    OUT_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- MD สรุป ----
    n = res["nakhonnayok"]
    md = ["# ตรวจกฎตัดน้ำ Sentinel-1 — ผลบวกเท็จ · น้ำเดิม · ความไวเกณฑ์ · ช่วง F1", "",
          "> กฎแช่แข็งเดิม ไม่ปรับค่า · สคริปต์ `analysis/goal6_s1_rule_validation.py` · ข้อมูลที่มีในโครงการเท่านั้น", "",
          "## A. ฉากควบคุม (ไม่ท่วม) — นครนายก", "", "| คู่ | น้ำที่กฎรายงาน (ผลบวกเท็จ) ตร.กม. | ฉากครอบที่ราบ ตร.กม. | ต่อ 1,000 ตร.กม. |", "|---|---|---|---|"]
    for k, v in n["control_pairs"].items():
        md.append(f"| {k} | {v['false_pos_km2']} | {v['covered_lowland_km2']} | {v['per_1000_km2']} |")
    md += ["", "## B–D. ฉากท่วมนครนายก เทียบ GISTDA (ผลิตภัณฑ์ 28 ก.ย.–2 ต.ค.)", "",
           "| ฉาก | พื้นที่ ตร.กม. | P | R | F1 | F1 ช่วง 95% | น้ำใหม่ที่มืดอยู่แล้วในฉากอ้างอิง | พื้นที่ช่วงตามเกณฑ์ที่ปรับ | F1 ช่วง |", "|---|---|---|---|---|---|---|---|---|"]
    for k in ("peak_27sep", "oct2"):
        v = n[k]
        md.append(f"| {k} | {v['area_km2']} | {v['precision']} | {v['recall']} | {v['f1']} | {v['f1_ci95'][0]}–{v['f1_ci95'][1]} | "
                  f"{v['share_new_water_already_dark_in_reference']:.1%} | {v['sensitivity_area_range_km2'][0]}–{v['sensitivity_area_range_km2'][1]} | "
                  f"{v['sensitivity_f1_range'][0]}–{v['sensitivity_f1_range'][1]} |")
    md += ["", "## ลุ่มอื่น (stage-2) — สัดส่วนน้ำที่ฉากอ้างอิงมืดอยู่แล้ว", "",
           "| ลุ่ม | ฉากน้ำสูงสุด ตร.กม. | % มืดอยู่แล้ว | ฉากควบคุม (n) · ผลบวกเท็จรวม ตร.กม. |", "|---|---|---|---|"]
    for bid, v in res["basins"].items():
        if not v["events"]:
            continue
        pk = max(v["events"], key=lambda e: e["water_km2"])
        fp = round(sum(c["water_km2"] for c in v["controls"]), 1)
        cs = v["control_summary"]
        md.append(f"| {bid} | {pk['water_km2']} (สุทธิใหม่ {pk['net_new_km2']}) | {pk['share_already_dark_in_reference']:.1%} | "
                  f"{cs['frames']} ฉาก ครอบ {cs['covered_lowland_km2']} ตร.กม. · ผลบวกเท็จ {cs['false_pos_km2']} ({cs['per_1000_km2']}/1,000) |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in n.items() if k != "sensitivity"}, ensure_ascii=False, indent=1))
    for bid, v in res["basins"].items():
        pk = max(v["events"], key=lambda e: e["water_km2"]) if v["events"] else None
        print(bid, "controls", len(v["controls"]), "peak", pk)


if __name__ == "__main__":
    main()
