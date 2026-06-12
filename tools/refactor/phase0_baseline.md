# Phase 0 Baseline

Recorded for `refactor-instructions.md` Phase 0.

## Linux / WSL Baseline

- Environment: WSL/Linux workspace at `/home/maho/m88`
- `devenv`: not available
- `msbuild`: not available
- `make -n`: failed because no Makefile exists
- `cmake -S . -B /tmp/m88-phase0-cmake-check`: failed because no `CMakeLists.txt` exists
- `M88.exe`: not present in the repository
- Automated tests / CI: not present; existing assets found were `src/devices/Z80Test.*` and `src/win32/filetest.*`

## Windows Baseline

- Environment: Windows with Visual C++ 2008 Express Edition
- Solution: `M88_2008.sln`
- Configuration: not specified
- Build: success, user-reported
- Run: simple smoke check success, user-reported
- Detailed checks: not specified
- Date recorded: 2026-06-12

## Notes

- No source code, project file, resource, encoding, include, or rename changes are part of this baseline record.
- Detailed ROM, D88/T88, input, video, audio, snapshot, and monitor verification remains unrecorded unless separately supplied.
