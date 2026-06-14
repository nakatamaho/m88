# Phase 5 WinCore/WinUI Operation Boundary Step 23 Inventory

## Scope

- Inventory `WinUI`-only remaining `core.*` call sites after Step22 routing.
- Keep this as inventory-only (no implementation change).
- Track what must remain in `core` for lifecycle, monitor and mutating paths for later phases.

## Search Method

```text
rg -n "\bcore\." src/win32/ui.cpp
rg -n "vmops" src/win32/ui.cpp
```

## Remaining Direct `core.*` Dependency Classification

### 1) Lifecycle / VM control

- `core.Init(...)`
- `core.Wait(false)`
- `core.Reset()`
- `core.Cleanup()`

### 2) Monitor / subsystem wiring

- `opnmon.Init(core.GetOPN1(), core.GetSound())`
- `core.GetSound()->SetSoundMonitor(&opnmon)`
- `OPNIF* opn = core.GetOPN1()`

### 3) Sound mutating

- `core.GetSound()->IsDumping()`
- `core.GetSound()->DumpBegin(buf)`
- `core.GetSound()->DumpEnd()`
- `core.SetVolume((PC8801::Config*) c)`

### 4) Configuration / snapshot control (fallback wrappers)

- `core.ApplyConfig(&config)`
- `core.Reset()`
- Snapshot writes/reads:
  - `core.SaveShapshot(name)`
  - `core.LoadShapshot(name, diskinfo[0].filename)`
  - `core.LoadShapshot(name, 0)` (both routed to vmops with fallback in Step22)

### 5) Read-only status in menu path

- No direct-only `core.*` calls remain in `WinUI::WmInitMenu` after Step24 boundary migration.
- Read-only menu state is now exposed through `vmops` wrappers.

## Next Step Candidate

- Remove legacy fallback conditions from menu-facing `core`-adjacent calls in a controlled way while keeping lifecycle/snapshot/memory/sound mutating paths for later steps.
