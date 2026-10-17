#!/usr/bin/env python3
"""analysis/goal2_nny_medium_dams.py — วิเคราะห์บทบาทอ่างเก็บน้ำขนาดกลาง 6 แห่งใน จ.นครนายก ช่วงน้ำท่วม 2569

คำถามวิจัย:
1. อ่างเก็บน้ำขนาดกลาง 6 แห่งของนครนายก (ห้วยปรือ, คลองสีเสียด, คลองโบด, ทรายทอง, คลองวังบอน, คลองกลาง)
   มีความจุรวมเท่าใด และคิดเป็นสัดส่วนเท่าใดเมื่อเทียบกับเขื่อนขุนด่านปราการชล?
2. ในช่วงน้ำท่วมพีค 26–29 ก.ย. 2569 อ่างใดบ้างที่น้ำเต็มความจุ (>100%) และมีการระบาย/ล้นออกปริมาณเท่าใด?
3. ลำน้ำสาขาและพื้นที่ท้ายน้ำใดบ้างที่ได้รับผลกระทบจากน้ำล้นของอ่างขนาดกลาง (เช่น ต.เขาพระ, อ.ปากพลี)?
4. ประวัติศาสตร์ 18 ปี (2552–2569 / 2009–2026): ความถี่ของการที่อ่างขนาดกลางน้ำเต็มล้น 100% ในฤดูฝนเป็นอย่างไร?

แหล่งข้อมูล:
- data/23_rid_swoc/raw/nny_medium_dams_2026.json (ช่วงเหตุการณ์ 2569)
- data/23_rid_swoc/raw/nny_medium_dams_history_2009_2026.json (ประวัติศาสตร์ 18 ปี)
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_2026 = ROOT / "data" / "23_rid_swoc" / "raw" / "nny_medium_dams_2026.json"
DATA_HIST = ROOT / "data" / "23_rid_swoc" / "raw" / "nny_medium_dams_history_2009_2026.json"
OUT_JSON = ROOT / "analysis" / "goal2_nny_medium_dams_summary.json"
OUT_MD = ROOT / "analysis" / "goal2_nny_medium_dams_report.md"

SUBBASIN_INFO = {
    "rsv380": {
        "receiving_stream": "คลองห้วยปรือ / คลองท่าด่าน",
        "downstream_area": "ต.เขาพระ, ต.สาริกา อ.เมืองนครนายก",
        "role": "อ่างขนาดกลางที่ใหญ่ที่สุด กักน้ำหลากได้ดี (หน่วงน้ำ 86.4%)",
    },
    "rsv381": {
        "receiving_stream": "คลองสีเสียด",
        "downstream_area": "ต.หนองแสง อ.ปากพลี",
        "role": "อ่างขนาดเล็ก กักน้ำได้เกือบทั้งหมด (ระบายออกน้อยมาก)",
    },
    "rsv382": {
        "receiving_stream": "คลองโบด / คลองเหมือง",
        "downstream_area": "ต.พรหมณี อ.เมืองนครนายก",
        "role": "น้ำในอ่างน้อย (17%) มีช่องว่างรับน้ำเหลือเฟือ",
    },
    "rsv383": {
        "receiving_stream": "คลองทรายทอง",
        "downstream_area": "ต.เขาพระ, เทศบาลเมืองนครนายก",
        "role": "น้ำเต็ม 100% ตั้งแต่ก่อนฝนตกหนัก น้ำหลากล้นผ่าน 99.5% ซ้ำเติมน้ำท่วม ต.เขาพระ",
    },
    "rsv384": {
        "receiving_stream": "คลองวังบอน",
        "downstream_area": "ต.นาหินลาด, อ.ปากพลี",
        "role": "น้ำเต็ม 100% ตลอดช่วง ระบาย/ล้นออกต่อเนื่องลงสู่ อ.ปากพลี",
    },
    "rsv386": {
        "receiving_stream": "คลองกลาง",
        "downstream_area": "ต.นาหินลาด, อ.ปากพลี",
        "role": "กักเก็บน้ำได้ 100% ไม่ปล่อยน้ำออกเลยในช่วงพีค 26–28 ก.ย. ช่วยหน่วงน้ำ อ.ปากพลี",
    },
}


def analyze():
    assert DATA_2026.exists(), f"ไม่พบไฟล์ {DATA_2026}"
    raw_2026 = json.loads(DATA_2026.read_text(encoding="utf-8"))["reservoirs"]
    
    # คำนวณความถี่ 18 ปีจาก DATA_HIST ถ้ามี
    hist_stats = {}
    if DATA_HIST.exists():
        raw_hist = json.loads(DATA_HIST.read_text(encoding="utf-8"))["reservoirs"]
        for cresv, r in raw_hist.items():
            cap = r["info"]["capacity_mcm"]
            by_y = {}
            for row in r["data"]:
                y = row["date"][:4]
                by_y.setdefault(y, []).append(row)
            
            over_years = sum(1 for y_rows in by_y.values() if max(float(x.get("qdisc_curr") or 0) for x in y_rows) >= cap)
            total_years = len(by_y)
            hist_stats[cresv] = {
                "total_years": total_years,
                "overflow_years": over_years,
                "overflow_pct": round((over_years / total_years) * 100, 1) if total_years else 0,
            }

    khundan_cap = 224.0  # ล้าน ลบ.ม. (active capacity)
    
    summary = {
        "metadata": {
            "title": "การวิเคราะห์อ่างเก็บน้ำขนาดกลาง 6 แห่ง จ.นครนายก เหตุการณ์ 26–29 ก.ย. 2569",
            "source": "SWOC RID (app.rid.go.th/reservoir)",
            "unit_storage": "ล้าน ลบ.ม. (MCM)",
            "unit_flow": "ล้าน ลบ.ม./วัน (MCM/day)",
        },
        "system_totals": {
            "khundan_capacity_mcm": khundan_cap,
            "medium_reservoirs_count": len(raw_2026),
            "total_medium_capacity_mcm": 0.0,
            "medium_to_khundan_pct": 0.0,
        },
        "event_26_29_sep": {
            "total_inflow_mcm": 0.0,
            "total_outflow_mcm": 0.0,
            "net_retention_mcm": 0.0,
            "retention_efficiency_pct": 0.0,
        },
        "reservoir_details": {},
    }
    
    total_cap = 0.0
    total_in = 0.0
    total_out = 0.0
    
    for cresv, rdata in raw_2026.items():
        info = rdata["info"]
        cap = info["capacity_mcm"]
        total_cap += cap
        
        event_days = [d for d in rdata["data"] if d["date"] in ["2026-09-26", "2026-09-27", "2026-09-28", "2026-09-29"]]
        
        r_inflow = sum(float(d.get("q_info", 0) or 0) for d in event_days)
        r_outflow = sum(float(d.get("q_outfo", 0) or 0) for d in event_days)
        max_storage = max(float(d.get("qdisc_curr", 0) or 0) for d in event_days)
        max_pct = max(float(d.get("percent_resv_curr", 0) or 0) for d in event_days)
        
        total_in += r_inflow
        total_out += r_outflow
        
        sub_info = SUBBASIN_INFO.get(cresv, {})
        h_info = hist_stats.get(cresv, {})
        
        retention = r_inflow - r_outflow
        summary["reservoir_details"][cresv] = {
            "name": info["name"],
            "amphoe": info["amphoe"],
            "capacity_mcm": cap,
            "receiving_stream": sub_info.get("receiving_stream", "-"),
            "downstream_area": sub_info.get("downstream_area", "-"),
            "hydrological_role": sub_info.get("role", "-"),
            "peak_storage_mcm": round(max_storage, 3),
            "peak_storage_pct": round(max_pct, 1),
            "is_overflow": max_pct >= 100.0,
            "event_inflow_4days_mcm": round(r_inflow, 3),
            "event_outflow_4days_mcm": round(r_outflow, 3),
            "net_retention_4days_mcm": round(retention, 3),
            "retention_pct": round((retention / r_inflow) * 100, 1) if r_inflow > 0 else 0,
            "18y_overflow_stat": h_info,
            "daily": {
                d["date"]: {
                    "storage_mcm": float(d.get("qdisc_curr", 0) or 0),
                    "storage_pct": float(d.get("percent_resv_curr", 0) or 0),
                    "inflow_mcm_day": float(d.get("q_info", 0) or 0),
                    "outflow_mcm_day": float(d.get("q_outfo", 0) or 0),
                }
                for d in event_days
            },
        }

    summary["system_totals"]["total_medium_capacity_mcm"] = round(total_cap, 2)
    summary["system_totals"]["medium_to_khundan_pct"] = round((total_cap / khundan_cap) * 100, 1)
    
    summary["event_26_29_sep"]["total_inflow_mcm"] = round(total_in, 3)
    summary["event_26_29_sep"]["total_outflow_mcm"] = round(total_out, 3)
    net_ret = total_in - total_out
    summary["event_26_29_sep"]["net_retention_mcm"] = round(net_ret, 3)
    summary["event_26_29_sep"]["retention_efficiency_pct"] = round((net_ret / total_in) * 100, 1) if total_in > 0 else 0

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # สร้าง Markdown Report
    md = [
        "# รายงานผลการวิเคราะห์อ่างเก็บน้ำขนาดกลาง 6 แห่ง จ.นครนายก เหตุการณ์น้ำท่วม 2569",
        "",
        "> แหล่งข้อมูล: [SWOC กรมชลประทาน](https://app.rid.go.th/reservoir/) (`data/23_rid_swoc/`)  ",
        f"> อ้างอิงตัวเลขสรุป: `{OUT_JSON.name}`",
        "",
        "## 1. ภาพรวมโครงสร้างความจุในลุ่มน้ำ",
        "",
        f"- **เขื่อนขุนด่านปราการชล (เขื่อนใหญ่)**: ความจุใช้การ {khundan_cap:.1f} ล้าน ลบ.ม.",
        f"- **อ่างเก็บน้ำขนาดกลาง 6 แห่ง**: ความจุรวม **{total_cap:.2f} ล้าน ลบ.ม.** (คิดเป็น **{summary['system_totals']['medium_to_khundan_pct']}%** ของเขื่อนขุนด่านฯ)",
        "- **บทบาทภาพรวมช่วงน้ำท่วมพีค 4 วัน (26–29 ก.ย. 2569)**:",
        f"  - ปริมาณน้ำไหลเข้า 6 อ่าง: **{total_in:.3f} ล้าน ลบ.ม.**",
        f"  - ปริมาณน้ำระบาย/ล้นออก: **{total_out:.3f} ล้าน ลบ.ม.**",
        f"  - **กักเก็บน้ำหลากไว้ได้สุทธิ: {net_ret:.3f} ล้าน ลบ.ม. (หน่วงน้ำได้ {summary['event_26_29_sep']['retention_efficiency_pct']}%)**",
        "",
        "## 2. ตารางพฤติกรรมรายอ่างช่วงเหตุการณ์ 26–29 ก.ย. 2569",
        "",
        "| อ่างเก็บน้ำ | อำเภอ | ลำน้ำรับน้ำ / พื้นที่ท้ายน้ำ | ความจุ (ลลบ.ม.) | น้ำพีค (% ความจุ) | น้ำเข้า 4 วัน | น้ำออก 4 วัน | หน่วงน้ำสุทธิ | ความถี่ล้น 18 ปี |",
        "|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    
    for cresv, r in summary["reservoir_details"].items():
        h = r["18y_overflow_stat"]
        h_str = f"{h.get('overflow_years', '-')}/{h.get('total_years', '-')} ปี ({h.get('overflow_pct', '-') }%)" if h else "-"
        over_badge = f"**{r['peak_storage_pct']}%** (ล้น)" if r["is_overflow"] else f"{r['peak_storage_pct']}%"
        md.append(f"| **{r['name']}** | {r['amphoe']} | {r['downstream_area']} | {r['capacity_mcm']} | {over_badge} | {r['event_inflow_4days_mcm']} | {r['event_outflow_4days_mcm']} | {r['net_retention_4days_mcm']} ({r['retention_pct']}%) | {h_str} |")
        
    md.extend([
        "",
        "## 3. ข้อค้นพบสำคัญเชิงนิติอุทกวิทยา",
        "",
        "1. **น้ำท่วมฉับพลันในเขต ต.เขาพระ มีส่วนเกิดจากน้ำล้นอ่างฯ ทรายทอง**:",
        "   - อ่างเก็บน้ำทรายทอง (ความจุ 2.0 ล้าน ลบ.ม.) มีน้ำเต็มเกิน 100% ตั้งแต่วันที่ 26 ก.ย. (106.1%) ก่อนที่แนวฝนหนักที่สุดจะถล่ม",
        "   - ส่งผลให้น้ำหลากที่ไหลเข้าอ่างช่วง 26–29 ก.ย. จำนวน **1.519 ล้าน ลบ.ม.** ล้นข้ามทางระบายน้ำล้นออกทันทีถึง **1.511 ล้าน ลบ.ม. (Pass-through 99.5%)** เข้าท่วมพื้นที่ ต.เขาพระ และมุ่งหน้าสู่เขตเทศบาลเมืองนครนายก",
        "2. **น้ำหลากใน อ.ปากพลี มีปัจจัยเสริมจากอ่างฯ คลองวังบอน**:",
        "   - อ่างเก็บน้ำคลองวังบอน (ความจุ 7.6 ล้าน ลบ.ม.) เต็มล้นความจุ (100.8%–101.6%) ตลอดช่วงเหตุการณ์ ระบายน้ำล้นออก 0.709 ล้าน ลบ.ม. ลงสู่อำเภอปากพลี",
        "3. **อ่างฯ ห้วยปรือ และ คลองกลาง ทำหน้าที่หน่วงน้ำได้อย่างสมบูรณ์**:",
        "   - อ่างเก็บน้ำห้วยปรือ (8.87 ล้าน ลบ.ม.) กักน้ำไว้ได้ถึง 1.134 ล้าน ลบ.ม. (หน่วงน้ำไว้ 86.4%)",
        "   - อ่างเก็บน้ำคลองกลาง (3.10 ล้าน ลบ.ม.) กักน้ำไว้ได้ถึง 0.886 ล้าน ลบ.ม. (หน่วงน้ำไว้ 97.7% โดยไม่ปล่อยน้ำออกเลยในช่วงพีค 26–28 ก.ย.)",
        "4. **สถิติ 18 ปี ยืนยันว่าอ่างเชิงเขาขนาดย่อมเต็ม 100% เกือบทุกปี**:",
        "   - อ่างทรายทองและคลองสีเสียดมีสถิติน้ำล้นเกิน 100% ถึง **15 ใน 18 ปี (83.3%)** แสดงว่าอ่างเหล่านี้มักเต็มเร็วตั้งแต่ต้นฤดูฝน เมื่อมีพายุหรือฝนตกหนักเป็นแถบในช่วงปลายเดือนกันยายน จึงไม่เหลือช่องว่างหน่วงน้ำ (Retention Buffer)",
    ])
    
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"[✓] สร้างรายงาน {OUT_MD.name} และ {OUT_JSON.name} สำเร็จ")


if __name__ == "__main__":
    analyze()
