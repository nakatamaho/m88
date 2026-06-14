# Phase 5 WinCore/WinUI Operation Boundary Step 16 Inventory

## Scope

- Recheck direct `core.*` call sites left in `src/win32/ui.cpp` after the
  `WmInitMenu` read-only migrations.
- Classify remaining calls into:
  - `ApplyConfig` / `Reset`
  - snapshot
  - sound mutating
  - monitor initialization
  - lifecycle
- Report next boundary candidates and risks.
- Do not change implementation.

## Baseline

- Starting commit: `9586123` `Update README porting progress`
- `9586123` has been pushed to `origin/master`.
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Search Method

```text
rg -n "\bcore\." src/win32/ui.cpp
```

The scan intentionally ignores commented-out historical lines unless they
matter for a future boundary decision.

## WmInitMenu Status

The primary low-risk read-only menu state checks have been moved to
`VMOperations`:

- `GetExecCount()`
- `IsN80Supported()`
- `IsN80V2Supported()`
- `IsCDSupported()`
- `IsSoundDumping()`
- `GetCPU1DumpState()`
- `GetCPU2DumpState()`

`WmInitMenu` still contains direct `core.*` fallback branches for abnormal
lifecycle cases where `vmops` is not available. These are not the primary path:

```text
vmops ? vmops->... : core....
```

Removing those fallbacks has little portability value and may reduce defensive
behavior during partial initialization, so they should be left alone unless a
separate lifecycle policy is approved.

## Remaining Direct Core Calls

### Lifecycle

Call sites:

- `WinUI::InitM88`
  - `core.Init(this, hwnd, &draw, diskmgr, &keyif, &winconfig, tapemgr)`
  - `core.Wait(false)`
  - `core.Reset()`
- `WinUI::CleanupM88`
  - `core.Cleanup()`

Risk:

- High. These calls define VM construction, start, reset, and shutdown order.
- They also determine when `VMOperations` can safely bind/unbind.
- Moving them before the ownership model is finalized could introduce use after
  free, missed cleanup, or startup ordering regressions.

Recommendation:

- Defer implementation.
- Keep `WinCore core` owned by `WinUI` for now.
- Do a dedicated lifecycle design step before migrating any of these calls.

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

Risk:

- High. The monitor windows are Win32 UI/debug tools and several of them take a
  raw `WinCore*`.
- `opnmon` also touches sound monitor binding.
- This is not needed for SDL2 frontend bootstrap unless monitor support is
  being designed at the same time.

Recommendation:

- Keep direct Win32 monitor initialization for now.
- Treat monitor support as a later optional frontend/debug boundary.

### ApplyConfig / Reset

Call sites:

- `WinUI::ApplyConfig`
  - `core.ApplyConfig(&config)`
- `WinUI::Reset`
  - `core.ApplyConfig(&config)`
  - `core.Reset()`

Risk:

- Medium to high.
- `WinUI::ApplyConfig` also updates keyboard, draw priority, menu text, status
  windows, and debug menu state.
- `WinUI::Reset` has the ask-before-reset dialog and applies key config before
  calling the core.
- `VMOperations` already has `ApplyConfig()` and `Reset()` wrappers, but the
  call order and UI side effects must remain unchanged.

Recommendation:

- Best next target for a design step.
- If implemented later, migrate one call at a time and preserve the existing
  UI-side order exactly.

### Snapshot

Call sites:

- `WinUI::SaveSnapshot`
  - `core.SaveShapshot(name)`
- `WinUI::LoadSnapshot`
  - `core.LoadShapshot(name, diskinfo[0].filename)`
  - `core.LoadShapshot(name, 0)`

Risk:

- Medium.
- `VMOperations` already has `SaveSnapshot()` and `LoadSnapshot()` wrappers.
- Snapshot format compatibility is a hard preservation point.
- `LoadSnapshot` has disk image coordination around multi-disk D88 state before
  the core call.

Recommendation:

- Mechanically simple but compatibility-sensitive.
- Keep this as a separate tiny step with explicit snapshot save/load runtime
  verification.
- Do not rename the existing `Shapshot` API spelling while preserving behavior.

### Sound Mutating

Call sites:

- `IDM_RECORDPCM`
  - `core.GetSound()->IsDumping()`
  - `core.GetSound()->DumpBegin(buf)`
  - `core.GetSound()->DumpEnd()`
- `WinUI::M88ChangeVolume`
  - `core.SetVolume((PC8801::Config*) c)`

Risk:

- Medium to high.
- These are command paths, not passive menu-state reads.
- PCM recording has file path and filename behavior.
- Volume changes are config/sound-driver interactions.

Recommendation:

- Do not mix with config/reset or snapshot changes.
- First design sound mutating wrappers:
  - `IsSoundDumping()` is already present.
  - Potential later additions: `BeginSoundDump(path)`, `EndSoundDump()`,
    `SetVolume(config)`.
- Preserve current PCM output path and filename behavior.

### Fallback-Only Direct Core Calls

Call sites:

- `WmTimer`
  - `vmops ? vmops->GetExecCount() : core.GetExecCount()`
- `WmInitMenu`
  - `vmops ? vmops->IsN80Supported() : core.IsN80Supported()`
  - `vmops ? vmops->IsN80V2Supported() : core.IsN80V2Supported()`
  - `vmops ? vmops->IsCDSupported() : core.IsCDSupported()`
  - `vmops ? vmops->IsSoundDumping() : core.GetSound()->IsDumping()`
  - `vmops ? vmops->GetCPU1DumpState() : core.GetCPU1()->GetDumpState()`
  - `vmops ? vmops->GetCPU2DumpState() : core.GetCPU2()->GetDumpState()`

Risk:

- Low for leaving them in place.
- Removing them would be a behavior cleanup, not a boundary improvement.

Recommendation:

- Leave them until lifecycle and `vmops` availability are final.

## Next Boundary Candidates

Recommended order:

1. `ApplyConfig` / `Reset` design only.
   - Reason: these are central VM operations and `VMOperations` already has
     wrappers, but UI-side call order must be documented before implementation.
2. Snapshot wrapper migration, one tiny step.
   - Reason: wrapper exists and call sites are few, but snapshot compatibility
     requires focused verification.
3. Sound mutating design.
   - Reason: recording and volume are behaviorful command paths.
4. Lifecycle design.
   - Reason: needed eventually, but highest risk.
5. Monitor boundary inventory/design.
   - Reason: likely Win32-only debug surface for longer.

## Suggested Next Step

```text
Phase 5 WinCore/WinUI operation boundary step 17 の設計だけ実行しろ。
ApplyConfig / Reset を VMOperations に寄せる場合の call order、
WinUI 側 side effect、fallback 方針、検証項目を report しろ。
実装はするな。
```

