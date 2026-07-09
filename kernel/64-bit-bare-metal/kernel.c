#include <stdint.h>
#include <stddef.h>

#define VGA_MEMORY ((volatile uint16_t*)0xB8000)
#define VGA_WIDTH 80
#define VGA_HEIGHT 25

static size_t row = 0;
static size_t col = 0;
static uint8_t color = 0x0F;

static inline uint8_t inb(uint16_t port) {
    uint8_t ret;
    __asm__ volatile ("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

static void putchar(char c) {
    if (c == '\n') {
        row++;
        col = 0;
    } else if (c == '\b') {
        if (col > 0) {
            col--;
            VGA_MEMORY[row * VGA_WIDTH + col] = ((uint16_t)color << 8) | ' ';
        }
    } else {
        VGA_MEMORY[row * VGA_WIDTH + col] = ((uint16_t)color << 8) | c;
        col++;

        if (col >= VGA_WIDTH) {
            col = 0;
            row++;
        }
    }

    if (row >= VGA_HEIGHT) {
        row = 0;
        col = 0;
    }
}

static void print(const char *s) {
    while (*s) {
        putchar(*s++);
    }
}

static void clear_screen(void) {
    for (size_t i = 0; i < VGA_WIDTH * VGA_HEIGHT; i++) {
        VGA_MEMORY[i] = ((uint16_t)color << 8) | ' ';
    }

    row = 0;
    col = 0;
}

static char scancode_to_ascii(uint8_t sc) {
    static const char map[128] = {
        0,  27, '1','2','3','4','5','6','7','8','9','0','-','=', '\b',
        '\t','q','w','e','r','t','y','u','i','o','p','[',']','\n',
        0,  'a','s','d','f','g','h','j','k','l',';','\'','`',
        0,  '\\','z','x','c','v','b','n','m',',','.','/',
        0,  '*', 0, ' '
    };

    if (sc >= 128) {
        return 0;
    }

    return map[sc];
}

static char getchar(void) {
    for (;;) {
        if (inb(0x64) & 1) {
            uint8_t sc = inb(0x60);

            if (!(sc & 0x80)) {
                char c = scancode_to_ascii(sc);

                if (c) {
                    return c;
                }
            }
        }
    }
}

void kernel_main(void) {
    clear_screen();

    print("64-bit bare metal kernel\n");
    print("> ");

    for (;;) {
        char c = getchar();

        if (c == '\n') {
            putchar('\n');
            print("> ");
        } else {
            putchar(c);
        }
    }
}
