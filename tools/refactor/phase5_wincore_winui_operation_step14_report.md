# Phase 5 WinCore/WinUI Operation Boundary Step 14 Report

## Scope

- Migrate exactly one `WinUI::WmInitMenu` sound read-only menu state check through `VMOperations`.
- Add only `VMOperations::IsSoundDumping()`.
- Replace only the `core.GetSound()->IsDumping()` call for `IDM_RECORDPCM` in `WmInitMenu`.
- Do not change PCM dump start/end call sites.
- Do not change CPU dump state call sites.
- Do not change disk, tape, snapshot, config, sound implementation, or monitor initialization.

## Baseline

- Previous design commit:
  - `fedf594` `Design remaining WinUI menu read-only wrappers`
- Local MSVC/VC8 build is not available in this WSL environment.
- Existing untracked generated directories were left untouched:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Changes

`src/win32/vmops.h`:

```text
bool IsSoundDumping();
```

`src/win32/vmops.cpp`:

```text
bool VMOperations::IsSoundDumping()
{
	PC8801::WinSound* sound = core ? core->GetSound() : 0;
	return sound ? sound->IsDumping() : false;
}
```

`src/win32/ui.cpp`:

```text
core.GetSound()->IsDumping()
```

was replaced in the `IDM_RECORDPCM` menu check state with:

```text
vmops ? vmops->IsSoundDumping() : core.GetSound()->IsDumping()
```

## Why This Call

`IsSoundDumping()` is read-only from the menu's point of view.

It only controls whether `Record PCM` is checked when the menu opens.

It does not:

- start PCM dump
- stop PCM dump
- change sound driver state
- change sound buffer state
- change monitor initialization
- change any VM timing or audio generation logic

## Intentionally Not Changed

- `IDM_RECORDPCM` command handling remains direct:
  - `core.GetSound()->DumpBegin(buf)`
  - `core.GetSound()->DumpEnd()`
- CPU dump state remains direct:
  - `core.GetCPU1()->GetDumpState()`
  - `core.GetCPU2()->GetDumpState()`
- No disk calls migrated.
- No tape calls migrated.
- No snapshot calls migrated.
- No config calls migrated.
- No sound implementation changed.
- No monitor initialization changed.
- No project files changed.

## Local Verification

Local checks:

```text
git diff --check
rg -n "IsSoundDumping|IsDumping|IDM_RECORDPCM|GetCPU[12].*GetDumpState|vmops" src/win32/ui.cpp src/win32/vmops.h src/win32/vmops.cpp src/win32/winsound.h
```

Results:

- `git diff --check` passed.
- Source diff is limited to `VMOperations::IsSoundDumping` and one `WinUI::WmInitMenu` call site.
- `IDM_RECORDPCM` command-side PCM dump start/end calls remain direct.
- CPU dump state calls remain direct.
- Local MSVC/VC8 build was not run because this WSL environment does not provide Visual Studio.

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
- open menu while PCM recording is not active:
  - `Record PCM` is unchecked
- start PCM recording if available
- open menu while PCM recording is active:
  - `Record PCM` is checked
- stop PCM recording
- snapshot save/load
- clean shutdown
- no new warning dialog or crash

## User-Side Verification Result

User-side verification passed after commits:

- `8099f28` `Route PCM dump menu state through VM operations`
- `530b3b2` `Write PCM dumps beside M88 executable`

Verified:

- writetag CRC appears
- M88 launch: OK
- D88 game launch: OK
- sound: OK
- PCM recording output file is created: OK
- PCM recording output location: same directory as `M88.exe`
- PCM recording output filename format: `YYYYMMDDhhmmss.wav`
- menu while PCM recording is not active:
  - `Record PCM` is unchecked
- menu while PCM recording is active:
  - `Record PCM` is checked
- PCM recording stop: OK
- snapshot save/load: OK
- clean shutdown: OK
- new warning dialog or crash: none

## Next Safe Step

If this builds and runs, the next isolated read-only migration can be CPU dump menu state:

```text
Phase 5 WinCore/WinUI operation boundary step 15 を小さく実行しろ。
WinUI::WmInitMenu の core.GetCPU1()->GetDumpState() と
core.GetCPU2()->GetDumpState() の read-only menu state だけを
VMOperations 経由の GetCPU1DumpState / GetCPU2DumpState wrapper に移せ。
CPU dump toggle、sound、disk/tape/snapshot/config/monitor initialization 変更は禁止。
完了後 report を出せ。
```
