"""ทดสอบความแม่นยำข้อความไทยของ Indra OCR เทียบ "ชั้นข้อความ PDF" ซึ่งเป็นเฉลยที่แน่นอน บนหน้าข้อความ 30 หน้าสุ่มจาก EIA เล่ม 1
เกณฑ์ตั้งก่อนดูผล: หน้าที่ชั้นข้อความยาวกว่า 1,500 อักขระ · สุ่มด้วยเมล็ด 7 · วัดความคล้ายตัวอักษร (SequenceMatcher บน 3,000 อักขระแรก ตัดช่องว่าง เลขไทย→อารบิก) และการพบตัวเลข
ข้อจำกัด: เป็นหน้าข้อความพิมพ์ ไม่ใช่หน้าสแกน/ภาพวาด · ยังไม่ได้เทียบ Typhoon บนหน้าชุดเดียวกัน (Typhoon ไม่ได้อ่านหน้าที่มีชั้นข้อความ)
รัน: E:/theera/indra_env/Scripts/python.exe analysis/goal7_indra_text_eval.py
ผลลัพธ์: analysis/goal7/indra_text_eval.json
"""
import sys, re, json, random, difflib, time
import pymupdf, cv2, numpy as np
import indra_ocr
TH = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
pdf = pymupdf.open('E:/theera/code/flood/data/32_goal7_chaophraya2/official_eia/extracted/main1.pdf')
# หน้าข้อความที่มีชั้นข้อความ: เลือก 30 หน้ากระจายทั่วเล่ม
pages = [p for p in range(1, len(pdf)+1) if len(pdf[p-1].get_text().strip()) > 1500]
random.seed(7); sel = sorted(random.sample(pages, 30))
conv = indra_ocr.load(threads=4)
def norm(s): return re.sub(r"\s+", "", s.translate(TH))
rows = []
for p in sel:
    pg = pdf[p-1]
    truth = norm(pg.get_text())
    pix = pg.get_pixmap(dpi=200)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if pix.n >= 3 else img[:, :, 0]
    t0 = time.time(); page = conv.ocr(gray); sec = time.time() - t0
    out = norm(page.text)
    sm = difflib.SequenceMatcher(None, truth[:3000], out[:3000], autojunk=False)
    nt = set(re.findall(r"\d+(?:\.\d+)*", pg.get_text().translate(TH))); no = set(re.findall(r"\d+(?:\.\d+)*", page.text.translate(TH)))
    rows.append((p, round(sm.ratio(), 3), round(len(nt & no) / max(1, len(nt)), 3), round(sec, 2)))
print(rows[:6])
print('mean char similarity', round(sum(r[1] for r in rows)/len(rows), 3), 'mean number recall', round(sum(r[2] for r in rows)/len(rows), 3), 'mean sec', round(sum(r[3] for r in rows)/len(rows), 2), 'n', len(rows))
json.dump({'note': 'Indra OCR (CPU) เทียบชั้นข้อความ PDF · 30 หน้า EIA เล่ม 1', 'pages': sel, 'rows': [{'page': r[0], 'char_similarity': r[1], 'number_recall': r[2], 'sec': r[3]} for r in rows], 'mean_char_similarity': round(sum(r[1] for r in rows)/len(rows), 3), 'mean_number_recall': round(sum(r[2] for r in rows)/len(rows), 3), 'mean_sec': round(sum(r[3] for r in rows)/len(rows), 2)}, open('E:/theera/code/flood/analysis/goal7/indra_text_eval.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
