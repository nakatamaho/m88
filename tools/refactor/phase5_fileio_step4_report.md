# Phase 5 FileIO Boundary Step 4 Report

## Scope

- Migrate only low-risk `FileIO` users from `#include "file.h"` to `#include "fileio.h"`.
- Exclude any file that uses `FileFinder`.
- Do not change `src/win32/file.cpp`.
- Do not change `FileIO` storage, ABI, or behavior.
- Do not change D88/T88/ROM/snapshot/fmgen logic.

## Baseline

- Previous user-side VS2008 / VC8 Express `Release|Win32` rebuild was successful.
- Previous user-side runtime smoke launched M88 and ran a game successfully.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- Replaced `#include "file.h"` with `#include "fileio.h"` in four `FileIO`-only source files:
  - `src/pc88/kanjirom.cpp`
  - `src/pc88/tapemgr.cpp`
  - `src/pc88/subsys.cpp`
  - `src/devices/opna.cpp`
- Left `FileFinder` users on `file.h`:
  - `src/win32/ui.cpp`
  - `src/win32/wincore.cpp`
- Left `src/win32/file.cpp` on `file.h`.
- No project-file changes were required because `M88_2008.vcproj` already includes `.\src\common` and `M88.dsp` already uses the common include path.

## Files Changed

- `src/pc88/kanjirom.cpp`
- `src/pc88/tapemgr.cpp`
- `src/pc88/subsys.cpp`
- `src/devices/opna.cpp`

## Commands Run

```sh
git status --short
rg -n "AdditionalIncludeDirectories|#include \"file\\.h\"|FileFinder|FileIO" M88_2008.vcproj diskdrv/diskdrv_2008.vcproj src/pc88/kanjirom.cpp src/pc88/tapemgr.cpp src/pc88/subsys.cpp src/devices/opna.cpp
git diff -- src/pc88/kanjirom.cpp src/pc88/tapemgr.cpp src/pc88/subsys.cpp src/devices/opna.cpp
rg -n "#include \"file(io)?\\.h\"|FileFinder" src/pc88/kanjirom.cpp src/pc88/tapemgr.cpp src/pc88/subsys.cpp src/devices/opna.cpp src/win32/ui.cpp src/win32/wincore.cpp src/win32/file.cpp diskdrv/src/diskio.h
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/kanjirom.cpp src/pc88/tapemgr.cpp src/pc88/subsys.cpp src/devices/opna.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/kanjirom.cpp src/pc88/tapemgr.cpp src/pc88/subsys.cpp src/devices/opna.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/kanjirom.cpp src/pc88/tapemgr.cpp src/pc88/subsys.cpp src/devices/opna.cpp
```

## Results

- `git diff --check`: passed.
- MinGW i686 syntax check passed for all four changed files.
- MinGW x64 syntax check without `-fpermissive` failed in existing `device_i.h` pointer-to-`uint` assertions while compiling `subsys.cpp`; this is the known x64 pointer tagging issue and is unrelated to the include migration.
- MinGW x64 syntax check with `-fpermissive` passed for all four changed files.
- User-side VS2008 / VC8 Express `Release|Win32` rebuild: passed.
  - Post-build `writetag`: success, `crc = e867e92f`.
- User-side runtime smoke:
  - M88 launched successfully.
  - A game loaded and ran successfully.
  - Sound output worked.
  - No new warning dialog or crash appeared.

## Behavior Preservation Notes

- Only include directives changed.
- `FileIO` method declarations, enum values, private members, and implementation are unchanged.
- `FileFinder` remains Win32-only behind `src/win32/file.h`.
- `src/win32/file.cpp` still includes `file.h`.
- D88/T88/ROM/ADPCM file read code was not modified.

## User-Side VC2008 Verification

- `tools\windows\build_vc2008.cmd Release`
- Result: passed.

## Next Step Candidate

- After VC2008 verification, migrate another small group of `FileIO`-only users.
- Keep `diskdrv/src/diskio.h`, `src/pc88/diskmgr.h`, and `FileFinder` users for separate steps.
