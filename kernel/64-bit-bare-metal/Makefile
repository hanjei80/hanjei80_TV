# CC = x86_64-elf-gcc
# LD = x86_64-elf-ld
# OBJCOPY = x86_64-elf-objcopy
CC = x86_64-linux-gnu-gcc
LD = x86_64-linux-gnu-ld
OBJCOPY = x86_64-linux-gnu-objcopy
NASM = nasm

KERNEL_SECTORS = 32
IMAGE_SIZE = 16896

all: os-image.bin

boot.bin: boot.asm
	$(NASM) -f bin boot.asm -o boot.bin

kernel_entry.o: kernel_entry.asm
	$(NASM) -f elf64 kernel_entry.asm -o kernel_entry.o

kernel.o: kernel.c
	$(CC) -ffreestanding -fno-pie -fno-pic -fno-stack-protector \
		-m64 -mno-red-zone -nostdlib -c kernel.c -o kernel.o

kernel.elf: kernel_entry.o kernel.o linker.ld
	$(LD) -T linker.ld -o kernel.elf kernel_entry.o kernel.o

kernel.bin: kernel.elf
	$(OBJCOPY) -O binary kernel.elf kernel.bin

os-image.bin: boot.bin kernel.bin
	cat boot.bin kernel.bin > os-image.bin
	truncate -s $(IMAGE_SIZE) os-image.bin

run: os-image.bin
	qemu-system-x86_64 -drive file=os-image.bin,format=raw,index=0,media=disk

clean:
	rm -f *.bin *.o *.elf os-image.bin
