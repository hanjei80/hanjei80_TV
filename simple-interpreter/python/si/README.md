# si — simple interpreter

`si` is a tiny C-like interpreter written in Python. It supports:

- C-like syntax: `let`, assignment, `if/else`, `while`, blocks, functions, `return`
- integers, floats, strings, booleans, `null`
- arithmetic, comparison, logical operators
- built-ins: `print`, `clock`, `len`, `str`, `int`, `float`
- plugins via dynamic Python modules
- native C integration via shared libraries (`.so`, `.dylib`, `.dll`) using `ctypes`

## Run

```bash
python3 src/si.py examples/hello.si
```

or make it executable:

```bash
chmod +x src/si.py
./src/si.py examples/hello.si
```

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

## Python plugins

Create a Python file with a `register(si)` function:

```python
def register(si):
    si.add_builtin("square", lambda x: x * x)
```

Then load it from `si`:

```c
plugin("plugins/math_plugin.py");
print(square(12));
```

## Native C plugins

Write C code:

```c
#include <stdint.h>

double c_add(double a, double b) {
    return a + b;
}
```

Compile:

```bash
gcc -shared -fPIC plugins/native_math.c -o plugins/native_math.so
```

Load and bind from `si`:

```c
native("plugins/native_math.so", "c_add", "addc", "double", "double", "double");
print(addc(2.5, 4.25));
```

`native(path, symbol, name, return_type, arg_type...)` supports these simple C types:

- `int`
- `double`
- `string`
- `void`

This is intentionally small and JNI-inspired, not a full ABI/framework.

## Files

- `src/si.py` — interpreter
- `examples/hello.si` — basic example
- `examples/plugin_demo.si` — Python plugin example
- `examples/native_demo.si` — C plugin example
- `plugins/math_plugin.py` — sample Python plugin
- `plugins/native_math.c` — sample C native plugin
