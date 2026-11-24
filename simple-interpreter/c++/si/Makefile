CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra
LDFLAGS ?= -ldl

all: si plugins/native_math.so

si: src/si.cpp
	$(CXX) $(CXXFLAGS) -o si src/si.cpp $(LDFLAGS)

plugins/native_math.so: plugins/native_math.c
	$(CC) -shared -fPIC plugins/native_math.c -o plugins/native_math.so

clean:
	rm -f si plugins/native_math.so
