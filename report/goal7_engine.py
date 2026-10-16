"""เอ็นจินรายงานเป้าหมาย 7 — ทะเบียนหัวข้อ/คำถามด้วยรหัสคงที่ (key) · เลขอัตโนมัติ · อ้างอิงข้ามฉบับ

หลักการ (docs/REPORT_CONVENTIONS.md §2):
  • หัวข้อ/คำถามทุกข้อมี key คงที่ — ห้ามพิมพ์เลขข้อ/เลขถามเป็น literal ในข้อความ
  • อ้างข้อด้วยโทเคน  ⟦key⟧  (ฉบับเดียวกัน) · ⟦ว:key⟧ (อ้างฉบับวิชาการ) · ⟦ป:key⟧ (อ้างฉบับประชาชน)
    หลายข้อ: ⟦a,b,c⟧ → "ถาม 3, 5, 7" · โทเคนที่ key ไม่มีจริง = สร้างรายงานล้ม (ไม่ปล่อยเลขผิดเงียบ ๆ)
  • ย้าย/รวม/เรียงใหม่ = แก้ลำดับที่เดียว เลขและการอ้างทั้งสองฉบับตามอัตโนมัติ (สร้างรอบสองด้วย goal7_build_all.py)
  • แต่ละฉบับเขียนผังหัวข้อลง analysis/goal7/outline_<ฉบับ>.json ให้อีกฉบับอ่านเพื่อแปลงโทเคนข้ามฉบับ
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTLINE_DIR = ROOT / "analysis/goal7"
TOKEN = re.compile(r"⟦([^⟧]+)⟧")
PENDING = "(เลขอ้างอิงจะปรากฏหลังสร้างรอบสอง)"
_EDITION = {"ป": ("public", "ฉบับประชาชน"), "ว": ("academic", "ฉบับวิชาการ")}
# ตัวอย่างหน้าพับได้ — ใส่ใน <style> ของหน้า (สีผ่านเกณฑ์ WCAG: ตัวอักษร ≥ 4.5)
COLLAPSE_CSS = (
    "details.qd{border:1px solid #b9c6d2;border-radius:8px;padding:4px 16px;margin:12px 0;background:#fff}"
    "details.qd>summary{cursor:pointer;font-weight:700;font-size:1.05em;color:#1c2b33;padding:8px 0}"
    "details.qd[open]>summary{border-bottom:1px solid #dbe3ea;margin-bottom:10px}"
    ".qctl button{background:#1d6fb8;color:#fff;border:0;border-radius:6px;padding:6px 14px;margin-right:8px;font-size:.95em;cursor:pointer}"
)
COLLAPSE_BUTTONS = (
    "<p class='qctl'><button type='button' onclick=\"document.querySelectorAll('details.qd').forEach(function(d){d.open=true})\">ขยายทุกข้อ</button> "
    "<button type='button' onclick=\"document.querySelectorAll('details.qd').forEach(function(d){d.open=false})\">ย่อทุกข้อ</button></p>"
)


import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from goal6_reportlib import esc as _esc  # noqa: E402


class Outline:
    """ทะเบียนหัวข้อของหนึ่งฉบับ ("ป" ประชาชน | "ว" วิชาการ)"""

    def __init__(self, edition: str):
        assert edition in _EDITION
        self.ed = edition
        self.items: dict[str, dict] = {}
        self.order: list[str] = []
        self.alias: dict[str, str] = {}
        self._h2 = 0
        self._h3 = 0
        self._other = self._load("ว" if edition == "ป" else "ป")

    # ---- ไฟล์ผังหัวข้อ ----
    @staticmethod
    def _path(ed: str) -> Path:
        return OUTLINE_DIR / f"outline_{_EDITION[ed][0]}.json"

    def _load(self, ed: str) -> dict:
        p = self._path(ed)
        if not p.exists():
            return {}
        return {i["key"]: i for i in json.loads(p.read_text(encoding="utf-8"))["items"]}

    def save(self) -> Path:
        p = self._path(self.ed)
        data = {"edition": _EDITION[self.ed][0],
                "items": [self.items[k] for k in self.order],
                "alias": self.alias}
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return p

    # ---- ลงทะเบียน ----
    def _add(self, key: str, kind: str, number: str, title: str, anchor: str | None = None) -> None:
        if key in self.items:
            raise ValueError(f"key ซ้ำ: {key}")
        self.items[key] = {"key": key, "kind": kind, "number": number, "title": re.sub(r"<[^>]+>", "", title), "anchor": anchor}
        self.order.append(key)

    def h2(self, key: str, title: str, anchor: str | None = None, numbered: bool = True) -> str:
        if numbered:
            self._h2 += 1
            self._h3 = 0
            num, text = str(self._h2), f"{self._h2}. {title}"
        else:
            num, text = "", title
        self._add(key, "h2", num, title, anchor)
        a = f' id="{anchor}"' if anchor else ""
        return f"<h2{a}>{_esc(text)}</h2>"

    def h3(self, key: str, title: str) -> str:
        self._h3 += 1
        num = f"{self._h2}.{self._h3}"
        self._add(key, "h3", num, title)
        return f"<h3>{num} {_esc(title)}</h3>"

    def question(self, key: str, number: int, title: str, alias_of: list[str] | None = None) -> None:
        self._add(key, "q", str(number), title)
        for a in alias_of or []:
            self.alias[a] = key

    def toc_items(self) -> list[tuple[str, str]]:
        out = []
        for k in self.order:
            it = self.items[k]
            if it["kind"] == "h2":
                if it.get("anchor"):
                    out.append((f"{it['number']}. {it['title']}" if it["number"] else it["title"], it["anchor"]))
        return out

    # ---- แปลงโทเคน ----
    def _lookup(self, key: str, other: bool):
        pool = self._other if other else self.items
        if not other and key in self.alias:
            key = self.alias[key]
        if key in pool:
            return pool[key]
        if other and key in {a for a in self._other_alias()}:
            return pool[self._other_alias()[key]]
        return None

    def _other_alias(self) -> dict:
        p = self._path("ว" if self.ed == "ป" else "ป")
        return json.loads(p.read_text(encoding="utf-8")).get("alias", {}) if p.exists() else {}

    def resolve(self, html: str) -> str:
        missing: list[str] = []

        def rep(m: re.Match) -> str:
            body = m.group(1)
            other = False
            if body[:2] in ("ว:", "ป:"):
                tgt, body = body[0], body[2:]
                if tgt == self.ed:
                    pass
                else:
                    other = True
            keys = [k.strip() for k in body.split(",")]
            its = []
            for k in keys:
                it = self._lookup(k, other)
                if it is None:
                    if other:   # ผังของอีกฉบับยังไม่มี/ยังไม่มี key นี้ — รอบสองจะเติมให้ (goal7_build_all.py ตรวจว่าไม่เหลือ)
                        return PENDING
                    missing.append(k)
                    continue
                its.append(it)
            if not its:
                return ""
            seen, nums = set(), []
            for it in its:
                if it["number"] not in seen:
                    seen.add(it["number"])
                    nums.append(it)
            nums.sort(key=lambda i: [int(x) for x in i["number"].split(".") if x.isdigit()])
            kind = nums[0]["kind"]
            lead = "ถาม " if kind == "q" else "ข้อ "
            txt = lead + ", ".join(i["number"] for i in nums)
            if other:
                txt = _EDITION["ว" if self.ed == "ป" else "ป"][1] + " " + txt
            return txt

        out = TOKEN.sub(rep, html)
        if missing:
            raise ValueError(f"โทเคนอ้างอิงไม่พบ key: {sorted(set(missing))} — แก้ key หรือเพิ่มหัวข้อก่อนสร้างรายงาน")
        return out


def details(number: int, title: str, body_html: str, open_: bool = False) -> str:
    """คำถามพับได้ (แบบเดียวกับรายงาน 1) — เปิดไว้ตั้งต้นเฉพาะข้อสำคัญ"""
    op = " open" if open_ else ""
    return f"<details class='qd'{op}><summary>ถาม {number}: {title}</summary>{body_html}</details>"
