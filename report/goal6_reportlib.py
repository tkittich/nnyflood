"""reportlib (เป้าหมาย 6) — builder บาง ๆ ใช้ร่วมทุกรายงาน (เสนอ §11 · เห็นด้วย 10 ต.ค. 69)

หลักการ (จากบทเรียน repo): HTML ไฟล์เดียว · ภาษาไทย · คำเตือน AI คำเดิมทุกฉบับ ·
ข้อมูลเข้าจาก JSON ที่สคริปต์วิเคราะห์สร้าง (ห้ามพิมพ์ตัวเลขในโค้ด builder) ·
figure = ฝัง base64 ในไฟล์เดียว · ไม่สร้าง framework ใหญ่ — ฟังก์ชันน้อยตัวออก HTML ชุดเดิม
+ **กติกาภาษา 10 ต.ค. 69: ห้ามคำทับศัพท์/ศัพท์เทคนิค · รายงานต้องอ่านจบในตัวเอง** —
เนื้อหาผ่าน `thai()` ตรวจคำต้องห้ามอัตโนมัติทุกครั้งที่สร้างรายงาน

ใช้:
    from reportlib import page, h2, prose, table, figure, note, kv
    html = page(title, subtitle, sections=[...])
    Path(out).write_text(html, encoding="utf-8")
"""

from __future__ import annotations

import base64
import html as _html
import re
from pathlib import Path

AI_WARNING = (
    "<b>คำเตือน</b> — รายงานนี้จัดทำโดยระบบปัญญาประดิษฐ์ (AI) ภายใต้การกำกับของเจ้าของโปรเจกต์ "
    "ข้อมูลต้นทางเป็นของจริงและตรวจสอบย้อนได้ทุกตัวเลข แต่การคำนวณ การตีความ และการจำลองสถานการณ์"
    "เป็นการประมาณการที่มีข้อจำกัด (ระบุไว้ทุกจุด) — <b>โปรดให้ผู้เชี่ยวชาญด้านอุทกวิทยา/"
    "ทรัพยากรน้ำ/วิศวกรรมตรวจทานอีกครั้งก่อนใช้ประกอบการตัดสินใจหรืออ้างอิงต่อ</b>"
)

# คำทับศัพท์/ศัพท์เทคนิคที่ห้ามในรายงาน → คำไทยแทน (ตรวจอัตโนมัติใน thai())
BANNED_TERMS = {
    "baseline": "ฉากอ้างอิงก่อนเหตุการณ์",
    "config": "ข้อตกลงการวิเคราะห์",
    "dataset": "ชุดข้อมูล",
    "default": "ค่าตั้งต้น",
    "endpoint": "จุดเชื่อมต่อข้อมูล",
    "feature": "ตัวแปรตั้งต้น",
    "grid search": "การค้นหาค่าที่ดีที่สุด",
    "model": "แบบจำลอง",
    "pipeline": "ลำดับการประมวลผล",
    "pre-registration": "กำหนดไว้ก่อนดูผล",
    "raw data": "ข้อมูลดิบ",
    "scenario": "สถานการณ์",
    "self-sufficient": "อ่านจบในตัวเอง",
    "threshold": "เกณฑ์ตัดสิน",
    "validation": "การตรวจสอบ",
    "workflow": "ขั้นตอนการทำงาน",
    # ศัพท์เทคนิคอุทกวิทยาที่มีคำไทย
    "cross-correlation": "ความสัมพันธ์ข้ามเวลา",
    "downstream": "ท้ายน้ำ",
    "upstream": "ต้นน้ำ",
    "runoff": "น้ำไหลผ่านผิวดิน",
    "satellite": "ดาวเทียม",
    "time series": "อนุกรมเวลา",
    "water level": "ระดับน้ำ",
    # รอบเพิ่ม 12 ต.ค. 69 (ผู้ใช้ชี้) — คำไทยที่ยังเป็นศัพท์เทคนิค/ทับศัพท์: แทนก่อนแล้วอธิบายครั้งแรก
    "น้ำพีค": "ระดับน้ำสูงสุด",
    "พีคน้ำ": "น้ำสูงสุด",
    "พีค": "จุดสูงสุด",
    "การแยกส่วนสาเหตุ": "การแยกส่วนของสาเหตุ",
    "คาลิเบรต": "สอบเทียบ",
    "คาลิเบรชั่น": "การสอบเทียบ",
    "เทมเพลต": "แบบสำเร็จรูป",
    "upper rule curve": "เส้นกำกับระดับน้ำบน",
    "lower rule curve": "เส้นกำกับระดับน้ำล่าง",
    "rule curve": "เส้นกำกับระดับน้ำตามแผน",
    "rulecurve": "เส้นกำกับระดับน้ำตามแผน",
    "curve": "เส้นกำกับระดับน้ำ",
    "critical": "วิกฤต",
    "datum": "ค่าอ้างอิงความสูง",
}

# ยกเว้น (รหัส/ชื่อเฉพาะ ใช้ได้): รหัสสถานี (Ny.7, Kgt.3, C.2), dam id, หน่วย (GB, ม., ตร.กม.),
# ชื่อดาวเทียม (Sentinel-1/2, Landsat), เวลา (UTC), ชื่อไฟล์ใน code tags


def thai(text: str, strict: bool = False) -> str:
    """ตรวจและแทนคำต้องห้าม (เรียกก่อนใส่รายงานทุกครั้ง)

    strict=False (default): ตรวจเฉพาะ**เนื้อความผู้อ่าน** — ตัดแท็ก HTML/CSS/attr ทิ้งก่อน
    strict=True: ตรวจทั้งก้อนรวมมาร์กอัป (ใช้เมื่อสงสัยข้อความหลุดไปอยู่ใน attr)

    คืนเสมอ: ข้อความที่**แทนคำต้องห้ามแล้ว** (ทั้งก้อน รวมแท็ก/attr — คำต้องห้ามที่หลุด
    เข้าไปใน alt/caption ก็ถูกแทน) · การแสกนสำหรับ error ทำบน**สำเนา**ที่ตัดแท็กแล้ว
    (เจอจริง 10 ต.ค.: ตัดแท็กบนตัวต้นฉบับแล้วรีเทิร์น → ภาพ base64 หายทั้ง 11 ชิ้น)
    """
    out = text
    for bad, good in BANNED_TERMS.items():
        out = re.sub(re.escape(bad), good, out, flags=re.IGNORECASE)
    if not strict:
        # สำเนาเพื่อแสกน: ตัด <style>…</style> · <code>…</code> · แท็ก HTML · attr style/href/id
        scan = re.sub(r"data:[a-zA-Z]+/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+", " ", out)
        scan = re.sub(r"<style.*?</style>", " ", scan, flags=re.S)
        scan = re.sub(r"<script.*?</script>", " ", scan, flags=re.S)
        scan = re.sub(r"<code>.*?</code>", " ", scan, flags=re.S)
        scan = re.sub(r"<[^>]+>", " ", scan)
        scan = re.sub(r"\b(?:style|href|id|class|src|alt|colspan)=\"[^\"]*\"", " ", scan)
        scan = re.sub(r"[a-z\-]+\s*:\s*[^;\"<>]+[;\"]", " ", scan)  # ทิ้งสิ่งที่เหลือแบบ CSS decl
    else:
        scan = out
    allowed = re.compile(
        r"^(?:[A-Z][a-zA-Z]*\.[0-9A-Za-z]*|Sentinel-[12]$|Sentinel-$|Landsat$|GRD$|COG$|SCL$|MNDWI$|URC$|"
        r"LRC$|NASA$|POWER$|ERA5$|GISTDA$|CDSE$|API$|DEM$|S1$|S2$|GBDT$|HH$|MM$|"
        r"GB$|MB$|km$|ม\.|ตร\.|ลลบ\.|มม\.|ม³$|รทก\.|UTC$|T4[0-9][A-Z]{3}$|"
        r"BKK$|BKC$|CPY$|GLF$|AIT$|CAN$|Kgt$|Ny$|QA$|RMSE$|MAE$|VH$|VV$|FOI$|"
        r"Copernicus$|GLO$|GLO-$|SHA$|SHA-$|SDV$|SUSPECT$|linear$|persistence$|"
        r"benchmark$|fluvial$|pluvial$|canonical$|mask$|opening$|datum$|pass$|"
        r"analysis$|goal\d*$|json$|raw$|vs$|N[0-9]+$|Q[0-9]+$|H[0-9]+$|lt$|gt$)"
    )
    suspicious = []
    for m in re.finditer(r"[A-Za-z][A-Za-z\-']+", scan):
        tok = m.group(0)
        # รหัสสถานี/เขื่อน แบบ Ny.7 · Kgt.3 · C.2 · S.26 · 2026-10-01
        if re.search(r"[A-Za-z]\.\d", scan[max(0, m.start() - 1):m.end() + 1]):
            continue
        if re.match(r"\d", scan[m.start():m.start() + 1]):
            continue
        if not allowed.match(tok):
            suspicious.append(tok)
    if suspicious:
        raise ValueError(
            "พบคำทับศัพท์/ศัพท์เทคนิคที่ยังไม่แทนด้วยคำไทย: "
            + ", ".join(sorted(set(suspicious)))
            + " — แก้ข้อความเป็นภาษาไทย หรือเพิ่มใน allowed list ของ reportlib พร้อมเหตุผล"
        )
    return out

# ชุดโทเคนสีกลาง (12 ต.ค. 69 — ตามข้อเสนอผู้ใช้หลังเจอ contrast 1.11 ที่ <code> ใน header)
# กฎ: ทุกสีใช้เป็น "คู่" (พื้น+ตัวอักษร) กำหนดพร้อมกันที่นี่เท่านั้น — ห้ามให้ตัวอักษรสืบทอดข้ามพื้น
# ตรวจแล้วด้วย WCAG: ตัวอักษร ≥4.5 · องค์ประกอบข้อมูล ≥3.0 (ดู tests/test_report3_language.py)
COLOR_TOKENS = {
    "paper":        ("#ffffff", "#1c2b33"),   # กระดาษ: พื้นขาว ตัวเข้ม (15.7)
    "page":         ("#eef2f5", "#1c2b33"),   # พื้นหน้ารอบกระดาษ
    "header":       ("#14212e", "#ffffff"),   # header พื้นน้ำเงินดำ ตัวขาว (16+)
    "accent":       ("#1e6fb8", "#ffffff"),   # สีเน้น/ลิงก์ (5.0)
    "note_bg":      ("#fff8e1", "#4a3b00"),   # กล่องหมายเหตุครีม (ตัวน้ำตาลเข้ม 9+)
    "warn_bg":      ("#fdecea", "#8a2b2b"),   # กล่องเตือนชมพู (7+)
    "ok_bg":        ("#e8f5e9", "#1b5e20"),   # กล่องผ่านเขียว (7+)
    "code_bg":      ("#eef2f6", "#153a5e"),   # inline code (10.4)
    "header_code":  ("#2a4d73", "#ffffff"),   # code บนพื้นเข้ม (~8.7)
    "muted":        ("#ffffff", "#5a6b7b"),   # ข้อความรองบนขาว (5.5)
    "table_head":   ("#28425c", "#ffffff"),   # หัวตาราง (10.4)
    "sea_flood":    ("#1d6fb8", "#f5edda"),   # แผนที่: น้ำบนครีม (4.5)
    "chart_bar":    ("#4d94c9", "#ffffff"),   # แท่งกราฟรอง (3.3)
    "chart_accent": ("#e74c3c", "#ffffff"),   # แท่งกราฟเน้น (3.8)
}

def css_tokens() -> str:
    """สร้าง CSS variables จาก COLOR_TOKENS — builder อ้าง var(--name) แทนค่าตรง"""
    lines = [":root {"]
    for name, (bg, fg) in COLOR_TOKENS.items():
        lines.append(f"  --c-{name.replace('_', '-')}: {bg}; --c-{name.replace('_', '-')}-fg: {fg};")
    lines.append("}")
    return "\n".join(lines)

CSS = """
  body { font-family:'Leelawadee UI','Segoe UI',Tahoma,'Loma','Garuda','Norasi',sans-serif;
         color:var(--c-paper-fg); background:var(--c-page); margin:0; line-height:1.75; }
  .wrap { max-width:980px; margin:0 auto; padding:28px 20px 60px; }
  .paper { background:#fff; border-radius:10px; padding:34px 40px; box-shadow:0 2px 14px rgba(0,0,0,.08); }
  h1 { font-size:1.9em; line-height:1.35; margin:.2em 0 .2em; }
  .meta { color:var(--c-muted-fg); font-size:.95em; margin:10px 0 0; }
  .warn { background:var(--c-note-bg); border:1px solid #e8c96a; border-radius:8px; padding:12px 16px;
          margin:18px 0; font-size:.95em; }
  .note { background:#eef6fb; border:1px solid #b9d7ea; border-radius:8px; padding:12px 16px;
          margin:16px 0; font-size:.95em; }
  h2 { margin:1.6em 0 .4em; padding-bottom:.25em; border-bottom:2px solid #d8e2ea; font-size:1.35em; }
  h3 { margin:1.2em 0 .3em; color:#28425c; }
  table { border-collapse:collapse; width:100%; margin:12px 0; font-size:.92em; }
  th { background:var(--c-table-head); color:var(--c-table-head-fg); padding:6px 9px; text-align:left; }
  td { border-bottom:1px solid #dde6ec; padding:5px 9px; }
  tr:nth-child(even) td { background:#f6f9fb; }
  .toc { font-size:.95em; background:#f4f7f9; border-radius:8px; padding:12px 18px; margin:16px 0; }
  .toc a { color:var(--c-accent); text-decoration:none; }
  figure { margin:18px 0; text-align:center; }
  figure img { max-width:100%; border:1px solid #dde6ec; border-radius:6px; }
  figcaption { color:#5a6b7b; font-size:.88em; margin-top:6px; text-align:left; }
  .placeholder { background:#fdf3f3; border:1px dashed #d99; border-radius:8px; padding:10px 16px;
                 color:var(--c-warn-bg-fg); margin:14px 0; font-size:.93em; }
  code { background:#f0f3f5; padding:1px 5px; border-radius:4px; font-size:.9em; }
  .foot { color:var(--c-muted-fg); font-size:.88em; border-top:1px solid #dde6ec; margin-top:34px; padding-top:14px; }
"""


def esc(s) -> str:
    return _html.escape(str(s), quote=False)


def h2(text: str, anchor: str | None = None) -> str:
    a = f' id="{anchor}"' if anchor else ""
    return f"<h2{a}>{esc(text)}</h2>"


def h3(text: str) -> str:
    return f"<h3>{esc(text)}</h3>"


def prose(html_text: str) -> str:
    """ย่อหน้า HTML ตรง ๆ (ผู้เรียกเตรียม <b>/<code> เอง — ข้อความต้อง escape เอง)"""
    return f"<p>{html_text}</p>"


def note(html_text: str, warn: bool = False) -> str:
    cls = "warn" if warn else "note"
    return f'<div class="{cls}">{html_text}</div>'


def placeholder(text: str) -> str:
    return f'<div class="placeholder">⏳ รอข้อมูล — {esc(text)}</div>'


def table(headers: list[str], rows: list[list], caption: str | None = None) -> str:
    out = ["<table>"]
    if caption:
        out.append(f"<caption style='text-align:left;color:#5a6b7b;padding:4px 2px'>{caption}</caption>")
    out.append("<tr>" + "".join(f"<th>{esc(h)}</th>" for h in headers) + "</tr>")
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    out.append("</table>")
    return "".join(out)


def figure(png_path: str | Path, caption: str) -> str:
    p = Path(png_path)
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return (f"<figure><img src='data:image/png;base64,{b64}' alt='{esc(caption)}'>"
            f"<figcaption>{esc(caption)}</figcaption></figure>")


def toc(sections: list[tuple[str, str]]) -> str:
    items = "".join(f"<li><a href='#{a}'>{esc(t)}</a></li>" for t, a in sections)
    return f"<div class='toc'><b>สารบัญ</b><ul style='margin:6px 0 0'>{''.join(items)}</ul></div>"


def page(title: str, subtitle: str, sections_html: list[str], footer_html: str) -> str:
    # M11 (รีวิว Sift): เรียก thai() จริงทุกครั้งที่สร้างรายงาน — เดิมเป็น dead code
    # (เทสภาษาครอบ 14/37 ศัพท์ · "การแยกส่วนสาเหตุ" หลุดอยู่ใน HTML จริง 2 จุด)
    body = thai("\n".join(sections_html))
    return f"""<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><style>{css_tokens()}
{CSS}</style></head>
<body><div class="wrap"><div class="paper">
<div class="meta">จัดทำเมื่อ ตุลาคม 2569 · ทุกตัวเลขตรวจสอบย้อนกลับได้ถึงไฟล์ต้นฉบับ ·
<b>จัดทำโดยปัญญาประดิษฐ์ (AI) ร่วมกับเจ้าของโปรเจกต์ — ก่อนนำไปอ้างอิง/ตัดสินใจ ควรตรวจทานโดยผู้เชี่ยวชาญด้านอุทกวิทยา/วิศวกรรมอีกครั้ง</b></div>
<h1>{esc(title)}</h1>
<div class="meta">{subtitle}</div>
<div class="warn">{AI_WARNING}</div>
{body}
<div class="foot">{footer_html}</div>
</div></div></body></html>"""