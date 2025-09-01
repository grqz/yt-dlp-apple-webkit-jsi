#include <stdio.h>

#include <dlfcn.h>

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

#ifdef __cplusplus
extern "C" {
#endif

typedef void *(*FnProto_objc_getClass)(const char *name);
typedef void (*FnProto_objc_msgSend)(void *self, void *op, ...);

typedef void *(*FnProto_sel_registerName)(const char * str);

typedef void (*FnProto_NSLog)(void *format, ...);

#ifdef __cplusplus
}
#endif

int main(void) {
    int ret = 1;
    void *objc = dlopen("/usr/lib/libobjc.A.dylib", RTLD_LAZY);
    if (!objc) {
        fprintf(stderr, "Failed to load libobjc, are you on APPLE?\n");
        goto end0;
    }
    FnProto_objc_getClass objc_getClass = dlsym(objc, "objc_getClass");
    if (!objc_getClass) {
        fprintf(stderr, "Failed to get objc_getClass\n");
        goto end1;
    }
    FnProto_objc_msgSend objc_msgSend = dlsym(objc, "objc_msgSend");
    if (!objc_msgSend) {
        fprintf(stderr, "Failed to get objc_msgSend\n");
        goto end1;
    }
    FnProto_sel_registerName sel_registerName = dlsym(objc, "sel_registerName");
    if (!sel_registerName) {
        fprintf(stderr, "Failed to get sel_registerName\n");
        goto end1;
    }

    void *foundation = dlopen("/System/Library/Frameworks/Foundation.framework/Foundation", RTLD_LAZY);
    if (!foundation) {
        fprintf(stderr, "Failed to load Foundation, is it in the right place?\n");
        goto end1;
    }
    fprintf(stderr, "All libraries loaded\n");

    FnProto_NSLog NSLog = dlsym(foundation, "NSLog");
    if (!NSLog) {
        fprintf(stderr, "Failed to load from Foundation: NSLog");
        goto end2;
    }
    void *ClsNSString = objc_getClass("NSString");
    if (!ClsNSString) {
        fprintf(stderr, "Failed to get NSString\n");
        goto end2;
    }
    void *msgAlloc = sel_registerName("alloc");
    void *msgInit = sel_registerName("init");
    void *msgDealloc = sel_registerName("dealloc");
    fprintf(stderr, "Initialised selectors\n");
    void *pStr = objc_msgSend(ClsNSString, msgAlloc);
    fprintf(stderr, "Allocated NSString\n");
    pStr = (((void *)(*)(void *, void *, const char *))objc_msgSend)(pStr, sel_registerName("initWithUTF8String:"), "Hello, World");
    fprintf(stderr, "Initialised NSString\n");

    NSLog(pStr);
    fprintf(stderr, "Logged NSString\n");

    ret = 0;
end3:
    objc_msgSend(pStr, msgDealloc);
end2:
    dlclose(foundation);
end1:
    dlclose(objc);
end0:
    return ret;
}
