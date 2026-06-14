# Phase 5 WinCore/WinUI Operation Boundary Step 37 Report

## Scope
- Very small implementation step.
- `WinUI::InitM88` の起動フローを `vmops` 実体前提へ寄せ、`core` のフォールバック式参照を減らす。

## Changes Made
- `src/win32/ui.cpp` の `WinUI::InitM88` において:
  - `vmops ? vmops->Start() : core.Wait(false);`
    → `vmops->Start();`
  - `vmops ? vmops->Reset() : core.Reset();`
    → `vmops->Reset();`
- 先行ステップで追加した `VMOperations::Init` 経由の `core.Init` 実行経路はそのまま継続。

## Files Changed
- `src/win32/ui.cpp`
- `tools/refactor/phase5_wincore_winui_operation_step37_report.md`

## Commands Run
```sh
rg -n "vmops \\? vmops->Start\\(\\) : core\\.Wait\\(false\\)|vmops \\? vmops->Reset\\(\\) : core\\.Reset\\(\\)" src/win32/ui.cpp
rg -n "vmops->Start\\(|vmops->Reset\\(" src/win32/ui.cpp
git diff -- src/win32/ui.cpp
git diff --check
```

## Result
- `WinUI` 起動時の `core` 依存をさらに削減し、既に存在する `VMOperations` への初期化委譲（`vmops->Init(...)`）と整合。
- 変更は呼び出しルートの一本化のみで、`Wait(false)` / `Reset` の挙動自体は `vmops->Start()/Reset()` が内部で呼ぶ既存 `WinCore` 実装に委譲されるため、既存シーケンスは維持。
- 参照先の読み替えのみで、引数やロジックは変更していない。

## Risks / Notes
- `vmops` 未初期化状態で `InitM88` に到達する経路があれば停止するため、初期化順序がより前提になります。
- 現在の通常起動順序では `vmops` は `InitM88` 冒頭で `new VMOperations` され、`Init` に成功時に `Bind` されるため問題なし。

## User-Side Runtime Verification Needed
- `tools/windows/build_vc2008.cmd Release`
- 確認項目:
  - writetag CRC 出力（writetag）
  - 起動確認（M88）
  - clean shutdown 到達
  - D88 ゲーム動作 + disk access（可能なら）
  - snapshot save/load（任意）
  - 音
  - メニューを開いて既知項目（PCM / Dump / モード表示）が従来どおり
  - 新規 warning/dialog/crash が増えていないこと
