"""แบบจำลอง 3 มิติ: ตัวเลขมิติต้องมาจากไฟล์ทางการ · เรขาคณิตสมเหตุสมผล · จำนวนอาคารตรงตาราง 2.3.2-3 (99 แถว)"""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
import goal7_build_3d_model as m  # noqa: E402

GEOM = ROOT / "analysis/goal7/official_geometry.json"
SUMMARY = ROOT / "report/models/chaophraya2_model_summary.json"


@pytest.fixture(scope="module")
def geom():
    return json.loads(GEOM.read_text(encoding="utf-8"))


def test_structure_counts_match_official_table(geom):
    kinds = {}
    for s in geom["structures"]:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    assert len(geom["structures"]) == 99
    assert kinds == {"road_bridge": 42, "crossing": 39, "aqueduct": 7, "gate": 5, "inlet": 4, "rail_bridge": 2}


def test_gates_have_official_bays(geom):
    gates = [s for s in geom["structures"] if s["kind"] == "gate"]
    assert [g["km"] for g in gates] == [0.57, 23.0, 74.0, 102.0, 134.35]
    assert all((g["bays"], g["bay_width_m"], g["bay_height_m"]) == (4, 12.5, 6.0) for g in gates)


def test_profile_follows_official_slope_and_depth(geom):
    st = {round(s["km"], 2): s for s in geom["stations"]}
    for km in (23.0, 75.0, 110.0):
        s = st[km]
        assert abs((s["water"] - s["bed"]) - 7.0) < 0.02
        assert abs((s["crest"] - s["water"]) - 1.5) < 0.02
    assert abs(st[75.0]["bed"] - (-3.13)) < 0.02          # ค่ากำกับบนรูป 2.3.2-9


def test_section_area_matches_official_table(geom):
    chk = m.section_area_check(geom)
    assert abs(chk["reach2"]["diff_pct"]) < 0.1
    assert abs(chk["reach1"]["diff_pct"]) < 3.0            # แถวแรกของตารางไม่ตรงสูตร trapezoid พอดี (ดู note ของค่าคงที่)


def test_section_params_use_official_table(geom):
    t = geom["section_table"]
    assert m.section_params(10.0, t)["B"] == 53.0 and m.section_params(60.0, t)["B"] == 51.0
    assert m.section_params(60.0, t)["z_in"] == 3.0 and m.section_params(60.0, t)["road"] == 10.0
    assert 51.0 < m.section_params(135.0, t)["B"] < 380.0


def test_model_geometry_is_finite_and_complete():
    mesh, fr, g = m.build(1.0)
    n = 0
    for mat, polys in mesh.polys.items():
        assert mat in m.MATERIALS
        for p in polys:
            for v in p:
                assert all(math.isfinite(c) for c in v)
                n += 1
    for needed in ("water", "concrete_lining", "earth_lining", "road", "gate", "road_bridge", "rail_bridge", "aqueduct", "culvert"):
        assert mesh.polys[needed], needed
    assert n > 10000


@pytest.mark.skipif(not SUMMARY.exists(), reason="ยังไม่ได้รันสคริปต์")
def test_summary_lists_assumptions():
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert s["assumptions"] and s["structures_modelled"]["gate"] == 5


OBJ = ROOT / "report/models/chaophraya2.obj"
MTL = ROOT / "report/models/chaophraya2.mtl"


@pytest.mark.skipif(not OBJ.exists(), reason="ยังไม่ได้รันสคริปต์")
def test_obj_file_is_well_formed_and_matches_summary():
    """ตรวจไฟล์ที่ส่งมอบจริง (ตรวจแทนการเปิด SketchUp): ดัชนีหน้าถูกต้อง ไม่มีหน้าลดรูป วัสดุมีครบ และกรอบเขตตรงสรุป"""
    verts, faces, mats = [], [], set()
    for ln in OBJ.read_text(encoding="utf-8").splitlines():
        if ln.startswith("v "):
            verts.append(tuple(float(x) for x in ln.split()[1:4]))
        elif ln.startswith("f "):
            faces.append([int(tok.split("/")[0]) for tok in ln.split()[1:]])
        elif ln.startswith("usemtl "):
            mats.add(ln.split()[1])
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert len(verts) == s["vertices"] and len(faces) == s["faces"]
    assert all(len(f) >= 3 and all(1 <= i <= len(verts) for i in f) for f in faces)
    assert all(len(set(f)) == len(f) for f in faces)                       # ไม่มีจุดซ้ำในหน้าเดียว
    defined = {ln.split()[1] for ln in MTL.read_text(encoding="utf-8").splitlines() if ln.startswith("newmtl ")}
    assert mats <= defined
    xs, ys, zs = zip(*verts)
    lo, hi = s["bbox_m"]
    for got, want in ((min(xs), lo[0]), (min(ys), lo[1]), (min(zs), lo[2]), (max(xs), hi[0]), (max(ys), hi[1]), (max(zs), hi[2])):
        assert abs(got - want) <= 0.2                                      # สรุปปัดทศนิยม 1 ตำแหน่ง
