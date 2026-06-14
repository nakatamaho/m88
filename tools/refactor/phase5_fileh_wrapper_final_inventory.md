# Phase 5 `file.h` Wrapper Final Inventory

## Scope

- Inventory only.
- Report:
  - remaining `file.h` includes
  - why `file.h` should remain as a compatibility wrapper
  - why `file.h` should not be deleted now
  - current `FileIO` / `FileFinder` boundary state
  - next platform boundary candidates
- Do not implement changes.

## Baseline

- Pushed commits:
  - `a65fe3d` `Inventory main.cpp file.h dependency`
  - `2dd2d05` `Use explicit debug CRT include in main`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - game launch
  - sound
  - snapshot save/load
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Remaining `file.h` Include

Only one direct source include remains:

```text
src/win32/file.cpp:10:#include "file.h"
```

`src/win32/file.h` itself includes:

```cpp
#include "../common/fileio.h"
#include "filefinder.h"
```

No other checked source currently includes `file.h` directly.

## Current Direct `fileio.h` Includes

Current direct `FileIO` declaration users include:

```text
src/win32/filetest.cpp
src/win32/memmon.cpp
diskdrv/src/diskio.h
src/win32/ui.cpp
src/win32/wincore.cpp
src/devices/opna.cpp
src/pc88/tapemgr.cpp
src/pc88/diskmgr.h
src/pc88/crtc.cpp
src/pc88/kanjirom.cpp
src/pc88/subsys.cpp
src/pc88/memory.cpp
```

These no longer require the mixed `file.h` wrapper to reach `FileIO`.

## Current Direct `filefinder.h` Includes

Current direct `FileFinder` declaration users include:

```text
src/win32/ui.cpp
src/win32/wincore.cpp
```

These no longer require the mixed `file.h` wrapper to reach `FileFinder`.

## `FileIO` Boundary State

`FileIO` declaration now lives in:

```text
src/common/fileio.h
```

The current `FileIO` class declaration is still not fully platform-neutral because it contains Win32 storage types:

- `HANDLE hfile`
- `char path[MAX_PATH]`

The implementation remains Win32-only:

```text
src/win32/file.cpp
```

It still uses:

- `CreateFile`
- `ReadFile`
- `WriteFile`
- `SetFilePointer`
- `SetEndOfFile`
- `CloseHandle`
- `GetLastError`
- Win32 sharing and creation flags

This is acceptable as an intermediate Phase 5 boundary: callers can include `fileio.h`, while the implementation and storage are unchanged.

## `FileFinder` Boundary State

`FileFinder` declaration and inline implementation now live in:

```text
src/win32/filefinder.h
```

It remains explicitly Win32-only and uses:

- `FindFirstFile`
- `FindNextFile`
- `FindClose`
- `WIN32_FIND_DATA`
- `HANDLE`
- `INVALID_HANDLE_VALUE`
- `DWORD`

This keeps module/snapshot-related discovery behavior on the Win32 side and avoids moving `FileFinder` into `src/common`.

## Role Of `src/win32/file.h`

`src/win32/file.h` is now a compatibility wrapper:

```cpp
#include "../common/fileio.h"
#include "filefinder.h"
```

It no longer owns either class definition.

Remaining useful roles:

- Preserves the historical include path for any future or external local code that still includes `"file.h"`.
- Provides a stable implementation include for `src/win32/file.cpp`.
- Keeps the Win32 `FileIO` implementation source aligned with the original file naming while caller includes are already clarified.
- Avoids a delete/rename decision before the storage split is designed.

## Why Keep `file.h`

Keep `file.h` for now because:

- It is low-risk and already proven in VC2008 Release runtime smoke.
- It protects compatibility with the historical include path.
- The real boundary improvement has already happened: callers use `fileio.h` or `filefinder.h` directly.
- Deleting it would provide little practical gain while increasing compatibility risk.
- `src/win32/file.cpp` still represents the Win32 `FileIO` implementation and can reasonably include the compatibility wrapper until the implementation/storage split is designed.

## Why Not Delete `file.h` Now

Do not delete `file.h` now because:

- It is still included by `src/win32/file.cpp`.
- Removing it would require changing the implementation include path without improving caller boundaries.
- The `FileIO` declaration still exposes Win32 storage types, so the implementation is not ready to become a clean common/backend split.
- Legacy project files and external module/sample expectations may still assume a historical `file.h` path.
- Deletion is a stronger compatibility action than this phase needs.

## Why Not Move `file.cpp` To `fileio.h` Now

Changing `src/win32/file.cpp` from `file.h` to `fileio.h` is mechanically possible later, but it is not necessary now.

Reasons to defer:

- `file.cpp` is the Win32 implementation, not a boundary consumer.
- Keeping `file.cpp` on `file.h` documents that `file.h` remains a Win32 compatibility wrapper.
- Moving it would not reduce platform coupling because `FileIO` storage still contains `HANDLE` and `MAX_PATH`.
- It would create another verification step without meaningful SDL2-readiness gain.

## Project File State

Existing project file references for the split headers are present:

- `M88_2008.vcproj`
  - `src\common\fileio.h`
  - `src\win32\filefinder.h`
- `M88.dsp`
  - `.\src\common\fileio.h`
  - `.\src\win32\filefinder.h`

No project-file change is needed for this inventory.

## Current Boundary Summary

`FileIO`:

- API declaration: `src/common/fileio.h`
- Win32 implementation: `src/win32/file.cpp`
- Compatibility wrapper: `src/win32/file.h`
- Current limitation: storage still exposes Win32 types.

`FileFinder`:

- API/inline implementation: `src/win32/filefinder.h`
- Win32-only by design.
- Used directly by `ui.cpp` and `wincore.cpp`.
- Not part of common/platform-neutral API.

`file.h`:

- Compatibility wrapper only.
- Kept intentionally.

## Next Platform Boundary Candidates

### Candidate A: `FileIO` Storage / Implementation Split

Goal:

- Keep `src/common/fileio.h` public API stable.
- Hide Win32 storage (`HANDLE`, `MAX_PATH`) from the common declaration.

Possible design options:

- Add an opaque implementation pointer or backend handle field.
- Introduce a small backend-neutral private storage struct.
- Keep ABI concerns in mind because object size changes may affect stack allocation and binary compatibility inside this codebase.

Risk:

- Medium.
- `FileIO` objects are stack/member values in disk, ROM, tape, snapshot, and monitor paths.
- Object size and copy prevention must be preserved carefully.

Recommended next action:

- Design-only inventory before implementation.

### Candidate B: Remaining `CritSect` Boundary

Goal:

- Reduce core/common dependency on Win32 `CRITICAL_SECTION`.

Current evidence:

- `src/pc88/diskmgr.h` includes `CritSect.h`.
- `src/pc88/fdc.cpp` includes `CritSect.h`.
- `src/common/soundbuf.h`, `sndbuf2.h`, and `srcbuf.h` include `CritSect.h`.
- Some Win32 headers also use `CritSect.h`, but those can remain Win32-side.

Risk:

- Medium.
- Disk and sound buffering are behavior-sensitive.
- Threading/timing behavior must not change.

Recommended next action:

- Inventory-only step for remaining non-Win32 `CritSect.h` usage before any abstraction.

### Candidate C: Remaining `headers.h` / PCH Boundary

Goal:

- Continue moving low-risk core/common files away from Win32 PCH.

Current evidence:

- Many `src/pc88` and `src/devices` files still include `headers.h`.
- Phase 5 has already added `core_headers.h` and converted a limited set of common files.

Risk:

- Medium to high if done broadly.
- PCH settings in VC2008 must be adjusted per file.
- CP932/VS2008 behavior must remain stable.

Recommended next action:

- Small inventory-only step for the lowest-risk remaining `headers.h` groups, not broad conversion.

### Candidate D: `WinCore` / `WinUI` Operation Boundary

Goal:

- Identify which VM operations are already in `WinCore` and which remain entangled in `WinUI`.

Usefulness:

- Helps later SDL2 UI/event-loop work.

Risk:

- Inventory is low risk.
- Implementation is high risk because `WinUI` owns menu, window, command-line, disk/tape, snapshot, fullscreen, config, and monitor behavior.

Recommended next action:

- Inventory-only step.

## Recommendation

Stop the `file.h` cleanup here for now.

Recommended next step:

```text
Phase 5 CritSect remaining boundary の棚卸しだけ実行しろ。
src/common と src/pc88 に残る CritSect.h 利用を対象に、
利用元、共有データ、スレッド/タイミング影響、Windows 実装維持案、
可搬化する場合の最小境界案、実装リスクを report しろ。
実装はするな。
```

Reason:

- `FileIO` / `FileFinder` include boundary is now clean enough for this phase.
- `CritSect` remains a direct Win32 dependency in common/core paths and blocks further `core_headers.h` expansion.
