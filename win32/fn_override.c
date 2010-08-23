#include <stdio.h>
#include <stdlib.h>

#ifndef _WIN32
#include <sys/mman.h>
#include <dlfcn.h>
#else
#include <windows.h>
#endif

#include <sys/types.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>

#include "fn_override.h"

int yb_fn_override_by_name(const char *orig, const char *target, const char *libname)
{
#ifdef _WIN32
	HMODULE handle = LoadLibrary(libname);
	if(!handle) {
		printf("LoadLibrary() failed\n");
		return 0;
	}
	FARPROC origptr = GetProcAddress(handle, orig);
	FARPROC targetptr = GetProcAddress(handle, target);
#else
	void *handle = dlopen(libname, RTLD_LAZY);
	if(!handle) {
		printf("%s\n", dlerror());
		return 0;
	}
	void *origptr = dlsym(handle, orig);
	void *targetptr = dlsym(handle, target);
#endif
	if(!(origptr && targetptr)) {
		printf("couldn't load symbols\n");
		return 0;
	}
	return yb_fn_override_by_ptr(origptr, targetptr);
}

int yb_fn_override_by_ptr(void *orig, const void *target) {
#ifdef _LP64
#define JMP_SIZE 12
#define PTR_TYPE uint64_t
#define DST_TYPE PTR_TYPE	
#define DST_ARG (PTR_TYPE)target
	char op[JMP_SIZE];
	/*two-byte movq*/
	op[0] = 0x48;
	op[1] = 0xb8;
	/*two byte jmpq*/
	op[10] = 0xff;
	op[11] = 0xe0;
	void *addrptr = op+2;
#else
#define JMP_SIZE 5
#define PTR_TYPE uint32_t
#define DST_TYPE int32_t
#define DST_ARG (DST_TYPE)(target-orig-JMP_SIZE)
	char op[JMP_SIZE];
	op[0] = 0xe9; /*jmp*/
	void *addrptr = op+1;
#endif
#define FN_OFFSET orig - (((PTR_TYPE)orig)%4096)
#define MPROTECT_SIZE (((PTR_TYPE)orig+4095+JMP_SIZE)/4096)*4096 - \
				((PTR_TYPE)orig-((PTR_TYPE)orig%4096))

#ifdef _WIN32
	DWORD wtf;
	if(!VirtualProtect(FN_OFFSET, MPROTECT_SIZE, PAGE_EXECUTE_READWRITE, &wtf))
	{
		DWORD dw = GetLastError();
		LPVOID buf;
		printf("got error\n");
		FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER|
				FORMAT_MESSAGE_FROM_SYSTEM|
				FORMAT_MESSAGE_IGNORE_INSERTS,
				NULL,
				dw,
			       	MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
				(LPSTR)&buf,
				0, NULL);
		printf("VirtualProtect() failed!\n");
		printf(buf);
		return 0;
	}
#else
	if(mprotect(FN_OFFSET, MPROTECT_SIZE,PROT_READ|PROT_WRITE|PROT_EXEC) == -1) {
		printf("mprotect failed!: %s\n", strerror(errno));
		return 0;
	}
#endif
	*(DST_TYPE*)addrptr = DST_ARG;
	memcpy(orig, op, JMP_SIZE);
	return 1;
}
