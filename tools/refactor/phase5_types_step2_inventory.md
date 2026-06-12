# Phase 5 types.h Neutralization Step 2 Inventory

Recorded for `refactor-instructions.md` Phase 5 after `src/common/core_types.h` was introduced.

## Scope

- Inventory only.
- Do not implement changes.
- Investigate:
  - `intpointer` / `LONG_PTR`
  - `PTR_IDBIT`
  - `USE_Z80_X86`
  - `MEMCALL`
- Report preservation conditions for:
  - 32-bit Win32
  - x64
  - Z80_x86 selection
  - pointer tagging

## Files Changed

- `tools/refactor/phase5_types_step2_inventory.md`

## Current Definitions

In `src/win32/types.h`:

```cpp
typedef LONG_PTR intpointer;

#if defined(_WIN64)
#undef PTR_IDBIT
#else
#if defined(_DEBUG)
	#define PTR_IDBIT	0x80000000
#else
	#define PTR_IDBIT	0x1
#endif
#endif

#if !defined(_WIN64)
#define USE_Z80_X86
#endif

#ifdef USE_Z80_X86
	#define MEMCALL __stdcall
#else
	#define MEMCALL
#endif
```

## Observed Macro Expansion

Using `core_headers.h` as the include path:

- i686 Release-style:
  - `USE_Z80_X86`: on
  - `PTR_IDBIT`: `0x1`
  - `MEMCALL`: `__stdcall`
- i686 with `_DEBUG`:
  - `USE_Z80_X86`: on
  - `PTR_IDBIT`: `0x80000000`
  - `MEMCALL`: `__stdcall`
- x86_64:
  - `USE_Z80_X86`: off
  - `PTR_IDBIT`: undefined
  - `MEMCALL`: empty

These are the behavior-preservation targets.

## Dependency Inventory

### intpointer / LONG_PTR

Definition:

- `src/win32/types.h`: `typedef LONG_PTR intpointer;`

Purpose:

- Integer type that can hold pointer values.
- Used for pointer tagging and function pointer storage in memory/device paths.

Observed core users:

- `src/common/device.cpp`
- `src/common/device_i.h`
- `src/common/memmgr.cpp`
- `src/common/memmgr.h`
- `src/devices/Z80c.cpp`

Observed Win32 uses of `LONG_PTR` unrelated to `intpointer`:

- `src/win32/ui.cpp`
- `src/win32/about.cpp`
- `src/win32/newdisk.cpp`
- `src/win32/winmon.cpp`
- `src/win32/memmon.cpp`
- `cdif/src/config.cpp`

Current bridge:

- `src/common/core_headers.h` provides a temporary `LONG_PTR` typedef when Windows headers have not supplied it.
- This lets `types.h` continue defining `intpointer` without directly including Windows headers.

Risk:

- Any replacement must preserve pointer width exactly.
- Using a 32-bit type on x64 would break pointer storage.
- Changing this in the same step as `PTR_IDBIT` or `MEMCALL` would make regressions hard to isolate.

### PTR_IDBIT

Purpose:

- Marks whether a memory page pointer stores raw memory or a callback function pointer.
- Used as a low bit or high debug bit in tagged pointers.

Current rules:

- x64: undefined.
- 32-bit Release-style: `0x1`.
- 32-bit `_DEBUG`: `0x80000000`.

Observed users:

- `src/common/device.h`
- `src/common/device_i.h`
- `src/common/memmgr.cpp`
- `src/common/memmgr.h`
- `src/devices/Z80c.cpp`
- `src/devices/Z80_x86.cpp`
- `src/devices/Z80_x86.h`

Important behavior:

- `src/devices/Z80_x86.h` requires `PTR_IDBIT`.
- `src/devices/Z80_x86.cpp` maps `IDBIT` to `PTR_IDBIT`.
- `MemoryBus` and `MemoryManager` use `idbit` to distinguish direct pointer access from callback dispatch.
- On x64, `PTR_IDBIT` is intentionally disabled and the non-tagged path is used.

Risk:

- Changing the value changes the memory callback encoding.
- Defining it on x64 would alter code paths and may break pointer assumptions.
- Removing it on 32-bit would disable Z80_x86 requirements.

### USE_Z80_X86

Current rule:

- Defined whenever `_WIN64` is not defined.

Observed users:

- `src/win32/types.h`
- `src/devices/Z80_x86.cpp`
- `src/pc88/pc88.h`

Selection path:

- `src/pc88/pc88.h` defines `CPU_Z80X86` when `USE_Z80_X86` is defined.
- `pc88.h` includes `Z80_x86.h` when `CPU_Z80X86` is defined.
- `pc88.h` chooses:
  - `typedef Z80_x86 Z80;` when `CPU_Z80X86` and `USE_Z80_X86` are both defined.
  - `typedef Z80C Z80;` otherwise.

Preservation conditions:

- 32-bit Win32 must continue selecting `Z80_x86`.
- x64 must continue selecting `Z80C`.

Risk:

- This affects CPU implementation and performance.
- Timing-sensitive behavior could change if selection changes.

### MEMCALL

Current rule:

- `__stdcall` when `USE_Z80_X86` is defined.
- empty otherwise.

Observed users:

- `src/common/device.cpp`
- `src/common/device.h`
- `src/common/memmgr.h`
- `src/devices/Z80Debug.*`
- `src/devices/Z80Test.*`
- `src/pc88/memory.*`
- `src/win32/memmon.*`
- `sample2/src/mem.*`
- `src/if/ifcommon.h`

Purpose:

- Calling convention for memory callback function pointer types.
- Coupled to the 32-bit x86 Z80 engine.

Preservation conditions:

- 32-bit Win32 with `USE_Z80_X86`: `MEMCALL` must remain `__stdcall`.
- x64 / non-`USE_Z80_X86`: `MEMCALL` must remain empty.

Risk:

- Changing this can make function pointer types incompatible.
- It can break inline assembly assumptions in `Z80_x86`.
- It can break callback signatures in memory manager and monitor paths.

## Implementation Risk Assessment

### Low-Risk Candidate

Extracting a neutral definition for pointer-sized integer could be low risk only if it preserves exact width and name:

- Possible future target: define `intpointer` through a neutral helper that maps to pointer-width integer.
- But do not change the public typedef name yet.

### High-Risk / Hold

Do not change in the next implementation step:

- `PTR_IDBIT` values or conditions.
- `USE_Z80_X86` condition.
- `MEMCALL` condition.
- `pc88.h` CPU typedef logic.
- `Z80_x86` include guards or requirements.

## Recommended Next Slice

The safest next implementation slice is not to move all remaining macros. Instead:

1. Add a tiny compatibility helper that supplies `LONG_PTR` / pointer-width support in one place, or document that `core_headers.h` remains responsible for it.
2. Keep `intpointer` in `src/win32/types.h` until a dedicated pointer-width verification step is approved.
3. Keep `PTR_IDBIT`, `USE_Z80_X86`, and `MEMCALL` in `src/win32/types.h` for now.

Alternative implementation, if approved later:

- Introduce `src/common/core_abi.h` for `intpointer` only, with compile-time size checks.
- Leave `PTR_IDBIT`, `USE_Z80_X86`, and `MEMCALL` in `src/win32/types.h`.
- Verify:
  - 32-bit: `USE_Z80_X86` on, `PTR_IDBIT` defined, `MEMCALL` `__stdcall`.
  - x64: `USE_Z80_X86` off, `PTR_IDBIT` undefined, `MEMCALL` empty.
  - VS2008 Release|Win32 rebuild.
  - Runtime smoke.

## Commands Run

```sh
git status --short
sed -n '1,90p' src/win32/types.h
rg -n '\b(intpointer|LONG_PTR|PTR_IDBIT|USE_Z80_X86|MEMCALL)\b' src cdif diskdrv sample1 sample2 -g '*.[ch]' -g '*.cpp'
rg -n 'CPU_Z80X86|Z80_x86|Z80C|cpu1|cpu2|USE_Z80_X86' src/pc88 src/devices src/win32 -g '*.[ch]' -g '*.cpp'
i686-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_types_macros.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
x86_64-w64-mingw32-g++ -std=gnu++98 -E /tmp/m88_types_macros_x64.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
i686-w64-mingw32-g++ -std=gnu++98 -D_DEBUG -E /tmp/m88_types_macros_debug.cpp -Isrc -Isrc/common -Isrc/win32 -Isrc/if | rg 'USE_Z80_X86_|PTR_IDBIT_|MEMCALL_TOKEN'
```

## Results

- Inventory only; no code behavior changed.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Questions

- Should the next implementation leave `PTR_IDBIT`, `USE_Z80_X86`, and `MEMCALL` in `src/win32/types.h` and only centralize the `LONG_PTR` compatibility bridge?
