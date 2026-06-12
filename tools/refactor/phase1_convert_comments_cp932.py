#!/usr/bin/env python3
"""Convert Phase 1 comments-only CP932 files to UTF-8.

Selection is driven by the Phase 0 manifest. The script excludes files that
Phase 1 explicitly must not touch and records both converted and excluded
files in a manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXCLUDED_SUFFIXES = {".asm", ".dsp", ".dsw", ".rc"}
HISTORICAL_PATHS = {
    "HISTORY.TXT",
    "readme.txt",
    "src/devices/readme.txt",
    "writetag.cpp",
}
EXTERNAL_PREFIXES = (
    "src/devices/fmgen",
    "src/devices/fmtimer",
    "src/devices/opm.",
    "src/devices/opna.",
    "src/devices/psg.",
)
EXTERNAL_PATHS = {
    "src/win32/romeo/c86ctl.h",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def newline_style(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    cr = data.count(b"\r") - crlf
    if crlf and not lf and not cr:
        return "CRLF"
    if lf and not crlf and not cr:
        return "LF"
    if cr and not crlf and not lf:
        return "CR"
    if not crlf and not lf and not cr:
        return "none"
    return "mixed"


def exclusion_reason(path: str) -> str | None:
    suffix = Path(path).suffix.lower()
    if suffix in EXCLUDED_SUFFIXES:
        return f"excluded suffix {suffix}"
    if path in HISTORICAL_PATHS:
        return "historical/peripheral asset excluded by Phase 1 scope"
    if path in EXTERNAL_PATHS or path.startswith(EXTERNAL_PREFIXES):
        return "external-origin risk excluded by Stop And Ask conditions"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--phase0", default="tools/refactor/phase0_manifest.json")
    parser.add_argument("--output", default="tools/refactor/phase1_manifest.json")
    parser.add_argument("--apply", action="store_true", help="write converted files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    phase0 = json.loads((root / args.phase0).read_text(encoding="utf-8"))
    converted = []
    excluded = []
    candidates = []

    for entry in phase0["files"]:
        path = entry["path"]
        non_ascii = entry.get("non_ascii") or {}
        if entry["classification"] == "CP932" and non_ascii.get("category") == "comments_only":
            reason = exclusion_reason(path)
            if reason:
                excluded.append({"path": path, "reason": reason})
            else:
                candidates.append(path)

    for rel in candidates:
        path = root / rel
        before = path.read_bytes()
        text = before.decode("cp932")
        after = text.encode("utf-8")
        record = {
            "path": rel,
            "before_encoding": "CP932",
            "after_encoding": "UTF-8",
            "unicode_sha256": sha256(text.encode("utf-8")),
            "before_sha256": sha256(before),
            "after_sha256": sha256(after),
            "before_newline": newline_style(before),
            "after_newline": newline_style(after),
            "nul_count": before.count(b"\x00"),
        }
        if args.apply:
            path.write_bytes(after)
        converted.append(record)

    manifest = {
        "phase": 1,
        "generated_by": "tools/refactor/phase1_convert_comments_cp932.py",
        "mode": "apply" if args.apply else "dry-run",
        "selection": {
            "source": args.phase0,
            "criteria": "CP932 files classified as comments_only in Phase 0",
            "excluded_suffixes": sorted(EXCLUDED_SUFFIXES),
            "historical_paths": sorted(HISTORICAL_PATHS),
            "external_paths": sorted(EXTERNAL_PATHS),
            "external_prefixes": sorted(EXTERNAL_PREFIXES),
        },
        "summary": {
            "converted_count": len(converted),
            "excluded_count": len(excluded),
        },
        "converted": converted,
        "excluded": sorted(excluded, key=lambda item: item["path"]),
    }
    (root / args.output).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
