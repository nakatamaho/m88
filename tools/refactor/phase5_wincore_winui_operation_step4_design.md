# Phase 5 WinCore/WinUI Operation Boundary Step 4 Design

## Scope

- Design only.
- Do not change source code or project files.
- Decide how `WinUI` should create and destroy `VMOperations`.
- Avoid owning two `WinCore` instances.
- Preserve the existing `WinCore core` member in `WinUI`.
- Treat `VMOperations` as a reference wrapper around existing objects.
- Report effects on monitor initialization, `WinSound` access, and `DiskManager` / `TapeManager` lifetime.

## Baseline

- Pushed commit:
  - `f9fa700` `Record WinUI VM facade hold verification`
- Current verified state:
  - `VMOperations` exists in `src/win32`
  - `WinUI` holds `VMOperations* vmops`
  - no `WinUI` call sites use `vmops` yet
  - user-side VS2008 / VC8 Express `Release|Win32` build and runtime smoke passed after `0ab7efc`
- Local MSVC/VC8 build is not available in this WSL environment.

## Current Problem

`VMOperations` currently owns a `WinCore` member:

```text
WinCore core;
DiskManager* diskmgr;
TapeManager* tapemgr;
```

`WinUI` already owns the active VM object:

```text
WinCore core;
DiskManager* diskmgr;
TapeManager* tapemgr;
```

If `WinUI` simply allocates `new VMOperations`, the program gets a second `WinCore` object. Even if unused, that is not a safe no-op because `WinCore` construction/destruction and cleanup are VM lifecycle code.

Therefore, the next implementation should change `VMOperations` from owner to reference wrapper.

## Required Ownership Direction

Keep ownership as:

```text
WinUI owns WinCore core
WinUI owns DiskManager* diskmgr
WinUI owns TapeManager* tapemgr
WinUI owns VMOperations* vmops
VMOperations references WinCore*
VMOperations references DiskManager*
VMOperations references TapeManager*
```

Do not make `VMOperations` own:

- `WinCore`
- `DiskManager`
- `TapeManager`
- `WinDraw`
- `WinKeyIF`
- `WinConfig`

This preserves current Windows behavior and keeps `VMOperations` as an operation facade only.

## Proposed `VMOperations` Shape

Change the private data from:

```text
WinCore core;
DiskManager* diskmgr;
TapeManager* tapemgr;
```

to:

```text
WinCore* core;
DiskManager* diskmgr;
TapeManager* tapemgr;
```

Recommended setup API:

```text
void Bind(WinCore* core, DiskManager* diskmgr, TapeManager* tapemgr);
void Unbind();
bool IsBound() const;
```

Existing operation methods should become thin calls through `core`, `diskmgr`, and `tapemgr`.

Do not call `WinCore::Init` from `VMOperations` after this conversion. `WinUI::InitM88` should continue to initialize `core` directly for now.

## Creation And Destruction Timing

Recommended minimal implementation:

1. `WinUI::WinUI`
   - keep `vmops(0)`.

2. `WinUI::InitM88`
   - after `diskmgr` and `tapemgr` are allocated
   - before or after `core.Init`
   - allocate `vmops = new VMOperations`
   - call `vmops->Bind(&core, diskmgr, tapemgr)`

3. `WinUI::CleanupM88`
   - before deleting `diskmgr` / `tapemgr`
   - call `vmops->Unbind()`
   - delete `vmops`
   - set `vmops = 0`
   - then continue current cleanup order

4. `WinUI::~WinUI`
   - optionally guard-delete `vmops` if non-null
   - this is defensive only; normal cleanup should happen in `CleanupM88`

This creates no second VM instance.

## Cleanup Ordering

Current cleanup order:

```text
PC8801::SaveConfig(&cfg, m88ini, true);
core.Cleanup();
delete diskmgr;
delete tapemgr;
```

Recommended future order:

```text
PC8801::SaveConfig(&cfg, m88ini, true);
if (vmops) {
    vmops->Unbind();
    delete vmops;
    vmops = 0;
}
core.Cleanup();
delete diskmgr;
delete tapemgr;
```

Reason:

- `VMOperations` should stop referencing `DiskManager` / `TapeManager` before they are deleted.
- `VMOperations` must not call `core.Cleanup`; current `WinUI` still owns that lifecycle.

Alternative:

```text
core.Cleanup();
vmops->Unbind();
delete vmops;
```

This is less clear because the facade would keep a pointer to a cleaned-up `WinCore` longer than necessary. Prefer unbind before `core.Cleanup`.

## Monitor Initialization Impact

Current monitor initialization depends directly on the active `WinCore`:

```text
opnmon.Init(core.GetOPN1(), core.GetSound());
memmon.Init(&core);
codemon.Init(&core);
basmon.Init(&core);
regmon.Init(&core);
iomon.Init(&core);
core.GetSound()->SetSoundMonitor(&opnmon);
```

Do not change this in the next implementation.

Reason:

- Monitor windows are debug/inspection tools and depend on `WinCore` / `PC88` internals.
- Moving them through `VMOperations` is not needed for SDL2 frontend readiness.
- The next step should prove object lifetime only.

Future option:

- keep monitors permanently Windows-only and `WinCore`-direct
- or add debug-specific facade methods much later

## `WinSound` Access Impact

Current sound access:

```text
core.GetSound()
```

Used for:

- sound monitor connection
- PCM dump menu state
- PCM dump start/end

Do not migrate this in the next implementation.

Reason:

- `WinSound` is Windows-specific.
- SDL2 audio boundary should be handled separately.
- Early migration through `VMOperations` would not make sound portable.

The existing `VMOperations::GetSound()` can remain for later call migration, but it should dereference the bound `WinCore*`.

## DiskManager Lifetime Impact

Current lifetime:

```text
diskmgr = new DiskManager;
diskmgr->Init();
core.Init(..., diskmgr, ...);
...
core.Cleanup();
delete diskmgr;
```

Recommended:

- keep `DiskManager` allocation in `WinUI`
- keep deletion in `WinUI`
- `VMOperations` only stores a non-owning pointer
- call `Unbind` before deleting `diskmgr`

Do not move DiskManager ownership yet.

Reason:

- disk menu state in `WinUI::DiskInfo` still depends on UI-owned filenames, read-only flags, current disk ids, and HMENU state
- D88 writeback and multi-disk behavior are sensitive

## TapeManager Lifetime Impact

Current lifetime:

```text
tapemgr = new TapeManager;
core.Init(..., tapemgr);
...
core.Cleanup();
delete tapemgr;
```

Recommended:

- keep `TapeManager` allocation in `WinUI`
- keep deletion in `WinUI`
- `VMOperations` only stores a non-owning pointer
- call `Unbind` before deleting `tapemgr`

Do not move TapeManager ownership yet.

Reason:

- tape menu label and snapshot naming are still frontend-owned
- T88 behavior should remain unchanged

## Recommended Next Implementation Step

Smallest safe implementation:

```text
Phase 5 WinCore/WinUI operation boundary step 5 を小さく実行しろ。
VMOperations を WinCore 所有から WinCore* 参照 wrapper に変更し、
Bind/Unbind/IsBound を追加しろ。
WinUI はまだ vmops を allocate しない。
既存 WinCore core 呼び出し元、disk/tape/snapshot/config 呼び出し元変更は禁止。
ロジック変更は禁止。
完了後 report を出せ。
```

Why not allocate in the same step:

- changing `VMOperations` ownership and changing `WinUI` lifetime at the same time makes failures harder to isolate
- the reference-wrapper conversion can be built and verified first

## Following Implementation Step

After the reference-wrapper conversion builds:

```text
Phase 5 WinCore/WinUI operation boundary step 6 を小さく実行しろ。
WinUI::InitM88 で VMOperations を allocate して Bind(&core, diskmgr, tapemgr) し、
WinUI::CleanupM88 で Unbind/delete しろ。
既存 core/diskmgr/tapemgr 呼び出し元置換は禁止。
ロジック変更は禁止。
完了後 report を出せ。
```

## Stop Points

Stop before implementation if any of these need to change:

- `VMOperations` should own `WinCore` after all
- `DiskManager` ownership should move into `VMOperations`
- `TapeManager` ownership should move into `VMOperations`
- monitor initialization should be routed through `VMOperations`
- `core.GetSound()` call sites should be migrated now

Recommended current decisions:

- keep `WinCore core` owned by `WinUI`
- keep `DiskManager` and `TapeManager` owned by `WinUI`
- make `VMOperations` non-owning
- keep monitors direct to `core`
- keep `WinSound` direct until audio boundary work
