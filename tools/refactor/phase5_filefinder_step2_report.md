# Phase 5 FileFinder Boundary Step 2 Report

## Scope

- Change only `src/win32/ui.cpp` and `src/win32/wincore.cpp`.
- Replace `#include "file.h"` with explicit includes:
  - `#include "fileio.h"`
  - `#include "filefinder.h"`
- Do not change `FileFinder` API, implementation, or behavior.
- Do not change `FileIO` API, implementation, storage, or behavior.
- Keep `src/win32/file.cpp` on `file.h`.
- Do not change project files.

## Baseline

- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke launched M88, ran a game, produced sound, snapshot save/load succeeded, and showed no new warning dialog or crash.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- `src/win32/ui.cpp`
  - Replaced `#include "file.h"` with:
    - `#include "fileio.h"`
    - `#include "filefinder.h"`
- `src/win32/wincore.cpp`
  - Replaced `#include "file.h"` with:
    - `#include "fileio.h"`
    - `#include "filefinder.h"`
- Left `src/win32/file.cpp` unchanged.
- No project-file changes were made.

## Files Changed

- `src/win32/ui.cpp`
- `src/win32/wincore.cpp`

## Commands Run

```sh
git status --short
rg -n "#include \"file\\.h\"|#include \"fileio\\.h\"|#include \"filefinder\\.h\"|FileFinder|FileIO" src/win32/ui.cpp src/win32/wincore.cpp src/win32/file.cpp
git diff -- src/win32/ui.cpp src/win32/wincore.cpp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/ui.cpp src/win32/wincore.cpp src/win32/file.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/ui.cpp src/win32/wincore.cpp src/win32/file.cpp
```

## Results

- `git diff --check`: passed.
- `src/win32/ui.cpp`, `src/win32/wincore.cpp`, and `src/win32/file.cpp` MinGW i686 syntax check with `-fpermissive` passed.
- `src/win32/ui.cpp`, `src/win32/wincore.cpp`, and `src/win32/file.cpp` MinGW x64 syntax check with `-fpermissive` passed.
- `src/win32/file.cpp` remains the only checked source still including `file.h`.
- User-side VC2008 / VC8 Express `Release|Win32` rebuild: passed.
- User-side post-build `writetag` CRC: passed.
- User-side runtime smoke:
  - M88 launched successfully.
  - Snapshot save and load both succeeded.
  - A game loaded and ran successfully.
  - Sound output worked.
  - No new warning dialog or crash appeared.
  - `.m88` external module discovery was not checked because no external module was available.

## Behavior Preservation Notes

- Only include directives changed.
- `ui.cpp` still uses the same `FileIO` and `FileFinder` APIs.
- `wincore.cpp` still uses the same `FileIO` and `FileFinder` APIs.
- `FileFinder` snapshot enumeration behavior is unchanged.
- `FileFinder` `.m88` module discovery behavior is unchanged.
- `FileIO` snapshot save/load behavior is unchanged.
- `src/win32/file.cpp` still includes `file.h`.

## User-Side VC2008 Verification

- `tools\windows\build_vc2008.cmd Release`
- Build result: passed.
- Runtime smoke: passed except `.m88` external module discovery, which was not checked because no external module was available.

## Next Step Candidate

- Inventory the remaining `file.h` compatibility wrapper state.
- Keep `src/win32/file.cpp` on `file.h` until the FileIO implementation split is explicitly designed.
