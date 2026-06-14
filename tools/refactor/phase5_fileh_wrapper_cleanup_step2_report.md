# Phase 5 `file.h` Wrapper Cleanup Step 2 Report

## Scope

- Target only:
  - `src/win32/main.cpp`
  - `src/win32/iomon.cpp`
- Remove unused `#include "file.h"`.
- Do not change `FileIO`, `FileFinder`, or logic.
- Keep `src/win32/file.cpp` on `file.h`.
- Do not change project files.

## Baseline

- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke launched M88, ran a game, produced sound, saved/loaded snapshots, and showed no new warning dialog or crash.
- Local MSVC/VC8 build is not available in this WSL environment.

## Changes Made

- `src/win32/iomon.cpp`
  - Removed unused `#include "file.h"`.
- `src/win32/main.cpp`
  - Left unchanged.
  - Removing `file.h` from this file exposed a transitive debug CRT dependency in syntax checks (`_CrtSetDbgFlag`, `_CRTDBG_ALLOC_MEM_DF`, `_CRTDBG_LEAK_CHECK_DF`).
  - To keep this step small and behavior-neutral, `main.cpp` was restored and deferred to a separate decision.
- `src/win32/file.cpp` was left unchanged.
- No project-file changes were made.

## Files Changed

- `src/win32/iomon.cpp`

## Commands Run

```sh
git status --short
git diff -- src/win32/main.cpp src/win32/iomon.cpp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/main.cpp src/win32/iomon.cpp src/win32/file.cpp
git checkout -- src/win32/main.cpp
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/iomon.cpp src/win32/file.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/iomon.cpp src/win32/file.cpp
```

## Results

- Initial removal from both requested files was not kept because `main.cpp` still needs a separate include-boundary decision for debug CRT declarations.
- `git diff --check`: passed.
- `src/win32/iomon.cpp` and `src/win32/file.cpp` MinGW i686 syntax check with `-fpermissive` passed.
- `src/win32/iomon.cpp` and `src/win32/file.cpp` MinGW x64 syntax check with `-fpermissive` passed.
- x64 warnings are the existing pointer-tagging casts in `device_i.h` while compiling `iomon.cpp`.

## Behavior Preservation Notes

- Only one include directive was removed.
- `iomon.cpp` does not use `FileIO` or `FileFinder`.
- `main.cpp` remains on `file.h` for now; no debug CRT behavior was changed.
- `src/win32/file.cpp` still includes `file.h`.
- `FileIO` and `FileFinder` APIs, implementations, storage, and behavior are unchanged.

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

- Treat `src/win32/main.cpp` separately:
  - either keep `file.h` as the compatibility wrapper include there, or
  - replace the transitive dependency with a precise debug CRT include if VC2008 and MinGW checks both agree.
- Do not remove `file.h` entirely while `src/win32/file.cpp` and `main.cpp` still use it.
