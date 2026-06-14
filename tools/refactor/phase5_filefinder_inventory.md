# Phase 5 FileFinder Boundary Inventory

## Scope

- Inventory only.
- Do not implement changes.
- Inspect the `FileFinder` class currently left in `src/win32/file.h`.
- Report API, callers, Win32 dependencies, separation options, `file.h` compatibility wrapper options, and project-file impact.

## Push Status

- Pushed the pending FileIO include migration commits before this inventory:
  - `65a50c8 Migrate ROM FileIO includes`
  - `45bec19 Migrate diskdrv FileIO include`
  - `1eea75d Migrate disk manager FileIO include`
- Push result:
  - `a6949b4..1eea75d master -> master`

## Current `FileFinder` API

Defined inline in `src/win32/file.h`.

```cpp
class FileFinder
{
public:
	FileFinder();
	~FileFinder();

	bool FindFile(char* szSearch);
	bool FindNext();

	const char* GetFileName();
	DWORD GetFileAttr();
	const char* GetAltName();

private:
	char* searcher;
	HANDLE hff;
	WIN32_FIND_DATA wfd;
};
```

## Current Behavior

- `FindFile(char* szSearch)`
  - Resets `hff` to `INVALID_HANDLE_VALUE`.
  - Frees any previous `searcher`.
  - Stores a duplicate of the search string with `_strdup`.
  - Returns whether allocation succeeded.
- `FindNext()`
  - Returns false if `FindFile` was not called successfully.
  - Calls `FindFirstFile(searcher, &wfd)` on the first iteration.
  - Calls `FindNextFile(hff, &wfd)` after that.
- Destructor
  - Frees `searcher`.
  - Calls `FindClose(hff)` if a search handle was opened.
- Accessors
  - Return `WIN32_FIND_DATA` fields directly.

## Callers

### `src/win32/ui.cpp`

- Includes `file.h`.
- Uses both `FileIO` and `FileFinder`.
- `FileIO` uses:
  - command-line/load-path checks around `ApplyCommandLine`.
  - snapshot save path handling.
- `FileFinder` use:
  - snapshot menu population.
  - Searches snapshot files with a wildcard path from `GetSnapshotName(buf, -1)`.
  - Uses `GetFileName()` and indexes the snapshot slot digit from the returned filename.

### `src/win32/wincore.cpp`

- Includes `file.h`.
- Uses both `FileIO` and `FileFinder`.
- `FileIO` uses:
  - snapshot save/load.
- `FileFinder` use:
  - external module discovery in `WinCore::ConnectExternalDevices()`.
  - Searches `m88dir + "*.m88"`.
  - Uses `GetFileName()` as the module filename passed to `ExtendModule::Create`.

## Other Remaining `file.h` Includes

These include `file.h` but do not use `FileFinder`:

- `src/win32/file.cpp`
  - Must remain on `file.h` for now because it is the Win32 `FileIO` implementation.
- `src/win32/memmon.cpp`
  - Uses `FileIO` only.
- `src/win32/filetest.cpp`
  - Uses `FileIO` only.
- `src/win32/iomon.cpp`
  - No `FileIO` or `FileFinder` usage found in the searched source.
- `src/win32/main.cpp`
  - No `FileIO` or `FileFinder` usage found in the searched source.

These can be handled separately from the `FileFinder` split:

- `memmon.cpp` and `filetest.cpp` can likely move to `fileio.h`.
- `iomon.cpp` and `main.cpp` can likely drop `file.h` if no transitive dependency exists.
- These are not part of the FileFinder boundary implementation.

## Win32 Dependencies

`FileFinder` is intentionally Win32-specific:

- `HANDLE`
- `WIN32_FIND_DATA`
- `INVALID_HANDLE_VALUE`
- `FindFirstFile`
- `FindNextFile`
- `FindClose`
- `DWORD`
- `_strdup`
- `free`
- `MAX_PATH` is not used directly by `FileFinder`, but callers use `MAX_PATH` buffers.

Because `FileFinder` exposes `DWORD` and returns `WIN32_FIND_DATA` string fields, it should remain in the Win32 layer for now.

## FileIO Separation State

`FileIO` declaration is now in `src/common/fileio.h`.

Most non-Win32-core users have already migrated from `file.h` to `fileio.h`.

`src/win32/file.h` currently acts as:

```cpp
#include "../common/fileio.h"
class FileFinder { ... };
```

So `file.h` is already a mixed compatibility wrapper plus `FileFinder` definition.

## Separation Options

### Option A: Add `src/win32/filefinder.h`

Move only the `FileFinder` class declaration/inline implementation to:

```text
src/win32/filefinder.h
```

Then make `src/win32/file.h` a compatibility wrapper:

```cpp
#pragma once

#include "../common/fileio.h"
#include "filefinder.h"
```

Pros:

- Keeps `FileFinder` explicitly Win32-only.
- Lets `ui.cpp` and `wincore.cpp` include `fileio.h` and `filefinder.h` directly later.
- Preserves existing code that still includes `file.h`.
- Lowest behavior risk.

Cons:

- `file.h` still exists as a wrapper.
- Does not make `FileFinder` portable.

Recommended for the next implementation step.

### Option B: Keep `FileFinder` in `file.h`

Do nothing now.

Pros:

- Zero immediate risk.

Cons:

- `file.h` remains a mixed boundary.
- `ui.cpp` and `wincore.cpp` cannot be migrated cleanly to explicit includes.

Not useful as the next step because FileIO migration has already reached the FileFinder boundary.

### Option C: Create a Portable Finder Abstraction

Create a common file enumeration interface.

Pros:

- Closer to SDL/Linux/macOS goals.

Cons:

- Needs path encoding, wildcard semantics, directory traversal behavior, attribute mapping, and module discovery policy decisions.
- Higher risk than needed.

Do not implement in this phase.

## Compatibility Wrapper Plan

Keep `src/win32/file.h` after splitting `filefinder.h`.

Suggested staged behavior:

1. Add `src/win32/filefinder.h` with the current `FileFinder` class.
2. Change `src/win32/file.h` to include `../common/fileio.h` and `filefinder.h`.
3. Do not change callers in the same commit.
4. Verify VS2008 `Release|Win32`.
5. In a later small step, migrate:
   - `ui.cpp` to include both `fileio.h` and `filefinder.h`.
   - `wincore.cpp` to include both `fileio.h` and `filefinder.h`.

This keeps `file.h` compatibility for any missed local include while still clarifying the boundary.

## Project File Impact

### `M88_2008.vcproj`

Currently references:

- `src\Win32\File.h`
- `src\common\fileio.h`

If `src/win32/filefinder.h` is added, add a header reference near `src\Win32\File.h`.

### `M88.dsp`

Currently references:

- `.\src\Win32\File.h`
- `.\src\common\fileio.h`

If `src/win32/filefinder.h` is added, add a source-file entry near `.\src\Win32\File.h`.

### `diskdrv`

Currently references:

- `..\src\Win32\File.h`
- `..\src\common\fileio.h`

`diskdrv` no longer includes `file.h` from source after step 6. A new `filefinder.h` reference is not needed for `diskdrv`.

Do not remove `File.h` from `diskdrv` project files in the same step; that is a project-file cleanup decision, not part of FileFinder splitting.

### `cdif`

No impact found.

## Risks

- `FileFinder` currently has inline implementation. Moving it to `filefinder.h` should be mechanically safe if the code is copied exactly.
- `FindFile(char*)` takes mutable `char*`; do not change it to `const char*` in the split step.
- Do not alter `_strdup`/`free` ownership behavior.
- Do not alter wildcard matching or `WIN32_FIND_DATA` field exposure.
- Do not migrate `ui.cpp`/`wincore.cpp` includes in the same commit as the split.

## Recommended Next Step

```text
Phase 5 FileFinder boundary step 1 を小さく実行しろ。
src/win32/filefinder.h を追加し、FileFinder の定義だけを src/win32/file.h から移せ。
src/win32/file.h は ../common/fileio.h と filefinder.h を include する互換 wrapper として残せ。
FileFinder の API/実装/挙動変更は禁止。
ui.cpp / wincore.cpp / file.cpp の include は変更禁止。
必要な M88_2008.vcproj / M88.dsp 参照だけ追加し、完了後 report を出せ。
```
