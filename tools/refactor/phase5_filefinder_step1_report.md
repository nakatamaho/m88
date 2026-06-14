# Phase 5 FileFinder Boundary Step 1 Report

## Scope

- Add `src/win32/filefinder.h`.
- Move only the `FileFinder` definition from `src/win32/file.h` to `src/win32/filefinder.h`.
- Keep `src/win32/file.h` as a compatibility wrapper that includes:
  - `../common/fileio.h`
  - `filefinder.h`
- Do not change `FileFinder` API, implementation, or behavior.
- Do not change `ui.cpp`, `wincore.cpp`, or `file.cpp` includes.
- Add only the necessary M88 project references.

## Baseline

- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke launched M88, ran a D88 game, verified disk access, produced sound, and showed no new warning dialog or crash.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- Added `src/win32/filefinder.h` containing the existing inline `FileFinder` class.
- Replaced the inline `FileFinder` definition in `src/win32/file.h` with `#include "filefinder.h"`.
- Kept `src/win32/file.h` as the compatibility wrapper for existing callers.
- Left caller includes unchanged:
  - `src/win32/ui.cpp`
  - `src/win32/wincore.cpp`
  - `src/win32/file.cpp`
- Added `src\win32\filefinder.h` to:
  - `M88_2008.vcproj`
  - `M88.dsp`

## Files Changed

- `src/win32/filefinder.h`
- `src/win32/file.h`
- `M88_2008.vcproj`
- `M88.dsp`

## Commands Run

```sh
git status --short
sed -n '1,120p' src/win32/file.h
rg -n "filefinder\\.h|FileFinder|#include \"file\\.h\"|#include \"fileio\\.h\"" src/win32/file.h src/win32/filefinder.h src/win32/ui.cpp src/win32/wincore.cpp src/win32/file.cpp M88_2008.vcproj M88.dsp
git diff -- src/win32/file.h src/win32/filefinder.h M88_2008.vcproj M88.dsp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/file.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/ui.cpp src/win32/wincore.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/ui.cpp src/win32/wincore.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/file.cpp src/win32/ui.cpp src/win32/wincore.cpp
```

## Results

- `git diff --check`: passed.
- `src/win32/file.cpp` MinGW i686 syntax check passed.
- `src/win32/ui.cpp` and `src/win32/wincore.cpp` MinGW i686 syntax check without `-fpermissive` stopped on existing GCC strictness issues:
  - dependent-name lookup in `winexapi.h`
  - `const char*` to `LPSTR` conversion in `ui.cpp`
  - unrelated to the `FileFinder` split.
- `src/win32/ui.cpp` and `src/win32/wincore.cpp` MinGW i686 syntax check with `-fpermissive` passed.
- `src/win32/file.cpp`, `src/win32/ui.cpp`, and `src/win32/wincore.cpp` MinGW x64 syntax check with `-fpermissive` passed.
- User-side VC2008 / VC8 Express `Debug|Win32` build:
  - `diskdrv`: error 0, warning 1.
  - `cdif`: error 0, warning 0.
  - `M88`: compile and resource compile completed.
  - Link failed with the existing environment issue: `LINK : fatal error LNK1104: file 'ddraw.lib' cannot be opened`.
  - This does not indicate a compile regression from the `FileFinder` header split.
- User-side VC2008 / VC8 Express `Release|Win32` build:
  - `diskdrv`: error 0, warning 0.
  - `cdif`: error 0, warning 0.
  - `M88`: error 0, warning 6.
  - Post-build `writetag`: success, `crc = f7b874d0`.
  - Full build summary: 3 succeeded, 0 failed, 0 skipped.
- User-side runtime smoke:
  - M88 launched successfully.
  - A game loaded and ran successfully.
  - Sound output worked.
  - Snapshot save and load both succeeded.
  - No new warning dialog or crash appeared.

## Behavior Preservation Notes

- `FileFinder` constructor, destructor, methods, private members, and inline behavior were copied unchanged.
- `FindFile(char*)` signature is unchanged.
- `_strdup` / `free` ownership behavior is unchanged.
- `FindFirstFile`, `FindNextFile`, and `FindClose` usage is unchanged.
- `ui.cpp` and `wincore.cpp` still include `file.h`, so caller behavior is unchanged.
- `src/win32/file.cpp` still includes `file.h`.

## User-Side VC2008 Verification

- `tools\windows\build_vc2008.cmd Release`
- Build result: passed.
- Runtime smoke: passed.

## Next Step Candidate

- After VC2008 verification, migrate `ui.cpp` and `wincore.cpp` to explicit includes:
  - `fileio.h`
  - `filefinder.h`
- Keep `src/win32/file.cpp` on `file.h` until the FileIO implementation split is explicitly designed.
