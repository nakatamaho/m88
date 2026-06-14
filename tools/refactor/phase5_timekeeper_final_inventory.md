# Phase 5 TimeKeeper Boundary Final Inventory

## Scope

- Inventory only.
- Treat TimeKeeper cleanup as complete for now.
- Report:
  - remaining state after moving the API to `src/common`
  - why `src/win32/timekeep.h` wrapper should remain
  - why `src/win32/timekeep.cpp` Windows implementation should remain
  - unresolved items before SDL2 timing implementation
  - next Phase 5 boundary candidates
- Do not implement changes.

## Baseline

- Pushed commit:
  - `3603f80` `Use common TimeKeeper include in Win32 users`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - D88 game
  - disk access
  - sound
  - snapshot save/load
  - clean shutdown
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Current State

Public API declaration:

```text
src/common/timekeeper.h
```

Compatibility wrapper:

```text
src/win32/timekeep.h
```

Windows implementation:

```text
src/win32/timekeep.cpp
```

Current direct include users:

```text
src/win32/sequence.h:          #include "timekeeper.h"
src/win32/romeo/piccolo.h:     #include "timekeeper.h"
src/win32/timekeep.cpp:        #include "timekeep.h"
```

Project references:

```text
M88_2008.vcproj: src\common\timekeeper.h
M88_2008.vcproj: src\win32\timekeep.h
M88_2008.vcproj: src\win32\timekeep.cpp
M88.dsp:        .\src\common\timekeeper.h
M88.dsp:        .\src\win32\timekeep.h
M88.dsp:        .\src\win32\timekeep.cpp
```

## What Is Complete

- `TimeKeeper` API is now available from `src/common`.
- `Sequencer` includes the common declaration directly.
- `Piccolo` includes the common declaration directly.
- Existing Windows implementation remains unchanged.
- VC2008 Release runtime smoke passed after the common placement and direct include cleanup.

Preserved behavior:

- `TimeKeeper::unit == 100`.
- `uint32 GetTime()` public API.
- private fields:
  - `uint32 freq`
  - `uint32 base`
  - `uint32 time`
- QPC-first behavior.
- QPC `LowPart` arithmetic.
- `timeGetTime` fallback.
- `timeBeginPeriod(1)` / `timeEndPeriod(1)` fallback behavior.

## Why Keep `src/win32/timekeep.h`

Keep the wrapper because:

- It preserves the historical include path.
- `src/win32/timekeep.cpp` still includes `"timekeep.h"`, which is appropriate for the Windows implementation file.
- It avoids breaking any local or future code that still includes `"timekeep.h"`.
- Deleting it provides no SDL2-readiness gain.
- It keeps the Windows implementation boundary explicit until implementation splitting is designed.

Recommended status:

- Keep indefinitely during Phase 5.
- Reconsider deletion only after a build-system-level platform implementation split exists.

## Why Keep `src/win32/timekeep.cpp`

Keep the implementation in `src/win32` because it still uses Windows APIs:

- `QueryPerformanceFrequency`
- `QueryPerformanceCounter`
- `timeGetTime`
- `timeBeginPeriod`
- `timeEndPeriod`

Moving this `.cpp` to common now would be misleading because the implementation is not platform-neutral.

Recommended status:

- Keep as the Windows backend implementation.
- Later add a separate SDL2 implementation rather than rewriting this file in place.

## SDL2 Timing Unresolved Items

Before adding SDL2 timing implementation, decide:

1. Build selection model
   - one implementation per target
   - avoid compiling both Windows and SDL2 `TimeKeeper` implementations into the same binary

2. SDL2 source file placement
   - likely `src/sdl/timekeep_sdl.cpp` or similar
   - do not add SDL2 headers to VC2008 project

3. Counter conversion behavior
   - preserve `unit = 100`
   - decide conversion rounding to 0.01ms units
   - decide whether to mimic accumulated Windows behavior

4. QPC `LowPart` compatibility
   - Windows backend currently uses low 32 bits only
   - improving this is a behavior change and should be separate from SDL2 backend addition

5. Fallback behavior
   - Windows fallback uses `timeGetTime` and `timeBeginPeriod(1)`
   - SDL fallback may use `SDL_GetTicks`, but there is no direct equivalent to Windows timer-period behavior

6. Verification target
   - timing changes need runtime checks for speed, sound tempo, frame pacing, disk access, and shutdown

## Remaining Risks

### Timing Behavior

Any implementation change can alter:

- normal speed
- full-speed/no-wait mode
- frame skip behavior
- audio tempo
- FDD wait timing

### Piccolo / G.I.M.I.C

`Piccolo` embeds `TimeKeeper` and is hardware-facing.

Hardware verification may not be available, so avoid behavior changes in the Windows implementation.

### Project Files

Future SDL2 implementation will require a build-system decision.

The current VC2008 project should keep using `src/win32/timekeep.cpp`.

## Next Phase 5 Boundary Candidates

### Candidate A: `WinCore` / `WinUI` Operation Boundary

Recommended next.

Reason:

- SDL2 frontend work will need a clear list of VM operations:
  - reset
  - apply config
  - disk mount/unmount
  - tape open
  - snapshot save/load
  - screen capture
  - speed/fullspeed changes
- `WinUI` currently owns menus, command routing, dialogs, drag/drop, fullscreen, monitors, and config interactions.
- `WinCore` already owns VM/device connection and some operations.

Next safe step:

```text
Phase 5 WinCore/WinUI operation boundary の棚卸しだけ実行しろ。
WinUI が直接持つ操作と WinCore に集約済みの操作を分類し、
SDL2 frontend が必要とする VM 操作 API 候補、
既存 Windows 挙動維持案、実装リスクを report しろ。
実装はするな。
```

### Candidate B: Sequencer Placement / Thread Backend Design

Useful but more timing-sensitive.

Reason:

- `Sequencer` still owns `_beginthreadex`, `WaitForSingleObject`, `TerminateThread`, `Sleep`.
- This is core timing infrastructure.

Recommended only after another design step:

- design the platform thread backend
- do not implement yet

### Candidate C: Video Boundary Review

Also useful for SDL2.

Reason:

- `src/common/draw.h` is already an abstraction.
- SDL2 video likely plugs in as another `Draw` implementation.

Need review:

- whether `Lock`/`Unlock`/`DrawScreen`/`SetPalette`/`Flip` is enough for SDL texture streaming
- whether fullscreen/window behavior can stay frontend-side

### Candidate D: Audio Driver Boundary Review

Useful but has `HWND` in `sounddrv.h`.

Reason:

- SDL2 audio backend needs an output driver that does not require `HWND`.
- Existing `WinSoundDriver::Driver::Init` takes `HWND`.

Risk:

- Audio timing and buffering are sensitive.

## Recommendation

Stop TimeKeeper cleanup here.

Recommended next work:

```text
Phase 5 WinCore/WinUI operation boundary の棚卸しだけ実行しろ。
WinUI が直接持つ操作と WinCore に集約済みの操作を分類し、
SDL2 frontend が必要とする VM 操作 API 候補、
既存 Windows 挙動維持案、実装リスクを report しろ。
実装はするな。
```

This moves closer to SDL2 frontend readiness without changing timing behavior.
