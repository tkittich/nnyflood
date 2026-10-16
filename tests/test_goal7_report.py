"""ตรวจรายงานที่ 7–8 (คลองเจ้าพระยา2) ทั้ง 2 ฉบับ — รันหลังสร้าง แยกจาก builder (กันวนซ้ำ)
โครงเดียวกับ test_report3_language: TLDR · บริบท · อ่านจบในตัวเอง · ห้ามทับศัพท์ · ภาพประกอบ · ตัวเลขตรง canonical"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "report/คลองเจ้าพระยา2_ประชาชน.html"
ACADEMIC = ROOT / "report/คลองเจ้าพระยา2_วิชาการ.html"
CAN = ROOT / "analysis/goal7/canonical.json"
BOTH = [PUBLIC, ACADEMIC]
BANNED = ["พีค", "น้ำพีค", "attribution", "คาลิเบรต", "เทมเพลต", "rule curve", "rulecurve",
          "critical", "datum", "baseline", "config", "scenario", "workflow", "threshold"]


def _body(p):
    h = p.read_text(encoding="utf-8")
    b = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    b = re.sub(r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]+", " ", b)
    b = re.sub(r"<code>.*?</code>", " ", b, flags=re.S)
    return h, re.sub(r"<[^>]+>", " ", b)


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_exists(p):
    assert p.exists(), f"ยังไม่ได้สร้าง {p.name} — รัน report/goal7_build_public.py / goal7_build_academic.py"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_no_banned_terms(p):
    _, b = _body(p)
    hits = {w: len(re.findall(w, b, flags=re.I)) for w in BANNED}
    hits = {k: v for k, v in hits.items() if v}
    assert not hits, f"พบคำทับศัพท์: {hits}"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_structure(p):
    h, _ = _body(p)
    assert "สรุปสั้น (อ่าน 2 นาที)" in h
    assert "บริบทสำหรับผู้อ่านใหม่" in h
    assert "อ่านจบในตัวเอง" in h
    assert h.count("<figure>") >= 4, "ต้องมีภาพประกอบอย่างน้อย 4 ภาพ"


def test_public_has_qa():
    h, _ = _body(PUBLIC)
    assert "ถาม 1" in h and "ถาม 6" in h, "ฉบับประชาชนต้องมีหัวข้อถาม–ตอบ"


def test_academic_has_method_and_appendix():
    h, _ = _body(ACADEMIC)
    for w in ("ข้อมูลและวิธีการ", "ภาคผนวก ก.", "ภาคผนวก ข.", "ภาคผนวก ค.", "คำถามที่ลงทะเบียนไว้ก่อนดูผล"):
        assert w in h, f"ฉบับวิชาการต้องมี: {w}"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_numbers_match_canonical(p):
    c = json.loads(CAN.read_text(encoding="utf-8"))
    _, b = _body(p)
    nn = c["structures"]["nakhonnayok"]
    assert f"{nn['n_siphon']}" in b
    assert f"{c['c2']['years']['2026']['peak_daily_m3s']:,}" in b
    assert f"{c['corridor_area']['rai']['mixed']:,}" in b
    assert f"{c['structures']['n_total']}" in b


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_alignment_caveat_and_tiers(p):
    _, b = _body(p)
    assert "ไม่ใช่แนวทางการ" in b or "ไม่ใช่ข้อมูลทางการ" in b, "ต้องระบุว่าแนวคลองไม่เป็นทางการ"
    assert "ชั้น A" in b and "ชั้น B" in b


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_concerns_listed_as_claims_not_facts(p):
    c = json.loads(CAN.read_text(encoding="utf-8"))
    _, b = _body(p)
    assert len(c["concerns"]) == 13
    assert "ผู้ยื่นระบุ" in b, "ข้อห่วงกังวลต้องระบุเป็นข้อความของผู้ยื่น ไม่ใช่ข้อเท็จจริง"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_no_person_blaming(p):
    _, b = _body(p)
    for w in ("ทุจริต", "ผลาญงบ", "ผิดพลาดโดยเจตนา", "ต้องรับผิดชอบ"):
        assert w not in b


# ---- เพิ่ม 15 ต.ค. 69: ความสูงคันตามข้อมูล · ภาพประกอบ · คำถามเพิ่ม · กฎหมาย/PDPA ----
def test_embankment_uses_documented_heights_only():
    c = json.loads(CAN.read_text(encoding="utf-8"))
    ids = [x["id"] for x in c["embankment"]["cases"]]
    assert ids == ["eia_lo", "eia_hi"], "ต้องใช้เฉพาะความสูงคันตามรูปตัดตามยาว (ไม่มีกรณีสมมติ 6/7 ม.)"
    top = max(x["crest_above_ground_m"] for x in c["embankment"]["cases"])
    assert top <= 4.8
    for p in (PUBLIC, ACADEMIC):
        _, b = _body(p)
        assert "คันสูง 6 หรือ 7" not in b and "สมมติคันสูง 6" not in b


def test_new_figures_and_questions():
    pub = PUBLIC.read_text(encoding="utf-8")
    aca = ACADEMIC.read_text(encoding="utf-8")
    assert pub.count("<figure>") >= 9 and aca.count("<figure>") >= 10
    assert pub.count("class='qa'") >= 7, "ถาม–ตอบต้องมีอย่างน้อย 24 ข้อ (เพิ่มประตู/รอยเลื่อน/ทางเลือก/การดูแล/ข้อเสนอ)"
    for w in ("ประตูจะเปิด–ปิดอย่างไร", "รอยเลื่อนองครักษ์", "ทางเลือกอื่น", "ใครดูแลคันและท่อ", "กันยายน 2569", "ใช้เวลานานเท่าไร", "ข้ามคลองได้ที่ไหน", "คุ้มค่าก่อสร้าง", "หอย", "นครนายกได้ประโยชน์จากเจ้าพระยา2"):
        assert w in pub


@pytest.mark.parametrize("p", [PUBLIC, ACADEMIC], ids=["ประชาชน", "วิชาการ"])
def test_legal_pdpa_no_persons_no_blame(p):
    """กฎหมายหมิ่นประมาท + PDPA (docs/LEGAL_REVIEW.md §4): ไม่มีชื่อบุคคลธรรมดา/เบอร์/ลิงก์โปรไฟล์ · ไม่ตั้งกรอบหาคนผิด"""
    _, b = _body(p)
    assert not re.search(r"(?<![ก-๙])(?:นางสาว|นาย|นาง)(?!ก|อำเภอ)[ก-๙]{2,}\s+[ก-๙]{2,}", b), "พบชื่อบุคคลธรรมดา"
    assert not re.search(r"0\d{1,2}[- ]?\d{3}[- ]?\d{4}", b), "พบเบอร์โทร"
    for w in ("ทุจริต", "โกง", "เจตนา", "ละเลย", "หลอกลวง", "ใครผิด", "ใครรับผิด", "ผลประโยชน์ทับซ้อน"):
        assert w not in b, f"พบถ้อยคำกล่าวหา: {w}"


def test_profile_from_drawing_consistent():
    """รูปตัดตามยาว (รูปที่ 2.3.2-9): ค่าที่อ่านต้องสอดคล้องกับค่าที่รายงานระบุ (สันคันสูงสุดเหนือพื้น 4.8 ม. · ระดับน้ำเหนือพื้น 1.0–3.3 ม.)"""
    c = json.loads(CAN.read_text(encoding="utf-8"))
    nn = c["eia_profile"]["nn_reach"]
    assert abs(nn["crest_above_ground_max_m"] - 4.8) <= 0.1
    assert 1.0 <= nn["water_above_ground_min_m"] and nn["water_above_ground_max_m"] <= 3.4
    rows = {r["km"]: r for r in c["eia_profile"]["rows"]}
    # ค่ากำกับบนรูป: กม.75 สันคัน +5.36 น้ำ +3.86
    assert abs(rows[75]["crest_m"] - 5.36) <= 0.02 and abs(rows[75]["water_m"] - 3.86) <= 0.02
    assert c["eia_profile"]["connecting_canal"]["km"] == [39.8, 51.5]


def test_options_screening_present_and_labeled():
    c = json.loads(CAN.read_text(encoding="utf-8"))
    o = c["options"]
    assert [w["water_above_ground_m"] for w in o["wide_canal"]] == [3.3, 2.0, 1.0, 0.0]
    assert o["wide_canal"][0]["land_vs_now_pct"] == 0 and abs(o["wide_canal"][0]["bottom_m"] - 51) <= 2, "ฐานเทียบต้องตรงหน้าตัดตามรายงาน"
    assert len(c["basins_2569"]["rows"]) == 17
    _, b = _body(ACADEMIC)
    assert "ข้อเสนอของผู้จัดทำ" in b and "ไม่ใช่ข้อมูลทางการ" in b
    _, b2 = _body(PUBLIC)
    assert "ข้อเสนอของผู้จัดทำ" in b2


# ---- ค่าที่ถูกแทนแล้ว (retired) — ห้ามค้างในรายงาน/builder (เพิ่ม 15 ต.ค. 69 หลังรีวิวอิสระ 3 ฉบับ) ----
RETIRED = ["2.5–4.8", "เฉพาะแม่น้ำใน 28.05", "น้ำสูงเพิ่ม ~19–39", "ผิวน้ำสูงขึ้นส่วนล้นไซฟอน",
           "ที่ยังไม่ปรากฏในเอกสารที่พบ:</b> ความสูงสันคัน", "ไม่มีขนาดอาคาร ความสูงคัน หรือระดับน้ำออกแบบ</b> ·"]
ALL_REPORTS = [PUBLIC, ACADEMIC]
BUILDERS = [ROOT / f"report/goal7_build_{n}.py" for n in ("public", "academic")]


@pytest.mark.parametrize("p", ALL_REPORTS + BUILDERS, ids=lambda p: p.name)
def test_no_retired_values(p):
    t = p.read_text(encoding="utf-8")
    hits = [r for r in RETIRED if r in t]
    assert not hits, f"{p.name} มีค่าที่ถูกแทนแล้ว: {hits}"


def test_nn_reach_stats_cover_full_reach():
    d = json.loads(CAN.read_text(encoding="utf-8"))["eia_profile"]
    r = d["nn_reach"]
    assert r["km"] == [38.6, 73.2]
    # พื้นดินต่ำสุด ~1.47 ม. อยู่ที่ปลายช่วง (กม.73.2) — ถ้าวนไม่ถึงปลายช่วง ค่านี้จะเป็น 1.95
    assert r["ground_min_m"] <= 1.5


def test_builders_have_no_crest_range_literal():
    """ช่วงสันคันเหนือพื้นเดิมต้องมาจาก canonical (eia_profile.nn_reach) — ห้ามพิมพ์เป็น literal ใน builder
    (ต้นเหตุของ "2.5–4.8" ค้าง — รีวิวอิสระ 15 ต.ค. 69)"""
    r = json.loads(CAN.read_text(encoding="utf-8"))["eia_profile"]["nn_reach"]
    lits = [f"{r['crest_above_ground_min_m']}–{r['crest_above_ground_max_m']}",
            f"{r['water_above_ground_min_m']}–{r['water_above_ground_max_m']}"]
    for b in BUILDERS:
        code = "\n".join(ln for ln in b.read_text(encoding="utf-8").splitlines() if not ln.strip().startswith("#"))
        for lit in lits:
            assert lit not in code, f"{b.name}: literal {lit!r} — อ่านจาก canonical"


def test_canal_in_three_basins_only():
    b = json.loads((ROOT / "analysis/goal7/basin_containment.json").read_text(encoding="utf-8"))
    assert b["n_basins"] == 3 and {x["basin"] for x in b["basins"]} == {"เจ้าพระยา", "ป่าสัก", "บางปะกง"}
    assert abs(b["sum_km"] - b["line_len_km"]) < 1.0


# ---- ทะเบียนช่องว่างความรู้ (กันข้อความล้าสมัย — เพิ่ม 16 ต.ค. 69) ----
GAPS = ROOT / "analysis/goal7/gaps.json"
_MISSING_RX = re.compile(r"ไม่พบ|ยังไม่พบ|ยังไม่ปรากฏ|ไม่ปรากฏ|ยังไม่มี|ยังไม่ได้อ่าน|ยังไม่ได้ตรวจ|ยังไม่ทราบ|ยังไม่ชัด|ไม่ระบุ|ยังไม่ได้รับ|ยังตอบ|ยังไม่รู้|ยังไม่แน่")


def _gap_lines():
    for b in BUILDERS:
        for i, ln in enumerate(b.read_text(encoding="utf-8").splitlines(), 1):
            if ln.strip().startswith("#"):
                continue
            yield b, i, ln


def test_missing_knowledge_sentences_are_tagged():
    """ประโยค "ไม่พบ/ยังไม่รู้…" ต้องผูกรหัสช่องว่าง (# gap: id) หรือ n/a ถ้าไม่ใช่การอ้างความรู้ที่ขาด"""
    bad = [f"{b.name}:{i}" for b, i, ln in _gap_lines() if _MISSING_RX.search(ln) and "# gap:" not in ln]
    assert not bad, f"ประโยคบอกว่าขาดข้อมูลแต่ไม่มีรหัสช่องว่าง: {bad[:10]}"


def test_gap_ids_are_open_in_ledger():
    """ช่องว่างที่ปิดแล้ว (closed) ห้ามมีประโยคอ้างถึงค้างอยู่ — ต้องแก้ข้อความให้เป็นข้อเท็จจริงใหม่"""
    led = {g["id"]: g for g in json.loads(GAPS.read_text(encoding="utf-8"))["gaps"]}
    used, stale, unknown = set(), [], []
    for b, i, ln in _gap_lines():
        m = re.search(r"# gap: ([a-z0-9_/]+)", ln)
        if not m or m.group(1) == "n/a":
            continue
        gid = m.group(1)
        used.add(gid)
        if gid not in led:
            unknown.append(f"{b.name}:{i}:{gid}")
        elif led[gid]["status"] != "open":
            stale.append(f"{b.name}:{i}:{gid}")
    assert not unknown, f"รหัสช่องว่างที่ไม่มีในทะเบียน: {unknown}"
    assert not stale, f"ช่องว่างปิดแล้วแต่ข้อความยังอ้างอยู่ — แก้บรรทัดเหล่านี้: {stale}"
    dead = [k for k, g in led.items() if g["status"] == "open" and k not in used]
    assert not dead, f"ช่องว่างที่ยังเปิดแต่ไม่มีที่ใช้ในรายงาน (ลบหรือปิดแล้ว?): {dead}"


def test_no_unreviewed_sources():
    """แหล่งข้อมูลใหม่ในทะเบียนแฮช = ต้องทบทวนช่องว่างที่ยังเปิดก่อน (python analysis/goal7_gaps_check.py)"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("g7gaps", ROOT / "analysis/goal7_gaps_check.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ns = m.new_sources()
    assert not ns, f"มีแหล่งใหม่ {len(ns)} รายการที่ยังไม่ได้ทบทวนช่องว่าง: {list(ns.values())[:5]} — รัน analysis/goal7_gaps_check.py แล้ว --ack"


# ---- เพิ่ม 16 ต.ค. 69: กรณีใหม่ · โครงหมวดพับได้ · เอกสารสถานะตรงกับรายงาน ----
HANDOFF = ROOT / "HANDOFF.md"


def test_new_cases_regression():
    """ตัวเลขกรณีใหม่ (new_cases) — ล็อกค่าสำคัญ ถ้าหน้าตัด/สมการเปลี่ยน เทสต์นี้ต้องล้มก่อนรายงานเปลี่ยนเงียบ ๆ"""
    nc = json.loads(CAN.read_text(encoding="utf-8"))["new_cases"]
    t = nc["tide"]["cases"]
    assert abs(t[0]["rise_m"]["134"]) < 0.05, "ปลายคลองตามแบบ (+1.5) ต้องไม่เท้อ"
    assert abs(t[1]["rise_m"]["134"] - 1.02) < 0.05 and abs(t[1]["rise_m"]["40"] - 0.18) < 0.05
    d = nc["deep_cut"]
    assert abs(d["depth_m"] - 11.9) < 0.3 and d["crest_above_ground_nn_max_m"] <= 2.0
    assert d["tide_rise_m"]["40"] > t[1]["rise_m"]["40"] * 3, "ขุดลึก: น้ำทะเลหนุนต้องส่งผลไกลกว่าแบบเดิมชัดเจน"
    assert abs(nc["tourism"]["water_area_km2"] - 10.3) < 0.2
    h = nc["hydro"]
    assert h["pv_gwh_per_year"][0] / h["days_scenarios"]["90"]["gate_gwh"] >= 15


def _pub():
    return PUBLIC.read_text(encoding="utf-8")


def test_public_questions_collapsible_and_numbered():
    h = _pub()
    heads = re.findall(r"<details class='qd'( open)?><summary>ถาม (\d+):", h)
    nums = [int(n) for _, n in heads]
    assert nums == list(range(1, len(nums) + 1)), f"เลขถามต้องเรียง 1..N ไม่ข้าม/ซ้ำ: {nums}"
    n_open = sum(1 for o, _ in heads if o)
    assert 3 <= n_open <= 8, "คำถามสำคัญเปิดไว้ตั้งต้น (3–8 ข้อ) ที่เหลือพับ"
    assert len(nums) < 25, "คำถามซ้ำซ้อนต้องรวมแล้ว"


def test_public_cross_refs_point_to_existing_questions():
    h = _pub()
    n = len(re.findall(r"<details class='qd'", h))
    body = re.sub(r"<[^>]+>", " ", h)
    refs = {int(x) for m in re.findall(r"ถาม (\d+(?:, \d+)*)", body) for x in m.split(", ")}
    assert refs and max(refs) <= n, f"อ้างถามที่ไม่มีอยู่: {sorted(r for r in refs if r > n)}"


def test_handoff_question_count_current():
    """HANDOFF ต้องบอกจำนวนถาม–ตอบตรงกับรายงานจริง (กันเอกสารสถานะล้าสมัย — เกิดขึ้นแล้ว: เขียน 19 ข้อขณะรายงานมี 20)"""
    n = len(re.findall(r"<details class='qd'", _pub()))
    t = HANDOFF.read_text(encoding="utf-8")
    assert f"ถาม–ตอบ {n} ข้อ" in t, f"HANDOFF.md ต้องมีข้อความ 'ถาม–ตอบ {n} ข้อ'"


# ---- เอ็นจินรายงาน (16 ต.ค. 69): key คงที่ · เลขอัตโนมัติ · ชิ้นส่วนร่วม (docs/REPORT_CONVENTIONS.md §2–3) ----
def test_builders_have_no_hardcoded_numbering_refs():
    """ห้ามพิมพ์เลขถาม/เลขข้อวิชาการเป็น literal ใน builder — ใช้โทเคน ⟦key⟧ (ย้ายคำถามแล้วเลขตามอัตโนมัติ)"""
    bad = []
    for b in BUILDERS:
        for i, ln in enumerate(b.read_text(encoding="utf-8").splitlines(), 1):
            code = ln.split("  # ")[0]
            if code.strip().startswith("#"):
                continue
            if re.search(r"ถาม \d|ข้อ 3\.\d|ฉบับวิชาการ ข้อ", code):
                bad.append(f"{b.name}:{i}")
    assert not bad, f"พบเลขอ้างอิงที่พิมพ์ตรง ๆ (ใช้ ⟦key⟧): {bad[:10]}"


@pytest.mark.parametrize("p", BOTH, ids=["ประชาชน", "วิชาการ"])
def test_no_unresolved_reference_tokens(p):
    h = p.read_text(encoding="utf-8")
    assert "⟦" not in h and "⟧" not in h, "มีโทเคนอ้างข้อที่ยังไม่ถูกแปลง — รัน report/goal7_build_all.py"
    assert "เลขอ้างอิงจะปรากฏหลังสร้างรอบสอง" not in h, "ผังหัวข้อยังไม่นิ่ง — รัน report/goal7_build_all.py"


def test_outlines_match_reports():
    for ed, p in (("public", PUBLIC), ("academic", ACADEMIC)):
        o = json.loads((ROOT / f"analysis/goal7/outline_{ed}.json").read_text(encoding="utf-8"))
        keys = [i["key"] for i in o["items"]]
        assert len(keys) == len(set(keys)), f"key ซ้ำใน outline_{ed}"
        _, b = _body(p)
        for it in o["items"]:
            if it["kind"] == "q":
                assert f"ถาม {it['number']}:" in b, f"{ed}: ถาม {it['number']} ({it['key']}) ไม่อยู่ในรายงาน (outline ล้าสมัย — รัน goal7_build_all.py)"
            elif it["kind"] == "h3" and it["number"]:
                assert f"{it['number']} " in b, f"{ed}: ข้อ {it['number']} ({it['key']}) ไม่อยู่ในรายงาน (outline ล้าสมัย)"


def test_shared_tables_not_duplicated_across_builders():
    """ตารางที่อยู่ในทั้งสองฉบับต้องมาจาก goal7_blocks.py (ที่เดียว) — ห้ามมีหัวตารางเดียวกันในสอง builder"""
    def heads(path):
        t = path.read_text(encoding="utf-8")
        return {tuple(re.findall(r'"([^"]+)"', m)[:3]) for m in re.findall(r"table\(\[(.*?)\]", t, flags=re.S)}
    dup = heads(BUILDERS[0]) & heads(BUILDERS[1])
    assert not dup, f"ตารางซ้ำสอง builder (ย้ายไป goal7_blocks.py): {list(dup)[:3]}"
