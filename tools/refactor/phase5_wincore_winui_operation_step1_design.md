# Phase 5 WinCore/WinUI Operation Boundary Step 1 Design

## Scope

- Design only.
- Do not change source code or project files.
- Keep the existing `WinCore` public API compatible.
- Propose a future VM operation facade with the smallest practical API.
- Identify which operations should move out of `WinUI` later, and which should stay in `WinUI`.
- Define a safe order for DiskManager, TapeManager, snapshot, and config work.

## Baseline

- Pushed commit:
  - `7bed477` `Inventory WinCore WinUI operation boundary`
- Previous user-side VC2008 / VC8 Express verification passed before this design step:
  - `Release|Win32` rebuild
  - writetag CRC
  - launch
  - D88 game
  - disk access
  - sound
  - snapshot save/load
  - clean shutdown
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Design Goal

Introduce a small VM operation facade later without breaking the current Windows frontend.

The facade should not replace `WinCore` immediately. It should initially sit next to the current `WinCore` API and provide operation-shaped wrappers that `WinUI` can adopt gradually.

The first implementation step after this design should be additive and should keep all current `WinUI` call paths working.

## Compatibility Rule

Do not remove or change these existing `WinCore` methods during the first operation-boundary steps:

```text
bool Init(WinUI*, HWND, Draw*, DiskManager*, WinKeyIF*, IConfigPropBase*, TapeManager*)
bool Cleanup()
void Reset()
void ApplyConfig(PC8801::Config*)
bool SaveShapshot(const char*)
bool LoadShapshot(const char*, const char* diskname = 0)
PC8801::WinSound* GetSound()
long GetExecCount()
void Wait(bool)
void* QueryIF(REFIID)
void Lock()
void Unlock()
```

Reason:

- `WinUI`, monitor windows, sound monitor, plugins, and sequencing already depend on this shape.
- Keeping this API stable makes each later change revertable.
- SDL2-readiness improves by adding a clearer facade, not by rewriting working Windows code.

## Proposed Minimum Facade Shape

Preferred name for a later header:

```text
src/win32/vmops.h
```

This should stay Windows-side at first because the initial implementation will still use Windows-specific `WinCore`, `WinSound`, `WinKeyIF`, `IConfigPropBase`, and project files.

Candidate class:

```text
class VMOperations
{
public:
    bool Init(...same objects currently passed to WinCore...);
    bool Cleanup();

    void Start();
    void Stop();
    void Reset();

    void ApplyConfig(PC8801::Config* config);
    PC8801::Config* GetConfig();

    bool MountDisk(uint drive, const char* path, bool readonly, int index, bool create);
    bool UnmountDisk(uint drive);
    bool SelectDisk(uint drive, int index);
    uint GetNumDisks(uint drive);
    int GetCurrentDisk(uint drive);
    const char* GetDiskTitle(uint drive, uint index);
    bool IsDiskImageOpen(const char* path);
    bool AddDisk(uint drive, const char* title, uint type);
    bool FormatDisk(uint drive);

    bool OpenTape(const char* path);
    bool CloseTape();
    bool IsTapeOpen();

    bool SaveSnapshot(const char* path);
    bool LoadSnapshot(const char* path, const char* diskPath);

    PC8801::WinSound* GetSound();
    long GetExecCount();
    void Lock();
    void Unlock();
    void* QueryIF(REFIID iid);
};
```

This is intentionally close to the current concrete objects. The first facade should reduce `WinUI` reach into VM objects without trying to become fully portable.

## What Should Move Later

Move later, in small steps:

- `core.Wait(false)` / stop-start naming:
  - `WinUI` can call `ops.Start()` instead of `core.Wait(false)`.
  - `ops.Stop()` can map to `core.Wait(true)` if needed.

- reset dispatch:
  - `WinUI` should keep the confirmation dialog.
  - the actual reset operation can become `ops.Reset()`.

- VM config apply:
  - `WinUI` can keep menu mutation and UI updates.
  - actual VM apply can become `ops.ApplyConfig(&config)`.

- DiskManager direct calls:
  - `Mount`
  - `Unmount`
  - `GetNumDisks`
  - `GetCurrentDisk`
  - `GetImageTitle`
  - `IsImageOpen`
  - `AddDisk`
  - `FormatDisk`

- TapeManager direct calls:
  - `Open`
  - `Close`
  - `IsOpen`

- snapshot core calls:
  - `core.SaveShapshot`
  - `core.LoadShapshot`

## What Should Stay In `WinUI`

Keep in `WinUI`:

- Win32 window creation
- message loop
- menus and accelerators
- confirmation dialogs
- file open/save dialogs
- status display messages
- snapshot slot menu construction
- disk menu construction
- tape menu label updates
- screen capture file dialog and generated BMP filename policy
- fullscreen/windowed Win32 style changes
- monitor/debug windows
- command-line parsing for now
- drag/drop file routing for now
- `M88.ini` load/save for the first operation-boundary steps

Reason:

- These are frontend policies or Win32 UI behaviors.
- Moving them into a VM facade would make the facade platform-specific and harder to reuse from SDL2.

## DiskManager Step Order

Disk work should be staged carefully because D88 writeback, multi-disk selection, and snapshot restore are sensitive.

Recommended sequence:

1. Design only, this document.
2. Add additive `VMOperations` wrappers around existing `DiskManager` calls.
3. Change only one low-risk `WinUI` read operation to use the wrapper:
   - candidate: `GetNumDisks` in menu/snapshot naming code.
4. Change `CreateDiskMenu` reads:
   - `GetNumDisks`
   - `GetImageTitle`
   - `GetCurrentDisk`
5. Change `SelectDisk` to use wrapper `SelectDisk`.
6. Change `OpenDiskImage` mount path to use wrapper `MountDisk`.
7. Change `ChangeDiskImage` unmount/new-disk/format flow last.

Do not move the Win32 file dialog, read-only dialog flag handling, or `WinNewDisk` dialog into the facade.

## TapeManager Step Order

Tape is smaller than disk but still affects snapshot naming and runtime state.

Recommended sequence:

1. Add wrappers:
   - `OpenTape`
   - `CloseTape`
   - `IsTapeOpen`
2. Change snapshot naming `tapemgr->IsOpen()` first.
3. Change `OpenTapeImage` to call `OpenTape`.
4. Change `ChangeTapeImage` `Close` call last.

Do not move the Win32 file dialog or menu label update into the facade.

## Snapshot Step Order

Snapshot file format must remain unchanged.

Recommended sequence:

1. Add wrappers:
   - `SaveSnapshot(path)` -> current `WinCore::SaveShapshot(path)`
   - `LoadSnapshot(path, diskPath)` -> current `WinCore::LoadShapshot(path, diskPath)`
2. Change `WinUI::SaveSnapshot` to use wrapper.
3. Change `WinUI::LoadSnapshot` to use wrapper.
4. Keep snapshot slot naming and snapshot menu discovery in `WinUI`.
5. Keep drive 2 pre-remount behavior in `WinUI` until disk wrapper steps are proven.

Do not change:

- `SNAPSHOT_ID`
- `SnapshotHeader`
- zlib compression behavior
- device status save/load order
- config fields restored from snapshot

## Config Step Order

Config is high risk because menu commands intentionally imply different behavior.

Recommended sequence:

1. Keep `PC8801::LoadConfig`, `SaveConfig`, and `LoadConfigDirectory` in `WinUI`.
2. Add wrapper only for applying a config to the VM:
   - `ApplyConfig(PC8801::Config*)`
3. Keep `WinUI::ApplyConfig` as the policy owner:
   - `mainsubratio` recalculation
   - debug mask cleanup
   - `keyif.ApplyConfig`
   - `draw.SetPriorityLow`
   - menu text updates
   - status window updates
4. Later split config persistence only after an SDL2 config path decision exists.

Do not move `M88.ini` path semantics yet.

## Suggested First Implementation Step

After this design is accepted, the safest implementation step is additive:

```text
Phase 5 WinCore/WinUI operation boundary step 2 を小さく実行しろ。
src/win32/vmops.h と src/win32/vmops.cpp を追加し、
既存 WinCore / DiskManager / TapeManager への thin wrapper だけを実装しろ。
WinUI の呼び出し元変更は禁止。
WinCore public API、DiskManager/TapeManager 実装、snapshot/config ロジック変更は禁止。
必要な project file 参照だけ追加し、完了後 report を出せ。
```

This gives a compile-tested facade before moving any UI calls.

## Risks And Stop Points

Stop and ask before implementation if any of these decisions are needed:

- Whether `VMOperations` should live in `src/win32` or `src/common`.
- Whether `DiskManager` lifetime should move from `WinUI` to the facade.
- Whether `TapeManager` lifetime should move from `WinUI` to the facade.
- Whether `M88.ini` config persistence should become portable now.
- Whether snapshot slot naming should stay frontend-owned.
- Whether SDL2 should use the same `DiskManager` and `TapeManager` classes directly.

Recommended answers for now:

- keep `VMOperations` in `src/win32`
- keep object lifetimes in `WinUI`
- keep config persistence in `WinUI`
- keep snapshot slot naming in `WinUI`
- keep SDL2 as a later consumer after the Windows facade is proven

## Verification For Future Implementation

For the first additive facade implementation:

- VC2008 / VC8 Express `Release|Win32` rebuild
- writetag CRC appears
- M88 launch
- D88 game launch
- disk access
- sound
- snapshot save/load
- clean shutdown
- no new warning dialog or crash

For later disk call migration:

- D88 game launch
- disk access after mount
- multi-disk image selection if available
- new disk create/format if touched
- snapshot load after disk mount

For later tape call migration:

- T88 open if available
- snapshot naming with tape open

For later config call migration:

- reset
- BASIC mode changes
- 4MHz/8MHz changes
- CPU burst/fullspeed toggle
- status bar/FDC status toggles
