#!/usr/bin/env python3
"""Phase 2b filename-case inventory.

This script is read-only except for the JSON path supplied with --output. It
does not rename files. It classifies tracked paths with uppercase characters
and records simple references from includes and Visual Studio project files.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path, PureWindowsPath


INCLUDE_RE = re.compile(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", re.MULTILINE)
VCPROJ_RE = re.compile(r'RelativePath="([^"]+)"')
DSP_RE = re.compile(r"^SOURCE=(.+)$", re.MULTILINE)
RC_ASSET_RE = re.compile(r"^\s*\w+\s+(?:ICON|BITMAP)\s+\"([^\"]+)\"", re.MULTILINE)


def git_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return [root / line for line in result.stdout.splitlines() if line]


def read_text_lossy(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "cp932", "latin1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin1", errors="replace")


def has_upper(path: str) -> bool:
    return any("A" <= ch <= "Z" for ch in path)


def normalize_ref(root: Path, owner: Path, value: str) -> str:
    value = value.strip().strip('"').replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    path = PureWindowsPath(value)
    joined = (owner.parent / Path(*path.parts)).resolve()
    try:
        return joined.relative_to(root).as_posix()
    except ValueError:
        return (owner.parent / value).as_posix()


def case_map(paths: list[Path], root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix().lower(): p.relative_to(root).as_posix() for p in paths}


def reason_for(path: str) -> tuple[str, str]:
    basename = Path(path).name
    suffix = Path(path).suffix.lower()
    if path in {"AGENTS.md", "README.md", "HISTORY.TXT", "M88.dsp", "M88.dsw", "M88_2008.sln", "M88_2008.vcproj"}:
        return "keep", "root project/document name; historical or tool-facing"
    if path.endswith("_2008.vcproj"):
        return "keep", "Visual Studio 2008 project name"
    if path.startswith("src/devices/Z80"):
        return "keep", "Z80 engine/debug/test naming is historical and domain-specific"
    if path in {"src/win32/M88.rc", "src/win32/M88.ico"}:
        return "keep", "product/resource file name"
    if path.startswith("src/win32/Draw"):
        return "keep", "Win32 draw driver class/file naming"
    if path.startswith("src/win32/Win"):
        return "keep", "Win32 interface class/file naming"
    if basename == "CritSect.h":
        return "keep", "Win32 CriticalSection wrapper name used across code"
    if suffix in {".rc", ".ico", ".bmp"}:
        return "keep", "resource or asset name"
    return "possible_rename_candidate", "uppercase present; no immediate portability need after Phase 2a"


def collect_references(paths: list[Path], root: Path) -> dict[str, list[dict[str, object]]]:
    actual = case_map(paths, root)
    refs: dict[str, list[dict[str, object]]] = defaultdict(list)
    search_dirs = ["src/common", "src/pc88", "src/devices", "src/win32", "src/if"]

    for owner in paths:
        rel_owner = owner.relative_to(root).as_posix()
        suffix = owner.suffix.lower()
        if suffix not in {".c", ".cpp", ".h", ".hpp", ".rc", ".vcproj", ".dsp"}:
            continue
        text = read_text_lossy(owner)
        if suffix in {".c", ".cpp", ".h", ".hpp", ".rc"}:
            for match in INCLUDE_RE.finditer(text):
                inc = match.group(1)
                candidates = [(owner.parent / inc.replace("\\", "/")).relative_to(root).as_posix()]
                if "/" not in inc and "\\" not in inc:
                    candidates += [f"{d}/{inc}" for d in search_dirs]
                for cand in candidates:
                    target = actual.get(cand.lower())
                    if target:
                        refs[target].append({"from": rel_owner, "kind": "include", "line": text.count("\n", 0, match.start()) + 1, "spelling": inc})
                        break
        if suffix == ".vcproj":
            for match in VCPROJ_RE.finditer(text):
                target = actual.get(normalize_ref(root, owner, match.group(1)).lower())
                if target:
                    refs[target].append({"from": rel_owner, "kind": "vcproj", "line": text.count("\n", 0, match.start()) + 1, "spelling": match.group(1)})
        if suffix == ".dsp":
            for match in DSP_RE.finditer(text):
                target = actual.get(normalize_ref(root, owner, match.group(1)).lower())
                if target:
                    refs[target].append({"from": rel_owner, "kind": "dsp", "line": text.count("\n", 0, match.start()) + 1, "spelling": match.group(1)})
        if suffix == ".rc":
            for match in RC_ASSET_RE.finditer(text):
                target = actual.get(normalize_ref(root, owner, match.group(1)).lower())
                if target:
                    refs[target].append({"from": rel_owner, "kind": "rc_asset", "line": text.count("\n", 0, match.start()) + 1, "spelling": match.group(1)})
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="tools/refactor/phase2b_inventory.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = git_files(root)
    refs = collect_references(paths, root)
    uppercase_paths = []
    for p in paths:
        rel = p.relative_to(root).as_posix()
        if has_upper(rel):
            decision, reason = reason_for(rel)
            uppercase_paths.append(
                {
                    "path": rel,
                    "decision": decision,
                    "reason": reason,
                    "reference_count": len(refs.get(rel, [])),
                    "references": refs.get(rel, []),
                }
            )

    manifest = {
        "phase": "2b-inventory",
        "generated_by": "tools/refactor/phase2b_inventory.py",
        "scope": "inventory only; no rename performed",
        "summary": {
            "tracked_files": len(paths),
            "uppercase_path_count": len(uppercase_paths),
            "keep_count": sum(1 for item in uppercase_paths if item["decision"] == "keep"),
            "possible_rename_candidate_count": sum(1 for item in uppercase_paths if item["decision"] == "possible_rename_candidate"),
        },
        "uppercase_paths": uppercase_paths,
    }
    out = root / args.output
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
