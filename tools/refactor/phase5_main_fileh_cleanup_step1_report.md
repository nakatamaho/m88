# Phase 5 `main.cpp` `file.h` Cleanup Step 1 Report

## Scope

- Target only:
  - `src/win32/main.cpp`
- Remove unused `#include "file.h"`.
- Add explicit `<crtdbg.h>` include for `_CrtSetDbgFlag`.
- Do not change `FileIO`, `FileFinder`, or logic.
- Keep `src/win32/file.cpp` on `file.h`.
- Do not change project files.

## Baseline

- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - game launch
  - sound
  - snapshot save/load
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- `src/win32/main.cpp`
  - Replaced unused `#include "file.h"` with `#include <crtdbg.h>`.
  - Left `_CrtSetDbgFlag(_CRTDBG_ALLOC_MEM_DF | _CRTDBG_LEAK_CHECK_DF)` unchanged.
- `src/win32/file.cpp`
  - Left unchanged and still includes `file.h`.
- No project-file changes were made.

## Files Changed

- `src/win32/main.cpp`

## Commands Run

```sh
git status --short --branch
git diff -- src/win32/main.cpp src/win32/file.cpp M88_2008.vcproj M88.dsp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/main.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/main.cpp
```

## Results

- `git diff --check`: passed.
- `src/win32/main.cpp` MinGW i686 syntax check with `-fpermissive` passed.
- `src/win32/main.cpp` MinGW x64 syntax check with `-fpermissive` passed.
- `src/win32/file.cpp` was not changed.
- `M88_2008.vcproj` and `M88.dsp` were not changed.

## Behavior Preservation Notes

- Only an include dependency was changed.
- `main.cpp` still calls `_CrtSetDbgFlag` exactly as before.
- `main.cpp` does not use `FileIO` or `FileFinder`.
- `file.h` remains as the compatibility wrapper for users that still need both `FileIO` and `FileFinder`.
- `src/win32/file.cpp` remains on `file.h`.

## User-Side VC2008 Verification

- Recommended:
  - `tools\windows\build_vc2008.cmd Release`
  - Confirm post-build `writetag` prints a CRC.
  - Launch M88.
  - Start a game.
  - Confirm sound.
  - Confirm snapshot save/load.
  - Confirm no new warning dialog or crash.
- Build result: not recorded yet for this step.
- Runtime smoke: not recorded yet for this step.

## Next Step Candidate

- Inventory the remaining role of `src/win32/file.h` after this cleanup.
- The expected remaining direct include is `src/win32/file.cpp`; do not delete `file.h` until the wrapper compatibility decision is made.
