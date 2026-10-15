"""เป้าหมาย 7 — ดึงตาราง "บัญชีอาคารประกอบของคลองระบายน้ำหลาก" (ตาราง 2.3.2-3) จากรายงานผลกระทบสิ่งแวดล้อม 3 ฉบับ
(ฉบับหลัก 2561 · ชี้แจงครั้งที่ 1 2564 · ชี้แจงครั้งที่ 2 2566) แล้วเทียบกับตารางอาคารที่อ่านจากแผนที่รายช่วง (structures_all.csv)

อินพุต: data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/EIA/EIA โครงการ…/ (3 ไฟล์ PDF · disk-only)
เอาต์พุต: analysis/goal7/eia_structs.json
ข้อสังเกต: กม. ในตารางนับจากฝั่งป่าสัก (กม.0+325 = ถนนท่าเรือ–เสาไห้) เหมือนตารางของเรา · ตัวอักษรไทยในไฟล์ใช้สระอำแบบแยกตัว ต้องแปลงก่อน
"""
import csv
import json
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "data/manual/ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง/EIA/EIA โครงการทางระบายน้ำหลากเจ้าพระยาฝั่งตะวันออกตอนล่าง ของกรมชลประทาน"
VERS = {"2561": B / "รายงานฉบับหลัก/1. รายงานหลัก EIA.pdf",
        "2564": B / "รายงานชี้แจงเพิ่มเติมครั้งที่ 1/1. รายงานหลัก(ชี้แจง1).pdf",
        "2566": B / "รายงานชี้แจงเพิ่มเติมครั้งที่ 2/1. รายงานชี้แจงเพิ่มเติม.pdf"}
ZIP2569 = ROOT / "data/32_goal7_chaophraya2/official_eia/256909-65.zip"
CSV = ROOT / "analysis/goal7/structures_all.csv"
OUT = ROOT / "analysis/goal7/eia_structs.json"
NN = (38.6, 73.2)
SPLIT = re.compile(r"\|\s*(\d{1,3})\s*\|\s*(\d{1,3}\+\d{3})")


def norm(s):
    return s.replace("น ้า", "น้ำ").replace("นำ้", "น้ำ").replace("ำ", "ำ").replace("ทั ง", "ทั้ง").replace("ล ำ", "ลำ")


def table_text(path):
    if isinstance(path, tuple):  # (zip, ชื่อไฟล์ในซิป)
        import zipfile
        d = fitz.open(stream=zipfile.ZipFile(path[0]).read(path[1]), filetype="pdf")
    else:
        d = fitz.open(path)
    hit = []
    for i, p in enumerate(d):
        t = p.get_text()
        if "บัญชีอาคารประกอบ" in t and re.search(r"\n\d{1,3}\n\d+\+\d{3}", t):
            hit.append(i)
    # หน้าของตารางต่อเนื่องกัน — เก็บเฉพาะช่วงที่ต่อกัน
    pages = [i for i in range(min(hit), max(hit) + 1)] if hit else []
    txt = ""
    for i in pages:
        txt += " | " + re.sub(r"\s*\n\s*", " | ", d[i].get_text())
    return norm(txt), [p + 1 for p in pages]


def parse(txt):
    ch = SPLIT.split(txt)
    rows = []
    for k in range(1, len(ch) - 2, 3):
        no, km, raw = int(ch[k]), ch[k + 1], re.sub(r"\s*\|\s*", " | ", ch[k + 2]).strip(" |")
        if no > 99:
            continue
        a, b = km.split("+")
        kmv = int(a) + int(b) / 1000
        if "ปตร" in raw:
            kind = "gate"
        elif "สะพานรถไฟ" in raw:
            kind = "rail_bridge"
        elif "สะพานรถยนต์" in raw:
            kind = "road_bridge"
        elif "ท่อรับน้ำ" in raw:
            kind = "inlet"
        elif "สะพานน้ำ" in raw:
            kind = "aqueduct"
        else:
            kind = "crossing"
        o = {"no": no, "km": round(kmv, 3), "kind": kind, "lock": "ประตูเรือ" in raw}
        name = raw.split(" | ")[0]
        o["name"] = re.sub(r"^\d+\+\d{3}\s*", "", name)[:60]
        sip = re.search(r"ไซฟอน\s*(\d+)\s*-\s*□\s*([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)", raw)
        cul = re.search(r"ท่อระบายน้ำ\s*(\d+)\s*-\s*□\s*([\d.]+)\s*x\s*([\d.]+)", raw)
        if sip:
            o.update(sip_n=int(sip[1]), sip_w=float(sip[2]), sip_h=float(sip[3]), sip_len=float(sip[4]))
        if cul:
            o.update(cul_n=int(cul[1]), cul_w=float(cul[2]), cul_h=float(cul[3]))
        wd = re.search(r"กว้าง(?:คลอง)?ประมาณ\s*([\d.]+)\s*ม", raw)
        if wd:
            o["canal_w"] = float(wd[1])
        qs = re.findall(r"\|\s*(\d+\.\d{2})\s*\|", raw)
        if qs and kind in ("crossing", "aqueduct", "inlet"):
            o["q_in"] = float(qs[0])
            o["q_struct"] = float(qs[-1])
        o["raw"] = raw[:300]
        rows.append(o)
    return rows


def main():
    res = {"note": "ตาราง 2.3.2-3 ของรายงานผลกระทบสิ่งแวดล้อม · กม. นับจากฝั่งป่าสัก · ค่า q = อัตราไหลออกแบบของคลองเดิมที่ตัด (ลบ.ม./วินาที) · "
                   "ขนาดช่อง = กว้าง × สูง (ม.) × ยาว (ม.)", "versions": {}}
    vers = dict(VERS)
    if ZIP2569.exists():
        import zipfile
        nm = next(i.filename for i in zipfile.ZipFile(ZIP2569).infolist() if "เล่ม 1-" in i.filename and "ภาคผนวก" not in i.filename)
        vers["2569"] = (ZIP2569, nm)
    for v, path in vers.items():
        txt, pages = table_text(path)
        rows = parse(txt)
        res["versions"][v] = {"pdf_pages": [pages[0], pages[-1]], "n": len(rows), "rows": rows}
        print(v, "pages", pages[:1], "-", pages[-1:], "rows", len(rows))
    # เทียบฉบับ
    base = {r["no"]: r for r in res["versions"]["2561"]["rows"]}
    diffs = []
    for v in [x for x in res["versions"] if x != "2561"]:
        for r in res["versions"][v]["rows"]:
            b = base.get(r["no"])
            if not b:
                diffs.append({"v": v, "no": r["no"], "what": "ไม่มีในฉบับ 2561"})
                continue
            for k in ("km", "kind", "sip_n", "sip_w", "sip_h", "sip_len", "cul_n", "cul_w", "cul_h", "canal_w", "q_in", "q_struct"):
                if r.get(k) != b.get(k):
                    diffs.append({"v": v, "no": r["no"], "km": r["km"], "field": k, "v2561": b.get(k), "this": r.get(k)})
    res["diffs_vs_2561"] = diffs
    print("diffs", len(diffs))
    # จับคู่กับตารางที่อ่านจากแผนที่
    mine = list(csv.DictReader(open(CSV, encoding="utf-8")))
    mk = [(float(m["km"]), m["kind"], m["name"]) for m in mine]
    matched, unmatched_eia = 0, []
    used = set()
    for r in res["versions"]["2561"]["rows"]:
        best = min(range(len(mk)), key=lambda i: abs(mk[i][0] - r["km"]))
        if abs(mk[best][0] - r["km"]) <= 0.25:
            matched += 1
            used.add(best)
            r["mine_km"], r["mine_kind"], r["mine_name"] = mk[best]
        else:
            unmatched_eia.append(r["no"])
    res["match"] = {"eia_rows": 99, "matched_within_250m": matched, "eia_unmatched_no": unmatched_eia,
                    "mine_total": len(mk), "mine_not_in_eia2561": len(mk) - len(used)}
    # ช่วงนครนายก
    nn = [r for r in res["versions"]["2561"]["rows"] if NN[0] <= r["km"] <= NN[1]]
    cr = [r for r in nn if r["kind"] == "crossing"]
    res["nn_reach"] = {"km": NN, "n_all": len(nn), "n_crossings": len(cr), "n_locks": sum(r["lock"] for r in nn),
                       "n_road_bridges": sum(r["kind"] == "road_bridge" for r in nn),
                       "n_aqueducts": sum(r["kind"] == "aqueduct" for r in nn),
                       "crossings": [{k: r.get(k) for k in ("no", "km", "name", "canal_w", "q_in", "q_struct", "sip_n", "sip_w", "sip_h", "sip_len", "cul_n", "cul_w", "cul_h", "lock")} for r in cr]}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res["match"], ensure_ascii=False))
    print("NN:", {k: v for k, v in res["nn_reach"].items() if k != "crossings"})
    for c in res["nn_reach"]["crossings"]:
        print(c)


if __name__ == "__main__":
    main()
