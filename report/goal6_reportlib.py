"""reportlib (เป้าหมาย 6) — builder บาง ๆ ใช้ร่วมทุกรายงาน (เสนอ §11 · เห็นด้วย 10 ต.ค. 69)

หลักการ (จากบทเรียน repo): HTML ไฟล์เดียว · ภาษาไทย · คำเตือน AI คำเดิมทุกฉบับ ·
ข้อมูลเข้าจาก JSON ที่สคริปต์วิเคราะห์สร้าง (ห้ามพิมพ์ตัวเลขในโค้ด builder) ·
figure = ฝัง base64 ในไฟล์เดียว · ไม่สร้าง framework ใหญ่ — ฟังก์ชันน้อยตัวออก HTML ชุดเดิม

ใช้:
    from reportlib import page, h2, prose, table, figure, note, kv
    html = page(title, subtitle, sections=[...])
    Path(out).write_text(html, encoding="utf-8")
"""

from __future__ import annotations

import base64
import html as _html
from pathlib import Path

AI_WARNING = (
    "<b>คำเตือน</b> — รายงานนี้จัดทำโดยระบบปัญญาประดิษฐ์ (AI) ภายใต้การกำกับของเจ้าของโปรเจกต์ "
    "ข้อมูลต้นทางเป็นของจริงและตรวจสอบย้อนได้ทุกตัวเลข แต่การคำนวณ การตีความ และการจำลองสถานการณ์"
    "เป็นการประมาณการที่มีข้อจำกัด (ระบุไว้ทุกจุด) — <b>โปรดให้ผู้เชี่ยวชาญด้านอุทกวิทยา/"
    "ทรัพยากรน้ำ/วิศวกรรมตรวจทานอีกครั้งก่อนใช้ประกอบการตัดสินใจหรืออ้างอิงต่อ</b>"
)

CSS = """
  body { font-family:'Leelawadee UI','Segoe UI',Tahoma,'Loma','Garuda','Norasi',sans-serif;
         color:#1a2430; background:#eef2f5; margin:0; line-height:1.75; }
  .wrap { max-width:980px; margin:0 auto; padding:28px 20px 60px; }
  .paper { background:#fff; border-radius:10px; padding:34px 40px; box-shadow:0 2px 14px rgba(0,0,0,.08); }
  h1 { font-size:1.9em; line-height:1.35; margin:.2em 0 .2em; }
  .meta { color:#5a6b7b; font-size:.95em; margin:10px 0 0; }
  .warn { background:#fff7e0; border:1px solid #e8c96a; border-radius:8px; padding:12px 16px;
          margin:18px 0; font-size:.95em; }
  .note { background:#eef6fb; border:1px solid #b9d7ea; border-radius:8px; padding:12px 16px;
          margin:16px 0; font-size:.95em; }
  h2 { margin:1.6em 0 .4em; padding-bottom:.25em; border-bottom:2px solid #d8e2ea; font-size:1.35em; }
  h3 { margin:1.2em 0 .3em; color:#28425c; }
  table { border-collapse:collapse; width:100%; margin:12px 0; font-size:.92em; }
  th { background:#28425c; color:#fff; padding:6px 9px; text-align:left; }
  td { border-bottom:1px solid #dde6ec; padding:5px 9px; }
  tr:nth-child(even) td { background:#f6f9fb; }
  .toc { font-size:.95em; background:#f4f7f9; border-radius:8px; padding:12px 18px; margin:16px 0; }
  .toc a { color:#28628f; text-decoration:none; }
  figure { margin:18px 0; text-align:center; }
  figure img { max-width:100%; border:1px solid #dde6ec; border-radius:6px; }
  figcaption { color:#5a6b7b; font-size:.88em; margin-top:6px; text-align:left; }
  .placeholder { background:#fdf3f3; border:1px dashed #d99; border-radius:8px; padding:10px 16px;
                 color:#8a4a4a; margin:14px 0; font-size:.93em; }
  code { background:#f0f3f5; padding:1px 5px; border-radius:4px; font-size:.9em; }
  .foot { color:#5a6b7b; font-size:.88em; border-top:1px solid #dde6ec; margin-top:34px; padding-top:14px; }
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
    body = "\n".join(sections_html)
    return f"""<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style></head>
<body><div class="wrap"><div class="paper">
<div class="meta">จัดทำเมื่อ ตุลาคม 2569 · ทุกตัวเลขตรวจสอบย้อนกลับได้ถึงไฟล์ต้นฉบับ ·
<b>จัดทำโดยปัญญาประดิษฐ์ (AI) ร่วมกับเจ้าของโปรเจกต์ — ก่อนนำไปอ้างอิง/ตัดสินใจ ควรตรวจทานโดยผู้เชี่ยวชาญด้านอุทกวิทยา/วิศวกรรมอีกครั้ง</b></div>
<h1>{esc(title)}</h1>
<div class="meta">{subtitle}</div>
<div class="warn">{AI_WARNING}</div>
{body}
<div class="foot">{footer_html}</div>
</div></div></body></html>"""