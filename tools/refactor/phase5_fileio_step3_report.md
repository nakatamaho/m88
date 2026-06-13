# Phase 5 FileIO Boundary Step 3 Report

## Scope

- Add `src/common/fileio.h`.
- Move only the `FileIO` declaration out of `src/win32/file.h`.
- Keep `src/win32/file.h` as the compatibility wrapper.
- Keep `FileFinder` in `src/win32/file.h`.
- Keep the Win32 implementation in `src/win32/file.cpp` unchanged.
- Add only the project-file references needed for the new header.
- Do not change FileIO behavior, storage layout, or caller include sites.

## Baseline

- Previous user-side VS2008 / VC8 Express `Release|Win32` rebuild was successful.
- Previous user-side runtime check was successful, including game execution and sound output.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- Added `src/common/fileio.h` with the existing `FileIO` declaration.
- Replaced the `FileIO` declaration in `src/win32/file.h` with `#include "../common/fileio.h"`.
- Left `FileFinder` in `src/win32/file.h`.
- Left `src/win32/file.cpp` untouched, preserving the current `CreateFile`/`ReadFile`/`WriteFile` implementation.
- Added the new header to:
  - `M88_2008.vcproj`
  - `M88.dsp`
  - `diskdrv/diskdrv_2008.vcproj`
  - `diskdrv/diskdrv.dsp`

## Files Changed

- `src/common/fileio.h`
- `src/win32/file.h`
- `M88_2008.vcproj`
- `M88.dsp`
- `diskdrv/diskdrv_2008.vcproj`
- `diskdrv/diskdrv.dsp`

## Commands Run

```sh
git status --short
git diff -- src/common/fileio.h src/win32/file.h M88_2008.vcproj M88.dsp diskdrv/diskdrv_2008.vcproj diskdrv/diskdrv.dsp
rg -n "fileio\\.h|FileIO|FileFinder|core_types\\.h|draw\\.h" src/win32/file.h src/common/fileio.h M88_2008.vcproj diskdrv/diskdrv_2008.vcproj M88.dsp diskdrv/diskdrv.dsp
git diff --check
git diff --cached --check
python3 tools/refactor/phase0_inventory.py --root .
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc/win32 -Isrc/common -Isrc/if /tmp/m88_fileio_smoke.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc/win32 -Isrc/common -Isrc/if /tmp/m88_fileio_smoke.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc/win32 -Isrc/common -Isrc/if /tmp/m88_fileio_direct_smoke.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc/win32 -Isrc/common -Isrc/if /tmp/m88_fileio_direct_smoke.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc/win32 -Isrc/common -Isrc/if src/win32/file.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc/win32 -Isrc/common -Isrc/if src/win32/file.cpp
```

## Results

- `git diff --check`: passed.
- `phase0_inventory.py`: passed; include case mismatch count remains `0`.
- `vcproj` missing reference count is `2`; the new `fileio.h` reference is present in the relevant project files.
- MinGW i686/x64 syntax checks passed for:
  - existing compatibility include path: `headers.h` + `file.h`
  - direct FileIO include path under the existing Windows/PCH context: `headers.h` + `../common/fileio.h`
  - `src/win32/file.cpp`
- Local VS2008/VC8 build was not run because MSVC is not available in this WSL environment.
- User-side VS2008 / VC8 Express `Release|Win32` rebuild:
  - `diskdrv`: error 0, warning 0.
  - `cdif`: error 0, warning 0.
  - `M88`: error 0, warning 6.
  - Post-build `writetag`: success, `crc = 4ad89380`.
  - Full rebuild summary: 3 succeeded, 0 failed, 0 skipped.
- User-side runtime smoke:
  - M88 launched successfully.
  - A game was loaded and ran successfully.

## Behavior Preservation Notes

- `FileIO` method declarations, enum values, member order, and private data members are unchanged.
- `FileIO` still uses `HANDLE` and `MAX_PATH`; this step intentionally does not make the storage platform-neutral.
- Existing callers can continue including `file.h`.
- `FileFinder` remains Win32-only in `src/win32/file.h`.
- No D88/T88/ROM/snapshot/fmgen logic was changed.

## Next Step Candidate

- After verification, a later small step can migrate selected core include sites from `file.h` to `fileio.h`, still without changing the Win32 implementation.
