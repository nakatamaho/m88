# Phase 5 WinCore/WinUI Operation Boundary Step 32 Report

## Changes Made
- `VMOperations::Cleanup()` を実体として `core->Cleanup()` を呼び出すように拡張し、内部で状態解除 (`Unbind()`) を続けて実行するように変更。
- `WinUI::CleanupM88` の終了処理を、`vmops` 在位時は `vmops->Cleanup()` に寄せる形へ変更。
- `vmops` 不在時のみ `core.Cleanup()` を直接実行するフォールバックは維持。

## Files Changed
- `src/win32/vmops.cpp`
- `src/win32/ui.cpp`
- `tools/refactor/phase5_wincore_winui_operation_step32_report.md`

## Commands Run
```sh
rg -n "vmops->Cleanup\\(|Unbind\\(|core\\.Cleanup\\(\\)|bool Cleanup\\(" src/win32/ui.cpp src/win32/vmops.h src/win32/vmops.cpp
git diff -- src/win32/ui.cpp src/win32/vmops.cpp
git diff --check
```

## Results
- これまで `WinUI` で直接 `core.Cleanup()` を行っていた終了時の停止処理を、`VMOperations` 経由へ寄せた。
- `VMOperations::Cleanup()` は、
  - `core` が有効な場合に `core->Cleanup()` を実行
  - その後 `Unbind()` して参照を解放
  - `true` を返却
  という順序で動作する。
- `WinUI::CleanupM88` は、`vmops` 非NULL時に `vmops->Cleanup()` を呼び、`vmops` NULL時は従来の `core.Cleanup()` を実行する既存安全性を保持。
- `active` フラグ/描画/デバイス削除順そのものには変更なし。

## Risks / Unknowns
- `core->Cleanup()` を `VMOperations` 経由に変更したことにより、`WinUI` 側での例外時フォールバックパスが変更されないことを確認する必要がある。
- `vmops` の寿命と `core` のバインド状態が期待どおりである前提でのみ、従来のシャットダウン順と同等の挙動が維持される。

## Next Step
- 次は Step33 として、`core.Reset()` / `core.Init` / 設定反映系の最小寄せを選定する（今回はロジック境界への影響が大きい領域を分離して進める）。
