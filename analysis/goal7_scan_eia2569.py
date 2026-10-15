"""เป้าหมาย 7 — แผนที่การอ่านรายงานผลกระทบสิ่งแวดล้อม ฉบับ 2569 (4 เล่ม): นับหน้าที่พบคำสำคัญ ใช้บอกว่าส่วนสำคัญอยู่หน้าใดและยังไม่ได้อ่าน
อินพุต: data/32_goal7_chaophraya2/official_eia/256909-65.zip · เอาต์พุต: analysis/goal7/eia2569_scan.json"""
import fitz, re, zipfile, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
z = zipfile.ZipFile(ROOT / "data/32_goal7_chaophraya2/official_eia/256909-65.zip")
KW = {"model": r"MIKE|HEC-|แบบจำลอง(?:ทางชลศาสตร์|น้ำท่วม|คณิตศาสตร์)", "flood_side": r"น้ำท่วมซ้ำซาก|น้ำท่วมขัง|ระดับน้ำท่วม", "gate_rule": r"เกณฑ์การ(?:เดิน|ปิด|เปิด)|กฎเกณฑ์การ|คู่มือการ(?:เดิน|ปฏิบัติ)", "fault": r"รอยเลื่อน", "salinity": r"ความเค็ม|น้ำเค็ม", "subsidence": r"การทรุดตัว|ทรุดตัว", "opinion": r"แบบสอบถาม|ความคิดเห็นของประชาชน|ข้อคิดเห็น", "cost": r"ค่าก่อสร้างรวม|ราคาโครงการ|วงเงิน"}
out = {}
for i in z.infolist():
    d = fitz.open(stream=z.read(i.filename), filetype="pdf")
    n = len(d)
    hits = {k: [] for k in KW}
    chars = 0
    for pi in range(n):
        t = d[pi].get_text()
        chars += len(t)
        for k, rx in KW.items():
            if re.search(rx, t):
                hits[k].append(pi + 1)
    out[i.filename] = {"pages": n, "text_chars": chars, "hits": {k: {"n": len(v), "first": v[:12]} for k, v in hits.items()}}
    print(i.filename[:50].encode("utf8").decode(), n, chars, flush=True)
json.dump(out, open(ROOT / "analysis/goal7/eia2569_scan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
