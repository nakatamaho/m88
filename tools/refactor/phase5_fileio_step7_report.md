# Phase 5 FileIO Boundary Step 7 Report

## Scope

- Migrate only `src/pc88/diskmgr.h` from `#include "file.h"` to `#include "fileio.h"`.
- Treat this as the D88-focused FileIO include step.
- Do not change D88 read/write logic.
- Do not change `src/win32/file.cpp`.
- Do not change `FileIO` storage, ABI, implementation, or behavior.
- Exclude all `FileFinder` users.

## Baseline

- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke launched M88, ran a game, verified disk access, produced sound, and showed no new warning dialog or crash.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- Replaced `#include "file.h"` with `#include "fileio.h"` in:
  - `src/pc88/diskmgr.h`
- Left these files on `file.h`:
  - `src/win32/ui.cpp` because it uses `FileFinder`.
  - `src/win32/wincore.cpp` because it uses `FileFinder`.
  - `src/win32/file.cpp` because it is the Win32 `FileIO` implementation.

## Files Changed

- `src/pc88/diskmgr.h`

## Commands Run

```sh
git status --short
rg -n "#include \"file\\.h\"|#include \"fileio\\.h\"|FileIO|FileFinder" src/pc88/diskmgr.h src/pc88/diskmgr.cpp src/win32/ui.cpp src/win32/wincore.cpp src/win32/file.cpp
git diff -- src/pc88/diskmgr.h
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/diskmgr.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/diskmgr.cpp
rg -n "#include \"file(io)?\\.h\"|FileFinder|FileIO" src/pc88/diskmgr.h src/pc88/diskmgr.cpp src/win32/ui.cpp src/win32/wincore.cpp src/win32/file.cpp
```

## Results

- `git diff --check`: passed.
- `src/pc88/diskmgr.cpp` MinGW i686 syntax check passed.
- `src/pc88/diskmgr.cpp` MinGW x64 syntax check with `-fpermissive` passed.
- Remaining `file.h` include sites are intentionally limited to:
  - `src/win32/ui.cpp`
  - `src/win32/wincore.cpp`
  - `src/win32/file.cpp`
- User-side VC2008 / VC8 Express `Release|Win32` rebuild: passed.
- User-side post-build `writetag` CRC: passed.
- User-side runtime smoke:
  - M88 launched successfully.
  - A D88 game loaded and ran successfully.
  - Disk access reached a normal in-game access point.
  - Sound output worked.
  - No new warning dialog or crash appeared.
  - D88 format handling was OK.

## Behavior Preservation Notes

- Only one include directive changed.
- `FileIO` method declarations, enum values, private members, and implementation are unchanged.
- D88 image open/read/write/flush logic is unchanged.
- `FileFinder` remains Win32-only behind `src/win32/file.h`.
- `src/win32/file.cpp` still includes `file.h`.

## User-Side VC2008 Verification

- `tools\windows\build_vc2008.cmd Release`
- Result: passed.

## Next Step Candidate

- Split `FileFinder` from `src/win32/file.h` in a Win32-only boundary step.
- Keep `src/win32/file.cpp` unchanged until the FileIO storage/implementation split is explicitly designed.
