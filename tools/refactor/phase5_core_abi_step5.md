# Phase 5 types.h Neutralization Step 5 Report

Recorded for `refactor-instructions.md` Phase 5 after `tools/refactor/phase5_types_step4_inventory.md`.

## Scope

- Small implementation slice only.
- Make `src/common/core_abi.h` safe for bare MinGW x64 direct include.
- Preserve the existing `LONG_PTR` fallback intent:
  - MSVC x64: `__int64`
  - GCC/MinGW x64: `long long`
  - 32-bit: `long`
- Do not add a direct `core_abi.h` include to `src/win32/types.h`.
- Do not change `intpointer`, `PTR_IDBIT`, `USE_Z80_X86`, or `MEMCALL` semantics.
- No runtime logic changes.

## Changes Made

- Updated only the `_WIN64` fallback branch in `src/common/core_abi.h`.
- `LONG_PTR` fallback now uses:
  - `__int64` when `_MSC_VER` is defined.
  - `long long` otherwise.
- The 32-bit fallback remains `long`.

## Files Changed

- `src/common/core_abi.h`
- `tools/refactor/phase5_core_abi_step5.md`

## Commands Run

```sh
git status --short
sed -n '1,80p' src/common/core_abi.h
sed -n '1,220p' tools/refactor/phase5_types_step4_inventory.md
git diff -- src/common/core_abi.h
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step5_types_with_core_abi.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_step5_types_with_core_abi.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step5_types_with_core_abi_x64.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_step5_types_with_core_abi_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step5_types_direct.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_step5_types_direct.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step5_types_direct_x64.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_step5_types_direct_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step5_core_headers.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step5_core_headers.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step5_core_headers_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step5_core_headers_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step5_headers.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step5_headers.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step5_headers_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step5_headers_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_step5_macros.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
i686-w64-mingw32-g++ -std=gnu++98 -D_DEBUG -E /tmp/m88_step5_macros_debug.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
x86_64-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_step5_macros_x64.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
for f in src/common/*.cpp; do o=/tmp/m88_step5_common_$(basename "$f" .cpp).o; i686-w64-mingw32-g++ -std=gnu++98 -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
for f in src/common/*.cpp; do o=/tmp/m88_step5_common_x64_ndebug_$(basename "$f" .cpp).o; x86_64-w64-mingw32-g++ -std=gnu++98 -DNDEBUG -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
git diff --check
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_step5_inventory.json
```

## Results

- `core_abi.h` + `types.h` direct include smoke:
  - i686 MinGW C++98: passed.
  - x64 MinGW C++98: passed.
- `types.h` direct include without `core_abi.h`:
  - i686 MinGW C++98: still fails because `LONG_PTR` is undefined.
  - x64 MinGW C++98: still fails because `LONG_PTR` is undefined.
  - This is expected because this step did not add `core_abi.h` to `types.h`.
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

- `src/win32/types.h` was not edited.
- `types.h` remains the compatibility wrapper but still expects `LONG_PTR` from the include path.
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

- `types.h` direct include still fails until a later approved step adds `core_abi.h` directly to `types.h`.
- x64 compile-only verification still uses `-DNDEBUG` because the existing debug-only pointer-to-`uint` asserts in `device_i.h` are outside this step.

## Recommendation

After VS2008 rebuild verification, the next small step can add `#include "../common/core_abi.h"` to `src/win32/types.h`, then verify direct `types.h` include on i686/x64 while keeping `intpointer`, `PTR_IDBIT`, `USE_Z80_X86`, and `MEMCALL` unchanged.
