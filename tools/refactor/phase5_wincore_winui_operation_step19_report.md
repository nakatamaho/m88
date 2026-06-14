# Phase 5 WinCore/WinUI Operation Boundary Step 19 Report

## Scope

- Route only `WinUI::Reset()`'s VM/core config and reset calls through
  `VMOperations`.
- Preserve fallback to the existing direct `core.ApplyConfig(&config)` and
  `core.Reset()` calls.
- Preserve the ask-before-reset dialog behavior.
- Preserve `keyif.ApplyConfig(&config)` ordering.
- Do not change `WinUI::ApplyConfig()`, `WinCore`, `VMOperations`, disk, tape,
  snapshot, config, sound, or monitor implementation.

## Baseline

- Previous pushed commit:
  - `e79518a` `Record WinUI config apply verification`
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Change

`src/win32/ui.cpp`, inside `WinUI::Reset()`:

```text
keyif.ApplyConfig(&config);
if (vmops)
    vmops->ApplyConfig(&config);
else
    core.ApplyConfig(&config);
if (vmops)
    vmops->Reset();
else
    core.Reset();
```

This replaces only:

```text
keyif.ApplyConfig(&config);
core.ApplyConfig(&config);
core.Reset();
```

## Preserved Call Order

`WinUI::Reset()` still performs operations in the same order:

1. If `askbeforereset` is enabled, enter GUI mode.
2. Show the reset confirmation dialog.
3. Leave GUI mode.
4. Return without side effects if the user cancels.
5. Apply keyboard config.
6. Apply VM/core config through `vmops` when available, otherwise direct core.
7. Reset VM/core through `vmops` when available, otherwise direct core.

## Intentionally Not Changed

- The reset confirmation dialog text and flags were not changed.
- `SetGUIFlag(true/false)` around the dialog was not changed.
- `keyif.ApplyConfig(&config)` remains before VM/core config and reset.
- `WinUI::ApplyConfig()` was not changed in this step.
- `core.Reset()` in `WinUI::InitM88` was not changed. That belongs to the
  higher-risk lifecycle boundary.
- No `VMOperations` API or implementation changed.
- No `WinCore` implementation changed.
- No project files changed.
- No string literal or resource text changed.
- No disk/tape/snapshot/sound/monitor command path changed.

## Local Verification

Local checks:

```text
git diff --check
rg -n "core\\.ApplyConfig\\(&config\\)|core\\.Reset\\(\\)|vmops->ApplyConfig\\(&config\\)|vmops->Reset\\(\\)" src/win32/ui.cpp
```

Expected remaining matches:

- `WinUI::ApplyConfig()`:
  - `vmops->ApplyConfig(&config)`
  - fallback `core.ApplyConfig(&config)`
- `WinUI::Reset()`:
  - `vmops->ApplyConfig(&config)`
  - fallback `core.ApplyConfig(&config)`
  - `vmops->Reset()`
  - fallback `core.Reset()`
- `WinUI::InitM88`:
  - direct `core.Reset()`, intentionally left for lifecycle work

MSVC/VC8 build was not run locally because this WSL environment does not
provide Visual Studio.

## User-Side Verification Request

Recommended:

```text
tools\windows\build_vc2008.cmd Release
```

Then verify:

- writetag CRC appears
- M88 launch
- D88 game launch
- disk access
- sound OK
- F12 reset if enabled
- menu `Reset`
- 4MHz / 8MHz menu change
- BASIC mode change where ROM availability allows
- game still boots after reset
- disk access after reset
- sound after reset
- snapshot save/load after reset
- clean shutdown
- no new warning dialog or crash

## Next Safe Step

After user-side verification, the remaining direct `core.*` calls in `WinUI`
are no longer the low-risk config/reset calls. The next step should be an
inventory or design step before touching one of these higher-risk groups:

- snapshot save/load wrappers
- sound mutating operations
- lifecycle start/stop/cleanup
- monitor initialization

Suggested next step:

```text
Phase 5 WinCore/WinUI operation boundary step 20 の棚卸しだけ実行しろ。
WinUI に残る snapshot save/load、sound mutating、lifecycle、monitor initialization の
core.* 呼び出しを再確認し、次に実装してよい低リスク候補を report しろ。
実装はするな。
```

