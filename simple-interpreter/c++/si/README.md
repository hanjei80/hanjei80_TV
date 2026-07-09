# si — simple interpreter in C++

`si` is a tiny C-like interpreter written in **C++17**. The name means "simple interpreter" and nods to `sí` — Spanish for "yes".

It supports:

- C-like syntax: `let`, assignment, `if/else`, `while`, blocks, functions, `return`
- values: numbers, strings, booleans, `null`
- arithmetic, comparison, logical operators
- built-ins: `print`, `clock`, `len`, `str`, `int`, `float`
- C/C++ extension points through shared libraries
- JNI-inspired native binding with `native(...)`

## Build

```bash
make
```

This creates the executable:

```bash
./si examples/hello.si
```

Manual compile:

```bash
g++ -std=c++17 -O2 -Wall -Wextra -o si src/si.cpp -ldl
```

On macOS, `-ldl` is normally not needed.

## Language sample

```c
let x = 5;
let y = 7;
print("sum =", x + y);

func fib(n) {
  if (n <= 1) return n;
  return fib(n - 1) + fib(n - 2);
}

print("fib(10) =", fib(10));
```

## Native C linking

Write C code:

```c
double c_add(double a, double b) {
    return a + b;
}
```

Compile it as a shared library:

```bash
gcc -shared -fPIC plugins/native_math.c -o plugins/native_math.so
```

Load and bind it inside `si`:

```c
native("../plugins/native_math.so", "c_add", "addc", "double", "double", "double");
print(addc(2.5, 4.25));
```

This starter native binder currently supports:

- `double(double, double)`
- `int(int, int)`

The code is intentionally small, so adding more ABI signatures is straightforward in `Interpreter::native(...)`.

## Plugin hook

`plugin(path)` loads a shared library with `dlopen` and looks for this exported symbol:

```cpp
extern "C" void si_register(Interpreter* si);
```

That gives you a place to extend the runtime from C++. For a production version, the next step would be to move the public API into a stable `si_plugin.h` header instead of exposing the interpreter class directly.

## Files

- `src/si.cpp` — C++ interpreter
- `Makefile` — build script
- `examples/hello.si` — basic example
- `examples/native_demo.si` — native C linking example
- `plugins/native_math.c` — sample C native plugin
