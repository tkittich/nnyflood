#!/usr/bin/env python3
"""tools/doctor.py — ตรวจทะเบียนเครื่องมือ/สภาพแวดล้อม (tools/registry.json) และสร้างส่วนเครื่องมือของ docs/ENVIRONMENT.md

ตรวจ:
  1. โครงสร้างทะเบียน (ฟิลด์จำเป็น · id ไม่ซ้ำ · สถานะอยู่ในรายการ · superseded_by ชี้ id ที่มีจริง)  → ผิด = ข้อผิดพลาด (รหัสออก 1)
  2. สภาพแวดล้อม: ตัวแปลภาษามีจริง · แพ็กเกจที่ประกาศติดตั้งแล้ว (อ่านเวอร์ชันจาก metadata ไม่ import) · --deep ตรวจ CUDA
  3. เครื่องมือ: ไฟล์มีจริง · อ้างสภาพแวดล้อมที่มี · ผลลัพธ์ที่ระบุเป็นพาธมีอยู่ · มีในเอกสาร (PROJECT_MAP/catalog/…)
  4. ความครอบคลุม: สคริปต์ใน analysis/ tools/ report/ ที่ยังไม่ลงทะเบียน (นับ · --list-unregistered แสดงรายชื่อ)
  5. โฟลเดอร์ data/NN_* ที่ไม่มี manifest.md
  6. ส่วนที่สร้างอัตโนมัติใน docs/ENVIRONMENT.md ตรงกับทะเบียนหรือไม่ (--write-docs เพื่อสร้างใหม่)
  7. เอกสาร (ส่วน docs ของทะเบียน): ทุก *.md ที่ root และ docs/ ลงทะเบียน · สถานะอยู่ในรายการ · superseded ชี้เอกสารที่มี ·
     เอกสารสถานะ current ที่อ้างไฟล์ที่ไม่มีแล้ว · เอกสาร current ที่ยังลิงก์ไปเอกสาร superseded · ดัชนีเอกสาร docs/DOCS_INDEX.md สร้างอัตโนมัติ
  8. สัญญาหัวไฟล์: สคริปต์ที่ลงทะเบียนต้องมี docstring บรรทัดแรกเป็นคำอธิบายสั้น ๆ (Purpose) และควรมีบรรทัด `รัน:` — ดู AGENTS.md
     สถานะ `unreviewed` = ลงทะเบียนอัตโนมัติจาก docstring แต่คนยังไม่ทบทวน (นับเป็นคำเตือน)
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
DOCS_INDEX = ROOT / "docs/DOCS_INDEX.md"
DOC_STATUS_OK = {"current", "generated", "log", "plan", "historical", "superseded", "needs-review"}
BEGIN = "<!-- BEGIN GENERATED: tool-registry (python tools/doctor.py --write-docs) -->"
END = "<!-- END GENERATED: tool-registry -->"
STATUS_OK = {"active", "superseded", "deprecated", "experimental", "unreviewed"}
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


def check_headers(reg: dict) -> list[str]:
    """สัญญาหัวไฟล์: docstring บรรทัดแรก = คำอธิบาย · สคริปต์ (มี __main__) ควรมีบรรทัด 'รัน:'/'ใช้:'"""
    import ast
    no_doc, no_run = [], []
    for t in reg["tools"]:
        p = ROOT / t["path"]
        if p.suffix != ".py" or not p.exists():
            continue
        src = p.read_text(encoding="utf-8", errors="ignore")
        try:
            doc = ast.get_docstring(ast.parse(src)) or ""
        except SyntaxError:
            doc = ""
        # สคริปต์เก่าที่ห้ามแก้ไฟล์ (เช่น goal4_model_v1.py) ใช้ทะเบียนเป็นหัวไฟล์แทน: purpose + run ที่คนทบทวนแล้ว (ไม่ใช่ unreviewed)
        in_registry = bool(t.get("purpose")) and bool(t.get("run")) and t.get("status") != "unreviewed"
        if not doc.strip():
            if not in_registry:
                no_doc.append(t["path"])
        elif "__main__" in src and not re.search(r"^\s*(รัน|ใช้|Run|Usage)\s*[:：]", doc, re.M):
            if not in_registry:
                no_run.append(t["path"])
    w = []
    if no_doc:
        w.append(f"สัญญาหัวไฟล์: {len(no_doc)} ไฟล์ไม่มี docstring คำอธิบาย (เช่น {', '.join(no_doc[:3])})")
    if no_run:
        w.append(f"สัญญาหัวไฟล์: {len(no_run)} สคริปต์ไม่มีบรรทัด `รัน:` ใน docstring")
    unrev = [t["id"] for t in reg["tools"] if t["status"] == "unreviewed"]
    if unrev:
        w.append(f"ทะเบียน: {len(unrev)} รายการสถานะ unreviewed (ลงทะเบียนอัตโนมัติ รอคนทบทวน)")
    return w


def doc_files() -> list[str]:
    return sorted(f.relative_to(ROOT).as_posix() for f in [*ROOT.glob("*.md"), *(ROOT / "docs").glob("*.md")])


def broken_refs(rel: str) -> list[str]:
    """พาธ/ชื่อสคริปต์ในเครื่องหมาย ` ` ที่ไม่มีอยู่จริง (ข้ามพาธใต้ data/ ที่โฟลเดอร์ระดับบนมีอยู่ — ไฟล์ใหญ่อาจอยู่นอก git)"""
    t = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    out = []
    for r in sorted(set(re.findall(r"`((?:analysis|report|tools|tests|docs|data)/[\w./\-ก-๙]+|[\w\-]+\.py)`", t))):
        if any(c in r for c in "*<>…") or "..." in r or r.endswith("/") and (ROOT / r).exists():
            continue
        if (ROOT / r).exists():
            continue
        if "/" not in r and any((ROOT / d / r).exists() for d in ("analysis", "report", "tools", "tests")):
            continue
        if r.startswith("data/"):
            parts = r.split("/")
            if len(parts) > 1 and (ROOT / "data" / parts[1]).exists():
                continue
            if len(parts) > 1 and re.fullmatch(r"\d\d_?", parts[1]):
                continue   # ตัวแทนพาธย่อ เช่น data/13_
        if r.endswith("/") or re.search(r"\.\w{2,5}$", r):
            out.append(r)
    return out


def check_docs(reg: dict) -> tuple[list[str], list[str]]:
    warns, errs = [], []
    docs = reg.get("docs", [])
    paths = {d["path"] for d in docs}
    for d in docs:
        if d.get("status") not in DOC_STATUS_OK:
            errs.append(f"doc {d['path']}: status '{d.get('status')}' ไม่อยู่ในรายการ")
        if not (ROOT / d["path"]).exists():
            errs.append(f"doc {d['path']}: ไม่พบไฟล์")
        if d.get("status") == "superseded" and d.get("superseded_by") not in paths:
            errs.append(f"doc {d['path']}: superseded ต้องมี superseded_by ที่ลงทะเบียน")
    miss = [p for p in doc_files() if p not in paths and p != "docs/DOCS_INDEX.md"]
    if miss:
        warns.append(f"เอกสารที่ยังไม่ลงทะเบียนใน registry.json: {miss}")
    sup = {d["path"] for d in docs if d.get("status") == "superseded"}
    for d in docs:
        if not (ROOT / d["path"]).exists() or d.get("status") in ("superseded", "historical", "log", "plan"):
            continue
        txt = (ROOT / d["path"]).read_text(encoding="utf-8", errors="ignore")
        for s in sup:
            name = Path(s).name
            occ = [m.start() for m in re.finditer(re.escape(name), txt)]
            if d["path"] != "docs/DOCS_INDEX.md" and any("ถูกแทนที่" not in txt[max(0, i - 160): i + 200] for i in occ):
                warns.append(f"doc {d['path']} (current) ยังอ้าง {Path(s).name} ซึ่งถูกแทนที่แล้ว โดยไม่บอกว่าถูกแทนที่")
        if d["status"] in ("current", "generated"):
            br = broken_refs(d["path"])
            if br:
                warns.append(f"doc {d['path']} อ้างไฟล์ที่ไม่มีแล้ว {len(br)} รายการ (เช่น {', '.join(br[:3])})")
    nr = [d["path"] for d in docs if d["status"] == "needs-review"]
    if nr:
        warns.append(f"เอกสารสถานะ needs-review {len(nr)} ฉบับ: {', '.join(Path(p).name for p in nr)}")
    sys.path.insert(0, str(ROOT))
    import catalog  # noqa: PLC0415  (สารบัญอ่านเอกสารแกนจากทะเบียนนี้ — ตรวจว่าเอกสารที่ลงทะเบียนอยู่ในสารบัญจริง)
    reg_paths = catalog.registered_paths()
    nocat = [d["path"] for d in docs if d["path"] not in reg_paths]
    if nocat:
        warns.append(f"เอกสารในทะเบียนที่ไม่อยู่ในสารบัญ (ตั้ง core=true + desc ใน registry.json หรือใส่ในแผนผังเสา): {nocat}")
    return warns, errs


def render_docs_index(reg: dict) -> str:
    L = ["# ดัชนีเอกสาร (สร้างอัตโนมัติจาก `tools/registry.json`)", "",
         "> อย่าแก้ด้วยมือ — แก้ส่วน `docs` ใน `tools/registry.json` แล้วรัน `python tools/doctor.py --write-docs` · สถานะ: `current` ใช้อ้างได้ · `generated` สร้างจากเครื่องมือ · `log` สมุดบันทึกตามเวลา (ไม่ใช่สถานะปัจจุบัน) · `plan` ความตั้งใจเดิม ไม่ตามแก้ · `historical` บันทึกเก่าเก็บเป็นประวัติ · `superseded` มีฉบับใหม่แทน · `needs-review` สงสัยว่าล้าสมัย รอคนตัดสิน", "",
         "| เอกสาร | สถานะ | ชนิด | หัวเรื่อง | หมายเหตุ |", "|---|---|---|---|---|"]
    order = {"needs-review": 0, "current": 1, "generated": 2, "log": 3, "plan": 4, "historical": 5, "superseded": 6}
    for d in sorted(reg.get("docs", []), key=lambda x: (order.get(x["status"], 9), x["path"])):
        st = d["status"] + (f" → `{d['superseded_by']}`" if d.get("superseded_by") else "")
        L.append(f"| `{d['path']}` | {st} | {d['kind']} | {d['title'].replace('|', '/')} | {d.get('note', '').replace('|', '/')} |")
    L += ["", f"รวม {len(reg.get('docs', []))} เอกสาร", ""]
    return "\n".join(L)


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
    reviewed = [x for x in reg["tools"] if x["status"] != "unreviewed"]
    unrev = [x for x in reg["tools"] if x["status"] == "unreviewed"]
    L += ["", "### เครื่องมือ/สคริปต์ที่ทบทวนแล้ว", "", "| id | ไฟล์ | สภาพแวดล้อม | สถานะ | ทำอะไร | รันอย่างไร | ผลิต |", "|---|---|---|---|---|---|---|"]
    for t_ in reviewed:
        status = t_["status"] + (f" → {t_['superseded_by']}" if t_.get("superseded_by") else "")
        outs = "<br>".join(f"`{o}`" for o in t_.get("outputs", [])) or "—"
        L.append(f"| `{t_['id']}` | `{t_['path']}` | `{t_['env']}` | {status} | {t_['purpose']} | `{t_['run']}` | {outs} |")
    L += ["", f"### ลงทะเบียนอัตโนมัติ รอทบทวน ({len(unrev)} รายการ · สถานะ `unreviewed`)", "",
          "> คำอธิบายมาจาก docstring บรรทัดแรกโดยอัตโนมัติ ยังไม่มีคนยืนยันสถานะ/ผลลัพธ์ — เปลี่ยนสถานะเป็น `active`/`deprecated` เมื่อทบทวนแล้ว", "",
          "| id | ไฟล์ | env | ชนิด | คำอธิบาย (จาก docstring) |", "|---|---|---|---|---|"]
    for t_ in unrev:
        L.append(f"| `{t_['id']}` | `{t_['path']}` | `{t_['env']}` | {t_.get('kind', '')} | {t_['purpose'].replace('|', '/')} |")
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

    if a.write_docs:
        DOCS_INDEX.write_text(render_docs_index(reg), encoding="utf-8", newline="")
    wd, ed = check_docs(reg)
    warns += wd
    errs += ed
    idx = render_docs_index(reg)
    if not a.write_docs and (not DOCS_INDEX.exists() or DOCS_INDEX.read_text(encoding="utf-8") != idx):
        warns.append("docs/DOCS_INDEX.md ไม่ตรงกับทะเบียน — รัน `python tools/doctor.py --write-docs`")
    warns += check_headers(reg)
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
