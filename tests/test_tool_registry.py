"""รอบ 6: ทะเบียนเครื่องมือ (tools/registry.json) ต้องถูกต้อง ไฟล์มีจริง และส่วนที่สร้างอัตโนมัติใน ENVIRONMENT.md ตรงกับทะเบียน
(คำเตือนเรื่องสคริปต์ที่ยังไม่ลงทะเบียน/สภาพแวดล้อมนอก repo ไม่ทำให้เทสต์ตก — เป็นหน้าที่ของ tools/doctor.py)"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import doctor  # noqa: E402


def test_registry_schema_valid():
    assert doctor.check_schema(doctor.load_registry()) == []


def test_registered_tool_files_exist():
    _, errs = doctor.check_tools(doctor.load_registry())
    assert errs == []


def test_generated_environment_section_in_sync():
    reg = doctor.load_registry()
    stored = json.loads(doctor.PROBE.read_text(encoding="utf-8")) if doctor.PROBE.exists() else {}
    cur = doctor.current_generated(doctor.ENV_DOC.read_text(encoding="utf-8"))
    assert cur == doctor.render_section(reg, stored), "รัน python tools/doctor.py --write-docs"


def test_superseded_env_is_not_used_by_active_tool_without_warning():
    reg = doctor.load_registry()
    warns, _ = doctor.check_tools(reg)
    assert not [w for w in warns if "ถูกแทนที่แล้ว" in w], warns


def test_verify_all_runs_doctor_step():
    assert "tools/doctor.py" in (ROOT / "tools/verify_all.py").read_text(encoding="utf-8")


def test_docs_registry_valid_and_index_in_sync():
    reg = doctor.load_registry()
    _, errs = doctor.check_docs(reg)
    assert errs == [], errs
    assert doctor.DOCS_INDEX.read_text(encoding="utf-8") == doctor.render_docs_index(reg), "รัน python tools/doctor.py --write-docs"


def test_every_markdown_doc_is_registered():
    reg = doctor.load_registry()
    paths = {d["path"] for d in reg["docs"]}
    missing = [p for p in doctor.doc_files() if p not in paths]
    assert missing == [], f"เอกสารยังไม่ลงทะเบียนใน tools/registry.json: {missing}"
