# Phase 5 WinCore/WinUI Operation Boundary Step 28 Report

## Changes Made
- `WinCore/WinUI` 境界で 1 箇所残っていた `core.SetVolume(...)` 依存を整理し、
  `WinUI::M88ChangeVolume()` から `VMOperations` 経由に変更。
- `src/win32/vmops.h` に `SetVolume(PC8801::Config* config)` を追加。
- `src/win32/vmops.cpp` に `VMOperations::SetVolume` を実装し、`core->SetVolume(config)` を委譲。
- `src/win32/ui.cpp` の `M88ChangeVolume` で直接 `core` を呼ばないように変更。

## Files Changed
- `src/win32/vmops.h`
- `src/win32/vmops.cpp`
- `src/win32/ui.cpp`

## Commands Run
```sh
git status --short
sed -n '1,240p' src/win32/vmops.h
sed -n '1,220p' src/win32/vmops.cpp
perl -0pi -e 's/\r?\n\tif \(c\)\r?\n\t\tcore\.SetVolume\(\(PC8801::Config\*\) c\);/\n\tif (c && vmops)\n\t\tvmops->SetVolume((PC8801::Config*) c);/g' src/win32/ui.cpp
rg -n "core\.SetVolume\(|vmops->SetVolume" src/win32/ui.cpp src/win32/vmops.*
git diff -- src/win32/vmops.h src/win32/vmops.cpp src/win32/ui.cpp
git diff --check
```

## Results
- `core.SetVolume` の UI 直呼び出しは削除し、`VMOperations` 経由に置換。
- `VMOperations::SetVolume` はコア未バインド時は no-op（既存のガード規約に従う）。
- 文字列/ロジックの意味変更はなく、`M88ChangeVolume` の呼び出し元側挙動を保持。
- ビルド実行はこの環境（WSL）では実施不可（MSVC 不在）。
- ローカル整合チェック: `git diff --check` はクリーン。

## Behavior Preserved
- 設定値に対して音量設定が直接 `core` 経由でのみ反映される経路は維持され、委譲先を `vmops` に置換。
- snapshot/config/reset/mount/sound monitor/lifecycle のロジックには手を入れていない。
- `VMOperations`/`WinCore` の所有権構造や初期化順を変更していない。

## Risks / Unknowns
- `VMOperations` が未初期化のタイミングで `M88ChangeVolume` が走ると無効化される（これ以前と同等でない可能性があるが、現在の起動時シーケンスでは既存の `vmops->Bind()` 後に到達する想定）。
- 実際の Windows 実行環境で `writetag` と起動/音量変更系の手動確認が必要。

## Questions
- 次の step へ進む順序: 次は `M88ChangeVolume` 以降の monitor/wiring 系（`opnmon.Init(core.GetOPN1(), core.GetSound())`）を別 step として扱う方針で進めるか。
