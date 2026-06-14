# Phase 5 `file.h` Compatibility Wrapper Inventory

## Scope

- Inventory only.
- Do not implement changes.
- Report the remaining `file.h` include sites, current `file.h` role, relationship to `src/win32/file.cpp`, FileIO storage / Win32 implementation split prerequisites, options for keeping/shrinking/removing `file.h`, and project-file impact.

## Push Status

- Pushed the pending FileFinder commits before this inventory:
  - `e2416b1 Inventory FileFinder boundary`
  - `7a338dc Split Win32 FileFinder header`
  - `ebb3908 Use explicit FileFinder includes`
- Push result:
  - `1eea75d..ebb3908 master -> master`

## Current `file.h` Role

`src/win32/file.h` is now a compatibility wrapper:

```cpp
#pragma once

#include "../common/fileio.h"
#include "filefinder.h"
```

It no longer owns either class definition directly.

- `FileIO` declaration lives in `src/common/fileio.h`.
- `FileFinder` definition lives in `src/win32/filefinder.h`.
- `src/win32/file.cpp` still includes `file.h` and implements the Win32 `FileIO` methods.

## Remaining `file.h` Includes

### `src/win32/file.cpp`

- Includes `file.h`.
- Implements all current Win32 `FileIO` methods.
- Should remain on `file.h` until the FileIO implementation/storage split is explicitly designed.

### `src/win32/filetest.cpp`

- Includes `file.h`.
- Uses `FileIO` only.
- Candidate for a small follow-up include migration to `fileio.h`.

### `src/win32/memmon.cpp`

- Includes `file.h`.
- Uses `FileIO` only.
- Candidate for a small follow-up include migration to `fileio.h`.

### `src/win32/main.cpp`

- Includes `file.h`.
- No direct `FileIO` or `FileFinder` usage found.
- Appears to rely on `headers.h` and direct Win32/CRT APIs (`MAX_PATH`, `GetModuleFileName`, `_splitpath`).
- Candidate for dropping `file.h` in a separate small cleanup step after syntax check.

### `src/win32/iomon.cpp`

- Includes `file.h`.
- No direct `FileIO` or `FileFinder` usage found.
- Candidate for dropping `file.h` in a separate small cleanup step after syntax check.

## Current `FileIO` Storage

`src/common/fileio.h` still exposes Win32 storage:

```cpp
private:
	HANDLE hfile;
	uint flags;
	uint32 lorigin;
	Error error;
	char path[MAX_PATH];
```

This means `fileio.h` is not platform-neutral yet. It depends on the existing Windows/PCH include environment for:

- `HANDLE`
- `MAX_PATH`
- `types.h` resolving through the existing include path to `src/win32/types.h`

The current migration has clarified include boundaries, but it has not made FileIO portable.

## Relationship To `src/win32/file.cpp`

`src/win32/file.cpp` is still the only `FileIO` implementation.

Current implementation behavior to preserve:

- `CreateFile` based open/create.
- readonly uses `GENERIC_READ` and `FILE_SHARE_READ`.
- writable/create uses `GENERIC_READ | GENERIC_WRITE` and no sharing.
- `CreateNew` uses `CREATE_NEW`.
- error mapping:
  - `ERROR_FILE_NOT_FOUND` -> `file_not_found`
  - `ERROR_SHARING_VIOLATION` -> `sharing_violation`
  - otherwise `unknown`
- logical origin offset is applied to seek/tell behavior.
- `path[MAX_PATH]` stores the last opened path for `Reopen`.

Do not change these while cleaning `file.h` includes.

## FileIO Storage / Implementation Split Prerequisites

Before removing Win32 storage from `src/common/fileio.h`, decide:

- Whether to use an opaque pointer (`FileIOPlatform*`) or fixed inline storage.
- Whether object size changes are acceptable.
- Whether allocation failure can be introduced in the constructor/open path.
- How to preserve `Reopen()` without exposing `MAX_PATH` in the common header.
- How to keep VC2008 compatibility without `alignas`, `std::unique_ptr`, or modern C++ facilities.
- Whether MinGW x64 should be supported before or after the pointer-tagging issues are addressed.

This should be a design step before implementation.

## Options For `file.h`

### Option A: Keep Wrapper As-Is

Keep `src/win32/file.h` indefinitely:

```cpp
#include "../common/fileio.h"
#include "filefinder.h"
```

Pros:

- Lowest risk.
- Existing project references remain valid.
- `src/win32/file.cpp` can stay untouched.
- Third-party/local source includes of `file.h` still work.

Cons:

- The name `file.h` remains a mixed compatibility layer.

Recommended until FileIO implementation split is designed.

### Option B: Shrink Wrapper Usage

Migrate or remove remaining non-implementation includes:

- `filetest.cpp` -> `fileio.h`
- `memmon.cpp` -> `fileio.h`
- `main.cpp` -> remove `file.h`
- `iomon.cpp` -> remove `file.h`

Pros:

- Leaves `file.h` used only by `src/win32/file.cpp` and project compatibility.
- Makes dependencies explicit.

Cons:

- Needs small verification steps.

Recommended next implementation direction.

### Option C: Remove `file.h`

Delete `src/win32/file.h` and update `src/win32/file.cpp` to include `fileio.h`.

Pros:

- Removes wrapper.

Cons:

- Premature.
- Project files reference `File.h`.
- Any untracked/local code including `file.h` breaks.
- `file.cpp` still implements a Win32 `FileIO` whose declaration contains Win32 storage.

Do not do this now.

## Project File Impact

### Current References

`M88_2008.vcproj`:

- `src\Win32\File.h`
- `src\win32\filefinder.h`
- `src\common\fileio.h`

`M88.dsp`:

- `.\src\Win32\File.h`
- `.\src\win32\filefinder.h`
- `.\src\common\fileio.h`

`diskdrv/diskdrv_2008.vcproj`:

- `..\src\Win32\File.h`
- `..\src\common\fileio.h`

`diskdrv/diskdrv.dsp`:

- `..\src\Win32\File.h`
- `..\src\common\fileio.h`

### Impact By Option

- Keeping `file.h`: no project-file changes.
- Shrinking wrapper usage: no project-file changes required.
- Removing `file.h`: would require M88 and diskdrv project-file cleanup and is not recommended yet.

## Recommended Next Step

```text
Phase 5 file.h wrapper cleanup step 1 を小さく実行しろ。
src/win32/filetest.cpp と src/win32/memmon.cpp のみ、
#include "file.h" を #include "fileio.h" に置換しろ。
FileIO API/実装/挙動変更は禁止。
src/win32/file.cpp は file.h のまま維持。
project file 変更は禁止。
完了後 report を出せ。
```

After that, handle `main.cpp` and `iomon.cpp` as a separate no-longer-needed include cleanup step.
