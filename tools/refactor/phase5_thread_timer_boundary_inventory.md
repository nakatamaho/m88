# Phase 5 Thread / Timer Boundary Inventory

## Scope

- Inventory only.
- Primary targets:
  - `src/win32/sequence.h`
  - `src/win32/sequence.cpp`
  - `src/win32/timekeep.h`
  - `src/win32/timekeep.cpp`
- Report:
  - `_beginthreadex`
  - `WaitForSingleObject`
  - `TerminateThread`
  - `QueryPerformanceCounter`
  - `timeGetTime`
  - `timeBeginPeriod`
  - timing impact
  - Windows implementation preservation option
  - SDL2 / portable boundary option
  - implementation risks
- Do not implement changes.

## Baseline

- Pushed commit:
  - `e235219` `Use common CriticalSection bridge in pc88`
- Previous user-side VC2008 / VC8 Express `Release|Win32` build passed.
- Previous user-side runtime smoke passed:
  - M88 launch
  - D88 game launch
  - disk access path
  - sound
  - snapshot save/load
  - no new warning dialog or crash
- Local MSVC/VC8 build is not available in this WSL environment.

## Current Sequencer Responsibilities

`Sequencer` owns the emulator execution thread and frame pacing:

- starts a worker thread in `Init`
- stops it in `Cleanup`
- drives `PC88::Proceed`
- calls `PC88::TimeSync`
- calls `PC88::UpdateScreen`
- handles active/inactive sleep behavior
- tracks execution count
- applies clock/speed/refresh timing values

Key fields:

- `PC88* vm`
- `TimeKeeper keeper`
- `CriticalSection cs`
- `HANDLE hthread`
- `uint idthread`
- `clock`
- `speed`
- `execcount`
- `effclock`
- `time`
- `skippedframe`
- `refreshcount`
- `refreshtiming`
- `drawnextframe`
- `volatile bool shouldterminate`
- `volatile bool active`

## Thread API Usage

### `_beginthreadex`

Location:

```text
src/win32/sequence.cpp
```

Purpose:

- Starts the emulator core thread.
- Uses `ThreadEntry` trampoline to call `Sequencer::ThreadMain`.

Current behavior:

```cpp
hthread = (HANDLE)
	_beginthreadex(NULL, 0, ThreadEntry,
		reinterpret_cast<void*>(this), 0, &idthread);
```

Boundary implication:

- Thread creation is Win32/CRT-specific.
- The function signature and return handle type are Win32-specific.

### `WaitForSingleObject`

Location:

```text
src/win32/sequence.cpp
```

Purpose:

- Waits up to 3000ms for the emulator thread to exit during cleanup.

Current behavior:

```cpp
if (WAIT_TIMEOUT == WaitForSingleObject(hthread, 3000))
{
	TerminateThread(hthread, 0);
}
```

Boundary implication:

- Join behavior is Win32-specific.
- Timeout behavior is part of current shutdown behavior and should be preserved unless explicitly redesigned.

### `TerminateThread`

Location:

```text
src/win32/sequence.cpp
```

Purpose:

- Forced termination if the emulator thread does not exit within 3000ms.

Risk:

- `TerminateThread` is unsafe in general because it can bypass destructors and leave locks/resources inconsistent.
- It is existing behavior and should not be removed in an include/boundary step.
- Removing it would be a behavior change and requires separate approval.

### `Sleep`

Locations:

```text
src/win32/sequence.cpp
```

Uses:

- inactive thread sleep: `Sleep(20)`
- frame pacing sleep: `Sleep(it)`

Behavior impact:

- Sleep granularity directly affects pacing and CPU usage.
- Sleep duration uses `TimeKeeper::unit = 100`, so `it = (twork - tdraw) / 100` maps 0.01ms units to milliseconds.

## Timer API Usage

### `QueryPerformanceFrequency` / `QueryPerformanceCounter`

Location:

```text
src/win32/timekeep.cpp
```

Purpose:

- Preferred high-resolution time source.

Current behavior:

```cpp
if (QueryPerformanceFrequency(&li))
{
	freq = (li.LowPart+unit*500) / (unit*1000);
	QueryPerformanceCounter(&li);
	base = li.LowPart;
}
```

`GetTime()` then accumulates elapsed ticks:

```cpp
QueryPerformanceCounter(&li);
uint32 dc = li.LowPart - base;
time += dc / freq;
base = li.LowPart - dc % freq;
return time;
```

Important notes:

- Only `LARGE_INTEGER::LowPart` is used.
- Returned unit is `1 / TimeKeeper::unit` milliseconds.
- `unit` is `100`, so the returned value is in 0.01ms units.
- The code increments a monotonic-ish accumulated `time` value rather than returning raw QPC each call.

Risk:

- Changing this math can alter emulation speed and audio tempo.
- 64-bit QPC handling may be improved later, but doing so would be behavior-sensitive.

### `timeGetTime`

Location:

```text
src/win32/timekeep.cpp`
```

Purpose:

- Fallback time source when QPC is unavailable.

Current behavior:

```cpp
base = timeGetTime();
...
time = timeGetTime();
return time * unit;
```

Risk:

- Fallback precision depends on multimedia timer resolution.
- Even if modern systems almost always have QPC, preserving fallback behavior is safest for VC2008-era compatibility.

### `timeBeginPeriod(1)` / `timeEndPeriod(1)`

Location:

```text
src/win32/timekeep.cpp
```

Purpose:

- Improve timer precision when falling back to `timeGetTime`.

Current behavior:

- Constructor calls `timeBeginPeriod(1)` only if QPC is unavailable.
- Destructor calls `timeEndPeriod(1)` only when that fallback path was used.

Risk:

- Timer resolution affects `Sleep`, audio latency, frame pacing, and CPU usage.
- Do not remove or broaden/narrow this behavior without dedicated timing verification.

## Emulation Timing Flow

`WinCore::ApplyConfig` drives `Sequencer`:

```cpp
int c = cfg->clock;
if (cfg->flags & PC8801::Config::fullspeed)
	c = 0;
if (cfg->flags & PC8801::Config::cpuburst)
	c = -c;
seq.SetClock(c);
seq.SetSpeed(cfg->speed / 10);
seq.SetRefreshTiming(cfg->refreshtiming);
```

Meaning:

- `clock > 0`: normal frame-period pacing.
- `clock == 0`: full-speed / no-wait path.
- `clock < 0`: CPU burst style path.
- `speed` influences target work time.
- `refreshtiming` controls frame update cadence.

`Sequencer::ExecuteAsynchronus` has two major modes:

### Full-speed / burst mode

Triggered when:

```cpp
clock <= 0
```

Behavior:

- reset timing base with `keeper.GetTime()`
- call `vm->TimeSync()`
- repeatedly call `Execute(...)` until about 1000 units have elapsed
- update screen once
- adjust `effclock`

Timing sensitivity:

- `effclock` feedback depends on elapsed time measurement.
- Changes can affect no-wait speed, burst behavior, and perceived emulator tempo.

### Normal frame pacing mode

Triggered when:

```cpp
clock > 0
```

Behavior:

- `texec = vm->GetFramePeriod()`
- `twork = texec * 100 / speed`
- `vm->TimeSync()`
- `Execute(clock, texec, clock * speed / 100)`
- compare elapsed CPU time to target work time
- update screen based on `drawnextframe`, `refreshcount`, and `refreshtiming`
- sleep if there is spare time
- skip frames if work overruns

Timing sensitivity:

- Frame pacing, frame skip, audio tempo, and FDD wait behavior can change if time measurement or sleeping changes.

## Related Configuration

`PC8801::Config` has timing-related flags:

- `fullspeed`
- `cpuburst`
- `enablewait`
- `useqpc`
- `fddnowait`
- `speed`
- `refreshtiming`

Observation:

- `Config::useqpc` exists, but `TimeKeeper` currently always tries QPC first and does not appear to consult this flag directly.
- This should be treated as historical behavior; wiring the flag into `TimeKeeper` would be a behavior change.

## Other Thread/Timer Users Nearby

This inventory focuses on `sequence.*` and `timekeep.*`, but related Win32 thread/timer usage exists:

- `src/win32/soundwo.cpp`
  - `_beginthreadex`
  - `WaitForSingleObject`
  - `TerminateThread`
  - `Sleep`
- `src/win32/soundds2.cpp`
  - `_beginthreadex`
  - `WaitForSingleObject`
  - `TerminateThread`
  - event wait
- `src/win32/windraw.cpp`
  - `_beginthreadex`
  - `WaitForSingleObject`
  - `TerminateThread`
- `src/win32/romeo/piccolo.cpp`
  - `_beginthreadex`
  - `WaitForSingleObject`
  - `TerminateThread`
  - `timeGetTime`
- `src/win32/soundds.cpp`
  - `timeBeginPeriod`
  - `timeEndPeriod`
  - `Sleep`

These should remain separate inventories because they are tied to sound/video/G.I.M.I.C backends rather than the core emulator sequencer.

## Windows Implementation Preservation Option

Recommended default:

- Keep `Sequencer` and `TimeKeeper` behavior unchanged for Windows.
- Keep `_beginthreadex`, `WaitForSingleObject`, `TerminateThread`, `Sleep`, QPC, and `timeGetTime` behavior in the Windows backend.
- Do not change:
  - `ThreadMain` loop
  - `ExecuteAsynchronus` math
  - `TimeKeeper::GetTime` units
  - timeout values
  - forced thread termination fallback
  - frame skip thresholds

Minimal safe boundary work:

- Introduce a design-only platform interface first.
- Avoid moving code until a Windows-backed implementation can be proven byte-for-byte or behavior-equivalent in build/runtime smoke.

## SDL2 / Portable Boundary Option

Possible future split:

### Time source boundary

Keep current public behavior:

```cpp
uint32 GetTime();
```

with the same unit:

```cpp
TimeKeeper::unit == 100
```

Possible platform implementations:

- Windows:
  - existing QPC / `timeGetTime` implementation
- SDL2:
  - `SDL_GetPerformanceCounter`
  - `SDL_GetPerformanceFrequency`
  - possibly `SDL_GetTicks` fallback
- POSIX/C++:
  - `clock_gettime` or `std::chrono`, but not for VC2008

### Thread boundary

Keep the `Sequencer` public API initially:

- `Init`
- `Cleanup`
- `Activate`
- `Lock` / `Unlock`
- `SetClock`
- `SetSpeed`
- `SetRefreshTiming`
- `GetExecCount`

Move thread creation/join/sleep behind a platform helper later.

Possible backend calls:

- Windows:
  - `_beginthreadex`
  - `WaitForSingleObject`
  - `CloseHandle`
  - `Sleep`
- SDL2:
  - `SDL_CreateThread`
  - `SDL_WaitThread`
  - `SDL_Delay`
- C++11:
  - `std::thread`
  - `std::chrono`
  - not VC2008-compatible

## Implementation Risks

### Timing / Speed

- `Sequencer::ExecuteAsynchronus` directly controls emulation speed.
- `effclock` feedback depends on `TimeKeeper` resolution and arithmetic.
- Changing the time source can alter full-speed/no-wait behavior.
- Changing sleep granularity can alter CPU usage and frame pacing.

### Audio

- Audio tempo and latency depend on stable emulator timing.
- Existing FM/SSG/ADPCM timing fixes should not be disturbed.
- Runtime verification must include sound, not just build.

### Disk / FDD Wait

- FDC/disk behavior uses scheduler timing.
- Timing changes can affect disk access speed and wait/no-wait behavior.
- D88 runtime verification is required after any implementation change.

### Shutdown

- Removing `TerminateThread` is attractive but risky.
- Current cleanup forcibly kills the thread if it does not exit within 3000ms.
- A graceful-only join may hang on shutdown if the old behavior relied on forced termination.

### VC2008

- `std::thread` and `std::chrono` are not available.
- SDL2 or platform-specific wrappers would need careful project-file and dependency handling.
- Do not introduce new dependencies in a boundary inventory step.

## Recommended Next Step

Do not implement the thread/timer abstraction yet.

Recommended next step:

```text
Phase 5 TimeKeeper boundary step 1 の設計だけ実行しろ。
TimeKeeper の public API と unit=100 を維持する前提で、
Windows 実装をそのまま残す案、SDL2 実装案、
QPC LowPart 使用を維持/改善する判断点、
VC2008/MinGW 影響、検証方法を report しろ。
実装はするな。
```

Reason:

- Time source is smaller than full `Sequencer` threading.
- A clean time boundary is prerequisite for any portable `Sequencer`.
- Implementation risk is high enough that one more design step is justified.

## User-Side Verification For Future Implementation

For any future thread/timer implementation:

- `tools\windows\build_vc2008.cmd Release`
- Confirm `writetag` CRC appears.
- Launch M88.
- Boot a D88 game.
- Reach disk-access activity.
- Confirm sound output and tempo feel normal.
- Confirm speed/no-wait related settings if practical.
- Confirm snapshot save/load.
- Confirm clean shutdown.
- Confirm no new warning dialog or crash.
