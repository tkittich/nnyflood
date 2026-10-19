#!/usr/bin/env python3
"""tools/doctor.py — ตรวจทะเบียนเครื่องมือ/สภาพแวดล้อม (tools/registry.json) และสร้างส่วนเครื่องมือของ docs/ENVIRONMENT.md

ตรวจ:
  1. โครงสร้างทะเบียน (ฟิลด์จำเป็น · id ไม่ซ้ำ · สถานะอยู่ในรายการ · superseded_by ชี้ id ที่มีจริง)  → ผิด = ข้อผิดพลาด (รหัสออก 1)
  2. สภาพแวดล้อม: ตัวแปลภาษามีจริง · แพ็กเกจที่ประกาศติดตั้งแล้ว (อ่านเวอร์ชันจาก metadata ไม่ import) · --deep ตรวจ CUDA
  3. เครื่องมือ: ไฟล์มีจริง · อ้างสภาพแวดล้อมที่มี · ผลลัพธ์ที่ระบุเป็นพาธมีอยู่ · มีในเอกสาร (PROJECT_MAP/catalog/…)
  4. ความครอบคลุม: สคริปต์ใน analysis/ tools/ report/ ที่ยังไม่ลงทะเบียน (นับ · --list-unregistered แสดงรายชื่อ)
  5. โฟลเดอร์ data/NN_* ที่ไม่มี manifest.md
  6. ส่วนที่สร้างอัตโนมัติใน docs/ENVIRONMENT.md ตรงกับทะเบียนหรือไม่ (--write-docs เพื่อสร้างใหม่)
คำเตือนทั้งหมด = รหัสออก 2 (verify_all ถือเป็น "ผ่านแบบมีเงื่อนไข") · ไม่แก้ไฟล์ใดนอกจาก --write-docs / --write-probe

ใช้: python tools/doctor.py [--deep] [--list-unregistered] [--write-docs] [--write-probe]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "tools/registry.json"
PROBE = ROOT / "tools/registry_probe.json"
ENV_DOC = ROOT / "docs/ENVIRONMENT.md"
BEGIN = "<!-- BEGIN GENERATED: tool-registry (python tools/doctor.py --write-docs) -->"
END = "<!-- END GENERATED: tool-registry -->"
STATUS_OK = {"active", "superseded", "deprecated", "experimental"}
ENV_REQUIRED = {"id", "label", "interpreter", "kind", "status", "purpose"}
TOOL_REQUIRED = {"id", "path", "env", "status", "purpose", "run"}
DOC_SURFACES = ["docs/PROJECT_MAP.md", "catalog.py", "docs/ENVIRONMENT.md", "README.md", "START_HERE.md"]


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def interpreter_of(env: dict) -> str:
    return sys.executable if env["interpreter"] == "$MAIN" else env["interpreter"]


# ---------- ตรวจโครงสร้าง ----------
def check_schema(reg: dict) -> list[str]:
    errs = []
    env_ids = [e.get("id") for e in reg.get("environments", [])]
    tool_ids = [t.get("id") for t in reg.get("tools", [])]
    for kind, items, req, ids in (("environment", reg.get("environments", []), ENV_REQUIRED, env_ids), ("tool", reg.get("tools", []), TOOL_REQUIRED, tool_ids)):
        for it in items:
            miss = req - set(it)
            if miss:
                errs.append(f"{kind} {it.get('id')}: ขาดฟิลด์ {sorted(miss)}")
            if it.get("status") not in STATUS_OK:
                errs.append(f"{kind} {it.get('id')}: status '{it.get('status')}' ไม่อยู่ในรายการ {sorted(STATUS_OK)}")
            sb = it.get("superseded_by")
            if sb and sb not in ids:
                errs.append(f"{kind} {it.get('id')}: superseded_by '{sb}' ไม่มีในทะเบียน")
            if it.get("status") == "superseded" and not sb:
                errs.append(f"{kind} {it.get('id')}: status superseded ต้องระบุ superseded_by")
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            errs.append(f"{kind}: id ซ้ำ {sorted(dup)}")
    for t in reg.get("tools", []):
        if t.get("env") not in env_ids:
            errs.append(f"tool {t.get('id')}: env '{t.get('env')}' ไม่มีในทะเบียนสภาพแวดล้อม")
    return errs


# ---------- สภาพแวดล้อม ----------
PROBE_CODE = (
    "import json,sys\n"
    "from importlib import metadata as m\n"
    "out={'python':sys.version.split()[0],'packages':{}}\n"
    "for p in __PK__:\n"
    "    try: out['packages'][p]=m.version(p)\n"
    "    except Exception: out['packages'][p]=None\n"
    "if __DEEP__:\n"
    "    try:\n"
    "        import torch; out['cuda']=bool(torch.cuda.is_available()); out['gpu']=torch.cuda.get_device_name(0) if out['cuda'] else None\n"
    "    except Exception as e: out['cuda']=None; out['gpu_error']=str(e)[:80]\n"
    "print(json.dumps(out))\n"
)


def probe_env(env: dict, deep: bool) -> dict:
    interp = interpreter_of(env)
    if env["interpreter"] != "$MAIN" and not Path(interp).exists():
        return {"available": False}
    code = PROBE_CODE.replace("__PK__", repr(env.get("packages", []))).replace("__DEEP__", repr(bool(deep and env.get("kind") == "gpu")))
    try:
        r = subprocess.run([interp, "-c", code], capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace")
        data = json.loads(r.stdout.strip().splitlines()[-1])
        data["available"] = True
        return data
    except Exception as e:  # noqa: BLE001
        return {"available": False, "error": str(e)[:100]}


def check_envs(reg: dict, deep: bool):
    warns, probes = [], {}
    for env in reg["environments"]:
        pr = probe_env(env, deep)
        probes[env["id"]] = pr
        if not pr.get("available"):
            if env["status"] == "active":
                warns.append(f"สภาพแวดล้อม {env['id']} (active) ใช้งานไม่ได้ในเครื่องนี้: {interpreter_of(env)} {pr.get('error', '')}")
            continue
        missing = [p for p, v in pr["packages"].items() if v is None]
        if missing and env["status"] != "deprecated":
            warns.append(f"สภาพแวดล้อม {env['id']}: ไม่พบแพ็กเกจ {missing}")
        if deep and env.get("kind") == "gpu" and not pr.get("cuda"):
            warns.append(f"สภาพแวดล้อม {env['id']}: CUDA ใช้ไม่ได้ ({pr.get('gpu_error', '')})")
    return warns, probes


# ---------- เครื่องมือ ----------
PATHLIKE = re.compile(r"^[\w./\-ก-๙]+\.[A-Za-z0-9]{2,5}$")


def check_tools(reg: dict):
    warns, errs = [], []
    envs = {e["id"]: e for e in reg["environments"]}
    docs_text = {p: (ROOT / p).read_text(encoding="utf-8", errors="ignore") for p in DOC_SURFACES if (ROOT / p).exists()}
    for t in reg["tools"]:
        p = ROOT / t["path"]
        if not p.exists():
            errs.append(f"tool {t['id']}: ไม่พบไฟล์ {t['path']}")
            continue
        if envs.get(t["env"], {}).get("status") == "superseded" and t["status"] == "active":
            warns.append(f"tool {t['id']} (active) ใช้สภาพแวดล้อม {t['env']} ที่ถูกแทนที่แล้ว")
        for o in t.get("outputs", []):
            if PATHLIKE.match(o) and "*" not in o and "<" not in o and not (ROOT / o).exists():
                warns.append(f"tool {t['id']}: ผลลัพธ์ที่ระบุยังไม่มีบนดิสก์ {o}")
        if t["status"] in ("active", "experimental") and not any(t["path"] in txt or Path(t["path"]).name in txt for txt in docs_text.values()):
            warns.append(f"tool {t['id']}: ไม่ปรากฏในเอกสารพื้นผิวใดเลย ({', '.join(DOC_SURFACES[:3])}…)")
    return warns, errs


def unregistered(reg: dict) -> list[str]:
    known = {t["path"] for t in reg["tools"]}
    out = []
    for pat in ("analysis/*.py", "tools/*.py", "report/*.py"):
        for f in sorted(ROOT.glob(pat)):
            rel = f.relative_to(ROOT).as_posix()
            if f.name.startswith("_") or rel in known:
                continue
            out.append(rel)
    return out


def missing_manifests() -> list[str]:
    return [d.name for d in sorted((ROOT / "data").iterdir()) if d.is_dir() and re.match(r"\d\d_", d.name) and not (d / "manifest.md").exists()]


# ---------- เอกสารที่สร้างอัตโนมัติ ----------
def render_section(reg: dict, probes: dict | None) -> str:
    probes = probes or {}
    L = [BEGIN, "", "## ทะเบียนเครื่องมือและสภาพแวดล้อม (สร้างอัตโนมัติจาก `tools/registry.json`)", "",
         "> อย่าแก้ส่วนนี้ด้วยมือ — แก้ `tools/registry.json` แล้วรัน `python tools/doctor.py --write-docs` · ตรวจด้วย `python tools/doctor.py`", "",
         "### สภาพแวดล้อม", "", "| id | ชื่อ | สถานะ | ตัวแปลภาษา | ใช้ทำอะไร | เวอร์ชันที่ตรวจล่าสุด |", "|---|---|---|---|---|---|"]
    for e in reg["environments"]:
        pr = probes.get(e["id"], {})
        ver = "—"
        if pr.get("available"):
            pk = ", ".join(f"{k} {v}" for k, v in sorted(pr.get("packages", {}).items()) if v)
            gpu = f" · GPU {pr['gpu']}" if pr.get("gpu") else ""
            ver = f"Python {pr['python']} · {pk}{gpu}"
        elif pr:
            ver = "ไม่พบในเครื่องที่ตรวจ"
        status = e["status"] + (f" → {e['superseded_by']}" if e.get("superseded_by") else "")
        interp = "`$MAIN` (python ที่รัน doctor)" if e["interpreter"] == "$MAIN" else f"`{e['interpreter']}`"
        L.append(f"| `{e['id']}` | {e['label']} | {status} | {interp} | {e['purpose']}{(' · ' + e['note']) if e.get('note') else ''} | {ver} |")
    L += ["", "### เครื่องมือ/สคริปต์ที่ลงทะเบียน", "", "| id | ไฟล์ | สภาพแวดล้อม | สถานะ | ทำอะไร | รันอย่างไร | ผลิต |", "|---|---|---|---|---|---|---|"]
    for t in reg["tools"]:
        status = t["status"] + (f" → {t['superseded_by']}" if t.get("superseded_by") else "")
        outs = "<br>".join(f"`{o}`" for o in t.get("outputs", [])) or "—"
        L.append(f"| `{t['id']}` | `{t['path']}` | `{t['env']}` | {status} | {t['purpose']} | `{t['run']}` | {outs} |")
    L += ["", f"รวม {len(reg['environments'])} สภาพแวดล้อม · {len(reg['tools'])} เครื่องมือที่ลงทะเบียน (สคริปต์อื่นที่ยังไม่ลงทะเบียนดูด้วย `python tools/doctor.py --list-unregistered`)", "", END]
    return "\n".join(L)


def current_generated(text: str) -> str | None:
    if BEGIN in text and END in text:
        return text[text.index(BEGIN): text.index(END) + len(END)]
    return None


def write_docs(section: str) -> None:
    text = ENV_DOC.read_text(encoding="utf-8")
    cur = current_generated(text)
    if cur is not None:
        text = text.replace(cur, section)
    else:
        marker = "## สิ่งที่ *ไม่* ต้องติดตั้ง"
        assert marker in text, "ไม่พบจุดแทรกใน ENVIRONMENT.md"
        text = text.replace(marker, section + "\n\n" + marker, 1)
    ENV_DOC.write_text(text, encoding="utf-8", newline="")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deep", action="store_true", help="ตรวจ CUDA ในสภาพแวดล้อมชนิด gpu (ช้า ~10–20 วินาที)")
    ap.add_argument("--list-unregistered", action="store_true")
    ap.add_argument("--write-docs", action="store_true")
    ap.add_argument("--write-probe", action="store_true", help="บันทึกเวอร์ชันที่ตรวจได้ลง tools/registry_probe.json")
    a = ap.parse_args()

    reg = load_registry()
    errs = check_schema(reg)
    warns: list[str] = []
    if errs:
        for e in errs:
            print(f"❌ {e}")
        return 1

    w, probes = check_envs(reg, a.deep)
    warns += w
    w2, e2 = check_tools(reg)
    warns += w2
    errs += e2

    stored = json.loads(PROBE.read_text(encoding="utf-8")) if PROBE.exists() else {}
    if a.write_probe or a.write_docs:
        merged = {k: v for k, v in probes.items() if v.get("available")}
        # ไม่ทิ้งผลตรวจเดิมของสภาพแวดล้อมที่เครื่องนี้ไม่พบ
        for k, v in stored.items():
            merged.setdefault(k, v)
        PROBE.write_text(json.dumps(merged, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        stored = merged

    section = render_section(reg, stored)
    if a.write_docs:
        write_docs(section)
        print("✅ เขียนส่วนเครื่องมือใน docs/ENVIRONMENT.md แล้ว")
    else:
        cur = current_generated(ENV_DOC.read_text(encoding="utf-8"))
        if cur != section:
            warns.append("docs/ENVIRONMENT.md ส่วนเครื่องมือไม่ตรงกับทะเบียน — รัน `python tools/doctor.py --write-docs`")

    un = unregistered(reg)
    if un:
        total = len(list(ROOT.glob("analysis/*.py"))) + len(list(ROOT.glob("tools/*.py"))) + len(list(ROOT.glob("report/*.py")))
        warns.append(f"สคริปต์ที่ยังไม่ลงทะเบียน {len(un)} จาก {total} ไฟล์ ({100 * (total - len(un)) // total}% ลงทะเบียนแล้ว)")
        if a.list_unregistered:
            for u in un:
                print(f"   · {u}")
    nm = missing_manifests()
    if nm:
        warns.append(f"โฟลเดอร์ข้อมูลที่ไม่มี manifest.md: {nm}")

    for e in errs:
        print(f"❌ {e}")
    for w_ in warns:
        print(f"⚠️  {w_}")
    if not errs and not warns:
        print("✅ ทะเบียนเครื่องมือสอดคล้องกับเครื่องและเอกสารทั้งหมด")
    return 1 if errs else (2 if warns else 0)


if __name__ == "__main__":
    sys.exit(main())
