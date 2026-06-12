// ---------------------------------------------------------------------------
//  M88 core ABI compatibility helpers.
//  This header provides pointer-width types needed before Win32 headers are
//  fully isolated from core sources.
// ---------------------------------------------------------------------------

#pragma once

#if !defined(_WINDEF_) && !defined(_BASETSD_H_)
	#if defined(_WIN64)
		typedef __int64 LONG_PTR;
	#else
		typedef long LONG_PTR;
	#endif
#endif
