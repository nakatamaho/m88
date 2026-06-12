# Phase 5 types.h Neutralization Step 4 Inventory

Recorded for `refactor-instructions.md` Phase 5 after `src/common/core_abi.h` was introduced.

## Scope

- Inventory only.
- Do not implement changes.
- Investigate whether `src/win32/types.h` can directly include `src/common/core_abi.h`.
- Check:
  - direct include compatibility
  - `headers.h` / `core_headers.h` include paths
  - VS2008 and MinGW 32-bit / x64 implications
  - preservation requirements for `intpointer`, `PTR_IDBIT`, `USE_Z80_X86`, and `MEMCALL`

## Files Changed

- `tools/refactor/phase5_types_step4_inventory.md`

## Current Include Shape

- `src/common/core_headers.h`
  - includes standard C/C++ headers
  - includes `core_abi.h`
  - includes `types.h`
- `src/win32/headers.h`
  - includes Windows headers
  - includes `types.h`
- `src/win32/types.h`
  - includes `../common/core_types.h`
  - still depends on `LONG_PTR` being supplied by the includer
  - defines `intpointer`, `PTR_IDBIT`, `ALLOWBOUNDARYACCESS`, `USE_Z80_X86`, and `MEMCALL`

## Direct Include Compatibility

Current direct include of `types.h` without Windows headers or `core_abi.h` still fails:

- i686 MinGW: fails because `LONG_PTR` is undefined.
- x64 MinGW: fails because `LONG_PTR` is undefined.

Directly including `core_abi.h` before `types.h` changes this:

- i686 MinGW: passes.
- x64 MinGW: fails with the current `core_abi.h` because the fallback uses MSVC-style `__int64`, and bare MinGW x64 does not accept `__int64` before MinGW support headers define it.

Including `<windows.h>` before `types.h` passes:

- i686 MinGW: passes.
- x64 MinGW: passes.

Including the same standard-header preamble used by `core_headers.h` before `core_abi.h` also passes on x64 MinGW because MinGW support headers make `__int64` usable as `long long` on that path.

## headers.h / core_headers.h Paths

Existing include paths remain valid:

- `#include "core_headers.h"`:
  - i686 MinGW compile smoke: passed.
  - x64 MinGW compile smoke: passed.
- `#include "headers.h"`:
  - i686 MinGW compile smoke: passed.
  - x64 MinGW compile smoke: passed.

The current build-relevant paths are therefore working. The only failing path is direct `types.h` or direct `core_abi.h` + `types.h` on bare x64 MinGW.

## Observed Macro Preservation

Using the current include paths:

- i686 Release-style:
  - `USE_Z80_X86`: on
  - `PTR_IDBIT`: `0x1`
  - `MEMCALL`: `__stdcall`
- i686 `_DEBUG`:
  - `USE_Z80_X86`: on
  - `PTR_IDBIT`: `0x80000000`
  - `MEMCALL`: `__stdcall`
- x64:
  - `USE_Z80_X86`: off
  - `PTR_IDBIT`: undefined
  - `MEMCALL`: empty

These match Step 2 and Step 3 and must not change.

## VS2008 Assessment

VS2008 / MSVC accepts `__int64`, so a direct `types.h -> core_abi.h` include is expected to be compatible with the current `core_abi.h` fallback on MSVC.

This was not directly compiled in this WSL environment. Final confirmation would still require a VS2008 / VC8 Express rebuild if the implementation is approved later.

## MinGW 32-bit / x64 Assessment

- 32-bit MinGW:
  - `core_abi.h` fallback uses `long`.
  - `core_abi.h` + `types.h` direct smoke passes.
  - Existing macro behavior remains compatible.
- x64 MinGW:
  - bare `core_abi.h` + `types.h` fails today because `__int64` is not accepted until MinGW support headers are included.
  - `core_headers.h` path passes because its standard C/C++ includes pull in the required MinGW support definitions before `core_abi.h`.
  - `<windows.h>` + `types.h` path passes because Windows headers define `LONG_PTR`.

Therefore, `types.h` should not include the current `core_abi.h` directly until `core_abi.h` itself is made safe for bare MinGW x64 include.

## Preservation Conditions

Any future implementation must preserve:

- `intpointer`
  - remains pointer-width.
  - remains usable for pointer tagging and callback pointer storage.
- `PTR_IDBIT`
  - 32-bit Release-style: `0x1`.
  - 32-bit `_DEBUG`: `0x80000000`.
  - x64: undefined.
- `USE_Z80_X86`
  - 32-bit Win32: defined.
  - x64: not defined.
- `MEMCALL`
  - `__stdcall` when `USE_Z80_X86` is defined.
  - empty otherwise.

## Risk Assessment

Directly adding `#include "../common/core_abi.h"` to `types.h` is not safe as the next implementation step unless `core_abi.h` is first adjusted for bare MinGW x64.

The likely safe implementation order is:

1. Make `core_abi.h` compiler-aware while preserving MSVC behavior:
   - MSVC x64: `typedef __int64 LONG_PTR;`
   - GCC/MinGW x64: `typedef long long LONG_PTR;` or rely on a minimal MinGW support header
   - 32-bit: `typedef long LONG_PTR;`
2. Re-run direct include smoke for i686/x64.
3. Only then consider adding `core_abi.h` directly to `types.h`.

Do not change `PTR_IDBIT`, `USE_Z80_X86`, or `MEMCALL` in that same implementation slice.

## Commands Run

```sh
git status --short
sed -n '1,120p' src/win32/types.h
sed -n '1,80p' src/common/core_abi.h
sed -n '1,80p' src/common/core_headers.h
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_types_direct.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_types_direct.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_types_direct_x64.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_types_direct_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_types_with_core_abi.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_types_with_core_abi.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_types_with_core_abi_x64.cpp -Isrc/win32 -Isrc/common -o /tmp/m88_types_with_core_abi_x64.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_core_headers_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_core_headers_x64.o
x86_64-w64-mingw32-g++ -std=gnu++98 -c /tmp/m88_headers_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if -o /tmp/m88_headers_x64.o
i686-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_headers_macros.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
x86_64-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_core_headers_macros_x64.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
i686-w64-mingw32-g++ -std=gnu++98 -D_DEBUG -E /tmp/m88_core_headers_macros_debug.cpp -Isrc -Isrc/win32 -Isrc/common -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
```

## Recommendation

Do not implement `types.h -> core_abi.h` directly yet.

Next small implementation slice should first make `core_abi.h` safe for bare x64 MinGW direct include, without changing `intpointer`, `PTR_IDBIT`, `USE_Z80_X86`, or `MEMCALL`.
