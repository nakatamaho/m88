# Phase 5 Step 1 Report

Recorded for `refactor-instructions.md` Phase 5 step 1.

## Scope

- Small core PCH boundary step only.
- Added a neutral include header for core/common sources.
- Replaced `headers.h` with `core_headers.h` in three low-risk `src/common` files.
- No logic changes.
- No `types.h` relocation.
- No `FileIO` or `CriticalSection` abstraction.
- No SDL2 implementation.
- Project PCH settings changed only for the three converted files so VS2008 does not require `headers.h` for them.

## Files Changed

- `src/common/core_headers.h`
- `src/common/error.cpp`
- `src/common/lpf.cpp`
- `src/common/lz77d.cpp`
- `M88_2008.vcproj`
- `M88.dsp`

## Change Details

- Added `src/common/core_headers.h`.
  - Includes standard C/C++ headers used by core code.
  - Includes existing `types.h`.
  - Provides a temporary `LONG_PTR` compatibility typedef when Windows headers have not supplied it.
  - Preserves the existing `using namespace std;` behavior from `headers.h` for now.
  - Preserves the existing MSVC `min` / `max` macro compatibility block.
- Replaced:
  - `#include "headers.h"`
- With:
  - `#include "core_headers.h"`
- In:
  - `src/common/error.cpp`
  - `src/common/lpf.cpp`
  - `src/common/lz77d.cpp`
- Disabled precompiled header use for those three files in:
  - `M88_2008.vcproj` (`UsePrecompiledHeader="0"` for Release/Debug/Tuning, Win32/x64)
  - `M88.dsp` (`# SUBTRACT CPP /YX /Yc /Yu`)

## Measured Result

- `src/common` + `src/devices` + `src/pc88` `.cpp` files: `43`.
- Files still including `headers.h`: `40`.
- Files including `core_headers.h`: `3`.
- Include case mismatch count remains `0`.

## Commands

```sh
git status --short
sed -n '1,220p' src/win32/headers.h
sed -n '1,220p' src/common/lpf.cpp
sed -n '1,220p' src/common/lz77d.cpp
sed -n '1,140p' src/common/error.cpp
git diff --check
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_step1_inventory.json
i686-w64-mingw32-g++ -c src/common/lpf.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_lpf.o
i686-w64-mingw32-g++ -c src/common/lz77d.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_lz77d.o
i686-w64-mingw32-g++ -c src/common/error.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_error.o
x86_64-w64-mingw32-g++ -c src/common/lpf.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_lpf_x64.o
x86_64-w64-mingw32-g++ -c src/common/lz77d.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_lz77d_x64.o
x86_64-w64-mingw32-g++ -c src/common/error.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_error_x64.o
```

After the first VS2008 rebuild attempt failed with C1010 because the project still required `headers.h` as a PCH, the project files were updated to disable PCH for only the three converted files.

## Verification

- `git diff --check`: success.
- Phase 0 inventory rerun:
  - include case mismatch count: `0`.
  - vcproj missing references: `2` (`m88dev.html`, `memo.txt`, unchanged by this step).
- MinGW compile-only smoke:
  - `i686-w64-mingw32-g++`: passed for the three changed `.cpp` files.
  - `x86_64-w64-mingw32-g++`: passed for the three changed `.cpp` files.

## Not Verified

- VS2008 / VC8 Express `Release|Win32` build has not been rerun after the per-file PCH setting fix.
- Runtime behavior has not been manually checked after this step.

## Risks / Unknowns

- `core_headers.h` still includes `types.h` from the current include path. `types.h` remains under `src/win32` and still contains Win32-oriented definitions.
- The temporary `LONG_PTR` compatibility typedef is a bridge only. The proper fix is the later `types.h` neutralization step.
- This step intentionally keeps `using namespace std;` and the MSVC `min` / `max` compatibility block to avoid surfacing unrelated changes.

## Recommendation

Run VS2008 / VC8 Express `Release|Win32` rebuild. If it passes, continue expanding this pattern through the remaining low-risk `src/common` files before moving to `src/devices` or `src/pc88`.

## Workspace Notes

- Generated build output directories observed and intentionally not committed:
  - `cdif/debug/`
  - `diskdrv/debug/`
