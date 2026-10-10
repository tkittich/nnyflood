"""สแกนรายงานที่ 3 — หาคำทับศัพท์/ศัพท์เทคนิคที่ยังไม่อนุมัติคำไทยแทน

งานตามข้อตกลง 12 ต.ค. 69: ตรวจหาอัตโนมัติ · อนุมัติคำแปลโดยคน
- อ่านรายงานที่สร้างแล้ว (ร่าง) → ตัด style/code/แท็ก
- แบ่งคำ: (1) อยู่ใน BANNED_TERMS/allowed แล้ว = ผ่าน (2) อังกฤษที่ยังเหลือ = candidate
- เขียน report/goal6_banned_terms_candidates.json (คำ + บริบท + จำนวน) — **ไม่แก้ BANNED_TERMS เอง**
- คำที่อนุมัติแล้ว (คนเติมใน BANNED_TERMS) จะหายจาก candidates ในรอบถัดไปเอง

รัน: python analysis/goal6_scan_banned_terms.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "report"))
from goal6_reportlib import BANNED_TERMS  # noqa: E402

DRAFT = ROOT / "report/รายงานที่3_ระลอกปลายกย2569_6ลุ่ม_ร่าง.html"
OUT = ROOT / "report/goal6_banned_terms_candidates.json"

# คำที่อนุมัติใช้ได้แล้ว (คนกำหนด — ไม่ใช่คำไทยแทน แต่เป็นรหัส/ชื่อเฉพาะ/หน่วย/ตัวย่อที่ผู้อ่านต้องเห็น)
ALLOWED_TOKENS = {
    # รหัสสถานี/เขื่อน: จับ pattern แยกในโค้ด
    # ชื่อดาวเทียม/ระบบ/องค์กร (อ้างชื่อเฉพาะ — เขียนคำอธิบายไทยคู่ไว้ในข้อความ)
    "Sentinel", "Landsat", "Copernicus", "GISTDA", "NASA", "POWER", "ERA5",
    "CDSE", "TMD", "EGAT", "Google",
    # ตัวย่อทางเทคนิคที่ใช้ในตาราง/กราฟ (อธิบายครั้งแรกแล้ว)
    "VH", "VV", "S1", "S2", "DEM", "URC", "LRC", "GBDT", "RMSE", "MAE",
    "SCL", "MNDWI", "COG", "GRD", "API", "FOI", "PDPA", "SNS", "QA",
    # หน่วย/เวลา
    "GB", "MB", "km", "UTC", "HH", "MM", "SDV", "BKK", "BKC", "CPY", "AIT", "CAN", "GLF", "GLO", "AI",
    # ชื่อโปรแกรม/ไฟล์ (อยู่ใน code tags — ถูกตัดก่อนแล้ว)
    "API", "JSON", "CSV",
}


def extract_body(html: str) -> str:
    body = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    body = re.sub(r"<code>.*?</code>", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r'\b(?:style|href|id|class|src|alt|colspan)="[^"]*"', " ", body)
    return body


def is_station_code(ctx: str) -> bool:
    """รหัสสถานี/เขื่อน เช่น Ny.7 · Kgt.3 · C.2 · S.26 — จับจากบริบทรอบคำ"""
    return bool(re.search(r"[A-Za-z]+\.\d", ctx))


def main() -> None:
    if not DRAFT.exists():
        raise SystemExit("ร่างยังไม่ถูกสร้าง — รัน python report/goal6_build_report3_draft.py ก่อน")
    h = DRAFT.read_text(encoding="utf-8")
    body = extract_body(h)

    banned_lower = {b.lower() for b in BANNED_TERMS}
    allowed_lower = {a.lower() for a in ALLOWED_TOKENS}

    tokens = Counter()
    contexts: dict[str, list[str]] = {}
    for m in re.finditer(r"[A-Za-z][A-Za-z\-']{1,}", body):
        tok = m.group(0)
        if tok.lower() in banned_lower or tok.lower() in allowed_lower:
            continue
        ctx = body[max(0, m.start() - 40):m.end() + 40].replace("\n", " ").strip()
        if is_station_code(ctx):
            continue
        if re.search(r"Sentinel-[12]", ctx) or re.search(r"GLO-30", ctx):
            continue
        # ตัดเศษจากการตัดแท็ก (คำที่ติดกันผิด ๆ)
        if not re.search(r"[A-Za-z]{2}", tok):
            continue
        tokens[tok] += 1
        contexts.setdefault(tok, [])
        if len(contexts[tok]) < 3:
            contexts[tok].append(ctx)

    # คำไทยที่อาจเป็นศัพท์เทคนิค (จากรายการเสนอเดิมของผู้ใช้ที่อาจหลงเหลือ)
    thai_check = {}
    for w in ["พีค", "น้ำพีค", "คาลิเบรต", "เทมเพลต", "อุทธรณ์"]:
        n = len(re.findall(w, body))
        if n:
            thai_check[w] = n

    out = {
        "scanned": DRAFT.name,
        "note": "ผลสแกนอัตโนมัติ — คำแปลต้องอนุมัติโดยคนแล้วเติมใน BANNED_TERMS (report/goal6_reportlib.py)",
        "candidates_english": {
            tok: {"count": n, "contexts": contexts[tok]}
            for tok, n in tokens.most_common()
        },
        "thai_terms_to_review": thai_check,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"candidates: {len(tokens)} คำ · คำไทยตรวจเพิ่ม: {thai_check or 'ไม่มี'}")
    print(f"เขียนแล้ว: {OUT} — ตรวจแล้วเติมคำที่เห็นด้วยลง BANNED_TERMS")


if __name__ == "__main__":
    main()