"""เป้าหมาย 6 — สรุปผล screen หน้าฝน 2569 ต่อลุ่ม -> analysis/goal6_screen_2026_findings.md

อ่าน analysis/goal6_screen_2026_summary.json (จาก goal6_screen_basins.py) แล้วจัดชั้น:
- EVENT  = เกินวิกฤตเชิงเหตุการณ์ (run ต่อเนื่องไม่กลืนทั้งหน้าต่าง)
- SUSPECT= เกินตลอดหน้าต่าง (hours_over_crit == n_values) — เกณฑ์ datum ไม่ตรงกับอนุกรม
           (ตรวจซ้ำด้วย max_vs_minbank < 0 ที่เกือบทั้งหมด — บทเรียน datum นครนายก)
รัน: python analysis/goal6_screen_findings.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "analysis/goal6_screen_2026_summary.json"
FINDINGS = ROOT / "analysis/goal6_screen_2026_findings.md"


def main() -> None:
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    crit = [x for x in s["stations"] if x.get("crit") is not None and (x.get("hours_over_crit") or 0) > 0]
    # M10 (รีวิว Sift/Gemini): เพิ่มเกณฑ์ SUSPECT แบบบางส่วน — ระดับสูงสุดต่ำกว่าตลิ่งต่ำสุดของจุดตัวเอง
    # แปลว่าพิกัด/เกณฑ์วิกฤตกับอนุกรมคนละระบบ แม้ไม่ใช่ทั้งอนุกรม (เดิมจับเฉพาะเคสเต็มอนุกรม
    # → B.10 ตลาดท่ายาง (max 9.44 < ตลิ่งต่ำสุด 13.90) หลุดเป็น EVENT ทั้งที่ datum ไม่ตรง)
    for x in crit:
        n, h, r = x["n_values"], x["hours_over_crit"], x["longest_run_over_crit_h"]
        whole = h == n and r == n
        partial = x.get("meta_min_bank") is not None and x.get("max_val") is not None \
            and x["max_val"] < x["meta_min_bank"]
        x["class"] = "SUSPECT" if (whole or partial) else "EVENT"
        x["class_reason"] = ("datum_mismatch_whole_record" if whole
                             else "datum_mismatch_partial_below_min_bank" if partial else "ok")

    events = sorted([x for x in crit if x["class"] == "EVENT"], key=lambda y: -(y["hours_over_crit"]))
    suspects = sorted([x for x in crit if x["class"] == "SUSPECT"], key=lambda y: y["basin"])
    dams = s["dams"]
    urc_ok = [d for d in dams if (d.get("urc_points") or 0) > 0]
    over = sorted([d for d in urc_ok if (d.get("days_over_urc_sep_oct") or 0) > 0], key=lambda y: -y["days_over_urc_sep_oct"])
    no_urc = [d for d in dams if (d.get("urc_points") or 0) == 0]
    peaks = [x for x in s["stations"] if x.get("max_dt") and x["max_dt"] >= "2026-09-20"]

    lines = [
        "# screen หน้าฝน 2569 ต่อลุ่ม — ผลและข้อเสนอรอบแรก",
        "",
        f"> สร้างโดย `analysis/goal6_screen_findings.py` จาก `goal6_screen_2026_summary.json` · "
        f"หน้าต่าง {s['window'][0]}..{s['window'][1]} · เกณฑ์ pre-register 10 ต.ค. 2569 "
        f"(จุดวัด {len(s['stations'])} จุด = key หรือมีเกณฑ์ทางการ, เขื่อนผู้สมัคร 24 แห่ง)",
        "",
        "## 1. ข้อสังเกตหลัก",
        "",
        f"- **จุดเกินวิกฤต {len(crit)} จุด แต่ใช้เป็นเกณฑ์เหตุการณ์ได้จริงแค่ {len(events)} จุด** — "
        f"อีก {len(suspects)} จุดเกินตลอดหน้าต่างและระดับสูงสุด**ต่ำกว่าตลิ่งต่ำสุด**ของจุดตัวเอง "
        "(max − min_bank เป็นลบเกือบทั้งหมด) = เกณฑ์ critical_level_m ใน API คนละ datum กับอนุกรม "
        "→ บทเรียนเดียวกับ datum นครนายก (เกจ ≠ ม.รทก.) · ใช้ต้อง QA datum รายจุดก่อน",
        f"- **เวลาที่ระดับสูงสุดใช้ได้ทุกจุด (datum-independent)**: จุดเกินวิกฤตทุกจุดมีพีคช่วง "
        "23 ก.ย.–9 ต.ค. 69 → ระลอกปลาย ก.ย. เป็นเหตุการณ์ระดับชาติ (ระลอกเดียวกับนครนายก 27 ก.ย.)",
f"- **เขื่อนเกิน URC ช่วง ก.ย.–ต.ค.: {len(over)} แห่ง** จาก {len(urc_ok)} แห่งที่ API มี URC — "
        f"**ป่าสักชลสิทธิ์/แก่งกระจาน/แม่งัดสมบูรณ์ชล/ขุนด่านฯ เกิน 39 วัน = ทั้งหน้าต่าง** · "
        f"แห่งที่ไม่มี URC เลย: {', '.join(d['name'] for d in no_urc) or '—'} (รันออฟริเวอร์) · "
        "⚠️ ค่า URC ใน API เป็นเทมเพลตแหล่งเดียว (ลงวันที่ปี 2020 แบบรายเดือน-วัน) — "
        "เขื่อน กฟผ. ที่สรุปว่า \"ไม่เกิน\" ยังต้องตรวจไขว้ URC ฉบับทางการของ กฟผ. ก่อนใช้เชิงวิชาการ",
        "- ตัวเลขยืนยันความถูกต้องของ pipeline: ขุนด่านฯ เก็บสูงสุด **224.34 @ 27 ก.ย.** และปล่อยสูงสุด "
        "**31.66 @ 27 ก.ย.** = ตรง canonical นครนายกเป๊ะ · Ny.7 max 9.23 @ 27 ก.ย. 10:00 ✓",
        "",
        "## 2. จุดวัดชั้น EVENT (ใช้เป็นหลักฐานเหตุการณ์ได้)",
        "",
        "| ลุ่มน้ำ | จุดวัด | เกินวิกฤต (ชม.) | run ต่อเนื่อง | ระดับสูงสุด | เวลาพีค | เหนือตลิ่งต่ำสุด |",
        "|---|---|---|---|---|---|---|",
    ]
    for x in events:
        gap = x.get("max_vs_minbank")
        gap_s = f"{gap:+.2f} ม." if gap is not None else "—"
        lines.append(
            f"| {x['basin']} | {x['code']} {x['name'][:24]} | {x['hours_over_crit']} | "
            f"{x['longest_run_over_crit_h']} | {x['max_val']:.2f} | {x['max_dt']} | {gap_s} |"
        )
    lines += [
        "",
        "## 3. จุดที่เกณฑ์วิกฤตใช้ไม่ได้ (SUSPECT — QA datum ก่อนใช้)",
        "",
        "| ลุ่มน้ำ | จุดวัด | crit(API) | ระดับสูงสุด | เวลาพีค | max − min_bank |",
        "|---|---|---|---|---|---|",
    ]
    for x in suspects:
        gap = x.get("max_vs_minbank")
        gap_s = f"{gap:+.2f} ม." if gap is not None else "—"
        lines.append(
            f"| {x['basin']} | {x['code']} {x['name'][:24]} | {x['crit']} | "
            f"{x['max_val']:.2f} | {x['max_dt']} | {gap_s} |"
        )
    lines += [
        "",
        "> แม้เกณฑ์ใช้ไม่ได้ **เวลาพีคยังเป็นสัญญาณเหตุการณ์จริง** (ตารางคอลัมน์เวลาพีค) — "
        "ใช้เป็นหลักฐานเชิงเวลา ไม่ใช่เชิงระดับ จนกว่าจะ QA datum เสร็จ",
        "",
        "## 4. เขื่อนผู้สมัคร 24 แห่ง ช่วง ก.ย.–ต.ค. 69",
        "",
        "| เขื่อน | ลุ่มน้ำ | เกิน URC (วัน) | เก็บสูงสุด | วันที่ | ปล่อยสูงสุด | วันที่ | URC ใน API |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for d in sorted(dams, key=lambda y: (-(y.get("days_over_urc_sep_oct") or 0), -y["normal_storage"])):
        lines.append(
            f"| {d['name']} | {d['basin']} | {d.get('days_over_urc_sep_oct', '—')} | "
            f"{d.get('sep_oct_max_storage', '—')} | {d.get('sep_oct_max_storage_dt', '')} | "
            f"{d.get('max_release', '—')} | {d.get('max_release_dt', '')} | "
            f"{'มี' if (d.get('urc_points') or 0) > 0 else 'ไม่มี'} |"
        )
    lines += [
        "",
        f"- จุดวัดรวมที่มีพีคตั้งแต่ 20 ก.ย.: {len(peaks)} จุดจาก {len(s['stations'])} · "
        "raw หลักฐาน: `data/22_goal6_network/raw/wl_screen_2026/` (จุด EVENT) + `dam_screen_2026/` (ทุกเขื่อน)",
        "",
        "## 5. ข้อเสนอลุ่มรอบแรก",
        "",
        "**✅ ผู้ใช้ยืนยัน 10 ต.ค. 2569: รอบแรก = ทั้ง 5 ลุ่ม** (บางปะกง–ปราจีนบุรี เลื่อนเป็นลุ่มเต็ม) · "
        "ต่อด้วย sweep ความพร้อมข้อมูล (`analysis/goal6_basin_readiness.py`) และ spike L1 ลุ่มแรก ป่าสัก",
        "",
        "คัดจากเกณฑ์ 4 ข้อ (GOAL6_PLAN §5) + ผล screen ข้างบน — เรียงตามความคุ้ม:",
        "",
        "| ลำดับ | ลุ่ม | หลักฐานเหตุการณ์ 2569 | เขื่อน | เหตุผลเชิงเปรียบเทียบ |",
        "|---|---|---|---|---|",
        "| 1 | **ป่าสัก** | เขื่อนเกิน URC 39 วัน · เก็บ 965 (110.7% เก็บปกติ) @ 4 ต.ค. · ปล่อยสูงสุด 43.2 ลลบ.ม./วัน @ 6 ต.ค. · S.26 เกินวิกฤต 18 ชม. | ป่าสักชลสิทธิ์ 872 ลลบ.ม. (ชป.) | ทางเดียวกับนครนายก · เทียบ \"เขื่อนใหญ่กว่า 4 เท่า\" ตรงสุด |",
        "| 2 | **แม่กลอง** | พีค 3 จุด 29–30 ก.ย. (K.3A/K.10/K.37 — เกณฑ์ datum เพี้ยน แต่เวลาพีคชัด) · แก่งกระจานเกิน URC 39 วัน ปล่อย 11.3 @ 4 ต.ค. | แก่งกระจาน 710 (ชป.) + ศรีนครินทร์ 17,745 + วชิราลงกรณ 8,860 (กฟผ. รายชั่วโมง — ยังปล่อย 40 ลลบ.ม./วัน 9 ต.ค.) | ทดสอบวิธีกับระบบ กฟผ. + cascade 2 เขื่อนใหญ่ |",
        "| 3 | **ปิง–เจ้าพระยาตอนบน** | P.17 พีค 30 ก.ย. · **C.2 ท่าเรือ พีค 24.1 @ 1 ต.ค. (ต่ำกว่าตลิ่ง 1.6 ม.)** | ภูมิพล 13,462 (กฟผ.) | ใหญ่สุดในประเทศ · ภูมิพลไม่เกิน URC ตามค่า API (ยังต้องตรวจไขว้ กฟผ. ฉบับทางการ) แต่ท้ายน้ำพีค 30 ก.ย.–1 ต.ค. = กรณีศึกษาตรงข้ามนครนายก · C.2 ดึงแล้ว 39,010 ชม. |",
        "| 4 | **ท่าจีน** | T.1 นครชัยศรี เกินวิกฤต 367 ชม. (EVENT ชัดสุด) พีค 2.33 (+0.83 ม. เหนือตลิ่ง) @ 30 ก.ย. | กระเสียว 299 (ชป. — เกิน URC 0 วัน) | ลุ่มที่ท่วมชัดแต่เขื่อนเล็ก = ทดสอบ attribution ฝน vs ปตร./ระบายธรรมชาติ |",
        "| ทางเลือก | บางปะกง–ปราจีนบุรี | Kgt.3 เกินวิกฤต 169 ชม. **เหนือตลิ่ง +3.37 ม.** · Kgt.1 307 ชม. · คลองสียัด/นฤบดินทรจินดา เกิน URC 14 วัน | คลองสียัด 420 + นฤบดินทรจินดา 295 | ลุ่มเดียวกับนครนายก — เสนอเป็นบทต่อยอดในรายงานที่ 3 มากกว่าลุ่มใหม่ |",
        "",
        "## 6. งานที่ต้องทำต่อหลังผู้ใช้ยืนยันรายชื่อลุ่ม",
        "",
        "1. QA datum จุดวัดหลักของแต่ละลุ่ม (ตาราง SUSPECT ข้อ 3 = คิวแรก) — เทียบเกจ/ม.รทก. แบบที่ทำในนครนายก",
        "2. ตรวจความพร้อม L1/L3: ดึงย้อนหลังสุดขีดของจุดเป้าหมาย (เดินปีถอยจน 2 ปีว่างต่อเนื่อง) + จุด กฟผ. ต้องหา URC เอกสาร",
        "3. เขื่อน ปากมูล (รันออฟริเวอร์ เก็บ 0 ตลอด) ตัดออกจากผู้สมัครเชิงเทียบ — จดไว้ใน manifest ผู้สมัคร",
        "",
    ]
    FINDINGS.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {FINDINGS} ({len(events)} EVENT / {len(suspects)} SUSPECT / {len(over)} เขื่อนเกิน URC / {len(no_urc)} ไม่มี URC)")


if __name__ == "__main__":
    main()