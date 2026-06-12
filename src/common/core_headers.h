// ---------------------------------------------------------------------------
//  M88 core includes.
//  This header is for common/devices/pc88 sources that do not need Win32 APIs.
// ---------------------------------------------------------------------------

#pragma once

#include <assert.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include <algorithm>
#include <map>
#include <string>
#include <utility>
#include <vector>

#if !defined(_WINDEF_) && !defined(_BASETSD_H_)
	#if defined(_WIN64)
		typedef __int64 LONG_PTR;
	#else
		typedef long LONG_PTR;
	#endif
#endif

#include "types.h"

using namespace std;

#ifdef _MSC_VER
	#undef max
	#define max _MAX
	#undef min
	#define min _MIN
#endif
