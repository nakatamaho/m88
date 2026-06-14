# Phase 5 WinCore/WinUI Operation Boundary Inventory

## Scope

- Inventory only.
- Classify operations that are already centralized in `WinCore`.
- Classify operations still owned directly by `WinUI`.
- Propose candidate VM operation APIs needed by a future SDL2 frontend.
- Document how to preserve current Windows behavior.
- Document implementation risks.
- Do not implement changes.

## Baseline

- Pushed commit:
  - `2f8eff0` `Inventory final TimeKeeper boundary state`
- Previous user-side VC2008 / VC8 Express verification after TimeKeeper cleanup passed:
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

## Current Boundary Summary

`WinCore` is already the owner of the VM-facing Windows core object.

It centralizes:

- PC88 initialization and cleanup
- device connection
- external module discovery
- emulation sequencer start/stop activation
- reset
- config application into the VM
- snapshot serialization and deserialization
- sound object ownership
- plugin interface query
- core lock/unlock

`WinUI` is still both the Win32 frontend and the high-level operation router.

It directly owns:

- Win32 window creation and message loop
- menus, accelerators, dialogs, and status display
- config load/save and menu-driven config mutation
- disk image dialog, mount, unmount, multi-disk menu state, and new-disk formatting flow
- tape image dialog and open/close flow
- snapshot slot naming and snapshot menu construction
- display mode switching, window sizing, screen capture, and window position
- command-line and drag/drop file handling
- monitor/debug window lifetime and menu routing
- input focus, key routing, mouse capture, and GUI mode state

## Operations Already Centralized In `WinCore`

Public API in `src/win32/wincore.h`:

```text
bool Init(WinUI*, HWND, Draw*, DiskManager*, WinKeyIF*, IConfigPropBase*, TapeManager*)
bool Cleanup()
void Reset()
void ApplyConfig(PC8801::Config*)
bool SaveShapshot(const char*)
bool LoadShapshot(const char*, const char* diskname = 0)
PC8801::WinSound* GetSound()
long GetExecCount()
void Wait(bool dowait)
void* QueryIF(REFIID)
void Lock()
void Unlock()
```

Implementation responsibilities:

- `Init` calls `PC88::Init`, initializes `WinSound`, connects keyboard/audio devices, discovers external modules, initializes the sequencer, and sets initial clock/speed.
- `Cleanup` stops the sequencer and releases external modules/devices.
- `Reset` locks the core and calls `PC88::Reset`.
- `ApplyConfig` maps config into sequencer clock/speed/refresh timing, joypad connection, `PC88::ApplyConfig`, sound config, and draw flip mode.
- `SaveShapshot` writes `SnapshotHeader`, current disk ids, device state, and optional zlib compression.
- `LoadShapshot` reads snapshot config/device state, applies config, resets, and optionally remounts disk ids.
- `QueryIF` provides the existing plugin ABI interface surface.
- `ConnectExternalDevices` uses `FileFinder` to discover `*.m88` modules under `m88dir`.

## Operations Still Directly Owned By `WinUI`

### Startup / Shutdown

`WinUI::InitM88` currently owns:

- `M88.ini` load via `PC8801::LoadConfig`
- status display initialization
- initial window sizing and position load
- display driver initialization
- BIOS path load
- `DiskManager` and `TapeManager` allocation/init
- keyboard interface initialization
- `WinCore::Init`
- monitor initialization
- sanity check
- `core.Wait(false)`
- command-line processing
- config application
- initial reset

`WinUI::CleanupM88` currently owns:

- config save via `PC8801::SaveConfig`
- `core.Cleanup`
- `DiskManager` and `TapeManager` deletion

### Config And Reset Routing

`WinUI::WmCommand` mutates config for:

- CPU burst / full speed related flags
- 4MHz / 8MHz clock selection
- BASIC mode selection
- debug display masks
- status bar and FDC status flags

`WinUI::ApplyConfig` then calls:

- `core.ApplyConfig`
- `keyif.ApplyConfig`
- `draw.SetPriorityLow`
- menu/status UI updates

`WinUI::Reset` owns the optional reset confirmation dialog before calling:

- `keyif.ApplyConfig`
- `core.ApplyConfig`
- `core.Reset`

### Disk Operations

`WinUI` directly calls `DiskManager` through:

- `ChangeDiskImage`
- `OpenDiskImage(const char*)`
- `OpenDiskImage(int, const char*, bool, int, bool)`
- `SelectDisk`
- `CreateDiskMenu`

Direct behaviors to preserve:

- `Unmount` before changing an image
- read-only flag from the Win32 file dialog
- missing-file new-disk prompt
- create/format flow through `WinNewDisk`
- automatic drive 2 mount for multi-disk D88 images
- multi-disk menu creation and selected-disk check state
- `snapshotchanged` invalidation

### Tape Operations

`WinUI` directly calls `TapeManager` through:

- `ChangeTapeImage`
- `OpenTapeImage`

Direct behaviors to preserve:

- close currently opened tape before choosing another tape
- Win32 file dialog filter/title
- menu label update using the tape title
- `snapshotchanged` invalidation

### Snapshot Operations

`WinCore` owns the snapshot file format and device-state save/load.

`WinUI` still owns:

- snapshot slot naming
- snapshot save/load menu construction
- `FileFinder` search for existing snapshot slots
- status messages
- disk menu refresh after load
- drive 2 remount before loading snapshots from multi-disk images

This split is intentional for now. Snapshot file format and disk remount semantics are high risk.

### Display And Capture

`WinUI` directly owns:

- fullscreen/windowed toggle
- Win32 window style changes
- status bar enable/disable
- window resize
- `WinDraw::ChangeDisplayMode`
- screen capture file naming/dialog
- writing captured BMP through `FileIO`

Display behavior should remain Win32-owned until a video backend boundary is designed.

### Input, Monitors, And UI State

`WinUI` owns:

- message loop
- keyboard and system key dispatch
- GUI mode state while menus/dialogs are open
- mouse capture and button state
- monitor/debug windows
- command-line parser
- drag/drop file routing
- PCM recording menu routing through `core.GetSound()`

These are frontend responsibilities, but several call into VM/device objects directly.

## SDL2 Frontend VM Operation API Candidates

A future SDL2 frontend likely needs a small operation facade above the VM.

Candidate operations:

```text
InitCore(draw, diskManager, tapeManager, input, configProvider)
ShutdownCore()
StartEmulation()
StopEmulation()
Reset(confirm handled by frontend)
ApplyConfig(config)
GetConfig()
SetClockMode(...)
SetBasicMode(...)
SetFullSpeed(...)
MountDisk(drive, path, readonly, diskIndex, create)
UnmountDisk(drive)
SelectDisk(drive, diskIndex)
GetDiskCount(drive)
GetDiskTitle(drive, diskIndex)
OpenTape(path)
CloseTape()
SaveSnapshot(path)
LoadSnapshot(path, optionalDiskPath)
GetSound()
GetExecCount()
LockCore()
UnlockCore()
QueryPluginInterface(iid)
```

This should be treated as a design target, not an implementation request.

Important split:

- File dialogs, menu labels, status messages, and confirmation dialogs belong to frontend code.
- D88/T88/snapshot semantics belong behind the operation boundary.
- Snapshot filename/slot policy may stay frontend-owned or become a small helper, but the snapshot file format must remain unchanged.

## Existing Windows Behavior Preservation Plan

When implementation begins, preserve the Windows path by default:

- Keep `WinUI` as the current frontend and message router.
- Keep `WinCore` public behavior unchanged until a facade is introduced.
- Keep `DiskManager` and `TapeManager` storage/lifetime unchanged at first.
- Keep `M88.ini` load/save path and format unchanged.
- Keep all Win32 dialogs and menu text in `WinUI`.
- Keep snapshot format and disk remount behavior unchanged.
- Keep external module discovery through `FileFinder` under `m88dir`.
- Keep monitor/debug windows Windows-only.
- Keep `WinSound` and `WinDraw` ownership unchanged until audio/video boundary steps.

## Implementation Risks

### Disk And Tape

Moving disk/tape operations too early can break:

- D88 writeback and resize behavior
- multi-disk image selection
- automatic drive 2 mount
- new disk creation and formatting
- T88 open/close state
- snapshot menu invalidation

### Snapshot

Snapshot work is high risk because:

- `SnapshotHeader` layout is a file format.
- load applies config and resets before loading device state.
- disk ids are saved and restored through `DiskManager`.
- Windows UI currently handles multi-disk remount before load.

### Config

Menu commands mutate `PC8801::Config` directly.

Risk areas:

- BASIC mode changes imply reset.
- clock changes imply reset.
- display/debug mask changes should not reset.
- `mainsubratio` is recalculated in `WinUI::ApplyConfig`.
- menu/status UI must stay consistent after config changes.

### External Modules

`WinCore::ConnectExternalDevices` still uses Windows module discovery and plugin loading.

The existing plugin ABI must remain stable:

- `QueryIF`
- GUIDs
- calling conventions
- factory loading behavior

### Display / Input / Sound

These are visible behavior areas:

- fullscreen/window placement
- screen capture naming and dialogs
- menu/key focus behavior
- mouse capture
- PCM dump menu state
- sound monitor connection

They should be separate boundaries, not mixed into operation routing.

## Recommended Next Step

Next safest step is design only:

```text
Phase 5 WinCore/WinUI operation boundary step 1 の設計だけ実行しろ。
WinCore の既存 public API を壊さず、
将来追加する VM operation facade の最小 API と、
WinUI から移す候補/移さない候補、
DiskManager/TapeManager/snapshot/config の段階的順序を report しろ。
実装はするな。
```

Do not implement SDL2 frontend yet.

Do not move disk/tape/snapshot code until the operation facade design is accepted.

## Future Verification Targets

For any future operation-boundary implementation:

- VC2008 / VC8 Express `Release|Win32` rebuild
- writetag CRC appears
- M88 launch
- D88 game launch
- disk access after launch
- D88 multi-disk selection if available
- T88 open if available
- snapshot save/load
- reset and BASIC mode menu changes
- 4MHz/8MHz changes
- fullscreen/windowed toggle
- screen capture
- sound playback
- PCM dump if touched
- clean shutdown
- no new warning dialog or crash
