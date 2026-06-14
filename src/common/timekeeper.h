// ---------------------------------------------------------------------------
//  M88 TimeKeeper API.
// ---------------------------------------------------------------------------

#pragma once

#include "types.h"

// ---------------------------------------------------------------------------
// TimeKeeper
// Provides elapsed time in 1/unit millisecond ticks.
// ---------------------------------------------------------------------------
class TimeKeeper
{
public:
	enum
	{
		unit = 100,
	};

public:
	TimeKeeper();
	~TimeKeeper();

	uint32 GetTime();

private:
	uint32 freq;
	uint32 base;
	uint32 time;
};

