# Phase 5 WinCore/WinUI Operation Boundary Step 12 Inventory

## Scope

- Inventory only.
- Target: remaining `core.*` call sites in `src/win32/ui.cpp`.
- Classify:
  - `WmInitMenu` read-only candidates.
  - lifecycle/config/snapshot/sound/monitor hold candidates.
  - low-risk migration order for `VMOperations`.
- No implementation was performed.

## Baseline

Pushed before this inventory:

- `26ce66a` `Record N80 support route verification`
- `64caa7f` `Route N80V2 support check through VM operations`
- `d21f60a` `Route CD support check through VM operations`

Current state after push:

- `master` matches `origin/master`.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

Local MSVC/VC8 build is not available in this WSL environment.

## Search Method

```text
rg -n "\bcore\." src/win32/ui.cpp
```

Comments containing old disabled `core.ActivateMouse` / `core.SetGUIFlag` calls were ignored for migration planning.

## Remaining Direct Core Calls

### Lifecycle / Ownership

These are not low-risk read-only menu candidates.

- `WinUI::InitM88`
  - `core.Init(this, hwnd, &draw, diskmgr, &keyif, &winconfig, tapemgr)`
  - `core.GetOPN1()`
  - `core.GetSound()`
  - `core.GetSound()->SetSoundMonitor(&opnmon)`
  - `core.Wait(false)`
  - `core.Reset()`
- `WinUI::CleanupM88`
  - `core.Cleanup()`
- `WinUI::Main`
  - `core.GetOPN1()`

Hold reason:

- These define startup/shutdown order, monitor binding, sound monitor binding, and VM lifecycle.
- `VMOperations` is currently bound after `core.Init`, so moving these requires a separate lifecycle design.
- `opnmon` and sound monitor setup are monitor/sound-adjacent and should not be mixed into simple menu migrations.

### Sound / Monitor

These are not low-risk menu capability checks.

- `WinUI::Command`
  - `core.GetSound()->IsDumping()`
  - `core.GetSound()->DumpBegin(buf)`
  - `core.GetSound()->DumpEnd()`
- `WinUI::WmInitMenu`
  - `core.GetSound()->IsDumping()`
  - `core.GetCPU1()->GetDumpState()`
  - `core.GetCPU2()->GetDumpState()`
- `WinUI::M88ChangeVolume`
  - `core.SetVolume((PC8801::Config*) c)`

Hold reason:

- PCM dump commands change sound output state and file output behavior.
- CPU dump state is debug/monitor-adjacent even though `WmInitMenu` reads it.
- Volume changes affect sound behavior.
- These should be handled only after a sound/debug operation boundary decision.

### Config / Reset

These should remain direct for now.

- `WinUI::ApplyConfig`
  - `core.ApplyConfig(&config)`
- `WinUI::Reset`
  - `core.ApplyConfig(&config)`
  - `core.Reset()`

Hold reason:

- Config application affects VM behavior, draw/key state, menu shape, and status UI together.
- Reset is a lifecycle/state operation, not a read-only facade candidate.
- Moving these should be paired with explicit `VMOperations::ApplyConfig` / `Reset` call-site migration and user-side verification.

### Snapshot

These should remain direct for now.

- `WinUI::SaveSnapshot`
  - `core.SaveShapshot(name)`
- `WinUI::LoadSnapshot`
  - `core.LoadShapshot(name, diskinfo[0].filename)`
  - `core.LoadShapshot(name, 0)`

Hold reason:

- Snapshot format and load behavior are compatibility-sensitive.
- `LoadSnapshot` also interacts with disk image state before loading.
- Although wrappers already exist in `VMOperations`, migrating these should be a separate snapshot-focused step with explicit save/load regression verification.

## WmInitMenu Read-Only Candidates

Already migrated through `VMOperations`:

- `IDM_N80MODE`
  - `VMOperations::IsN80Supported()`
- `IDM_N80V2MODE`
  - `VMOperations::IsN80V2Supported()`
- `IDM_N88V2CD`
  - `VMOperations::IsCDSupported()`

Remaining direct calls in `WmInitMenu`:

- `IDM_RECORDPCM`
  - `core.GetSound()->IsDumping()`
- `IDM_DUMPCPU1`
  - `core.GetCPU1()->GetDumpState()`
- `IDM_DUMPCPU2`
  - `core.GetCPU2()->GetDumpState()`

Classification:

- These are read-only menu state updates, but they are not as low-risk as N80/N80V2/CD support checks.
- `IsDumping()` is sound-state read-only.
- `GetDumpState()` is debug/CPU monitor-state read-only.
- They are candidates only if the next step explicitly allows sound/debug read-only wrappers.

## Low-Risk Migration Order

Recommended order if continuing in small steps:

1. Inventory or design a `VMOperations` read-only sound/debug query boundary before changing code.
2. Migrate `core.GetSound()->IsDumping()` in `WmInitMenu` only, adding a wrapper such as `VMOperations::IsSoundDumping()`.
3. Verify the PCM record menu check state and normal audio playback.
4. Separately consider `GetCPU1()->GetDumpState()` and `GetCPU2()->GetDumpState()` together, adding wrappers such as `GetCPU1DumpState()` / `GetCPU2DumpState()`.
5. Only after that, consider command-side sound dumping (`DumpBegin` / `DumpEnd`) as a separate mutating operation step.
6. Keep `ApplyConfig`, `Reset`, lifecycle, monitor init, and snapshot operations out of this sequence until explicitly approved.

## Hold Candidates

Do not migrate in the next small step without a focused design:

- `core.Init`
- `core.Cleanup`
- `core.Wait`
- `core.Reset`
- `core.ApplyConfig`
- `core.SetVolume`
- `core.GetOPN1`
- `core.GetSound()->SetSoundMonitor`
- `core.GetSound()->DumpBegin`
- `core.GetSound()->DumpEnd`
- `core.SaveShapshot`
- `core.LoadShapshot`

## Suggested Next Step

Conservative next step:

```text
Phase 5 WinCore/WinUI operation boundary step 13 の設計だけ実行しろ。
WmInitMenu に残る sound/debug read-only 状態
core.GetSound()->IsDumping(),
core.GetCPU1()->GetDumpState(),
core.GetCPU2()->GetDumpState()
を VMOperations に移す場合の wrapper 名、検証項目、
sound/monitor boundary への影響を report しろ。
実装はするな。
```

More aggressive but still small:

```text
Phase 5 WinCore/WinUI operation boundary step 13 を小さく実行しろ。
WinUI::WmInitMenu の core.GetSound()->IsDumping() 1 箇所だけを
VMOperations 経由の IsSoundDumping wrapper に移せ。
PCM dump start/end の呼び出し元変更は禁止。
CPU dump state、disk/tape/snapshot/config/sound implementation/monitor initialization 変更は禁止。
完了後 report を出せ。
```
