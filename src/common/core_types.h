// ----------------------------------------------------------------------------
//  M88 core basic types and cast helpers.
// ----------------------------------------------------------------------------

#pragma once

typedef unsigned char uchar;
typedef unsigned short ushort;
typedef unsigned int uint;
typedef unsigned long ulong;

typedef unsigned char uint8;
typedef unsigned short uint16;
typedef unsigned int uint32;

typedef signed char sint8;
typedef signed short sint16;
typedef signed int sint32;

typedef signed char int8;
typedef signed short int16;
typedef signed int int32;

typedef uint32 packed;
#define PACK(p) ((p) | ((p) << 8) | ((p) << 16) | ((p) << 24))

#define USE_NEW_CAST

#if defined(USE_NEW_CAST) && defined(__cplusplus)
	#define STATIC_CAST(t, o)			static_cast<t> (o)
	#define REINTERPRET_CAST(t, o)		reinterpret_cast<t> (o)
#else
	#define STATIC_CAST(t, o)			((t)(o))
	#define REINTERPRET_CAST(t, o)		(*(t*)(void*)&(o))
#endif
