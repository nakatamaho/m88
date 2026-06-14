# Phase 5 `CritSect` Include Boundary Step 2 Report

## Scope

- Target only:
  - `src/pc88/diskmgr.h`
  - `src/pc88/fdc.cpp`
- Replace only the include:
  - `#include "CritSect.h"`
  - with `#include "core_critsect.h"`
- Do not change `CriticalSection` implementation, type name, `Lock` API, DiskManager/FDC logic, or lock scopes.
- Keep `src/win32/CritSect.h`.
- Do not change project files.

## Baseline

- Pushed commit:
  - `ea23e66` `Add common CriticalSection include bridge`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - game launch
  - sound
  - snapshot save/load
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- `src/pc88/diskmgr.h`
  - Replaced `#include "CritSect.h"` with `#include "core_critsect.h"`.
- `src/pc88/fdc.cpp`
  - Replaced `#include "CritSect.h"` with `#include "core_critsect.h"`.
- Left unchanged:
  - `src/win32/CritSect.h`
  - `CriticalSection` class implementation
  - `CriticalSection::Lock`
  - `DiskManager` logic
  - `FDC` logic
  - all lock scopes
  - all project files

## Files Changed

- `src/pc88/diskmgr.h`
- `src/pc88/fdc.cpp`

## Commands Run

```sh
git status --short --branch
rg -n "#include \"CritSect\\.h\"|#include \"core_critsect\\.h\"|CriticalSection::Lock|GetCS\\(\\)" src/pc88/diskmgr.h src/pc88/fdc.cpp
git diff -- src/pc88/diskmgr.h src/pc88/fdc.cpp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/diskmgr.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/fdc.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/diskmgr.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/pc88/fdc.cpp
rg -n "#include \"CritSect\\.h\"|#include \"core_critsect\\.h\"|core_critsect" src/common src/pc88 src/win32/CritSect.h
```

## Results

- `git diff --check`: passed.
- MinGW i686 syntax check passed for:
  - `src/pc88/diskmgr.cpp`
  - `src/pc88/fdc.cpp`
- MinGW x64 syntax check with `-fpermissive` passed for:
  - `src/pc88/diskmgr.cpp`
  - `src/pc88/fdc.cpp`
- Warnings observed are the existing deprecated string-literal-to-`char*` warnings in `diskmgr.cpp` and `fdc.cpp`.
- No project-file changes were made.

## Behavior Preservation Notes

- `core_critsect.h` still includes the existing Win32 `CritSect.h`.
- `CriticalSection` still uses Win32 `CRITICAL_SECTION`.
- `CriticalSection::Lock` behavior is unchanged.
- `DiskManager::GetCS()` still returns `CriticalSection&`.
- All `CriticalSection::Lock lock(...)` scopes in `fdc.cpp` are unchanged.
- D88/FDC logic is unchanged.

## Remaining Direct `CritSect.h` Includes In Common/Core

After this step:

- `src/common` uses `core_critsect.h`.
- `src/pc88` uses `core_critsect.h`.
- No direct `#include "CritSect.h"` remains in `src/common` or `src/pc88`.

Win32-side headers may still include `CritSect.h` directly and are intentionally not changed in this step.

## User-Side VC2008 Verification

- Recommended:
  - `tools\windows\build_vc2008.cmd Release`
  - Confirm post-build `writetag` prints a CRC.
  - Launch M88.
  - Boot a D88 game.
  - Reach a disk-access path if practical.
  - Confirm sound output.
  - Confirm snapshot save/load.
  - Confirm no new warning dialog or crash.
- Build result: not recorded yet for this step.
- Runtime smoke: not recorded yet for this step.

## Next Step Candidate

- Inventory remaining platform/threading boundaries now that common/core direct `CritSect.h` includes are gone:
  - `src/win32/sequence.*`
  - `src/win32/timekeep.*`
  - Win32-side `CritSect.h` users
- Do not replace `CriticalSection` with a portable implementation until a separate design step decides storage, recursion semantics, and VC2008 support.
