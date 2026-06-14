# Phase 5 WinCore/WinUI Operation Boundary Step 17 Design

## Scope

- Design only.
- Target the remaining `ApplyConfig` / `Reset` direct `core.*` calls in
  `src/win32/ui.cpp`.
- Preserve the existing `WinUI` public methods and UI-side behavior.
- Do not change implementation code.

## Baseline

- Previous local commit:
  - `c48b001` `Inventory post-menu WinUI core operation risks`
- `c48b001` is local and not pushed yet.
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Current Call Sites

`WinUI::ApplyConfig()`:

```text
config.mainsubratio = ...
if (config.dipsw != 1) { ... }
core.ApplyConfig(&config);
keyif.ApplyConfig(&config);
draw.SetPriorityLow(...);
SetMenuItemInfo(... IDM_RESET ...);
ShowStatusWindow();
debug menu update
```

`WinUI::Reset()`:

```text
if (askbeforereset) {
    SetGUIFlag(true);
    MessageBox(...);
    SetGUIFlag(false);
    if (cancel) return;
}
keyif.ApplyConfig(&config);
core.ApplyConfig(&config);
core.Reset();
```

Existing `VMOperations` wrappers already exist:

```text
VMOperations::ApplyConfig(PC8801::Config* config)
VMOperations::Reset()
```

They only delegate to `WinCore` when bound.

## Behavior To Preserve

### `ApplyConfig()` Order

The current order should be preserved exactly:

1. Normalize `config.mainsubratio`.
2. Clear debug/special palette flags when `dipsw != 1`.
3. Apply VM/core config.
4. Apply keyboard config.
5. Apply draw priority.
6. Update Reset menu text.
7. Update status window visibility and FDC status display.
8. Update debug menu / register menu shape.

The VM call currently happens before keyboard, draw, and menu/status updates.
Changing that order is not justified by this boundary work.

### `Reset()` Order

The current order should be preserved exactly:

1. If `askbeforereset` is enabled, enter GUI mode.
2. Show the reset confirmation dialog.
3. Leave GUI mode.
4. Return without side effects if the user cancels.
5. Apply keyboard config.
6. Apply VM/core config.
7. Reset VM/core.

The keyboard config is currently applied before the core config/reset pair.
That order should not move.

## Fallback Policy

For the first implementation step, keep defensive fallback behavior:

```text
if (vmops)
    vmops->ApplyConfig(&config);
else
    core.ApplyConfig(&config);
```

and:

```text
if (vmops)
    vmops->Reset();
else
    core.Reset();
```

Reason:

- `vmops` is allocated and bound during `WinUI::InitM88`, but `ApplyConfig()`
  is called during initialization.
- Keeping fallback matches the existing pattern in `WmTimer` / `WmInitMenu`.
- Removing fallback should wait until lifecycle ownership and `vmops`
  availability are final.

## Implementation Split

### Step 18 Candidate: `ApplyConfig()` One Call

Smallest safe implementation:

- In `WinUI::ApplyConfig()` only, replace:

```text
core.ApplyConfig(&config);
```

with the `vmops` fallback form.

Do not change:

- `WinUI::Reset()`
- menu updates
- status window handling
- keyboard config
- draw priority
- `VMOperations` API
- `WinCore` implementation

Risk:

- Low to medium.
- The wrapper already exists and only delegates.
- Verification must still cover config changes because `ApplyConfig()` is a
  broad UI path.

### Later Step Candidate: `Reset()` Core Calls

Second implementation step:

- In `WinUI::Reset()` only, replace the VM/core pair with:

```text
if (vmops)
    vmops->ApplyConfig(&config);
else
    core.ApplyConfig(&config);

if (vmops)
    vmops->Reset();
else
    core.Reset();
```

Do not combine this with `ApplyConfig()` unless explicitly requested.

Risk:

- Medium.
- Reset affects BASIC mode changes, clock changes, CPU mode, disk state, and
  confirmation dialog behavior.

## Validation Plan

For `ApplyConfig()` migration:

- VS2008 / VC8 Express `Release|Win32` rebuild.
- writetag CRC appears.
- M88 launch.
- D88 game launch.
- Sound OK.
- Toggle CPU burst and confirm no new warning/dialog/crash.
- Toggle FDC status or status bar and confirm menu/status UI still updates.
- Open config dialog, change a harmless display/audio option, apply, confirm
  no crash.
- Snapshot save/load.
- Clean shutdown.

For `Reset()` migration:

- All `ApplyConfig()` checks above.
- F12 reset if enabled.
- Menu `Reset`.
- BASIC mode change such as N88 V1/V2 where ROM availability allows.
- 4MHz / 8MHz menu change.
- D88 game still boots after reset.
- Disk access after reset.
- Sound after reset.
- Snapshot save/load after reset.
- No new warning/dialog/crash.

## Recommended Next Step

```text
まず c48b001 とこの design commit を push しろ。
その後、Phase 5 WinCore/WinUI operation boundary step 18 を小さく実行しろ。
WinUI::ApplyConfig の core.ApplyConfig(&config) 1 箇所だけを
vmops 経由の ApplyConfig wrapper に移せ。
WinUI::Reset、keyboard/draw/menu/status/debug menu、WinCore/VMOperations 実装変更は禁止。
fallback は維持し、完了後 report を出せ。
```

