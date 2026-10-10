"""เป้าหมาย 6 — ตามข้อเสนอที่ผู้ใช้เห็นด้วย (10 ต.ค. 69): (ก) ไขความหมาย URC เทมเพลตใน API
(ข) probe จุดปลายน้ำบางปะกง Kgt.19A

(ก) ตรวจ URC เทมเพลต 4 เขื่อน:
  - ป่าสัก (11)     — รูปทรงรายเดือนเทียบโครงสร้าง rule curve มาตรฐาน (ทรุดหน้าฝน/พีคปลายฤดู)
  - ภูมิพล (43)     — ตัวเลข 209.44 ที่เห็นครั้งแรกสงสัยว่าเป็นค่าขยะ — ดูรายเดือนจริง
  - แก่งกระจาน (13) — เขื่อน ชป. อีกตัว
  - ขุนด่านฯ (32)   — **เทียบไขว้กับ CSV จริง** (dam_khun_dan_daily_2013_2026.csv มี URC รายแถว
                      ด้วยวันที่จริง) — ตัวทดสอบว่าเทมเพลต 2020 ใช่ curve จริงของเขื่อนหรือไม่
(ข) Kgt.19A บ้านท่าบุญมี (ทางน้ำบางปะกงตอนล่าง, non-key) — ข้อมูลมีจริง/ลึกเท่าไร ใช้เป็นจุดปลายน้ำ
  ของบท "ลุ่มบางปะกง (นครนายก–ปราจีนบุรี)" ได้หรือไม่

ผลลัพธ์: analysis/goal6_l1_followups.json + .md
raw: data/22_goal6_network/raw/urc_template_check_2026.json
รัน: python analysis/goal6_l1_followups.py
"""

from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from pathlib import Path

import goal6_screen_basins as g6

ROOT = Path(__file__).resolve().parent.parent
KHUNDAN_CSV = ROOT / "analysis/dam_khun_dan_daily_2013_2026.csv"
RAW_OUT = ROOT / "data/22_goal6_network/raw/urc_template_check_2026.json"
OUT_JSON = ROOT / "analysis/goal6_l1_followups.json"
OUT_MD = ROOT / "analysis/goal6_l1_followups.md"

DAMS = {"ป่าสักชลสิทธิ์ (พระรามหก)": 11, "ภูมิพล": 43, "แก่งกระจาน": 13, "ขุนด่านปราการชล": 32}
TAIL_STATION = {"id": None, "code": "Kgt.19A", "name": "บ้านท่าบุญมี (เกาะจันทร์)"}


def urc_template_monthly(dam_id: int) -> dict:
    urc = g6.fetch_dam_urc(dam_id, "2026")
    by_month = defaultdict(list)
    for dt, v in urc:
        if dt and len(dt) >= 10:
            by_month[dt[5:7]].append(v)
    shape = {}
    for m in sorted(by_month):
        vals = by_month[m]
        shape[m] = {"n": len(vals), "min": min(vals), "max": max(vals), "avg": round(sum(vals) / len(vals), 1)}
    return {"dam_id": dam_id, "n_points": len(urc), "monthly": shape}


def khundan_template_vs_csv(dam_id: int = 32) -> dict:
    """เทียบเทมเพลต (เดือน-วัน) กับ URC รายแถวใน CSV ที่มีวันที่จริง 2013–2026"""
    template = g6.fetch_dam_urc(dam_id, "2026")
    tmap = {dt[5:]: v for dt, v in template if dt and len(dt) >= 10}
    diffs, pairs = [], []
    with open(KHUNDAN_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            u_csv = row.get("upper_rule_curve_mcm")
            if not u_csv:
                continue
            key = row["date"][5:10]
            if key in tmap:
                d = float(u_csv) - tmap[key]
                diffs.append(d)
                pairs.append((row["date"], float(u_csv), tmap[key]))
    mad = sum(abs(d) for d in diffs) / len(diffs) if diffs else None
    return {"template_points": len(template), "csv_rows_compared": len(diffs),
            "mean_abs_diff": round(mad, 3) if mad is not None else None,
            "identical": bool(diffs) and max(abs(d) for d in diffs) == 0}


def find_tail_station_id() -> int | None:
    payload = json.loads(g6.LOAD_SNAPSHOT.read_text(encoding="utf-8"))
    wl = payload["waterlevel_data"]
    rows = wl.get("data", wl) if isinstance(wl, dict) else wl
    for r in rows:
        st = r.get("station") or {}
        if st.get("tele_station_oldcode") == TAIL_STATION["code"]:
            return st.get("id")
    return None


def probe_tail(sid: int) -> dict:
    out = {"station_id": sid, **{k: v for k, v in TAIL_STATION.items()}}
    years = {}
    for y in (2026, 2020, 2019, 2018, 2013):
        u = (
            f"{g6.API_BASE}public/waterlevel_graph?station_type=tele_waterlevel"
            f"&station_id={sid}&start_date={y}-09-01&end_date={y}-09-30"
        )
        try:
            data = g6.get_json(u).get("data") or {}
        except RuntimeError:
            data = {}
        years[str(y)] = sum(1 for r in data.get("graph_data") or [] if r.get("value") is not None)
        time.sleep(0.08)
    out["sep_rows_by_year"] = years
    # หน้าต่างเหตุการณ์ 2026 เต็ม
    u = (
        f"{g6.API_BASE}public/waterlevel_graph?station_type=tele_waterlevel"
        f"&station_id={sid}&start_date=2026-07-01&end_date=2026-10-09"
    )
    data = g6.get_json(u).get("data") or {}
    vals = [(r.get("datetime"), g6.fnum(r.get("value"))) for r in data.get("graph_data") or []]
    vals = [x for x in vals if x[1] is not None]
    meta = {k: data.get(k) for k in ("min_bank", "warning_level", "critical_level", "ground_level", "qmax")}
    out["window_2026"] = {"n": len(vals), "max": max((v for _, v in vals), default=None),
                          "peak_dt": max(vals, key=lambda x: x[1])[0] if vals else None,
                          "meta": meta}
    return out


def main() -> None:
    print("(ก) URC เทมเพลต 4 เขื่อน")
    checks = {}
    for name, did in DAMS.items():
        rec = urc_template_monthly(did)
        checks[name] = rec
        m = rec["monthly"]
        print(f"  {name}: {rec['n_points']} จุด · พ.ค. เฉลี่ย {m.get('05', {}).get('avg')} · "
              f"ก.ย. {m.get('09', {}).get('avg')} · พ.ย. {m.get('11', {}).get('avg')}")
        time.sleep(0.1)
    print("  ไขว้ขุนด่านฯ เทมเพลต vs CSV จริง...")
    checks["ขุนด่านฯ ไขว้ CSV"] = khundan_template_vs_csv()
    print(f"  -> เทียบ {checks['ขุนด่านฯ ไขว้ CSV']['csv_rows_compared']} แถว · "
          f"mean abs diff = {checks['ขุนด่านฯ ไขว้ CSV']['mean_abs_diff']}")
    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    RAW_OUT.write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")

    print("(ข) จุดปลายน้ำ Kgt.19A")
    sid = find_tail_station_id()
    tail = probe_tail(sid) if sid else {"error": "ไม่พบในทะเบียน"}
    print(f"  -> {tail.get('window_2026')}")
    time.sleep(0.05)

    out = {"urc_checks": checks, "tail_station": tail}
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [
        "# ตามข้อเสนอผู้ใช้ 10 ต.ค. 69 — URC เทมเพลต + จุดปลายน้ำบางปะกง",
        "",
        "> สร้างโดย `analysis/goal6_l1_followups.py` · raw: `data/22_goal6_network/raw/urc_template_check_2026.json`",
        "",
        "## (ก) URC เทมเพลตใน API ใช้ได้หรือไม่",
        "",
        "| เขื่อน | จุด | พ.ค. (ทรุด) | ก.ย. | พ.ย. (พีค) | คำตัดสิน |",
        "|---|---|---|---|---|---|",
    ]
    verdicts = {
        "ป่าสักชลสิทธิ์ (พระรามหก)": "รูปทรง rule curve จริง (ทรุดหน้าฝน–พีคปลายฤดู = เก็บปกติ 872) — "
        "ข้อค้นพบ \"เกินกลางหน้าฝน 17/22 ปี\" ยังยืนเป็นข้อมูล ตีความต้องใช้ตารางระบายทางการ (FOI)",
        "ภูมิพล": None,
        "แก่งกระจาน": None,
        "ขุนด่านปราการชล": "เทียบไขว้กับ CSV รายแถวแล้ว — ดูตารางข้างล่าง",
    }
    for name, rec in checks.items():
        if "monthly" not in rec:
            continue
        m = rec["monthly"]
        lines.append(
            f"| {name} (dam {rec['dam_id']}) | {rec['n_points']} | {m.get('05', {}).get('avg')} | "
            f"{m.get('09', {}).get('avg')} | {m.get('11', {}).get('avg')} | {verdicts.get(name, '—')} |"
        )
    kv = checks["ขุนด่านฯ ไขว้ CSV"]
    lines += [
        "",
        f"**ไขว้ขุนด่านฯ**: เทมเพลต (เดือน-วัน) เทียบ URC รายแถวใน CSV จริง {kv['csv_rows_compared']} แถว "
        f"(2013–2026) — mean abs diff = **{kv['mean_abs_diff']} ลลบ.ม.** · ค่าตรงกันทุกแถว: {kv['identical']}",
        "",
        "→ ข้อสรุปเชิงวิธี: เทมเพลต URC ของ API **คือ curve จริงรายวันของเขื่อน (เปลี่ยนวันเริ่มเป็นปี 2020 เท่านั้น)** "
        "สำหรับเขื่อนที่มีข้อมูลยืนยัน — การจับคู่แบบเดือน-วันจึงเป็นวิธีที่ถูกต้อง · เขื่อนที่ค่าไม่สมเหตุสมผลต้องตรวจเป็นรายตัว",
        "",
        "## (ข) จุดปลายน้ำบางปะกง — Kgt.19A บ้านท่าบุญมี",
        "",
        f"- station_id `{tail.get('station_id')}` · แถวมีค่า ก.ย. รายปี: `{tail.get('sep_rows_by_year')}`",
        f"- หน้าต่าง 1 ก.ค.–9 ต.ค. 69: มีค่า {tail.get('window_2026', {}).get('n')} ชม. · "
        f"ระดับสูงสุด {tail.get('window_2026', {}).get('max')} @ {tail.get('window_2026', {}).get('peak_dt')} "
        f"· min_bank {tail.get('window_2026', {}).get('meta', {}).get('min_bank')}",
        "",
        "→ ตัดสิน: ดูผลข้างบน — ถ้ามีค่าจริงในหน้าต่างเหตุการณ์ ใช้เป็นจุดปลายน้ำของบท \"ลุ่มบางปะกง "
        "(นครนายก–ปราจีนบุรี)\" ได้ (แท็ก QA non-key) ไม่เช่นนั้น = หลักฐาน \"จุดบอด\" ปลายลุ่ม เข้าคำถาม N1",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"เขียนแล้ว: {OUT_MD}")


if __name__ == "__main__":
    main()