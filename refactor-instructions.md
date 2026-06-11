# refactor-instructions.md — m88 (nakatamaho fork) 段階的リファクタリング指示書

対象リポジトリ: `https://github.com/nakatamaho/m88`
調査時点 HEAD: `1c48d83` ("SSG-EGとCSMの実装を修正 SSG-EGはXM7由来")
本書は実装担当モデル (Codex / Opus / Claude Code 等) への作業指示書である。
本書に書かれていない大規模変更を行ってはならない。不明点は実装せず質問すること。

---

# Objective

* m88 (PC-8801 系エミュレータ、Windows 専用コードベース) を、SDL2 backend を追加しやすい構造へ**段階的に**リファクタリングする。
* 対象環境として Windows (MSVC) / MinGW / Linux / macOS を見据える。
* **既存 Windows 版の挙動を壊さない**ことを最優先とする。エミュレーションコア (`src/pc88`, `src/devices`, `src/common`) の正しさは見た目より優先する。
* 大規模 rewrite は行わない。検証可能な小さい変更を積み重ねる。
* 文字コード (CP932 → UTF-8)、ファイル名の大文字小文字、build system の整理は、**挙動変更を伴わないことを機械的に検証できる範囲**で段階的に行う。
* SDL2 対応そのものは、platform boundary (抽象境界) を確立した**後**にのみ着手する。本書の範囲では SDL2 backend は「設計提案」までであり、承認なしに実装しない。

---

# Project Understanding

すべて調査時点のリポジトリ内容に基づく。「不明」と書いた項目は推測で埋めないこと。

## 何のプロジェクトか

* cisc 氏作の PC-8801 シリーズエミュレータ M88 (最終公式版 M88_221, 2003年) の私家版 fork。
* fork 側の追加: 最近のコンパイラ対応、英語101キーモード、ウインドウ座標保存、PC-8001mkIISR ひらがなフォント (FONT80SR.ROM、参照箇所 `src/pc88/crtc.cpp`)、fmgen 修正、c86ctl (G.I.M.I.C / OPNA 実チップ) 対応、SSG-EG/CSM 修正等 (git log および README.md より)。
* 動作環境 (README.md): Windows Vista 以降。**現状 Windows 以外のターゲットは存在しない。**

## Build system

* `M88_2008.sln` + `M88_2008.vcproj` (Visual Studio 2008 形式)。構成: Debug/Release/Tuning × Win32/x64。
* レガシー: `M88.dsp` / `M88.dsw` (VC6)。サブプロジェクト `cdif/cdif.dsp`, `diskdrv/diskdrv.dsp`, `sample1/sample1.dsp`, `sample2/sample2.dsp` は **VC6 .dsp しかない**。
* Makefile / CMake / configure / CI (.github) / テスト / AGENTS.md / CLAUDE.md: **存在しない。**
* `M88_2008.vcproj` 内のパス表記はディスク上と大文字小文字が不一致 (`src\Win32\...`, `src\PC88\...` と書かれているが実ディレクトリは `src/win32`, `src/pc88`)。Windows の case-insensitive FS でのみ成立。
* `M88_2008.vcproj` が参照するが**ディスク上に存在しない**ファイル: `m88dev.html`, `memo.txt`, `src/win32/romeo/juliet.cpp`, `juliet.h` (juliet は少なくとも Release 構成で ExcludedFromBuild=true)。これらが他構成でビルドを壊すかは不明。
* precompiled header: `headers.h` を全プロジェクトで PCH として使用 (`PrecompiledHeaderThrough="headers.h"`)。

## ディレクトリと責務

| ディレクトリ | 責務 | platform 依存度 |
|---|---|---|
| `src/pc88` | エミュレーションコア。`PC88` クラス (= `Scheduler` + `ICPUTime`, `pc88.h`) が VM 本体。memory, crtc (描画生成), screen (フレーム合成), fdc/fdu/floppy/diskmgr (FDD・D88系イメージ), pd8257 (DMA), intc, sio, pio, subsys (サブCPU), opnif (FM音源接続), beep, calender, mouse, joypad, kanjirom, tapemgr (T88 テープ), ioview/memview (モニタ用) | 構造上はコアだが、後述の通りコンパイル時に Win32 へ依存 |
| `src/devices` | Z80 コア2種 (`Z80c.cpp`: C++版 2374行 / `Z80_x86.cpp`: VC6 inline asm 489ブロック、32bit専用)、fmgen/opna/psg/opm (FM・SSG 音源生成)、fmtimer、Z80 逆アセンブラ・デバッグ・比較実行 | Z80_x86 のみ x86/VC6 固定。それ以外はほぼ可搬 |
| `src/common` | `Device`/`IOBus`/`MemoryManager` (device.h, memmgr.h)、`Scheduler` (schedule.h)、`Draw` 抽象インターフェース (draw.h)、サウンドバッファ (soundbuf, sndbuf2, srcbuf, lpf)、error、lz77d | `sndbuf2.h`/`soundbuf.h`/`srcbuf.h` が `critsect.h` (Win32) を include |
| `src/if` | プラグイン (拡張モジュール DLL) 用 COM 風インターフェース。`IFCALL`=`__stdcall`, `REFIID`, GUID を使用 | ABI が Win32 規約に依存 |
| `src/win32` | UI・platform 層全部。詳細は下記 | 完全に Win32 |
| `src/win32/romeo` | ROMEO / G.I.M.I.C (c86ctl) 実 FM チップハードウェア制御 | Win32 + 実ハード |
| `src/zlib` | 同梱 zlib 1.2.8。利用者は `src/win32/wincore.cpp` (スナップショット圧縮) のみ | 可搬 |
| `cdif/` | CD-ROM 拡張モジュール (ASPI 経由)。独立 DLL | Win32 + ASPI (Vista以降では動作不明) |
| `diskdrv/` | DiskDrive 拡張モジュール + Z80 アセンブリ ROM ソース (.asm) | Win32 DLL |
| `sample1/`, `sample2/` | 拡張モジュールのサンプル | Win32 DLL |

## src/win32 の主要構成

* entry point: `main.cpp` の `WinMain`。`GetModuleFileName` で exe の位置を取得し `m88dir`/`m88ini` (グローバル変数) を設定 → `WinUI::Main(cmdline)`。
* `ui.cpp` (2041行): `WinUI` クラス。ウインドウ生成、message loop、メニュー処理 (IDM_ 113箇所)、ドラッグ&ドロップ、コマンドライン処理 (`ApplyCommandLine`)、fullscreen 切替等が**単一クラスに集中**。
* `wincore.cpp`: `WinCore`。VM とUI の接続、スナップショット save/load (`SNAPSHOT_ID "M88 SnapshotData"`, `SnapshotHeader` を raw 書き出し + zlib 圧縮)。
* 描画: `windraw.cpp` (`WinDraw` = `Draw` 実装) が `WinDrawSub` サブドライバを選択: `DrawGDI` / `DrawDDS` (DirectDraw surface) / `DrawDDW` (DirectDraw window) / `DrawD2D` (Direct2D, `winexapi` で動的ロード)。
* 音声: `winsound.cpp` (`WinSound` : `PC8801::Sound` 派生) がドライバ選択: `DriverWO` (waveOut) / `DriverDS` / `DriverDS2` (DirectSound)。共通基底は `sounddrv.h` の `WinSoundDriver::Driver` (`Init(SoundSource*, HWND, rate, ch, buflen)` — **HWND がシグネチャに入っている**)。
* 入力: `WinKeyIF.cpp` (VK_ 直接マッピング、106/PC98/101 キータイプ)、`WinJoy.cpp` (winmm `joyGetPos`)、`winmouse.cpp`。
* タイミング: `sequence.cpp` (`Sequencer`: `_beginthreadex` でエミュレーション専用スレッド、speed/frameskip 制御)、`timekeep.cpp` (`TimeKeeper`: QueryPerformanceCounter、フォールバックで timeGetTime + timeBeginPeriod(1))。
* 設定: `88config.cpp` — `GetPrivateProfileInt/String`, `WritePrivateProfileString` による **exe と同じディレクトリの M88.ini**。レジストリは不使用 (確認済み: RegOpenKey 等の呼び出しなし)。
* デバッガ/モニタ群: `winmon` 基底 + `memmon`, `codemon`, `iomon`, `basmon`, `regmon`, `loadmon`, `soundmon`, `mvmon` (Win32 ダイアログ)。
* 拡張モジュール: `extdev.cpp` / `module.cpp` — `LoadLibrary` + `__cdecl` factory で DLL プラグイン接続。
* `M88.rc`: `LANGUAGE LANG_JAPANESE`, `#pragma code_page(932)`。日本語メニュー・ダイアログ・文字列テーブル。

## コアと platform の結合状態 (最重要事実)

ディレクトリ上は分離されているが、**コンパイル依存はまったく分離されていない**:

1. `src/pc88`, `src/common`, `src/devices` の**すべての .cpp** が `#include "headers.h"` (= `src/win32/headers.h`) を先頭に持つ。headers.h は `<windows.h>`, `<ddraw.h>`, `<dsound.h>`, `<mmsystem.h>` 等を含む PCH であり、`using namespace std;` をグローバルに行う。
2. `src/win32/types.h` がコア全体の基本型定義だが、`intpointer` を `LONG_PTR` (Win32 型) で定義し、`ENDIAN_IS_SMALL` / `ALLOWBOUNDARYACCESS` / `USE_Z80_X86` (非 _WIN64 時) をハードコードする。
3. コアが `FileIO` (`src/win32/file.cpp`, 内部は `::CreateFile`/`::ReadFile`) を直接使用: `diskmgr`, `tapemgr`, `memory`, `kanjirom`, `subsys`, `crtc`, `devices/opna`。
4. コアが `CritSect.h` (Win32 `CRITICAL_SECTION`) を直接使用: `diskmgr.h`, `fdc.cpp`, `common/sndbuf2.h`, `common/soundbuf.h`, `common/srcbuf.h`。
5. `src/if/ifcommon.h` のプラグイン ABI が `__stdcall` (`IFCALL`/`IOCALL`)・`REFIID`・GUID に依存。
6. `src/pc88/config2.h` に `DirectSound` という設定シンボルが現れるが、このファイル自体が未参照 (後述)。

逆に、抽象として既に存在するもの:
* `src/common/draw.h` の `Draw` 抽象クラス (Init/Lock/Unlock/DrawScreen/SetPalette/Flip)。コアは `Draw*` 経由で描画する。**SDL2 video backend はこの境界に挿せる可能性が高い。**
* `src/pc88/sound.h` の `Sound` クラスと `SoundSource`/`ISoundSource`。**SDL2 audio backend の挿入点候補。**
* `WinSoundDriver::Driver` (sounddrv.h) — ただし `HWND` がシグネチャに含まれるため、そのままでは platform 中立でない。

## 文字コードの現状 (機械的に分類済み)

* ASCII のみ: 105 ファイル
* UTF-8: 2 ファイル (`README.md`, `M88_2008.sln`)
* CP932 (Shift_JIS): **178 ファイル** (テキスト全体の大半。コア・win32・サブプロジェクト・.dsp・HISTORY.TXT を含む)
* バイナリ: 5 (.ico/.bmp)
* C/C++/.rc のうち、**非 ASCII がコメント以外 (文字列リテラル・.rc 表示文字列) に存在する**のは以下の 14 ファイル:
  * `src/win32/M88.rc`, `cdif/src/cdif.rc`, `sample2/src/sample2.rc` (日本語メニュー/ダイアログ/文字列テーブル)
  * `src/win32/ui.cpp`, `about.cpp`, `wincfg.cpp`, `wincore.cpp`, `windraw.cpp`, `winmon.cpp`, `winsound.cpp`, `WinJoy.cpp` (日本語メッセージ文字列)
  * `src/common/error.cpp` (日本語エラーメッセージ)
  * `src/pc88/diskmgr.cpp` (日本語文字列)
  * `src/devices/Z80Test.cpp`
* それ以外の CP932 ファイル約 150 個は**コメントのみ**に日本語を含む (機械的検証済み。実装時は再検証すること)。

## ファイル名・大文字小文字の現状

* 命名は混在: `CritSect.h`, `DrawDDS.cpp`, `WinJoy.cpp`, `Z80c.cpp`, `Z80Debug.cpp` (大文字混じり) と `windraw.cpp`, `fdc.cpp` (小文字) が同居。
* **case-mismatch な #include が 31 箇所**存在する (機械的照合済み)。代表例:
  * `src/pc88/pc88.h`, `base.h`, `Z80Debug.h`, `Z80Test.h`: `#include "Z80C.h"` → 実ファイルは `Z80c.h`
  * `src/pc88/fdc.cpp`: `#include "FDC.h"`, `"FDU.h"` → 実ファイルは `fdc.h`, `fdu.h`
  * 多数のファイル: `#include "critsect.h"` → 実ファイルは `CritSect.h`
  * `src/win32/windraw.cpp`: `"drawgdi.h"`, `"drawdds.h"`, `"drawd2d.h"` → 実ファイルは `DrawGDI.h`, `DrawDDS.h`, `DrawD2D.h`
  * `src/win32/ui.h`: `"WinDraw.h"` → `windraw.h`、`wincore.h`: `"winjoy.h"` → `WinJoy.h`、ほか
* 同名で大文字小文字のみ異なるファイルの**衝突は存在しない** (checkout 自体は case-insensitive FS でも可能)。
* `makefile`/`Makefile` の混在は**存在しない** (Makefile 自体がない)。
* 結論: **Linux/macOS では checkout は可能だが、現状の include のままではコンパイル不可能** (31箇所の解決失敗)。

## データの流れ (証拠に基づく概要)

* CPU: `PC88::Proceed(us, clock, eff)` を `Sequencer` のスレッドが時間予算単位で呼ぶ。`Scheduler` (common/schedule) がイベント駆動。main CPU と sub CPU (subsys) の2つの Z80。
* memory/I/O: `MemoryManager`/`IOBus` (common/device.h, memmgr.h)。Z80_x86 使用時は `MEMCALL=__stdcall` 規約 (types.h)。
* video: crtc + screen が `Draw::Lock` で得たバッファへ描画 (`packed` 型による 32bit 一括書き込み、`ALLOWBOUNDARYACCESS` 前提 = **little-endian + 非アラインアクセス前提**) → `WinDraw::DrawScreen`。
* audio: fmgen/opna/psg (`ISoundSource::Mix`) → `pc88/sound.cpp` がミキシング → `common` のサウンドバッファ → `WinSound` ドライバが DirectSound/waveOut へ。実チップ出力 (romeo/piccolo) も opnif から分岐。
* input: `WinKeyIF` が VK 状態をエミュレータ側キーマトリクスへ変換。joypad は `WinJoy` 経由。
* disk: `DiskManager`/`DiskImageHolder` (diskmgr) が FileIO でイメージを保持し、FDC/FDU がアクセス。バックグラウンド処理のため `CriticalSection` 使用。
* snapshot: `WinCore::SaveShapshot` が `SnapshotHeader` + 各デバイスの状態 (`GetStatus`系, pcinfo.h) を raw 構造体で書き出し、zlib 圧縮。**構造体レイアウト = ファイルフォーマット**であり、コンパイラ・パディング・アーキテクチャ依存。

## 検証コマンドの現状

* 自動テスト・lint・CI: **存在しない**。
* ビルド: Visual Studio 2008 以降 (vcproj のアップグレード込み) でのみ可能と推定される。**本環境 (Linux コンテナ) では MSVC が無いためベースラインビルドは実行不能。確認できていない。**
* `Z80Test` (2エンジン比較実行) と `filetest.cpp` (CRC によるファイル検証、about.cpp/ui.cpp から参照) が既存の検証資産。

## 不明事項

* 現行の Visual Studio (2019/2022) で M88_2008.vcproj が変換・ビルドできるか: 不明。
* `juliet.cpp` 欠落が Debug/Tuning 構成のビルドを壊すか: 不明。
* cdif (ASPI) が現代の Windows で動作するか: 不明 (ASPI は Vista 以降標準では存在しない)。
* fork 元 (cisc 版) との正確な差分範囲: git 履歴は fork 後のみのため網羅は不明。
* fmgen のライセンス・由来コードの改変可否の詳細: `src/devices/readme.txt` 等を実装前に確認すること。

---

# Behaviors To Preserve

以下は調査で確認された、**壊してはいけない既存挙動**。変更がこれらに触れる場合は Stop And Ask。

1. 既存 Windows ビルドが (現状ビルド可能な構成において) 通ること。
2. 起動手順: `M88.exe` 起動 → exe と同じディレクトリの `M88.ini` 読み込み (`main.cpp` の `InitPathInfo`)。**ini のパス規則と内容フォーマット (`GetPrivateProfileString` 形式) は変更禁止。**
3. ROM 読み込み: exe ディレクトリからの各種 ROM (N88 系、`FONT80SR.ROM` 等) の読み込み挙動。
4. ディスクイメージ (D88 系、`DiskImageHolder` の multi-disk 対応・書き戻し・サイズ変更ロジック) およびテープ (T88, tapemgr) の読み書き挙動。
5. スナップショット: `"M88 SnapshotData"` ヘッダ、`SnapshotHeader` 構造体レイアウト、zlib 圧縮形式。**既存スナップショットが読めなくなる変更は禁止。**
6. キーボード割り当て (106/PC98/英語101 の各モード、`WinKeyIF` のテンキー・矢印変換挙動)。
7. ジョイパッド (winmm 経由、ボタン入れ替えオプション含む)。
8. 画面: GDI/DirectDraw/D2D 各ドライバの選択挙動、15KHz/24KHz モード、デジタル/アナログパレット、fullscreen/window 切替、ウインドウ座標保存オプション。
9. 音声: waveOut/DirectSound ドライバ選択、サンプルレート・バッファ長設定、OPN/OPNA の 44h/a8h 配置設定、CMD SING、c86ctl (G.I.M.I.C) 出力。
10. タイミング: クロック設定、ノーウェイト、FDD ウェイト、speed 500–2000‰、フレームスキップ。fmgen の音色・テンポ (直近コミットで修正された SSG-EG/CSM, ADPCM 挙動を含む) は**1バイトも根拠なく触らない**。
11. reset / BASIC モード切替 (N/N80/N80V2/N88V1/V1H/V2/V2CD)。
12. コマンドライン処理 (`WinUI::ApplyCommandLine`) の互換性。
13. デバッガ・モニタ群 (memmon/codemon/iomon/basmon/regmon/loadmon/soundmon) の表示・操作。
14. メニュー・ダイアログの日本語表示 (M88.rc, code_page 932)。**表示文言のバイト列・見た目を変えない。**
15. 拡張モジュール DLL の ABI (`__stdcall`/GUID/`__cdecl` factory)。既存のサードパーティモジュールが接続できなくなる変更は禁止。
16. `writetag.cpp` / `diskdrv/*.asm` などの周辺資産はそのまま残す。

---

# Non-Negotiables

実装担当モデルは以下を厳守する。

1. 作業開始時に必ず `git status --short` を確認し、既存の未コミット変更と自分の変更を混ぜない。
2. 編集前に baseline の build / run / test 結果 (実行できない場合は「実行不能であること」) を記録する。
3. 変更は小さく、revert 可能な単位で commit する。
4. 無関係な整形・命名変更・「ついで」のリファクタリングを混ぜない。
5. 既存挙動を勝手に変えない。エミュレーションコアの timing / I/O / CPU / audio / video 挙動を根拠なく変更しない。特に `fmgen.cpp`, `opna.cpp`, `psg.cpp`, `Z80c.cpp`, `crtc.cpp`, `memory.cpp`, `fdc.cpp` は本書のどのフェーズでもロジック変更禁止。
6. 正しさが不明な場合は実装を止めて質問する。
7. 各フェーズごとに検証し、Reporting Format に従って報告する。
8. 大きな削除、全面 rewrite、backend 置換は承認なしに行わない。
9. Windows backend を壊して SDL2 に置き換えるのではなく、**まず境界を作る**。SDL2 化は platform abstraction 確立後。
10. 互換性リスクがある変更 (snapshot, ini, image format, plugin ABI, 表示文字列) は提案に留める。
11. 文字コード変換は、挙動不変を機械的に検証できる範囲 (原則コメントのみのファイル) に限定する。
12. 文字コード変換とファイル名変更を同じ commit に混ぜない。ファイル名変更と build system 変更を同じ commit に混ぜない。
13. case-only rename は二段階 rename (`git mv FDC.h __tmp__ && git mv __tmp__ fdc.h`) で行う。
14. 本リポジトリに `makefile` は存在しないため新規に作る場合は `Makefile` (または CMake) とし、既存 .dsp/.sln/.vcproj は削除しない。
15. ファイル名・ディレクトリ名の変更は機械的一括変換せず、include・vcproj・dsp・rc への影響を確認してから行う。
16. `src/zlib` (同梱 zlib 1.2.8) と `src/devices` の fmgen 系は外部由来コードとして扱い、ライセンス・由来を確認せずに改変・削除・差し替えをしない。
17. `_CrtSetDbgFlag` 等の CRT デバッグ機構、`Z80Test`/`Z80Debug` の比較実行機構は削除しない (貴重な検証資産)。

---

# Stop And Ask Conditions

次のいずれかに該当したら作業を止め、質問として報告する。

* baseline build が通らない、または build 環境 (MSVC) が無くベースラインを確立できない (→ 本書執筆時点で既知。Phase 0 参照)。
* 起動検証に ROM (実機吸い出し) が必要で検証不能。
* 既存 Windows 挙動と新設計が衝突する。
* snapshot / M88.ini / D88 / T88 / plugin ABI の互換性に影響しうる。
* CPU / memory / I/O / interrupt / timing の意味が確信を持って判断できない。
* audio / video / input の正しい仕様がコードから判断できない。
* 削除候補コードが本当に不要か判断できない (動的参照・vcproj の別構成・拡張モジュールからの参照の可能性)。
* Windows API 依存を抽象化すると挙動が変わりうる (例: `timeBeginPeriod(1)` の有無はタイマ精度に影響する)。
* SDL2 backend と既存 backend の共存方針 (併存ビルドか、ビルド時切替か) を決める必要がある。
* MinGW / Linux / macOS のサポート範囲 (32bit? x64 のみ? Z80_x86 をどうするか) を決める必要がある。
* 文字コード判定が曖昧、非 ASCII が string literal / char literal / macro / `.rc` にある (前掲 14 ファイルは**全て該当**。Phase 1 で無断変換禁止)。
* `.rc` の `#pragma code_page(932)` と UTF-8 化の整合が取れない。
* MSVC / MinGW で文字列リテラルの execution charset の扱いが異なる可能性がある。
* 変換・rename 後に build warning / error が増える。
* 変換対象が外部由来 (zlib, fmgen, c86ctl.h ほか) で、ライセンス上改変してよいか不明。
* vcproj が参照する欠落ファイル (`juliet.cpp` 等) の扱いを決める必要がある。
* case-insensitive FS 上で rename が正しく反映されるか不明。
* 大文字名 (`Z80c.cpp`, `M88.rc`, `HISTORY.TXT` 等) が歴史的・配布物的な意味を持つ可能性がある。

---

# Baseline Commands

**確認済みの事実: 自動化された build / test / lint コマンドは存在しない。**

存在するもの:

* Windows + Visual Studio 2008 (またはアップグレード可能な後継): `M88_2008.sln` を開いてビルド。コマンドラインなら (未検証の参考):
  * `devenv M88_2008.sln /build "Release|Win32"` — **未確認の提案。実行結果を記録すること。**
* VC6 (歴史的): `M88.dsw`。現実的に検証不能と思われる。
* MinGW / Linux / macOS / CMake / Makefile / configure: **存在しない。**
* test / lint: **存在しない。** 内部的検証資産として `CPU_TEST` (Z80Test: 2エンジン比較実行) と `filetest.cpp` がある。
* run: `M88.exe` を ROM 群と同じディレクトリで起動 (README.md / main.cpp より)。ROM は著作物のためリポジトリに含まれない。

**未確認の提案** (実装してよいのは Phase 7 以降、承認後):
* Linux 上での「コンパイルのみ」smoke check (リンク・実行は不可) を、コアファイル単位で行う案。

---

# Debt Map

優先度は SDL2 化への寄与順。各項目の Implementation status を厳守すること。

## Debt 1: 全コアソースが Win32 PCH `headers.h` に依存

- Evidence:
  - `src/pc88/*.cpp` 全ファイル先頭の `#include "headers.h"`
  - `src/win32/headers.h` (windows.h, ddraw.h, dsound.h, mmsystem.h, `using namespace std;`)
  - vcproj `PrecompiledHeaderThrough="headers.h"`
- Why this is debt: エミュレーションコアが Win32 ヘッダ無しでコンパイルできず、SDL2/Linux/macOS ビルドの最大の阻害要因。`using namespace std;` のグローバル汚染も含む。
- Impact: コア全ファイル。
- Risk: 中。include 差し替えはコンパイルエラーを大量に顕在化させるが、実行時挙動は原則変わらない。PCH 設定 (vcproj) との整合に注意。
- Proposed improvement: コア用の中立ヘッダ (例: `src/common/core_headers.h`: 標準C/C++ヘッダ + types のみ) を新設し、コア側 `#include "headers.h"` を段階的に置換。win32 側は現行 PCH 維持。
- Verification: Windows build が同一警告レベルで通ること。可能なら Linux 上でコア単体のコンパイル試行。
- Implementation status: **Needs approval** (Phase 5 で実施。Phase 0–4 では手を付けない)

## Debt 2: `types.h` が `src/win32` にあり Win32 型 `LONG_PTR` に依存

- Evidence: `src/win32/types.h:36` (`typedef LONG_PTR intpointer;`)、同 9行 `ENDIAN_IS_SMALL`、52行 `ALLOWBOUNDARYACCESS`、55行 `#if !defined(_WIN64) #define USE_Z80_X86`
- Why this is debt: コア全体の基本型がwin32 ディレクトリ・Win32 型に依存。`intpointer` は `<cstdint>` の `intptr_t` で代替可能。エンディアン・アライン前提もここに集約されている。
- Impact: コア全体 + 全プラグイン。
- Risk: 低〜中。`intptr_t` 置換は機械的だが、`USE_Z80_X86` の定義位置変更は Z80 エンジン選択 (=挙動) に影響しうる。
- Proposed improvement: types.h を `src/common` へ移設 (または中立版を新設) し、`LONG_PTR` → `intptr_t` (`<cstdint>`)。`USE_Z80_X86` の定義条件は**変えない**。
- Verification: Win32/x64 両構成でビルド・起動。Z80 エンジン選択が変わっていないことをプリプロセッサ出力等で確認。
- Implementation status: **Needs approval** (Phase 5)

## Debt 3: コアが Win32 `FileIO` / `CritSect` を直接使用

- Evidence:
  - FileIO: `src/pc88/diskmgr.h`, `tapemgr.cpp`, `memory.cpp`, `kanjirom.cpp`, `subsys.cpp`, `crtc.cpp`, `src/devices/opna.cpp` が `file.h` を include。実装 `src/win32/file.cpp` は `::CreateFile`/`::ReadFile`。
  - CritSect: `src/pc88/diskmgr.h`, `fdc.cpp`, `src/common/sndbuf2.h`, `soundbuf.h`, `srcbuf.h` が `critsect.h` を include。実装は `CRITICAL_SECTION`。
- Why this is debt: コアのファイル I/O・排他が Win32 API に直結。SDL2/POSIX 移植の必須分離点。
- Impact: ディスク・テープ・ROM 読み込み、サウンドバッファ排他、FDC バックグラウンド処理。
- Risk: 中。FileIO はインターフェースが既に薄い (Open/Read/Write/Seek) ので置換しやすい。CriticalSection は `std::recursive_mutex` 等で代替可能だが、再帰ロックの有無 (CRITICAL_SECTION は再帰可) を確認すること。
- Proposed improvement: FileIO のインターフェースを維持したまま実装を分離 (win32 実装 / stdio 実装)。CriticalSection は同名同インターフェースのまま `std::recursive_mutex` ベースの可搬実装を用意し、Windows では既存実装を維持。
- Verification: Windows build + ディスク読み書き・テープ・スナップショットの動作確認。
- Implementation status: **Needs approval** (Phase 5–6)

## Debt 4: include の大文字小文字不一致 31 箇所

- Evidence: 機械的照合により 31 件。代表: `pc88.h`→`"Z80C.h"` (実体 `Z80c.h`)、`fdc.cpp`→`"FDC.h"`/`"FDU.h"`、多数→`"critsect.h"` (実体 `CritSect.h`)、`windraw.cpp`→`"drawgdi.h"` ほか (全リストは Phase 2.1 で再生成)。
- Why this is debt: Linux/macOS (case-sensitive FS) でのコンパイルを 100% 阻害する。Win32 ヘッダ依存と並ぶ二大阻害要因。
- Impact: ほぼ全ディレクトリ。
- Risk: 低。**include 側の文字列をディスク上の実ファイル名に合わせる修正は挙動不変**であり、Windows ビルドにも影響しない。rename より安全。
- Proposed improvement: 第一段階では「include 文字列を実ファイル名に一致させる」のみ行う (rename しない)。ファイル名自体の正規化 (小文字統一等) は Phase 2 で別途判断。
- Verification: Windows build が通ること。照合スクリプトで mismatch 0 件を確認。
- Implementation status: **Safe to implement now** (Phase 2 前半。include 修正のみ。rename は Needs approval)

## Debt 5: CP932 が 178 ファイル、うち 14 ファイルは文字列リテラル/.rc に日本語

- Evidence: 機械的分類 (Project Understanding 参照)。`M88.rc` は `#pragma code_page(932)` + `LANG_JAPANESE`。
- Why this is debt: 現代のツールチェーン (MinGW, clang, エディタ, grep) で文字化け・警告・誤変換の温床。ただし**実行時文字列とリソースは CP932 であることが仕様**である点に注意。
- Impact: 全体。
- Risk: コメントのみのファイル (約150) は低。文字列リテラル/.rc を含む 14 ファイルは**高** (表示文言のバイト列が変わる)。
- Proposed improvement: Phase 1 でコメントのみのファイルに限定して UTF-8 (BOM なし) 化。14 ファイルと .dsp/.dsw 等は除外し manifest に記録。execution charset の扱い (`/execution-charset:shift_jis`, `-fexec-charset=CP932`) は Phase 7 の提案事項。
- Verification: Phase 1.4 の機械的検証 (CP932 decode == UTF-8 decode の Unicode 一致、改行保存、ビルド通過)。
- Implementation status: コメントのみファイル: **Safe to implement now** (Phase 1)。14 ファイル + .rc + .dsp: **Proposal only**

## Debt 6: `Z80_x86.cpp` — VC6 専用 32bit inline asm

- Evidence: `src/devices/Z80_x86.cpp` (冒頭コメント「VC6 以外でコンパイルすることは考えない方がいい」、`__asm` 489 ブロック)、`types.h:55` で非 _WIN64 時に有効化、`PTR_IDBIT` 機構。
- Why this is debt: 移植対象外のコード。x64 構成では既に `Z80C` (C++版) が使われており、可搬パスは存在する。
- Impact: 32bit Windows ビルドの性能 (歴史的意義)。
- Risk: 削除は 32bit ビルドの挙動 (速度) を変える。**削除してはならない。**
- Proposed improvement: 現状維持。SDL2/非 Windows ビルドでは `USE_Z80_X86` が無効になる構造を維持するのみ。ドキュメント化。
- Verification: 32bit/64bit 両構成のビルドで従来通りのエンジンが選ばれること。
- Implementation status: **Proposal only** (変更しない)

## Debt 7: 未参照ファイル群 (死コード候補)

- Evidence (参照ゼロを機械的に確認):
  - `src/pc88/config2.h` — どこからも include されず、vcproj にも含まれない (新設計の設定システムの未完成品と推定。`DECLARE_CONFIG_*` マクロ前提)
  - `src/win32/critsectos2.h` — OS/2 用 CriticalSection。参照ゼロ
  - `src/win32/drawdds_.h` — 参照ゼロ (DrawDDS の旧版?)
  - `src/win32/instthnk.cpp/.h` — 相互参照のみ。vcproj 非含有。x86 機械語を実行時生成する window proc thunk
  - `src/common/lz77d.cpp/.h` — 自己参照のみ (旧スナップショット圧縮? 現行は zlib)
  - ルートの `writetag.cpp` — 単体ツール (バイナリにタグを書く)。ビルド対象外
  - vcproj 参照だが欠落: `juliet.cpp/.h`, `m88dev.html`, `memo.txt`
- Why this is debt: 理解コストと誤改変リスク。
- Impact: なし (ビルド対象外)。
- Risk: 低だが、`lz77d` は**旧形式スナップショットの読み込み互換**に関係する可能性がゼロでない (現行コードからの参照はないが、歴史的形式は不明)。
- Proposed improvement: 即削除はしない。Phase 4 で「削除候補リスト + 根拠」を提示し、承認を得たものだけ削除。`config2.h` は将来の設定システム整理の参考資料として残す選択肢も提示。
- Verification: 削除後の全構成ビルド。
- Implementation status: **Needs approval** (Phase 4 で提案、承認後削除)

## Debt 8: vcproj とディスクの不整合・大文字小文字パス

- Evidence: vcproj 内 `src\Win32\`, `src\PC88\` 表記、`Z80debug.cpp` (実体 `Z80Debug.cpp`)、欠落ファイル参照 (Debt 7)。
- Why this is debt: ビルド定義としての信頼性が低く、新 build system (CMake 等) を起こす際の正本にならない。
- Impact: build system 移行作業。
- Risk: vcproj の修正自体が Windows ビルドを壊すリスク。
- Proposed improvement: vcproj は**触らず**、Phase 7 で CMake を「追加」する際にディスク上の実ファイルを正本として定義する。
- Verification: 既存 sln/vcproj ビルドが従来通り通ること (CMake は併設)。
- Implementation status: **Proposal only** (Phase 7)

## Debt 9: `WinUI` (ui.cpp, 2041行) への責務集中

- Evidence: `src/win32/ui.cpp` — message loop、メニュー 113 分岐、D&D、fullscreen、コマンドライン、ダイアログ起動が単一クラス。
- Why this is debt: UI とアプリケーションロジック (どのディスクを挿入するか等) が不可分で、SDL2 UI を別途作る際に再利用できない。
- Impact: win32 層。
- Risk: 高 (UI 挙動の微妙な変化)。
- Proposed improvement: 全面分割はしない。SDL2 化に必要な「VM 操作 API」(ディスク挿入、リセット、speed 変更等) が `WinCore` にどの程度集約済みかを Phase 5 で棚卸しし、不足分のみ抽出を提案。
- Verification: メニュー操作の手動確認。
- Implementation status: **Proposal only**

## Debt 10: タイミング・スレッドが Win32 API 直結

- Evidence: `sequence.cpp` (`_beginthreadex`, `WaitForSingleObject`, `TerminateThread`)、`timekeep.cpp` (QPC / `timeGetTime` + `timeBeginPeriod(1)`)。
- Why this is debt: フレームペーシングとエミュレーション速度制御の中核が OS API 直結。SDL2 化の必須分離点。`TerminateThread` の使用は元々危険 (リソースリーク)。
- Impact: 速度制御・フレームスキップ・音声同期すべて。
- Risk: **高**。タイマ分解能 (`timeBeginPeriod(1)`) やスレッド優先度の違いは audio latency / テンポに直結する。
- Proposed improvement: `Sequencer`/`TimeKeeper` のインターフェースを保ったまま、実装を platform 層として分離する設計を Phase 5 で提案。`std::thread`/`std::chrono` 版は提案のみとし、Windows では既存実装を既定で維持。
- Verification: 速度・テンポ・音切れの手動比較 (同一マシン・同一設定)。
- Implementation status: **Proposal only** (Phase 5 で設計、実装は承認後)

## Debt 11: プラグイン ABI の Win32 依存

- Evidence: `src/if/ifcommon.h` (`IFCALL __stdcall`, `REFIID`, GUID)、`module.cpp` (`LoadLibrary`, `__cdecl` factory)、`cdif`/`diskdrv`/`sample*` がこの ABI の DLL。
- Why this is debt: 非 Windows では `__stdcall` が無意味/不在であり、プラグイン機構ごと移植方針の判断が要る。
- Impact: 拡張モジュール全部、ifcommon を include するコア。
- Risk: 高 (既存サードパーティ DLL との互換)。
- Proposed improvement: 非 Windows ビルドでは `IFCALL` を空定義にし GUID 型を可搬定義に差し替える案を Phase 5 で提案。**Windows での実 ABI は一切変えない。**
- Verification: Windows で既存モジュール (sample1 等) の接続確認。
- Implementation status: **Proposal only**

## Debt 12: little-endian・非アラインアクセス前提

- Evidence: `types.h` `ENDIAN_IS_SMALL` (無条件定義) / `ALLOWBOUNDARYACCESS`、`PACK()` マクロ、`screen.cpp` (packed 75箇所)、`crtc.cpp` (50箇所)、`Z80c.cpp`、`common/device.h:249`。
- Why this is debt: x86/ARM64 little-endian では実害がないが、厳密には未定義動作 (非アライン書き込み) を含み、将来のコンパイラ最適化・サニタイザで問題化しうる。
- Impact: 描画・CPU コアの高速パス。
- Risk: 修正は性能と挙動に影響。**今は触らない。**
- Proposed improvement: ドキュメント化のみ。サポート対象を little-endian に限定する旨を明記。
- Verification: n/a
- Implementation status: **Proposal only** (変更しない)

## Debt 13: snapshot 形式が構造体レイアウト依存

- Evidence: `wincore.cpp:199` `SnapshotHeader ssh;` の raw 書き出し、各デバイスの status 構造体 (pcinfo.h)。
- Why this is debt: コンパイラ・パディング・32/64bit 差でファイル互換が壊れうる。クロスプラットフォーム時に Windows で保存したスナップショットが Linux で読めない可能性。
- Impact: save/load state。
- Risk: 高。
- Proposed improvement: 形式は変更しない。Phase 9 で「現行レイアウトの固定化 (static_assert によるサイズ検証) 」を提案。
- Verification: 既存スナップショットの load 互換確認。
- Implementation status: **Proposal only**

---

# Implementation Phases

各フェーズは独立に commit し、完了報告と検証結果を出してから次に進む。

## Phase 0: Baseline and inventory

* `git status --short` を確認 (調査時点では clean)。
* build / run / test の baseline を試み、結果 (成功・失敗・環境がなく実行不能) を記録する。**MSVC が無い環境では「ビルド不能」が baseline であり、それを正直に記録する。** その場合、以降のフェーズの「ビルドが通ること」検証は「Windows 環境を持つ人間による確認待ち」として Stop And Ask に積む。
* 以下の棚卸しスクリプトを作成しリポジトリ外 (または `tools/`、承認後) に保存:
  1. 文字コード分類 (ASCII / UTF-8 / CP932 / binary / 判定不能) — manifest 出力
  2. CP932 ファイルの非 ASCII 所在分類 (コメントのみ / 文字列リテラル等)
  3. include 大文字小文字照合 (現状 31 件の再現)
  4. vcproj 参照 vs ディスク照合
* 本書 Project Understanding と一致するか確認し、差異があれば報告。
* このフェーズではコード変更しない。

## Phase 1: 機械的浄化 — 文字コード正規化 (コメントのみのファイルに限定)

目的: 挙動変更ゼロの前処理。リファクタ・rename・SDL2 はやらない。

### 1.1 棚卸し
Phase 0 のスクリプトで対象を確定し manifest 保存。対象拡張子: `.c .cpp .h .hpp .rc .txt .md .ini .def .dsp .dsw .sln .vcproj .asm`。分類: ASCII / CP932 / UTF-8 / 判定不能 / binary / generated / 除外。

### 1.2 非 ASCII の所在確認
CP932 ファイルを「コメントのみ」「文字列リテラル含む」「文字リテラル含む」「macro 含む」「.rc 表示文字列含む」「判定不能」に分類する。**本調査では以下 14 ファイルがコメント以外に非 ASCII を含むことを確認済み (再検証必須):**
`src/win32/M88.rc`, `cdif/src/cdif.rc`, `sample2/src/sample2.rc`, `src/win32/ui.cpp`, `about.cpp`, `wincfg.cpp`, `wincore.cpp`, `windraw.cpp`, `winmon.cpp`, `winsound.cpp`, `WinJoy.cpp`, `src/common/error.cpp`, `src/pc88/diskmgr.cpp`, `src/devices/Z80Test.cpp`。
これらは**このフェーズでは変換しない** (Stop And Ask)。`.dsp`/`.dsw`/`HISTORY.TXT`/`readme.txt`/`diskdrv/*.asm` もツール互換・歴史的文書として除外を推奨 (除外理由を manifest に記録)。

### 1.3 変換ルール
* CP932 と確認できたテキストのみ。UTF-8 (BOM なし) へ。
* 改行コード保存、file mode 不変、whitespace 整形・include 整理・rename・意味変更を混ぜない。
* 変換スクリプトと manifest を記録。

### 1.4 機械的検証 (必須)
* `git status --short` で意図したファイルのみ変更。
* manifest と変更ファイル一覧の一致。
* 旧ファイルを CP932、新ファイルを UTF-8 として decode した Unicode 文字列の完全一致。
* 改行・NUL・binary・generated の非変換確認。
* コメントのみのファイルについて、可能なら前処理後 token 列の同一性確認 (コメント除去後のバイト列比較で代替可)。
* ビルド通過 (環境があれば。なければ人間に依頼)。

### 1.5 build charset
MSVC 既定では UTF-8 (BOM なし) ソースはシステムコードページで解釈されうるため、コメントのみの変換であっても `/source-charset:utf-8` (MSVC) / `-finput-charset=UTF-8` (MinGW) の追加が必要になる可能性がある。**build flag 追加は build 挙動変更なので、必要が確認された場合は提案に留めて質問する。** コメント内の CP932 バイトが MSVC でエラーになることは通常ないが、UTF-8 化後の日本語コメントが警告 C4819 を出す可能性がある — 出た場合は報告。

### 1.6 commit 方針
文字コード変換のみの commit とし、message に: 変換ファイル数 / 判定基準 / 使用コマンド / 除外ファイル数と理由 / 検証結果 / 文字列リテラル・.rc の扱い、を記す。

### 1.7 Stop And Ask
判定曖昧 / 文字列リテラル・文字リテラル・macro・.rc に非 ASCII / 実行時表示が変わりうる / charset 指定不明 / MSVC・MinGW 差 / warning 増加 / 外部由来 (zlib, fmgen, c86ctl.h) / generated 判定不能 / ライセンス不明。

### 1.8 禁止事項
rename、case-only rename、include path 変更、build system 変更、SDL2、Windows API 削除、コア変更、UI 文言変更、文字列リテラル変更、.rc 意味変更、フォーマッタ、warning 修正、dead code 削除。

### 1.9 完了条件
manifest あり / 除外理由記録 / Unicode 一致確認済み / 文字列リテラル系を無検証変換していない / build が baseline 同等 (または人間確認待ちとして明記) / commit が変換のみ / 最終報告完備。

## Phase 2: include 整合とファイル名正規化

Phase 1 と別 commit。文字コード変換と混ぜない。二段階で行う。

### Phase 2a (低リスク・先行): include 文字列を実ファイル名に一致させる
* rename は一切せず、31 箇所の `#include "..."` をディスク上の実ファイル名と一致するよう修正する (例: `"Z80C.h"` → `"Z80c.h"`, `"critsect.h"` → `"CritSect.h"`, `"FDC.h"` → `"fdc.h"`)。
* これは Windows ビルドに影響せず (case-insensitive)、Linux/macOS でのコンパイル阻害を除去する純粋な前進。
* 検証: 照合スクリプトで mismatch 0 件、Windows ビルド通過。
* Implementation status: Safe to implement now。

### Phase 2b (承認後): ファイル名・ディレクトリ名の正規化
* 2.1 棚卸し: 全ファイル名を「小文字のみ / 大文字混在 / build・include・rc・vcproj から参照される名前 / 歴史的・配布物名 (`M88.rc`, `M88.ico`, `HISTORY.TXT`, `Z80*.{cpp,h}` 等)」に分類。
* 2.2 方針: 機械的全小文字化はしない。`Z80c.h` 等の実機・規格・歴史由来名は原則維持。正規化が build 可搬性に資する場合のみ、参照箇所 (include / vcproj / dsp / rc) を同時更新できる範囲で個別に提案→承認→実施。
* 2.3 case-only rename は必ず二段階 (`git mv X __tmp__ && git mv __tmp__ x`)。
* 2.4 参照更新対象: `#include`、`M88_2008.vcproj`、`M88.dsp` (歴史的だが残す)、`.rc`、ドキュメント。generated か判断できないものは質問。
* 2.5 検証: `git status --short` で rename 認識 (delete/add になっていない)、include 照合 0 件、Windows ビルド、case-insensitive FS で checkout 可能。
* 2.6 commit: rename のみの commit。message に対象一覧・理由・二段階の有無・参照更新・検証結果・除外候補。
* 2.7 禁止: 文字コード変換、SDL2、build 再設計、コア変更、dead code 削除、フォーマッタ、保存ファイル名 (M88.ini 等実行時に使われる名前) の変更。

## Phase 3: Safety net

* 自動テストが無いため、まず**手動検証チェックリスト**を `docs/verification.md` (新規) として明文化する: 起動、ROM 読み込み、D88 マウント・読み書き、T88、キー入力 (3モード)、パッド、各 draw ドライバ、各 sound ドライバ、speed/ノーウェイト、reset、BASIC モード切替、snapshot save/load、M88.ini 保存・再読み込み、モニタ群、c86ctl (ハードがあれば)。
* ROM・著作物はリポジトリに含めず手順のみ書く。
* 既存資産の活用を明記: `CPU_TEST` (Z80Test による 2 エンジン比較) のビルド・実行手順を調査しドキュメント化 (可能なら)。
* 可能なら「コンパイルのみ smoke check」スクリプトを提案 (実装は承認後)。

## Phase 4: Low-risk cleanup

* Debt 7 の未参照ファイルについて、削除候補リスト + 根拠 (参照ゼロの機械的証明、vcproj 非含有) を提示し、**承認を得たものだけ**削除する。`lz77d` は旧スナップショット互換の懸念を明記して人間に判断を委ねる。
* vcproj の欠落参照 (`juliet.cpp`, `m88dev.html`, `memo.txt`) の扱いを質問する (vcproj を直すか、放置するか)。
* 挙動変更・フォーマット変更・warning 修正は行わない。

## Phase 5: Identify and isolate platform boundaries

ここから設計フェーズ。実装は項目ごとに承認を得る。

* Win32 固有処理の分類表を作る: window/video (windraw + 4 ドライバ)、audio (winsound + 3 ドライバ + sounddrv.h の HWND)、input (WinKeyIF/WinJoy/winmouse)、timer/thread (sequence/timekeep/CritSect)、filesystem (file.cpp/main.cpp のパス処理)、config (88config の PrivateProfile)、plugin (module/extdev/winexapi)。
* 最小境界の確立を以下の優先順で提案・実施 (各々承認後):
  1. `headers.h` 依存の解消 (Debt 1): コア用中立ヘッダ新設、コアの include 差し替え。Windows ビルド維持。
  2. `types.h` の中立化 (Debt 2): `intptr_t` 化、common への移設。`USE_Z80_X86` の条件は不変。
  3. `FileIO`/`CriticalSection` の可搬実装追加 (Debt 3): インターフェース不変、Windows では既存実装を既定。
  4. `sounddrv.h` から `HWND` を外す設計案 (DirectSound が必要とするため、Windows 実装内部へ押し込む案) — 提案のみ。
  5. plugin ABI の非 Windows 時定義 (Debt 11) — 提案のみ。
* 既存 Windows backend は adapter として残す。置換しない。

## Phase 6: Small responsibility separation

* video 生成 (crtc/screen → Draw) は既に分離済みであることを確認し、`Draw` インターフェースが SDL2 実装に十分かをレビュー (Lock/Unlock モデル、パレット、Region 更新)。不足があれば拡張案を提案。
* audio 生成 (fmgen/sound) と出力 (winsound) の境界 = `SoundSource`/サウンドバッファであることを確認し、SDL2 audio callback への適合性を評価。
* input: エミュレータ側キーマトリクスと VK 依存部の境界を `WinKeyIF` 内に特定し、「キーコード変換テーブルの platform 分離」案を提案。
* timing: `TimeKeeper`/`Sequencer` の抽象化案 (Debt 10)。
* 各分離は 1 つずつ、毎回 Windows での手動検証チェックリストを通す。

## Phase 7: Build system preparation

* 既存 .sln/.vcproj/.dsp を**残したまま**、CMake を併設する案を具体化して提案する (ターゲット: まず Windows/MSVC で既存と同等のバイナリ、次に MinGW でのコンパイル到達点測定)。
* execution charset 方針 (`/execution-charset:shift_jis` 等、Debt 5 の残課題) をここで確定提案。
* 大きな build system 変更は承認なしに実装しない。

## Phase 8: SDL2 backend proposal

* 提案のみ。実装は承認後。
* 内容: `Draw` 実装としての SDL2 video (SDL_Texture streaming)、`Sound` ドライバとしての SDL2 audio (callback と既存バッファの接続)、SDL event → キーマトリクス変換、`TimeKeeper` の SDL_GetPerformanceCounter 実装、SDL2 main loop と既存 `Sequencer` スレッドモデルの関係。
* 既存 Windows backend との共存方式 (ビルド時切替を推奨するか、実行時選択か) の選択肢と推奨を列挙。
* UI (メニュー・ダイアログ・モニタ群) は SDL2 では当面非対応とする等のスコープ案を明示し、人間の判断を仰ぐ。

## Phase 9: Testability and long-term cleanup

* Z80Test 機構を活用した CPU 回帰テスト、screen 出力の CRC 比較、サウンドバッファのハッシュ比較などの回帰検証案を提案。
* snapshot レイアウトの static_assert 固定化案 (Debt 13)。
* CI (GitHub Actions: Windows MSVC build + Linux コンパイル smoke) の提案。
* 大規模削除・設計変更は提案に留める。

---

# Verification Requirements

各フェーズで必ず記録する: 実行コマンド / 成功・失敗 / 失敗ログ要約 / 守られた挙動 / 手動確認内容 / 未確認内容 / 既知リスク。

検証観点 (該当フェーズで適用):
* build が通る (MSVC。環境が無い場合は「人間による確認待ち」と明記)
* 既存 Windows build が壊れていない
* MinGW / Linux / macOS の現状 (コンパイル到達点) — Phase 5 以降
* 起動できる / M88.ini を読める / キー入力が反応する / 画面が更新される / 音が出る (または audio path が壊れていない)
* timing・speed・テンポに明らかな変化がない (FM 音源のテンポは特に注意 — 直近の修正対象)
* snapshot save/load が壊れていない (旧ファイルの load 含む)
* D88/T88/ROM の読み込みが壊れていない
* 文字コード変換後、メニュー・ダイアログ・メッセージの日本語表示が壊れていない
* rename 後、include / vcproj / rc 参照が壊れていない
* case-insensitive / case-sensitive 両 FS で checkout・ビルド可能

---

# Reporting Format

各フェーズ後に以下の形式で報告する。

````markdown
## Phase <N> Report

### Changes Made
- ...

### Files Changed
- ...

### Commands Run
```sh
...
```

### Results
- ...

### Behavior Preserved
- ...

### Risks / Unknowns
- ...

### Questions
- ...
````

最終報告には必ず含める: 何を変更したか / 何を変更しなかったか / なぜその順序か / 実行した検証 / 未実行の検証 / 既存挙動への影響可能性 / 次に人間が判断すべきこと。

---

# Out-of-scope Items

明示的な承認なしに以下は範囲外:

* エミュレーションコア (`pc88`/`devices`/`common` のロジック) の rewrite・仕様変更
* CPU / memory / I/O / interrupt timing の変更 (`Z80c.cpp`, `Z80_x86.cpp`, `fmgen` 系含む)
* Windows backend (windraw/winsound/WinKeyIF/sequence 等) の削除
* SDL2 backend への全面置換
* snapshot / M88.ini / D88 / T88 / ROM 形式の破壊的変更
* プラグイン DLL ABI の変更 (Windows 上)
* 既存 UI 操作体系 (メニュー構成、キー割り当て、コマンドライン) の変更
* 大規模なファイル移動、全体フォーマット変更、無関係な modern C++ 化
* 同梱 zlib の更新・差し替え、依存ライブラリの大幅変更
* .sln/.vcproj/.dsp の削除・全面置換
* fmgen / zlib / c86ctl.h 等外部由来コードのライセンス判断を要する改変
* 文字列リテラル・resource string の意味変更、表示文言の翻訳・修正
* 実行時エンコーディング (CP932 表示) の破壊的変更
* 保存済み config / snapshot / イメージパスに影響するファイル名変更
* `writetag.cpp`, `diskdrv/*.asm`, `HISTORY.TXT`, `readme.txt` 等の歴史的資産の削除
