# Phase 5 Platform Boundary Report

Recorded for `refactor-instructions.md` Phase 5.

## Scope

- Design / inventory only.
- No platform abstraction implemented.
- No source include changes performed.
- No build-system changes performed.
- Existing Windows backend remains the only backend.

## Commands

```sh
rg -n "#include \"headers\\.h\"|#include \"file\\.h\"|#include \"CritSect\\.h\"|#include \"types\\.h\"|HWND|LoadLibrary|GetPrivateProfile|WritePrivateProfile|_beginthreadex|WaitForSingleObject|TerminateThread|QueryPerformanceCounter|timeBeginPeriod|timeGetTime|CreateFile|ReadFile|WriteFile|DirectSound|DirectDraw|DrawD2D|DrawDDS|DrawGDI|WinKeyIF|WinJoy|winmouse|IFCALL|IOCALL|REFIID|GUID" src M88_2008.vcproj
rg -l "#include \"file\\.h\"" src/pc88 src/devices src/common
rg -l "#include \"CritSect\\.h\"" src/pc88 src/common src/devices src/win32
rg -n "GetPrivateProfile|WritePrivateProfile|InitPathInfo|GetModuleFileName|m88ini|m88dir" src/win32/main.cpp src/win32/88config.cpp src/win32/winvars.* src/win32/ui.cpp
rg -n "_beginthreadex|WaitForSingleObject|TerminateThread|QueryPerformanceCounter|timeGetTime|timeBeginPeriod|CRITICAL_SECTION" src/win32 src/common src/pc88
```

## High-Level Finding

The directory layout suggests a core/platform split, but the compile boundary is still Windows-first:

- All `src/common`, `src/devices`, and `src/pc88` `.cpp` files include `headers.h`.
- `headers.h` is the Win32 PCH path and pulls in Windows/DirectX headers through `src/win32`.
- Core-visible fundamental types still come from `src/win32/types.h`.
- File I/O and locking used by core code are implemented through Win32-specific classes.

Measured after Phase 4 cleanup:

- `src/common` + `src/devices` + `src/pc88` `.cpp` files: `43`.
- Those including `headers.h`: `43`.
- Include case mismatches: `0`.

## Platform-Specific Areas

### Window / Video

- Main UI and message loop:
  - `src/win32/main.cpp`
  - `src/win32/ui.cpp`
  - `src/win32/ui.h`
- Existing core-facing abstraction:
  - `src/common/draw.h` (`Draw`)
- Windows implementation stack:
  - `src/win32/windraw.cpp`
  - `src/win32/windraw.h`
  - `src/win32/DrawGDI.*`
  - `src/win32/DrawDDS.*`
  - `src/win32/drawddw.*`
  - `src/win32/DrawD2D.*`
- Platform dependencies:
  - `HWND`, `HDC`, `RECT`, `GUID`, DirectDraw, Direct2D, window messages.
- Boundary note:
  - `Draw` is already a useful backend insertion point.
  - `WinDrawSub::Init(HWND, ..., GUID*)` is Windows-specific and should remain inside the Win32 adapter.

### Audio

- Core-facing abstraction:
  - `src/pc88/sound.h` (`Sound`)
  - `src/common/soundsrc.h`
  - `src/common/soundbuf.*`
  - `src/common/sndbuf2.*`
  - `src/common/srcbuf.*`
- Windows output:
  - `src/win32/winsound.*`
  - `src/win32/sounddrv.h`
  - `src/win32/soundwo.*`
  - `src/win32/soundds.*`
  - `src/win32/soundds2.*`
- Platform dependencies:
  - `HWND` in `WinSoundDriver::Driver::Init`.
  - waveOut / DirectSound.
  - worker threads and wait handles in output drivers.
- Boundary note:
  - Audio generation and output are partly separated already.
  - `sounddrv.h` is not platform-neutral because `HWND` is in the driver interface.

### Input

- Keyboard:
  - `src/win32/WinKeyIF.*`
  - `src/win32/keybconn.*`
  - `src/win32/ui.cpp` message handlers
- Joystick:
  - `src/win32/WinJoy.*`
- Mouse:
  - `src/win32/winmouse.*`
- Platform dependencies:
  - Win32 virtual-key codes.
  - window messages.
  - winmm joystick API.
  - `HWND` mouse/window coupling.
- Boundary note:
  - Emulator-side key matrix connection is isolated around `WinKeyIF`, but the key translation tables are VK-based.
  - A future backend should keep emulator matrix semantics stable and replace only platform event translation.

### Timer / Thread / Locking

- Emulator sequencing:
  - `src/win32/sequence.*`
- Clock:
  - `src/win32/timekeep.*`
- Locking:
  - `src/win32/CritSect.h`
- Other threaded paths:
  - `src/win32/windraw.cpp`
  - `src/win32/soundwo.cpp`
  - `src/win32/soundds2.cpp`
  - `src/win32/romeo/piccolo.cpp`
- Platform dependencies:
  - `_beginthreadex`
  - `WaitForSingleObject`
  - `TerminateThread`
  - `QueryPerformanceCounter`
  - `timeGetTime`
  - `timeBeginPeriod`
  - `CRITICAL_SECTION`
- Boundary note:
  - This is high risk. Timer precision and thread behavior affect audio latency, emulator speed, and frame pacing.
  - Windows behavior should remain the default while any alternate implementation is proven separately.

### Filesystem

- Core users of `FileIO`:
  - `src/devices/opna.cpp`
  - `src/pc88/crtc.cpp`
  - `src/pc88/diskmgr.h`
  - `src/pc88/kanjirom.cpp`
  - `src/pc88/memory.cpp`
  - `src/pc88/subsys.cpp`
  - `src/pc88/tapemgr.cpp`
- Implementation:
  - `src/win32/file.cpp`
  - `src/win32/file.h`
- Platform dependencies:
  - `CreateFile`
  - `ReadFile`
  - `WriteFile`
  - Win32 handle semantics.
- Boundary note:
  - `FileIO` is already a thin API.
  - The safest future step is to keep the `FileIO` interface stable and split implementations behind it.

### Configuration

- Path initialization:
  - `src/win32/main.cpp` (`GetModuleFileName`, `m88dir`, `m88ini`)
- INI read/write:
  - `src/win32/88config.cpp`
- UI/core application:
  - `src/win32/ui.cpp`
- Platform dependencies:
  - `GetPrivateProfileInt`
  - `GetPrivateProfileString`
  - `WritePrivateProfileString`
- Boundary note:
  - Preserve executable-directory `M88.ini` behavior.
  - Do not change config file format or path rules in Phase 5.

### Plugin / Extension ABI

- Interfaces:
  - `src/if/ifcommon.h`
  - `src/if/ifguid.h`
  - `src/if/ifui.h`
  - `src/if/ifpc88.h`
- Windows loaders:
  - `src/win32/module.*`
  - `src/win32/extdev.*`
  - `src/win32/winexapi.*`
- Bundled modules:
  - `cdif/`
  - `diskdrv/`
  - `sample1/`
  - `sample2/`
- Platform / ABI dependencies:
  - `IFCALL` / `IOCALL` as `__stdcall`
  - `REFIID`
  - `GUID`
  - `LoadLibrary`
  - `GetProcAddress`
  - `__cdecl` factories such as `M88CreateModule`
- Boundary note:
  - Windows plugin ABI must not change.
  - Non-Windows definitions should be proposal-only until the support scope is decided.

### Hardware-Specific FM Output

- G.I.M.I.C / c86ctl:
  - `src/win32/romeo/piccolo_gimic.cpp`
  - `src/win32/romeo/c86ctl.h`
- ROMEO / PCIDEBUG path:
  - `src/win32/romeo/piccolo_romeo.cpp`
- Platform dependencies:
  - Windows DLL loading.
  - real hardware and vendor DLLs.
- Boundary note:
  - Treat as optional Win32-only hardware backend.
  - Do not alter while establishing core boundaries.

## Existing Abstractions Worth Preserving

- `Draw` in `src/common/draw.h`
  - Candidate boundary for future SDL2 video.
- `Sound`, `SoundSource`, `ISoundSource`
  - Candidate boundary for future SDL2 audio.
- `FileIO`
  - Thin enough to split by implementation later.
- `CriticalSection`
  - Interface can likely be preserved while implementations vary.
- `Sequencer` / `TimeKeeper`
  - Names can remain, but implementation must be treated as platform-sensitive.

## Proposed Phase 5 Implementation Order

Implementation requires explicit approval per item.

### 1. Core PCH Boundary

- Add a neutral core header, for example `src/common/core_headers.h`.
- Move non-Win32 standard includes and shared type inclusion there.
- Replace `headers.h` in `src/common`, `src/devices`, and `src/pc88` gradually.
- Keep Win32 project PCH behavior intact for Win32 files.
- Verification:
  - VS2008 `Release|Win32` rebuild.
  - No warning increase.
  - No behavior changes.

### 2. Neutralize Basic Types

- Introduce or move neutral type definitions out of `src/win32/types.h`.
- Replace `LONG_PTR` use for `intpointer` with an equivalent fixed standard type only after confirming pointer-tag behavior.
- Preserve:
  - `USE_Z80_X86` selection rules.
  - `ENDIAN_IS_SMALL`
  - `ALLOWBOUNDARYACCESS`
  - `MEMCALL` / ABI behavior on Win32.
- Verification:
  - Confirm 32-bit still selects the same Z80 path.
  - Confirm x64 path remains unchanged.

### 3. Split `FileIO` And `CriticalSection` Implementations

- Keep current class names and call sites stable.
- Provide Win32 implementation as the existing default.
- Add portable implementation only behind a deliberate platform selection.
- Verification:
  - ROM load.
  - D88 read/write on disposable copy.
  - T88 load.
  - Snapshot save/load.

### 4. Remove `HWND` From Future Audio Driver Boundary

- Proposal only for now.
- Keep DirectSound/waveOut needs inside Win32 driver classes.
- Do not change `winsound` behavior until a second backend exists.

### 5. Non-Windows Plugin ABI Definitions

- Proposal only for now.
- Windows ABI remains unchanged.
- Decide whether non-Windows builds support plugins at all before implementing.

## Stop And Ask Items Before Implementation

- Whether non-Windows support targets x64 only or includes 32-bit.
- Whether `Z80_x86` is Windows-only forever.
- Whether SDL2 backend will be build-time selectable or coexist with Win32.
- Whether plugin ABI exists on non-Windows or is disabled there.
- Whether a future portable build must support snapshots saved by Win32 builds.
- Whether timer precision should prioritize original Windows behavior or platform-native behavior.

## Recommendation

Do not implement Phase 5 changes in one large patch.

The first concrete implementation step should be the core PCH boundary, but only after explicit approval. It is the largest blocker for cross-platform compilation and can be verified mechanically by compiler errors plus Windows rebuilds.

For now, treat this report as the Phase 5 design checkpoint.

## Workspace Notes

- Generated build output directories observed and intentionally not committed:
  - `cdif/debug/`
  - `diskdrv/debug/`
