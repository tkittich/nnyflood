# สกัดรูปตัดขวางลำน้ำ (cross section) จากไฟล์ RID ศูนย์อุทกวิทยาชลประทานภาคตะวันออก
# ไฟล์ต้นฉบับ: data/19_rid_cross_sections/raw/<ST>.xlsx  (คอลัมน์ I:J, K:L, M:N = เส้นสำรวจปัจจุบัน)
# หมายเหตุ: ค่าที่ไม่ใช่ตัวเลขในคอลัมน์ "ระยะ" มีป้ายกำกับ เช่น "0   R1    บน", "50  ท้องน้ำ"
#           -> เก็บป้ายกำกับไว้ในคอลัมน์ label และดึงตัวเลขนำหน้าออกมาเป็น offset
# ผลลัพธ์: data/19_rid_cross_sections/derived/<ST>_profile.csv  +  สรุป <ST>_geometry.json
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "19_rid_cross_sections" / "raw"
DER = ROOT / "data" / "19_rid_cross_sections" / "derived"
DER.mkdir(parents=True, exist_ok=True)

SEGMENTS = [(9, 10), (11, 12), (13, 14)]  # I:J, K:L, M:N
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def parse_offset(v):
    """คืน (offset, label). offset อาจมาเป็นตัวเลข หรือสตริงมีป้ายกำกับ."""
    if isinstance(v, (int, float)):
        return float(v), ""
    if v is None:
        return None, ""
    s = str(v).strip()
    m = NUM.search(s)
    if not m:
        return None, s
    return float(m.group(0)), s[m.end():].strip()


def extract(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    pts = []
    for co, ce in SEGMENTS:
        for r in range(1, ws.max_row + 1):
            elev = ws.cell(r, ce).value
            if not isinstance(elev, (int, float)):
                continue
            off, label = parse_offset(ws.cell(r, co).value)
            if off is None:
                continue
            pts.append({"row": r, "offset_m": off, "elev_msl_m": float(elev), "label": label})
    pts.sort(key=lambda p: (p["offset_m"], p["row"]))
    return pts


def summarise(pts):
    """crest = จุดสูงสุดของแต่ละฝั่งของร่องน้ำ (แยกที่จุดต่ำสุด = ท้องน้ำ)"""
    if not pts:
        return {}
    thal = min(pts, key=lambda p: p["elev_msl_m"])
    left = [p for p in pts if p["offset_m"] <= thal["offset_m"]]
    right = [p for p in pts if p["offset_m"] >= thal["offset_m"]]
    return {
        "n_points": len(pts),
        "offset_min": pts[0]["offset_m"],
        "offset_max": pts[-1]["offset_m"],
        "thalweg": thal,
        "left_crest": max(left, key=lambda p: p["elev_msl_m"]),
        "right_crest": max(right, key=lambda p: p["elev_msl_m"]),
    }


def main():
    out = {}
    for x in sorted(RAW.glob("*.xlsx")):
        stem = x.stem.replace("_2025", "")
        pts = extract(x)
        if not pts:
            print(f"{stem}: no numeric profile found")
            continue
        csv = DER / f"{stem}_profile.csv"
        with open(csv, "w", encoding="utf-8", newline="") as f:
            f.write("offset_m,elev_msl_m,label\n")
            for p in pts:
                f.write(f'{p["offset_m"]},{p["elev_msl_m"]},"{p["label"]}"\n')
        s = summarise(pts)
        out[stem] = s
        lc, rc, th = s["left_crest"], s["right_crest"], s["thalweg"]
        print(f"{stem}: {s['n_points']} pts  offsets {s['offset_min']:g}..{s['offset_max']:g} m")
        print(f"   thalweg  {th['elev_msl_m']:7.3f} m MSL @ {th['offset_m']:g} m  [{th['label']}]")
        print(f"   L crest  {lc['elev_msl_m']:7.3f} m MSL @ {lc['offset_m']:g} m  [{lc['label']}]")
        print(f"   R crest  {rc['elev_msl_m']:7.3f} m MSL @ {rc['offset_m']:g} m  [{rc['label']}]")
        print(f"   lower crest -> gauge (crest+1.59) = {min(lc['elev_msl_m'], rc['elev_msl_m']) + 1.59:.2f} m")
        print(f"   -> {csv.name}")
    with open(DER / "cross_section_geometry.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
