# Phase 5 `main.cpp` `file.h` Dependency Inventory

## Scope

- Inventory only.
- Target:
  - `src/win32/main.cpp`
- Investigate:
  - what `main.cpp` gets through `file.h`
  - debug CRT declarations
  - VC2008 / MinGW compatibility
  - keeping `file.h` versus replacing it with explicit includes
- Do not implement changes.

## Baseline

- Pushed commits:
  - `2060ab9` `Inventory file.h wrapper state`
  - `7f088fa` `Use fileio include in Win32 FileIO users`
  - `8970c9e` `Remove unused file.h include from iomon`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - game launch
  - sound
  - snapshot save/load
- Local MSVC/VC8 build is not available in this WSL environment.

## Current `main.cpp` Includes

`src/win32/main.cpp` currently includes:

```cpp
#include "headers.h"
#include "ui.h"
#include "file.h"
```

`main.cpp` directly uses:

- Win32 entry point and APIs:
  - `WinMain`
  - `HINSTANCE`
  - `LPSTR`
  - `GetModuleFileName`
  - `CoInitialize`
  - `CoUninitialize`
  - `InitCommonControls`
  - `FAILED`
- C runtime path/string APIs:
  - `_splitpath`
  - `sprintf`
  - `_MAX_DRIVE`
  - `_MAX_DIR`
  - `_MAX_FNAME`
  - `_MAX_EXT`
- project globals:
  - `m88dir`
  - `m88ini`
- UI:
  - `WinUI`
- debug CRT:
  - `_CrtSetDbgFlag`
  - `_CRTDBG_ALLOC_MEM_DF`
  - `_CRTDBG_LEAK_CHECK_DF`

## What `file.h` Provides Now

`src/win32/file.h` is now only a compatibility wrapper:

```cpp
#include "../common/fileio.h"
#include "filefinder.h"
```

This means `file.h` provides:

- `FileIO` declaration through `src/common/fileio.h`
- `FileFinder` declaration through `src/win32/filefinder.h`

`main.cpp` does not reference `FileIO` or `FileFinder`.

## `file.h` Transitive Dependencies

Through `fileio.h` and `filefinder.h`, `file.h` also assumes several declarations already exist:

- `HANDLE`
- `MAX_PATH`
- `INVALID_HANDLE_VALUE`
- `WIN32_FIND_DATA`
- `FindFirstFile`
- `FindNextFile`
- `FindClose`
- `DWORD`
- `_strdup`
- `free`
- project integer types from `types.h`

In the current include order, these are supplied mostly by `headers.h` before `file.h`.

## Debug CRT Findings

`main.cpp` uses `_CrtSetDbgFlag(...)`, but `headers.h` does not include `<crtdbg.h>`.

Local MinGW checks show that current `main.cpp` already fails syntax checking without an explicit `<crtdbg.h>` include:

```text
error: '_CRTDBG_ALLOC_MEM_DF' was not declared in this scope
error: '_CRTDBG_LEAK_CHECK_DF' was not declared in this scope
error: '_CrtSetDbgFlag' was not declared in this scope
```

Removing `file.h` from a temporary copy does not change this failure. The failure is not caused by `file.h`; it is caused by the missing explicit debug CRT declaration.

A temporary copy of `main.cpp` with:

```cpp
#include <crtdbg.h>
```

and without `#include "file.h"` passed MinGW i686 and x64 syntax checks.

## VC2008 Compatibility

VC2008 provides `<crtdbg.h>` for `_CrtSetDbgFlag` and `_CRTDBG_*` declarations.

The current source compiles under user-side VC2008 `Release|Win32`, so the MSVC PCH/project environment is currently masking or tolerating the missing explicit include.

Adding `<crtdbg.h>` explicitly would be the conventional MSVC-compatible way to declare these debug CRT APIs. The change should be checked in VC2008 because the call is currently unconditional and appears in both Release and Debug configurations.

## MinGW Compatibility

MinGW-w64 provides `<crtdbg.h>`.

Observed local behavior:

- current `main.cpp`: fails syntax check due missing `_CrtSetDbgFlag` declarations
- temporary `main.cpp` without `file.h`: same failure
- temporary `main.cpp` without `file.h` and with `<crtdbg.h>`: passes i686 and x64 syntax checks

MinGW's `<crtdbg.h>` defines `_CrtSetDbgFlag` as a no-op when `_DEBUG` is not defined, and declares debug CRT functions when `_DEBUG` is defined.

## Option A: Keep `file.h` In `main.cpp`

Pros:

- Zero code change.
- Already proven by user-side VC2008 Release build and runtime smoke.
- Avoids touching the `WinMain` include boundary in the same FileIO/FileFinder cleanup series.

Cons:

- `main.cpp` continues to include a compatibility wrapper it does not use.
- `file.h` removal remains blocked by unrelated debug CRT declaration cleanup.
- The include graph keeps suggesting `main.cpp` may need FileIO/FileFinder when it does not.

Risk:

- Lowest immediate risk.
- Leaves a known portability cleanup item.

## Option B: Replace `file.h` With Explicit `<crtdbg.h>`

Candidate future change:

```cpp
#include "headers.h"
#include "ui.h"
#include <crtdbg.h>
```

Pros:

- Removes unused `file.h` from `main.cpp`.
- Makes the debug CRT dependency explicit.
- Keeps FileIO/FileFinder boundary cleaner.
- Local MinGW i686/x64 syntax checks passed on a temporary copy.

Cons:

- Changes `main.cpp` include boundary and should be tested with VC2008.
- The `_CrtSetDbgFlag` call remains unconditional; that is existing behavior, but it becomes more visible.
- Need confirm VC2008 Release and Debug behavior remains unchanged.

Risk:

- Low, but not zero because it touches the program entry point's include boundary.

## Option C: Guard `_CrtSetDbgFlag` With `_MSC_VER` Or `_DEBUG`

This is not recommended for the next small step.

Reasons:

- It changes behavior or at least build-time behavior.
- It may affect Release builds if VC2008 currently accepts and emits the call.
- It is larger than an include-boundary cleanup.

## Recommendation

Use Option B as the next small implementation step, only if the user agrees:

- Replace `#include "file.h"` in `src/win32/main.cpp` with `#include <crtdbg.h>`.
- Do not change the `_CrtSetDbgFlag` call.
- Do not change logic.
- Do not change project files.
- Keep `src/win32/file.cpp` on `file.h`.

This isolates the real dependency and removes the final non-implementation `file.h` include outside `file.cpp`.

## Verification For Future Step

Local:

```sh
git diff --check
i686-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/main.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/main.cpp
```

User-side:

- `tools\windows\build_vc2008.cmd Release`
- Confirm `writetag` CRC appears.
- Launch M88.
- Start a game.
- Confirm sound.
- Confirm snapshot save/load.
- Confirm no new warning dialog or crash.

Optional:

- `tools\windows\build_vc2008.cmd Debug`
  - Current environment may still fail at link with missing `ddraw.lib`; that should not be counted as a regression if unchanged.
