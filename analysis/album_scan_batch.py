# อัลบั้ม 666 ภาพ: ตัวช่วยเลือกแบตช์ถัดไปสำหรับสแกนด้วย AI vision
# อ่านอย่างเดียว (ไม่แก้ CSV) — สร้างภาพย่อขนาดไปยังโฟลเดอร์ชั่วคราว แล้วพิมพ์ manifest ให้อ่านทีละใบ
# วิธีใช้:  python analysis/album_scan_batch.py --n 12
#          (สแกนเสร็จ -> เขียนผลต่อท้าย analysis/album_geotag_results.csv -> รันคำสั่งเดิมได้แบตช์ถัดไป)
import argparse
import csv
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ALB = ROOT / "data" / "06_citizen_social" / "flood_album"
CAPS = ROOT / "analysis" / "flood_album_captions.csv"
RES = ROOT / "analysis" / "album_geotag_results.csv"


def ordered_fbids():
    """ลำดับภาพตามอัลบั้ม (จากไฟล์ caption) — dedupe คงลำดับ"""
    order = []
    with open(CAPS, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            fb = (r.get("fbid") or "").strip()
            if fb:
                order.append(fb)
    seen, out = set(), []
    for fb in order:
        if fb not in seen:
            seen.add(fb)
            out.append(fb)
    return out


def captions():
    cap = {}
    with open(CAPS, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            fb = (r.get("fbid") or "").strip()
            if fb and fb not in cap:
                cap[fb] = (r.get("caption") or "").strip()
    return cap


def scanned():
    s = set()
    with open(RES, encoding="utf-8-sig") as f:
        for r in csv.reader(f):
            if r and r[0].lstrip("\ufeff").lower().endswith(".jpg"):
                s.add(r[0].lstrip("\ufeff")[:-4])
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--thumb-dir", default=str(Path(tempfile.gettempdir()) / "album_thumbs"))
    ap.add_argument("--max", type=int, default=720)
    a = ap.parse_args()

    td = Path(a.thumb_dir)
    td.mkdir(parents=True, exist_ok=True)
    for p in td.glob("*.jpg"):      # ล้างภาพย่อรอบก่อน (โฟลเดอร์ชั่วคราวเท่านั้น)
        p.unlink()

    cap = captions()
    sc = scanned()
    todo = [fb for fb in ordered_fbids() if fb not in sc]
    missing = [fb for fb in todo if not (ALB / f"{fb}.jpg").exists()]
    todo = [fb for fb in todo if (ALB / f"{fb}.jpg").exists()]
    batch = todo[: a.n]

    print(f"# scanned={len(sc)} | todo_with_file={len(todo)} | missing_file={len(missing)} | batch={len(batch)}")
    if missing:
        print("# missing (ไม่มีไฟล์ในโฟลเดอร์ — ควรเขียนแถว 'ไม่พบไฟล์' เพื่อข้าม):", ", ".join(missing))
    for i, fb in enumerate(batch, 1):
        im = Image.open(ALB / f"{fb}.jpg").convert("RGB")
        im.thumbnail((a.max, a.max))
        im.save(td / f"{i:02d}_{fb}.jpg", quality=78)
        print(f"[{i:02d}] {fb} {im.size[0]}x{im.size[1]} | caption: {cap.get(fb, '')[:160]}")
    print("THUMB_DIR", td)


if __name__ == "__main__":
    main()
