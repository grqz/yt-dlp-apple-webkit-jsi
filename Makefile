CC = clang
CFLAGS = --std=c99 -Wall
CXX = clang++
CXXFLAGS = --std=c++17 -Wall
OBJCFLAGS = --std=c99 -Wall -fblocks -fno-objc-arc \
	-framework Foundation -framework WebKit -framework CoreFoundation -framework CoreGraphics \
	-isysroot "$(shell xcrun --show-sdk-path)"

all: hello translated

translated: translated.m config.o
	$(CC) $(OBJCFLAGS) $^ -o $@

config.o: config.cpp
	$(CXX) $(CXXFLAGS) -c $^ -o $@

hello: hello.c config.o testcall.o
	$(CC) $(CFLAGS) $^ -o $@

testcall.o: testcall.m
	$(CC) $(OBJCFLAGS) -c $^ -o $@

clean:
	rm -f *.o a.out hello translated
