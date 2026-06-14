# Phase 5 WinCore/WinUI Operation Boundary Step 39 Report

## Scope

- `src/win32/ui.cpp` の `WinUI::ApplyConfig()` と `WinUI::Reset()` から
  直接 `core.*` 呼び出しを削除し、`VMOperations` 経由へ寄せる。
- `keyif.ApplyConfig`、`keyif` の更新順、`Draw`/メニュー更新、`Reset` 確認ダイアログ、`core`/`WinCore`/`VMOperations` 実装は変更しない。
- `project file` / `vcproj` / `dsp` は変更しない。

## Baseline

- 直前 commit:
  - `725d655` `Phase5 step36-38: route WinCore lifecycle via VMOperations`
- 既存の `tools/refactor/phase5_wincore_winui_operation_step24_report.md` で
  `WmInitMenu` / `WmTimer` 側の read-only fallback は整理済み。
- WSL では MSVC/VC8 Express の実行 build は不可（ローカル build 未実施）。
- 未追跡生成物:
  - `cdif/debug/`
  - `diskdrv/debug/`

## Changes

`src/win32/ui.cpp`:

- `WinUI::ApplyConfig()`
  - 変更前:
    - `if (vmops) vmops->ApplyConfig(&config); else core.ApplyConfig(&config);`
  - 変更後:
    - `if (vmops) vmops->ApplyConfig(&config);`
- `WinUI::Reset()`
  - 変更前:
    - `if (vmops) vmops->ApplyConfig(&config); else core.ApplyConfig(&config);`
    - `if (vmops) vmops->Reset(); else core.Reset();`
  - 変更後:
    - `if (vmops) { vmops->ApplyConfig(&config); vmops->Reset(); }`

この結果、`src/win32/ui.cpp` の未コメント領域における `core.` 直参照は解消済み。

## Verification (local)

- `rg -n "\\bcore\\." src/win32/ui.cpp`  
  - 期待どおり、コメント内の履歴参照のみ残存。
- `git diff --check`  
  - クリア。

## User-Side Runtime Verification Needed

Windows 側で以下を実施してください:

- `tools\\windows\\build_vc2008.cmd Release`
- `writetag` CRC 出力確認
- 起動確認（M88）
- clean shutdown 到達
- D88 ゲーム起動と disk access
- snapshot save/load
- 音再生
- メニュー操作（PCM、CPU dump、モード系）
- 新規 warning / dialog / crash の有無（増加なし）

## Expected Result

- 上記項目がすべて成立すれば、`WinCore/WinUI` の設定・リセット経路での直接 `core.*` 呼び出しは、
  `VMOperations` 経由に統一されるため、次の段階へ進める。
