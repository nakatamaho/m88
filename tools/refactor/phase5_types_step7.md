# Phase 5 types.h Neutralization Step 7 Report

Recorded for `refactor-instructions.md` Phase 5 after `tools/refactor/phase5_types_step6.md`.

## Scope

- Small cleanup slice only.
- Remove the redundant direct `core_abi.h` include from `src/common/core_headers.h`.
- Keep `src/win32/types.h` as the compatibility wrapper that supplies `core_abi.h`.
- Do not change `intpointer`, `PTR_IDBIT`, `USE_Z80_X86`, or `MEMCALL` semantics.
- No runtime logic changes.

## Changes Made

- Removed this line from `src/common/core_headers.h`:
  - `#include "core_abi.h"`
- `src/common/core_headers.h` still includes `types.h`.
- `src/win32/types.h` still includes `../common/core_abi.h` before `../common/core_types.h`.

## Files Changed

- `src/common/core_headers.h`
- `tools/refactor/phase5_types_step7.md`

## Commands Run

```sh
git status --short --branch
sed -n '1,80p' src/common/core_headers.h
sed -n '1,40p' src/win32/types.h
git diff -- src/common/core_headers.h
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step7_types_direct.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_step7_types_direct.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step7_types_direct_x64.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_step7_types_direct_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step7_core_headers.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step7_core_headers.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step7_core_headers_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step7_core_headers_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step7_headers.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step7_headers.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step7_headers_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step7_headers_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_step7_macros.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
i686-w64-mingw32-g++ -std=gnu++98 -D_DEBUG -E /tmp/m88_step7_macros_debug.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
x86_64-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_step7_macros_x64.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
for f in src/common/*.cpp; do o=/tmp/m88_step7_common_$(basename "$f" .cpp).o; i686-w64-mingw32-g++ -std=gnu++98 -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
for f in src/common/*.cpp; do o=/tmp/m88_step7_common_x64_ndebug_$(basename "$f" .cpp).o; x86_64-w64-mingw32-g++ -std=gnu++98 -DNDEBUG -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
git diff --check
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_step7_inventory.json
```

## Results

- `types.h` direct include smoke:
  - i686 MinGW C++98: passed.
  - x64 MinGW C++98: passed.
- `core_headers.h` include smoke:
  - i686 MinGW C++98: passed.
  - x64 MinGW C++98: passed.
- `headers.h` include smoke:
  - i686 MinGW C++98: passed.
  - x64 MinGW C++98: passed.
- Observed macro expansion stayed unchanged:
  - i686 Release-style: `USE_Z80_X86` on, `PTR_IDBIT` `0x1`, `MEMCALL` `__stdcall`.
  - i686 `_DEBUG`: `USE_Z80_X86` on, `PTR_IDBIT` `0x80000000`, `MEMCALL` `__stdcall`.
  - x64: `USE_Z80_X86` off, `PTR_IDBIT` undefined, `MEMCALL` empty.
- `src/common/*.cpp` compile-only smoke:
  - i686 MinGW C++98: passed.
  - x64 MinGW C++98 with `-DNDEBUG`: passed.
- `git diff --check`: success.
- Phase 0 inventory:
  - include case mismatch count: `0`.
  - vcproj missing references: `2` (`m88dev.html`, `memo.txt`, unchanged).

## Behavior Preserved

- `src/win32/types.h` remains the compatibility wrapper.
- `intpointer` remains `typedef LONG_PTR intpointer`.
- `PTR_IDBIT` rules are unchanged.
- `USE_Z80_X86` selection is unchanged.
- `MEMCALL` behavior is unchanged.
- Existing `headers.h` and `core_headers.h` include paths remain valid.
- No runtime logic changed.

## Not Verified

- VS2008 / VC8 Express rebuild was not run in this environment.
- Runtime startup/game/audio smoke was not run in this environment.
- Full `docs/verification.md` checklist has not been completed.

## Risks / Unknowns

- x64 compile-only verification still uses `-DNDEBUG` because the existing debug-only pointer-to-`uint` asserts in `device_i.h` are outside this step.

## Recommendation

The direct `LONG_PTR` dependency is now closed inside `types.h`, and the temporary duplicate include in `core_headers.h` has been removed. Further `types.h` neutralization should stop here until a separate inventory decides whether `PTR_IDBIT`, `USE_Z80_X86`, `MEMCALL`, `ENDIAN_IS_SMALL`, or `ALLOWBOUNDARYACCESS` should remain in the compatibility wrapper or move behind a new boundary.
