# Phase 5 `CritSect` Include Boundary Step 1 Report

## Scope

- Add `src/common/core_critsect.h`.
- For Windows builds, make `core_critsect.h` include the existing `src/win32/CritSect.h`.
- Replace only these `src/common` headers:
  - `src/common/soundbuf.h`
  - `src/common/sndbuf2.h`
  - `src/common/srcbuf.h`
- Do not change `CriticalSection` implementation, type name, `Lock` API, logic, or lock scopes.
- Leave `src/pc88/diskmgr.h` and `src/pc88/fdc.cpp` for a later step.
- Add only necessary project-file header references.

## Baseline

- `file.h` cleanup is considered complete for now.
- Pushed commit:
  - `9bbe51e` `Inventory remaining CritSect boundaries`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - game launch
  - sound
  - snapshot save/load
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- Added `src/common/core_critsect.h`.
  - It includes `../win32/CritSect.h`.
  - It does not define a new lock type or implementation.
- Replaced direct `CritSect.h` include with `core_critsect.h` in:
  - `src/common/soundbuf.h`
  - `src/common/sndbuf2.h`
  - `src/common/srcbuf.h`
- Added header references to:
  - `M88_2008.vcproj`
  - `M88.dsp`
- Left unchanged:
  - `src/win32/CritSect.h`
  - `src/pc88/diskmgr.h`
  - `src/pc88/fdc.cpp`
  - all logic and lock scopes

## Files Changed

- `src/common/core_critsect.h`
- `src/common/soundbuf.h`
- `src/common/sndbuf2.h`
- `src/common/srcbuf.h`
- `M88_2008.vcproj`
- `M88.dsp`

## Commands Run

```sh
git status --short --branch
rg -n "core_critsect|#include \"CritSect\\.h\"|#include \"core_critsect\\.h\"" src/common src/pc88 M88_2008.vcproj M88.dsp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -c src/common/soundbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_soundbuf_core_critsect.o
i686-w64-mingw32-g++ -std=gnu++98 -c src/common/sndbuf2.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_sndbuf2_core_critsect.o
i686-w64-mingw32-g++ -std=gnu++98 -c src/common/srcbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_srcbuf_core_critsect.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c src/common/soundbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_soundbuf_core_critsect_x64.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c src/common/sndbuf2.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_sndbuf2_core_critsect_x64.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c src/common/srcbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_srcbuf_core_critsect_x64.o
```

## Results

- `git diff --check`: passed.
- MinGW i686 compile smoke passed for:
  - `src/common/soundbuf.cpp`
  - `src/common/sndbuf2.cpp`
  - `src/common/srcbuf.cpp`
- MinGW x64 compile smoke passed for:
  - `src/common/soundbuf.cpp`
  - `src/common/sndbuf2.cpp`
  - `src/common/srcbuf.cpp`
- `src/pc88/diskmgr.h` still directly includes `CritSect.h`.
- `src/pc88/fdc.cpp` still directly includes `CritSect.h`.

## Behavior Preservation Notes

- `CriticalSection` is still the same class from `src/win32/CritSect.h`.
- Windows `CRITICAL_SECTION` behavior is unchanged.
- `CriticalSection::Lock` behavior is unchanged.
- Sound buffer, resampler, and source-list logic are unchanged.
- Lock scope and call order are unchanged.
- No source file PCH settings were changed in this step.

## User-Side VC2008 Verification

- Recommended:
  - `tools\windows\build_vc2008.cmd Release`
  - Confirm post-build `writetag` prints a CRC.
  - Launch M88.
  - Start a game.
  - Confirm sound output.
  - Confirm snapshot save/load.
  - Confirm no new warning dialog or crash.
- Build result: not recorded yet for this step.
- Runtime smoke: not recorded yet for this step.

## Next Step Candidate

- After VC2008 verification, handle `src/pc88` separately:
  - `src/pc88/diskmgr.h`
  - `src/pc88/fdc.cpp`
- Keep the same rule:
  - include-boundary only
  - no `CriticalSection` implementation change
  - no D88/FDC logic change
  - no lock-scope change
