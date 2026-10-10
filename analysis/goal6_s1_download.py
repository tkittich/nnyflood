"""เป้าหมาย 6 — ดาวน์โหลดคิว S1 GRDH-COG จาก CDSE ผ่าน S3 (credential ของผู้ใช้ในไฟล์ gitignored)

ทำงานต่อจาก `analysis/goal6_s1_queue.py` (35 ฉาก ~42 GB):
1. อ่านคิวจาก data/22_goal6_network/raw/s1_queue/s1_queue.json (ชน footprint แล้ว)
2. รายฉาก: ถาม OData หา S3Path (จุดเริ่ม object ใน bucket eodata)
3. S3: list object ใต้ prefix → ดาวน์โหลดทีละไฟล์เก็บตามโครง .SAFE
   · resume: ไฟล์ .part ดาวน์โหลดต่อด้วย Range header · ไฟล์ที่เสร็จข้าม
   · SHA-256 ทุกไฟล์บันทึกใน _progress.json (ใช้ทำ manifest หลังจบ)
4. ปลายทาง: data/22_goal6_network/raw/s1_2026/<ชื่อฉาก>/...

ต้องการ: boto3 (pip install boto3 — ใช้เฉพาะเครื่องดาวน์โหลด ไม่อยู่ใน requirements.txt เพื่อไม่กระทบ env CI/โมเดล)
credential: data/22_goal6_network/.cdse_s3.json {"access_key","secret_key"} — gitignored (ผู้ใช้ใส่เอง, revoke ได้)
รัน: python analysis/goal6_s1_download.py [--limit N] [--test-one]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import boto3
from botocore.config import Config

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "data/22_goal6_network/raw/s1_queue/s1_queue.json"
CRED = ROOT / "data/22_goal6_network/.cdse_s3.json"
DEST = ROOT / "data/22_goal6_network/raw/s1_2026"
PROGRESS = DEST / "_progress.json"
ODATA = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
S3_ENDPOINT = "https://eodata.dataspace.copernicus.eu/"
CHUNK = 8 * 1024 * 1024


def s3_client() -> "boto3.resource":
    cred = json.loads(CRED.read_text(encoding="utf-8"))
    return boto3.resource(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=cred["access_key"],
        aws_secret_access_key=cred["secret_key"],
        region_name="default",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 6, "mode": "standard"},
            connect_timeout=60,
            read_timeout=180,
        ),
    )


def odata_lookup(name: str) -> dict:
    filt = f"Name eq '{name}'"
    url = ODATA + "?$filter=" + urllib.parse.quote(filt, safe="'(),=") + "&$top=1"
    req = urllib.request.Request(url, headers={"User-Agent": "nnyflood-goal6/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        d = json.load(resp)
    rows = d.get("value", [])
    if not rows:
        raise RuntimeError(f"OData ไม่พบ {name}")
    r = rows[0]
    return {"id": r["Id"], "s3_path": r["S3Path"], "content_length": r.get("ContentLength")}


def load_progress() -> dict:
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    return {"products": {}}


def save_progress(p: dict) -> None:
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROGRESS.with_suffix(".tmp")
    tmp.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(PROGRESS)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def download_object(s3, bucket: str, key: str, dest_file: Path) -> dict:
    """ดาวน์โหลด 1 object — resume ด้วย Range ถ้ามี .part ค้าง · คืน {bytes, sha256}"""
    obj = s3.Object(bucket, key)
    head = obj.meta.client.head_object(Bucket=bucket, Key=key)
    total = head["ContentLength"]
    part = dest_file.with_suffix(dest_file.suffix + ".part")
    start = part.stat().st_size if part.exists() else 0
    mode = "ab" if start else "wb"
    if start >= total:
        pass
    else:
        kwargs = {"Bucket": bucket, "Key": key}
        if start:
            kwargs["Range"] = f"bytes={start}-"
        resp = obj.meta.client.get_object(**kwargs)
        with open(part, mode) as f:
            stream = resp["Body"]
            while True:
                chunk = stream.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)
    size = part.stat().st_size
    if size != total:
        raise RuntimeError(f"ขนาดไม่ตรง {key}: {size} != {total} (ลบ .part แล้วรันใหม่ได้)")
    part.replace(dest_file)
    return {"bytes": total, "sha256": sha256_file(dest_file)}


def process_product(s3, bucket: str, name: str, rec: dict) -> dict:
    base_s3 = rec["s3_path"].lstrip("/")  # เช่น eodata/Sentinel-1/... -> หลัง bucket คือ 'Sentinel-1/...'
    bucket_name, base = base_s3.split("/", 1)
    bucket_name = bucket_name or bucket
    client = s3.meta.client
    paginator = client.get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix=base):
        keys += [o["Key"] for o in page.get("Contents", [])]
    out = {"s3_prefix": base, "objects": [], "n_objects": len(keys)}
    total_bytes = 0
    t0 = time.time()
    for key in sorted(keys):
        rel = key[len(base):].lstrip("/")
        dest_file = DEST / name / rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        info = download_object(s3, bucket_name, key, dest_file)
        total_bytes += info["bytes"]
        out["objects"].append({"key": key, **info})
        print(f"    {rel[:60]} · {info['bytes'] / 1e6:.0f} MB · sha {info['sha256'][:12]}", flush=True)
    out["total_bytes"] = total_bytes
    out["seconds"] = round(time.time() - t0, 1)
    if rec.get("content_length") and abs(total_bytes - rec["content_length"]) > rec["content_length"] * 0.05:
        out["size_note"] = f"S3 {total_bytes} vs OData {rec['content_length']} — ต่างเกิน 5% (โครงไฟล์ต่างกันได้ ไม่ถือว่าพัง)"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="จำนวนฉากที่ทำ (ทดสอบ)")
    ap.add_argument("--test-one", action="store_true", help="ทำฉากเล็กสุดฉากเดียวแล้วจบ")
    args = ap.parse_args()

    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    names = sorted({p["name"] for prods in q["basins"].values() for p in prods})
    if args.test_one:
        names = names[:1]
    if args.limit:
        names = names[: args.limit]

    prog = load_progress()
    done = set(prog["products"].keys())
    todo = [n for n in names if n not in done]
    print(f"คิว {len(todo)} ฉาก (ทำแล้ว {len(done)}) — ปลายทาง {DEST}", flush=True)

    s3 = s3_client()
    for i, name in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {name}", flush=True)
        try:
            meta = odata_lookup(name)
        except Exception as exc:  # noqa: BLE001
            print(f"    OData ERROR {str(exc)[:80]}", flush=True)
            prog["products"][name] = {"error": str(exc)[:200]}
            save_progress(prog)
            continue
        prog["products"][name] = {"odata": {"id": meta["id"], "content_length": meta["content_length"]}}
        save_progress(prog)
        try:
            res = process_product(s3, "eodata", name, {"s3_path": meta["s3_path"], "content_length": meta["content_length"]})
            prog["products"][name].update(res)
            prog["products"][name]["done"] = True
        except Exception as exc:  # noqa: BLE001
            prog["products"][name]["error"] = str(exc)[:300]
            print(f"    ERROR {str(exc)[:120]} — รันซ้ำเพื่อ resume", flush=True)
        save_progress(prog)
    n_ok = sum(1 for v in prog["products"].values() if v.get("done"))
    n_err = sum(1 for v in prog["products"].values() if v.get("error"))
    print(f"จบรอบ: เสร็จ {n_ok} · ค้าง/ผิด {n_err} — รันสคริปต์ซ้ำเพื่อ resume", flush=True)


if __name__ == "__main__":
    main()