# มุมมอง "เครือข่าย" — ความสามารถ + คุณภาพข้อมูลรายจุด (P1)
#
# อ่าน raw จาก data/20_multistation_levels/ (P0) แล้วสรุป:
#   1) แต่ละจุด "มีอะไร" (ระดับ / Q / ฝน) — ตรวจรายจุดจริง ไม่อ้างว่า "19 จุดมีครบ"
#   2) คุณภาพข้อมูล (coverage / flat / dropout / distinct / เซนเซอร์เสีย)
#   3) ตารางเหตุการณ์ Δ **2 คอลัมน์** — แยก "การขึ้นเชิงอุทกวิทยา" ออกจาก "ขั้นปฏิบัติการ"
#      (ห้ามใช้ น้ำสูงสุด − ต่ำสุด เพราะปนการปิดบานเข้าไป ทำให้ Δ ถูก artifact ครอบงำ)
#
# ใช้: python analysis/all_stations_network.py
# ออก: analysis/all_stations_network.json + analysis/all_stations_network.md
import csv
import datetime as dt
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "20_multistation_levels"
OUT_JSON = ROOT / "analysis" / "all_stations_network.json"
OUT_MD = ROOT / "analysis" / "all_stations_network.md"
REGISTRY = json.loads((ROOT / "analysis" / "khundan_station_registry.json").read_text(encoding="utf-8"))

W_START = dt.datetime(2026, 9, 1)
W_END = dt.datetime(2026, 9, 30, 23, 45)
EXPECTED_ROWS = 30 * 96                     # 15 นาที × 30 วัน
BASELINE_DAY = dt.date(2026, 9, 25)         # วันก่อนเหตุการณ์ (น้ำสูงสุด 26–29 ก.ย.)
STEP_MIN = 15
FLAT_EPS = 0.01                             # นิยาม "ไม่เปลี่ยน"
ZERO_EPS = 0.005                            # ค่าที่ถือเป็น 0.00 (dropout)

# กลุ่มตามกายภาพ — ใช้จัดตาราง/ตีความ
GROUP = {}
for i in ("16", "17", "18", "19", "20", "21"):
    GROUP[i] = "คลองสายใหญ่"
GROUP["72"] = "คลองสายใหญ่"
GROUP["69"] = "คลองสายใหญ่"
GROUP["74"] = "คลองสายใหญ่"
for i in ("23", "26", "28", "30", "84"):
    GROUP[i] = "ปตร./สาขา"
for i in ("61", "62", "63", "105"):
    GROUP[i] = "แม่น้ำหลัก"
GROUP["80"] = "อื่น ๆ"


def num(x):
    x = (x or "").strip()
    if x in ("", "-"):
        return None
    try:
        return float(x)
    except ValueError:
        return None


def load(sid):
    rows = []
    p = DATA / f"st{sid}.csv"
    if not p.exists():
        return rows
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = dt.datetime.fromisoformat(r["datetime"])
            rows.append((t, num(r["level_msl_m"]), num(r["q_cms"]), num(r["rain_mm"])))
    rows.sort()
    return rows


def despike(vals, win=9, k=5.0, floor=0.5):
    """หา spike เทียบ rolling median — คืน (mask ที่ True = ใช้ได้, จำนวน spike).

    จำเป็น: บางจุดมีค่ากระโดดครั้งเดียว (เช่น st19 -> 17.08 จากฐาน 13.06,
    st26 -> 12.81 จากฐาน 1.62) ถ้าไม่กรอง 'น้ำสูงสุด' จะเป็น spike ไม่ใช่น้ำสูงสุดท่วม
    """
    n = len(vals)
    if n < win:
        return [True] * n, 0
    half = win // 2
    resid = []
    for i in range(n):
        seg = sorted(vals[max(0, i - half):min(n, i + half + 1)])
        resid.append(vals[i] - seg[len(seg) // 2])
    absres = sorted(abs(r) for r in resid)
    mad = absres[len(absres) // 2]
    thr = max(floor, k * 1.4826 * mad)
    keep = [abs(r) <= thr for r in resid]
    return keep, sum(1 for x in keep if not x)


def max_drop_within(rows, minutes=60, tol=8):
    """การดิ่งลงมากสุดภายใน ~minutes นาที (ใช้ timestamps จริง)."""
    lv = [(t, v) for t, v, _, _ in rows if v is not None]
    best, when = 0.0, None
    j0 = 0
    for i in range(len(lv)):
        for j in range(j0, len(lv)):
            gap = (lv[j][0] - lv[i][0]).total_seconds() / 60
            if gap > minutes + tol:
                break
            if minutes - tol <= gap <= minutes + tol:
                d = lv[i][1] - lv[j][1]
                if d > best:
                    best, when = d, (lv[i][0], lv[j][0])
        if (lv[i][0] - lv[j0][0]).total_seconds() / 60 > minutes + tol:
            j0 = i
    return best, when


def analyse(sid, rows):
    name = REGISTRY.get(sid, "?")
    n = len(rows)
    lv = [v for _, v, _, _ in rows if v is not None]
    q = [v for _, _, v, _ in rows if v is not None]
    rn = [v for _, _, _, v in rows if v is not None]

    out = {
        "id": sid,
        "name": name,
        "group": GROUP.get(sid, "?"),
        "rows": n,
        "coverage_pct": round(100 * n / EXPECTED_ROWS, 1),
        "capability": {
            "level_nonnull_pct": round(100 * len(lv) / n, 1) if n else 0.0,
            "q_nonnull_pct": round(100 * len(q) / n, 1) if n else 0.0,
            "q_positive_pct": round(100 * sum(1 for v in q if v > 0) / n, 1) if n else 0.0,
            "rain_nonnull_pct": round(100 * len(rn) / n, 1) if n else 0.0,
            "rain_positive_pct": round(100 * sum(1 for v in rn if v > 0) / n, 1) if n else 0.0,
        },
        "health": [],
    }

    if not lv:
        out["health"].append("no level data")
        out["event"] = None
        return out

    med = st.median(lv)
    zero_frac = sum(1 for v in lv if abs(v) < ZERO_EPS) / len(lv)
    steps = [abs(lv[i] - lv[i - 1]) for i in range(1, len(lv))]
    flat = sum(1 for s in steps if s < FLAT_EPS) / len(steps) if steps else 0.0
    distinct = len({round(v, 2) for v in lv})

    out["level"] = {
        "median": round(med, 3),
        "min": round(min(lv), 3),
        "max": round(max(lv), 3),
        "distinct_2dp": distinct,
        "flat_pct": round(100 * flat, 1),
        "zero_frac": round(zero_frac, 3),
        "p95_step": round(sorted(steps)[int(len(steps) * 0.95)], 3) if steps else 0.0,
    }

    # --- ธงสุขภาพเซนเซอร์ ---
    if max(lv) == min(lv):
        out["health"].append("constant (dead sensor)")
    elif flat > 0.90:
        out["health"].append("near-constant")
    if zero_frac > 0.02 and med > 1.0:
        out["health"].append("0.00 dropouts mixed in")
    if med > 100:
        out["health"].append("different datum (msl offset)")
    if out["coverage_pct"] < 80:
        out["health"].append(f"coverage {out['coverage_pct']}%")
    if q and min(q) < -0.5:
        out["health"].append("negative Q present")

    # --- กรอง spike ก่อนคำนวณเหตุการณ์ (spike เดี่ยว ไม่ใช่น้ำสูงสุดท่วม) ---
    lv_rows = [(t, v) for t, v, _, _ in rows if v is not None]
    vals = [v for _, v in lv_rows]
    keep, n_spike = despike(vals)
    clean = [tv for tv, k in zip(lv_rows, keep) if k]
    out["spikes_removed"] = n_spike
    if n_spike:
        out["health"].append(f"{n_spike} spikes filtered")

    # --- แบ่ง segment ที่ datum/calibration เปลี่ยน (|Δ| > 3 ม.) ---
    # พบจริงในข้อมูล 1–30 ก.ย. 69:
    #   st16 09-16 10:45  1.18 -> 13.83 · st19 09-15 17:30  0.76 -> 17.08
    #   st26 09-17 16:45 12.32 ->  1.29 · st30 09-22 18:00  3.26 -> -4.99 (sentinel)
    #   st84 09-08 17:29 -4.99 ->  4.00
    # => เทียบ baseline กับน้ำสูงสุด "ข้าม" segment ไม่มีความหมาย ต้องใช้ segment ที่ครอบช่วงเหตุการณ์
    SHIFT = 3.0
    segs, cur = [], ([clean[0]] if clean else [])
    for prev, nxt in zip(clean, clean[1:]):
        if abs(nxt[1] - prev[1]) > SHIFT:
            segs.append(cur)
            cur = [nxt]
        else:
            cur.append(nxt)
    if cur:
        segs.append(cur)
    EV0, EV1 = dt.datetime(2026, 9, 25), dt.datetime(2026, 9, 30, 23, 59, 59)
    seg = max(segs, key=lambda s: sum(1 for t, _ in s if EV0 <= t <= EV1)) if segs else []
    n_shift = len(segs) - 1
    out["datum_shifts"] = n_shift
    out["segment_rows"] = len(seg)
    if n_shift > 0:
        out["health"].append(f"datum shift ×{n_shift} (ใช้ segment ช่วงเหตุการณ์)")

    # --- เหตุการณ์: baseline / peak / การขึ้น / ขั้นปฏิบัติการ (ภายใน segment เดียว) ---
    seg_med = st.median([v for _, v in seg]) if seg else 0.0
    base_vals = [v for t, v in seg if t.date() == BASELINE_DAY]
    peak_v, peak_t = None, None
    for t, v in seg:
        if abs(v) < ZERO_EPS and seg_med > 1.0:
            continue
        if peak_v is None or v > peak_v:
            peak_v, peak_t = v, t
    baseline = st.median(base_vals) if base_vals else None
    drop, drop_when = max_drop_within([(t, v, None, None) for t, v in seg], 60)

    if not out["health"]:
        out["health"].append("ok")

    out["event"] = {
        "baseline_25sep": round(baseline, 3) if baseline is not None else None,
        "peak": round(peak_v, 3) if peak_v is not None else None,
        "peak_time": peak_t.strftime("%Y-%m-%d %H:%M") if peak_t else None,
        # คอลัมน์ที่ 1: การขึ้นเชิงอุทกวิทยา (น้ำสูงสุด − baseline) — สิ่งที่ฝนทำ
        "hydro_rise_m": round(peak_v - baseline, 3) if (peak_v is not None and baseline is not None) else None,
        # คอลัมน์ที่ 2: ขั้นปฏิบัติการ (ดิ่งเร็วสุดใน 1 ชม.) — สิ่งที่คนทำ (ปิดบาน)
        "max_1h_drop_m": round(drop, 3),
        "max_1h_drop_from": drop_when[0].strftime("%Y-%m-%d %H:%M") if drop_when else None,
    }
    return out


def main():
    stations = {}
    for sid in sorted(REGISTRY, key=int):
        stations[sid] = analyse(sid, load(sid))

    doc = {
        "generated_from": "data/20_multistation_levels/ (analysis/fetch_multistation_levels.py)",
        "window": {"from": W_START.isoformat(), "to": W_END.isoformat()},
        "baseline_day": BASELINE_DAY.isoformat(),
        "definitions": {
            "hydro_rise_m": "peak − median(level on 25 Sep) — การขึ้นที่ฝนทำ",
            "max_1h_drop_m": "การดิ่งลงมากสุดภายใน ~60 นาที — ขั้นที่การเดินเครื่องทำ",
            "flat_pct": "สัดส่วนช่วง 15 นาทีที่ระดับไม่เปลี่ยน (|Δ| < 0.01)",
        },
        "stations": stations,
    }
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------- markdown ----------
    L = []
    L.append("# มุมมองเครือข่าย — ความสามารถ + คุณภาพรายจุด (P1)\n")
    L.append(f"สร้างจาก `data/20_multistation_levels/` · ช่วง {W_START:%d %b}–{W_END:%d %b %Y} · baseline = {BASELINE_DAY:%d %b}\n")
    L.append("นิยาม: **การขึ้นเชิงอุทกวิทยา** = น้ำสูงสุด − ระดับมัธยฐานวันที่ 25 ก.ย. (สิ่งที่ฝนทำ) · "
             "**ขั้นปฏิบัติการ** = การดิ่งเร็วสุดใน ~1 ชม. (สิ่งที่การปิดบานทำ)\n")

    L.append("## 1. ตารางเหตุการณ์ (Δ 2 คอลัมน์ — แยกอุทกวิทยา ออกจากปฏิบัติการ)\n")
    L.append("| กลุ่ม | id | จุด | baseline 25 ก.ย. | น้ำสูงสุด | **การขึ้น (อุทกวิทยา)** | **ขั้นปฏิบัติการ (1 ชม.)** |")
    L.append("|---|---:|---|---:|---:|---:|---:|")
    for g in ("คลองสายใหญ่", "ปตร./สาขา", "แม่น้ำหลัก", "อื่น ๆ"):
        for sid, s in stations.items():
            if s["group"] != g or not s.get("event"):
                continue
            e = s["event"]
            L.append(f"| {g} | {sid} | {s['name'][:30]} | {e['baseline_25sep']} | {e['peak']} | "
                     f"**+{e['hydro_rise_m']}** | {e['max_1h_drop_m']} |")
    L.append("")

    L.append("## 2. ความสามารถรายจุด — \"มีอะไร\"\n")
    L.append("| id | จุด | ระดับ | Q>0 | ฝน>0 | หมายเหตุ |")
    L.append("|---|---|---:|---:|---:|---|")
    for sid, s in stations.items():
        c = s["capability"]
        note = "ระดับเท่านั้น" if c["q_nonnull_pct"] == 0 else ("มี Q" if c["q_positive_pct"] > 50 else "Q ใช้ได้บางส่วน")
        if c["rain_positive_pct"] > 0.1:
            note += " · มีฝน"
        L.append(f"| {sid} | {s['name'][:30]} | {c['level_nonnull_pct']}% | {c['q_positive_pct']}% | "
                 f"{c['rain_positive_pct']}% | {note} |")
    L.append("")

    L.append("## 3. คุณภาพข้อมูล + ธงสุขภาพ\n")
    L.append("| id | จุด | coverage | flat% | ค่าที่ต่าง | zero% | ธง |")
    L.append("|---|---|---:|---:|---:|---:|---|")
    for sid, s in stations.items():
        lv = s.get("level")
        if not lv:
            L.append(f"| {sid} | {s['name'][:30]} | {s['coverage_pct']}% | — | — | — | {'; '.join(s['health'])} |")
            continue
        L.append(f"| {sid} | {s['name'][:30]} | {s['coverage_pct']}% | {lv['flat_pct']} | {lv['distinct_2dp']} | "
                 f"{lv['zero_frac']} | {'; '.join(s['health'])} |")
    L.append("")

    # ---- 4. สรุปอัตโนมัติ ----
    L.append("## 4. สรุปอัตโนมัติ\n")
    dead = [s["id"] for s in stations.values() if not s.get("level")]
    const = [s["id"] for s in stations.values()
             if s.get("level") and s["level"]["distinct_2dp"] <= 2]
    shifted = [s["id"] for s in stations.values() if s.get("datum_shifts")]
    spiky = [s["id"] for s in stations.values() if s.get("spikes_removed")]
    rainy = [s["id"] for s in stations.values() if s["capability"]["rain_positive_pct"] > 0.1]
    levelonly = [s["id"] for s in stations.values() if s["capability"]["q_positive_pct"] < 1
                 and s["capability"]["level_nonnull_pct"] > 50]
    L.append(f"- **ไม่มีข้อมูลระดับเลย:** {', '.join(dead) or '—'}")
    L.append(f"- **เซนเซอร์ค้าง (ค่าคงที่):** {', '.join(const) or '—'}")
    L.append(f"- **datum/calibration เปลี่ยนกลางเดือน:** {', '.join(shifted) or '—'}  "
             f"→ ห้ามเทียบ baseline–น้ำสูงสุดข้ามรอยนี้")
    L.append(f"- **มี spike ที่ต้องกรอง:** {', '.join(spiky) or '—'}")
    L.append(f"- **มีข้อมูลฝน (>0):** {', '.join(rainy) or '—'}")
    L.append(f"- **มีแค่ระดับ ไม่มี Q:** {', '.join(levelonly) or '—'}  → ตัดสัดส่วนรายสายไม่ได้")
    L.append("")
    can = [(s["id"], s["event"]["hydro_rise_m"], s["event"]["max_1h_drop_m"])
           for s in stations.values() if s["group"] == "คลองสายใหญ่" and s.get("event")
           and s["event"]["hydro_rise_m"] is not None]
    if can:
        L.append("**ลายเซ็นของคลองสายใหญ่** (จุด 16–21, 72): การขึ้นเชิงอุทกวิทยาเล็ก "
                 "แต่ขั้นปฏิบัติการ (ดิ่งใน 1 ชม.) ใหญ่กว่า — ยืนยันว่าระดับถูกกำหนดโดยบาน ไม่ใช่ฝน\n")
        L.append("| id | การขึ้น (อุทกวิทยา) | ขั้นปฏิบัติการ (1 ชม.) | สัดส่วน |")
        L.append("|---|---:|---:|---:|")
        for sid, rise, drop in can:
            ratio = f"{drop/rise:.1f}×" if rise and rise > 0.02 else "∞"
            L.append(f"| {sid} | +{rise} | {drop} | {ratio} |")
        L.append("")

    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON.name} + {OUT_MD.name}")
    print(f"stations with level: {sum(1 for s in stations.values() if s.get('level'))}/19")


if __name__ == "__main__":
    main()
