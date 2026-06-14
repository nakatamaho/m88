# Phase 5 WinCore/WinUI Operation Boundary Step 29 Report

## Changes Made
- `WinUI` の終了処理で残っていた `core.GetOPN1()` 依存を `VMOperations` 経由に寄せる。
- `VMOperations` に `GetOPN1()` を追加し、終了時の OPN リセット経路を `vmops` 対応に変更。
- `core` 直呼び出しは `OPNIF` 取得のみを条件付きで残す（`vmops` 未バインド時の既存フォールバックを維持）。

## Files Changed
- `src/win32/vmops.h`
- `src/win32/vmops.cpp`
- `src/win32/ui.cpp`

## Commands Run
```sh
rg -n "OPNIF\* opn = core\.GetOPN1\(|GetOPN1\(" src/win32/ui.cpp src/win32/vmops.*
git diff -- src/win32/vmops.h src/win32/vmops.cpp src/win32/ui.cpp
git diff --check
```

## Results
- `WinUI::Main` の終了時:
  - `OPNIF* opn = core.GetOPN1();`
  - から
  - `OPNIF* opn = vmops ? vmops->GetOPN1() : core.GetOPN1();`
  に変更。
- `VMOperations` 新規追加:
  - `PC8801::OPNIF* GetOPN1()`
- ローカル整合チェック: `git diff --check` はエラーなし。
- WSL 環境のため MSVC/VC2008 実行ビルドは未実施（必要）。

## Behavior Preserved
- 終了時の OPN リセット挙動（`opn->Reset()`）は変えていない。
- 例外時のフォールバックとして `vmops` 不在時は従来通り `core.GetOPN1()` を利用。
- `WinCore` 実装/初期化/シャットダウン手順は変更しない。

## Risks / Unknowns
- VMOperations 経由化の可否は `vmops` の生存と `Bind` 状態に依存。現行ではガード有りのため、既存起動経路では影響は最小。
- 実機での VC2008 ビルド確認は必要。

## Next Step
- 引き続き `core.*` 直呼び出しの残存（`core.GetSound()->SetSoundMonitor(...)`, `core.GetSound()`, `core.Wait/Reset/Cleanup` 等）を次ステップで棚卸し→必要に応じて 1 箇所ずつ `vmops` 経由へ移行。
