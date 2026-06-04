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

void func(char *s)
{
	char buffer[8];

	memcpy(buffer, s, 24);
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

	func(hack);
}
