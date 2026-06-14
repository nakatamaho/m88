# Phase 5 WinCore/WinUI Operation Boundary Step 31 Report

## Changes Made
- `WinUI::InitM88` のエミュレーション開始呼び出しを `VMOperations` 経由に寄せた。
- 具体的には `core.Wait(false)` を `vmops ? vmops->Start() : core.Wait(false)` に置換。
- `Start()` は既存の `vmops` 実装 (`vmops.cpp`) のみで `core->Wait(false)` を呼ぶ既存委譲を使用するため、実行系の挙動は変更しない。

## Files Changed
- `src/win32/ui.cpp`
- `tools/refactor/phase5_wincore_winui_operation_step31_report.md`

## Commands Run
```sh
rg -n "core\\.Wait\\(false\\)|vmops->Start\\(\\)|InitM88" src/win32/ui.cpp
git diff -- src/win32/ui.cpp
```

## Results
- 該当行は `InitM88` のエミュレーション開始直前で、`vmops` バインド後に実行されるため、通常経路は `vmops` 経由になる。
- フォールバックとして `vmops` が未作成時には従来どおり `core.Wait(false)` へ戻るガードを維持。
- これ以外の `WinUI` の core ライフサイクル (config、reset、cleanup) は現状維持。

## Behavior Preserved
- 起動直後のシーケンサ起動呼び出し順は変更なし (`core.Init -> emulation begin` 時点で開始)。
- 実行開始時に `Wait(false)` が同等に呼ばれるため、既存の実行タイミングやスレッド起動動作への影響を避ける。

## Risks / Unknowns
- `vmops` が未バインドの異常系時はフォールバックが残るため、挙動差は極小。
- `core.Cleanup` や `core.Reset` は引き続き `WinUI` 直呼び出しのまま。

## Next Step
- 次は `core.Cleanup()` の `vmops` ルート化を検討する（`VMOperations` の責務を広げたうえで、`WinCore` 呼び出し順の安全性を確認しながら実施）。
