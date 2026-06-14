# Phase 5 WinCore/WinUI Operation Boundary Step 26 Report

## Scope

- Small implementation after Step25.
- Remove direct `core` access from `IDM_RECORDPCM` sound-recording command path in `WinUI`.
- Keep snapshot, menu-state, monitor, config, reset, lifecycle handling unchanged.

## Baseline

- Previous pushed state:
  - `e9b460a` `Migrate snapshot save/load in WinUI to VMOperations-only`
- Existing untracked generated directories left unchanged:
  - `cdif/debug/`
  - `diskdrv/debug/`
- VC2008 runtime verification is outside this WSL environment.

## Change

`src/win32/ui.cpp` (`WinUI::WmCommand`, `IDM_RECORDPCM` branch):

- `core.GetSound()` direct calls were replaced by the following vmops-first flow:
  - `PC8801::WinSound* sound = vmops ? vmops->GetSound() : 0;`
  - guarded by `if (sound)` before any state/query/mutation calls.
  - `sound->IsDumping()`, `sound->DumpBegin(buf)`, `sound->DumpEnd()` used instead of `core.GetSound()->...`.

No other command branches were changed.

## Preservation Policy

- No changes to snapshot format or routing.
- No changes to `WinCore`, `VMOperations`, monitor/sound initialization, config/reset lifecycle, or disk/tape behavior.
- If `vmops` is not yet bound, sound recording command becomes no-op (safe behavior, consistent with defensive guard).

## Local Checks

- Scope verification:
  - `git diff -- src/win32/ui.cpp`
  - `rg -n "core\.GetSound\(\)->|IDM_RECORDPCM" src/win32/ui.cpp`

## User-Side Verification Needed

- `tools\\windows\\build_vc2008.cmd Release`
- runtime checklist:
  - writetag CRC
  - 起動
  - メニュー open
  - snapshot save/load
  - D88ゲーム起動 / disk access
  - 音
  - PCM録音開始/停止（`Record PCM` チェック状態）
  - clean shutdown
  - 新規 warning/dialog/crash なし


## Runtime Verification

- Command: `tools\\windows\\build_vc2008.cmd Release`
- Result:
  - writetag CRC: 出力あり
  - M88 起動: OK
  - メニュー open: OK
  - D88ゲーム起動 / disk access: OK
  - snapshot save/load: OK
  - 音: OK
  - PCM録音開始/停止（Record PCM チェック状態）: OK
  - clean shutdown: OK
  - 新規 warning/dialog/crash: なし

最終判定: **all green**
