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

    # 4. เอกสาร OCR (RapidOCR + Typhoon OCR)
    for p in list(ROOT.glob("data/32_goal7_chaophraya2/ocr/**/text.txt")) + list(
        ROOT.glob("data/32_goal7_chaophraya2/typhoon_ocr/**/document.md")
    ):
        rel = p.relative_to(ROOT).as_posix()
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            conn.execute(
                "INSERT INTO docs_fts(path, category, title, body) VALUES (?, ?, ?, ?)",
                (rel, "ocr", f"OCR: {p.parent.name}", txt)
            )
            indexed_count += 1
        except Exception:
            pass

    conn.commit()
    conn.close()

    elapsed = time.time() - t0
    if verbose:
        print(f"✅ ทำดัชนี Mini-FTS สำเร็จ: {indexed_count} รายการ ({elapsed:.2f} วินาที) ที่ {DB_PATH.name}")
    return indexed_count


def search(query: str, limit: int = 10) -> list[dict]:
    if not DB_PATH.exists():
        index_all(verbose=False)

    conn = get_db()
    terms = [t.replace('"', '').replace("'", '').strip() for t in query.split() if t.strip()]
    if not terms:
        return []

    # สำหรับ trigram ให้ match ทั้งใน title และ body
    clauses = []
    for t in terms:
        clauses.append(f'title:"{t}" OR body:"{t}"')
    fts_query = " AND ".join(f"({c})" for c in clauses)

    sql = """
        SELECT path, category, title, snippet(docs_fts, 3, '[', ']', '...', 20), rank
        FROM docs_fts
        WHERE docs_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """
    try:
        cur = conn.execute(sql, (fts_query, limit))
        rows = cur.fetchall()
        results = []
        for path, cat, title, snippet_text, rank in rows:
            results.append({
                "path": path,
                "category": cat,
                "title": title,
                "snippet": snippet_text.replace("\n", " ").strip(),
                "rank": round(float(rank), 3)
            })
        return results
    except Exception as e:
        return []
    finally:
        conn.close()


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
