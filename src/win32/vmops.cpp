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
: core(0), diskmgr(0), tapemgr(0)
{
}

VMOperations::~VMOperations()
{
}

void VMOperations::Bind(WinCore* c, DiskManager* disk, TapeManager* tape)
{
	core = c;
	diskmgr = disk;
	tapemgr = tape;
}

void VMOperations::Unbind()
{
	core = 0;
	diskmgr = 0;
	tapemgr = 0;
}

bool VMOperations::Init
(WinUI*, HWND, Draw*, DiskManager* disk,
 PC8801::WinKeyIF*, IConfigPropBase*, TapeManager* tape)
{
	Bind(0, disk, tape);
	return false;
}

bool VMOperations::Cleanup()
{
	Unbind();
	return true;
}

void VMOperations::Start()
{
	if (core)
		core->Wait(false);
}

void VMOperations::Stop()
{
	if (core)
		core->Wait(true);
}

void VMOperations::Reset()
{
	if (core)
		core->Reset();
}

void VMOperations::ApplyConfig(PC8801::Config* config)
{
	if (core)
		core->ApplyConfig(config);
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
	return core ? core->SaveShapshot(path) : false;
}

bool VMOperations::LoadSnapshot(const char* path, const char* diskPath)
{
	return core ? core->LoadShapshot(path, diskPath) : false;
}

PC8801::WinSound* VMOperations::GetSound()
{
	return core ? core->GetSound() : 0;
}

long VMOperations::GetExecCount()
{
	return core ? core->GetExecCount() : 0;
}

bool VMOperations::IsN80Supported()
{
	return core ? core->IsN80Supported() : false;
}

bool VMOperations::IsN80V2Supported()
{
	return core ? core->IsN80V2Supported() : false;
}

void VMOperations::Lock()
{
	if (core)
		core->Lock();
}

void VMOperations::Unlock()
{
	if (core)
		core->Unlock();
}

void* VMOperations::QueryIF(REFIID iid)
{
	return core ? core->QueryIF(iid) : 0;
}
