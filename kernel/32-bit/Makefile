all: os-image.bin

boot.bin: boot.asm
	nasm -f bin boot.asm -o boot.bin

kernel_entry.o: kernel_entry.asm
	nasm -f elf32 kernel_entry.asm -o kernel_entry.o

kernel.o: kernel.c
	i686-linux-gnu-gcc -m32 -ffreestanding -fno-pie -fno-stack-protector \
		-nostdlib -c kernel.c -o kernel.o

kernel.elf: kernel_entry.o kernel.o linker.ld
	i686-linux-gnu-ld -m elf_i386 -T linker.ld -o kernel.elf kernel_entry.o kernel.o

kernel.bin: kernel.elf
	i686-linux-gnu-objcopy -O binary kernel.elf kernel.bin

os-image.bin: boot.bin kernel.bin
	cat boot.bin kernel.bin > os-image.bin
	truncate -s 16896 os-image.bin

run: os-image.bin
	qemu-system-i386 -drive format=raw,file=os-image.bin

clean:
	rm -f *.bin *.o *.elf
