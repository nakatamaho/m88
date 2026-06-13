# Phase 5 FileIO Boundary Step 5 Report

## Scope

- Migrate only two additional `FileIO`-only files from `#include "file.h"` to `#include "fileio.h"`.
- Target only:
  - `src/pc88/crtc.cpp`
  - `src/pc88/memory.cpp`
- Exclude `diskmgr.h`, `diskdrv`, `src/win32/file.cpp`, and all `FileFinder` users.
- Do not change `FileIO` storage, ABI, implementation, or behavior.
- Do not change ROM, D88/T88, snapshot, audio, video, timing, or CPU logic.

## Baseline

- `a6949b4` was pushed to `origin/master` before this step.
- Previous user-side VS2008 / VC8 Express `Release|Win32` rebuild passed.
- Previous user-side runtime smoke launched M88, ran a game, produced sound, and showed no new warning dialog or crash.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- Replaced `#include "file.h"` with `#include "fileio.h"` in:
  - `src/pc88/crtc.cpp`
  - `src/pc88/memory.cpp`
- No project-file changes were required because `M88_2008.vcproj` already includes `.\src\common`.
- Left the following on `file.h` for separate steps:
  - `src/pc88/diskmgr.h`
  - `diskdrv/src/diskio.h`
  - `src/win32/ui.cpp`
  - `src/win32/wincore.cpp`
  - `src/win32/file.cpp`

## Files Changed

- `src/pc88/crtc.cpp`
- `src/pc88/memory.cpp`

## Commands Run

```sh
git status --short
git push origin master
rg -n "#include \"file\\.h\"|FileFinder|FileIO" src/pc88/crtc.cpp src/pc88/memory.cpp
git diff -- src/pc88/crtc.cpp src/pc88/memory.cpp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/crtc.cpp src/pc88/memory.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/crtc.cpp src/pc88/memory.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/memory.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/memory.cpp
rg -n "#include \"file(io)?\\.h\"|FileFinder" src/pc88/crtc.cpp src/pc88/memory.cpp src/pc88/diskmgr.h src/win32/ui.cpp src/win32/wincore.cpp diskdrv/src/diskio.h
```

## Results

- Push of previous commit succeeded:
  - `b43c2a8..a6949b4 master -> master`
- `git diff --check`: passed.
- `src/pc88/memory.cpp` MinGW i686 syntax check passed.
- `src/pc88/memory.cpp` MinGW x64 syntax check with `-fpermissive` passed; warnings are the existing pointer-tagging casts in `device_i.h`.
- Combined MinGW syntax check for `crtc.cpp` and `memory.cpp` stopped at the existing `crtc.cpp` `LOG5` argument-count issue:
  - GCC reports this as an error.
  - VS2008 has previously reported this as warning C4003 and continued.
  - This is unrelated to the include migration and was not changed.
- User-side VC2008 / VC8 Express `Release|Win32` rebuild: passed.
- User-side post-build `writetag` CRC: passed.
- User-side runtime smoke:
  - M88 launched successfully.
  - A game loaded and ran successfully.
  - Sound output worked.
  - No new warning dialog or crash appeared.

## Behavior Preservation Notes

- Only include directives changed.
- `FileIO` method declarations, enum values, private members, and implementation are unchanged.
- `src/win32/file.cpp` is unchanged.
- `FileFinder` users remain on `file.h`.
- ROM loading paths touched by these files remain logic-identical:
  - `FONT80SR.ROM`
  - `FONT.ROM`
  - `KANJI1.ROM`
  - `pc88.rom`
  - user-specified ROM file paths through existing `Memory` loaders

## User-Side VC2008 Verification

- `tools\windows\build_vc2008.cmd Release`
- Result: passed.

## Next Step Candidate

- After VC2008 verification, handle either:
  - another small `FileIO`-only group, or
  - a separate `diskdrv/src/diskio.h` step.
- Keep `src/pc88/diskmgr.h` and `FileFinder` users for later isolated steps.
