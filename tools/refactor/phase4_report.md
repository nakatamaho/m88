# Phase 4 Inventory Report

Recorded for `refactor-instructions.md` Phase 4.

## Scope

- Inventory only.
- No files deleted.
- No project files edited.
- No source code, resource, encoding, or build-system changes performed.

## Commands

```sh
git status --short
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase4_inventory.json
rg -n "config2|critsectos2|drawdds_|instthnk|lz77d|writetag|juliet|m88dev|memo\\.txt" . -g '!cdif/debug/**' -g '!diskdrv/debug/**'
```

## Summary

- Include case mismatch count remains `0`.
- `M88_2008.vcproj` missing references remain `4`.
- Immediate deletion candidates without approval: `0`.
- Possible cleanup candidates needing explicit approval: `3`.
- Maintain / do not delete candidates: `3` groups.

## Possible Cleanup Candidates

These appear unreferenced by normal source includes and project build lists. Do not delete without explicit approval.

### `src/pc88/config2.h`

- Observed references:
  - `refactor-instructions.md`
  - `tools/refactor/phase0_manifest.json`
- Not included by tracked source files.
- Not listed in `M88_2008.vcproj` or `M88.dsp`.
- Notes:
  - Appears to be an unfinished or alternate config declaration table using `DECLARE_CONFIG_*` macros.
  - Contains settings that overlap important runtime behavior, including sound, display, keyboard, snapshot compression, and reset behavior.
- Recommendation:
  - Keep for now unless a maintainer confirms it has no historical or design value.

### `src/win32/critsectos2.h`

- Observed references:
  - `refactor-instructions.md`
  - `tools/refactor/phase0_manifest.json`
- Not included by tracked source files.
- Not listed in `M88_2008.vcproj` or `M88.dsp`.
- Notes:
  - OS/2 implementation of `CriticalSection`.
  - Not relevant to current Windows build.
- Recommendation:
  - Possible future deletion candidate, but only after explicit approval.

### `src/win32/drawdds_.h`

- Observed references:
  - `refactor-instructions.md`
  - `tools/refactor/phase0_manifest.json`
- Not included by tracked source files.
- Not listed in `M88_2008.vcproj` or `M88.dsp`.
- Notes:
  - Looks like an older DirectDraw fullscreen driver header.
  - Name overlaps conceptually with `DrawDDS.*`, but it is not the active header after Phase 2a.
- Recommendation:
  - Possible future deletion candidate, but only after explicit approval.

## Maintain / Do Not Delete

### `src/common/lz77d.cpp` and `src/common/lz77d.h`

- Observed references:
  - `M88_2008.vcproj`
  - `M88.dsp`
  - self include from `src/common/lz77d.cpp`
  - `refactor-instructions.md`
  - `tools/refactor/phase0_manifest.json`
- Notes:
  - Contrary to the earlier debt note, these files are listed in the VS2008 and VC6 project files.
  - They are compiled as part of the current project definitions even if no higher-level code references their API.
  - They may relate to historical compression or old snapshot compatibility.
- Recommendation:
  - Do not delete in Phase 4.
  - If cleanup is desired later, first confirm whether removing them changes project builds or historical snapshot support.

### `src/win32/instthnk.cpp` and `src/win32/instthnk.h`

- Observed references:
  - `M88.dsp`
  - `cdif/cdif.dsp`
  - `sample2/sample2.dsp`
  - `sample2/src/config.h`
  - self include from `src/win32/instthnk.cpp`
  - `refactor-instructions.md`
  - `tools/refactor/phase0_manifest.json`
- Notes:
  - Not listed in `M88_2008.vcproj`, but still referenced by legacy VC6 project files and sample/module code.
  - `sample2/src/config.h` uses `InstanceThunk`.
- Recommendation:
  - Do not delete.
  - Treat as legacy/plugin-support code unless the sample and VC6 project files are formally retired.

### `writetag.cpp`

- Observed references:
  - `M88_2008.vcproj` post-build command: `writetag release\m88.exe`
  - `M88.dsp` post-build command: `writetag release\m88.exe`
  - `docs/verification.md`
  - `tools/refactor/phase2a_verification.md`
  - `refactor-instructions.md`
- Notes:
  - Required helper for current Release post-build flow.
  - Recently used successfully in `Release|Win32` verification.
- Recommendation:
  - Do not delete.

## Missing Project References

These are referenced by `M88_2008.vcproj` but are not present on disk.

### `src/win32/romeo/juliet.cpp`

- Referenced by:
  - `M88_2008.vcproj`
  - `M88.dsp`
- `M88_2008.vcproj` marks it `ExcludedFromBuild="true"` for Release, Debug, and Tuning on both Win32 and x64.
- `M88.dsp` marks it excluded from build.
- Related source note:
  - `src/pc88/opnif.cpp` has a commented include for `romeo/juliet.h`.
- Recommendation:
  - Do not create a stub.
  - Ask whether to remove the stale project reference or keep it as historical ROMEO/JULIET documentation.

### `src/win32/romeo/juliet.h`

- Referenced by:
  - `M88_2008.vcproj`
  - `M88.dsp`
- Missing on disk.
- Header entry itself is not compiled, but stale references confuse inventory.
- Recommendation:
  - Ask whether to remove the stale project reference or keep it as historical.

### `m88dev.html`

- Referenced by:
  - `M88_2008.vcproj`
  - `M88.dsp`
- Missing on disk.
- Recommendation:
  - Ask whether this historical document should be restored from upstream/source archives or removed from project references.

### `memo.txt`

- Referenced by:
  - `M88_2008.vcproj`
  - `M88.dsp`
- Missing on disk.
- Recommendation:
  - Ask whether this historical document should be restored from upstream/source archives or removed from project references.

## Recommendation

- Do not delete anything in Phase 4 yet.
- Keep `lz77d`, `instthnk`, and `writetag`.
- Treat `config2.h`, `critsectos2.h`, and `drawdds_.h` as possible cleanup candidates only after maintainer approval.
- Decide separately whether missing project references should be removed, restored, or left as historical references.

## Workspace Notes

- Generated build output directories observed and intentionally not committed:
  - `cdif/debug/`
  - `diskdrv/debug/`
