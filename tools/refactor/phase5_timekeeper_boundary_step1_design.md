# Phase 5 TimeKeeper Boundary Step 1 Design

## Scope

- Design only.
- Target:
  - `src/win32/timekeep.h`
  - `src/win32/timekeep.cpp`
- Preserve:
  - `TimeKeeper` public API
  - `TimeKeeper::unit == 100`
  - `uint32 GetTime()`
  - existing Windows behavior unless a later implementation step explicitly changes it
- Report:
  - Windows implementation preservation plan
  - SDL2 implementation option
  - QPC `LowPart` keep/improve decision point
  - VC2008 / MinGW impact
  - verification method
- Do not implement changes.

## Current Public API

```cpp
class TimeKeeper
{
public:
	enum
	{
		unit = 100,
	};

	TimeKeeper();
	~TimeKeeper();

	uint32 GetTime();

private:
	uint32 freq;
	uint32 base;
	uint32 time;
};
```

Meaning:

- `GetTime()` returns elapsed time in `1 / unit` milliseconds.
- With `unit = 100`, the public time unit is `0.01ms`.
- The caller generally uses deltas, not absolute wall-clock meaning.

Primary caller:

- `src/win32/sequence.cpp`
  - frame pacing
  - full-speed/no-wait loop
  - sleep decision
  - `effclock` feedback

Secondary users:

- `src/win32/romeo/piccolo.h` has a `TimeKeeper` member.
- Other Win32 code uses raw `timeGetTime` / QPC separately and is outside this step.

## Current Windows Implementation

Constructor:

- asserts `unit > 0`
- calls `QueryPerformanceFrequency`
- if QPC exists:
  - computes `freq = (li.LowPart + unit * 500) / (unit * 1000)`
  - stores initial `base = QueryPerformanceCounter().LowPart`
- otherwise:
  - stores `freq = 0`
  - calls `timeBeginPeriod(1)`
  - stores `base = timeGetTime()`
- initializes `time = 0`

Destructor:

- calls `timeEndPeriod(1)` only if fallback path was used.

`GetTime()`:

- QPC path:
  - reads current `QueryPerformanceCounter().LowPart`
  - computes `dc = current_lowpart - base`
  - increments accumulated `time` by `dc / freq`
  - advances `base` by the consumed remainder
- fallback path:
  - reads `timeGetTime()`
  - returns `time * unit`

## Windows Preserve Plan

Recommended first implementation plan:

- Do not change the existing Windows `TimeKeeper` arithmetic.
- Keep QPC-first behavior.
- Keep `timeGetTime` fallback.
- Keep `timeBeginPeriod(1)` and `timeEndPeriod(1)` limited to the fallback path.
- Keep `freq`, `base`, and `time` member types as `uint32` for the first boundary implementation.

Rationale:

- Existing behavior is proven by VC2008 Release runtime smoke.
- `Sequencer` timing math depends on the exact unit and delta behavior.
- Any arithmetic "fix" is behavior-sensitive even if technically cleaner.

Possible include/file organization later:

- Keep public header name and API:
  - `timekeep.h`
- Move Windows implementation behind a platform-specific implementation file only after a project-file design step.
- Or add a minimal `core_timekeeper` bridge later, but do not rename the class while `Sequencer` still uses it directly.

## SDL2 Implementation Option

SDL2 can provide a compatible time source with:

- `SDL_GetPerformanceCounter`
- `SDL_GetPerformanceFrequency`
- fallback: `SDL_GetTicks`

Design target:

```cpp
uint32 TimeKeeper::GetTime();
```

must still return `0.01ms` units.

SDL2 QPC-like path:

- store SDL frequency in a counter-per-0.01ms scale
- store current SDL counter as base
- compute elapsed counter delta
- accumulate returned `time` in `uint32` 0.01ms units

Important:

- Keep accumulated-time behavior rather than returning raw converted absolute time if exact Windows pacing is desired.
- Keep conversion rounding semantics deliberately chosen and documented.
- Avoid introducing SDL headers into existing Win32 build files.

SDL fallback path:

- `SDL_GetTicks()` returns milliseconds.
- equivalent fallback return would be:

```cpp
return ticks * TimeKeeper::unit;
```

There is no SDL equivalent of `timeBeginPeriod(1)` that should be applied to Windows fallback behavior. The SDL backend should document that sleep/timer resolution is SDL/platform dependent.

## QPC `LowPart` Decision

### Option A: Preserve `LowPart`

Recommended for first implementation.

Pros:

- Minimal behavior change.
- Matches current VC2008-proven behavior.
- Avoids timing drift/regression being mixed into a boundary refactor.

Cons:

- Ignores high 32 bits of the QPC counter and frequency.
- Can behave poorly if the low 32 bits wrap in a problematic interval.
- Modern correctness is weaker.

### Option B: Improve To 64-bit QPC

Do not combine with the first boundary implementation.

Pros:

- More correct for modern systems.
- Avoids low-32-bit wrap assumptions.
- Easier to map to SDL's 64-bit performance counter.

Cons:

- Changes arithmetic behavior.
- May change `freq` rounding.
- Can affect emulator speed, audio tempo, no-wait behavior, and frame pacing.
- Requires dedicated runtime timing comparison before/after.

Decision:

- Preserve `LowPart` in any first boundary extraction.
- Treat 64-bit QPC as a separate behavior-change proposal.

## VC2008 Impact

Constraints:

- VC2008 has no `std::chrono`.
- VC2008 has no `std::thread`.
- Existing Windows APIs are available through `headers.h`.
- `timekeep.cpp` currently uses Win32/PCH context.

Safe path:

- Keep Windows implementation unchanged for VC2008.
- Do not add SDL2 or C++11 dependencies to the VC2008 project.
- If a new header/source is added later, update `M88_2008.vcproj` and `M88.dsp` in the same small step.

Risk:

- Changing `timekeep.h` private fields can affect object layout of `Sequencer`, but that is internal to one build.
- Still, object layout change is unnecessary for the first boundary step.

## MinGW Impact

Current compile context:

- MinGW can compile the existing Windows APIs when include paths and charset are set.
- Any SDL2 implementation would need dependency discovery and build-system support not present in this repository.

Safe path:

- Keep Windows implementation compiling under MinGW as a Windows target.
- Design SDL2 implementation as a future backend, not as an immediate source dependency.
- Avoid introducing `#ifdef SDL` paths into `timekeep.*` before the build system can select them clearly.

## Proposed Minimal Boundary Shape

Do not implement yet. Candidate future shape:

```text
src/win32/timekeep.h        public TimeKeeper API, unchanged
src/win32/timekeep.cpp      current Windows implementation, unchanged initially
```

After that is documented and stable, a later platform split could be:

```text
src/common/timekeeper.h     public API, if/when moving out of win32 is approved
src/win32/timekeep_win32.cpp
src/sdl/timekeep_sdl.cpp
```

But this should wait because moving the header out of `src/win32` affects includes, project files, and `romeo/piccolo` users.

## Implementation Plan For A Future Small Step

Recommended next implementation should still be conservative:

1. Add a report-backed compile smoke around current `timekeep.cpp`.
2. Do not change arithmetic.
3. If adding a bridge header, make it include the existing `timekeep.h` only.
4. Keep `Sequencer` unchanged.

Avoid in the first implementation:

- 64-bit QPC conversion.
- `std::chrono`.
- SDL2 includes.
- changing fallback behavior.
- changing `Config::useqpc` behavior.
- changing `timeBeginPeriod(1)` scope.

## Verification Method

Local compile smoke:

```sh
i686-w64-mingw32-g++ -std=gnu++98 -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/timekeep.cpp
x86_64-w64-mingw32-g++ -std=gnu++98 -fpermissive -fsyntax-only -finput-charset=CP932 -Isrc -Isrc/win32 -Isrc/common -Isrc/pc88 -Isrc/devices -Isrc/if src/win32/timekeep.cpp
```

User-side VC2008 verification for any later implementation:

- `tools\windows\build_vc2008.cmd Release`
- Confirm post-build `writetag` CRC appears.
- Launch M88.
- Boot a D88 game.
- Confirm disk access works.
- Confirm sound output and tempo feel normal.
- Confirm speed/no-wait behavior if practical.
- Confirm frame pacing looks normal.
- Confirm snapshot save/load.
- Confirm clean shutdown.
- Confirm no new warning dialog or crash.

## Recommendation

Do not implement SDL2 timing yet.

Recommended next step:

```text
Phase 5 TimeKeeper boundary step 2 の棚卸しだけ実行しろ。
TimeKeeper を win32 から common/platform 境界へ移す場合の include path、
project file、romeo/piccolo 依存、Sequencer 依存、VC2008 PCH 影響を report しろ。
実装はするな。
```

Reason:

- The public API is small, but file placement affects `src/win32`, `src/win32/romeo`, and future SDL2 layout.
- One more placement-focused design step reduces risk before any file move or wrapper introduction.
