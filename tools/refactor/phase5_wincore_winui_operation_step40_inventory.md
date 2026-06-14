# Phase 5 WinCore/WinUI Operation Boundary Step 40 Inventory

## Scope

- Final inventory after Step 39 (configuration/reset routing migrated to VMOperations).
- No implementation changes.
- Confirm remaining direct `core.*` runtime dependencies in `src/win32/ui.cpp`.

## Baseline

- Previous pushed commit:
  - `0bf1602` `Phase 5 WinUI/WinCore operation boundary step39`
- User-side runtime確認:
  - writetag CRC output: present
  - 起動/clean shutdown/D88ゲーム/disk access/音/snapshot save/load: 問題なし
  - CPU dump menu state: CPU dump 無効（`-1`）として従来どおり gray 状態
  - 新規 warning/dialog/crash: なし

## Scan Result

- `rg -n "\\bcore\\." src/win32/ui.cpp`
  - runtime paths: direct `core.` references are only inside commented code.
  - active runtime paths: no direct `core.*` calls remain in `ui.cpp`.
- `vmops` is used directly for:
  - init/start/reset/cleanup/apply/set-volume
  - menu-state read wrappers
  - snapshot save/load
  - sound/OPN monitor wiring
- Remaining guards are mostly null-safe fallback guards (e.g. `vmops ? vmops->SaveSnapshot(...) : false;`), intentional for safety under abnormal paths.

## Status by Remaining Area

- Direct call migration:
  - lifecycle/mutating menu/config paths: `vmops` へ移行済み
  - snapshot paths: `vmops` へ移行済み（`vmops` 未初期化時は false/no-op）
  - read-only menu query: `vmops` wrapper 経由
- Not touched in this phase:
  - 全 `src/win32/ui.cpp` 以外のファイル（今フェーズでは扱わない）
  - `WinCore` / `VMOperations` / `vmops` の実装本体のロジック

## Risks

- `vmops` null/未初期化時のフェイルソフト動作が `core` フォールバック（または false）で残るため、次フェーズで `vmops` 生存保証を前提にするか判断が必要。
- `cpu dump` は `Release Win32 + Z80_x86` 側で `GetDumpState() == -1` で既存どおり gray となる。

## Recommendation (Next)

- Step40 as inventory is complete.
- If moving forward, next phase should start with the next low-risk platform boundary (e.g. further reduction of Win32-owned helper dependencies outside `ui.cpp`), or finalize this phase with a boundary handoff report.
