# อัลบั้ม 666 ภาพ: ตัวต่อท้ายผลสแกนแบบ idempotent (กันข้อมูลหาย/กันแถวซ้ำ)
# อ่านแถวใหม่จากไฟล์ TSV (fbid<TAB>หลักฐานที่เห็น<TAB>ตำแหน่งที่อนุมาน<TAB>ความมั่นใจ)
# - ข้าม fbid ที่มีอยู่แล้วใน CSV (รันซ้ำได้ ไม่เกิดแถวซ้ำ)
# - สำรองไฟล์เดิมแบบ byte-identical ก่อนเขียน แล้วต่อท้ายเท่านั้น (ไม่เขียนทับของเดิม)
# - ตรวจ BOM/newline ปลายไฟล์ก่อนต่อ (กันไฟล์เสีย)
# วิธีใช้:  python analysis/album_append.py rows.tsv
#          cat rows.tsv | python analysis/album_append.py -
import argparse
import csv
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "analysis" / "album_geotag_results.csv"
HEADER = ["ไฟล์", "หลักฐานที่เห็น", "ตำแหน่งที่อนุมาน", "ความมั่นใจ"]


def scanned_ids(path):
    s = set()
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.reader(f):
            if r and r[0].lstrip("\ufeff").lower().endswith(".jpg"):
                s.add(r[0].lstrip("\ufeff")[:-4])
    return s


def read_rows(src):
    """อ่านแถวใหม่จาก TSV/CSV: 4 คอลัมน์ คั่นด้วย TAB (หรือ comma)

    ใช้ utf-8-sig + lstrip('\\ufeff') กัน BOM ที่ editor บางตัว (รวมถึง Write tool)
    แอบเติมต้นไฟล์ แล้ว BOM ไปติดหน้า fbid ทำให้ scanned() มองไม่เห็น -> สแกนซ้ำไม่จบ
    """
    text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8-sig")
    rows = []
    for i, line in enumerate(text.splitlines(), 1):
        line = line.rstrip("\r\n").lstrip("\ufeff")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        sep = "\t" if "\t" in line else ","
        parts = [p.strip().lstrip("\ufeff") for p in line.split(sep)]
        if len(parts) != 4:
            raise SystemExit(f"บรรทัด {i}: ต้องมี 4 คอลัมน์ (พบ {len(parts)}): {line!r}")
        if any("\ufeff" in p for p in parts):
            raise SystemExit(f"บรรทัด {i}: ยังพบ BOM หลังทำความสะอาด: {parts!r}")
        fb = parts[0][:-4] if parts[0].lower().endswith(".jpg") else parts[0]
        rows.append([f"{fb}.jpg", parts[1], parts[2], parts[3]])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="ไฟล์ TSV/CSV ของแถวใหม่ หรือ - สำหรับ stdin")
    a = ap.parse_args()

    raw = RES.read_bytes()
    if not raw.endswith(b"\n"):
        raise SystemExit("ไฟล์เดิมไม่ลงท้ายด้วย newline — หยุดเพื่อกันไฟล์เสีย")
    if raw.count(b"\xef\xbb\xbf") > 1:
        raise SystemExit("ไฟล์ปลายทางมี BOM กลางไฟล์ — ซ่อมก่อน (ดู mid-file BOM) แล้วรันใหม่")

    have = scanned_ids(RES)
    rows = read_rows(a.src)
    new = [r for r in rows if r[0][:-4] not in have]
    dup_in_batch = len(rows) - len({r[0] for r in rows})

    bak = Path(tempfile.gettempdir()) / "album_geotag_results.bak.csv"
    shutil.copy2(RES, bak)
    if bak.read_bytes() != raw:
        raise SystemExit("สำรองไฟล์ไม่ตรงกับต้นฉบับ — หยุด")

    if new:
        with open(RES, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            for r in new:
                w.writerow(r)
        after = RES.read_bytes()
        if after.count(b"\xef\xbb\xbf") != 1:
            raise SystemExit("เขียนแล้วเกิด BOM กลางไฟล์ — หยุด (กู้จาก backup)")

    total = len(scanned_ids(RES))
    print(f"appended {len(new)} rows (skipped {len(rows) - len(new)})")
    if dup_in_batch:
        print(f"  note: input มี fbid ซ้ำกันเอง {dup_in_batch} แถว")
    print(f"total data rows now: {total}")
    print(f"backup: {bak}")


if __name__ == "__main__":
    main()
