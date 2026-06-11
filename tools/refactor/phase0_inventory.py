#!/usr/bin/env python3
"""Phase 0 inventory for the m88 refactoring plan.

The script is intentionally read-only except for the manifest path supplied
with --output. It classifies encodings, CP932 non-ASCII locations, include
case mismatches, and Visual Studio project references.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path, PureWindowsPath
from typing import Iterable
from xml.etree import ElementTree


TEXT_SUFFIXES = {
    ".asm",
    ".c",
    ".cpp",
    ".def",
    ".dsp",
    ".dsw",
    ".h",
    ".hpp",
    ".ini",
    ".md",
    ".rc",
    ".sln",
    ".txt",
    ".vcproj",
}

SKIP_DIRS = {".git", "tools/refactor"}
INCLUDE_RE = re.compile(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", re.MULTILINE)
VCPROJ_RE = re.compile(r'RelativePath="([^"]+)"')


def git_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return [root / line for line in result.stdout.splitlines() if line]


def is_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    if not data:
        return False
    control = sum(1 for b in data if b < 32 and b not in (9, 10, 12, 13, 26))
    return control / len(data) > 0.08


def classify_encoding(data: bytes) -> tuple[str, str | None]:
    if is_binary(data):
        return "binary", None
    if all(b < 128 for b in data):
        return "ASCII", data.decode("ascii")
    try:
        return "UTF-8", data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return "CP932", data.decode("cp932")
    except UnicodeDecodeError:
        return "undetermined", None


def mask_comments_and_literals(text: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[tuple[int, int]]]:
    comments: list[tuple[int, int]] = []
    strings: list[tuple[int, int]] = []
    chars: list[tuple[int, int]] = []
    i = 0
    n = len(text)
    state = "code"
    start = 0
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if state == "code":
            if c == "/" and nxt == "/":
                start = i
                i += 2
                state = "line_comment"
                continue
            if c == "/" and nxt == "*":
                start = i
                i += 2
                state = "block_comment"
                continue
            if c == '"':
                start = i
                i += 1
                state = "string"
                continue
            if c == "'":
                start = i
                i += 1
                state = "char"
                continue
            i += 1
            continue
        if state == "line_comment":
            if c == "\n":
                comments.append((start, i))
                state = "code"
            i += 1
            continue
        if state == "block_comment":
            if c == "*" and nxt == "/":
                comments.append((start, i + 2))
                i += 2
                state = "code"
            else:
                i += 1
            continue
        if state in {"string", "char"}:
            if c == "\\":
                i += 2
                continue
            if (state == "string" and c == '"') or (state == "char" and c == "'"):
                (strings if state == "string" else chars).append((start, i + 1))
                i += 1
                state = "code"
            else:
                i += 1
            continue
    if state in {"line_comment", "block_comment"}:
        comments.append((start, n))
    elif state == "string":
        strings.append((start, n))
    elif state == "char":
        chars.append((start, n))
    return comments, strings, chars


def pos_in_ranges(pos: int, ranges: Iterable[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in ranges)


def line_col(text: str, pos: int) -> dict[str, int]:
    line = text.count("\n", 0, pos) + 1
    line_start = text.rfind("\n", 0, pos) + 1
    return {"line": line, "column": pos - line_start + 1}


def classify_non_ascii(path: Path, text: str) -> dict[str, object]:
    positions = [i for i, ch in enumerate(text) if ord(ch) > 127]
    if not positions:
        return {"category": "ascii_only", "samples": []}
    rel = path.as_posix()
    if path.suffix.lower() == ".rc":
        return {
            "category": "resource_or_display_string",
            "samples": [line_col(text, p) for p in positions[:10]],
        }
    comments, strings, chars = mask_comments_and_literals(text)
    macro_positions = []
    other_positions = []
    string_positions = []
    char_positions = []
    comment_positions = []
    for pos in positions:
        if pos_in_ranges(pos, comments):
            comment_positions.append(pos)
        elif pos_in_ranges(pos, strings):
            string_positions.append(pos)
        elif pos_in_ranges(pos, chars):
            char_positions.append(pos)
        else:
            line_start = text.rfind("\n", 0, pos) + 1
            line_end = text.find("\n", pos)
            line = text[line_start : line_end if line_end != -1 else len(text)]
            if line.lstrip().startswith("#"):
                macro_positions.append(pos)
            else:
                other_positions.append(pos)
    if string_positions or char_positions or macro_positions or other_positions:
        parts = []
        if string_positions:
            parts.append("string_literal")
        if char_positions:
            parts.append("char_literal")
        if macro_positions:
            parts.append("macro")
        if other_positions:
            parts.append("other_code")
        category = "+".join(parts)
        sample_positions = string_positions + char_positions + macro_positions + other_positions
    elif comment_positions:
        category = "comments_only"
        sample_positions = comment_positions
    else:
        category = "undetermined"
        sample_positions = positions
    return {
        "category": category,
        "samples": [line_col(text, p) for p in sample_positions[:10]],
        "path_note": rel if category != "comments_only" else None,
    }


def case_map(paths: list[Path], root: Path) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for p in paths:
        rel = p.relative_to(root).as_posix()
        mapping.setdefault(rel.lower(), []).append(rel)
    return mapping


def include_case_mismatches(paths: list[Path], root: Path) -> list[dict[str, object]]:
    mapping = case_map(paths, root)
    mismatches = []
    for p in paths:
        if p.suffix.lower() not in {".c", ".cpp", ".h", ".hpp", ".rc"}:
            continue
        data = p.read_bytes()
        enc, text = classify_encoding(data)
        if text is None:
            continue
        rel_parent = p.parent.relative_to(root)
        for match in INCLUDE_RE.finditer(text):
            inc = match.group(1)
            if inc.startswith("<") or "/" not in inc and "\\" not in inc:
                candidates = [
                    (rel_parent / inc).as_posix(),
                    ("src/common/" + inc),
                    ("src/pc88/" + inc),
                    ("src/devices/" + inc),
                    ("src/win32/" + inc),
                    ("src/if/" + inc),
                ]
            else:
                candidates = [(rel_parent / inc.replace("\\", "/")).as_posix()]
            for cand in candidates:
                actuals = mapping.get(cand.lower())
                if actuals:
                    if cand not in actuals:
                        mismatches.append(
                            {
                                "file": p.relative_to(root).as_posix(),
                                "line": text.count("\n", 0, match.start()) + 1,
                                "include": inc,
                                "resolved_as_written": cand,
                                "actual": actuals,
                            }
                        )
                    break
    return mismatches


def normalize_vcproj_path(root: Path, project: Path, value: str) -> str:
    value = value.replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    path = PureWindowsPath(value)
    joined = (project.parent / Path(*path.parts)).resolve()
    try:
        return joined.relative_to(root).as_posix()
    except ValueError:
        return (project.parent / value).as_posix()


def vcproj_refs(paths: list[Path], root: Path) -> list[dict[str, object]]:
    mapping = case_map(paths, root)
    projects = [p for p in paths if p.suffix.lower() == ".vcproj"]
    refs = []
    for project in projects:
        text = project.read_text(encoding="utf-8", errors="ignore")
        for match in VCPROJ_RE.finditer(text):
            raw = match.group(1)
            if raw.startswith("http:") or raw.startswith("https:"):
                continue
            norm = normalize_vcproj_path(root, project, raw)
            actuals = mapping.get(norm.lower(), [])
            status = "ok" if norm in actuals else "case_mismatch" if actuals else "missing"
            refs.append(
                {
                    "project": project.relative_to(root).as_posix(),
                    "line": text.count("\n", 0, match.start()) + 1,
                    "reference": raw,
                    "normalized": norm,
                    "status": status,
                    "actual": actuals,
                }
            )
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--output", default="tools/refactor/phase0_manifest.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    paths = git_files(root)
    files = []
    encoding_counts: Counter[str] = Counter()
    cp932_location_counts: Counter[str] = Counter()

    for p in paths:
        rel = p.relative_to(root).as_posix()
        data = p.read_bytes()
        enc, text = classify_encoding(data)
        encoding_counts[enc] += 1
        entry: dict[str, object] = {
            "path": rel,
            "suffix": p.suffix,
            "classification": enc,
            "size": len(data),
        }
        if enc == "CP932" and text is not None:
            loc = classify_non_ascii(p.relative_to(root), text)
            entry["non_ascii"] = loc
            cp932_location_counts[str(loc["category"])] += 1
        files.append(entry)

    include_mismatches = include_case_mismatches(paths, root)
    project_refs = vcproj_refs(paths, root)
    manifest = {
        "phase": 0,
        "generated_by": "tools/refactor/phase0_inventory.py",
        "scope": "inventory only; no product source changes",
        "summary": {
            "tracked_files": len(paths),
            "encoding_counts": dict(sorted(encoding_counts.items())),
            "cp932_non_ascii_location_counts": dict(sorted(cp932_location_counts.items())),
            "include_case_mismatch_count": len(include_mismatches),
            "vcproj_reference_counts": dict(Counter(ref["status"] for ref in project_refs)),
        },
        "files": files,
        "include_case_mismatches": include_mismatches,
        "vcproj_references": project_refs,
        "vcproj_missing_references": [ref for ref in project_refs if ref["status"] == "missing"],
        "vcproj_case_mismatches": [ref for ref in project_refs if ref["status"] == "case_mismatch"],
    }
    out = (root / args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
