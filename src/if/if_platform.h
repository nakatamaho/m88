// ----------------------------------------------------------------------------
//  M88 plugin ABI platform declarations.
// ----------------------------------------------------------------------------

#pragma once

#if defined(_WIN32)

#ifndef STRICT
#define STRICT
#endif

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif

#ifndef WINVER
#define WINVER 0x500
#endif

#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x500
#endif

#include <windows.h>
#include <commctrl.h>

#ifndef interface
#define interface struct
#endif

#endif
