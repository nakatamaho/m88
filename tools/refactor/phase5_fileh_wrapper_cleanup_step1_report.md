# Phase 5 `file.h` Wrapper Cleanup Step 1 Report

## Scope

- Change only:
  - `src/win32/filetest.cpp`
  - `src/win32/memmon.cpp`
- Replace `#include "file.h"` with `#include "fileio.h"`.
- Do not change `FileIO` API, implementation, storage, or behavior.
- Keep `src/win32/file.cpp` on `file.h`.
- Do not change project files.

## Baseline

- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke launched M88, ran a game, produced sound, snapshot save/load succeeded, and showed no new warning dialog or crash.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- `src/win32/filetest.cpp`
  - Replaced `#include "file.h"` with `#include "fileio.h"`.
- `src/win32/memmon.cpp`
  - Replaced `#include "file.h"` with `#include "fileio.h"`.
- Left `src/win32/file.cpp` unchanged.
- No project-file changes were made.

## Files Changed

- `src/win32/filetest.cpp`
- `src/win32/memmon.cpp`

## Commands Run

```sh
git status --short
rg -n "#include \"file\\.h\"|#include \"fileio\\.h\"|FileIO|FileFinder" src/win32/filetest.cpp src/win32/memmon.cpp src/win32/file.cpp
git diff -- src/win32/filetest.cpp src/win32/memmon.cpp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/filetest.cpp src/win32/memmon.cpp src/win32/file.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/filetest.cpp src/win32/memmon.cpp src/win32/file.cpp
```

## Results

- `git diff --check`: passed.
- `src/win32/filetest.cpp`, `src/win32/memmon.cpp`, and `src/win32/file.cpp` MinGW i686 syntax check with `-fpermissive` passed.
- `src/win32/filetest.cpp`, `src/win32/memmon.cpp`, and `src/win32/file.cpp` MinGW x64 syntax check with `-fpermissive` passed.
- x64 warnings are the existing pointer-tagging casts in `device_i.h` while compiling `memmon.cpp`.
- User-side runtime smoke:
  - M88 launched successfully.
  - A game loaded and ran successfully.
  - Sound output worked.
  - Snapshot save and load both succeeded.
  - No new warning dialog or crash appeared.

## Behavior Preservation Notes

- Only include directives changed.
- `filetest.cpp` still uses the same `FileIO` API for the module sanity check.
- `memmon.cpp` still uses the same `FileIO` API for memory monitor save output.
- `src/win32/file.cpp` still includes `file.h`.
- `FileIO` implementation and storage are unchanged.

## User-Side VC2008 Verification

- `tools\windows\build_vc2008.cmd Release`
- Expected result:
  - `diskdrv`: error 0.
  - `cdif`: error 0.
  - `M88`: error 0.
  - Existing warnings only.
  - Post-build `writetag` succeeds and prints a CRC.
- Build result: not recorded yet.
- Runtime smoke: passed.

## Next Step Candidate

- Remove unused `file.h` includes from `src/win32/main.cpp` and `src/win32/iomon.cpp` in a separate small cleanup step.
- Keep `src/win32/file.cpp` on `file.h`.
