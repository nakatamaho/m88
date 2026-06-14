// ---------------------------------------------------------------------------
//	M88 - PC-8801 Emulator
//	Copyright (C) cisc 1998, 1999.
// ---------------------------------------------------------------------------
//	file finder class
// ---------------------------------------------------------------------------

#pragma once

// ---------------------------------------------------------------------------

class FileFinder
{
public:
	FileFinder() : hff(INVALID_HANDLE_VALUE), searcher(0) {}

	~FileFinder()
	{
		free(searcher);
		if (hff != INVALID_HANDLE_VALUE)
			FindClose(hff);
	}

	bool FindFile(char* szSearch)
	{
		hff = INVALID_HANDLE_VALUE;
		free(searcher);
		searcher = _strdup(szSearch);
		return searcher != 0;
	}

	bool FindNext()
	{
		if (!searcher)
			return false;
		if (hff == INVALID_HANDLE_VALUE)
		{
			hff = FindFirstFile(searcher, &wfd);
			return hff != INVALID_HANDLE_VALUE;
		}
		else
			return FindNextFile(hff, &wfd) != 0;
	}

	const char* GetFileName()	{ return wfd.cFileName; }
	DWORD GetFileAttr()			{ return wfd.dwFileAttributes; }
	const char* GetAltName()	{ return wfd.cAlternateFileName; }

private:
	char* searcher;
	HANDLE hff;
	WIN32_FIND_DATA wfd;
};
