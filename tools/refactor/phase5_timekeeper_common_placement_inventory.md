# Phase 5 TimeKeeper Common Placement Inventory

## Scope

- Inventory only.
- Direction decided by maintainer:
  - place `TimeKeeper` API in `src/common`.
- Report:
  - new placement candidates
  - include path effects
  - impact on `src/win32/sequence.h`
  - impact on `src/win32/romeo/piccolo.h`
  - VC2008 PCH / project-file impact
  - minimal steps to preserve the Windows implementation
  - boundary for later SDL2 implementation
- Do not implement changes.

## Baseline

- Pushed commit:
  - `c67d40f` `Design TimeKeeper boundary options`
- Current user-side baseline from earlier steps:
  - VC2008 / VC8 Express `Release|Win32` build passed.
  - M88 launch, D88 game, disk access, sound, snapshot save/load passed.
  - No new warning dialog or crash.
- Local MSVC/VC8 build is not available in this WSL environment.

## Current Files

Current declaration:

```text
src/win32/timekeep.h
```

Current implementation:

```text
src/win32/timekeep.cpp
```

Current project references:

```text
M88_2008.vcproj: src\win32\timekeep.cpp
M88_2008.vcproj: src\win32\timekeep.h
M88.dsp:        .\src\win32\timekeep.cpp
M88.dsp:        .\src\win32\timekeep.h
```

## Current Include Users

Only two checked headers include `timekeep.h` directly:

```text
src/win32/sequence.h
src/win32/romeo/piccolo.h
```

Both embed `TimeKeeper` by value:

```cpp
TimeKeeper keeper;      // Sequencer
TimeKeeper timekeeper;  // Piccolo
```

## `src/win32/sequence.h` Impact

`Sequencer` uses `TimeKeeper` as the core pacing time source.

Impact of moving declaration to common:

- `sequence.h` can continue including `"timekeep.h"` if `src/win32/timekeep.h` remains a compatibility wrapper.
- Or it can include `"timekeeper.h"` directly after a later cleanup step.
- For the first implementation, leaving `sequence.h` unchanged is safer.

Why:

- `Sequencer` is highly timing-sensitive.
- It already has direct Win32 dependencies:
  - `CritSect.h`
  - `HANDLE`
  - `_beginthreadex` implementation in `.cpp`
- Moving only the `TimeKeeper` declaration does not make `Sequencer` portable yet.

Recommended first step:

- Do not change `sequence.h`.
- Keep `src/win32/timekeep.h` as a wrapper that includes `../common/timekeeper.h`.

## `src/win32/romeo/piccolo.h` Impact

`Piccolo` uses `TimeKeeper` for ROMEO / G.I.M.I.C driver timing.

Impact of moving declaration to common:

- `piccolo.h` can continue including `"timekeep.h"` via wrapper.
- Directly changing `piccolo.h` to include common `timekeeper.h` is possible later, but not needed for first step.

Why keep wrapper first:

- `piccolo` is hardware-facing and timing-sensitive.
- It also has its own thread handling and `timeGetTime` usage in `piccolo.cpp`.
- Keeping the include path stable reduces risk while moving the public API declaration.

## New Placement Candidate

Recommended new declaration file:

```text
src/common/timekeeper.h
```

Contents should initially be the current public class declaration only:

- copyright/history header can be copied or updated conservatively
- `#pragma once`
- include `types.h`
- `class TimeKeeper`
- `unit = 100`
- constructor/destructor declarations
- `uint32 GetTime()`
- private fields unchanged:
  - `uint32 freq`
  - `uint32 base`
  - `uint32 time`

Why keep private fields in common for first step:

- `timekeep.cpp` needs the same fields.
- No object-size/layout change.
- No implementation behavior change.
- Keeps the move mechanical.

Longer-term note:

- If a later SDL2 backend needs different private fields, that should be a separate design step.
- Do not introduce opaque storage in the first move because it would alter object layout and allocation behavior.

## Compatibility Wrapper

Recommended wrapper:

```text
src/win32/timekeep.h
```

should become:

```cpp
#pragma once
#include "../common/timekeeper.h"
```

Rationale:

- Existing include users (`sequence.h`, `piccolo.h`) remain unchanged.
- `src/win32/timekeep.cpp` can continue including `"timekeep.h"`.
- Project-file churn is minimized.
- The public API is now available from `src/common/timekeeper.h`.

## Include Path Impact

Current M88 include paths already include:

- `src`
- `src\Win32`
- `src\common`
- `src\devices`

Existing common headers like `fileio.h`, `core_types.h`, and `core_critsect.h` are already referenced by project files.

For first implementation:

- `src/common/timekeeper.h` can include `"types.h"` consistently with existing common boundary headers.
- No include path changes should be required.
- Do not update `sequence.h` or `piccolo.h` include lines in the first step.

## VC2008 PCH Impact

Current `timekeep.cpp`:

```cpp
#include "headers.h"
#include "timekeep.h"
```

Recommended first implementation:

- Keep `timekeep.cpp` unchanged.
- Keep using Win32 PCH `headers.h`.
- Do not disable PCH.
- Do not move `timekeep.cpp`.

Reason:

- The implementation still uses Windows APIs:
  - `QueryPerformanceFrequency`
  - `QueryPerformanceCounter`
  - `timeBeginPeriod`
  - `timeGetTime`
  - `timeEndPeriod`
- The goal is API placement first, not implementation portability.

## Project File Impact

Required for first implementation:

- Add header reference:
  - `M88_2008.vcproj`: `src\common\timekeeper.h`
  - `M88.dsp`: `.\src\common\timekeeper.h`

Keep existing references:

- `src\win32\timekeep.cpp`
- `src\win32\timekeep.h`

Do not add to:

- `diskdrv` projects
- `cdif` projects

Reason:

- Only M88 uses `TimeKeeper`.
- `diskdrv` and `cdif` do not include `timekeep.h`.

## Windows Implementation Preservation

Minimal safe sequence:

1. Add `src/common/timekeeper.h` with the existing `TimeKeeper` declaration.
2. Replace `src/win32/timekeep.h` body with a wrapper include.
3. Leave `src/win32/timekeep.cpp` untouched.
4. Leave `sequence.h` and `romeo/piccolo.h` untouched.
5. Add project-file header references only.
6. Compile smoke `timekeep.cpp`, `sequence.cpp`, and `romeo/piccolo.cpp` if possible.

Preserved behavior:

- QPC-first behavior.
- QPC `LowPart` arithmetic.
- `unit = 100`.
- `timeGetTime` fallback.
- `timeBeginPeriod(1)` fallback behavior.
- `timeEndPeriod(1)` fallback cleanup.

## SDL2 Boundary Later

After common placement is proven:

- Keep `src/common/timekeeper.h` as the public API.
- Keep Windows implementation in `src/win32/timekeep.cpp`.
- Later add a separate SDL implementation file, for example:
  - `src/sdl/timekeep_sdl.cpp`

Build-system decision needed later:

- choose exactly one implementation per target
  - Windows VC2008: `src/win32/timekeep.cpp`
  - SDL2 target: SDL implementation

SDL implementation should use:

- `SDL_GetPerformanceCounter`
- `SDL_GetPerformanceFrequency`
- optional `SDL_GetTicks` fallback

Do not introduce SDL2 includes into the current Win32 project.

## Risks

### Object Layout

If private fields remain unchanged, object layout is unchanged.

Risk is low for declaration move only.

### Include Ordering

`src/common/timekeeper.h` including `"types.h"` relies on existing include paths.

This is consistent with current common headers, but still depends on `src/win32/types.h` wrapper state.

### CP932 / Encoding

`src/win32/timekeep.h` is CP932 due comments.

Implementation should avoid unnecessary comment conversion. A new `src/common/timekeeper.h` can be ASCII-only if comments are simplified.

### Piccolo / Hardware Timing

`Piccolo` uses `TimeKeeper` by value.

Even declaration-only move should be validated by build. Runtime G.I.M.I.C hardware verification may not be available; do not change behavior.

### Future SDL2

SDL timing can differ subtly from Windows QPC.

Do not compare SDL behavior until the Windows behavior is captured and the public unit remains stable.

## Verification For Future Implementation

Local:

```sh
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/timekeep.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/sequence.cpp
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/romeo/piccolo.cpp
```

User-side:

- `tools\windows\build_vc2008.cmd Release`
- Confirm post-build `writetag` CRC appears.
- Launch M88.
- Boot a D88 game.
- Confirm disk access works.
- Confirm sound output and tempo feel normal.
- Confirm snapshot save/load.
- Confirm clean shutdown.
- Confirm no new warning dialog or crash.

## Recommended Next Implementation Step

```text
Phase 5 TimeKeeper common placement step 1 を小さく実行しろ。
src/common/timekeeper.h を追加し、既存の TimeKeeper public API 宣言だけを移せ。
src/win32/timekeep.h は互換 wrapper として src/common/timekeeper.h を include するだけにしろ。
src/win32/timekeep.cpp の Windows 実装、QPC LowPart、unit=100、ロジック変更は禁止。
sequence.h と romeo/piccolo.h の include は変更禁止。
必要な project file header 参照だけ追加し、完了後 report を出せ。
```
