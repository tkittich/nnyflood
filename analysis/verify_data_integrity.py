#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ตรวจความสมบูรณ์ของ `data/` — เทียบ SHA-256 ที่บันทึกไว้ กับไฟล์จริงบนดิสก์

ช่องว่างที่ปิด: "No CI and no data-integrity test.
A nightly job that re-hashes `data/` and re-runs `s1_change_detect.py`
would catch silent drift."

ทำไมต้องมี: โปรเจคนี้ยึด protocol "raw-first" — ข้อค้นพบทุกข้อต้องพิสูจน์จาก repo ได้
แฮชคือหลักประกันข้อนั้น แต่ **แฮชที่ไม่มีใครตรวจ = คำสัญญา ไม่ใช่หลักฐาน**
(ดู `data/20_multistation_levels/manifest.md` — ต้นทาง khundan-tele เป็นข้อมูลสดที่
เปลี่ยนได้: n_id=105 ให้ผลต่างกันในสองการดึง จึงยิ่งต้องมีตัวตรวจ)

## รูปแบบที่อ่าน (มี 4 แบบในโปรเจคนี้ — heterogeneous โดยธรรมชาติ)

1. ตาราง markdown:  ``| `path` | size | `<64hex>` |``      (04, 09, 10, 13, 14, 17, 19, manual)
2. บุลเลตมีหัวข้อ:  ``### path`` แล้ว ``- SHA-256: `<64hex>` ``   (01, 02)
3. ข้อความในบรรทัด: ``... `path` ... `<64hex>` ...``            (10 — FLOOD.rar)
4. ไฟล์แยก `_hashes.txt`:  ``<64hex>  *<name>``                  (01, 10, 12, 16, 20)

## ใช้

    python analysis/verify_data_integrity.py                 # ตรวจทั้งหมด (ช้า — แฮช ~12 GB)
    python analysis/verify_data_integrity.py --quick         # เฉพาะไฟล์ <= 5 MB (เร็ว)
    python analysis/verify_data_integrity.py --only data/19_rid_cross_sections
    python analysis/verify_data_integrity.py --json out.json

**exit code:** 0 = ไม่มี MISMATCH · 1 = มี MISMATCH · 2 = มี MISSING แต่ไม่มี MISMATCH

`MISSING` ≠ ไฟล์เสีย — ส่วนใหญ่คือไฟล์ใหญ่ที่ **ไม่ได้อยู่ใน git** (data/13, data/18,
data/manual เก็บแค่ manifest) หรือไฟล์ที่ลบโดยเจตนา (ชุด T47PPS ไทล์ผิด)
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

HEX64 = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])")
BACKTICK = re.compile(r"`([^`]+)`")
# เส้นทางที่มี "/" และลงท้ายด้วยนามสกุลไฟล์ — ใช้จับ path ที่เขียนลอย ๆ ในข้อความ
# (เช่น "... เก็บต้นฉบับไว้ที่ raw/FLOOD.rar") โดยไม่ไปโดนโดเมนอย่าง facebook.com/mitrearth
SLASH_PATH = re.compile(r"[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+\.[A-Za-z0-9]{2,5}")
# ไฟล์ที่ "ไม่มีใน repo โดยเจตนา" — ลบแล้ว/ไทล์ผิด (ดู data/manual/manifest.md)
DELETED_MARKERS = ("T47PPS",)
# รายการ "หายโดยอธิบายได้" (เปลี่ยนชื่อ/ถูกแทนที่/เป็นไฟล์เครื่องมือ) — อ่านจาก
# data/INTEGRITY_EXCEPTIONS.md ถ้าไม่มีไฟล์นี้ก็ไม่เป็นไร (ว่าง)
EXCEPTIONS_FILE = DATA / "INTEGRITY_EXCEPTIONS.md"


def looks_like_path(tok):
    """เป็นชื่อไฟล์/เส้นทาง ไม่ใช่แฮชหรือข้อความล้วน"""
    if not tok or HEX64.fullmatch(tok):
        return False
    if tok.startswith(("http://", "https://")):
        return False
    return ("/" in tok) or ("." in tok)


def is_deleted(name):
    return any(m in name for m in DELETED_MARKERS)


# ---------- ตัวอ่าน ----------

def path_from_line(line, section):
    """เลือก path จากบรรทัด ตามลำดับความน่าเชื่อถือ (สูง -> ต่ำ)"""
    # 1) ช่องแรกของตาราง markdown
    if line.startswith("|"):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells:
            cand = cells[0].strip("`").strip()
            if looks_like_path(cand):
                return cand
    # 2) โทเคนใน backtick
    for tok in BACKTICK.findall(line):
        if looks_like_path(tok):
            return tok
    # 3) เส้นทางที่มี "/" ลอยอยู่ในข้อความ (raw/FLOOD.rar)
    m = SLASH_PATH.search(line)
    if m:
        return m.group(0)
    # 4) หัวข้อล่าสุด (รูปแบบ "### from_user/<ชื่อไฟล์>")
    if section and looks_like_path(section):
        return section
    return None


def load_exceptions():
    """อ่าน data/INTEGRITY_EXCEPTIONS.md -> {path หรือ basename: เหตุผล}"""
    exc = {}
    if not EXCEPTIONS_FILE.exists():
        return exc
    for raw in EXCEPTIONS_FILE.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        key = cells[0].strip("`").strip()
        if not key or set(key) <= set("-: ") or key.lower() in ("ไฟล์", "file"):
            continue
        exc[key] = cells[1]
        exc.setdefault(Path(key).name, cells[1])
    return exc


def parse_manifest(md_path):
    """อ่านตาราง + บุลเลตจาก manifest.md -> [(source, relpath|None, sha)]"""
    out = []
    section = None
    for raw in md_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()

        # จำหัวข้อล่าสุดไว้ใช้เป็น path สำรอง (รูปแบบที่ 2)
        if line.startswith("#"):
            section = line.lstrip("#").strip()
            continue

        hashes = HEX64.findall(line)
        if not hashes:
            continue

        path = path_from_line(line, section)
        for h in hashes:
            out.append((md_path.name, path, h.lower()))
    return out


def parse_hashes_txt(p):
    """`<64hex>  *<name>` หรือ `<64hex>  <name>`"""
    out = []
    for raw in p.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+)$", line)
        if m:
            out.append((p.name, m.group(2).strip(), m.group(1).lower()))
    return out


def collect(target_dirs):
    """เก็บ (dir, source, relpath, sha) จากทุก manifest.md + _hashes.txt"""
    recs = []
    for d in target_dirs:
        md = d / "manifest.md"
        if md.exists():
            for src, rel, sha in parse_manifest(md):
                recs.append((d, src, rel, sha))
        for hf in sorted(d.rglob("*hashes*.txt")):
            for src, rel, sha in parse_hashes_txt(hf):
                recs.append((d, src, rel, sha))
    return recs


# ---------- ตัวแก้เส้นทาง ----------

def build_index(d):
    """basename -> [path, ...] ใช้เป็นทางเลือกสุดท้ายเมื่อ path ใน manifest ไม่ตรงจริง
    (sort ให้ลำดับ deterministic ทุก OS — เดิมพึ่งลำดับ rglob ที่ต่างกันแต่ละระบบ)"""
    idx = {}
    for p in sorted(d.rglob("*")):
        if p.is_file():
            idx.setdefault(p.name, []).append(p)
    for k in idx:
        idx[k].sort()
    return idx


# รายการที่ resolve ด้วย basename แล้ว "ชนกันหลายไฟล์" — ใช้ไฟล์แรกต่อไปแต่ต้องเตือน
# (เพราะอาจแฮชผิดไฟล์แบบเงียบ ๆ — ทางแก้ถาวรคือให้ manifest ระบุ path ให้ตรง)
AMBIGUOUS = []  # [(dir, relpath, [Path, ...])]


def resolve(d, relpath, index):
    if relpath is None:
        return None
    rel = relpath.strip().lstrip("./")
    for cand in (d / rel, d / "raw" / rel, d / "derived" / rel):
        if cand.is_file():
            return cand
    hits = index.get(Path(rel).name)
    if hits:
        if len(hits) > 1:
            AMBIGUOUS.append((str(d), rel, hits))
        return hits[0]
    return None


# ---------- ตัวตรวจ ----------

def sha256_file(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def verify(target_dirs, max_bytes=None):
    exc = load_exceptions()
    rows = []
    for d in target_dirs:
        index = build_index(d)
        # ชื่อ directory ที่ใช้แสดง (โฟลเดอร์นอก ROOT เช่น --only ไปที่อื่น = ใช้ path เต็ม)
        try:
            dd_root = d.relative_to(ROOT).as_posix()
        except ValueError:
            dd_root = str(d)
        for dd, src, rel, sha in collect([d]):
            path = resolve(dd, rel, index)
            name = rel or "(path ไม่ทราบ)"
            try:
                key = (dd.relative_to(ROOT) / rel).as_posix() if rel else ""
            except ValueError:
                # โฟลเดอร์เป้าหมายอยู่นอก ROOT (เช่น --only ชี้ไปที่อื่น) — ใช้ key เต็มแทน
                key = (dd / rel).as_posix() if rel else ""
            reason = exc.get(key) or exc.get(Path(rel).name if rel else "")
            if path is None:
                if is_deleted(name):
                    status = "DELETED"
                elif reason:
                    status = "EXPLAINED"
                else:
                    status = "MISSING"
                rows.append((dd_root, src, name, status, None))
                continue
            if max_bytes is not None and path.stat().st_size > max_bytes:
                rows.append((dd_root, src, name, "SKIPPED", path.stat().st_size))
                continue
            got = sha256_file(path)
            rows.append((dd_root, src, name,
                         "OK" if got == sha else "MISMATCH", path.stat().st_size))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="ตรวจ SHA-256 ของ data/ กับไฟล์จริง")
    ap.add_argument("--only", action="append", default=None,
                    help="ตรวจเฉพาะโฟลเดอร์ เช่น --only data/19_rid_cross_sections (ใส่ซ้ำได้)")
    ap.add_argument("--quick", action="store_true", help="ข้ามไฟล์ > 5 MB")
    ap.add_argument("--max-bytes", type=int, default=None, help="ข้ามไฟล์ใหญ่กว่านี้ (ไบต์)")
    ap.add_argument("--json", default=None, help="เขียนผลเป็น JSON")
    ap.add_argument("--quiet", action="store_true", help="พิมพ์แค่สรุป")
    args = ap.parse_args(argv)

    if args.only:
        dirs = [ROOT / o if not Path(o).is_absolute() else Path(o) for o in args.only]
        missing = [d for d in dirs if not d.is_dir()]
        if missing:
            print("ไม่พบโฟลเดอร์:", ", ".join(str(m) for m in missing), file=sys.stderr)
            return 2
    else:
        dirs = sorted(d for d in DATA.iterdir() if d.is_dir())

    max_bytes = args.max_bytes if args.max_bytes is not None else (5 << 20 if args.quick else None)
    rows = verify(dirs, max_bytes)

    counts = {}
    for _, _, _, status, _ in rows:
        counts[status] = counts.get(status, 0) + 1

    if not args.quiet:
        for d, src, name, status, size in rows:
            if status in ("MISMATCH", "MISSING", "DELETED", "EXPLAINED", "SKIPPED"):
                sz = f"{size/1e6:,.1f} MB" if size else "-"
                print(f"  [{status:9s}] {d}  {name}   ({sz})  <- {src}")

    print("\n== สรุป ==")
    for k in ("OK", "MISMATCH", "MISSING", "DELETED", "EXPLAINED", "SKIPPED"):
        if k in counts:
            print(f"  {k:9s} {counts[k]}")
    print(f"  รวมที่บันทึกไว้ {len(rows)} แฮช")

    if args.json:
        Path(args.json).write_text(
            json.dumps({"counts": counts,
                        "rows": [{"dir": d, "source": s, "file": n, "status": st, "bytes": sz}
                                 for d, s, n, st, sz in rows]},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  -> {args.json}")

    if AMBIGUOUS:
        print(f"\n!! resolve ด้วย basename ที่ชนกัน {len(AMBIGUOUS)} รายการ — ใช้ไฟล์แรกต่อไป "
              "แต่ควรแก้ manifest ให้ระบุ path เต็ม (อาจแฮชผิดไฟล์แบบเงียบ ๆ):", file=sys.stderr)
        for d, rel, hits in AMBIGUOUS[:10]:
            print(f"   {d} :: {rel}  ->  {len(hits)} ตัวเลือก", file=sys.stderr)

    if counts.get("MISMATCH"):
        print("\n!! มีแฮชไม่ตรง — ไฟล์ถูกแก้หรือเสียหาย", file=sys.stderr)
        return 1
    if AMBIGUOUS:
        # GLM GL-18: เดิม "เตือนแล้วคืน 0" — เคสแฮชบังเอิญตรงไฟล์แรกผ่านเงียบ ๆ ทั้งที่
        # ผลตรวจของรายการนั้นใช้ยืนยันไม่ได้ → exit 3 (CI/run_all ล้มที่ code>2)
        print("\n!! มีรายการ resolve ด้วย basename ที่ชนกัน — ผลตรวจรายการนั้นใช้ยืนยันไม่ได้ (exit 3)", file=sys.stderr)
        return 3
    if counts.get("MISSING"):
        print("\n(มี MISSING — ส่วนใหญ่คือไฟล์ที่ไม่อยู่ใน git ไม่ใช่ไฟล์เสีย)", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
