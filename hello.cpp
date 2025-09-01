#include <cstdio>

#define _GNU_SOURCE
#include <dlfcn.h>

#include <objc/objc.h>
#include <objc/runtime.h>
// only loaded:
// _dyld_image_count
// _dyld_get_image_name range
// strstr _ Foundation.framework
// obsolete:
// dyld
// NSAddImage
// objc:
// NSBundle
// message.h

extern "C"
typedef void (*FnProto_NSLog)(id format, ...);

int main() {
    int ret = 1;
    id ClsNSString = objc_getClass("NSString");
    if (!ClsNSString) {
        fprintf(stderr, "Failed to get NSString\n");
        goto end0;
    }
    void *foundation = dlopen("/System/Library/Frameworks/Foundation.framework/Foundation", RTLD_LAZY);
    if (!foundation) {
        fprintf(stderr, "Failed to load Foundation, is it in the right place?\n");
        goto end0;
    }
    SEL msgAlloc = sel_registerName("alloc");
    SEL msgInit = sel_registerName("init");
    SEL msgDealloc = sel_registerName("dealloc");
    id pStr = objc_msgSend(ClsNSString, msgAlloc);
    pStr = objc_msgSend(pStr, sel_registerName("initWithUTF8String:"), "Hello, World");

    FnProto_NSLog NSLog = dlsym(foundation, "NSLog");
    if (!NSLog) {
        fprintf(stderr, "Could not find NSLog");
        goto end2;
    }

    NSLog(pStr);

    ret = 0;
end2:
    objc_msgSend(pStr, msgDealloc);
end1:
    dlclose(foundation);
end0:
    return ret;
}
