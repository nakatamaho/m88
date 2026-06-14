# Phase 5 `CritSect` Remaining Boundary Inventory

## Scope

- Inventory only.
- Target remaining `CritSect.h` / `CriticalSection` usage in:
  - `src/common`
  - `src/pc88`
- Report:
  - include/use sites
  - shared data protected by each lock
  - thread/timing impact
  - Windows implementation preservation option
  - minimal portability boundary option
  - implementation risks
- Do not implement changes.

## Baseline

- `file.h` cleanup is considered complete for now.
- Pushed commit:
  - `7403e12` `Inventory final file.h wrapper state`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - game launch
  - sound
  - snapshot save/load
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Current `CriticalSection` Implementation

`src/win32/CritSect.h` defines:

```cpp
class CriticalSection
{
public:
	class Lock
	{
		CriticalSection& cs;
	public:
		Lock(CriticalSection& c) : cs(c) { cs.lock(); }
		~Lock() { cs.unlock(); }
	};

	CriticalSection() { InitializeCriticalSection(&css); }
	~CriticalSection() { DeleteCriticalSection(&css); }

	void lock() { EnterCriticalSection(&css); }
	void unlock() { LeaveCriticalSection(&css); }

private:
	CRITICAL_SECTION css;
};
```

Important properties:

- Win32 implementation uses `CRITICAL_SECTION`.
- RAII lock type is `CriticalSection::Lock`.
- No try-lock, timeout, condition variable, or recursive policy abstraction is exposed.
- Windows `CRITICAL_SECTION` is recursive for the owning thread; any portable replacement must preserve this if same-thread reentry can occur.

## Remaining Include Sites

Direct `CritSect.h` includes in the requested scope:

```text
src/common/soundbuf.h
src/common/sndbuf2.h
src/common/srcbuf.h
src/pc88/diskmgr.h
src/pc88/fdc.cpp
```

Additional `src/pc88` dependency:

- `src/pc88/sound.h` does not include `CritSect.h` directly, but includes `sndbuf2.h` and `srcbuf.h`, and declares `CriticalSection cs_ss`.

## `src/common` Usage

### `src/common/soundbuf.h` / `soundbuf.cpp`

Protected data:

- `Sample* buffer`
- `buffersize`
- `read`
- `write`
- `ch`
- `fillwhenempty`

Lock sites:

```text
SoundBuffer::Init
SoundBuffer::Cleanup
SoundBuffer::Put
SoundBuffer::Get
SoundBuffer::IsEmpty
```

Behavior protected:

- ring-buffer allocation/reset
- producer writes through `Put` / `PutMain`
- consumer reads through `Get`
- empty-state query

Thread/timing impact:

- This is audio-buffering code.
- Lock granularity affects audio callback/output latency and underflow behavior.
- `Get` may call `PutMain` while holding the same lock; any replacement must allow the current call structure.

### `src/common/sndbuf2.h` / `sndbuf2.cpp`

Protected data:

- `SoundSource* source`
- `Sample* buffer`
- `buffersize`
- `read`
- `write`
- `ch`
- `fillwhenempty`

Lock sites:

```text
SoundBuffer2::Init
SoundBuffer2::Cleanup
SoundBuffer2::Fill
SoundBuffer2::Get
SoundBuffer2::IsEmpty
```

Behavior protected:

- source attachment/reset
- ring-buffer allocation/reset
- buffered reads/writes
- empty-state query

Thread/timing impact:

- Also audio-buffering code.
- `FillMain` calls `GetAvail`, and `Get` also calls `GetAvail`; currently those calls occur while the public method holds the lock.
- `GetAvail` itself is inline and does not lock. This is deliberate within the current internal call pattern.

### `src/common/srcbuf.h` / `srcbuf.cpp`

Class:

- `SamplingRateConverter`

Protected data:

- `SoundSourceL* source`
- `SampleL* buffer`
- `float* h2`
- `buffersize`
- `read`
- `write`
- `ch`
- `fillwhenempty`
- filter/resampler state:
  - `n`
  - `nch`
  - `oo`
  - `ic`
  - `oc`
  - `outputrate`

Lock sites:

```text
SamplingRateConverter::GetAvail
SamplingRateConverter::Init
SamplingRateConverter::Cleanup
SamplingRateConverter::Fill
SamplingRateConverter::Get
```

Behavior protected:

- source attachment/reset
- buffer/filter allocation and deletion
- ring-buffer state
- sample-rate conversion state

Thread/timing impact:

- High audio sensitivity.
- `Get` may call `FillMain` while holding the lock.
- Resampling math and buffer movement must not be reordered or widened casually.

## `src/pc88` Usage

### `src/pc88/sound.h` / `sound.cpp`

Dependency path:

- `sound.h` includes `sndbuf2.h` and `srcbuf.h`.
- It declares `CriticalSection cs_ss`.

Protected data:

- `SSNode* sslist`
- connected `ISoundSource` nodes

Lock sites:

```text
Sound::Get(Sample* dest, int nsamples)
Sound::Get(SampleL* dest, int nsamples)
Sound::Connect
Sound::Disconnect
```

Behavior protected:

- mixing source list traversal
- source connect/disconnect
- calls into `ISoundSource::Mix`

Thread/timing impact:

- High audio sensitivity.
- Mixing may happen from output/audio path while source list changes happen from emulation/config/plugin paths.
- Replacement must preserve source-list consistency and avoid changing callback latency.

### `src/pc88/diskmgr.h` / `diskmgr.cpp`

Protected data:

- `DiskManager::holder[max_drives]`
- `DiskManager::drive[max_drives]`
- mounted `DiskImageHolder` references
- `Drive::disk`
- `Drive::fdu`
- `Drive::holder`
- `Drive::index`
- `Drive::sizechanged`
- `Drive::trackpos`
- `Drive::tracksize`
- `Drive::modified`

Lock sites in `DiskManager`:

```text
DiskManager::IsImageOpen
DiskManager::Mount
DiskManager::Unmount
DiskManager::UpdateDrive
```

Exposed lock:

```cpp
CriticalSection& GetCS() { return cs; }
```

Behavior protected:

- mount/unmount
- holder sharing between drives
- disk image read/write/update
- modified track writeback
- FDU/FloppyDisk access serialized with FDC operations

Thread/timing impact:

- Disk access can happen from UI commands and emulation/FDC paths.
- Lock ordering matters because `Unmount`/`Mount` can perform file I/O and FDU mutation while holding the lock.
- Writeback timing affects D88 persistence and disk access behavior.

### `src/pc88/fdc.cpp`

Direct include:

```cpp
#include "CritSect.h"
```

Lock target:

```cpp
CriticalSection::Lock lock(diskmgr->GetCS());
```

Lock sites:

```text
FDC::ReadData
FDC::SeekEvent
FDC::GetDeviceStatus
FDC::CmdWriteData
FDC::WriteData
FDC::ReadID
FDC::WriteID
FDC::ReadDiagnostic
```

Behavior protected:

- FDC access to `DiskManager` / `FDU`
- read/write sector operations
- seek/event status updates involving drive state
- ID read/write and diagnostic reads

Thread/timing impact:

- Very high behavior sensitivity.
- FDC timing is scheduler-driven and disk-wait dependent.
- `fdc.cpp` is explicitly listed in `refactor-instructions.md` as logic-change prohibited.

## Windows Implementation Preservation Option

Recommended default for the next implementation step:

- Keep `src/win32/CritSect.h` and its `CRITICAL_SECTION` behavior unchanged.
- Do not replace with `std::mutex` or `std::recursive_mutex` yet.
- Do not change lock scopes.
- Do not change any FDC/DiskManager/SoundBuffer logic.

Minimal safe work that can still help boundaries:

- Add a neutral wrapper include path, for example:

```text
src/common/core_critsect.h
```

with Windows builds including:

```cpp
#include "../win32/CritSect.h"
```

Then migrate only include directives, not class names or behavior.

This would keep the exact `CriticalSection` class and `CriticalSection::Lock` semantics for Windows while moving common/core headers away from a direct `src/win32` include name.

## Portable Boundary Option

Later, after the wrapper include path is proven:

- Keep public type name:
  - `CriticalSection`
  - `CriticalSection::Lock`
- Provide platform-specific implementation behind one header.
- Windows backend:
  - same `CRITICAL_SECTION` implementation.
- Non-Windows backend:
  - likely recursive mutex equivalent, not plain non-recursive mutex.

Potential implementation models:

1. Header-only backend selection.
   - `core_critsect.h` defines/includes platform implementation.
   - Low project-file churn.
   - Must be careful with `<mutex>` availability; VC2008 does not provide C++11 `std::mutex`.

2. Platform implementation headers.
   - `src/win32/CritSect.h` stays Windows implementation.
   - later `src/posix/critsect_posix.h` or similar can provide pthread recursive mutex.
   - More explicit, but requires build-system decisions.

3. Opaque implementation pointer.
   - Hides backend storage from common headers.
   - Changes object size and allocation behavior.
   - Higher risk for embedded member fields like `SoundBuffer::cs` and `DiskManager::cs`.

## Implementation Risks

### Audio Risks

- Lock overhead or semantics changes can affect underruns, latency, and sound stability.
- Recursive call patterns exist under locked public methods (`Get`/`Fill` -> internal helpers).
- Source-list locking in `Sound` protects calls into plugin/external sound sources.
- Runtime verification must include actual audio output.

### Disk / FDC Risks

- Lock scope changes can corrupt D88 writes or modified track writeback.
- FDC scheduler events access disk state while emulation timing is active.
- Disk access needs runtime verification with D88 game boot and disk-access activity.
- `fdc.cpp` logic must not be changed in a boundary step.

### ABI / Object Layout Risks

- `CriticalSection` is embedded by value in several classes.
- Changing the implementation storage changes object size/layout.
- Snapshot format does not appear to serialize these lock fields directly, but object layout changes can still affect build assumptions and binary compatibility inside one build.
- A wrapper include path that preserves the exact class definition avoids this risk.

### VC2008 Risks

- C++11 mutex APIs are not available.
- Keep Windows implementation as `CRITICAL_SECTION` for VC2008.
- If project files add new headers, add only header references; do not change PCH unless source includes change require it.

## Minimal Next Implementation Step

Recommended next step if implementation is approved:

```text
Phase 5 CritSect include boundary step 1 を小さく実行しろ。
src/common/core_critsect.h を追加し、Windows build では既存の src/win32/CritSect.h を include するだけにしろ。
src/common/soundbuf.h, src/common/sndbuf2.h, src/common/srcbuf.h の include だけを CritSect.h から core_critsect.h に置換しろ。
CriticalSection の実装、型名、Lock API、ロジック、lock scope 変更は禁止。
src/pc88/diskmgr.h と src/pc88/fdc.cpp は次 step に残せ。
必要な project file header 参照だけ追加し、完了後 report を出せ。
```

Why split common first:

- These files already had Phase 5 compile smoke after the earlier `CritSect.h` boundary work.
- It reduces direct Win32 include naming in `src/common`.
- It does not touch `fdc.cpp` or disk writeback behavior.

## User-Side Verification For Future Implementation

For common audio-buffer include boundary:

- `tools\windows\build_vc2008.cmd Release`
- Confirm `writetag` CRC appears.
- Launch M88.
- Start a game.
- Confirm sound output.
- Confirm no new warning dialog or crash.

For later disk/FDC boundary:

- Same build checks.
- Launch M88.
- Boot a D88 game.
- Reach a disk-access path.
- Confirm disk format/write/read paths if practical.
- Confirm snapshot save/load still works.

## Conclusion

`FileIO` / `FileFinder` cleanup can stop here for now.

The remaining `CritSect` debt should be handled as an include-boundary split first, while preserving the current Win32 `CRITICAL_SECTION` implementation exactly.
