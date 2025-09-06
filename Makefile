CC ?= clang
CFLAGS ?= --std=c99 -Wall
CXX ?= clang++
CXXFLAGS ?= --std=c++17 -Wall
OBJC ?= clang
OBJCFLAGS ?= --std=c99 -Wall -fblocks -fno-objc-arc
LDFLAGS ?= \
	-framework Foundation -framework WebKit -framework CoreFoundation -framework CoreGraphics \
	-isysroot "$(shell xcrun --show-sdk-path)"

all: hello translated

translated: translated.o config.o cbmap.o
	$(CXX) $(LDFLAGS) $^ -o $@

translated.o: translated.m
	$(OBJC) $(OBJCFLAGS) -c $^ -o $@

hello: hello.o config.o cbmap.o
	$(CXX) $(LDFLAGS) $^ -o $@

hello.o: hello.c
	$(CC) $(CFLAGS) -c $^ -o $@

config.o: config.cpp
	$(CXX) $(CXXFLAGS) -c $^ -o $@

cbmap.o: cbmap.cpp
	$(CXX) $(CXXFLAGS) -c $^ -o $@

clean:
	rm -f *.o a.out hello translated
