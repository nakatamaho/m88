# Phase 5 TimeKeeper Common Placement Step 2 Report

## Scope

- Target only:
  - `src/win32/sequence.h`
  - `src/win32/romeo/piccolo.h`
- Replace only:
  - `#include "timekeep.h"`
  - with `#include "timekeeper.h"`
- Keep:
  - `src/win32/timekeep.cpp` including `"timekeep.h"`
  - `src/win32/timekeep.h` compatibility wrapper
  - TimeKeeper implementation
  - QPC `LowPart`
  - `unit = 100`
  - all logic
  - all project files

## Baseline

- Pushed commit:
  - `0f04fa5` `Move TimeKeeper API to common header`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - D88 game
  - disk access
  - sound
  - snapshot save/load
  - clean shutdown
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- `src/win32/sequence.h`
  - Now includes `timekeeper.h` directly.
- `src/win32/romeo/piccolo.h`
  - Now includes `timekeeper.h` directly.
- Left unchanged:
  - `src/win32/timekeep.cpp`
  - `src/win32/timekeep.h`
  - `src/common/timekeeper.h`
  - `M88_2008.vcproj`
  - `M88.dsp`

## Files Changed

- `src/win32/sequence.h`
- `src/win32/romeo/piccolo.h`

## Commands Run

```sh
git status --short --branch
rg -n "#include \"timekeep\\.h\"|#include \"timekeeper\\.h\"|TimeKeeper" src/win32/sequence.h src/win32/romeo/piccolo.h src/win32/timekeep.cpp src/win32/timekeep.h
git diff -- src/win32/sequence.h src/win32/romeo/piccolo.h src/win32/timekeep.cpp src/win32/timekeep.h M88_2008.vcproj M88.dsp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/sequence.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/romeo/piccolo.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/sequence.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/romeo/piccolo.cpp
```

## Results

- `git diff --check`: passed.
- MinGW i686 syntax checks passed for:
  - `src/win32/sequence.cpp`
  - `src/win32/romeo/piccolo.cpp`
- MinGW x64 syntax checks with `-fpermissive` passed for:
  - `src/win32/sequence.cpp`
  - `src/win32/romeo/piccolo.cpp`

## Behavior Preservation Notes

- Only include directives changed.
- `src/win32/timekeep.cpp` still includes `"timekeep.h"` and uses the same Windows implementation path.
- `src/win32/timekeep.h` remains a compatibility wrapper.
- `TimeKeeper::unit` remains `100`.
- QPC `LowPart` arithmetic is unchanged.
- `timeGetTime` fallback and `timeBeginPeriod(1)` behavior are unchanged.
- `Sequencer` logic is unchanged.
- `Piccolo` logic is unchanged.
- No project files were changed.

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

- Stop TimeKeeper include cleanup here for now.
- Keep `src/win32/timekeep.h` as a compatibility wrapper until the Windows implementation split is designed.
- Next safe work is an inventory/design step for `Sequencer` placement or the Windows `timekeep.cpp` implementation boundary.
