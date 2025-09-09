C_CXX_OBJC_WARNING_FLAGS ?= -Wall -Wextra -pedantic -Wno-unused-but-set-variable -Wno-cast-function-type -Wno-unused-parameter
CC ?= clang
CFLAGS ?= -g --std=c99 $(C_CXX_OBJC_WARNING_FLAGS)
CXX ?= clang++
CXXFLAGS ?= --std=c++17 $(C_CXX_OBJC_WARNING_FLAGS)
OBJC ?= clang
OBJCFLAGS ?= --std=c99 $(C_CXX_OBJC_WARNING_FLAGS) -fblocks -fno-objc-arc
LDFLAGS ?= -fsanitize=address \
	-framework Foundation -framework WebKit -framework CoreFoundation -framework CoreGraphics \
	-isysroot "$(shell xcrun --show-sdk-path)"

all: hello translated testcall

translated: translated.o config.o cbmap.o
	$(CXX) $(LDFLAGS) $^ -o $@

translated.o: translated.m
	$(OBJC) $(OBJCFLAGS) -c $^ -o $@

hello: hello.o config.o cbmap.o
	$(CXX) $(LDFLAGS) $^ -o $@

hello.o: hello.c
	$(CC) $(CFLAGS) -c $^ -o $@

testcall: testcall.m
	$(OBJC) $(OBJCFLAGS) $(LDFLAGS) $^ -o $@

config.o: config.cpp
	$(CXX) $(CXXFLAGS) -c $^ -o $@

cbmap.o: cbmap.cpp
	$(CXX) $(CXXFLAGS) -c $^ -o $@

clean:
	rm -f *.o a.out hello translated
