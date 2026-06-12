# Phase 5 types.h Neutralization Step 1 Report

Recorded for `refactor-instructions.md` Phase 5 after `tools/refactor/phase5_types_inventory.md`.

## Scope

- Add `src/common/core_types.h`.
- Move only basic typedefs and cast helper macros from `src/win32/types.h`.
- Keep `src/win32/types.h` as the compatibility include path.
- Do not move or change ABI, Z80_x86 selection, pointer tagging, endian, or alignment-related definitions.
- No logic changes.

## Changes Made

- Added `src/common/core_types.h` containing:
  - `uchar`, `ushort`, `uint`, `ulong`
  - `uint8`, `uint16`, `uint32`
  - `sint8`, `sint16`, `sint32`
  - `int8`, `int16`, `int32`
  - `packed`
  - `PACK(p)`
  - `USE_NEW_CAST`
  - `STATIC_CAST`
  - `REINTERPRET_CAST`
- Updated `src/win32/types.h` to include `../common/core_types.h`.
- Left these definitions in `src/win32/types.h` unchanged:
  - `ENDIAN_IS_SMALL`
  - `intpointer`
  - `PTR_IDBIT`
  - `ALLOWBOUNDARYACCESS`
  - `USE_Z80_X86`
  - `MEMCALL`
- Added `src/common/core_types.h` to:
  - `M88_2008.vcproj`
  - `M88.dsp`

## Files Changed

- `src/common/core_types.h`
- `src/win32/types.h`
- `M88_2008.vcproj`
- `M88.dsp`
- `tools/refactor/phase5_core_types_step1.md`

## Commands Run

```sh
git status --short
sed -n '1,140p' src/win32/types.h
sed -n '1,120p' src/common/core_headers.h
git diff --check
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_core_types_inventory.json
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_types_smoke.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_types_smoke.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_types_smoke_x64.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_types_smoke_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_core_headers_types_smoke.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_core_headers_types_smoke.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_headers_types_smoke.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_headers_types_smoke.o
for f in src/common/*.cpp; do o=/tmp/m88_core_types_$(basename "$f" .cpp).o; i686-w64-mingw32-g++ -std=gnu++98 -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
for f in src/common/*.cpp; do o=/tmp/m88_core_types_x64_$(basename "$f" .cpp).o; x86_64-w64-mingw32-g++ -std=gnu++98 -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
for f in src/common/*.cpp; do o=/tmp/m88_core_types_x64_ndebug_$(basename "$f" .cpp).o; x86_64-w64-mingw32-g++ -std=gnu++98 -DNDEBUG -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
rg -n "typedef unsigned char uchar|typedef unsigned short ushort|typedef unsigned int uint|typedef LONG_PTR intpointer|ENDIAN_IS_SMALL|ALLOWBOUNDARYACCESS|USE_Z80_X86|MEMCALL|STATIC_CAST|REINTERPRET_CAST" src/win32/types.h src/common/core_types.h
rg -n "core_types\\.h" M88_2008.vcproj M88.dsp src
```

## Results

- `git diff --check`: success.
- `core_headers.h` include smoke:
  - `i686-w64-mingw32-g++ -std=gnu++98`: passed.
- `headers.h` include smoke:
  - `i686-w64-mingw32-g++ -std=gnu++98`: passed.
- `src/common/*.cpp` compile-only smoke:
  - `i686-w64-mingw32-g++ -std=gnu++98`: passed.
  - `x86_64-w64-mingw32-g++ -std=gnu++98 -DNDEBUG`: passed.
- `x86_64-w64-mingw32-g++ -std=gnu++98` without `-DNDEBUG` still fails in `device_i.h` because of existing debug-only pointer-to-`uint` casts in `assert`. This is unchanged by this step.
- Direct `#include "types.h"` smoke without prior Windows or `core_headers.h` setup still fails because `LONG_PTR` is intentionally retained in `src/win32/types.h` for `intpointer`. This is an existing Win32 dependency and was explicitly out of scope.
- Phase 0 inventory was rerun after staging:
  - include case mismatch count: `0`.
  - vcproj missing references: `2` (`m88dev.html`, `memo.txt`, unchanged).
- VS2008 / VC8 Express rebuild:
  - Configuration: `Release|Win32`.
  - Projects: `cdif`, `diskdrv`, `M88`.
  - Result: success.
  - Summary: `3` succeeded, `0` failed, `0` skipped.
  - `cdif`: errors `0`, warnings `0`.
  - `diskdrv`: errors `0`, warnings `0`.
  - `M88`: errors `0`, warnings `6`.
  - Post-build `writetag`: success.
  - Reported CRC: `21e2a91c`.

## Remaining Warnings

- `src/common/srcbuf.cpp`: C4244 x4.
- `src/pc88/crtc.cpp`: C4003 x1.
- `src/pc88/crtc.cpp`: C4018 x1.

These warnings match the known baseline warning pattern and were not introduced by the `core_types.h` split.

## Behavior Preserved

- `src/win32/types.h` remains the compatibility include path.
- Existing include sites were not rewritten.
- `intpointer` remains `LONG_PTR`.
- `PTR_IDBIT` rules are unchanged.
- `USE_Z80_X86` selection is unchanged.
- `MEMCALL` behavior is unchanged.
- `ENDIAN_IS_SMALL` and `ALLOWBOUNDARYACCESS` remain in `src/win32/types.h`.
- No runtime logic changed.

## Not Verified

- Runtime behavior has not been manually checked after this step.

## Risks / Unknowns

- `types.h` is still not portable by itself because `intpointer` depends on `LONG_PTR`.
- A later step must decide how to neutralize `intpointer` without changing pointer width or pointer tagging behavior.
- Modern MinGW default C++ mode can still expose the existing `std::byte` / Windows `byte` conflict through global `using namespace std;`.

## Questions

- After VS2008 rebuild verification, the next decision is whether to handle `intpointer` in place or leave `types.h` compatibility as-is while moving more includes to `core_types.h`.
