# Phase 2b Inventory Report

Recorded for `refactor-instructions.md` Phase 2b.

## Scope

- Inventory only.
- No file rename performed.
- No include, project, resource, encoding, or build-system changes performed.
- Existing Phase 2a state remains: include case mismatch count is `0`.

## Commands

```sh
python3 tools/refactor/phase2b_inventory.py --root . --output tools/refactor/phase2b_inventory.json
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase2b_inventory.json
```

## Summary

- Tracked files: `296`.
- Paths containing uppercase letters: `30`.
- Keep candidates: `30`.
- Rename candidates: `0`.
- Include case mismatch count: `0`.
- vcproj path case mismatches remain: `48` (out of Phase 2b inventory-only scope).
- vcproj missing references remain: `4` (out of Phase 2b inventory-only scope).

## Keep Candidates

### Root Project And Documents

These names are tool-facing, historical, or conventional and should not be renamed without a stronger reason:

- `AGENTS.md`
- `HISTORY.TXT`
- `M88.dsp`
- `M88.dsw`
- `M88_2008.sln`
- `M88_2008.vcproj`
- `README.md`

### Z80 Engine / Debug / Test Files

These names are domain-specific and historical. They are referenced by source and project files, and Phase 2a already fixed include spelling where needed:

- `src/devices/Z80.h`
- `src/devices/Z80Debug.cpp`
- `src/devices/Z80Debug.h`
- `src/devices/Z80Test.cpp`
- `src/devices/Z80Test.h`
- `src/devices/Z80_x86.cpp`
- `src/devices/Z80_x86.h`
- `src/devices/Z80c.cpp`
- `src/devices/Z80c.h`
- `src/devices/Z80diag.h`

### Win32 Product / Backend Files

These names match product names or Win32 class/backend names and are already referenced with matching case after Phase 2a:

- `src/win32/CritSect.h`
- `src/win32/DrawD2D.cpp`
- `src/win32/DrawD2D.h`
- `src/win32/DrawDDS.cpp`
- `src/win32/DrawDDS.h`
- `src/win32/DrawGDI.cpp`
- `src/win32/DrawGDI.h`
- `src/win32/M88.ico`
- `src/win32/M88.rc`
- `src/win32/WinJoy.cpp`
- `src/win32/WinJoy.h`
- `src/win32/WinKeyIF.cpp`
- `src/win32/WinKeyIF.h`

## Rename Candidates

None recommended.

Phase 2a removed the practical portability blocker by making include strings match on-disk filenames. The remaining uppercase paths are either project/document names, product/resource names, or historical/domain-specific source names. Renaming them now would create churn across `.vcproj`, `.dsp`, resource files, and documentation without a clear portability gain.

## Reference Notes

- `src/win32/CritSect.h` has the highest source include fan-out among uppercase Win32 files.
- `src/devices/Z80c.h`, `Z80_x86.h`, and related `Z80*` files are referenced by source and project files.
- `src/win32/M88.rc` and `M88.ico` are product/resource names and should remain stable.
- Full per-file reference data is in `tools/refactor/phase2b_inventory.json`.

## Recommendation

Do not perform Phase 2b renames at this point. Treat Phase 2b as complete for now with "no rename recommended".

If a later build-system migration needs canonical lowercase names, handle each rename individually with explicit approval, two-step case-only rename where applicable, and simultaneous reference updates.

## Workspace Notes

- Generated build output directories observed and intentionally not committed:
  - `cdif/debug/`
  - `diskdrv/debug/`
