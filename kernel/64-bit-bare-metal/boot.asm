bits 16
org 0x7C00

KERNEL_OFFSET equ 0x1000
KERNEL_SECTORS equ 32

PML4 equ 0x70000
PDPT equ 0x71000
PD   equ 0x72000

start:
    cli

    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    mov [BOOT_DRIVE], dl

    ; Enable A20 using fast A20 gate
    in al, 0x92
    or al, 00000010b
    out 0x92, al

    ; Load kernel to 0000:1000
    mov ah, 0x02
    mov al, KERNEL_SECTORS
    mov ch, 0
    mov cl, 2
    mov dh, 0
    mov dl, [BOOT_DRIVE]
    mov bx, KERNEL_OFFSET
    int 0x13
    jc disk_error

    lgdt [gdt32_desc]

    mov eax, cr0
    or eax, 1
    mov cr0, eax

    jmp 0x08:protected_mode

disk_error:
    mov ah, 0x0E
    mov al, 'E'
    int 0x10
    hlt
    jmp $

BOOT_DRIVE db 0

gdt32:
    dq 0
    dq 0x00CF9A000000FFFF
    dq 0x00CF92000000FFFF
gdt32_end:

gdt32_desc:
    dw gdt32_end - gdt32 - 1
    dd gdt32

bits 32

protected_mode:
    mov ax, 0x10
    mov ds, ax
    mov ss, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    mov esp, 0x90000

    ; Clear page table area
    mov edi, PML4
    xor eax, eax
    mov ecx, 0x3000 / 4
    rep stosd

    ; PML4[0] -> PDPT
    mov dword [PML4], PDPT | 0x03
    mov dword [PML4 + 4], 0

    ; PDPT[0] -> PD
    mov dword [PDPT], PD | 0x03
    mov dword [PDPT + 4], 0

    ; Identity-map first 8 MiB using 2 MiB pages
    mov dword [PD + 0], 0x00000083
    mov dword [PD + 4], 0

    mov dword [PD + 8], 0x00200083
    mov dword [PD + 12], 0

    mov dword [PD + 16], 0x00400083
    mov dword [PD + 20], 0

    mov dword [PD + 24], 0x00600083
    mov dword [PD + 28], 0

    ; Enable PAE
    mov eax, cr4
    or eax, 1 << 5
    mov cr4, eax

    ; Load PML4
    mov eax, PML4
    mov cr3, eax

    ; Enable Long Mode
    mov ecx, 0xC0000080
    rdmsr
    or eax, 1 << 8
    wrmsr

    ; Enable paging
    mov eax, cr0
    or eax, 1 << 31
    mov cr0, eax

    lgdt [gdt64_desc]

    jmp 0x08:long_mode

gdt64:
    dq 0
    dq 0x00AF9A000000FFFF
    dq 0x00AF92000000FFFF
gdt64_end:

gdt64_desc:
    dw gdt64_end - gdt64 - 1
    dd gdt64

bits 64

long_mode:
    mov ax, 0x10
    mov ds, ax
    mov ss, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    mov rsp, 0x90000

    jmp KERNEL_OFFSET

times 510 - ($ - $$) db 0
dw 0xAA55
