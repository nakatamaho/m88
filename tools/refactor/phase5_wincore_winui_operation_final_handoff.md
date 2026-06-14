# Phase 5 WinCore/WinUI Operation Boundary — Final Handoff (Step 40+)

## Scope

- `WinCore` と `WinUI` の責務分離を進める `Phase 5` の `WinCore/WinUI operation boundary` を最終整理する。
- 本報告は実装内容の要約、移行完了状況、確認結果、次フェーズ移行時の留意点をまとめる。

## Commited progression summary

Boundary work was executed incrementally from `step1` onward (design/inventory + small changes), then finalized with `step39` (all `ui.cpp` mutating/config paths switched to `vmops`) and `step40` inventory cleanup.

- Current HEAD: `57fedbf`  
  `Phase 5 WinCore/WinUI operation boundary step40 inventory`
- Main code changes ended at `step39` and are already in history.
- `Step40` is inventory-only (`tools/refactor/phase5_wincore_winui_operation_step40_inventory.md`).

## Migration coverage (practical result)

- `WinUI`→`WinCore` の主要ライフサイクル/操作呼び出しの `core.*` 直参照を段階的に `VMOperations` へ寄せた。
  - init, start, reset, cleanup
  - apply config
  - snapshot save/load
  - sound monitor wiring (GetSound/GetOPN1 wrappers)
  - PCM録音系の命令ルート
  - volume/CPU dumpメニュー状態
- WmInitMenu などの read-only 参照は `VMOperations` wrapper ベースへ統一（fallback 無し）。
- `VMOperations` の API追加 (`GetOPN1`, `GetSound`, `SetVolume`, `GetCPU1DumpState`, `GetCPU2DumpState`, `Start`, `Reset`, `Cleanup`, `ApplyConfig`, `SaveSnapshot`, `LoadSnapshot`, `IsN80...`, `IsCD...`, `IsSoundDumping`) を活用して `core` 依存を圧縮。

## Current dependency status

- `rg -n "\bcore\." src/win32/ui.cpp` の結果:
  - ランタイム実行パスの直接 `core.*` は残存せず。
  - 既存コメント内の履歴参照のみ残存（現行運用上、未コメント領域は `vmops` 経由）。
- `src/win32/ui.cpp` での `vmops` 利用は、`WinUI` が UI 固有責務を担いながら `core` 直接依存を避ける形に収束。

## Runtime verification (user-side)

最終確認項目は全て合格（ユーザー実施）:
- writetag CRC 出力確認
- M88 起動 / clean shutdown
- D88 ゲーム＋disk access
- snapshot save/load
- 音再生
- PCM 録音（任意）・CPU dump メニュー状態
  - CPU dump は従来どおり `Release Win32 + Z80_x86` で `-1` のため `gray`（既知仕様内）
- 新規 warning / dialog / crash 増加なし

## Risks & follow-up

- `vmops` が未初期化の異常系では一部 no-op/skip となる安全側挙動を採用している箇所あり。
- この Phase の次は、`WinCore/WinUI` の境界そのものは「ハンドオフ完了」として扱い、残存の移植対象は次のバウンダリ (`CritSect`, `FileIO`, `types`, 他 platform abstraction) へ展開する。
- `CPU dump` が有効化された環境（例: `Z80_x86` 以外）での表示状態は次フェーズ以降で再確認すると安全。

## Notes for next phase

- この境界で行った変更は Windows 挙動保全を優先し、小変更（小分割）で実施済み。
- 次フェーズでは実装よりも、未移行の `Win32` 依存（core側を含む）の設計と低リスク順で分離を継続するのが妥当。
