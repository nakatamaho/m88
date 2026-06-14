# Phase 5 WinCore/WinUI Operation Boundary Step 34 Inventory

## Scope
- Step34 は Step31-33 の `Start/Cleanup/Reset` 寄せ完了後に、`WinUI` 側の `core.*` 直呼び出しの残存を棚卸しし、次の移行候補を定義する。
- 実装は行わず確認のみ。

## Checked Points
- `src/win32/ui.cpp` の `core.` 呼び出し箇所を再スキャン。

## Findings
- 起動/終了/起動時 reset の直接呼び出しは基本 fallback 形になっている。
- `core` 直呼び出しの残存（主に vmops 未初期化保険）:
  - `vmops ? vmops->Start() : core.Wait(false)`
  - `vmops ? vmops->Reset() : core.Reset()`（`InitM88`）
  - `core.Cleanup()`（`vmops` 未使用時のみ）
- `WinUI::Reset()` / `WinUI::ApplyConfig()` は既に vmops 経由優先で、vmops 未設定時のみ `core` フォールバック。
- 一時的な `core.Get*` 参照は、初期化前/終了時の monitor 接続/初期化で `vmops ? vmops->... : core...` 形式。
- 他、`core.Reset()` / `core.ApplyConfig()` の直接呼び出しは非 vmops 分岐を残すもののみ。

## Risk & Note
- 既存の vmops 不在パス（`core` フォールバック）を残す限り、挙動変更は最小。
- 次 step の対象は「non-fallback 依存」を削除する前に、`vmops` 生存保証の強化（初期化順/破棄順）を別途設計してから進めるのが安全。

## Commands
```sh
rg -n "\bcore\." src/win32/ui.cpp
```

## Suggested Next Step
- 次 Step35 として、`WinUI::ApplyConfig()` と `WinUI::Reset()` の vmops fallback をそのまま維持しつつ、
  `WinUI`/`WinCore` `lifecycle` 呼び出しの順序を壊さない形で `WmInitMenu` 以外の read-only 呼び出しをさらに掃除し、`Apply` 系を対象外にしないまま進む。
