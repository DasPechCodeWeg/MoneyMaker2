#!/usr/bin/env python3
"""py315ready: will your dependencies install on Python 3.15?

Reads a requirements file (or package names), asks PyPI for the latest
release of each package, and classifies it by its *published files*:

  READY       a wheel that installs on CPython 3.15 exists (pure-Python,
              cp315, or stable-ABI abi3 built for <=3.15)
  NO-WHEEL    binary wheels exist for other Pythons but none for 3.15 ->
              pip falls back to building from source (compiler needed,
              slow CI, frequent failures)
  SDIST-ONLY  no wheels at all, only a source archive
  BLOCKED     the package's Requires-Python excludes 3.15
  ERROR       not found on PyPI / network error

Standard library only. Exit code 1 when anything is BLOCKED or NO-WHEEL
(use --lenient to only fail on BLOCKED), so it can gate CI.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

TARGET = (3, 15)
TARGET_TAG = "cp315"
PYPI = "https://pypi.org/pypi/{}/json"
ORDER = ["BLOCKED", "NO-WHEEL", "SDIST-ONLY", "ERROR", "READY"]


# ----------------------------------------------------------------- tags
def wheel_tags(filename: str):
    """Return (python_tags, abi_tag, platform_tag) of a wheel filename."""
    parts = filename[:-4].split("-")
    if len(parts) < 5:
        return None
    return parts[-3].split("."), parts[-2], parts[-1]


def wheel_verdict(filename: str) -> str | None:
    """'cp315' | 'abi3' | 'pure' | None for one wheel file."""
    tags = wheel_tags(filename)
    if not tags:
        return None
    pys, abi, _plat = tags
    for py in pys:
        if py == TARGET_TAG and abi.startswith(TARGET_TAG):
            return "cp315t" if abi.endswith("t") else "cp315"
    if abi == "abi3":
        for py in pys:
            m = re.fullmatch(r"cp3(\d+)", py)
            if m and int(m.group(1)) <= TARGET[1]:
                return "abi3"
    if abi == "none" and any(p in ("py3", "py2.py3") or p == "py3" or re.fullmatch(r"py3\d*", p) for p in pys):
        m = [re.fullmatch(r"py3(\d+)", p) for p in pys]
        if any(x and int(x.group(1)) > TARGET[1] for x in m):
            return None
        return "pure"
    return None


# ------------------------------------------------ Requires-Python check
def _ver(s: str):
    return tuple(int(x) for x in re.findall(r"\d+", s)[:3])


def _cmp(a, b):
    n = max(len(a), len(b))
    a, b = a + (0,) * (n - len(a)), b + (0,) * (n - len(b))
    return (a > b) - (a < b)


def spec_allows(spec: str | None, target=(3, 15, 0)) -> bool:
    """Minimal PEP 440 specifier check for a CPython version like 3.15.0."""
    if not spec:
        return True
    for clause in spec.split(","):
        clause = clause.strip()
        if not clause:
            continue
        m = re.fullmatch(r"(~=|===|==|!=|<=|>=|<|>)\s*([0-9][0-9.]*)(\.\*)?", clause)
        if not m:
            continue  # unparseable clause: do not block on it
        op, v, star = m.group(1), _ver(m.group(2)), bool(m.group(3))
        if star:
            head = target[: len(v)]
            eq = head == v
            if (op == "==" and not eq) or (op == "!=" and eq):
                return False
            continue
        c = _cmp(target, v)
        ok = {
            ">=": c >= 0, ">": c > 0, "<=": c <= 0, "<": c < 0,
            "==": c == 0, "===": c == 0, "!=": c != 0,
            "~=": c >= 0 and target[: len(v) - 1] == v[: len(v) - 1],
        }[op]
        if not ok:
            return False
    return True


# ---------------------------------------------------------------- PyPI
def fetch(name: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(PYPI.format(name), headers={"User-Agent": "py315ready/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def check(name: str, fetcher=fetch) -> dict:
    row = {"package": name, "version": None, "status": "ERROR", "detail": "", "declares_315": False}
    try:
        data = fetcher(name)
    except urllib.error.HTTPError as e:
        row["detail"] = f"PyPI HTTP {e.code}"
        return row
    except Exception as e:  # network, JSON
        row["detail"] = f"{type(e).__name__}: {e}"
        return row
    info, files = data["info"], data.get("urls", [])
    row["version"] = info.get("version")
    row["declares_315"] = "Programming Language :: Python :: 3.15" in (info.get("classifiers") or [])
    rp = info.get("requires_python")
    wheels = [f["filename"] for f in files if f["filename"].endswith(".whl")]
    kinds = {k for k in (wheel_verdict(w) for w in wheels) if k}
    uploaded = max((f.get("upload_time_iso_8601", "") for f in files), default="")[:10]
    row["uploaded"] = uploaded
    if not spec_allows(rp):
        row["status"], row["detail"] = "BLOCKED", f"Requires-Python {rp!r} excludes 3.15"
    elif kinds:
        row["status"] = "READY"
        row["detail"] = "wheels: " + ", ".join(sorted(kinds))
    elif wheels:
        row["status"] = "NO-WHEEL"
        pys = sorted({p for w in wheels if wheel_tags(w) for p in wheel_tags(w)[0] if re.fullmatch(r"cp3\d+", p)},
                     key=lambda t: int(t[3:]))
        row["detail"] = f"{len(wheels)} binary wheels, newest tags {', '.join(pys[-3:]) or '?'}; 3.15 builds from source"
    elif files:
        row["status"], row["detail"] = "SDIST-ONLY", "no wheels published; installs by building the sdist"
    else:
        row["detail"] = "latest release has no files"
    return row


def read_requirements(path: str) -> list[str]:
    names = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith(("-", "git+", "http")):
                continue
            m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", line)
            if m and m.group(0).lower() not in (n.lower() for n in names):
                names.append(m.group(0))
    return names


def render_md(rows: list[dict]) -> str:
    counts = {s: sum(r["status"] == s for r in rows) for s in ORDER}
    out = [f"# Python 3.15 install readiness ({len(rows)} packages)", "",
           " | ".join(f"**{s}** {counts[s]}" for s in ORDER if counts[s]), "",
           "| Package | Latest | Status | 3.15 classifier | Evidence |",
           "| --- | --- | --- | --- | --- |"]
    for r in sorted(rows, key=lambda r: (ORDER.index(r["status"]), r["package"].lower())):
        out.append(f"| {r['package']} | {r['version'] or '-'} | {r['status']} | "
                   f"{'yes' if r['declares_315'] else 'no'} | {r['detail']} |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("packages", nargs="*", help="package names")
    ap.add_argument("-r", "--requirement", action="append", default=[], help="requirements file")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--lenient", action="store_true", help="fail only on BLOCKED")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args(argv)
    names = list(a.packages)
    for path in a.requirement:
        names += [n for n in read_requirements(path) if n not in names]
    if not names:
        ap.error("give package names or -r requirements.txt")
    with ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(check, names))
    print(json.dumps(rows, indent=2) if a.format == "json" else render_md(rows), end="")
    bad = {"BLOCKED"} if a.lenient else {"BLOCKED", "NO-WHEEL"}
    return 1 if any(r["status"] in bad for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
