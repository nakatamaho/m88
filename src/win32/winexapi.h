// ---------------------------------------------------------------------------
//	$Id

#pragma once

class ExtendedAPIAccessBase
{
public:
	ExtendedAPIAccessBase(const char* dllname, const char* apiname, void* dummy);
	bool IsValid() { return valid; }

protected:
	void* Method() { return method; }

private:
	void* method;
	bool valid;
};
	
class ExternalDLLAccessBase
{
public:
	ExternalDLLAccessBase(const char* _dllname, const char* _apiname, void* _dummy)
		: method(0), dllname(_dllname), apiname(_apiname), dummy(_dummy)
	{
	}

	~ExternalDLLAccessBase();

	bool IsValid() 
	{ 
		Method();
		return !!hmod; 
	}

protected:
	void* Method() 
	{ 
		if (!method)
			Load(); 
		return method; 
	}

private:
	void Load();
	void* method;
	const char* dllname;
	const char* apiname;
	union
	{
		void* dummy;
		HMODULE hmod;
	};
};

template<class T, class Base>
class ExtendedAPIAccess : public Base
{
public:
	ExtendedAPIAccess(const char* dllname, const char* apiname, T dummy)
		: Base(dllname, apiname, (void*) dummy)
	{
	}

	operator T() { return T(Method()); }
};


#ifndef DECLARE_EXAPI
	#define DECLARE_EXAPI(name, type, arg, dll, api, def) \
		extern ExtendedAPIAccess <type (WINAPI*) arg, ExtendedAPIAccessBase> name;
#endif

#ifndef DECLARE_EXDLL
	#define DECLARE_EXDLL(name, type, arg, dll, api, def) \
		extern ExtendedAPIAccess <type (WINAPI*) arg, ExternalDLLAccessBase> name;
#endif

// ---------------------------------------------------------------------------
//	標準では提供されないかもしれない API を列挙
//	EXAPI - GetModuleHandle で接続
//	EXDLL - 起動時 に LoadLibrary で接続
//
DECLARE_EXAPI(EnableIME, BOOL, (HWND, BOOL), "user32.dll", "WINNLSEnableIME", FALSE)
DECLARE_EXAPI(MonitorFromWin, HMONITOR, (HWND, DWORD), "user32.dll", "MonitorFromWindow", 0)
DECLARE_EXDLL(DDEnumerateEx, HRESULT, (LPDDENUMCALLBACKEX, LPVOID, DWORD), "ddraw.dll", "DirectDrawEnumerateExA", S_OK)

