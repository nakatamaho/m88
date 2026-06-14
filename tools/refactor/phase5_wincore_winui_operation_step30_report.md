# Phase 5 WinCore/WinUI Operation Boundary Step 30 Report

## Changes Made
- `WinUI` の monitor 初期化と monitor 接続で、`core.GetOPN1()` / `core.GetSound()` の直接参照を `VMOperations` 経由優先に変更。
- `core.GetSound()->SetSoundMonitor(&opnmon)` を安全な取得パターンへ変更し、`sound` が空でない場合のみ接続するようにした。

## Files Changed
- `src/win32/ui.cpp`

## Commands Run
```sh
rg -n "opnmon.Init\(|SetSoundMonitor\(|GetOPN1\(|GetSound\(" src/win32/ui.cpp src/win32/vmops.h src/win32/vmops.cpp
sed -n '130,152p' src/win32/ui.cpp
sed -n '1,220p' src/win32/vmops.h
sed -n '130,190p' src/win32/vmops.cpp
```

## Results
- monitor wiring の起点は次の形へ変更:
  - `opnmon.Init(vmops ? vmops->GetOPN1() : core.GetOPN1(), vmops ? vmops->GetSound() : core.GetSound());`
  - `PC8801::WinSound* sound = vmops ? vmops->GetSound() : core.GetSound();`
  - `if (sound) sound->SetSoundMonitor(&opnmon);`
- `core.GetOPN1()`/`core.GetSound()` の直接参照は fallback 時のみ残し、通常経路は vmops ベース。
- WSL 上での実機ビルドは引き続き未実施。

## Behavior Preserved
- monitor の初期化タイミングと接続先は変更なし（`opnmon` へ同じ `core`-提供の OPN/Sound 参照を渡す）。
- 既存の `core` バインド順・ライフサイクル手順は変更なし。

## Risks / Unknowns
- `vmops` が未初期化の理論ケースでは従来 `core` 直接参照へフォールバック。
- MSVC/VC2008 での runtime 検証（起動〜シャットダウン）が必要。

## Questions
- 次 Step31 として残る `core.*` 直呼び出し（`core.Wait(false)/Reset()/Cleanup()` 系など）をどこまで除去する方針で進めますか？
