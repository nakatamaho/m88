# Phase 5 WinCore/WinUI Operation Boundary Step 18 Report

## Scope

- Route only `WinUI::ApplyConfig()`'s direct VM config application through
  `VMOperations`.
- Preserve fallback to the existing direct `core.ApplyConfig(&config)` call.
- Do not change `WinUI::Reset()`.
- Do not change keyboard, draw, menu, status, or debug menu behavior.
- Do not change `WinCore`, `VMOperations`, disk, tape, snapshot, sound, or
  monitor implementation.

## Baseline

- Previous pushed commits:
  - `c48b001` `Inventory post-menu WinUI core operation risks`
  - `73c08df` `Design WinUI config reset operation migration`
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Change

`src/win32/ui.cpp`:

```text
if (vmops)
    vmops->ApplyConfig(&config);
else
    core.ApplyConfig(&config);
```

This replaces the single direct call in `WinUI::ApplyConfig()`:

```text
core.ApplyConfig(&config);
```

## Preserved Call Order

`WinUI::ApplyConfig()` still performs operations in the same order:

1. Normalize `config.mainsubratio`.
2. Clear debug/special palette flags when `dipsw != 1`.
3. Apply VM/core config through `vmops` when available, otherwise direct core.
4. Apply keyboard config.
5. Apply draw priority.
6. Update Reset menu text.
7. Update status window visibility and FDC status display.
8. Update debug menu / register menu shape.

## Intentionally Not Changed

- `WinUI::Reset()` still calls:
  - `keyif.ApplyConfig(&config)`
  - `core.ApplyConfig(&config)`
  - `core.Reset()`
- No `VMOperations` API or implementation changed.
- No `WinCore` implementation changed.
- No project files changed.
- No string literal or resource text changed.
- No disk/tape/snapshot/sound/monitor command path changed.

## Local Verification

Local checks:

```text
git diff --check
rg -n "core\\.ApplyConfig\\(&config\\)|vmops->ApplyConfig\\(&config\\)" src/win32/ui.cpp
```

Expected remaining matches:

- `vmops->ApplyConfig(&config)` in `WinUI::ApplyConfig()`
- fallback `core.ApplyConfig(&config)` in `WinUI::ApplyConfig()`
- direct `core.ApplyConfig(&config)` in `WinUI::Reset()`, intentionally left
  for a later step

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
- sound OK
- toggle CPU burst and confirm no new warning/dialog/crash
- toggle FDC status or status bar and confirm menu/status UI still updates
- open config dialog, change a harmless display/audio option, apply, and
  confirm no crash
- snapshot save/load
- clean shutdown
- no new warning dialog or crash

## User-Side Verification Result

User-side verification passed after commit:

- `ae65dd3` `Route WinUI config apply through VM operations`

Verified:

- VS2008 / VC8 Express `Release|Win32` rebuild: OK
- config-related light runtime check: OK
- game launch / run: OK
- snapshot save/load: OK

## Next Safe Step

After user-side verification, the next small step is:

```text
Phase 5 WinCore/WinUI operation boundary step 19 を小さく実行しろ。
WinUI::Reset の core.ApplyConfig(&config) と core.Reset() だけを
vmops 経由の ApplyConfig / Reset wrapper に移せ。
ask-before-reset dialog、keyif.ApplyConfig、WinCore/VMOperations 実装、
disk/tape/snapshot/config/sound/monitor 呼び出し元変更は禁止。
fallback は維持し、完了後 report を出せ。
```
