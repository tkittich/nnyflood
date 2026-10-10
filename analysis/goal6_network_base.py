"""เป้าหมาย 6 — ขั้น 5: ชั้นเครือข่ายฐานระดับชาติ — HydroBASINS + ESA WorldCover

1) HydroBASINS มาตรฐาน v1c เอเชีย ระดับ 3–12 (โครงกราฟลำน้ำ + ขอบลุ่มย่อย)
   แหล่ง: data.hydrosheds.org/file/HydroBASINS/standard/hybas_as_levXX_v1c.zip (เปิด/ฟรี)
2) ESA WorldCover 10 ม. 2021 v200 — ไทล์ 3°×3° ที่ตัดประเทศไทย (18 ไทล์ N09–N18 × E096–E108)
   แหล่ง: esa-worldcover.s3.eu-central-1.amazonaws.com (เปิด/ฟรี) — ใช้ทำความหยาบ Manning (แผน 2D)
   ไทล์ใหญ่ 200–600 MB — ดึงแบบตัดขนาด + รีซูม (ไฟล์เป็นตัวทำเครื่องหมาย + .part)

ผลลัพธ์: data/22_goal6_network/raw/hydrobasins/ · data/22_goal6_network/raw/worldcover/
แฮช SHA-256 ต่อไฟล์ → _hashes.txt · ทำซ้ำได้ · รัน: python analysis/goal6_network_base.py [--wc]
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HB_DIR = ROOT / "data/22_goal6_network/raw/hydrobasins"
WC_DIR = ROOT / "data/22_goal6_network/raw/worldcover"
HASHES_HB = HB_DIR / "_hashes.txt"
HASHES_WC = WC_DIR / "_hashes.txt"
LEVELS = list(range(3, 13))
# ไทล์ที่ตัดประเทศไทย (ยืนยันจาก list bucket: lat N09..N18, lon E096..E108)
TH_TILES = [(lat, lon) for lat in (9, 12, 15, 18) for lon in (96, 99, 102, 105, 108)
            if not (lat == 18 and lon == 111) and not (lat == 9 and lon == 111)]

UA = {"User-Agent": "nnyflood-goal6/1.0"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hashes(p: Path) -> dict:
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if "  " in line:
            h, name = line.split("  ", 1)
            out[name.strip("*")] = h
    return out


def save_hashes(p: Path, d: dict) -> None:
    p.write_text("".join(f"{h}  {name}\n" for name, h in sorted(d.items())), encoding="utf-8", newline="\n")


def download(url: str, dest: Path) -> None:
    """ดาวน์โหลด + รีซูมด้วย .part (Range header)"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    done = part.stat().st_size if part.exists() else 0
    req = urllib.request.Request(url, headers={**UA, **({"Range": f"bytes={done}-"} if done else {})})
    with urllib.request.urlopen(req, timeout=120) as r, open(part, "ab" if done else "wb") as f:
        total = r.headers.get("Content-Length")
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    got = part.stat().st_size
    if total is not None and got < int(total):
        raise RuntimeError(f"{dest.name}: ดาวน์โหลดไม่ครบ {got}/{total}")
    part.replace(dest)


def fetch(url: str, dest: Path, hashes: dict, hp: Path, min_size: int = 0) -> bool:
    if dest.exists() and dest.stat().st_size >= min_size:
        return False
    print(f"ดึง {dest.name} ...", flush=True)
    for attempt in range(3):
        try:
            download(url, dest)
            break
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  ซ้ำ {attempt+1}: {e}", flush=True)
            time.sleep(3)
    hashes[dest.name] = sha256(dest)
    save_hashes(hp, hashes)
    print(f"  เสร็จ {dest.stat().st_size/1e6:.0f} MB", flush=True)
    return True


def main() -> None:
    only_wc = "--wc" in sys.argv

    # ---- HydroBASINS (เล็ก — ดึงเต็มทุกระดับ) ----
    if not only_wc:
        HB_DIR.mkdir(parents=True, exist_ok=True)
        hh = load_hashes(HASHES_HB)
        for lev in LEVELS:
            name = f"hybas_as_lev{lev:02d}_v1c.zip"
            fetch(f"https://data.hydrosheds.org/file/HydroBASINS/standard/{name}",
                  HB_DIR / name, hh, HASHES_HB)
        print("HydroBASINS ครบ 10 ระดับ", flush=True)

    # ---- WorldCover (ไทล์ไทย 18 ไทล์ — ใหญ่ ดึงแบบมีรีซูม) ----
    WC_DIR.mkdir(parents=True, exist_ok=True)
    hw = load_hashes(HASHES_WC)
    for lat, lon in TH_TILES:
        name = f"ESA_WorldCover_10m_2021_v200_N{lat:02d}E{lon:03d}_Map.tif"
        fetch(f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/{name}",
              WC_DIR / name, hw, HASHES_WC)
    print(f"WorldCover ครบ {len(TH_TILES)} ไทล์", flush=True)


if __name__ == "__main__":
    main()
