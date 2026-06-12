# Phase 5 ifcommon Boundary Report

Recorded for `refactor-instructions.md` Phase 5 after Phase 5 step 2 identified `if/ifcommon.h` as the next blocker.

## Scope

- Add the minimal explicit Win32/plugin ABI include boundary for `if/ifcommon.h`.
- Preserve the existing Windows ABI.
- Convert only the three `src/common` files that were blocked solely by `if/ifcommon.h`.
- Keep Win32 project PCH behavior intact by disabling PCH only for those converted files.
- No logic changes.
- No non-Windows plugin ABI implementation.
- No `CriticalSection` abstraction.
- No SDL2 implementation.

## Changes Made

- Added `src/if/if_platform.h`.
  - Defines the same baseline Win32 targeting macros used by the existing PCH path when they are not already defined.
  - Includes `<windows.h>` and `<commctrl.h>` on `_WIN32`.
  - Provides `interface` as `struct` only when the platform headers did not define it.
- Updated `src/if/ifcommon.h` to include `if_platform.h` before `types.h`.
- Replaced `headers.h` with `core_headers.h` in:
  - `src/common/device.cpp`
  - `src/common/memmgr.cpp`
  - `src/common/schedule.cpp`
- Removed `#pragma hdrstop` from `src/common/device.cpp` because the file no longer uses the Win32 PCH.
- Disabled PCH only for those three files in:
  - `M88_2008.vcproj`
  - `M88.dsp`

## Files Changed

- `src/if/if_platform.h`
- `src/if/ifcommon.h`
- `src/common/device.cpp`
- `src/common/memmgr.cpp`
- `src/common/schedule.cpp`
- `M88_2008.vcproj`
- `M88.dsp`
- `tools/refactor/phase5_ifcommon_boundary.md`

## Commands Run

```sh
git status --short
sed -n '1,280p' src/if/ifcommon.h
sed -n '1,220p' src/win32/headers.h
rg -n "#include \"headers\\.h\"|#include \"core_headers\\.h\"" src/common
git diff --check
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_if_boundary_inventory.json
i686-w64-mingw32-g++ -c src/common/device.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_device_if_boundary.o
i686-w64-mingw32-g++ -c src/common/memmgr.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_memmgr_if_boundary.o
i686-w64-mingw32-g++ -c src/common/schedule.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_schedule_if_boundary.o
x86_64-w64-mingw32-g++ -c src/common/device.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_device_if_boundary_x64.o
x86_64-w64-mingw32-g++ -DNDEBUG -c src/common/device.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_device_if_boundary_x64_ndebug.o
x86_64-w64-mingw32-g++ -DNDEBUG -c src/common/memmgr.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_memmgr_if_boundary_x64_ndebug.o
x86_64-w64-mingw32-g++ -DNDEBUG -c src/common/schedule.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_schedule_if_boundary_x64_ndebug.o
printf '#include "if/ifcommon.h"\nint main(){return 0;}\n' > /tmp/m88_ifcommon_include.cpp
i686-w64-mingw32-g++ -c /tmp/m88_ifcommon_include.cpp -Isrc -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_ifcommon_include.o
x86_64-w64-mingw32-g++ -c /tmp/m88_ifcommon_include.cpp -Isrc -Isrc/win32 -finput-charset=CP932 -o /tmp/m88_ifcommon_include_x64.o
```

## Results

- `git diff --check`: success.
- Phase 0 inventory rerun:
  - include case mismatch count: `0`.
  - vcproj missing references: `2` (`m88dev.html`, `memo.txt`, unchanged).
- `if/ifcommon.h` include-only smoke:
  - `i686-w64-mingw32-g++`: passed.
  - `x86_64-w64-mingw32-g++`: passed.
- Converted file compile-only smoke:
  - `i686-w64-mingw32-g++`: passed for `device.cpp`, `memmgr.cpp`, and `schedule.cpp`.
  - `x86_64-w64-mingw32-g++ -DNDEBUG`: passed for `device.cpp`, `memmgr.cpp`, and `schedule.cpp`.
  - `x86_64-w64-mingw32-g++` without `-DNDEBUG` failed for `device.cpp` because `device_i.h` has existing debug-only `assert(uint(ptr) ...)` pointer truncation casts. This is not changed in this step.
- Current `src/common` include state:
  - `core_headers.h`: `6` files.
  - `headers.h`: `3` files (`soundbuf.cpp`, `sndbuf2.cpp`, `srcbuf.cpp`).

## Behavior Preserved

- Windows ABI calling conventions remain `__stdcall` through the existing `IFCALL` / `IOCALL` macros.
- Existing interface method signatures are unchanged.
- No runtime logic changed.
- No plugin factory or module loading behavior changed.
- Existing Win32 PCH behavior remains for files that still include `headers.h`.

## Not Verified

- VS2008 / VC8 Express `Release|Win32` rebuild has not been run in this environment.
- Runtime behavior has not been manually checked.

## Risks / Unknowns

- `if_platform.h` is intentionally a Win32 ABI boundary, not a portable plugin ABI. Non-Windows plugin support remains undecided.
- `src/common/soundbuf.cpp`, `src/common/sndbuf2.cpp`, and `src/common/srcbuf.cpp` remain blocked by `CritSect.h`.
- The x64 debug-only pointer truncation issue in `device_i.h` remains out of scope.

## Questions

- The next boundary to approve is `CriticalSection` include isolation for the remaining three `src/common` files.
