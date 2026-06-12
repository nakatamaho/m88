# Phase 5 Step 2 Report

Recorded for `refactor-instructions.md` Phase 5 step 2.

## Scope

- Continue the Phase 5 core PCH boundary work in a small step.
- Evaluate remaining `src/common` files that still include `headers.h`.
- Keep Win32 build behavior as the baseline.
- No logic changes.
- No `types.h` relocation.
- No `FileIO` / `CriticalSection` abstraction.
- No plugin ABI abstraction.
- No SDL2 implementation.

## Changes Made

- No source or project file changes were kept.
- A tentative conversion of `device.cpp`, `memmgr.cpp`, and `schedule.cpp` was tested and then backed out because those files depend on `if/ifcommon.h`, which still requires Win32/plugin ABI declarations supplied by the old Win32 PCH path.
- This report records why Phase 5 step 2 should not expand `core_headers.h` further inside `src/common` before the next boundary decision.

## Files Changed

- `tools/refactor/phase5_step2_core_headers.md`

## Candidate Inventory

Remaining `src/common` files still including `headers.h`:

- `src/common/device.cpp`
  - Includes `device.h`.
  - `device.h` includes `if/ifcommon.h`.
  - Blocked by plugin ABI / Win32 type dependency.
- `src/common/memmgr.cpp`
  - Includes `memmgr.h`.
  - `memmgr.h` includes `if/ifcommon.h`.
  - Blocked by plugin ABI / Win32 type dependency.
- `src/common/schedule.cpp`
  - Includes `schedule.h`.
  - `schedule.h` includes `device.h`.
  - `device.h` includes `if/ifcommon.h`.
  - Blocked by plugin ABI / Win32 type dependency.
- `src/common/soundbuf.cpp`
  - Includes `soundbuf.h`.
  - `soundbuf.h` includes `CritSect.h` and `if/ifcommon.h`.
  - Blocked by `CriticalSection` and plugin ABI / Win32 type dependency.
- `src/common/sndbuf2.cpp`
  - Includes `sndbuf2.h`.
  - `sndbuf2.h` includes `CritSect.h` and `if/ifcommon.h`.
  - Blocked by `CriticalSection` and plugin ABI / Win32 type dependency.
- `src/common/srcbuf.cpp`
  - Includes `srcbuf.h`.
  - `srcbuf.h` includes `CritSect.h`.
  - Blocked by `CriticalSection` / Win32 type dependency.

## Commands Run

```sh
git status --short
rg -n "#include \"headers\\.h\"" src/common
sed -n '1,220p' src/common/device.cpp
sed -n '1,220p' src/common/schedule.cpp
sed -n '1,220p' src/common/memmgr.cpp
perl -0pi -e 's/#include "headers\\.h"\\n#pragma hdrstop\\n/#include "core_headers.h"\\n/' src/common/device.cpp
perl -0pi -e 's/#include "headers\\.h"/#include "core_headers.h"/' src/common/schedule.cpp src/common/memmgr.cpp
perl -0pi -e 's/(SOURCE=\\.\\\\src\\\\common\\\\device\\.cpp\\n)(?!# SUBTRACT CPP)/$1# SUBTRACT CPP \\/YX \\/Yc \\/Yu\\n/; s/(SOURCE=\\.\\\\src\\\\common\\\\memmgr\\.cpp\\n)(?!# SUBTRACT CPP)/$1# SUBTRACT CPP \\/YX \\/Yc \\/Yu\\n/; s/(SOURCE=\\.\\\\src\\\\common\\\\schedule\\.cpp\\n)(?!# SUBTRACT CPP)/$1# SUBTRACT CPP \\/YX \\/Yc \\/Yu\\n/' M88.dsp
perl -0pi -e 'for my $name (qw(device memmgr schedule)) { s{(<File\\s+RelativePath="src\\\\common\\\\$name\\.cpp"\\s*>.*?</File>)}{ my $b=$1; $b =~ s/(PreprocessorDefinitions="")/$1\\n\\t\\t\\t\\t\\t\\tUsePrecompiledHeader="0"/g; $b }ges }' M88_2008.vcproj
git diff --check
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_step2_inventory.json
i686-w64-mingw32-g++ -c src/common/device.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_device_step2.o
i686-w64-mingw32-g++ -c src/common/memmgr.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_memmgr_step2.o
i686-w64-mingw32-g++ -c src/common/schedule.cpp -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_schedule_step2.o
i686-w64-mingw32-g++ -c src/common/device.cpp -Isrc -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_device_step2.o
i686-w64-mingw32-g++ -c src/common/memmgr.cpp -Isrc -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_memmgr_step2.o
i686-w64-mingw32-g++ -c src/common/schedule.cpp -Isrc -Isrc/common -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_schedule_step2.o
git diff -- src/common/device.cpp src/common/schedule.cpp src/common/memmgr.cpp M88_2008.vcproj M88.dsp > /tmp/phase5_step2_attempt.diff
git apply -R /tmp/phase5_step2_attempt.diff
rg -n '#include|ifcommon|CritSect|CRITICAL_SECTION|HWND|REFIID|interface' src/common/device.cpp src/common/device.h src/common/memmgr.cpp src/common/memmgr.h src/common/schedule.cpp src/common/schedule.h src/common/soundbuf.cpp src/common/soundbuf.h src/common/sndbuf2.cpp src/common/sndbuf2.h src/common/srcbuf.cpp src/common/srcbuf.h
rg -n "#include \"headers\\.h\"|#include \"core_headers\\.h\"" src/common
```

## Results

- `git diff --check`: success during the tentative patch.
- Phase 0 inventory rerun during the tentative patch:
  - include case mismatch count: `0`.
  - vcproj missing references: `2` (`m88dev.html`, `memo.txt`, unchanged).
- Initial MinGW compile-only smoke failed because the compile command lacked `-Isrc` for `if/ifcommon.h`.
- Retried MinGW compile-only smoke with `-Isrc`; the three tentative files failed on `if/ifcommon.h` declarations:
  - `interface`
  - `REFIID`
  - `HWND`
  - `PROPSHEETPAGE`
  - `UINT`
  - `WPARAM`
  - `LPARAM`
- The tentative conversion was backed out.
- Current `src/common` include state after backout:
  - `core_headers.h`: `3` files (`error.cpp`, `lpf.cpp`, `lz77d.cpp`).
  - `headers.h`: `6` files (`device.cpp`, `memmgr.cpp`, `schedule.cpp`, `soundbuf.cpp`, `sndbuf2.cpp`, `srcbuf.cpp`).

## Behavior Preserved

- No retained source logic changes.
- No retained project build setting changes.
- Existing Windows PCH behavior is preserved for the six remaining `src/common` files.
- The Phase 5 step 1 converted files remain unchanged.

## Risks / Unknowns

- Further `src/common` conversion is blocked by Debt 3 (`CritSect`) and Debt 11 (plugin ABI / Win32 declarations).
- Converting `device.cpp`, `memmgr.cpp`, or `schedule.cpp` safely requires deciding how `if/ifcommon.h` should be made visible without the Win32 PCH.
- Converting `soundbuf.cpp`, `sndbuf2.cpp`, or `srcbuf.cpp` safely requires the `CriticalSection` boundary decision.
- Runtime behavior was not manually checked because no retained runtime code change was made.

## Questions

- Should Phase 5 next address the minimal plugin ABI include boundary for `if/ifcommon.h`, while preserving Windows ABI exactly?
- Or should Phase 5 next address `CriticalSection` include isolation first?

## Recommendation

Do not force more `src/common` files onto `core_headers.h` until one of the two remaining boundaries is approved:

- plugin ABI / Win32 declaration visibility for `if/ifcommon.h`
- `CriticalSection` include isolation
