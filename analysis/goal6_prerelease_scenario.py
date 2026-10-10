"""คำถามต่อยอด M2/M3 — ถ้าเขื่อนปล่อยล่วงหน้าแรง-เร็วก่อนฝนถึง 3–4 วัน ระดับ C.2 ลดได้เท่าไร

วิธี (หยาบ เชิงตรวจแนวคิด — ไม่ใช่โมเดลไฮโดรลิกส์เต็ม):
1) สมการระดับน้ำ↔ปริมาตรที่ C.2 จากข้อมูลจริง 39 วัน (เส้นตรง)
2) สถานการณ์: ปล่อยเพิ่มจากที่ทำจริง โดยเริ่ม 11 ก.ย. (4 วันก่อนระลอกใหญ่ 20 ก.ย.)
   → น้ำส่วนเกินที่เคลื่อนออก = (X − ที่ปล่อยจริง) × 4 วัน
3) ลด Q พีคของ C.2 ลงตาม แล้วแปลงเป็นระดับด้วยสมการ
ข้อจำกัด: ไม่คิดน้ำเข้าเพิ่มจากฝนระลอกถัดมากลับมาชดเชย · ปล่อยได้มีเพดานจริง (ต้องเหลือน้ำใช้)
รัน: python analysis/goal6_prerelease_scenario.py
"""
import json
import urllib.request
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'nnyflood-goal6/1.0'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)

base = 'https://api-v3.thaiwater.net/api/v1/thaiwater30/'
src = json.loads((ROOT / 'data/22_goal6_network/raw/spike_ping_cp/c2_discharge_daily_sep2026.json').read_text(encoding='utf-8'))
src2 = json.loads((ROOT / 'data/22_goal6_network/raw/spike_ping_cp/c2_vs_dam_releases_sep2026.json').read_text(encoding='utf-8'))
dates = sorted(src['C2_daily_volume_max_mcm'])
c2v = np.array([src['C2_daily_volume_max_mcm'][d] for d in dates])
rel = np.array([(src2['bhumibol_released'].get(d) or 0) + (src2['sirikit_released'].get(d) or 0) for d in dates])
inflow = np.array([(src2['bhumibol_inflow'].get(d) or 0) + (src2['sirikit_inflow'].get(d) or 0) for d in dates])

d = get(f'{base}public/waterlevel_graph?station_type=tele_waterlevel&station_id=2795&start_date=2026-09-01&end_date=2026-10-09')
daily_lv = {}
for r in d['data']['graph_data']:
    if r.get('value') is None:
        continue
    daily_lv.setdefault(r['datetime'][:10], []).append(r['value'])
lv = np.array([max(daily_lv[dd]) for dd in dates])

A = np.vstack([np.ones_like(c2v), c2v]).T
coef, *_ = np.linalg.lstsq(A, lv, rcond=None)
pred = A @ coef
r2 = 1 - ((lv - pred) ** 2).sum() / ((lv - lv.mean()) ** 2).sum()
print(f"สมการระดับ C.2 ≈ {coef[0]:.2f} + {coef[1]:.5f} × ปริมาตร (ลลบ.ม./วัน) · R² = {r2:.3f}")

peak_idx = dates.index('2026-10-01')
i15 = dates.index('2026-09-15')
print(f"\nจุดตั้งต้น: พีค C.2 = 24.10 ม. (1 ต.ค.) · ปล่อยจริง 11–15 ก.ย. เฉลี่ย {rel[i15-2:i15+3].mean():.1f} ลลบ.ม./วัน")
print("\nสถานการณ์ปล่อยล่วงหน้า (เริ่ม 11 ก.ย. — 4 วันก่อนระลอกใหญ่):")
print(f"{'ปล่อย/วัน (ลลบ.ม.)':>18}{'น้ำเพิ่มออกก่อนพีค':>20}{'Q พีคใหม่':>12}{'ระดับพีคใหม่':>14}")
for extra in [40, 60, 80, 100]:
    actual_avg = rel[i15 - 2:i15 + 3].mean()
    moved = (extra - actual_avg) * 4
    q_new = max(c2v[peak_idx] - moved, 0)
    lv_new = coef[0] + coef[1] * q_new
    drop = lv[peak_idx] - lv_new
    print(f"{extra:>18}{moved:>20.0f}{q_new:>12.0f}{lv_new:>14.2f} ม. (ลด {drop:.2f})")

print("\n⚠️ ข้อจำกัดสำคัญ (ต้องอ่านก่อนตีความ):")
print("1. แบบหยาบเชิงปริมาตร — ไม่คิดน้ำเข้าเพิ่มจากระลอกถัดมาที่จะกลับมาเติมแม่น้ำใหม่")
print("2. ปล่อยล่วงหน้ามีเพดานจริง — อ่างต้องเหลือน้ำใช้ ต.-ง. (ภูมิพล+สิริกิติ์รวมเก็บจริง ~15,000 ลลบ.ม.)")
print("3. ต้องมีพยากรณ์เชื่อถือก่อนถึงตัดสินใจปล่อย — Q8 แสดงว่าพยากรณ์ 2 วันยังจำกัด")
print("4. ระดับ C.2 ไม่ใช่ระดับน้ำท่วมที่เมือง — เทียบต่อ Ny.7 ต้องผ่านโมเดล routing ต่างหาก")

out = {'equation': {'a': round(float(coef[0]), 3), 'b': round(float(coef[1]), 6), 'r2': round(r2, 3)},
       'scenarios': []}
for extra in [40, 60, 80, 100]:
    moved = (extra - rel[i15 - 2:i15 + 3].mean()) * 4
    q_new = max(c2v[peak_idx] - moved, 0)
    lv_new = coef[0] + coef[1] * q_new
    out['scenarios'].append({'release_per_day': extra, 'moved_mcm': round(moved),
                             'peak_q_new': round(q_new), 'peak_lv_new': round(lv_new, 2),
                             'drop_m': round(lv[peak_idx] - lv_new, 2)})
(ROOT / 'analysis/goal6/prerelease_scenario.json').write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print('\nเขียนแล้ว: analysis/goal6/prerelease_scenario.json')
