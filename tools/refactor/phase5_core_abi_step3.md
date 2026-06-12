# Phase 5 types.h Neutralization Step 3 Report

Recorded for `refactor-instructions.md` Phase 5 after `tools/refactor/phase5_types_step2_inventory.md`.

## Scope

- Small implementation slice only.
- Split only the `LONG_PTR` / pointer-width compatibility bridge from `src/common/core_headers.h`.
- Add `src/common/core_abi.h`.
- Keep `src/win32/types.h` as the compatibility wrapper.
- Do not change `intpointer`, `PTR_IDBIT`, `USE_Z80_X86`, or `MEMCALL` semantics.
- No runtime logic changes.

## Changes Made

- Added `src/common/core_abi.h`.
- Moved the existing fallback `LONG_PTR` typedef from `src/common/core_headers.h` into `src/common/core_abi.h`.
- Updated `src/common/core_headers.h` to include `core_abi.h` before `types.h`.
- Added `src/common/core_abi.h` to:
  - `M88_2008.vcproj`
  - `M88.dsp`

## Files Changed

- `src/common/core_abi.h`
- `src/common/core_headers.h`
- `M88_2008.vcproj`
- `M88.dsp`
- `tools/refactor/phase5_core_abi_step3.md`

## Commands Run

```sh
git status --short
sed -n '1,200p' refactor-instructions.md
sed -n '1,80p' src/common/core_headers.h
sed -n '1,80p' src/common/core_abi.h
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_core_abi_smoke.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -o /tmp/m88_core_abi_smoke.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_headers_core_abi_smoke.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if -o /tmp/m88_headers_core_abi_smoke.o
i686-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_types_macros.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
x86_64-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_types_macros_x64.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
i686-w64-mingw32-g++ -std=gnu++98 -D_DEBUG -E /tmp/m88_types_macros_debug.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
for f in src/common/*.cpp; do o=/tmp/m88_core_abi_$(basename "$f" .cpp).o; i686-w64-mingw32-g++ -std=gnu++98 -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
for f in src/common/*.cpp; do o=/tmp/m88_core_abi_x64_ndebug_$(basename "$f" .cpp).o; x86_64-w64-mingw32-g++ -std=gnu++98 -DNDEBUG -c "$f" -Isrc -Isrc/common -Isrc/win32 -Isrc/if -finput-charset=CP932 -o "$o" || exit 1; done
python3 tools/refactor/phase0_inventory.py --root . --output /tmp/m88_phase5_core_abi_inventory.json
```

## Results

- `git diff --check`: success.
- `core_headers.h` include smoke:
  - `i686-w64-mingw32-g++ -std=gnu++98`: passed.
- `headers.h` include smoke:
  - `i686-w64-mingw32-g++ -std=gnu++98`: passed.
- Observed macro expansion stayed unchanged from Step 2:
  - i686 Release-style: `USE_Z80_X86` on, `PTR_IDBIT` `0x1`, `MEMCALL` `__stdcall`.
  - i686 `_DEBUG`: `USE_Z80_X86` on, `PTR_IDBIT` `0x80000000`, `MEMCALL` `__stdcall`.
  - x64: `USE_Z80_X86` off, `PTR_IDBIT` undefined, `MEMCALL` empty.
- `src/common/*.cpp` compile-only smoke:
  - `i686-w64-mingw32-g++ -std=gnu++98`: passed.
  - `x86_64-w64-mingw32-g++ -std=gnu++98 -DNDEBUG`: passed.
- Phase 0 inventory was rerun:
  - include case mismatch count: `0`.
  - vcproj missing references: unchanged after staging; expected historical missing refs remain `m88dev.html` and `memo.txt`.
- VS2008 / VC8 Express rebuild:
  - Configuration: `Release|Win32`.
  - Result: success.
- Manual runtime smoke:
  - `M88.exe` launched successfully.
  - Test game ran briefly.
  - Audio output was confirmed.

## Behavior Preserved

- `src/win32/types.h` still defines `intpointer` as `LONG_PTR`.
- `PTR_IDBIT` rules are unchanged.
- `USE_Z80_X86` selection is unchanged.
- `MEMCALL` behavior is unchanged.
- `ENDIAN_IS_SMALL` and `ALLOWBOUNDARYACCESS` remain in `src/win32/types.h`.
- Existing Win32 `headers.h` include path remains valid.
- No logic changed.

## Not Verified

- Full `docs/verification.md` checklist has not been completed.

## Risks / Unknowns

- Direct `#include "types.h"` without prior Windows headers or `core_abi.h` still depends on `LONG_PTR` being supplied by the includer. This preserves the existing compatibility shape and avoids changing `types.h` semantics in this slice.
- x64 compile-only verification still uses `-DNDEBUG` because the existing debug-only pointer-to-`uint` asserts in `device_i.h` are outside this step.

## Questions

- After VS2008 rebuild verification, the next safe slice is to decide whether `types.h` should include `core_abi.h` directly, or whether to keep `core_abi.h` only on the `core_headers.h` path until a dedicated `intpointer` neutralization step.
