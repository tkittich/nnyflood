#!/usr/bin/env python3
"""tools/number_inventory.py — บัญชีตัวเลขทั้งคลัง: หาค่าที่ขัดกัน / ไม่มีที่มา / ล้าสมัย (รอบ 6, R7-07/R7-08 ขั้นแรก)

ทำไมต้องมี: ตัวตรวจเดิมตรวจว่า "ค่าที่รู้ว่าผิดไม่กลับมา" ไม่ตรวจว่า "ตัวเลขที่ใช้อยู่ตรงกันและมีที่มา" —
เครื่องมือนี้สแกนทุกแหล่งแล้วออกรายงานให้คนตัดสิน (ไม่แก้อะไรเอง · อ่านอย่างเดียว)

ตรวจ 5 อย่าง:
  A. ปริมาณเดียวกัน ค่าต่างกัน — ตารางแนวคิด CONCEPTS (ป้ายภาษาไทย + หน่วย + ช่วงค่า) ดึงตัวเลขจาก HTML รายงาน/เอกสาร/builder
     แล้วรวมกลุ่มตามค่า (ความคลาดเคลื่อน ≤ 0.15%) → แนวคิดที่มี ≥ 2 ค่าแยกกันถูกรายงาน
  B. ตัวเลขกำพร้า — ตัวเลขมีหน่วยในข้อความผู้อ่าน (HTML) ที่ไม่ตรงค่าใดใน JSON ของ analysis/ (เทียบที่ทศนิยมเท่าที่พิมพ์)
     = พิมพ์ตรงจาก builder / คำนวณต่อโดยไม่มีที่มาใน JSON → รายการงานตรวจที่มา
  C. คีย์ JSON ชื่อเดียวกัน ค่าต่างกันข้ามไฟล์ (เฉพาะคีย์ที่มีหน่วยต่อท้าย)
  D. ตัวเลขที่ฝังในสตริงของ builder (AST) — ตัวเลข ≥ 3 หลักที่มีหน่วย อยู่ใน literal ไม่ใช่ f-string ช่อง {...}
  ประตูชั้นที่ 2 (R7-29 รีวิวรอบ 7): ตัวเลขฝังใน builder ที่ค่าไปตรงกับ JSON ก็ตรึงจำนวนแบบ ratchet ด้วย (analysis/goal7/literal_allowlist_traced.json) · และสแกน 'ร้อยละ N'
  E. ตัวเลขนับในเอกสารสถานะที่ล้าสมัย (จำนวนรายการสารบัญ ฯลฯ เทียบค่าจริง)

ใช้: python tools/number_inventory.py [--out docs/reviews/INVENTORY_YYYY-MM-DD.md] [--json out.json]
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------- หน่วย ----------
UNITS = [
    ("ล้าน ลบ.ม./วัน", "mcm_day"), ("ล้านลูกบาศก์เมตร", "mcm"), ("ล้าน ลบ.ม.", "mcm"), ("ลลบ.ม.", "mcm"),
    ("ลบ.ม./วินาที", "cms"), ("ลบ.ม./วิ", "cms"), ("ม³/วิ", "cms"), ("ม³/วินาที", "cms"),
    ("บาท/ลบ.ม.", "thb_m3"), ("บาทต่อลูกบาศก์เมตร", "thb_m3"), ("ล้านบาท/ปี", "mb_yr"), ("ล้านบาท", "mb"),
    ("ตร.กม.", "km2"), ("ตร.ม.", "m2"), ("ม.รทก.", "msl"), ("กม.", "km"), ("ซม.", "cm"), ("ม.", "m"),
    ("ชั่วโมง", "h"), ("ชม.", "h"), ("วัน", "day"), ("ปี", "year"), ("ไร่", "rai"), ("หลัง", "house"), ("%", "pct"),
]
UNITS.sort(key=lambda u: -len(u[0]))
UNIT_ALT = "|".join(re.escape(u) for u, _ in UNITS)
UNIT_MAP = dict(UNITS)
NUM_RE = re.compile(r"(?<![\w.,/\-:])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?\s{0,2}(" + UNIT_ALT + r")(?![ก-๙A-Za-z])")

# ---------- แนวคิดที่ตรวจ (ป้ายที่ใกล้ตัวเลข + หน่วย + ช่วงค่าที่สมเหตุสมผล) ----------
CONCEPTS = [
    ("ความยาวคลองช่วงใหม่", r"ความยาว|ช่วงใหม่|ทั้งคลอง|ทั้งสาย", "km", (130, 150)),
    ("ความกว้างท้องคลอง", r"ท้องคลอง", "m", (30, 120)),
    ("ความกว้างผิวน้ำ", r"ผิวน้ำ", "m", (60, 120)),
    ("งบลงทุนโครงการ", r"งบลงทุน|วงเงินลงทุน|กรอบ(เงิน|งบ)|เพดาน|งบประมาณ", "mb", (100000, 300000)),
    ("ที่ดินเวนคืน", r"เวนคืน", "rai", (10000, 25000)),
    ("ปริมาตรกักเก็บของคลอง", r"คลอง.{0,40}(ความจุ|กักเก็บ|ปริมาตร)|(ความจุ|กักเก็บ|ปริมาตร).{0,40}คลอง", "mcm", (10, 200)),
    ("อัตราผันออกแบบของคลอง", r"คลอง|ผัน|ระบาย|ออกแบบ", "cms", (550, 650)),
    ("ความจุตลิ่ง/ลำน้ำ", r"ตลิ่ง|ความจุลำน้ำ", "cms", (400, 900)),
    ("วันเทียบเท่าเต็มกำลัง", r"เต็มกำลัง|เทียบเท่า", "day", (5, 140)),
    ("ต้นทุนต่อน้ำผัน", r"ต้นทุน|น้ำผัน", "thb_m3", (3, 20)),
    ("ฝนสะสม/น้ำท่วมแผ่นดินพื้นที่", r"น้ำท่วม|ท่วม", "km2", (100, 600)),
]
TOL = 0.0015  # 0.15%


def sig3(v: float) -> float:
    return float(f"{v:.3g}")


# ---------- โหลดแหล่งข้อความ ----------
def html_segments(path: Path):
    t = path.read_text(encoding="utf-8", errors="ignore")
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S)
    t = re.sub(r'<img[^>]*?src="data:[^"]{100,}"', "<img ", t)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"</(p|div|tr|li|h\d|table|section|figure|figcaption|caption)>|<br\s*/?>", "\n", t)
    t = re.sub(r"</t[dh]>", " | ", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    for i, line in enumerate(t.splitlines(), 1):
        if line.strip():
            yield i, line


def md_segments(path: Path):
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if line.strip():
            yield i, line


def py_string_literals(path: Path):
    """คืน (บรรทัด, ข้อความ, อยู่ใน f-string หรือไม่) — เฉพาะส่วนคงที่ของสตริง"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return
    fparts = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.JoinedStr):
            for v in n.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    fparts.add(id(v))
                    yield v.lineno, v.value, True
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in fparts:
            yield n.lineno, n.value, False


# "ร้อยละ N" (ไม่มี % ตามหลัง) — รีวิวรอบ 7 พบว่าตัวเลขแบบนี้ (เช่น "ร้อยละ 20.6") หลุดตัวสแกนเดิมที่ต้องมีหน่วยตามหลังตัวเลข
RATIO_RE = re.compile(r"ร้อยละ\s{0,2}(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?!\.?\d)(?!\s{0,2}%)")


def extract(line: str):
    for m in NUM_RE.finditer(line):
        ip, fp, unit = m.group(1), m.group(2), m.group(3)
        val = float(ip.replace(",", "") + ("." + fp if fp else ""))
        yield m.start(), val, (len(fp) if fp else 0), UNIT_MAP[unit], m.group(0)
    for m in RATIO_RE.finditer(line):
        ip, fp = m.group(1), m.group(2)
        yield m.start(), float(ip.replace(",", "") + ("." + fp if fp else "")), (len(fp) if fp else 0), "pct", m.group(0)


def sources():
    reports = sorted((ROOT / "report").glob("*.html"))
    docs = [p for p in [*ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md")] if p.name != "OFFLINE_DATA_BACKLOG.md"]
    builders = sorted((ROOT / "report").glob("*.py"))
    return reports, docs, builders


# ---------- A: ปริมาณเดียวกันค่าต่างกัน ----------
def concept_scan(reports, docs):
    found = defaultdict(lambda: defaultdict(list))   # concept -> sig3 value -> [(file, line, context)]
    for kind, files, gen in (("report", reports, html_segments), ("doc", docs, md_segments)):
        for f in files:
            for ln, line in gen(f):
                for pos, val, dec, unit, raw in extract(line):
                    ctx = line[max(0, pos - 70): pos + 8]
                    for name, lab, u, (lo, hi) in CONCEPTS:
                        if unit == u and lo <= val <= hi and re.search(lab, ctx):
                            found[name][sig3(val)].append((f.name, ln, ctx.strip(), kind))
    out = {}
    for name, vals in found.items():
        # รวมค่าที่ต่างกันไม่เกิน TOL
        groups = []
        for v in sorted(vals):
            if groups and abs(v - groups[-1][0]) <= TOL * max(v, 1e-9):
                groups[-1][1].extend(vals[v])
            else:
                groups.append([v, list(vals[v])])
        if len(groups) >= 2:
            out[name] = [{"value": g[0], "n": len(g[1]), "files": sorted({x[0] for x in g[1]}), "example": g[1][0][:3]} for g in groups]
    return out


# ---------- ดัชนีค่าใน JSON ----------
def json_leaves():
    leaves = defaultdict(set)   # key -> {(file, value)}
    values = []
    for p in sorted((ROOT / "analysis").rglob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        rel = str(p.relative_to(ROOT))
        if p.stat().st_size > 400_000 and not p.name.startswith("canonical"):
            continue   # อนุกรมเวลาขนาดใหญ่ทำให้ตัวเลขใด ๆ "บังเอิญตรง" — ตัดออกจากดัชนีที่มา

        def walk(o, key=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    walk(v, k)
            elif isinstance(o, list):
                if len(o) > 300 and all(isinstance(x, (int, float)) for x in o[:5]):
                    return   # อนุกรมตัวเลขยาว
                for v in o[:2000]:
                    if isinstance(v, (dict, list)):
                        walk(v, key)
                    elif isinstance(v, (int, float)) and not isinstance(v, bool):
                        values.append(float(v))
            elif isinstance(o, (int, float)) and not isinstance(o, bool):
                values.append(float(o))
                leaves[key].add((rel, float(o)))
        walk(d)
    return leaves, values


def known_set(values):
    ks = {d: set() for d in range(0, 5)}
    for v in values:
        for scale in (1.0, 100.0, 1e-6):
            w = v * scale
            for d in range(0, 5):
                ks[d].add(round(w, d))
    return ks


# ---------- B: ตัวเลขกำพร้าในรายงาน ----------
def orphan_scan(reports, ks):
    cnt = defaultdict(lambda: {"n": 0, "files": set(), "example": ""})
    for f in reports:
        for ln, line in html_segments(f):
            for pos, val, dec, unit, raw in extract(line):
                digits = len(str(int(val)).lstrip("0")) + dec
                if digits < 3 or unit in ("year",) or (unit == "pct" and val <= 100 and dec == 0):
                    continue
                if 2400 <= val <= 2600 and unit == "year":
                    continue
                if round(val, dec) in ks[min(dec, 4)] and not (dec == 0 and val < 1000):
                    continue
                k = (val, unit)
                e = cnt[k]
                e["n"] += 1
                e["files"].add(f.name)
                if not e["example"]:
                    e["example"] = line[max(0, pos - 50): pos + 20].strip()
    rows = [{"value": k[0], "unit": k[1], "n": v["n"], "files": sorted(v["files"]), "example": v["example"]} for k, v in cnt.items()]
    rows.sort(key=lambda r: (-len(r["files"]), -r["n"]))
    return rows


# ---------- C: คีย์ JSON ชื่อเดียวกัน ค่าต่างกัน ----------
KEY_SUFFIX = re.compile(r"(_km|_m|_mcm|_cms|_m3s|_pct|_mb|_rai|_h|_hours|_days|_m2|_km2|_msl_m)$")


def key_conflicts(leaves):
    out = []
    for key, items in leaves.items():
        if not KEY_SUFFIX.search(key):
            continue
        by_val = defaultdict(set)
        for f, v in items:
            by_val[sig3(v)].add(f)
        files = {f for _, fs in by_val.items() for f in fs}
        if len(by_val) >= 2 and len(files) >= 2:
            out.append({"key": key, "values": {str(v): sorted(fs)[:3] for v, fs in sorted(by_val.items())[:6]}, "n_files": len(files)})
    out.sort(key=lambda r: (-r["n_files"], r["key"]))
    return out


# ---------- D: literal ในสตริงของ builder ----------
def builder_literals(builders):
    rows = []
    for b in builders:
        for ln, s, in_f in py_string_literals(b):
            if "# gap:" in s and len(s) < 3:
                continue
            for pos, val, dec, unit, raw in extract(s):
                digits = len(str(int(val)).lstrip("0")) + dec
                if digits >= 3 and unit not in ("year",) and not (2400 <= val <= 2600):
                    rows.append({"file": b.name, "line": ln, "text": raw, "ctx": s[max(0, pos - 30): pos + 25].replace("\n", " ")})
    return rows


# ---------- ประตูตัวเลขฝังใน builder แบบรายการที่อนุญาต (R7-07) ----------
ALLOWLIST = ROOT / "analysis/goal7/literal_allowlist.json"


def untraced_literals(builders, ks):
    """ตัวเลข (≥ 3 หลัก มีหน่วย) ที่ฝังในสตริงคงที่ของ builder และไม่ตรงค่าใดใน JSON ของ analysis/ → นับต่อ (ไฟล์, ข้อความ)"""
    cnt: dict[tuple[str, str], int] = defaultdict(int)
    for x in builder_literals(builders):
        _, val, dec, _unit, _raw = next(iter(extract(x["text"])))
        if round(val, dec) in ks[min(dec, 4)] and not (dec == 0 and val < 1000):
            continue
        cnt[(x["file"], x["text"])] += 1
    return dict(cnt)


# ---------- ประตูชั้นที่ 2: ตัวเลขฝังที่ "ตรงค่าใน JSON โดยบังเอิญหรือโดยตั้งใจ" (รีวิวรอบ 7 R7-29) ----------
# ประตูชั้นแรกปล่อยผ่านทุกตัวเลขที่ค่าไปตรงกับ JSON ไฟล์ใดก็ได้ — จึงไม่จับตัวเลขที่พิมพ์ตรงใน builder แล้วค่าไปพ้องกับคนละความหมาย
# (เจอจริง: เอกสารนโยบายพิมพ์ "22.4 กม." และ "ช่วง 1.0–3.3 ม." เองแล้วลอยจาก canonical) · ชั้นนี้ตรึงจำนวนแบบ ratchet: เพิ่มใหม่ไม่ได้
ALLOWLIST_TRACED = ROOT / "analysis/goal7/literal_allowlist_traced.json"


def traced_literals(builders, ks):
    cnt: dict[tuple[str, str], int] = defaultdict(int)
    for x in builder_literals(builders):
        _, val, dec, _unit, _raw = next(iter(extract(x["text"])))
        if round(val, dec) in ks[min(dec, 4)] and not (dec == 0 and val < 1000):
            cnt[(x["file"], x["text"])] += 1
    return dict(cnt)


def load_allowlist_traced() -> dict[tuple[str, str], int]:
    d = json.loads(ALLOWLIST_TRACED.read_text(encoding="utf-8"))
    return {(e["file"], e["text"]): e["count"] for e in d["entries"]}


def gate_traced_violations(builders, ks, allow=None):
    allow = load_allowlist_traced() if allow is None else allow
    cur = traced_literals(builders, ks)
    new = {k: v for k, v in cur.items() if v > allow.get(k, 0)}
    stale = {k: v for k, v in allow.items() if cur.get(k, 0) < v}
    return new, stale


def load_allowlist() -> dict[tuple[str, str], int]:
    d = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    return {(e["file"], e["text"]): e["count"] for e in d["entries"]}


def gate_violations(builders, ks, allow=None):
    """คืน (ใหม่/เพิ่มจำนวน, ค้างในรายการแต่ไม่มีแล้ว) — รายการใหม่ต้องเป็น 0 (เพิ่มตัวเลขฝังใหม่ = เทสต์ตก) และรายการค้างต้องถอดออก (ratchet ลงอย่างเดียว)"""
    allow = load_allowlist() if allow is None else allow
    cur = untraced_literals(builders, ks)
    new = {k: v for k, v in cur.items() if v > allow.get(k, 0)}
    stale = {k: v for k, v in allow.items() if cur.get(k, 0) < v}
    return new, stale


def _keep_status(path, default: str) -> dict:
    """คงสถานะที่คนจัดประเภทไว้แล้ว (เช่น method_parameter) เมื่อเขียนรายการใหม่ — ไม่ล้างกลับเป็นค่าตั้งต้น"""
    if not path.exists():
        return {}
    return {(e["file"], e["text"]): {k: v for k, v in e.items() if k in ("status", "source_constant")}
            for e in json.loads(path.read_text(encoding="utf-8")).get("entries", []) if e.get("status") != default}


def write_allowlist() -> int:
    _, _, builders = sources()
    _, values = json_leaves()
    cur = untraced_literals(builders, known_set(values))
    kept = _keep_status(ALLOWLIST, "legacy_unreviewed")
    entries = [{"file": f, "text": s, "count": n, **kept.get((f, s), {"status": "legacy_unreviewed"})} for (f, s), n in sorted(cur.items())]
    ALLOWLIST.write_text(json.dumps({"note": "ตัวเลขฝังใน builder ที่ยังไม่มีที่มาใน JSON — baseline ของประตู ratchet: เพิ่มใหม่ไม่ได้ มีแต่ลดลง · เมื่อย้ายไปอ่านจาก JSON/โทเคนแล้วให้รัน tools/number_inventory.py --write-allowlist (ตรวจ git diff ทุกครั้ง — ต้องมีแต่การลบ)",
                                    "entries": entries}, ensure_ascii=False, indent=1), encoding="utf-8")
    traced = traced_literals(builders, known_set(values))
    kept_t = _keep_status(ALLOWLIST_TRACED, "traced_by_value_unreviewed")
    t_entries = [{"file": f, "text": s, "count": n, **kept_t.get((f, s), {"status": "traced_by_value_unreviewed"})} for (f, s), n in sorted(traced.items())]
    ALLOWLIST_TRACED.write_text(json.dumps({"note": "ตัวเลขฝังใน builder ที่ค่าไปตรงกับ JSON (อาจพ้องโดยบังเอิญ) — baseline ประตูชั้นที่ 2 แบบ ratchet: เพิ่มใหม่ไม่ได้ มีแต่ลดลง · ย้ายไปอ่านจาก JSON/โทเคนแล้วให้รัน tools/number_inventory.py --write-allowlist (ตรวจ git diff — ต้องมีแต่การลบ)",
                                            "entries": t_entries}, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(entries)


# ---------- E: เอกสารสถานะที่ล้าสมัย ----------
def stale_status_counts():
    issues = []
    try:
        out = subprocess.run([sys.executable, str(ROOT / "catalog.py"), "check"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT).stdout
        m = re.search(r"(\d+)\s*รายการ", out)
        n_cat = int(m.group(1)) if m else None
    except Exception:
        n_cat = None
    if n_cat:
        for f in (ROOT / "START_HERE.md", ROOT / "README.md", ROOT / "HANDOFF.md"):
            if not f.exists():
                continue
            for ln, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if "catalog.py check" in line:
                    mm = re.search(r"\((\d+)\s*รายการ\)", line)
                    if mm and int(mm.group(1)) != n_cat:
                        issues.append({"file": f.name, "line": ln, "says": int(mm.group(1)), "actual": n_cat, "what": "จำนวนรายการสารบัญ"})
    return issues


def render(res) -> str:
    L = ["# บัญชีตัวเลขทั้งคลัง (number inventory)", "",
         f"สร้างโดย `tools/number_inventory.py` · อ่านอย่างเดียว · รายการเป็น **รายการให้คนตัดสิน** ไม่ใช่ข้อสรุปว่าผิด", ""]
    L += ["## A. ปริมาณเดียวกัน ค่าต่างกัน", "",
          "แต่ละแนวคิดดึงจากตัวเลขที่ป้ายใกล้เคียง+หน่วย+ช่วงค่าตรงกัน · ค่าต่างกันอาจเป็น \"คนละบริบท\" (ถูกต้อง) หรือ \"ค่าขัดกัน\" (ต้องแก้) — ดูตัวอย่างประกอบ", ""]
    for name, groups in res["A"].items():
        L.append(f"### {name} — {len(groups)} ค่า")
        for g in groups:
            ex = g["example"]
            L.append(f"- **{g['value']:g}** ×{g['n']} ({', '.join(g['files'][:4])}{'…' if len(g['files']) > 4 else ''}) — `{ex[2][-60:]}`")
        L.append("")
    L += ["## B. ตัวเลขกำพร้าในรายงาน (ไม่พบในไฟล์ JSON ใดของ analysis/)", "",
          f"รวม {len(res['B'])} ค่า · แสดง 60 อันดับแรก (เรียงตามจำนวนรายงานที่พบ)", "", "| ค่า | หน่วย | จำนวนครั้ง | รายงาน | ตัวอย่าง |", "|---|---|---|---|---|"]
    for r in res["B"][:60]:
        L.append(f"| {r['value']:g} | {r['unit']} | {r['n']} | {len(r['files'])} | {r['example'][:70].replace('|', '/')} |")
    L += ["", "## C. คีย์ JSON ชื่อเดียวกัน ค่าต่างกันข้ามไฟล์", "", f"รวม {len(res['C'])} คีย์ · แสดง 40 อันดับแรก", ""]
    for r in res["C"][:40]:
        L.append(f"- `{r['key']}` ({r['n_files']} ไฟล์): " + " · ".join(f"{v} ← {fs[0]}" for v, fs in list(r["values"].items())[:4]))
    L += ["", "## D. ตัวเลขที่พิมพ์ตรงใน builder (literal)", "", f"รวม {len(res['D'])} จุด · แสดงสรุปรายไฟล์", ""]
    per = defaultdict(int)
    for r in res["D"]:
        per[r["file"]] += 1
    for f, n in sorted(per.items(), key=lambda x: -x[1]):
        L.append(f"- `{f}`: {n} จุด")
    L += ["", "## E. เอกสารสถานะที่ล้าสมัย", ""]
    L += [f"- `{i['file']}:{i['line']}` {i['what']}: เอกสารเขียน {i['says']} แต่จริง {i['actual']}" for i in res["E"]] or ["- ไม่พบ"]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--write-allowlist", action="store_true", help="เขียน baseline ประตูตัวเลขฝัง (ตรวจ git diff — ต้องมีแต่การลบ)")
    a = ap.parse_args()
    if a.write_allowlist:
        print("เขียนรายการอนุญาต", write_allowlist(), "รายการ")
        return
    reports, docs, builders = sources()
    leaves, values = json_leaves()
    ks = known_set(values)
    res = {
        "A": concept_scan(reports, docs),
        "B": orphan_scan(reports, ks),
        "C": key_conflicts(leaves),
        "D": builder_literals(builders),
        "E": stale_status_counts(),
    }
    md = render(res)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    else:
        print(md)
    if a.json:
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"A={len(res['A'])} แนวคิดมีหลายค่า · B={len(res['B'])} ค่ากำพร้า · C={len(res['C'])} คีย์ขัด · D={len(res['D'])} literal · E={len(res['E'])} เอกสารล้าสมัย", file=sys.stderr)


if __name__ == "__main__":
    main()
