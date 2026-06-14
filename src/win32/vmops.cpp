// ---------------------------------------------------------------------------
//  M88 - PC-8801 emulator
// ---------------------------------------------------------------------------
//  VM operation facade for Win32
// ---------------------------------------------------------------------------

#include "headers.h"
#include "vmops.h"
#include "pc88/diskmgr.h"
#include "pc88/tapemgr.h"

// ---------------------------------------------------------------------------

VMOperations::VMOperations()
: diskmgr(0), tapemgr(0)
{
}

VMOperations::~VMOperations()
{
}

bool VMOperations::Init
(WinUI* ui, HWND hwnd, Draw* draw, DiskManager* disk,
 PC8801::WinKeyIF* keyb, IConfigPropBase* cpb, TapeManager* tape)
{
	diskmgr = disk;
	tapemgr = tape;
	return core.Init(ui, hwnd, draw, disk, keyb, cpb, tape);
}

bool VMOperations::Cleanup()
{
	return core.Cleanup();
}

void VMOperations::Start()
{
	core.Wait(false);
}

void VMOperations::Stop()
{
	core.Wait(true);
}

void VMOperations::Reset()
{
	core.Reset();
}

void VMOperations::ApplyConfig(PC8801::Config* config)
{
	core.ApplyConfig(config);
}

bool VMOperations::MountDisk
(uint drive, const char* path, bool readonly, int index, bool create)
{
	return diskmgr ? diskmgr->Mount(drive, path, readonly, index, create) : false;
}

bool VMOperations::UnmountDisk(uint drive)
{
	return diskmgr ? diskmgr->Unmount(drive) : false;
}

uint VMOperations::GetNumDisks(uint drive)
{
	return diskmgr ? diskmgr->GetNumDisks(drive) : 0;
}

int VMOperations::GetCurrentDisk(uint drive)
{
	return diskmgr ? diskmgr->GetCurrentDisk(drive) : -1;
}

const char* VMOperations::GetDiskTitle(uint drive, uint index)
{
	return diskmgr ? diskmgr->GetImageTitle(drive, index) : 0;
}

bool VMOperations::IsDiskImageOpen(const char* path)
{
	return diskmgr ? diskmgr->IsImageOpen(path) : false;
}

bool VMOperations::AddDisk(uint drive, const char* title, uint type)
{
	return diskmgr ? diskmgr->AddDisk(drive, title, type) : false;
}

bool VMOperations::FormatDisk(uint drive)
{
	return diskmgr ? diskmgr->FormatDisk(drive) : false;
}

bool VMOperations::OpenTape(const char* path)
{
	return tapemgr ? tapemgr->Open(path) : false;
}

bool VMOperations::CloseTape()
{
	return tapemgr ? tapemgr->Close() : false;
}

bool VMOperations::IsTapeOpen()
{
	return tapemgr ? tapemgr->IsOpen() : false;
}

bool VMOperations::SaveSnapshot(const char* path)
{
	return core.SaveShapshot(path);
}

bool VMOperations::LoadSnapshot(const char* path, const char* diskPath)
{
	return core.LoadShapshot(path, diskPath);
}

PC8801::WinSound* VMOperations::GetSound()
{
	return core.GetSound();
}

long VMOperations::GetExecCount()
{
	return core.GetExecCount();
}

void VMOperations::Lock()
{
	core.Lock();
}

void VMOperations::Unlock()
{
	core.Unlock();
}

void* VMOperations::QueryIF(REFIID iid)
{
	return core.QueryIF(iid);
}
