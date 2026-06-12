# M88 Verification Checklist

This checklist is the manual safety net for staged refactoring. Do not add ROM
images, disk images, tape images, snapshots, or hardware-specific binaries to
the repository. Record local test asset names and results outside git when
needed.

## Baseline Build

- Build environment:
  - Windows with Visual Studio 2008 / VC8 Express.
  - `writetag.exe` available from the solution root or `PATH`.
- Primary baseline:
  - Solution: `M88_2008.sln`
  - Configuration: `Release|Win32`
  - Projects: `diskdrv`, `cdif`, `M88`
- Expected result:
  - `diskdrv`: 0 errors.
  - `cdif`: 0 errors.
  - `M88`: 0 errors.
  - Post-build `writetag release\m88.exe` runs and prints a CRC.
- Record:
  - Build date.
  - Compiler / IDE version.
  - Configuration.
  - Error count.
  - Warning count and new warning deltas.
  - `writetag` CRC.

## Launch And Configuration

- Start `M88.exe` from a directory containing the required local ROM files.
- Confirm the application window opens.
- Confirm `M88.ini` is read from the executable directory.
- Change a harmless UI setting, exit, restart, and confirm the setting persists.
- Confirm no registry dependency is introduced.
- Confirm command-line handling still accepts previously working arguments.

## ROM And Machine Modes

- Confirm required N/N80/N80V2/N88 ROM sets load as available locally.
- Confirm missing ROM behavior is unchanged from baseline.
- Switch BASIC modes:
  - N
  - N80
  - N80V2
  - N88 V1
  - N88 V1H
  - N88 V2
  - N88 V2CD
- Confirm reset after mode switching behaves like baseline.
- Confirm `FONT80SR.ROM` behavior if the local test setup includes it.

## Disk Images

- Mount a known-good D88 image in drive 1.
- Boot or list files from the image.
- Exercise multi-disk image selection if the test image contains multiple disks.
- Perform a write operation on a disposable copy of a disk image.
- Confirm disk image size and write-back behavior are unchanged.
- Eject and remount the image.
- Repeat with drive 2 if applicable.

## Tape Images

- Mount a known-good T88 tape image.
- Confirm load behavior against baseline.
- Confirm tape controls do not regress.
- Use disposable copies for any write or save-path checks.

## Snapshot

- Save a snapshot from a known running state.
- Load the saved snapshot in the same build.
- Load a snapshot created by the previous baseline build if available.
- Confirm `"M88 SnapshotData"` compatibility is preserved.
- Confirm snapshot menu entries update correctly.

## Video

- Confirm screen updates in windowed mode.
- Test draw drivers available in the environment:
  - GDI
  - DirectDraw surface
  - DirectDraw window
  - Direct2D
- Confirm digital and analog palette behavior.
- Toggle 15 kHz / 24 kHz display mode if available.
- Toggle fullscreen and return to windowed mode.
- Confirm window position persistence if the option is enabled.

## Audio

- Confirm audio starts without errors.
- Test available output drivers:
  - waveOut
  - DirectSound
  - DirectSound secondary path, if selectable
- Check sample rate and buffer length options.
- Confirm OPN / OPNA placement settings still apply.
- Confirm CMD SING behavior if a known test program is available.
- Confirm there is no obvious tempo or pitch change compared with baseline.

## Input

- Keyboard:
  - Test 106-key mode.
  - Test PC-98 key mode.
  - Test English 101-key mode.
  - Confirm arrow keys and numeric keypad mappings.
- Mouse:
  - Confirm mouse capture / release behavior where applicable.
- Joystick:
  - Confirm winmm joystick input if hardware is available.
  - Confirm button swap options if configured.

## Timing And Speed

- Confirm normal-speed execution.
- Test no-wait mode.
- Test speed settings in the 500-2000 permille range.
- Test frame skip settings.
- Confirm FDD wait behavior with a disk image.
- Listen for obvious FM / SSG tempo regressions.

## Debuggers And Monitors

Open and perform a basic smoke check for:

- Memory monitor
- Code monitor
- I/O monitor
- BASIC monitor
- Register monitor
- Load monitor
- Sound monitor
- MV monitor

Confirm each window opens, updates, and closes without crashing.

## Extension Modules

- Confirm bundled `cdif` module can be built.
- Confirm bundled `diskdrv` module can be built.
- If local third-party modules are available, confirm they still load.
- Do not change plugin ABI expectations:
  - `__stdcall`
  - GUID / `REFIID`
  - `__cdecl` factory loading

## c86ctl / G.I.M.I.C

Only test when the hardware and local `c86ctl.dll` setup are available.

- Place `c86ctl.dll` next to `M88.exe`.
- Confirm G.I.M.I.C device detection.
- Confirm YMF288 / YM2608 path selection as applicable.
- Confirm fallback behavior when hardware or DLL is absent.

## Existing Verification Assets

- `src/devices/Z80Test.cpp` and `src/devices/Z80Test.h`
  - Existing CPU comparison mechanism gated by `CPU_TEST`.
  - Treat as a valuable diagnostic asset; do not remove.
  - Build and execution procedure is not yet automated.
- `src/win32/filetest.cpp` and `src/win32/filetest.h`
  - Existing file CRC/check helper used by Win32 UI/about paths.
  - Treat as a regression aid; do not remove.
- `writetag.cpp`
  - Builds the `writetag.exe` helper used by the Release post-build step.
  - Build manually with Visual Studio tools when needed:

```bat
cl /EHsc writetag.cpp
```

## Result Template

Use this shape when recording a manual verification run:

```text
Date:
Commit:
Environment:
Configuration:
Build result:
Warnings:
Post-build CRC:
Launch:
ROM/mode checks:
Disk checks:
Tape checks:
Snapshot checks:
Video checks:
Audio checks:
Input checks:
Timing checks:
Monitor checks:
Extension checks:
c86ctl/G.I.M.I.C checks:
Notes:
```
