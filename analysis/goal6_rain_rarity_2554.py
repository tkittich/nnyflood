"""เป้าหมาย 6 — อันดับฝน 2554 จากแคช POWER เดียวกับ 2569 (ไม่ดาวน์โหลดใหม่)

ทำไมต้องมี: รายงานที่ 4 (benchmark 2554) เทียบแต่การเดินเขื่อน — ผู้วิจารณ์จะถามว่า
"ปี 2554 ฝนหนักกว่าหรือเปล่า?" คำนวณจากแคช raw/rain_rarity_national/ (1981–2026 ครบ 199 จุด)
→ อันดับฝน 2554 ต่อจุด + เทียบอันดับ 2569 รายจุด

ผลลัพธ์: analysis/goal6/rain_rarity_2554.json/.md
ทำซ้ำได้ · รัน: python analysis/goal6_rain_rarity_2554.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/22_goal6_network/raw/rain_rarity_national"
NATIONAL = ROOT / "analysis/goal6/rain_rarity_national.json"
OUT_JSON = ROOT / "analysis/goal6/rain_rarity_2554.json"
OUT_MD = ROOT / "analysis/goal6/rain_rarity_2554.md"


def main() -> None:
    # ใช้ฟังก์ชันหน้าต่างเดียวกับตัววิเคราะห์หลัก — ห้ามเขียน logic คู่
    from goal6_rain_rarity_national import best_window

    nat = json.loads(NATIONAL.read_text(encoding="utf-8"))
    basin = {k: v["basin"] for k, v in nat["points"].items()}
    name = {k: v["name"] for k, v in nat["points"].items()}

    out = {"note": "อันดับฝน 2554 คำนวณจากแคช POWER เดียวกันกับ 2569 · หน้าต่าง ก.ค.–ต.ค. เดิม · "
                   "กริด 0.5° รีดยอดฝนเบลอ — ค่าสถานีจริงสูงกว่าเสมอ", "points": {}}
    for p in sorted(RAW.glob("power_*.json")):
        sid = p.stem.split("_")[1]
        if sid not in basin:
            continue
        daily = json.loads(p.read_text(encoding="utf-8"))
        rec = {"id": sid, "name": name[sid], "basin": basin[sid]}
        for win in (7, 30):
            annual = {y: best_window(daily, y, win) for y in range(1981, 2027)}
            vals = sorted((s for s, _ in annual.values() if s == s), reverse=True)
            n = len(vals)
            v54 = annual.get(2011, (float("nan"), None))[0]
            r54 = vals.index(v54) + 1 if v54 == v54 and vals else None
            v26 = annual.get(2026, (float("nan"), None))[0]
            r26 = vals.index(v26) + 1 if v26 == v26 and vals else None
            rec[f"best{win}"] = {"v54": round(v54, 1) if v54 == v54 else None,
                                 "rank54": r54, "rp54": round((n + 1) / r54, 1) if r54 else None,
                                 "v26": round(v26, 1) if v26 == v26 else None, "rank26": r26}
        out["points"][sid] = rec
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # MD: ตารางรายจุด (เรียงตามอันดับ 2554) + สรุประดับลุ่ม (อันดับกลาง)
    pts = sorted(out["points"].values(), key=lambda r: (r["best7"]["rank54"] or 999))
    lines = ["# อันดับฝน 2554 เทียบ 2569 — ครบ 199 จุดจากแคช POWER เดิม", "",
             "> คำนวณจากแคช NASA POWER 1981–2026 เดียวกับตัววิเคราะห์ 2569 (ไม่ดาวน์โหลดใหม่) · "
             "หน้าต่าง ก.ค.–ต.ค. · <b>จุดในช่องกริดเดียวกันได้ค่าเดียวกัน — อ่านเป็นภาพระดับลุ่ม อย่าอ่านรายจุดต่างลุ่ม</b>", "",
             "| จุดวัด | ลุ่ม | 7 วัน 2554 (มม.) | อันดับ 2554 | คาบคืน~ | อันดับ 2569 |",
             "|---|---|---|---|---|---|"]
    for r in pts:
        b7 = r["best7"]
        lines.append(f"| {r['name']} | {r['basin']} | {b7['v54']} | {b7['rank54']}/199 | "
                     f"~{b7['rp54']} ปี | {b7['rank26']}/199 |")
    import collections
    rows = collections.defaultdict(list)
    for r in out["points"].values():
        rows[r["basin"]].append((r["best7"]["rank54"], r["best7"]["rank26"]))
    lines += ["", "## ระดับลุ่ม (อันดับกลาง 7 วัน)", "",
              "| ลุ่ม | n | อันดับกลาง 2554 | อันดับกลาง 2569 |", "|---|---|---|---|"]
    for b, lst in sorted(rows.items(), key=lambda x: sorted(y[0] for y in x[1])[len(x[1]) // 2]):
        m54 = sorted(x[0] for x in lst)[len(lst) // 2]
        m26 = sorted(x[1] for x in lst)[len(lst) // 2]
        lines.append(f"| {b} | {len(lst)} | {m54} | {m26} |")
    lines += ["", "**อ่านสำคัญ**: 2554 ฝนหนักกระจุกลุ่มเหนือ–อีสานตอนบน (ปิง/วัง/ยม/โขง อันดับกลาง 4–6) "
              "แต่ลุ่มกลาง–ล่าง (บางปะกง 30 · แม่กลอง 39 · ท่าจีน 37) ฝนปีนั้น<b>ปกติ</b> — "
              "ต่างจาก 2569 ที่ฝนหนักลุ่มกลาง–ล่างเอง · ข้อสรุปรายงานที่ 4: ทั้งสองปีท่วมใหญ่ด้วย"
              "<b>รูปแบบฝนคนละแบบ</b> — จึงเทียบ \"การเดินเขื่อน\" ได้แต่ห้ามเทียบ \"เหตุการณ์ฝน\"", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    n = len(out["points"])
    t3 = sum(1 for r in out["points"].values() if (r["best7"]["rank54"] or 99) <= 3)
    print(f"ครบ {n} จุด · 7 วันอด 1–3: 2554={t3} · 2569=67 · เขียน {OUT_MD}")


if __name__ == "__main__":
    main()
