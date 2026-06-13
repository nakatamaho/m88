# Phase 5 FileIO Boundary Step 6 Report

## Scope

- Migrate only `diskdrv/src/diskio.h` from `#include "file.h"` to `#include "fileio.h"`.
- Limit the change to the `diskdrv` `FileIO` boundary.
- Do not change `src/win32/file.cpp`.
- Do not change `FileIO` storage, ABI, implementation, or behavior.
- Exclude `src/pc88/diskmgr.h` and all `FileFinder` users.

## Baseline

- Previous user-side VC2008 / VC8 Express `Release|Win32` rebuild passed.
- Previous user-side runtime smoke launched M88, ran a game, produced sound, and showed no new warning dialog or crash.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- Replaced `#include "file.h"` with `#include "fileio.h"` in:
  - `diskdrv/src/diskio.h`
- No project-file changes were required:
  - `diskdrv/diskdrv_2008.vcproj` already includes `..\src\common`.
  - `diskdrv/diskdrv.dsp` already uses the existing include setup and the new header is already referenced by the project.

## Files Changed

- `diskdrv/src/diskio.h`

## Commands Run

```sh
git status --short
rg -n "#include \"file\\.h\"|#include \"fileio\\.h\"|FileIO|FileFinder|AdditionalIncludeDirectories" diskdrv/src/diskio.h diskdrv/src/diskio.cpp diskdrv/diskdrv_2008.vcproj diskdrv/diskdrv.dsp
git diff -- diskdrv/src/diskio.h
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Idiskdrv -Idiskdrv/src -Isrc -Isrc/win32 -Isrc/common -Isrc/if diskdrv/src/diskio.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Idiskdrv -Idiskdrv/src -Isrc -Isrc/win32 -Isrc/common -Isrc/if diskdrv/src/diskio.cpp
rg -n "#include \"file(io)?\\.h\"|FileFinder|FileIO" diskdrv/src/diskio.h diskdrv/src/diskio.cpp src/pc88/diskmgr.h src/win32/ui.cpp src/win32/wincore.cpp src/win32/file.cpp
```

## Results

- `git diff --check`: passed.
- `diskdrv/src/diskio.cpp` MinGW i686 syntax check passed.
- `diskdrv/src/diskio.cpp` MinGW x64 syntax check with `-fpermissive` passed.
- `src/pc88/diskmgr.h` remains on `file.h`.
- `src/win32/ui.cpp` and `src/win32/wincore.cpp` remain on `file.h` because they use `FileFinder`.
- `src/win32/file.cpp` remains on `file.h`.
- User-side VC2008 / VC8 Express `Release|Win32` build: passed.
  - Post-build `writetag`: success, `crc = 578af886`.
  - Full build summary: 3 succeeded, 0 failed, 0 skipped.
- User-side runtime smoke:
  - M88 launched successfully.
  - A game loaded and ran successfully.
  - Disk access worked.
  - Sound output worked.
  - No new warning dialog or crash appeared.

## Behavior Preservation Notes

- Only one include directive changed.
- `FileIO` method declarations, enum values, private members, and implementation are unchanged.
- `diskdrv` file read/write logic is unchanged.
- `FileFinder` remains Win32-only behind `src/win32/file.h`.

## User-Side VC2008 Verification

- `tools\windows\build_vc2008.cmd Release`
- Result: passed.

## Next Step Candidate

- After VC2008 verification, keep `src/pc88/diskmgr.h` as a separate higher-risk FileIO include step.
- Keep `FileFinder` users for a later FileFinder-specific boundary step.
