# Phase 5 FileIO Boundary Step 2 Design

Recorded for `refactor-instructions.md` Phase 5 after `tools/refactor/phase5_fileio_inventory.md`.

## Scope

- Design only.
- Do not implement changes.
- Treat `FileIO` and `FileFinder` as separate boundaries.
- Design a minimal `src/common/fileio.h` API option.
- Keep `src/win32/file.h` as a compatibility wrapper.
- Keep the current Win32 implementation as the default.
- Evaluate object size, ABI, VC2008, PCH, vcproj, and dsp impact.
- Propose a staged implementation order.

## Current Split Problem

`src/win32/file.h` currently contains two different concerns:

- `FileIO`
  - byte stream API used by core, devices, Win32 UI, snapshots, and `diskdrv`.
  - needed for eventual portable ROM/D88/T88/snapshot/sample file access.
- `FileFinder`
  - wildcard directory enumeration.
  - currently used for Win32 snapshot-slot menu discovery and `.m88` extension module discovery.
  - exposes Win32-specific names, attributes, and alternate 8.3 names.

These should not be moved together. `FileIO` is the first portability boundary. `FileFinder` should remain Win32-side until module/plugin discovery and non-Windows file enumeration are designed separately.

## Minimal `src/common/fileio.h` API Option

The smallest useful common API is the existing `FileIO` API only:

```cpp
#pragma once

#include "types.h"

class FileIO
{
public:
	enum Flags
	{
		open     = 0x000001,
		readonly = 0x000002,
		create   = 0x000004,
	};

	enum SeekMethod
	{
		begin = 0,
		current = 1,
		end = 2,
	};

	enum Error
	{
		success = 0,
		file_not_found,
		sharing_violation,
		unknown = -1
	};

public:
	FileIO();
	FileIO(const char* filename, uint flg = 0);
	~FileIO();

	bool Open(const char* filename, uint flg = 0);
	bool CreateNew(const char* filename);
	bool Reopen(uint flg = 0);
	void Close();
	Error GetError() { return error; }

	int32 Read(void* dest, int32 len);
	int32 Write(const void* src, int32 len);
	bool Seek(int32 fpos, SeekMethod method);
	int32 Tellp();
	bool SetEndOfFile();

	uint GetFlags() { return flags; }
	void SetLogicalOrigin(int32 origin) { lorigin = origin; }

private:
	FileIO(const FileIO&);
	const FileIO& operator=(const FileIO&);

private:
	FileIOPlatform platform;
	uint flags;
	uint32 lorigin;
	Error error;
	char path[M88_MAX_PATH];
};
```

This is an API sketch, not an implementation. The unresolved parts are deliberate:

- `FileIOPlatform`
  - must be defined in a way that does not expose Win32 in common headers.
  - options are listed below.
- `M88_MAX_PATH`
  - must preserve current `MAX_PATH` behavior on Windows.
  - portable path length policy should not be decided in the same patch.

## Platform Storage Options

### Option A: Opaque Pointer

```cpp
struct FileIOPlatform;
FileIOPlatform* platform;
```

Pros:

- Removes Win32 types from the public common header.
- Stable common header for non-Windows.
- Lets each platform own its native handle type.

Cons:

- Changes `FileIO` object size and allocation behavior.
- Adds allocation failure path or requires embedded static storage elsewhere.
- `FileIO` is embedded in `DiskImageHolder` and `diskdrv::DiskIO`; object layout changes are broad.
- Needs careful destructor/copy prevention review.

Risk:

- Medium. API stays stable, but object layout changes.

### Option B: Fixed Inline Storage

```cpp
struct FileIOPlatformStorage
{
	uintptr-sized bytes...
};
```

Pros:

- Avoids allocation.
- Can preserve object value semantics better.

Cons:

- Hard to size portably without leaking platform assumptions.
- Alignment and 32/64-bit differences become an ABI problem.
- VC2008 lacks modern `alignas`.

Risk:

- Higher than Option A for old compiler portability.

### Option C: Keep Win32 Storage Until Later

First introduce `src/common/fileio.h` with the same public class shape but keep the real class in `src/win32/file.h` as the included compatibility path.

Pros:

- Lowest immediate build risk.
- Allows include path migration and caller classification first.
- Does not change object size yet.

Cons:

- Does not actually remove Win32 types from common callers yet.
- Only prepares naming and include boundaries.

Risk:

- Low, but limited benefit.

## Recommended Storage Direction

Use a staged path:

1. First add the common API header as documentation/compile boundary only, without moving storage.
2. Then migrate include sites from `file.h` to `fileio.h` only for low-risk compile-only targets if useful.
3. Only after verification, switch `FileIO` internals to an opaque pointer or a private implementation struct.

Do not combine common header addition with storage movement.

## `src/win32/file.h` Compatibility Wrapper

Keep `src/win32/file.h` present indefinitely during Phase 5.

Initial wrapper shape:

```cpp
#pragma once

#include "../common/fileio.h"

class FileFinder
{
	// Keep current Win32 FileFinder here.
};
```

Important constraints:

- Existing source files that include `"file.h"` must continue to compile.
- `FileFinder` should remain in `src/win32/file.h` or move to a separate Win32-only `filefinder.h`.
- Do not move `FileFinder` into `src/common/fileio.h`.
- Do not rename `File.cpp` / `File.h` case in this step.
- Do not remove `src/win32/file.cpp`; it remains the Win32 implementation.

## Win32 Implementation Preservation

Keep current Win32 behavior byte-for-byte where practical:

- `CreateFile` access flags:
  - readonly: `GENERIC_READ`, `FILE_SHARE_READ`
  - read-write/create: `GENERIC_READ | GENERIC_WRITE`, no sharing
- `create`: `CREATE_ALWAYS`
- `CreateNew`: `CREATE_NEW`
- error mapping:
  - `ERROR_FILE_NOT_FOUND` -> `file_not_found`
  - `ERROR_SHARING_VIOLATION` -> `sharing_violation`
  - others -> `unknown`
- `ReadFile` / `WriteFile` byte-count return semantics.
- `SetFilePointer` with `int32` positions.
- logical origin behavior:
  - `Seek(begin)` adds `lorigin`
  - `Tellp()` subtracts `lorigin`
- `SetEndOfFile` at the current file pointer.
- `char` path API and current Windows ANSI/CP932 behavior.

The first implementation should be a no-op behavior preservation patch. Portable POSIX implementation comes later.

## Object Size / ABI Impact

Known embedded users:

- `src/pc88/diskmgr.h`
  - `DiskImageHolder` embeds `FileIO fio`.
- `diskdrv/src/diskio.h`
  - `DiskIO` embeds `FileIO file`.

External ABI risk:

- `diskdrv` is a separate extension DLL project but built from the same source tree.
- The plugin interfaces in `src/if` do not appear to expose `FileIO` directly.
- `FileIO` object layout is not obviously a public third-party ABI, but it is a cross-project compile dependency.

Design implication:

- Adding a common header that preserves class layout is low risk.
- Moving Win32 storage to an opaque pointer changes object size and should be a separate approved step.
- Any layout-changing step needs at least:
  - VS2008 `Release|Win32` rebuild.
  - diskdrv rebuild.
  - D88 mount/writeback smoke.
  - snapshot save/load smoke.

## VC2008 Impact

Constraints:

- Use C++98-compatible code.
- No `std::unique_ptr`.
- No `alignas`.
- No `<cstdint>` assumption beyond current project typedefs.
- Keep `#pragma once`, matching existing style.
- Header must compile with the current include paths:
  - `src/win32`
  - `src/common`
  - `src/if`

Important:

- If `src/common/fileio.h` uses `types.h`, include path must support both:
  - common sources including from `src/common`
  - Win32/project sources including from `src/win32`
- Because `types.h` currently lives under `src/win32`, a new common header that includes `"types.h"` still relies on include directories. This is acceptable only as an intermediate Phase 5 step, consistent with `core_headers.h`.

## PCH Impact

Current state:

- Many Win32/core sources still compile with `headers.h` PCH.
- Some `src/common` files have PCH disabled and use `core_headers.h`.

Design guidance:

- Do not force PCH changes in the same patch as FileIO header split.
- If a source already includes `headers.h`, it can keep doing so.
- If a source moves to `core_headers.h` later and needs `FileIO`, that is a separate boundary decision.
- A new `src/common/fileio.h` should not include `windows.h`.

## vcproj / dsp Impact

Current project references:

- `M88_2008.vcproj`
  - `src\Win32\File.cpp`
  - `src\Win32\File.h`
- `M88.dsp`
  - `.\src\Win32\File.cpp`
  - `.\src\Win32\File.h`
- `diskdrv/diskdrv_2008.vcproj`
  - `..\src\win32\file.cpp`
  - `..\src\Win32\File.h`
- `diskdrv/diskdrv.dsp`
  - `..\src\win32\file.cpp`
  - `..\src\Win32\File.h`

Design implications:

- Adding `src/common/fileio.h` requires adding it to:
  - `M88_2008.vcproj`
  - `M88.dsp`
  - `diskdrv/diskdrv_2008.vcproj`
  - `diskdrv/diskdrv.dsp`
- `cdif` does not currently reference `FileIO`.
- Keep existing File.cpp/File.h entries in all project files.
- Do not rename files or change path case in this step.
- `.dsp` files are CP932/legacy text; edit carefully without encoding churn.

## FileFinder Separation

Recommended:

- Leave `FileFinder` in `src/win32/file.h` for now.
- Do not include `FileFinder` in `src/common/fileio.h`.
- Later, consider:
  - `src/win32/filefinder.h`
  - or keep it in `file.h` permanently as Win32 compatibility.

Reasons:

- Current callers are Win32-side:
  - `src/win32/ui.cpp`
  - `src/win32/wincore.cpp`
- It exposes Win32 attributes and alternate names.
- Portable wildcard behavior differs from Win32.
- `.m88` module discovery is a Windows plugin/backend feature.

## Staged Implementation Order

### Step A: Header Introduction Only

- Add `src/common/fileio.h`.
- Move or duplicate only the `FileIO` class declaration into it.
- Keep `src/win32/file.h` as a wrapper that includes `../common/fileio.h` and keeps `FileFinder`.
- Keep `src/win32/file.cpp` unchanged except include path if necessary.
- Add `src/common/fileio.h` to relevant project files.
- No caller include changes.
- No object layout changes.

Verification:

- MinGW include smoke for:
  - `#include "fileio.h"`
  - `#include "file.h"`
- VS2008 `Release|Win32` rebuild.

### Step B: Low-Risk Include Migration

- Change a very small number of non-Win32 callers from `"file.h"` to `"fileio.h"` only if include paths allow it.
- Do not touch D88 first.
- Candidate low-risk inventory-only candidates:
  - none should be changed without compile proof, because most FileIO users affect runtime assets.

Recommendation:

- Skip this until Step A is verified.

### Step C: Implementation Storage Split

- Introduce a private platform implementation for `FileIO`.
- Keep Windows behavior unchanged.
- Do not add POSIX implementation yet.

Verification:

- Full VS2008 Release rebuild.
- D88/snapshot/ROM runtime smoke.
- Compare FileIO behavior with small explicit tests if a local harness is approved.

### Step D: Portable Implementation

- Add POSIX/stdio implementation behind the same API.
- Keep Windows implementation as default for existing project files.
- Decide path encoding policy before enabling non-Windows runtime.

## Recommended Next Step

If implementation is approved, do **Step A only**:

```text
Phase 5 FileIO boundary step 3 を小さく実行しろ。
src/common/fileio.h を追加し、FileIO の宣言だけを移せ。
src/win32/file.h は互換 wrapper として残し、FileFinder は src/win32/file.h に残せ。
src/win32/file.cpp の Win32 実装は維持し、ロジック変更は禁止。
必要な vcproj/dsp 参照だけ追加し、完了後 report を出せ。
```

Do not move `FileFinder`, do not rename files, and do not change `FileIO` storage layout in that same step.

## Commands Run

```sh
git status --short --branch
sed -n '1,260p' tools/refactor/phase5_fileio_inventory.md
rg -n "file\\.h|file\\.cpp|File\\.cpp|File\\.h" M88_2008.vcproj M88.dsp diskdrv/diskdrv_2008.vcproj diskdrv/diskdrv.dsp cdif/cdif_2008.vcproj cdif/cdif.dsp
rg -n '#include "file\\.h"|#include "File\\.h"|\\bFileIO\\b|\\bFileFinder\\b' src diskdrv cdif sample1 sample2 -g '*.[ch]' -g '*.cpp'
```

## Result

- Design only.
- No source code or project behavior changed.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`
