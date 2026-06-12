# Phase 5 CriticalSection Boundary Report

Recorded for `refactor-instructions.md` Phase 5 after the `if/ifcommon.h` boundary.

## Scope

- Add the minimal include boundary needed for the existing Win32 `CriticalSection` implementation.
- Preserve the current Win32 `CRITICAL_SECTION` behavior.
- Convert only the remaining `src/common` files from `headers.h` to `core_headers.h`.
- Disable PCH only for those converted files.
- No logic changes.
- No portable `CriticalSection` implementation.
- No `std::mutex` / `std::recursive_mutex` replacement.
- No SDL2 implementation.

## Changes Made

- Updated `src/win32/CritSect.h` to include `<windows.h>` directly.
  - This makes `CRITICAL_SECTION` available without relying on `src/win32/headers.h`.
  - The `CriticalSection` class implementation is unchanged.
- Replaced `headers.h` with `core_headers.h` in:
  - `src/common/soundbuf.cpp`
  - `src/common/sndbuf2.cpp`
  - `src/common/srcbuf.cpp`
- Disabled PCH only for those three files in:
  - `M88_2008.vcproj`
  - `M88.dsp`

## Files Changed

- `src/win32/CritSect.h`
- `src/common/soundbuf.cpp`
- `src/common/sndbuf2.cpp`
- `src/common/srcbuf.cpp`
- `M88_2008.vcproj`
- `M88.dsp`
- `tools/refactor/phase5_critsect_boundary.md`

## Commands Run

```sh
git status --short
sed -n '1,200p' src/win32/CritSect.h
rg -n "#include \"headers\\.h\"|#include \"core_headers\\.h\"" src/common
git diff --check
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_critsect_inventory.json
i686-w64-mingw32-g++ -c src/common/soundbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_soundbuf_critsect.o
i686-w64-mingw32-g++ -c src/common/sndbuf2.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_sndbuf2_critsect.o
i686-w64-mingw32-g++ -c src/common/srcbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_srcbuf_critsect.o
i686-w64-mingw32-g++ -std=gnu++98 -c src/common/soundbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_soundbuf_critsect.o
i686-w64-mingw32-g++ -std=gnu++98 -c src/common/sndbuf2.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_sndbuf2_critsect.o
i686-w64-mingw32-g++ -std=gnu++98 -c src/common/srcbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_srcbuf_critsect.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c src/common/soundbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_soundbuf_critsect_x64.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c src/common/sndbuf2.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_sndbuf2_critsect_x64.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c src/common/srcbuf.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o /tmp/m88_srcbuf_critsect_x64.o
rg -n '#include "headers\\.h"' src/common || true
rg -n '#include "core_headers\\.h"' src/common | wc -l
```

## Results

- `git diff --check`: success.
- Phase 0 inventory rerun:
  - include case mismatch count: `0`.
  - vcproj missing references: `2` (`m88dev.html`, `memo.txt`, unchanged).
- `src/common` files still including `headers.h`: `0`.
- `src/common` files including `core_headers.h`: `9`.
- Converted file compile-only smoke:
  - `i686-w64-mingw32-g++ -std=gnu++98`: passed for `soundbuf.cpp`, `sndbuf2.cpp`, and `srcbuf.cpp`.
  - `x86_64-w64-mingw32-g++ -std=gnu++98`: passed for `soundbuf.cpp`, `sndbuf2.cpp`, and `srcbuf.cpp`.
- MinGW default C++ mode without `-std=gnu++98` failed because modern libstdc++ exposes `std::byte`, which conflicts with the Windows SDK `byte` typedef after `using namespace std;` from `core_headers.h`. This is not a VS2008 issue and is not fixed in this step.
- VS2008 / VC8 Express rebuild:
  - Configuration: `Release|Win32`.
  - Result: success.
- Manual runtime smoke:
  - `M88.exe` launched.
  - Runtime behavior was checked and worked.

## Behavior Preserved

- `CriticalSection` still uses Win32 `CRITICAL_SECTION`.
- Lock/unlock behavior is unchanged.
- Sound buffer logic is unchanged.
- Existing Windows PCH behavior remains for files outside the converted set.
- No runtime behavior was intentionally changed.
- Basic runtime behavior still works in the tested `Release|Win32` build.

## Not Verified

- Full `docs/verification.md` checklist has not been completed.

## Risks / Unknowns

- `CritSect.h` is still a Win32 implementation. A portable implementation remains a later decision.
- Modern MinGW C++17-or-newer compile-only mode still exposes the existing global `using namespace std;` / Windows `byte` conflict. This should be handled separately from the VS2008 boundary step.
- `types.h` remains under `src/win32`.

## Questions

- After VS2008 rebuild verification, the next Phase 5 candidate is `types.h` neutralization.
