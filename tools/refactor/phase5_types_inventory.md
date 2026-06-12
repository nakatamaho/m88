# Phase 5 types.h Neutralization Inventory

Recorded for `refactor-instructions.md` Phase 5.

## Scope

- Inventory only.
- Do not move `types.h`.
- Do not change typedef or macro meanings.
- Do not change ABI, Z80 engine selection, endian assumptions, pointer tagging, or build settings.

## Files Changed

- `tools/refactor/phase5_types_inventory.md`

## Current File

- `src/win32/types.h`

## Direct Includes / Project References

Direct `#include "types.h"` users found:

- `src/common/core_headers.h`
- `src/common/device.h`
- `src/common/draw.h`
- `src/common/lpf.h`
- `src/common/lz77d.h`
- `src/common/soundbuf.h`
- `src/common/soundsrc.h`
- `src/devices/Z80.h`
- `src/devices/Z80_x86.cpp`
- `src/devices/Z80c.h`
- `src/devices/Z80diag.h`
- `src/if/ifcommon.h`
- `src/if/ifui.h`
- `src/pc88/config.h`
- `src/pc88/floppy.h`
- `src/pc88/pcinfo.h`
- `src/pc88/screen.h`
- `src/pc88/sound.cpp`
- `src/win32/about.h`
- `src/win32/dderr.cpp`
- `src/win32/file.h`
- `src/win32/headers.h`
- `src/win32/keybconn.h`
- `src/win32/newdisk.h`
- `src/win32/romeo/piccolo.h`
- `src/win32/sequence.h`
- `src/win32/sounddrv.h`
- `src/win32/status.h`
- `src/win32/timekeep.h`
- `src/win32/ui.h`
- `src/win32/wincore.h`
- `src/win32/windraw.h`
- `src/win32/winmon.h`
- `src/win32/winsound.h`
- `cdif/src/aspi.h`
- `cdif/src/cdrom.h`

Build/project references:

- `M88_2008.vcproj`: `src\Win32\types.h`
- `M88.dsp`: `.\src\Win32\types.h`

Indirect reach is broad because `src/common/core_headers.h` and `src/win32/headers.h` both include `types.h`.

## Content Classification

### Basic Typedefs

- `uchar`
- `ushort`
- `uint`
- `ulong`
- `uint8`
- `uint16`
- `uint32`
- `sint8`
- `sint16`
- `sint32`
- `int8`
- `int16`
- `int32`
- `packed`

These are portable in intent but historically tied to exact compiler sizes. Do not replace with `<stdint.h>` / `<cstdint>` types without confirming structure layouts and binary formats.

### Win32-Dependent Typedef

- `typedef LONG_PTR intpointer;`

This is the primary Win32 type dependency. `intpointer` is used for pointer tagging and function pointer storage in memory/device paths.

Observed use areas:

- `src/common/device.cpp`
- `src/common/device_i.h`
- `src/common/memmgr.cpp`
- `src/common/memmgr.h`
- `src/devices/Z80c.cpp`

Risk: high enough to split from any include relocation. It must preserve pointer width exactly on Win32 and x64.

### Endian / Packed Access Assumptions

- `ENDIAN_IS_SMALL`
- `packed`
- `PACK(p)`
- `ALLOWBOUNDARYACCESS`

Observed references:

- `ENDIAN_IS_SMALL`: `src/common/device.h`
- `ALLOWBOUNDARYACCESS`: `src/devices/Z80c.cpp`
- `packed` / `PACK`: display and memory fast paths, especially `crtc`, `screen`, and device code.

These are behavior and performance assumptions, not just type declarations. Keep them unchanged.

### Pointer Tagging

- `PTR_IDBIT`
- `intpointer`

Current rules:

- `_WIN64`: `PTR_IDBIT` undefined.
- 32-bit `_DEBUG`: `PTR_IDBIT 0x80000000`
- 32-bit non-debug: `PTR_IDBIT 0x1`

Observed references:

- `src/common/device.h`
- `src/common/device_i.h`
- `src/common/memmgr.cpp`
- `src/common/memmgr.h`
- `src/devices/Z80c.cpp`
- `src/devices/Z80_x86.cpp`
- `src/devices/Z80_x86.h`

Risk: high. This affects memory manager representation and the 32-bit x86 Z80 engine. Do not change in the first implementation step.

### Z80_x86 Selection

- `USE_Z80_X86`

Current rule:

- Defined when `!defined(_WIN64)`.

Observed references:

- `src/win32/types.h`
- `src/devices/Z80_x86.cpp`
- `src/pc88/pc88.h`

Behavior to preserve:

- 32-bit Win32 keeps `USE_Z80_X86`.
- x64 keeps `USE_Z80_X86` disabled.

This is not merely a type concern. It selects the CPU implementation path and affects performance and potentially timing.

### ABI / Calling Convention

- `MEMCALL`
- `STATIC_CAST`
- `REINTERPRET_CAST`
- `USE_NEW_CAST`

`MEMCALL` current rule:

- `__stdcall` when `USE_Z80_X86` is defined.
- empty otherwise.

Observed `MEMCALL` use areas:

- `src/common/device.cpp`
- `src/common/device.h`
- `src/common/memmgr.h`
- `src/devices/Z80Debug.*`
- `src/devices/Z80Test.*`
- `src/pc88/memory.*`
- `src/win32/memmon.*`
- `sample2/src/mem.*`
- `src/if/ifcommon.h`

Risk: high. This is ABI-relevant for memory callback function pointer types. Preserve exactly.

`STATIC_CAST` is widely used in device descriptor tables. Keep macro spelling and behavior until a separate cleanup is approved.

`REINTERPRET_CAST` is used by `src/pc88/crtc.cpp`; keep unchanged.

## Move Candidates

Safe to propose for a future small implementation step, without changing meaning:

- Basic typedef block:
  - `uchar`, `ushort`, `uint`, `ulong`
  - `uint8`, `uint16`, `uint32`
  - `sint8`, `sint16`, `sint32`
  - `int8`, `int16`, `int32`
- `packed`
- `PACK(p)`
- `USE_NEW_CAST`
- `STATIC_CAST`
- `REINTERPRET_CAST`

Possible target:

- Add `src/common/core_types.h`.
- Have `src/win32/types.h` include `src/common/core_types.h`.
- Keep `src/win32/types.h` path as the compatibility include during the first implementation step.

This would reduce duplication risk while preserving all existing include paths.

## Hold / Do Not Move First

Do not move or alter in the first implementation step:

- `intpointer`
- `PTR_IDBIT`
- `USE_Z80_X86`
- `MEMCALL`
- `ENDIAN_IS_SMALL`
- `ALLOWBOUNDARYACCESS`

Reasons:

- They are tied to CPU selection, memory callback ABI, pointer tagging, and low-level memory/display behavior.
- Changing or even relocating them without a dedicated verification plan could alter 32-bit vs x64 behavior.

## Suggested Next Implementation Slice

Smallest safe implementation candidate after this inventory:

1. Add `src/common/core_types.h` containing only the basic typedefs, `packed`, `PACK`, and cast macros.
2. Update `src/win32/types.h` to include `core_types.h`.
3. Leave `intpointer`, `PTR_IDBIT`, `USE_Z80_X86`, `MEMCALL`, `ENDIAN_IS_SMALL`, and `ALLOWBOUNDARYACCESS` in `src/win32/types.h`.
4. Do not update all include sites yet.
5. Verify VS2008 `Release|Win32` rebuild and runtime smoke.

This is intentionally conservative. It creates a neutral type home without changing existing consumers.

## Commands Run

```sh
git status --short
sed -n '1,220p' src/win32/types.h
rg -n '#include "types\\.h"|#include <types\\.h>|types\\.h' . -g '*.[ch]' -g '*.cpp' -g '*.hpp' -g '*.vcproj' -g '*.dsp'
rg -n '\\b(uint8|uint16|uint32|uint64|int8|int16|int32|int64|ulong|ushort|uint|intpointer|MEMCALL|IFCALL|IOCALL|USE_Z80_X86|ENDIAN_IS_SMALL|ALLOWBOUNDARYACCESS|PTR_IDBIT|LONG_PTR|__stdcall|__cdecl)\\b' src cdif diskdrv sample1 sample2 -g '*.[ch]' -g '*.cpp'
for p in ENDIAN_IS_SMALL ALLOWBOUNDARYACCESS USE_Z80_X86 PTR_IDBIT MEMCALL STATIC_CAST REINTERPRET_CAST intpointer LONG_PTR; do printf '%s ' "$p"; rg -l "\\b$p\\b" src cdif diskdrv sample1 sample2 -g '*.[ch]' -g '*.cpp' | wc -l; done
for p in ENDIAN_IS_SMALL ALLOWBOUNDARYACCESS USE_Z80_X86 PTR_IDBIT MEMCALL STATIC_CAST REINTERPRET_CAST intpointer LONG_PTR; do printf '\n## %s\n' "$p"; rg -n "\\b$p\\b" src cdif diskdrv sample1 sample2 -g '*.[ch]' -g '*.cpp' | head -80; done
rg -l '#include "types\\.h"|#include "core_headers\\.h"|#include "headers\\.h"' src cdif diskdrv sample1 sample2 -g '*.[ch]' -g '*.cpp' | sort
```

## Results

- Inventory only; no code behavior changed.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Questions

- Should the next implementation step add `src/common/core_types.h` with only the safe basic typedef/cast subset while keeping ABI and CPU-selection macros in `src/win32/types.h`?
