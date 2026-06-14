# Phase 5 WinCore/WinUI Operation Boundary Step 38 Report

## Scope
- Very small implementation step.
- `WinUI::CleanupM88` の `core.Cleanup()` フォールバック参照を削除して、`VMOperations` 経由で収束。

## Changes Made
- `src/win32/ui.cpp`
  - `WinUI::CleanupM88()` から以下を除去:
    - `vmops` 未設定時の `core.Cleanup()` 呼び出し
  - `vmops` が存在する通常経路では `vmops->Cleanup()` のみで終了処理を行うように整理。

## Files Changed
- `src/win32/ui.cpp`
- `tools/refactor/phase5_wincore_winui_operation_step38_report.md`

## Commands Run
```sh
rg -n "core\\.Cleanup\\(\\)|vmops->Cleanup\\(\\)" src/win32/ui.cpp
git diff -- src/win32/ui.cpp
git diff --check
```

## Result
- `WinUI` 側のクリーンアップルートで `core.*` への直接依存を 1 箇所削減。
- `Cleanup` の実体は `VMOperations::Cleanup()` を経由した既存委譲のまま。`core` 直呼び出しは除去。
- フォールバック (`else core.Cleanup()`) を外したため、通常運転中の経路（`vmops` が初期化済み）ではシンプル化され、責務が `vmops` に統一。

## Risks / Notes
- `vmops` が未初期化の経路で `CleanupM88` が呼ばれた場合、`core.Cleanup()` は実行されません。
- 現在の通常起動フローでは `vmops` は `InitM88` で必ず生成・初期化される想定なので、通常動作への影響は小さい。

## User-Side Runtime Verification Needed
- `tools/windows/build_vc2008.cmd Release`
- 確認項目:
  - writetag CRC の出力確認
  - 起動確認（M88）
  - clean shutdown 到達（前回から引き続き重要）
  - D88 ゲーム動作 + disk access（可能なら）
  - snapshot save/load（任意）
  - 音
  - メニュー open と既知項目表示
  - 新規 warning/dialog/crash が増えていないこと
