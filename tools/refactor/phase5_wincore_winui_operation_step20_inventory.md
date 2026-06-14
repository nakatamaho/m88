# Phase 5 WinCore/WinUI Operation Boundary Step 20 Inventory

## Scope

- Inventory only.
- Recheck remaining direct `core.*` call sites in `src/win32/ui.cpp` after the
  config/reset migrations.
- Classify remaining calls into:
  - snapshot save/load
  - sound mutating operations
  - lifecycle start/stop/cleanup
  - monitor initialization
  - fallback-only direct core calls
- Recommend the next low-risk implementation candidate.
- Do not change implementation code.

## Baseline

- Previous pushed commit:
  - `d25d9e8` `Record WinUI reset verification`
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Search Method

```text
rg -n "\bcore\." src/win32/ui.cpp
```

## Current Classification

### Snapshot Save/Load

Call sites:

- `WinUI::SaveSnapshot`
  - `core.SaveShapshot(name)`
- `WinUI::LoadSnapshot`
  - `core.LoadShapshot(name, diskinfo[0].filename)`
  - `core.LoadShapshot(name, 0)`

Existing wrapper support:

- `VMOperations::SaveSnapshot(const char* path)`
- `VMOperations::LoadSnapshot(const char* path, const char* diskPath)`

Risk:

- Medium.
- The wrapper already delegates to the same `WinCore` methods.
- Snapshot format compatibility is still a hard preservation point.
- `LoadSnapshot` has D88 multi-disk coordination before the VM/core call.

Recommendation:

- Best next implementation candidate.
- Migrate only `SaveSnapshot()` in one step, or migrate save and load together
  only if explicitly approved.
- Keep fallback to direct `core.*` calls.
- Do not rename the existing `Shapshot` spelling.

### Sound Mutating Operations

Call sites:

- `IDM_RECORDPCM`
  - `core.GetSound()->IsDumping()`
  - `core.GetSound()->DumpBegin(buf)`
  - `core.GetSound()->DumpEnd()`
- `WinUI::M88ChangeVolume`
  - `core.SetVolume((PC8801::Config*) c)`

Existing wrapper support:

- `VMOperations::IsSoundDumping()` exists.
- `VMOperations::GetSound()` exists, but using it directly from `WinUI` would
  keep the sound object exposed.
- No wrappers currently exist for:
  - `DumpBegin(path)`
  - `DumpEnd()`
  - `SetVolume(config)`

Risk:

- Medium to high.
- These are command paths with side effects.
- PCM recording has path and filename behavior.
- Volume changes touch sound/config behavior.

Recommendation:

- Do a design step before implementation.
- Prefer adding explicit `VMOperations` methods later, not exposing
  `GetSound()` further through new call sites.

### Lifecycle Start/Stop/Cleanup

Call sites:

- `WinUI::InitM88`
  - `core.Init(this, hwnd, &draw, diskmgr, &keyif, &winconfig, tapemgr)`
  - `core.Wait(false)`
  - `core.Reset()`
- `WinUI::CleanupM88`
  - `core.Cleanup()`

Existing wrapper support:

- `VMOperations::Start()`
- `VMOperations::Stop()`
- `VMOperations::Reset()`
- `VMOperations::Cleanup()`
- `VMOperations::Init(...)` exists but currently returns `false` after binding
  no `WinCore`, so it is not a usable replacement for `core.Init(...)`.

Risk:

- High.
- This area controls VM construction, startup, reset, shutdown, and `vmops`
  binding lifetime.
- Moving these calls without a lifecycle policy risks startup/shutdown order
  regressions.

Recommendation:

- Defer implementation.
- Keep direct lifecycle calls until a dedicated design step defines ownership,
  bind/unbind timing, and failure cleanup.

### Monitor Initialization

Call sites:

- `opnmon.Init(core.GetOPN1(), core.GetSound())`
- `memmon.Init(&core)`
- `codemon.Init(&core)`
- `basmon.Init(&core)`
- `regmon.Init(&core)`
- `iomon.Init(&core)`
- `core.GetSound()->SetSoundMonitor(&opnmon)`
- `OPNIF* opn = core.GetOPN1()` in the main cleanup/reset path

Existing wrapper support:

- No suitable monitor boundary exists.
- `VMOperations::GetSound()` exists, but monitor objects still take direct
  `WinCore*` or OPN/sound internals.

Risk:

- High.
- These are Win32 monitor/debug UI surfaces.
- They are not required for the first SDL2 frontend boundary.

Recommendation:

- Defer implementation.
- Treat monitor support as a later optional Win32/debug boundary.

### Fallback-Only Direct Core Calls

Call sites:

- `WmTimer`
  - `vmops ? vmops->GetExecCount() : core.GetExecCount()`
- `WmInitMenu`
  - `vmops ? ... : core.IsN80Supported()`
  - `vmops ? ... : core.IsN80V2Supported()`
  - `vmops ? ... : core.IsCDSupported()`
  - `vmops ? ... : core.GetSound()->IsDumping()`
  - `vmops ? ... : core.GetCPU1()->GetDumpState()`
  - `vmops ? ... : core.GetCPU2()->GetDumpState()`
- `WinUI::ApplyConfig`
  - fallback `core.ApplyConfig(&config)`
- `WinUI::Reset`
  - fallback `core.ApplyConfig(&config)`
  - fallback `core.Reset()`

Risk:

- Low for leaving in place.
- Removing fallbacks is not a functional boundary improvement while lifecycle
  availability is still intentionally defensive.

Recommendation:

- Leave fallback branches until lifecycle ownership and `vmops` availability
  are final.

## Next Low-Risk Candidate

Recommended next implementation:

1. Migrate `WinUI::SaveSnapshot()` only.
   - Use `vmops ? vmops->SaveSnapshot(name) : core.SaveShapshot(name)`.
   - Keep status display behavior unchanged.
   - Keep `currentsnapshot` / `snapshotchanged` updates unchanged.
   - Do not touch `LoadSnapshot()` in the same step unless explicitly approved.

Why this is the safest next implementation:

- `VMOperations::SaveSnapshot()` already exists.
- The `WinUI::SaveSnapshot()` call site is small.
- Runtime verification is straightforward.
- It does not touch disk/tape/sound/lifecycle/monitor code.

## Suggested Next Step

```text
Phase 5 WinCore/WinUI operation boundary step 21 を小さく実行しろ。
WinUI::SaveSnapshot の core.SaveShapshot(name) 1 箇所だけを
vmops 経由の SaveSnapshot wrapper に移せ。
LoadSnapshot、snapshot name/status/currentsnapshot/snapshotchanged、
WinCore/VMOperations 実装、disk/tape/sound/lifecycle/monitor 変更は禁止。
fallback は維持し、完了後 report を出せ。
```

