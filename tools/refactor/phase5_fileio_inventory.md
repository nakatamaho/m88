# Phase 5 FileIO Boundary Inventory

Recorded for `refactor-instructions.md` Phase 5.

## Scope

- Inventory only.
- Do not implement changes.
- Inspect `src/win32/file.*` API and Win32 dependencies.
- Identify callers and behavior risks for ROM, D88/T88, snapshot, fmgen, UI/export, diskdrv, and module discovery.
- Propose a minimal portable boundary while preserving existing Windows behavior.

## Files Changed

- `tools/refactor/phase5_fileio_inventory.md`

## Current API

`src/win32/file.h` exposes two classes:

- `FileIO`
  - flags: `open`, `readonly`, `create`
  - seek methods: `begin`, `current`, `end`
  - errors: `success`, `file_not_found`, `sharing_violation`, `unknown`
  - methods:
    - `Open(const char* filename, uint flg = 0)`
    - `CreateNew(const char* filename)`
    - `Reopen(uint flg = 0)`
    - `Close()`
    - `GetError()`
    - `Read(void* dest, int32 len)`
    - `Write(const void* src, int32 len)`
    - `Seek(int32 fpos, SeekMethod method)`
    - `Tellp()`
    - `SetEndOfFile()`
    - `GetFlags()`
    - `SetLogicalOrigin(int32 origin)`
- `FileFinder`
  - `FindFile(char* search)`
  - `FindNext()`
  - `GetFileName()`
  - `GetFileAttr()`
  - `GetAltName()`

## Win32 Dependencies

`FileIO` stores Win32 state directly in the header:

- `HANDLE hfile`
- `char path[MAX_PATH]`

`FileFinder` stores Win32 state directly in the header:

- `HANDLE hff`
- `WIN32_FIND_DATA wfd`
- `DWORD` return type for attributes

`file.cpp` uses:

- `CreateFile`
- `CloseHandle`
- `ReadFile`
- `WriteFile`
- `SetFilePointer`
- `SetEndOfFile`
- `GetLastError`
- `ERROR_FILE_NOT_FOUND`
- `ERROR_SHARING_VIOLATION`
- Win32 sharing semantics:
  - readonly opens use `GENERIC_READ` and `FILE_SHARE_READ`
  - read-write/create opens use `GENERIC_READ | GENERIC_WRITE` and no sharing
  - `create` maps to `CREATE_ALWAYS`
  - `CreateNew` maps to `CREATE_NEW`

`FileFinder` uses:

- `FindFirstFile`
- `FindNextFile`
- `FindClose`
- `WIN32_FIND_DATA::cFileName`
- `WIN32_FIND_DATA::cAlternateFileName`
- `WIN32_FIND_DATA::dwFileAttributes`

## Behavior To Preserve

- `char*` path API and existing CP932/ANSI path behavior on Windows.
- Relative paths resolve from the current process working directory.
- ROM lookup behavior:
  - `pc88.rom`
  - `n88.rom`, `n80.rom`, `n88_0.rom` through `n88_3.rom`
  - optional ROMs such as `jisyo.rom`, `cdbios.rom`, `n80_2.rom`, `n80_3.rom`, `e1.rom` through `e8.rom`
  - `PC88.ROM`, `DISK.ROM`
  - `FONT80SR.ROM`, `FONT.ROM`, `KANJI1.ROM`
- Open failure classification where callers depend on it:
  - `file_not_found`
  - `sharing_violation`
  - `unknown`
- `readonly` fallback behavior for D88:
  - try read-write first unless requested readonly
  - if read-write fails, retry readonly
  - mark holder readonly when readonly fallback succeeds
- Existing no-share write semantics for writable images and snapshot/output files.
- `create` truncation semantics from `CREATE_ALWAYS`.
- `CreateNew` no-overwrite semantics from `CREATE_NEW`.
- `Read` and `Write` return byte counts, `-1` on failure.
- `Seek(begin)` honors `SetLogicalOrigin`; `Tellp()` subtracts logical origin.
- `SetEndOfFile()` truncates/extends at current file pointer.
- D88 multi-disk logical origin behavior must be preserved exactly.
- 32-bit signed file offsets remain the current behavioral limit.
- File enumeration order is whatever Win32 returns today; do not sort unless explicitly approved.

## Caller Inventory

### Core ROM / Font / Optional ROM

- `src/pc88/memory.cpp`
  - loads required and optional ROM files.
  - fills short optional ROM reads with `0xff`.
  - uses relative file names directly.
- `src/pc88/subsys.cpp`
  - loads `PC88.ROM` or `DISK.ROM`.
  - falls back to a tiny halt stub when disk ROM is missing.
- `src/pc88/crtc.cpp`
  - loads `FONT80SR.ROM`, `FONT.ROM`, or `KANJI1.ROM`.
- `src/pc88/kanjirom.cpp`
  - loads kanji ROM data from a caller-provided filename.

Risk:

- Changing path encoding, case sensitivity expectations, or current-directory rules can break ROM discovery.
- Short-read handling differs by caller; FileIO should not try to normalize reads.

### D88 / Raw Disk Images

- `src/pc88/diskmgr.h`
  - embeds `FileIO` in `DiskImageHolder`.
- `src/pc88/diskmgr.cpp`
  - opens disk images read-write, readonly fallback, or create.
  - parses D88 headers and raw image headers.
  - writes modified tracks in place when track size fits.
  - rewrites and truncates image file when disk size changes.
  - uses `SetLogicalOrigin` for multi-disk images.
  - uses `SetEndOfFile` after moving following disk images.

Risk:

- D88 writeback behavior depends on byte-accurate seek/write/truncate semantics.
- Sharing behavior matters: writable images currently open with no sharing.
- `SetLogicalOrigin` is part of the D88 multi-image abstraction; moving it incorrectly can corrupt multi-disk images.
- The existing `DiskImageHolder::SetDiskSize` appears to update following disk positions by `sizemove`; this is existing behavior and must not be touched in a FileIO boundary step.

### T88 Tape Images

- `src/pc88/tapemgr.cpp`
  - opens T88 readonly.
  - checks the 24-byte `PC-8801 Tape Image(T88)` header.
  - reads tagged records into memory.

Risk:

- Read byte counts and EOF behavior must stay unchanged.
- Tape parsing is sensitive to binary layout and short reads.

### Snapshot

- `src/win32/wincore.cpp`
  - save: `Open(filename, FileIO::create)`, writes `SnapshotHeader` and raw/compressed state.
  - load: readonly open, strict header/version checks, then read state.

Risk:

- Snapshot file format is raw structure data plus optional compressed payload.
- Any change to write truncation, read counts, or binary mode would break compatibility.
- Snapshot remains Win32-side today, but it is a high-risk file-format path.

### fmgen / OPNA Rhythm Samples

- `src/devices/opna.cpp`
  - loads `2608_BD.WAV`, `2608_SD.WAV`, `2608_TOP.WAV`, `2608_HH.WAV`, `2608_TOM.WAV`, `2608_RIM.WAV`.
  - falls back to `2608_RYM.WAV` for the last rhythm file path.
  - parses RIFF/WAV chunks manually using `Seek`/`Read`.

Risk:

- Existing code assumes byte-exact WAV chunk traversal.
- Do not alter sample loading, endianness assumptions, or path concatenation in a FileIO boundary step.

### UI / Export / Diagnostics

- `src/win32/ui.cpp`
  - checks whether selected D88 file exists before creating.
  - writes screenshots/BMP data with `FileIO::create`.
- `src/win32/memmon.cpp`
  - writes 64KB memory image as `.bin`.
- `src/win32/filetest.cpp`
  - computes CRC-like validation over a readonly file.

Risk:

- UI behavior depends on `GetError() == file_not_found`.
- `create` must continue truncating destination files.

### FileFinder

- `src/win32/ui.cpp`
  - enumerates snapshot slots.
- `src/win32/wincore.cpp`
  - enumerates `*.m88` extension modules under `m88dir`.

Risk:

- Module discovery is Win32 plugin/backend behavior.
- Enumeration result names are passed to `ExtendModule::Create`.
- `FileFinder` also exposes short 8.3 alternate names and Win32 attributes, even if current callers mostly use names.

### diskdrv Extension

- `diskdrv/src/diskio.h`
- `diskdrv/src/diskio.cpp`
  - embeds `FileIO`.
  - exposes guest-side read/write file commands.
  - reads up to 64KB from host files.
  - writes host files with `FileIO::create`.

Risk:

- This is an extension module interface path, not only emulator core.
- Error codes (`err = 53`, `60`, `64`) depend on FileIO success/failure.

## Impact By File Category

- D88:
  - high impact; read/write/truncate/logical-origin path.
- T88:
  - medium impact; readonly binary parser.
- ROM/font:
  - high user-visible impact; startup depends on required ROMs.
- Snapshot:
  - high compatibility impact; raw binary format.
- fmgen/OPNA rhythm:
  - medium impact; optional audio samples and manual WAV parser.
- UI exports:
  - low to medium impact; screenshot/memory dump output.
- Plugin/module discovery:
  - high Win32-backend impact; FileFinder is tied to `.m88` DLL discovery.
- diskdrv:
  - medium impact; extension command behavior.

## Minimal Portable Boundary Proposal

Do not change callers first. Keep the public `FileIO` API stable and hide platform-specific state behind a small implementation boundary.

Suggested staged approach:

1. Split platform declarations without behavior change.
   - Keep `FileIO` public API and enums exactly as-is.
   - Move Win32-specific storage out of the public header only after a dedicated ABI check.
   - Candidate: `src/common/fileio.h` for API, `src/win32/file_win32.cpp` for current implementation.
2. If moving storage is too risky for plugin ABI or project churn, first keep `src/win32/file.h` as a compatibility wrapper that includes the new API.
3. Add a portable implementation only after the API is stable.
   - POSIX implementation can use `fopen`/`fread`/`fwrite`/`fseek`/`ftell` or file descriptors.
   - It must emulate the existing open/create/reopen/error semantics as closely as possible.
4. Treat `FileFinder` separately from `FileIO`.
   - FileFinder is mostly Win32 backend/module discovery.
   - Portable enumeration should be a separate interface because directory wildcard behavior differs across platforms.

## Decisions Needed Before Implementation

- Should Windows continue using ANSI `CreateFileA` semantics through the current `CreateFile` macro, or should Unicode paths be considered later?
- Should portable non-Windows builds preserve CP932 byte paths or treat paths as UTF-8 bytes?
- Should `FileFinder` remain Win32-only for plugin discovery until non-Windows plugin support is designed?
- Should `FileIO` object size/layout be considered part of any external ABI? It is included by `diskdrv`, and `DiskImageHolder` embeds it.
- Should D88 writeback paths be tested manually before and after any FileIO implementation change?

## Verification Requirements For Future Implementation

- VS2008 / VC8 Express `Release|Win32` rebuild.
- Existing Debug link status should be recorded separately if `ddraw.lib` remains unavailable.
- Startup with ROM files in the executable/current directory.
- D88:
  - mount existing image readonly.
  - mount writable image.
  - modify disk contents enough to exercise writeback.
  - multi-disk image selection.
  - create new disk image from UI path.
- T88 open and playback/position smoke if available.
- Snapshot:
  - save.
  - load newly saved snapshot.
  - load an older snapshot if available.
- Optional audio sample path:
  - OPNA rhythm sample load when files are present.
  - absence of samples remains non-fatal.
- UI exports:
  - screenshot save.
  - memory dump save.
- Module discovery:
  - `.m88` module enumeration still works on Windows.

## Commands Run

```sh
git status --short --branch
sed -n '1,240p' src/win32/file.h
sed -n '1,260p' src/win32/file.cpp
rg -n '\bFileIO\b|#include "file\.h"|#include "File\.h"' src cdif diskdrv sample1 sample2 -g '*.[ch]' -g '*.cpp'
sed -n '1,180p' src/pc88/tapemgr.cpp
sed -n '1,360p' src/pc88/diskmgr.cpp
sed -n '360,880p' src/pc88/diskmgr.cpp
sed -n '200,280p' src/win32/wincore.cpp
sed -n '360,430p' src/pc88/crtc.cpp
sed -n '1030,1145p' src/pc88/memory.cpp
sed -n '80,115p' src/pc88/subsys.cpp
sed -n '1270,1345p' src/devices/opna.cpp
rg -n 'FileFinder|FindFile|FindNext|GetFileName|GetAltName|GetFileAttr' src cdif diskdrv sample1 sample2 -g '*.[ch]' -g '*.cpp'
sed -n '1888,1922p' src/win32/ui.cpp
sed -n '340,370p' src/win32/wincore.cpp
sed -n '1,90p' src/pc88/diskmgr.h
sed -n '1,95p' diskdrv/src/diskio.h
sed -n '170,250p' diskdrv/src/diskio.cpp
```

## Result

- Inventory only.
- No source code or project behavior changed.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Recommendation

The next implementation should not move `FileIO` directly into `common` in one patch. The safest next step is a design-only or very small compatibility-wrapper slice:

1. Add a report-only proposal for `FileIO` header split and object-layout risk.
2. Then, if approved, introduce a new neutral header while leaving `src/win32/file.h` as the include path used by existing callers.
3. Only later move Win32-specific storage and implementation behind a platform file.
