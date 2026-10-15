"""เป้าหมาย 7 — ตรวจทะเบียนช่องว่างความรู้ (analysis/goal7/gaps.json) เทียบแหล่งข้อมูลที่ลงทะเบียนแฮชไว้

ใช้: python analysis/goal7_gaps_check.py          # แสดงแหล่งใหม่ที่ยังไม่ได้ทบทวน + ช่องว่างที่อาจถูกปิด
     python analysis/goal7_gaps_check.py --ack    # ยืนยันว่าทบทวนช่องว่างต่อแหล่งใหม่ครบแล้ว (บันทึกแฮชปัจจุบัน)
หลักการ: มีแหล่งใหม่เข้าทะเบียนแฮช → เทสล้มจนกว่าจะทบทวนทุกช่องว่างที่ status=open ว่ายังเปิดอยู่หรือปิดแล้ว
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAPS = ROOT / "analysis/goal7/gaps.json"
HASH_FILES = list((ROOT / "data/32_goal7_chaophraya2").rglob("hashes.sha256")) + [ROOT / "data/32_goal7_chaophraya2/external_files.sha256"]
MANIFEST = ROOT / "data/manual/manifest.md"
MANUAL_FILTER = re.compile(r"ระบบระบายน้ำเจ้าพระยาฝั่งตะวันออกตอนล่าง|ป่าสัก|ทางระบายน้ำหลาก|เจ้าพระยา2")


def current_sources() -> dict[str, str]:
    """แฮช → ชื่อ/บรรทัดอธิบาย (เฉพาะแหล่งของเป้าหมาย 7)"""
    out: dict[str, str] = {}
    for f in HASH_FILES:
        if not f.exists():
            continue
        for ln in f.read_text(encoding="utf-8").splitlines():
            if ln.lstrip().startswith("#"):
                continue
            m = re.search(r"\b([0-9a-f]{64})\b", ln)
            if m:
                out[m.group(1)] = re.sub(r"\s+", " ", ln.replace(m.group(1), "")).strip(" ·|")[:110]
    if MANIFEST.exists():
        for ln in MANIFEST.read_text(encoding="utf-8").splitlines():
            m = re.search(r"\b([0-9a-f]{64})\b", ln)
            if m and MANUAL_FILTER.search(ln):
                out[m.group(1)] = re.sub(r"\s+", " ", ln.replace(m.group(1), "")).strip(" ·|`")[:110]
    return out


def load() -> dict:
    return json.loads(GAPS.read_text(encoding="utf-8"))


def new_sources() -> dict[str, str]:
    g = load()
    seen = set(g.get("reviewed_hashes", []))
    return {h: n for h, n in current_sources().items() if h not in seen}


def main():
    g = load()
    ns = new_sources()
    open_gaps = [x for x in g["gaps"] if x["status"] == "open"]
    if "--ack" in sys.argv:
        g["reviewed_hashes"] = sorted(current_sources())
        GAPS.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"บันทึกแฮช {len(g['reviewed_hashes'])} รายการ — ทบทวนแล้ว")
        return
    print(f"แหล่งใหม่ที่ยังไม่ได้ทบทวน: {len(ns)} · ช่องว่างที่ยังเปิด: {len(open_gaps)}")
    for h, n in ns.items():
        print("  +", n or h[:12])
    if ns:
        print("ช่องว่างที่ควรทบทวน (ดู closes_with):")
        for x in open_gaps:
            print(f"  - {x['id']}: {x['claim']} | ปิดได้ด้วย: {', '.join(x['closes_with'])}")


if __name__ == "__main__":
    main()
