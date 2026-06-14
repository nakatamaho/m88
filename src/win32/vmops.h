// ---------------------------------------------------------------------------
//  M88 - PC-8801 emulator
// ---------------------------------------------------------------------------
//  VM operation facade for Win32
// ---------------------------------------------------------------------------

#pragma once

#include "wincore.h"

// ---------------------------------------------------------------------------

class VMOperations
{
public:
	VMOperations();
	~VMOperations();

	void Bind(WinCore* core, DiskManager* diskmgr, TapeManager* tapemgr);
	void Unbind();
	bool IsBound() const { return core != 0; }

	bool Init(WinUI* ui, HWND hwnd, Draw* draw, DiskManager* diskmgr,
			  PC8801::WinKeyIF* keyb, IConfigPropBase* cpb,
			  TapeManager* tapemgr);
	bool Cleanup();

	void Start();
	void Stop();
	void Reset();
	void ApplyConfig(PC8801::Config* config);

	bool MountDisk(uint drive, const char* path, bool readonly, int index, bool create);
	bool UnmountDisk(uint drive);
	uint GetNumDisks(uint drive);
	int GetCurrentDisk(uint drive);
	const char* GetDiskTitle(uint drive, uint index);
	bool IsDiskImageOpen(const char* path);
	bool AddDisk(uint drive, const char* title, uint type);
	bool FormatDisk(uint drive);

	bool OpenTape(const char* path);
	bool CloseTape();
	bool IsTapeOpen();

	bool SaveSnapshot(const char* path);
	bool LoadSnapshot(const char* path, const char* diskPath);

	PC8801::WinSound* GetSound();
	long GetExecCount();
	bool IsN80Supported();
	bool IsN80V2Supported();
	void Lock();
	void Unlock();
	void* QueryIF(REFIID iid);

private:
	VMOperations(const VMOperations&);
	VMOperations& operator=(const VMOperations&);

	WinCore* core;
	DiskManager* diskmgr;
	TapeManager* tapemgr;
};
