# Phase 5 TimeKeeper Common Placement Step 1 Report

## Scope

- Add `src/common/timekeeper.h`.
- Move only the existing `TimeKeeper` public API declaration to the common header.
- Keep `src/win32/timekeep.h` as a compatibility wrapper.
- Do not change:
  - `src/win32/timekeep.cpp` Windows implementation
  - QPC `LowPart` arithmetic
  - `unit = 100`
  - `TimeKeeper` logic
  - `sequence.h` include
  - `romeo/piccolo.h` include
- Add only necessary project-file header references.

## Baseline

- Pushed commit:
  - `4600149` `Inventory common TimeKeeper placement`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - D88 game
  - disk access
  - sound
  - snapshot save/load
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- Added `src/common/timekeeper.h`.
  - Contains the `TimeKeeper` class declaration.
  - Keeps `unit = 100`.
  - Keeps private fields:
    - `uint32 freq`
    - `uint32 base`
    - `uint32 time`
- Replaced `src/win32/timekeep.h` with a compatibility wrapper:

```cpp
#pragma once

#include "../common/timekeeper.h"
```

- Left `src/win32/timekeep.cpp` unchanged.
- Left `src/win32/sequence.h` unchanged.
- Left `src/win32/romeo/piccolo.h` unchanged.
- Added header references to:
  - `M88_2008.vcproj`
  - `M88.dsp`

## Files Changed

- `src/common/timekeeper.h`
- `src/win32/timekeep.h`
- `M88_2008.vcproj`
- `M88.dsp`

## Commands Run

```sh
git status --short --branch
rg -n "timekeeper\\.h|timekeep\\.h|TimeKeeper|timekeep\\.cpp" src M88_2008.vcproj M88.dsp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/timekeep.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/sequence.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/romeo/piccolo.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/timekeep.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/sequence.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/romeo/piccolo.cpp
```

## Results

- `git diff --check`: passed.
- MinGW i686 syntax checks passed for:
  - `src/win32/timekeep.cpp`
  - `src/win32/sequence.cpp`
  - `src/win32/romeo/piccolo.cpp`
- MinGW x64 syntax checks with `-fpermissive` passed for:
  - `src/win32/timekeep.cpp`
  - `src/win32/sequence.cpp`
  - `src/win32/romeo/piccolo.cpp`

## Behavior Preservation Notes

- `TimeKeeper::unit` remains `100`.
- `TimeKeeper` private fields remain unchanged.
- `src/win32/timekeep.cpp` still includes `"timekeep.h"` and still uses the same Windows implementation.
- QPC `LowPart` arithmetic is unchanged.
- `timeGetTime` fallback is unchanged.
- `timeBeginPeriod(1)` / `timeEndPeriod(1)` behavior is unchanged.
- `Sequencer` and `Piccolo` include paths are unchanged because the wrapper preserves `"timekeep.h"`.

## User-Side VC2008 Verification

- Recommended:
  - `tools\windows\build_vc2008.cmd Release`
  - Confirm post-build `writetag` prints a CRC.
  - Launch M88.
  - Boot a D88 game.
  - Confirm disk access works.
  - Confirm sound output and tempo feel normal.
  - Confirm snapshot save/load.
  - Confirm clean shutdown.
  - Confirm no new warning dialog or crash.
- Build result: not recorded yet for this step.
- Runtime smoke: not recorded yet for this step.

## Next Step Candidate

- After VC2008 verification, optionally replace direct `"timekeep.h"` includes in:
  - `src/win32/sequence.h`
  - `src/win32/romeo/piccolo.h`
- with `"timekeeper.h"` in a separate include-only step.
- Keep `src/win32/timekeep.cpp` on `"timekeep.h"` until the Windows implementation split is explicitly designed.
