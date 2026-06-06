/*
  compile in linux with: gcc -fno-stack-protector 2026-06-05-buffer-overflow.c -o 2026-06-05-buffer-overflow.out

*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>


void func2()
{
	printf("How did I end up here??\n");
}

/*
0xffffffff

stack grows downwards

8 bytes gets allocated by substracting the stack pointer by 8 bytes

-8(esp)
...... <-- overflows here... but what is here? well there's the RIP, and saved frame pointer...
.......
.......
buffer[8].... when it overflows... it goes up



heap grows upwards

0x00000000



*/

void func(char *s)
{
	char buffer[8];

	memcpy(buffer, s, 24);

	return;
}

int main()
{

	char hack[1024];
	long *p;

	printf("0x%lx\n", func2);

	p = (long *) &hack;
	*p++ = func2;
	*p++ = func2;
	*p++ = func2;


//	strcpy(hack, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");

	func(hack);
}
