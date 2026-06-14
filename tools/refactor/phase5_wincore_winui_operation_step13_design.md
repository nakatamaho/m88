# Phase 5 WinCore/WinUI Operation Boundary Step 13 Design

## Scope

- Design only.
- Target the remaining `WinUI::WmInitMenu` direct `core.*` read-only calls:
  - `core.GetSound()->IsDumping()`
  - `core.GetCPU1()->GetDumpState()`
  - `core.GetCPU2()->GetDumpState()`
- Define possible `VMOperations` wrapper names.
- Define verification items.
- Describe sound/monitor boundary impact.
- No implementation was performed.

## Baseline

Pushed before this design:

- `049f96d` `Inventory remaining WinUI core operation calls`

Current state:

- `master` matches `origin/master` before this design report.
- Existing untracked generated directories are left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

Local MSVC/VC8 build is not available in this WSL environment.

## Current Call Sites

In `WinUI::WmInitMenu`:

```text
CheckMenuItem(hmenu, IDM_RECORDPCM, core.GetSound()->IsDumping() ? MF_CHECKED : MF_UNCHECKED);

EnableMenuItem(hmenu, IDM_DUMPCPU1, core.GetCPU1()->GetDumpState() == -1 ? MF_GRAYED : MF_ENABLED);
CheckMenuItem(hmenu, IDM_DUMPCPU1, core.GetCPU1()->GetDumpState() == 1 ? MF_CHECKED : MF_UNCHECKED);
EnableMenuItem(hmenu, IDM_DUMPCPU2, core.GetCPU2()->GetDumpState() == -1 ? MF_GRAYED : MF_ENABLED);
CheckMenuItem(hmenu, IDM_DUMPCPU2, core.GetCPU2()->GetDumpState() == 1 ? MF_CHECKED : MF_UNCHECKED);
```

These only refresh menu state when a menu opens.

They do not start/stop PCM dump and do not enable/disable CPU dump.

## Proposed Wrapper Names

### Sound Read-Only

Recommended wrapper:

```text
bool VMOperations::IsSoundDumping();
```

Behavior:

```text
return core && core->GetSound() && core->GetSound()->IsDumping();
```

Reason:

- The UI only needs a boolean for the menu check state.
- It avoids exposing `WinSound*` at the call site.
- It keeps the existing `GetSound()` compatibility API available but avoids expanding its use.

### CPU Debug Read-Only

Recommended wrappers:

```text
int VMOperations::GetCPU1DumpState();
int VMOperations::GetCPU2DumpState();
```

Behavior:

```text
return core ? core->GetCPU1()->GetDumpState() : -1;
return core ? core->GetCPU2()->GetDumpState() : -1;
```

State meaning from existing usage:

- `-1`: dump unsupported, menu disabled.
- `0`: dump supported and off, menu enabled and unchecked.
- `1`: dump supported and on, menu enabled and checked.

Reason:

- The existing menu logic already depends on the exact integer state.
- Returning `int` preserves the current tri-state behavior without inventing a new enum.
- A future enum can be considered only after all callers are isolated and verified.

## Implementation Order

Recommended small steps:

1. Migrate only `core.GetSound()->IsDumping()` in `WmInitMenu` to `VMOperations::IsSoundDumping()`.
2. Verify the PCM record menu check state and normal sound playback.
3. Migrate CPU dump state as a separate step, preferably CPU1 and CPU2 together because their menu logic is symmetrical.
4. Verify CPU dump menu enable/check state in both normal and debug-capable configurations if available.
5. Leave mutating operations for later:
   - `core.GetSound()->DumpBegin(buf)`
   - `core.GetSound()->DumpEnd()`
   - any CPU dump toggle command paths

## Sound Boundary Impact

`IsSoundDumping()` is read-only, but it belongs to the sound domain.

Impact:

- No audio generation behavior should change.
- No PCM dump start/end behavior should change.
- No sound driver selection or buffer behavior should change.
- It creates a narrow precedent for sound state reads through `VMOperations`.

Hold for later:

- `DumpBegin`
- `DumpEnd`
- `SetVolume`
- sound monitor binding
- driver/backend abstraction

These are mutating or lifecycle-adjacent and should not be mixed with this read-only menu check.

## Debug / Monitor Boundary Impact

`GetDumpState()` is read-only, but it is debug/CPU-monitor adjacent.

Impact:

- No CPU execution, timing, or Z80 implementation behavior should change.
- No dump enable/disable behavior should change.
- No monitor window behavior should change.
- Wrapper should return the same tri-state integer.

Hold for later:

- Any CPU dump toggling command.
- Monitor initialization.
- `memmon`, `codemon`, `basmon`, `regmon`, `loadmon`, `iomon` ownership or call paths.

## Verification Plan

For `IsSoundDumping()` step:

- VS2008 / VC8 Express `Release|Win32` rebuild.
- writetag CRC appears.
- M88 launch.
- D88 game launch.
- Sound OK.
- Open menu while PCM recording is not active:
  - `Record PCM` is unchecked.
- Start PCM recording if available in the menu.
- Open menu while PCM recording is active:
  - `Record PCM` is checked.
- Stop PCM recording.
- Snapshot save/load.
- Clean shutdown.
- No new warning dialog or crash.

For CPU dump state step:

- VS2008 / VC8 Express `Release|Win32` rebuild.
- M88 launch.
- Open menu.
- `Dump CPU1` enable/check state is same as before.
- `Dump CPU2` enable/check state is same as before.
- If the active CPU backend reports unsupported dump state:
  - corresponding menu item remains gray/disabled.
- D88 game launch.
- Disk access.
- Sound OK.
- Snapshot save/load.
- Clean shutdown.
- No new warning dialog or crash.

## Risks

- `IsSoundDumping()` requires `core->GetSound()` to be valid. Existing code assumes this in `WmInitMenu`; wrapper should be defensive but not mask normal lifecycle bugs.
- CPU dump state uses an integer protocol, not a named enum. The wrapper should preserve the exact values.
- Debug support differs by CPU backend:
  - `Z80C::GetDumpState()` returns `0` or `1`.
  - `Z80_x86::GetDumpState()` returns `-1`.
- Do not merge sound read-only and CPU debug read-only into the same implementation commit unless explicitly requested.

## Recommended Next Step

Smallest implementation candidate:

```text
Phase 5 WinCore/WinUI operation boundary step 14 を小さく実行しろ。
WinUI::WmInitMenu の core.GetSound()->IsDumping() 1 箇所だけを
VMOperations 経由の IsSoundDumping wrapper に移せ。
PCM dump start/end の呼び出し元変更は禁止。
CPU dump state、disk/tape/snapshot/config/sound implementation/monitor initialization 変更は禁止。
完了後 report を出せ。
```
