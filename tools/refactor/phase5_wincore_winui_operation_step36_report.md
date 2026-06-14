# Phase 5 WinCore/WinUI Operation Boundary Step 36 Report

## Scope
- Very small implementation step in Phase 5 WinCore/WinUI operation boundary.
- Goal: route VM initialization through `VMOperations` instead of calling `WinCore::Init` directly from WinUI.

## Changes Made
- `src/win32/vmops.h`
  - `VMOperations::Init()` のシグネチャを `WinCore* core` を受け取る形に更新。
- `src/win32/vmops.cpp`
  - `VMOperations::Init()` を実装。
  - 具体的には、受け取った `WinCore*` に対して `WinCore::Init(...)` を実行し、成功時に `Bind()` を行って facade を有効化。
  - 失敗時は `false` を返し、既存挙動（初期化失敗は `InitM88` 中断）を維持。
- `src/win32/ui.cpp`
  - `WinUI::InitM88()` 内の `core.Init(...)` 呼び出しを `vmops->Init(...)` 呼び出しへ置換。
  - それに伴う `vmops->Bind(&core, ...)` の直呼び出しを削除（`vmops->Init` の成功時バインドで吸収）。

## Commands Executed
- `rg -n "vmops->Init|core\\.Init\\(this"` src/win32/ui.cpp
- `git diff -- src/win32/ui.cpp src/win32/vmops.h src/win32/vmops.cpp`

## Results
- `WinUI` の初期化経路における `core.Init` の直接呼び出しが `VMOperations::Init` 経由へ統一されました。
- `core` への `Bind` は `VMOperations` 内部で成功時のみ行うため、初期化成功と VM 所有状態の一致を保っています。
- 既存の `core.Reset()/core.Wait()` フォールバック分岐、`core.Cleanup()` フォールバック、および監視/描画初期化での読み取り経路は変更していません。

## Risks / Notes
- 変更は呼び出し導線の置換で、`WinCore` の内部ロジックを変更していません。
- ただし、`VMOperations::Init` の振る舞いは `win32` 側の初期化順を維持しつつ `core` の `Init` 成否と `Bind` の整合を管理するため、次回の検証で順序が崩れていないか確認が必要です。

## Runtime Verification Needed (User Side)
上記変更後、実機での確認は以下を実施してください:

- Writetag CRC の確認（`writetag` が出力）
- VC2008/VC8 Express Release|Win32 rebuild（成功）
- 起動確認（`M88`）
- clean shutdown まで到達
- D88 ゲーム起動 / disk access
- `snapshot save/load`（任意）
- 音再生
- メニュー open（既知の PCM / Dump / モード系表示）
- 新規 warning / dialog / crash が増えていないこと
