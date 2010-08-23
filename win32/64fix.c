/*Thanks to ne from ##linux for helping me with this.. I made the windows parts*/

#include <stdio.h>
#include <stdlib.h>

#ifndef _WIN32
#include <sys/mman.h>
#else
#include <windows.h>
#endif

#include <sys/types.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>

void foo1(void) {printf("in foo1\n");}
void foo2(void) {printf("in foo2\n");}

void override(void *orig, void *target) {
#ifdef _LP64
#define JMP_SIZE 12
#define PTR_TYPE uint64_t
#define DST_TYPE PTR_TYPE	
#define DST_ARG (PTR_TYPE)target
	char op[JMP_SIZE];
	op[0] = 0x48;
	op[1] = 0xb8;
	op[10] = 0xff;
	op[11] = 0xe0;
	void *addrptr = op+2;
#else
#define JMP_SIZE 5
#define PTR_TYPE uint32_t
#define DST_TYPE int32_t
#define DST_ARG (DST_TYPE)(int32_t)(target-orig-5)
	char op[JMP_SIZE];
	op[0] = 0xe9;
	void *addrptr = op+1;
#endif
#define FN_OFFSET orig - (((PTR_TYPE)orig)%4096)
#define MPROTECT_SIZE (((PTR_TYPE)orig+4095+JMP_SIZE)/4096)*4096 - \
				((PTR_TYPE)orig-((PTR_TYPE)orig%4096))

#ifdef _WIN32
	printf("fn_offset: %lx\n", FN_OFFSET);
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
		exit(1);
	}
#else
	if(mprotect(FN_OFFSET, MPROTECT_SIZE,PROT_READ|PROT_WRITE|PROT_EXEC) == -1) {
		printf("mprotect failed!: %s\n", strerror(errno));
		exit(1);
	}
#endif
	*(DST_TYPE*)addrptr = DST_ARG;
	memcpy(orig, op, JMP_SIZE);
}

int main(void)
{
	override(foo1, foo2);
	foo1();
	return 0;
}
