#!/bin/bash

mkdir rootfs
cd rootfs
cp ../hello init
find . | cpio -o -H newc | gzip > ../initramfs.cpio.gz


