"""run_all — รัน pipeline ทั้งระบบตามลำดับมาตรฐาน จบในคำสั่งเดียว

ลำดับ (ตามที่รีวิวภายนอกเสนอ + ปรับให้ทำงานได้แม้ข้อมูลดิบใหญ่ไม่อยู่บนเครื่อง):
    1. pytest                — ทดสอบ 26 ตัว (gate แรก)
    2. integrity --quick     — แฮชข้อมูล (exit 2 = MISSING ปกติบน clone ผ่านได้)
    3. attribution_share     — สัดส่วนเขื่อน/ฝน (ต้องมี data/16 CSV)
    4. goal4_model_v1        — โมเดลทำนายหลัก + results/coeffs
    5. goal4_model_backtest_long — LOSO 5 ฤดู (ช้า ~20-25 นาที — ข้ามได้ด้วย --fast)
    6. goal4_counterfactual_model — สถานการณ์ R1/M1-M4 (อ่าน corridor จาก hecras_lite)
    7. hecras_lite_channel   — ภาคตัดขวางลำน้ำ (ต้องมี DEM บนดิสก์)
    8. s2_water              — น้ำ optical จาก Sentinel-2 (ต้องมี SAFE บนดิสก์)
    9. build_canonical_numbers — รวมตัวเลข canonical
   10. build_report_html + build_expert_report — ประกอบรายงาน 2 ฉบับ (ตรวจ canonical ในตัว)

ขั้นที่ต้องการข้อมูลดิบขนาดใหญ่ที่ไม่ได้อยู่ใน git (S1 17 GB, DEM, S2 SAFE) —
ขาดเมื่อไรขั้นนั้นถูก "ข้าม (ไม่มีข้อมูล)" อัตโนมัติ ไม่ทำให้ทั้ง pipeline ล้ม
S1 ดิบ (s1_process/s1_change_detect) ไม่รวมอัตโนมัติเพราะช้าและข้อมูล 17 GB —
รันเฉพาะเมื่อ ingest ฉากใหม่เท่านั้น (ดู docs/METHODS.md §6)

ใช้: python analysis/run_all.py [--fast]   (--fast = ข้าม backtest ยาว)
"""
import argparse
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(cmd, cwd=PROJ):
    print(f"\n$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if r.returncode != 0:
        print(f"!! ล้ม (exit {r.returncode}) — หยุด pipeline", file=sys.stderr)
        sys.exit(r.returncode)


def have(*paths):
    return all((PROJ / p).exists() for p in paths)


steps = []

steps.append((True, [PY, "-m", "pytest", "tests/", "-q"]))
steps.append((True, [PY, "analysis/verify_data_integrity.py", "--quick"]))
steps.append((have("data/16_training_data/khundan_15min_Ny7_Jun-Oct2026.csv"),
              [PY, "analysis/attribution_share.py"]))
steps.append((have("data/16_training_data/khundan_15min_Ny7_Jun-Oct2026.csv"),
              [PY, "analysis/goal4_model_v1.py"]))
steps.append((True, [PY, "analysis/goal4_model_backtest_long.py"]))  # รันเฉพาะเมื่อ --with-backtest (ช้า)
steps.append((have("data/16_training_data/khundan_15min_Ny7_Jun-Oct2026.csv",
                   "analysis/river_cross_sections.json"),
              [PY, "analysis/goal4_counterfactual_model.py"]))
steps.append((have("data/13_sentinel1_copernicus/derived/dem_30m.npy",
                   "data/13_sentinel1_copernicus/derived/waterways.json"),
              [PY, "analysis/hecras_lite_channel.py"]))
steps.append((bool(list((PROJ / "data/18_sentinel2_copernicus").glob("S2B_MSIL2A_20261002*")))
              if (PROJ / "data/18_sentinel2_copernicus").exists() else False,
              [PY, "analysis/s2_water.py"]))
steps.append((True, [PY, "report/make_x_charts_thai.py"]))
steps.append((True, [PY, "analysis/build_canonical_numbers.py"]))
steps.append((True, [PY, "report/build_report_html.py"]))
steps.append((True, [PY, "report/build_expert_report.py"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="ข้าม backtest ยาว (~25 นาที)")
    ap.add_argument("--with-backtest", action="store_true", help="รัน backtest ยาวด้วย")
    args = ap.parse_args()

    ran = skipped = 0
    for i, (ok, cmd) in enumerate(steps, 1):
        name = " ".join(str(c) for c in cmd[1:])
        if not ok:
            print(f"[{i:>2}] SKIP (ไม่มีข้อมูลบนเครื่อง) — {name}")
            skipped += 1
            continue
        if "--fast" in sys.argv and "backtest_long" in name:
            print(f"[{i:>2}] SKIP (--fast) — {name}")
            skipped += 1
            continue
        if "backtest_long" in name and not args.with_backtest:
            print(f"[{i:>2}] SKIP (ใช้ --with-backtest เพื่อรัน) — {name}")
            skipped += 1
            continue
        print(f"[{i:>2}] RUN — {name}", flush=True)
        run(cmd)
        ran += 1

    print(f"\n== pipeline เสร็จ: รัน {ran} · ข้าม {skipped} — รายงานอยู่ที่ report/ ==")


if __name__ == "__main__":
    main()
