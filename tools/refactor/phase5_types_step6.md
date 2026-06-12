# Phase 5 types.h Neutralization Step 6 Report

Recorded for `refactor-instructions.md` Phase 5 after `tools/refactor/phase5_core_abi_step5.md`.

## Scope

- Small implementation slice only.
- Include `src/common/core_abi.h` directly from `src/win32/types.h`.
- Make direct `types.h` include compile on i686/x64 MinGW.
- Keep `src/win32/types.h` as the compatibility wrapper.
- Do not change `intpointer`, `PTR_IDBIT`, `USE_Z80_X86`, or `MEMCALL` semantics.
- No runtime logic changes.

## Changes Made

- Added one include to `src/win32/types.h`:
  - `#include "../common/core_abi.h"`
- Left the existing `#include "../common/core_types.h"` in place.
- Did not remove the existing `core_abi.h` include from `src/common/core_headers.h`; it remains harmless because `core_abi.h` has `#pragma once`.

## Files Changed

- `src/win32/types.h`
- `tools/refactor/phase5_types_step6.md`

## Commands Run

```sh
git status --short
sed -n '1,80p' src/win32/types.h
sed -n '1,80p' src/common/core_headers.h
git diff -- src/win32/types.h
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step6_types_direct.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_step6_types_direct.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step6_types_direct_x64.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_step6_types_direct_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step6_core_headers.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step6_core_headers.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step6_core_headers_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step6_core_headers_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step6_headers.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step6_headers.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_step6_headers_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_step6_headers_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_step6_macros.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
i686-w64-mingw32-g++ -std=gnu++98 -D_DEBUG -E /tmp/m88_step6_macros_debug.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
x86_64-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_step6_macros_x64.cpp -Isrc/win32 -Isrc/common | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
for f in src/common/*.cpp; do o=/tmp/m88_step6_common_$(basename "$f" .cpp).o; i686-w64-mingw32-g++ -std=gnu++98 -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
for f in src/common/*.cpp; do o=/tmp/m88_step6_common_x64_ndebug_$(basename "$f" .cpp).o; x86_64-w64-mingw32-g++ -std=gnu++98 -DNDEBUG -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
git diff --check
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_step6_inventory.json
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

- `core_headers.h` still includes `core_abi.h` before `types.h`. This is redundant after this step but not behavior-changing because `core_abi.h` is guarded by `#pragma once`.
- x64 compile-only verification still uses `-DNDEBUG` because the existing debug-only pointer-to-`uint` asserts in `device_i.h` are outside this step.

## Recommendation

After VS2008 rebuild verification, the next small cleanup can consider removing the redundant direct `core_abi.h` include from `core_headers.h`, or move on to the next `types.h` neutralization hold item only after a separate inventory.
