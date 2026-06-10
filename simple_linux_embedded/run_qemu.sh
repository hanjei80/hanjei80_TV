#!/bin/bash

qemu-system-x86_64 -kernel vmlinuz -nographic -initrd initramfs.cpio.gz -append "console=ttyS0 init=/init"
