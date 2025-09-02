#include <stdio.h>

#include <dlfcn.h>

#define SYSFWK(fwk) "/System/Library/Frameworks/" #fwk ".framework/" #fwk

typedef void *(*FnProto_objc_getClass)(const char *name);

typedef void (*FnProto_objc_msgSend)();
typedef void (*FnProtov_objc_msgSend)(void *self, void *op);
typedef void *(*FnProtovp_objc_msgSend)(void *self, void *op);
typedef void *(*FnProtovp_vp_objc_msgSend)(void *self, void *op, void *);

typedef void *(*FnProto_sel_registerName)(const char * str);

typedef void (*FnProto_NSLog)(void *format, ...);

int main(void) {
    char nul = 0;
    int ret = 1;
    void *objc = dlopen("/usr/lib/libobjc.A.dylib", RTLD_NOW);
    if (!objc) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to load libobjc: %s; Are you on APPLE?\n", errm ? errm : &nul);
        goto end0;
    }
    FnProto_objc_getClass objc_getClass = dlsym(objc, "objc_getClass");
    if (!objc_getClass) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get objc_getClass: %s\n", errm ? errm : &nul);
        goto end1;
    }
    FnProto_objc_msgSend objc_msgSend = dlsym(objc, "objc_msgSend");
    if (!objc_msgSend) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get objc_msgSend: %s\n", errm ? errm : &nul);
        goto end1;
    }
    FnProto_sel_registerName sel_registerName = dlsym(objc, "sel_registerName");
    if (!sel_registerName) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get sel_registerName: %s\n", errm ? errm : &nul);
        goto end1;
    }

    // Would Foundation.framework always be here?
    void *foundation = dlopen(SYSFWK(Foundation), RTLD_LAZY);
    if (!foundation) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to load Foundation: %s; Is it in the right place?\n", errm ? errm : &nul);
        goto end1;
    }

    void *webkit = dlopen(SYSFWK(WebKit), RTLD_LAZY);
    if (!webkit) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to load Webkit: %s; Is it in the right place?\n", errm ? errm : &nul);
        goto end2;
    }
    fprintf(stderr, "All libraries loaded\n");

    FnProto_NSLog NSLog = dlsym(foundation, "NSLog");
    if (!NSLog) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get NSLog from Foundation: %s\n", errm ? errm : &nul);
        goto end3;
    }

    void *ClsNSString = objc_getClass("NSString");
    if (!ClsNSString) {
        fprintf(stderr, "Failed to getClass NSString\n");
        goto end3;
    }
    void *selAlloc = sel_registerName("alloc");
    void *selInit = sel_registerName("init");
    void *selRelease = sel_registerName("release");
    fprintf(stderr, "Initialised selectors\n");
    void *pStr = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc);
    fprintf(stderr, "Allocated NSString\n");
    pStr = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(pStr, sel_registerName("initWithUTF8String:"), "Hello, World");
    fprintf(stderr, "Initialised NSString\n");

    NSLog(pStr);
    fprintf(stderr, "Logged NSString\n");

    ret = 0;
end4:
    ((FnProtov_objc_msgSend)objc_msgSend)(pStr, selRelease);
end3:
    if (dlclose(webkit)) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to dlclose WebKit: %s\n", errm ? errm : &nul);
    }
end2:
    if (dlclose(foundation)) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to dlclose Foundation: %s\n", errm ? errm : &nul);
    }
end1:
    if (dlclose(objc)) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to dlclose libobjc: %s\n", errm ? errm : &nul);
    }
end0:
    return ret;
}
