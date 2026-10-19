"""เครื่องมือสืบค้นเนื้อหาเต็ม (Mini Full-Text Search Engine with SQLite FTS5)

ทำหน้าที่ทำดัชนีและค้นหาเนื้อหาเอกสารทั้งหมดในคลัง (Docs, Data Manifests, OCR texts, Analysis findings)
ให้ผลลัพธ์แบบ BM25 พร้อมไฮไลต์ข้อความ (snippet) ในระดับมิลลิวินาที
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TONE = re.compile(r"[่-์]")   # วรรณยุกต์/ไม้ทัณฑฆาต — OCR และชั้นข้อความ PDF มักลำดับอักขระต่างกัน จึงทำดัชนีเสริมแบบตัดทิ้ง
DB_PATH = ROOT / "data/search_index.db"


def get_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
            path UNINDEXED,
            category,
            title,
            body,
            tokenize = 'trigram'
        )
    """)
    return conn


def index_all(verbose: bool = True) -> int:
    t0 = time.time()
    conn = get_db()
    conn.execute("DELETE FROM docs_fts")

    indexed_count = 0

    # 1. Markdown เอกสารและข้อกำหนด
    for md in list(ROOT.glob("*.md")) + list(ROOT.glob("docs/**/*.md")):
        if ".git" in str(md) or "node_modules" in str(md):
            continue
        rel = md.relative_to(ROOT).as_posix()
        try:
            txt = md.read_text(encoding="utf-8", errors="ignore")
            title = md.name
            for ln in txt.splitlines():
                if ln.startswith("# "):
                    title = ln.lstrip("# ").strip()
                    break
            conn.execute(
                "INSERT INTO docs_fts(path, category, title, body) VALUES (?, ?, ?, ?)",
                (rel, "docs", title, txt)
            )
            indexed_count += 1
        except Exception:
            pass

    # 2. Data manifests ทั่วทั้งคลังข้อมูลดิบ 200GB
    for man in ROOT.glob("data/**/manifest.md"):
        rel = man.relative_to(ROOT).as_posix()
        try:
            txt = man.read_text(encoding="utf-8", errors="ignore")
            conn.execute(
                "INSERT INTO docs_fts(path, category, title, body) VALUES (?, ?, ?, ?)",
                (rel, "data_manifest", man.parent.name, txt)
            )
            indexed_count += 1
        except Exception:
            pass

    # 3. ผลการวิเคราะห์และข้อเท็จจริงสำคัญ (Analysis markdown & findings)
    for p in list(ROOT.glob("analysis/**/*.md")) + [
        ROOT / "analysis/canonical_numbers.json",
        ROOT / "analysis/goal6/canonical.json",
        ROOT / "analysis/goal7/canonical.json",
        ROOT / "analysis/goal7/gaps.json",
        ROOT / "analysis/goal7/ocr_findings.json",
        ROOT / "analysis/goal7/dam_to_gulf_summary.json",
        ROOT / "analysis/goal7/bangban_bangsai_comparison.json",
    ]:
        if not p.exists():
            continue
        rel = p.relative_to(ROOT).as_posix()
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            conn.execute(
                "INSERT INTO docs_fts(path, category, title, body) VALUES (?, ?, ?, ?)",
                (rel, "analysis", p.stem, txt)
            )
            indexed_count += 1
        except Exception:
            pass

    # 4. OCR รายหน้า: Typhoon-OCR เท่านั้น (ตัดสินใจ 19 ต.ค. 69) — หน้า echo/ถอดไม่ได้ไม่ถูกทำดัชนี
    import json

    D32 = ROOT / "data/32_goal7_chaophraya2"
    for jl in sorted(D32.glob("typhoon_ocr/*/pages*.jsonl")):
        label = jl.parent.name
        for ln in jl.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            txt = (r.get("text") or "").strip()
            if not txt or r.get("error") or (r.get("meta") or {}).get("echo_final") or "RAW_TEXT_START" in txt:
                continue
            conn.execute(
                "INSERT INTO docs_fts(path, category, title, body) VALUES (?, ?, ?, ?)",
                (f"{jl.parent.relative_to(ROOT).as_posix()}#p{r['page']}", "ocr_typhoon", f"Typhoon OCR {label} หน้า {r['page']}", txt + " " + TONE.sub("", txt)),
            )
            indexed_count += 1
    # RapidOCR เลิกใช้ (ผู้ใช้ 19 ต.ค. 69) — ไม่ทำดัชนีผลเดิมใน data/32_goal7_chaophraya2/ocr/

    # 5. ชั้นข้อความของเล่ม EIA 2569 รายหน้า (ค้นหาค่าที่รายงานระบุตรงได้ทันที — เช่น "ก้นคลองกว้าง 51 เมตร")
    try:
        import fitz

        for pdf in sorted((D32 / "official_eia/extracted").glob("*.pdf")):
            doc = fitz.open(pdf)
            for i, pg in enumerate(doc, 1):
                txt = (pg.get_text() or "").strip()
                if len(txt) < 40:
                    continue
                conn.execute(
                    "INSERT INTO docs_fts(path, category, title, body) VALUES (?, ?, ?, ?)",
                    (f"{pdf.relative_to(ROOT).as_posix()}#p{i}", "eia_text", f"EIA 2569 {pdf.stem} หน้าไฟล์ {i}", " ".join(txt.split()) + " " + TONE.sub("", " ".join(txt.split()))),
                )
                indexed_count += 1
            doc.close()
    except ImportError:
        pass

    conn.commit()
    conn.close()

    elapsed = time.time() - t0
    if verbose:
        print(f"✅ ทำดัชนี Mini-FTS สำเร็จ: {indexed_count} รายการ ({elapsed:.2f} วินาที) ที่ {DB_PATH.name}")
    return indexed_count


def is_stale(db_path: Path = DB_PATH) -> bool:
    """ตรวจสอบว่ามีเอกสารใหม่หรือไฟล์วิเคราะห์แก้ไขหลังจากทำดัชนีครั้งล่าสุดหรือไม่"""
    if not db_path.exists():
        return True
    db_mtime = db_path.stat().st_mtime
    # 1. ตรวจสอบไฟล์ Markdown เอกสารและข้อกำหนด
    for md in list(ROOT.glob("*.md")) + list(ROOT.glob("docs/**/*.md")):
        if ".git" in str(md) or "node_modules" in str(md):
            continue
        try:
            if md.stat().st_mtime > db_mtime:
                return True
        except Exception:
            pass
    # 2. ตรวจสอบไฟล์การวิเคราะห์หลัก
    for p in [
        ROOT / "analysis/canonical_numbers.json",
        ROOT / "analysis/goal6/canonical.json",
        ROOT / "analysis/goal7/canonical.json",
        ROOT / "analysis/goal7/gaps.json",
        ROOT / "analysis/goal7/dam_to_gulf_summary.json",
        ROOT / "analysis/goal7/bangban_bangsai_comparison.json",
    ]:
        if p.exists() and p.stat().st_mtime > db_mtime:
            return True
    D32 = ROOT / "data/32_goal7_chaophraya2"
    for p in list(D32.glob("typhoon_ocr/*/pages*.jsonl")) + list((D32 / "official_eia/extracted").glob("*.pdf")):
        try:
            if p.stat().st_mtime > db_mtime:
                return True
        except Exception:
            pass
    return False


def search(query: str, limit: int = 10) -> list[dict]:
    if not DB_PATH.exists() or is_stale():
        index_all(verbose=False)

    conn = get_db()
    terms = [t.replace('"', '').replace("'", '').strip() for t in query.split() if t.strip()]
    if not terms:
        return []

    # รอบ 6: ตัวค้นของ FTS5 แบบ trigram พลาดคำไทยจำนวนมากที่ LIKE หาเจอ (เช่น "คลองระบาย" FTS 10 หน้า vs จริง 587 หน้า; SQLite 3.50.4)
    # คลังมีไม่ถึง 3,000 แถว — ใช้สแกนด้วย LIKE (ทุกคำต้องอยู่ ตัดวรรณยุกต์ด้วย) แล้วจัดอันดับตามจำนวนครั้งที่พบ แม่นกว่าและเร็วพอ (มิลลิวินาที)
    conn_rows = conn.execute("SELECT path, category, title, body FROM docs_fts WHERE " + " AND ".join(
        "(body LIKE ? OR title LIKE ?" + (" OR body LIKE ?" if TONE.sub("", t) != t else "") + ")" for t in terms),
        [x for t in terms for x in ((f"%{t}%", f"%{t}%") + ((f"%{TONE.sub('', t)}%",) if TONE.sub("", t) != t else ()))]).fetchall()
    scored = []
    for path, cat, title, body in conn_rows:
        low = body
        n = 0
        first = -1
        for t in terms:
            for cand in {t, TONE.sub("", t)}:
                c_ = low.count(cand)
                n += c_
                if c_ and (first < 0 or low.find(cand) < first):
                    first = low.find(cand)
        scored.append((n + (5 if any(t in title for t in terms) else 0), path, cat, title, body, first))
    scored.sort(key=lambda r: -r[0])
    results = []
    for n, path, cat, title, body, first in scored[:limit]:
        s = max(0, first - 60) if first >= 0 else 0
        results.append({"path": path, "category": cat, "title": title, "snippet": body[s:s + 200].replace(chr(10), " ").strip(), "rank": -float(n)})
    conn.close()
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="เครื่องมือสืบค้นเนื้อหาเต็ม (Mini-FTS)")
    parser.add_argument("query", nargs="?", help="คำค้นหา")
    parser.add_argument("--reindex", action="store_true", help="สร้างดัชนีใหม่")
    parser.add_argument("--limit", type=int, default=10, help="จำนวนผลลัพธ์สูงสุด")

    args = parser.parse_args()

    if args.reindex or not DB_PATH.exists():
        index_all(verbose=True)

    if args.query:
        t0 = time.time()
        res = search(args.query, limit=args.limit)
        print(f"\n🔍 ผลการค้นหาสำหรับ: '{args.query}' ({len(res)} รายการ, {(time.time() - t0)*1000:.1f} ms)\n")
        for idx, r in enumerate(res, 1):
            print(f"{idx}. [{r['category'].upper()}] {r['title']} ({r['path']})")
            print(f"   ↳ {r['snippet']}\n")
