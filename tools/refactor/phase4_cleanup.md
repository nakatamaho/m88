# Phase 4 Cleanup Record

Recorded after maintainer approval.

## Changes

- Deleted approved cleanup candidates:
  - `src/pc88/config2.h`
  - `src/win32/critsectos2.h`
  - `src/win32/drawdds_.h`
- Removed stale `juliet` project references:
  - `src/win32/romeo/juliet.cpp`
  - `src/win32/romeo/juliet.h`
- Project files updated:
  - `M88_2008.vcproj`
  - `M88.dsp`

## Explicitly Preserved

- `src/common/lz77d.cpp`
- `src/common/lz77d.h`
- `src/win32/instthnk.cpp`
- `src/win32/instthnk.h`
- `writetag.cpp`
- Missing historical document references:
  - `m88dev.html`
  - `memo.txt`

## Notes

- The `juliet` source/header files were already absent on disk.
- `src/pc88/opnif.cpp` still contains historical `juliet` text in a commented include and symbol name; runtime code was not changed.
- No source logic, resource string, encoding, or build-system redesign was performed.
