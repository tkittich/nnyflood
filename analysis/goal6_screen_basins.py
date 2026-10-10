"""เป้าหมาย 6 — screen เหตุการณ์ท่วมจริงหน้าฝน 2569 ต่อลุ่ม (เกณฑ์ pre-register)

เกณฑ์ที่กำหนดไว้ **ก่อนดูผล** (10 ต.ค. 2569 — ตามกติกา GOAL6_PLAN §5):

- หน้าต่างเวลา: 2026-07-01..2026-10-09 (ครอบหน้าฝนทั้งฤดู + เหตุการณ์นครนายก 26–27 ก.ย.)
- จุดวัด: ทุกจุดใน snapshot `public/waterlevel_load` (data/02 raw 10 ต.ค.) ที่
  (มี critical_level_m หรือ warning_level_m) หรือ is_key_station — ดึงรายชั่วโมงทั้งหน้าต่าง
- เหตุการณ์ระดับจุด (ใช้ได้เมื่อมีเกณฑ์ทางการใน API): ระดับสูงสุด ≥ critical = "เกินวิกฤต"
  / ≥ warning = "เกินเตือน" — นับชม.เกิน + run ต่อเนื่องยาวสุด
- เขื่อนผู้สมัคร 24 แห่ง (goal6_dam_candidates.json): จำนวนวันเกิน URC ใน ก.ย.–ต.ค.
  + ค่าสูงสุด เก็บ/เข้า/ปล่อย ในหน้าต่าง
- จุด key ที่ไม่มีเกณฑ์ทางการ: รายงานระดับสูงสุดอย่างเดียว — **ไม่จัดเหตุการณ์ ห้ามเดา threshold**

ผลลัพธ์: analysis/goal6_screen_2026_summary.json + analysis/goal6_screen_2026_findings.md
raw หลักฐาน (เฉพาะจุดที่เกินเกณฑ์ + ข้อมูลเขื่อน): data/22_goal6_network/raw/
ทำซ้ำได้: python analysis/goal6_screen_basins.py (จุดที่ดึงแล้วข้ามอัตโนมัติ)
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://api-v3.thaiwater.net/api/v1/thaiwater30/"
WINDOW_START = "2026-07-01"
WINDOW_END = "2026-10-09"
SEP_OCT_START = "2026-09-01"

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data/22_goal6_network/raw"
SUMMARY_PATH = ROOT / "analysis/goal6_screen_2026_summary.json"
FINDINGS_PATH = ROOT / "analysis/goal6_screen_2026_findings.md"
LOAD_SNAPSHOT = ROOT / "data/02_thaiwater/raw/2026-10-10_waterlevel_load.json"
CANDIDATES_PATH = ROOT / "analysis/goal6_dam_candidates.json"


def get_json(url: str, retries: int = 2) -> dict:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except Exception as exc:  # noqa: BLE001 — จด error ต่อจุดแล้วเดินต่อ
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{url[:90]}: {last}")


def day(v: str | None) -> str | None:
    return str(v)[:10] if v else None


def fnum(x) -> float | None:
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def sanitize(code: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", code)


def load_selected_stations() -> list[dict]:
    payload = json.loads(LOAD_SNAPSHOT.read_text(encoding="utf-8"))
    wl = payload["waterlevel_data"]
    rows = wl.get("data", wl) if isinstance(wl, dict) else wl
    out, seen = [], set()
    for r in rows:
        st = r.get("station") or {}
        sid = st.get("id")
        if sid in seen:
            continue
        seen.add(sid)
        key = bool(st.get("is_key_station"))
        crit = fnum(st.get("critical_level_m"))
        warn = fnum(st.get("warning_level_m"))
        if not (key or crit is not None or warn is not None):
            continue
        name = (st.get("tele_station_name") or {})
        out.append(
            {
                "id": sid,
                "code": st.get("tele_station_oldcode") or str(sid),
                "name": name.get("th") or name.get("en") or str(sid),
                "lat": st.get("tele_station_lat"),
                "long": st.get("tele_station_long"),
                "agency": ((r.get("agency") or {}).get("agency_shortname") or {}).get("th")
                or "?",
                "basin": ((r.get("basin") or {}).get("basin_name") or {}).get("th") or "ไม่ระบุลุ่ม",
                "province": ((r.get("geocode") or {}).get("province_name") or {}).get("th") or "",
                "is_key": key,
                "warn": warn,
                "crit": crit,
            }
        )
    return out


def fetch_station_screen(station: dict) -> dict:
    u = (
        f"{API_BASE}public/waterlevel_graph?station_type=tele_waterlevel"
        f"&station_id={station['id']}&start_date={WINDOW_START}&end_date={WINDOW_END}"
    )
    d = get_json(u)
    data = d.get("data") or {}
    meta = {k: data.get(k) for k in ("min_bank", "warning_level", "critical_level", "ground_level", "qmax")}
    # เกณฑ์ทางการ: load snapshot เป็นหลัก (graph meta มัก null) — จดที่มาไว้ทุกจุด
    warn, crit = station.get("warn"), station.get("crit")
    crit_source = "load" if crit is not None else None
    if crit is None:
        crit = fnum(meta.get("critical_level"))
        crit_source = "graph" if crit is not None else None
    if warn is None:
        warn = fnum(meta.get("warning_level"))
    graph = data.get("graph_data") or []
    vals = [(r.get("datetime"), fnum(r.get("value")), fnum(r.get("discharge"))) for r in graph]
    vals = [(dt, v, q) for dt, v, q in vals if v is not None]
    vals.sort(key=lambda x: x[0] or "")
    rec = dict(station)
    rec.update(
        n_values=len(vals),
        max_val=max((v for _, v, _ in vals), default=None),
        max_dt=None,
        max_discharge=max((q for _, _, q in vals if q is not None), default=None),
        hours_over_warn=0,
        hours_over_crit=0,
        longest_run_over_crit_h=0,
        meta_min_bank=fnum(meta.get("min_bank")),
        meta_ground=fnum(meta.get("ground_level")),
        meta_qmax=fnum(meta.get("qmax")),
        crit_source=crit_source,
    )
    if vals:
        rec["max_dt"], rec["max_val"] = max(vals, key=lambda x: x[1])[:2]
    if rec["meta_min_bank"] is not None and rec["max_val"] is not None:
        rec["max_vs_minbank"] = round(rec["max_val"] - rec["meta_min_bank"], 2)  # เชิงข้อมูล ไม่ใช่เกณฑ์จัดเหตุการณ์
    if warn is not None:
        rec["hours_over_warn"] = sum(1 for _, v, _ in vals if v >= warn)
    if crit is not None:
        over = [v >= crit for _, v, _ in vals]
        rec["hours_over_crit"] = sum(over)
        run = best = 0
        for flag in over:
            run = run + 1 if flag else 0
            best = max(best, run)
        rec["longest_run_over_crit_h"] = best
    # raw หลักฐานเฉพาะจุดที่เกินเกณฑ์ทางการ
    evidence = None
    if (crit is not None and rec["max_val"] is not None and rec["max_val"] >= crit) or (
        warn is not None and rec["max_val"] is not None and rec["max_val"] >= warn
    ):
        evidence = (
            RAW_DIR / "wl_screen_2026" / f"{station['id']}_{sanitize(station['code'])}.json"
        )
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(
            json.dumps(
                {"station": station, "meta": meta, "graph_data": vals},
                ensure_ascii=False,
                indent=0,
            ),
            encoding="utf-8",
        )
    rec["evidence"] = evidence.name if evidence else None
    return rec


def fetch_dam_series(dam_id: int, data_type: str, year: str = "2026") -> dict | None:
    u = f"{API_BASE}analyst/dam_yearly_graph?data_type={data_type}&dam_id={dam_id}&year={year}"
    try:
        d = get_json(u)
    except RuntimeError:
        return None
    data = d.get("data") or {}
    rows = data.get("graph_data") or []
    pairs: list[tuple[str, float]] = []
    for r in rows:
        if isinstance(r.get("data"), list):  # โครงซ้อน (เช่น dam_id 43)
            pairs += [
                (day(x.get("date")), fnum(x.get("value")))
                for x in r["data"]
                if fnum(x.get("value")) is not None
            ]
        else:
            v = fnum(r.get(data_type))
            if v is not None:
                pairs.append((day(r.get("dam_date") or r.get("date")), v))
    return pairs


def fetch_dam_urc(dam_id: int, year: str = "2026") -> list[tuple[str, float]]:
    u = f"{API_BASE}analyst/dam_yearly_graph?data_type=dam_storage&dam_id={dam_id}&year={year}"
    d = get_json(u)
    data = d.get("data") or {}
    urc = data.get("upper_rule_curve") or []
    out = []
    for r in urc:
        v = fnum(r.get("value") if "value" in r else r.get("upper_rule_curve"))
        dt = day(r.get("date") or r.get("dam_date"))
        if v is not None and dt:
            out.append((dt, v))
    if not out:  # บางโครงวาง URC บนแถวรายวัน
        for r in data.get("graph_data") or []:
            v = fnum(r.get("upper_rule_curve"))
            if v is not None:
                out.append((day(r.get("dam_date")), v))
    return out


def screen_dams() -> list[dict]:
    cands = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))["candidates"]
    out = []
    for c in cands:
        rec = {
            "name": c["dam_name"],
            "basin": c["basin"],
            "normal_storage": c["normal_storage"],
            "dam_ids": c["dam_ids"],
        }
        best = None
        for did in c["dam_ids"]:
            try:
                pairs = fetch_dam_series(did, "dam_storage")
            except RuntimeError:
                pairs = None
            if pairs and (best is None or len(pairs) > len(best[0])):
                best = (pairs, did)
        if not best:
            rec["error"] = "no storage data"
            out.append(rec)
            continue
        pairs, did = best
        rec["storage_dam_id"] = did
        urc = []
        try:
            urc = fetch_dam_urc(did)
        except RuntimeError:
            pass
        rec["urc_points"] = len(urc)
        # URC ที่ API คืนเป็นเทมเพลตรายวัน ลงวันที่ปี 2020 เสมอ — เทียบด้วย เดือน-วัน
        urc_map = {dt[5:]: v for dt, v in urc if dt and len(dt) >= 10}
        in_window = [(dt, v) for dt, v in pairs if SEP_OCT_START <= (dt or "") <= WINDOW_END]
        rec["sep_oct_n_days"] = len(in_window)
        if in_window:
            rec["sep_oct_max_storage"] = max(v for _, v in in_window)
            mx = max(in_window, key=lambda x: x[1])
            rec["sep_oct_max_storage_dt"] = mx[0]
        over = [
            (dt, v - urc_map[(dt or "")[5:]])
            for dt, v in in_window
            if v is not None and urc_map.get((dt or "")[5:]) is not None and v > urc_map[(dt or "")[5:]]
        ]
        rec["days_over_urc_sep_oct"] = len(over)
        if over:
            rec["max_over_urc"] = max(gap for _, gap in over)
        evidence = RAW_DIR / "dam_screen_2026" / f"dam{did}_dam_storage.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(
            json.dumps({"dam": c["dam_name"], "dam_id": did, "storage_2026": pairs, "urc_2026": urc}, ensure_ascii=False),
            encoding="utf-8",
        )
        rec["evidence_storage"] = evidence.name
        for dtype, key in (("dam_inflow", "max_inflow"), ("dam_released", "max_release")):
            try:
                p2 = fetch_dam_series(did, dtype)
            except RuntimeError:
                p2 = None
            p2w = [(dt, v) for dt, v in (p2 or []) if SEP_OCT_START <= (dt or "") <= WINDOW_END]
            rec[f"sep_oct_n_{dtype}"] = len(p2w)
            if p2w:
                rec[key], rec[f"{key}_dt"] = max(p2w, key=lambda x: x[1])
            ev = RAW_DIR / "dam_screen_2026" / f"dam{did}_{dtype}.json"
            ev.write_text(
                json.dumps({"dam": c["dam_name"], "dam_id": did, dtype + "_2026": p2}, ensure_ascii=False),
                encoding="utf-8",
            )
        out.append(rec)
    return out


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stations = load_selected_stations()
    print(f"จุดวัดที่เลือก (key หรือมีเกณฑ์ทางการ): {len(stations)} จุด")

    summary = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "window": [WINDOW_START, WINDOW_END], "criteria": "pre-register 10 ต.ค. 2569 (docstring)",
               "stations": [], "dams": [], "errors": []}
    if SUMMARY_PATH.exists():
        old = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        summary["stations"] = old.get("stations", [])
        summary["dams"] = old.get("dams", [])
        summary["errors"] = old.get("errors", [])

    done_ids = {s["id"] for s in summary["stations"]}
    t0 = time.time()
    for i, st in enumerate(stations, 1):
        if st["id"] in done_ids:
            continue
        try:
            rec = fetch_station_screen(st)
            summary["stations"].append(rec)
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append({"station": st["id"], "error": str(exc)[:120]})
            print(f"  [{i}/{len(stations)}] {st['code']} ERROR {str(exc)[:80]}")
            continue
        if i % 25 == 0:
            SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  [{i}/{len(stations)}] เสร็จ {time.time() - t0:.0f} วิ")
        time.sleep(0.1)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"จุดวัดเสร็จ: {len(summary['stations'])} · error {len(summary['errors'])}")

    if not summary["dams"]:
        print("ดึงเขื่อน 24 แห่ง (storage/inflow/released 2026 + URC)...")
        summary["dams"] = screen_dams()
        SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"เขื่อนเสร็จ: {len(summary['dams'])} แห่ง")

    # ตารางรวมสั้น ๆ
    crit_st = [s for s in summary["stations"] if (s.get("crit") is not None and (s.get("hours_over_crit") or 0) > 0)]
    warn_st = [s for s in summary["stations"] if (s.get("warn") is not None and (s.get("hours_over_warn") or 0) > 0)]
    print(f"\nจุดเกินวิกฤต: {len(crit_st)} · เกินเตือน (ไม่เกินวิกฤต): {len([s for s in warn_st if s not in crit_st])}")
    for s in sorted(crit_st, key=lambda x: -(x.get("longest_run_over_crit_h") or 0))[:20]:
        print(f"  {s['basin']} | {s['code']} {s['name'][:22]} | วิกฤต {s['hours_over_crit']} ชม. (run {s['longest_run_over_crit_h']}) | max {s['max_val']} @{s['max_dt']}")
    dams_over = [d for d in summary["dams"] if (d.get("days_over_urc_sep_oct") or 0) > 0]
    print(f"\nเขื่อนเกิน URC ช่วง ก.ย.–ต.ค.: {len(dams_over)} แห่ง")
    for d in sorted(dams_over, key=lambda x: -(x.get("days_over_urc_sep_oct") or 0)):
        print(f"  {d['name']} | เกิน URC {d['days_over_urc_sep_oct']} วัน | เก็บสูงสุด {d.get('sep_oct_max_storage')} @{d.get('sep_oct_max_storage_dt')}")


if __name__ == "__main__":
    main()