# Phase 5 WinCore/WinUI Operation Boundary Step 8 Inventory

## Scope

- Inventory only.
- Classify remaining `core.*` call sites in `WinUI`.
- Identify low-risk read-only migration candidates.
- Identify migration-hold candidates.
- Exclude disk, tape, snapshot, config, monitor, and sound implementation work.
- Do not implement changes.

## Baseline

- Pushed commit:
  - `12f1c7e` `Record VM exec count route verification`
- Current verified state:
  - `VMOperations` is allocated and bound in `WinUI::InitM88`
  - `VMOperations` is unbound and deleted in `WinUI::CleanupM88`
  - `WinUI::WmTimer` routes `GetExecCount` through `vmops`
  - user-side VS2008 / VC8 Express `Release|Win32` build passed after `559bc91`
  - title fps/MHz update passed after `559bc91`
- Local MSVC/VC8 build is not available in this WSL environment.

## Remaining `core.*` Call Sites In `WinUI`

Lifecycle and startup:

```text
core.Init(...)
core.GetOPN1()
core.GetSound()
core.GetSound()->SetSoundMonitor(...)
core.Wait(false)
core.Reset()
core.Cleanup()
```

Shutdown:

```text
core.GetOPN1()
```

Sound / PCM dump:

```text
core.GetSound()->IsDumping()
core.GetSound()->DumpBegin(...)
core.GetSound()->DumpEnd()
```

Menu read-only capability checks:

```text
core.IsN80Supported()
core.IsN80V2Supported()
core.IsCDSupported()
```

Debug CPU dump menu state:

```text
core.GetCPU1()->GetDumpState()
core.GetCPU2()->GetDumpState()
```

Config / reset / volume:

```text
core.ApplyConfig(&config)
core.Reset()
core.SetVolume(...)
```

Snapshot:

```text
core.SaveShapshot(...)
core.LoadShapshot(...)
```

Already migrated:

```text
vmops ? vmops->GetExecCount() : core.GetExecCount()
```

Commented-out historical calls:

```text
// core.ActivateMouse(...)
// core.SetGUIFlag(...)
```

These should remain untouched.

## Low-Risk Read-Only Candidates

### Candidate A: BASIC Capability Menu Checks

Call sites:

```text
core.IsN80Supported()
core.IsN80V2Supported()
core.IsCDSupported()
```

Context:

- Used in `WinUI::WmInitMenu`.
- Only controls whether menu items are enabled or grayed.
- Read-only capability checks.
- Does not touch disk, tape, snapshot, config persistence, or VM lifecycle directly.

Risk:

- Low.
- Visible if menu enable/gray state changes.
- Needs user-side menu-open smoke after migration.

Recommended first migration after this inventory:

```text
core.IsN80Supported()
```

Only migrate one call first.

### Candidate B: Remaining BASIC Capability Checks

Call sites:

```text
core.IsN80V2Supported()
core.IsCDSupported()
```

Context and risk:

- Similar to Candidate A.
- Keep separate from the first migration to preserve small commit size.

Recommended:

- Migrate after `IsN80Supported` proves safe.

## Migration-Hold Candidates

### Hold: Lifecycle Calls

Call sites:

```text
core.Init(...)
core.Wait(false)
core.Reset()
core.Cleanup()
```

Reason to hold:

- These control VM initialization, start, reset, and teardown.
- Moving them changes lifecycle ownership.
- `VMOperations` is still a facade, not the lifecycle owner.

Recommended:

- Hold until more read-only calls are proven.
- Design separately before moving.

### Hold: Monitor Initialization

Call sites:

```text
opnmon.Init(core.GetOPN1(), core.GetSound())
memmon.Init(&core)
codemon.Init(&core)
basmon.Init(&core)
regmon.Init(&core)
iomon.Init(&core)
core.GetSound()->SetSoundMonitor(&opnmon)
```

Reason to hold:

- Debug monitor windows directly inspect `WinCore` / `PC88` internals.
- `OPNMonitor` also depends on `WinSound`.
- SDL2 frontend does not need these Windows debug windows initially.

Recommended:

- Keep direct to `core`.

### Hold: Shutdown OPN Reset

Call site:

```text
OPNIF* opn = core.GetOPN1();
opn->Reset();
```

Reason to hold:

- Shutdown behavior.
- Hardware / sound-facing side effect.
- Not read-only.

Recommended:

- Hold.

### Hold: Sound / PCM Dump

Call sites:

```text
core.GetSound()->IsDumping()
core.GetSound()->DumpBegin(...)
core.GetSound()->DumpEnd()
```

Reason to hold:

- `WinSound` is Windows-specific.
- `DumpBegin` / `DumpEnd` are side-effecting.
- Even `IsDumping` controls visible PCM-recording menu state and is tied to the same feature.

Recommended:

- Hold until audio boundary or sound facade inventory.

### Hold: CPU Dump Menu State

Call sites:

```text
core.GetCPU1()->GetDumpState()
core.GetCPU2()->GetDumpState()
```

Reason to hold:

- Debug CPU dump state is a verification/debug feature.
- Accesses CPU internals through `WinCore`.
- It is read-only at the call site, but tied to debug controls rather than frontend VM operations.

Recommended:

- Hold until debug/monitor boundary.

### Hold: Config / Reset / Volume

Call sites:

```text
core.ApplyConfig(&config)
core.Reset()
core.SetVolume(...)
```

Reason to hold:

- `ApplyConfig` changes sequencer, draw, sound, and PC88 config state.
- `Reset` changes VM state.
- `SetVolume` changes sound configuration.

Recommended:

- Hold.
- Move only after a separate config/sound operation plan.

### Hold: Snapshot

Call sites:

```text
core.SaveShapshot(...)
core.LoadShapshot(...)
```

Reason to hold:

- Snapshot format and load semantics are high-risk.
- Load path interacts with disk remount behavior.

Recommended:

- Hold until snapshot-specific operation boundary step.

## Recommended Next Implementation Step

Smallest safe migration:

```text
Phase 5 WinCore/WinUI operation boundary step 9 を小さく実行しろ。
WinUI::WmInitMenu の core.IsN80Supported() 1 箇所だけを
vmops 経由の IsN80Supported wrapper に移せ。
VMOperations に IsN80Supported() を追加して WinCore に委譲しろ。
disk/tape/snapshot/config/sound/monitor 呼び出し元変更は禁止。
WinCore/DiskManager/TapeManager 実装変更は禁止。
完了後 report を出せ。
```

Required detail:

- Add `VMOperations::IsN80Supported()` first.
- Use a defensive fallback in `WinUI`:

```text
vmops ? vmops->IsN80Supported() : core.IsN80Supported()
```

Verification after that step:

- VS2008 / VC8 Express `Release|Win32` build
- open menu and confirm N80 menu enable/gray state is sane
- normal launch/runtime smoke

## Notes

Do not migrate multiple menu capability calls in one commit.

Do not migrate sound, CPU dump, reset, config, or snapshot paths yet.
