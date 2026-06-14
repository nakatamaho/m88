# Phase 5 WinCore/WinUI Operation Boundary Step 33 Report

## Changes Made
- `WinUI::InitM88` の起動時 `Reset` 呼び出しを `vmops` 優先経路へ寄せた。
- `core.Reset()` を `vmops ? vmops->Reset() : core.Reset();` に置換。
- `WinUI::Reset()` の内部ロジックは意図的に変更せず、既存の `if (vmops) vmops->Reset(); else core.Reset();` を維持した。

## Files Changed
- `src/win32/ui.cpp`
- `tools/refactor/phase5_wincore_winui_operation_step33_report.md`

## Commands Run
```sh
rg -n "core\\.Reset\\(\\)|vmops \\? vmops->Reset\\(\\) : core\\.Reset\\(\\)|vmops->Reset\\(\\)" src/win32/ui.cpp
sed -n '158,172p' src/win32/ui.cpp
sed -n '1048,1068p' src/win32/ui.cpp
git diff -- src/win32/ui.cpp
git diff --check
```

## Results
- `InitM88` のみを `vmops` 経由起動に寄せたため、`vmops` 正常時はこれまでと同等の reset 処理を `VMOperations` が `WinCore->Reset()` を委譲実行。
- `vmops` が未初期化時は既存パス（`core.Reset()`）へフォールバック。
- `WinUI::Reset()` の挙動は変更なし（起動時以外のリセットフローをそのまま保持）。

## Behavior Preserved
- 起動シーケンスの順序（`ApplyConfig()` 後の `Reset()`）は維持。
- `vmops` fallback ガードを残すことで、既存の異常系（初期化競合）での保守的挙動を維持。

## Risks / Unknowns
- `VMOperations::Reset()` が呼ばれた場合、`WinUI::Reset()` の分岐条件と呼び出し条件が一致していることを実機で確認する必要あり。
- 実際の runtime 検証（release rebuild / writetag / D88 / snapshot / shutdown）で順番差分がないか確認。

## Next Step
- 次は `core.ApplyConfig(&config)` の残存箇所（`WinUI::ApplyConfig` の直接呼び出しを除去し `vmops` 経由へ統一する）など、低リスク read-only から mutating boundary に進むかを検討する。
