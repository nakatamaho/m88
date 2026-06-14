# Phase 5 WinCore/WinUI Operation Boundary Step 35 Report

## Changes Made
- `WinUI::InitM88` の monitor/wireup 前処理で、`core.GetOPN1()` / `core.GetSound()` へのフォールバック参照を除去し、
  `VMOperations` 経由の取得に寄せた。
- `WinUI::Main` 終了時に `core.GetOPN1()` を直接参照しないようにし、`VMOperations` 参照のみに変更。

`main` と `monitors` の起動/終了ルートは同一で、`vmops` 未設定時は 0 を返却して安全側に落とす形で変更。

## Files Changed
- `src/win32/ui.cpp`
- `tools/refactor/phase5_wincore_winui_operation_step35_report.md`

## Commands Run
```sh
rg -n "opnmon.Init\(|SetSoundMonitor\(|OPNIF\* opn = vmops\?" src/win32/ui.cpp
nl -ba src/win32/ui.cpp | sed -n '130,150p'
nl -ba src/win32/ui.cpp | sed -n '320,330p'
git diff --check
```

## Results
- `opnmon.Init` と `SetSoundMonitor` の取得源を `core` から `vmops` ベースへ変更。
- 終了時 OPN リセットの参照元も `core.GetOPN1()` から `vmops->GetOPN1()` (未設定時は `0`) へ変更。
- ローカルの `git diff --check` は clean。
- WSL では MSVC/VC8 のビルドは未実行。

## Behavior Preserved
- WinUI の monitor 初期化順、`sound` が null の場合の `SetSoundMonitor` 呼び出し抑止は既存挙動を維持。
- OPN リセット処理と終了手順の順序は変更せず、参照元の取得先のみ置換。
- ディスク/サウンド/snapshot/設定の mutating 経路は変更していない。

## Risks / Unknowns
- `vmops` が未初期化のまま到達した場合、終了時は OPN リセットを実行しない（`0` 参照）。
  ただし現行初期化シーケンス上、この経路は保守的で既存より重大に変更しない想定。
- 実行時検証は引き続き必要。

## User-Side Verification Needed
- `tools\\windows\\build_vc2008.cmd Release`
- runtime checklist:
  - writetag CRC
  - 起動 / clean shutdown
  - D88ゲーム / disk access
  - 音
  - snapshot save/load
  - メニュー操作 (PCM / CPU dump など)
  - 新規 warning / dialog / crash が増えないこと
