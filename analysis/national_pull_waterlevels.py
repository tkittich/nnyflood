"""คลังข้อมูลระดับชาติ — ระดับน้ำรายชั่วโมงทุกจุดวัดสำคัญ (199 จุด) × 2020–2026

เป้าหมาย: ฐานข้อมูลเดียวสำหรับวิเคราะห์ทั้งประเทศ (รายงานที่ 5 เครือข่ายระดับชาติ)
ทำซ้ำได้ · resume อัตโนมัติ (ไฟล์ที่มีแล้วข้าม) · จำกัดความถี่กัน API ล้ม
ผลลัพธ์: data/30_national_warehouse/waterlevels/<sid>.json (รายจุด รวมทุกปี)
รัน: python analysis/national_pull_waterlevels.py [--workers 6]
"""
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from multiprocessing import Pool

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://api-v3.thaiwater.net/api/v1/thaiwater30/'
OUT = ROOT / 'data/30_national_warehouse/waterlevels'
LOAD = ROOT / 'data/02_thaiwater/raw/2026-10-10_waterlevel_load.json'
YEARS = list(range(2020, 2027))


def get(url, retries=2):
    last = None
    for a in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'nnyflood-national/1.0'})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(1.5 * (a + 1))
    raise last


def pull_station(args):
    sid, code, name, basin = args
    out_file = OUT / f"{sid}.json"
    if out_file.exists():
        return f"skip {sid} {code}"
    data = {'station_id': sid, 'code': code, 'name': name, 'basin': basin, 'years': {}}
    for y in YEARS:
        try:
            d = get(f'{BASE}public/waterlevel_graph?station_type=tele_waterlevel'
                    f'&station_id={sid}&start_date={y}-01-01&end_date={y}-12-31')
            g = (d.get('data') or {}).get('graph_data') or []
            rows = [{'t': r.get('datetime'), 'lv': r.get('value'),
                     'q': r.get('discharge')} for r in g if r.get('value') is not None]
            if rows:
                data['years'][str(y)] = rows
        except Exception as e:
            data['years'][str(y)] = {'error': str(e)[:80]}
        time.sleep(0.05)
    n = sum(len(v) if isinstance(v, list) else 0 for v in data['years'].values())
    data['n_values'] = n
    out_file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return f"done {sid} {code} {n} ชม."


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    payload = json.loads(LOAD.read_text(encoding='utf-8'))
    wl = payload['waterlevel_data']
    rows = wl.get('data', wl) if isinstance(wl, dict) else wl
    jobs, seen = [], set()
    for r in rows:
        st = r.get('station') or {}
        if not st.get('is_key_station'):
            continue
        sid = st.get('id')
        if sid in seen:
            continue
        seen.add(sid)
        jobs.append((sid, st.get('tele_station_oldcode') or str(sid),
                     (st.get('tele_station_name') or {}).get('th') or str(sid),
                     ((r.get('basin') or {}).get('basin_name') or {}).get('th') or '?'))
    print(f"จุดวัด key: {len(jobs)}", flush=True)
    with Pool(6) as pool:
        for res in pool.imap_unordered(pull_station, jobs):
            print(res, flush=True)


if __name__ == '__main__':
    main()
