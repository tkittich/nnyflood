"""วิเคราะห์ทั้งลุ่มบางปะกงและฉะเชิงเทรา (goal7_bangpakong_chachoengsao) — โครงผล ความสอดคล้อง และข้อสรุปที่ต้องเป็นจริงตามข้อมูล"""
import json
from pathlib import Path

R = json.loads((Path(__file__).resolve().parent.parent / "analysis/goal7/bangpakong_chachoengsao.json").read_text(encoding="utf-8"))


def test_flood_area_consistent_with_gistda_attribute_area():
    """พื้นที่น้ำท่วมบนตาราง (ถ่วง f_area) ต้องใกล้ผลรวม f_area ของ GISTDA (ไม่ใช่พื้นที่รูปทรง ซึ่งใหญ่กว่าราว 2 เท่า)"""
    for pv in ("ฉะเชิงเทรา", "นครนายก", "ปราจีนบุรี"):
        grid = R["terrain"]["provinces"][pv]["flooded_km2_grid"]
        att = R["gistda_30d"][pv]["2026-10-20"]["total_km2"]
        assert abs(grid - att) / att < 0.12, (pv, grid, att)


def test_elevation_explains_flooding_more_than_province():
    ve = R["terrain"]["variance_explained_flooded_cells"]
    assert ve["by_elevation_zone"] > 10 * ve["by_province"]


def test_basin_covers_the_three_provinces_and_gauge_upstream_is_most_of_basin():
    b = R["basin"]
    for v in b["overlap_with_provinces"].values():
        assert v["share_of_province_in_basin_pct"] > 90
    assert 0.5 < b["upstream_of_gauges"]["BPK003 บางน้ำเปรี้ยว"]["area_union_km2"] / b["basin_area_km2"] < 0.8


def test_bpk003_gauge_story_fields():
    s = {x["code"]: x for x in R["gauges"]["stations"]}
    assert s["BPK003"]["run_above_bank_days_to_latest"] > 7           # ยังท่วมเหนือตลิ่งต่อเนื่อง
    assert s["Kgt.1"]["latest_minus_bank_m"] < 0                      # ต้นน้ำลงต่ำกว่าตลิ่งแล้ว
    assert R["story"]["lag_first_upstream_to_bpk003_days"] > 3
    assert 0 < R["story"]["bpk003_recession_m_per_day_last7d"] < 0.3


def test_snapshots_archived_not_overwritten():
    root = Path(__file__).resolve().parent.parent / "data/12_gistda_flood/raw/provinces"
    if root.exists():   # ไฟล์ดิบอยู่นอก git — ตรวจเฉพาะเมื่อมีบนเครื่อง
        assert (root / "ฉะเชิงเทรา_30days_2026-10-16.json").exists()


def test_gistda_recent_windows_present_and_7day_is_substantial():
    rc = R["gistda_recent"]
    assert rc["ฉะเชิงเทรา"]["7days"]["area_km2"] > 100
    assert any("_202610" in x and int(x.split("_")[1]) >= 20261014 for x in rc["ฉะเชิงเทรา"]["7days"]["scenes"])
