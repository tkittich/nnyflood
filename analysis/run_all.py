"""run_all — รัน pipeline ทั้งระบบตามลำดับมาตรฐาน จบในคำสั่งเดียว

ลำดับ (12 ขั้น; ทำงานได้แม้ข้อมูลดิบใหญ่ไม่อยู่บนเครื่อง — ขั้นที่ต้องมีข้อมูลจะถูกข้าม):
    1. pytest                     — ชุดทดสอบทั้งหมด (gate แรก)
    2. integrity --quick          — แฮชข้อมูล (exit 2 = MISSING ปกติบน clone = ผ่าน; exit 1 = MISMATCH = ล้ม)
    3. attribution_share          — สัดส่วนเขื่อน/ฝน (ต้องมี data/16 CSV)
    4. goal4_model_v1             — โมเดลทำนายหลัก + results/coeffs
    5. goal4_model_backtest_long  — LOSO 5 ฤดู (ช้า ~20-25 นาที — ข้ามได้ด้วย --fast)
    6. goal4_counterfactual_model — สถานการณ์ R1/M1-M4 (อ่าน corridor จาก hecras_lite)
    7. hecras_lite_channel        — ภาคตัดขวางลำ้น้ำ (ต้องมี DEM บนดิสก์)
    8. s2_water                   — น้ำ optical จาก Sentinel-2 (ต้องมี SAFE บนดิสก์)
    9. make_x_charts_thai         — กราฟ x1/x2 แกนไทย
   10. build_canonical_numbers    — รวมตัวเลข canonical (ต้องมีมาสก์ S1 บนดิสก์ — clone ข้าม)
   11. build_report_html          — รายงานประชาชน (ตรวจ canonical ในตัว)
   12. build_expert_report        — รายงานวิชาการ (ตรวจ canonical ในตัว)

ขั้นที่ต้องการข้อมูลดิบขนาดใหญ่ที่ไม่ได้อยู่ใน git (S1 17 GB, DEM, S2 SAFE) —
ขาดเมื่อไรขั้นนั้นถูก "ข้าม (ไม่มีข้อมูล)" อัตโนมัติ ไม่ทำให้ทั้ง pipeline ล้ม
และบรรทัดสรุปท้ายรันจะระบุชื่อขั้นที่ถูกข้ามทุกตัว
S1 ดิบ (s1_process/s1_change_detect) ไม่รวมอัตโนมัติเพราะช้าและข้อมูล 17 GB —
รันเฉพาะเมื่อ ingest ฉากใหม่เท่านั้น (ดู docs/METHODS.md §6)

ใช้: python analysis/run_all.py [--fast] [--with-backtest]   (--fast = ข้าม backtest ยาว)
"""
import argparse
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(cmd, cwd=PROJ, ok_codes=(0,)):
    print(f"\n$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if r.returncode not in ok_codes:
        print(f"!! ล้ม (exit {r.returncode}) — หยุด pipeline", file=sys.stderr)
        sys.exit(r.returncode)


def have(*paths):
    return all((PROJ / p).exists() for p in paths)


steps = []

steps.append((True, [PY, "-m", "pytest", "tests/", "-q"], (0,)))
# exit 2 = MISSING (ไฟล์ใหญ่ไม่อยู่ใน git — ปกติบน clone) = ผ่าน; exit 1 = MISMATCH = ล้ม
steps.append((True, [PY, "analysis/verify_data_integrity.py", "--quick", "--max-bytes", "50000000"], (0, 2)))
steps.append((have("data/16_training_data/khundan_15min_Ny7_Jun-Oct2026.csv"),
              [PY, "analysis/attribution_share.py"], (0,)))
steps.append((have("data/16_training_data/khundan_15min_Ny7_Jun-Oct2026.csv"),
              [PY, "analysis/goal4_model_v1.py"], (0,)))
steps.append((True, [PY, "analysis/goal4_model_backtest_long.py"], (0,)))  # รันเฉพาะเมื่อ --with-backtest (ช้า)
steps.append((have("data/16_training_data/khundan_15min_Ny7_Jun-Oct2026.csv",
                   "analysis/river_cross_sections.json"),
              [PY, "analysis/goal4_counterfactual_model.py"], (0,)))
steps.append((have("data/13_sentinel1_copernicus/derived/dem_30m.npy",
                   "data/13_sentinel1_copernicus/derived/waterways.json"),
              [PY, "analysis/hecras_lite_channel.py"], (0,)))
steps.append((bool(list((PROJ / "data/18_sentinel2_copernicus").glob("S2B_MSIL2A_20261002*")))
              if (PROJ / "data/18_sentinel2_copernicus").exists() else False,
              [PY, "analysis/s2_water.py"], (0,)))
steps.append((True, [PY, "report/make_x_charts_thai.py"], (0,)))
steps.append((have("data/13_sentinel1_copernicus/derived/grid.json",
                   "data/13_sentinel1_copernicus/derived/flood_peak_27sep1828.npy",
                   "data/13_sentinel1_copernicus/derived/flood_2oct_validated.npy",
                   "analysis/s1_flood_series.json",
                   "analysis/gistda_pass_areas_nn.json",
                   "analysis/attribution_share.json",
                   "analysis/goal4_counterfactual_summary.json",
                   "analysis/goal4_model_v1_results.json",
                   "analysis/goal4_model_backtest_long.json"),
              [PY, "analysis/build_canonical_numbers.py"], (0,)))
steps.append((True, [PY, "report/build_report_html.py"], (0,)))
steps.append((True, [PY, "report/build_expert_report.py"], (0,)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="ข้าม backtest ยาว (~25 นาที)")
    ap.add_argument("--with-backtest", action="store_true", help="รัน backtest ยาวด้วย")
    args = ap.parse_args()

    ran = skipped = 0
    skipped_names = []
    for i, (ok, cmd, ok_codes) in enumerate(steps, 1):
        name = " ".join(str(c) for c in cmd[1:])
        if not ok:
            print(f"[{i:>2}] SKIP (ไม่มีข้อมูลบนเครื่อง) — {name}")
            skipped += 1
            skipped_names.append(name)
            continue
        if args.fast and "backtest_long" in name:
            print(f"[{i:>2}] SKIP (--fast) — {name}")
            skipped += 1
            skipped_names.append(name)
            continue
        if "backtest_long" in name and not args.with_backtest:
            print(f"[{i:>2}] SKIP (ใช้ --with-backtest เพื่อรัน) — {name}")
            skipped += 1
            skipped_names.append(name)
            continue
        print(f"[{i:>2}] RUN — {name}", flush=True)
        run(cmd, ok_codes=ok_codes)
        ran += 1

    print(f"\n== pipeline เสร็จ: รัน {ran} · ข้าม {skipped} — รายงานอยู่ที่ report/ ==")
    if skipped_names:
        print("   ขั้นที่ข้าม: " + " · ".join(skipped_names))


if __name__ == "__main__":
    main()
