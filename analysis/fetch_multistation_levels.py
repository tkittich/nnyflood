# ดึงระดับน้ำโทรมาตรเขื่อนขุนด่านปราการชล "ทุกจุดวัด" (19 สถานี) -> data/20_multistation_levels/
#
# P0 ของ analysis/ALL_STATIONS_IMPLEMENTATION_PLAN.md — ชั้นที่ทำให้ทุกอย่างพิสูจน์จาก repo ได้
# (คู่กับ raw series + manifest + hash เก็บใน data/20_multistation_levels/)
#
# ที่มา: http://khundan-tele.rid.go.th/station_detail.php (POST urlencoded: n_id/date_from/date_to)
# ความละเอียด: 15 นาที ใช้ได้ทุกช่วงความยาว
#   ยืนยัน 6 ต.ค. 69: ขอ 2022-01-01..2025-12-31 ของ n_id=62 -> 138,822 แถว median gap 15 นาที
#   (อย่าตีความ API ว่า "<=7 วันเท่านั้น" — ดึง 5 ปี 15 นาทีได้จริง ดู fetch_khundan_training.py)
#   ⚠️ ยังดึงเป็นก้อน <=6 วันเพื่อกัน timeout/ตัดช่วง
#
# ใช้:
#   python analysis/fetch_multistation_levels.py --from 2026-09-01 --to 2026-09-30
#   python analysis/fetch_multistation_levels.py --from 2026-09-01 --to 2026-09-30 --stations 61,62,63
#   python analysis/fetch_multistation_levels.py --from 2026-09-01 --to 2026-09-30 --dry-run
#
# หมายเหตุสถานีเสีย (ยืนยัน 6 ต.ค. 69): 69/74 = 0 แถว · 80 = ค้าง 0.00 · 105 = ข้อมูลเสีย
#   สคริปต์นี้ยังพยายามดึงทุกจุด แล้วให้ผลลัพธ์เป็นจริง (ผู้วิเคราะห์ตัดสินเองที่ P1)
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "20_multistation_levels"
REGISTRY = json.loads((ROOT / "analysis" / "khundan_station_registry.json").read_text(encoding="utf-8"))

URL = "http://khundan-tele.rid.go.th/station_detail.php"
CHUNK_DAYS = 6
RETRIES = 3
UA = "Mozilla/5.0 flood-analysis/1.0 (multistation; contact: project)"


def fetch(n_id, d_from, d_to, timeout=90):
    """คืน list ของ [date, time, level, q, rain] ดิบ (ใหม่->เก่า ตามที่เซิร์ฟเวอร์ส่ง)."""
    body = urllib.parse.urlencode(
        {"n_id": str(n_id), "date_from": d_from, "date_to": d_to}
    ).encode()
    req = urllib.request.Request(
        URL, data=body,
        headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"},
    )
    txt = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="ignore")
    rows = []
    for tr in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", txt):
        c = [x.strip() for x in re.findall(r"<t[dh][^>]*>([^<]*)", tr)]
        if len(c) >= 4 and re.match(r"\d{2}/\d{2}/\d{4}", c[0]):
            rows.append(c[:5])
    return rows


def iso_stamp(date_s, time_s):
    day, mon, yr = date_s.split("/")
    return f"{yr}-{mon}-{day}T{time_s}:00"


def to_num(s):
    """'-' / '' / '0.000' เก็บตามจริง — คืน '' ถ้าไม่มีค่า."""
    s = (s or "").strip()
    if s in ("", "-"):
        return ""
    try:
        return f"{float(s):.3f}"
    except ValueError:
        return ""


def chunked(n_id, start, end, chunk_days=CHUNK_DAYS, quiet=False):
    """ดึงช่วง start..end เป็นก้อน — รวมทุกแถว (dedupe ตาม timestamp ภายหลัง)."""
    rows = []
    d = start
    while d <= end:
        d2 = min(d + dt.timedelta(days=chunk_days - 1), end)
        got = None
        for attempt in range(RETRIES):
            try:
                got = fetch(n_id, d.isoformat(), d2.isoformat())
                break
            except Exception as e:  # noqa: BLE001 — เครือข่าย/endpoint ล่มชั่วคราว
                if attempt == RETRIES - 1:
                    print(f"    st{n_id} {d}..{d2}: FAIL {type(e).__name__}: {e}", flush=True)
                    got = []
                else:
                    time.sleep(4)
        rows.extend(got)
        if not quiet:
            print(f"    st{n_id} {d.isoformat()}..{d2.isoformat()}: +{len(got)}", flush=True)
        d = d2 + dt.timedelta(days=1)
        time.sleep(0.6)  # สุภาพกับเซิร์ฟเวอร์
    return rows


def write_csv(path, rows):
    """เขียน csv: datetime_iso,level_msl_m,q_cms,rain_mm (เรียงเก่า->ใหม่, dedupe)."""
    seen = {}
    for c in rows:
        stamp = iso_stamp(c[0], c[1])
        seen[stamp] = (stamp, to_num(c[2]), to_num(c[3]), to_num(c[4]) if len(c) > 4 else "")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("datetime,level_msl_m,q_cms,rain_mm\n")
        for stamp in sorted(seen):
            f.write(",".join(seen[stamp]) + "\n")
    return len(seen)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="ดึงระดับน้ำโทรมาตรทุกจุดวัด (khundan-tele)")
    ap.add_argument("--from", dest="d_from", required=True, help="YYYY-MM-DD")
    ap.add_argument("--to", dest="d_to", required=True, help="YYYY-MM-DD")
    ap.add_argument("--stations", default="all", help="'all' หรือรหัสคั่นด้วยจุลภาค เช่น 61,62,63")
    ap.add_argument("--dry-run", action="store_true", help="แสดงแผน ไม่ดึงจริง")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    start = dt.date.fromisoformat(args.d_from)
    end = dt.date.fromisoformat(args.d_to)
    if end < start:
        sys.exit("--to ต้องไม่ก่อน --from")

    ids = sorted(REGISTRY, key=int) if args.stations == "all" else [s.strip() for s in args.stations.split(",")]
    missing = [i for i in ids if i not in REGISTRY]
    if missing:
        sys.exit(f"ไม่รู้จักรหัสสถานี: {missing}")

    print(f"ช่วง {start}..{end} · {len(ids)} สถานี · ก้อน {CHUNK_DAYS} วัน · ปลายทาง {OUT}")
    if args.dry_run:
        for i in ids:
            print(f"  st{i:>4}  {REGISTRY[i]}")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    per_station = {}
    for i in ids:
        rows = chunked(i, start, end, quiet=args.quiet)
        # ชื่อไฟล์เป็น ASCII ล้วน (st<id>.csv) — ชื่อไทยอยู่ใน fetch_info.json/registry
        # (ชื่อไทยในชื่อไฟล์ถูกแทนด้วย _ จนอ่านไม่ออก จึงเลี่ยง)
        csv = OUT / f"st{i}.csv"
        n = write_csv(csv, rows)
        per_station[i] = {"file": csv.name, "rows": n, "raw_rows": len(rows)}
        print(f"  st{i:>4} {REGISTRY[i][:44]:44s} -> {n:>6} rows  {csv.name}", flush=True)

    # _hashes.txt — ครอบทุก st*.csv ที่มีในโฟลเดอร์ (ไม่ใช่แค่รันนี้)
    # เพื่อให้รันบางสถานีไม่ทำให้แฮชของสถานีอื่นหายไป
    lines = []
    for p in sorted(OUT.glob("st*.csv"), key=lambda q: int(q.stem[2:])):
        digest = sha256_file(p)
        lines.append(f"{digest}  {p.name}")
        sid = p.stem[2:]
        if sid in per_station:
            per_station[sid]["sha256"] = digest
    (OUT / "_hashes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    info = {
        "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
        "source": f"{URL} (POST n_id/date_from/date_to)",
        "resolution": "15-min",
        "window": {"from": start.isoformat(), "to": end.isoformat()},
        "chunk_days": CHUNK_DAYS,
        "stations": {i: {"name": REGISTRY[i], **per_station[i]} for i in ids},
        "note": "P0 ของ analysis/ALL_STATIONS_IMPLEMENTATION_PLAN.md — raw-first + hash ตาม protocol โครงการ",
    }
    # รันบางสถานี (--stations subset) ต้องไม่ทับบันทึกของรันเต็ม -> แยกไฟล์
    info_name = "fetch_info.json" if args.stations == "all" else "fetch_info_partial.json"
    (OUT / info_name).write_text(
        json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    ok = sum(1 for i in ids if per_station[i]["rows"] > 0)
    print(f"\nเสร็จใน {time.time()-t0:.0f}s · {ok}/{len(ids)} สถานีมีข้อมูล")
    print(f"ไฟล์: {OUT}/  (CSV + _hashes.txt + fetch_info.json)")


if __name__ == "__main__":
    main()
