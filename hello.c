#include "config.h"
#include "fn_to_block.h"

#include <stdio.h>
#include <stdarg.h>

#include <dlfcn.h>

#define SYSFWK(fwk) "/System/Library/Frameworks/" #fwk ".framework/" #fwk

struct Prototype_CGRect {
    struct { double x, y; } m_orig, m_size;
} Proto_CGRectZero = { {0.00, 0.00}, {0.00, 0.00} };

typedef void *(*FnProto_objc_getClass)(const char *name);

typedef void (*FnProto_objc_msgSend)();
typedef void (*FnProtov_objc_msgSend)(void *self, void *op);
typedef void (*FnProtov_2vp_objc_msgSend)(void *self, void *op, void *, void *);
typedef void (*FnProtov_5vp_objc_msgSend)(void *self, void *op, void *, void *, void *, void *, void *);
typedef void (*FnProtov_u8_objc_msgSend)(void *self, void *op, unsigned char);
typedef void *(*FnProtovp_CGRect_vp_objc_msgSend)(void *self, void *op, struct Prototype_CGRect, void *);
typedef void *(*FnProtovp_2vp_objc_msgSend)(void *self, void *op, void *, void *);
typedef void *(*FnProtovp_objc_msgSend)(void *self, void *op);
typedef void *(*FnProtovp_vp_objc_msgSend)(void *self, void *op, void *);

typedef void *(*FnProto_sel_registerName)(const char * str);

typedef void (*FnProto_NSLog)(void *format, ...);

const unsigned char kbTrue = 1, kbFalse = 0;

static inline
void onCallAsyncJSComplete(struct Prototype_FnPtrWrapperBlock *self, void *idResult, void *nserrError) {
    fprintf(stderr, "JS Complete! idResult: %p; nserrError: %p\n", idResult, nserrError);
}

int main(void) {
    char nul = 0;
    int ret = 1;
    void *objc = dlopen("/usr/lib/libobjc.A.dylib", RTLD_LAZY);
    if (!objc) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to load libobjc: %s; Are you on APPLE?\n", errm ? errm : &nul);
        goto fail_ret;
    }

    void *libSystem = dlopen("/usr/lib/libSystem.B.dylib", RTLD_LAZY);
    if (!libSystem) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to load libSystem: %s; Are you on APPLE?\n", errm ? errm : &nul);
        goto fail_objc;
    }

    // Frameworks
    void *foundation = dlopen(SYSFWK(Foundation), RTLD_LAZY);
    if (!foundation) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to load Foundation: %s; Is it in the right place?\n", errm ? errm : &nul);
        goto fail_libSystem;
    }

    void *webkit = dlopen(SYSFWK(WebKit), RTLD_LAZY);
    if (!webkit) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to load Webkit: %s; Is it in the right place?\n", errm ? errm : &nul);
        goto fail_foundation;
    }

    void *cf = dlopen(SYSFWK(CoreFoundation), RTLD_LAZY);
    if (!cf) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to load CoreFoundation: %s; Is it in the right place?\n", errm ? errm : &nul);
        goto fail_webkit;
    }
    fprintf(stderr, "All libraries loaded\n");

    FnProto_objc_getClass objc_getClass = dlsym(objc, "objc_getClass");
    if (!objc_getClass) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get objc_getClass: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    FnProto_objc_msgSend objc_msgSend = dlsym(objc, "objc_msgSend");
    if (!objc_msgSend) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get objc_msgSend: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    FnProto_sel_registerName sel_registerName = dlsym(objc, "sel_registerName");
    if (!sel_registerName) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get sel_registerName: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }

    void *pNSConcreteStackBlock = dlsym(libSystem, "_NSConcreteStackBlock");
    if (!pNSConcreteStackBlock) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get _NSConcreteStackBlock: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }

    FnProto_NSLog NSLog = dlsym(foundation, "NSLog");
    if (!NSLog) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get NSLog from Foundation: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    void *kCFBooleanTrue = *(void **)dlsym(cf, "kCFBooleanTrue");
    if (!kCFBooleanTrue) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get NSLog from CoreFoundation: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    void *kCFBooleanFalse = *(void **)dlsym(cf, "kCFBooleanFalse");
    if (!kCFBooleanFalse) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get NSLog from CoreFoundation: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }

    void *ClsNSString = objc_getClass("NSString");
    if (!ClsNSString) {
        fprintf(stderr, "Failed to getClass NSString\n");
        goto fail_libs;
    }
    void *ClsNSDictionary = objc_getClass("NSDictionary");
    if (!ClsNSDictionary) {
        fprintf(stderr, "Failed to getClass NSDictionary\n");
        goto fail_libs;
    }
    void *ClsWKWebView = objc_getClass("WKWebView");
    if (!ClsWKWebView) {
        fprintf(stderr, "Failed to getClass WKWebView\n");
        goto fail_libs;
    }
    void *ClsWKContentWorld = objc_getClass("WKContentWorld");
    if (!ClsWKContentWorld) {
        fprintf(stderr, "Failed to getClass WKContentWorld\n");
        goto fail_libs;
    }
    void *ClsWKWebViewConfiguration = objc_getClass("WKWebViewConfiguration");
    if (!ClsWKWebViewConfiguration) {
        fprintf(stderr, "Failed to getClass WKWebViewConfiguration\n");
        goto fail_libs;
    }
    void *selAlloc = sel_registerName("alloc");
    void *selInit = sel_registerName("init");
    void *selRelease = sel_registerName("release");
    void *selSetVal4K = sel_registerName("setValue:forKey:");
    fprintf(stderr, "Initialised selectors\n");

    void *pStr = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(ClsNSString, sel_registerName("stringWithUTF8String:"), "Hello, World!");
    fprintf(stderr, "Initialised NSString\n");
    NSLog(pStr);
    fprintf(stderr, "Logged NSString\n");
    ((FnProtov_objc_msgSend)objc_msgSend)(pStr, selRelease); pStr = NULL;
    fprintf(stderr, "Released NSString\n");

    void *pCfg = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKWebViewConfiguration, selAlloc);
    pCfg = ((FnProtovp_objc_msgSend)objc_msgSend)(pCfg, selInit);
    void *pPref = ((FnProtovp_objc_msgSend)objc_msgSend)(pCfg, sel_registerName("preferences"));
    ((FnProtov_u8_objc_msgSend)objc_msgSend)(pPref, sel_registerName("setJavaScriptCanOpenWindowsAutomatically:"), kbTrue);

    void *psSetKey = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(ClsNSString, sel_registerName("stringWithUTF8String:"), "allowFileAccessFromFileURLs");
    ((FnProtov_2vp_objc_msgSend)objc_msgSend)(pPref, selSetVal4K, kCFBooleanTrue, psSetKey);
    ((FnProtov_objc_msgSend)objc_msgSend)(psSetKey, selRelease); psSetKey = NULL;

    pPref = NULL;

    psSetKey = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(ClsNSString, sel_registerName("stringWithUTF8String:"), "allowUniversalAccessFromFileURLs");
    ((FnProtov_2vp_objc_msgSend)objc_msgSend)(pCfg, selSetVal4K, kCFBooleanTrue, psSetKey);
    ((FnProtov_objc_msgSend)objc_msgSend)(psSetKey, selRelease); psSetKey = NULL;

    void *pWebview = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKWebView, selAlloc);
    pWebview = ((FnProtovp_CGRect_vp_objc_msgSend)objc_msgSend)(pWebview, sel_registerName("initWithFrame:configuration:"), Proto_CGRectZero, pCfg);
    ((FnProtov_objc_msgSend)objc_msgSend)(pCfg, selRelease); pCfg = NULL;
    fprintf(stderr, "Initialised WKWebView\n");

    void *psHTMLString = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(ClsNSString, sel_registerName("stringWithUTF8String:"), (void *)szHTMLString);
    void *psBaseURL = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(ClsNSString, sel_registerName("stringWithUTF8String:"), (void *)szBaseURL);

    ((FnProtovp_2vp_objc_msgSend)objc_msgSend)(pWebview, sel_registerName("loadHTMLString:baseURL:"), psHTMLString, psBaseURL);

    ((FnProtov_objc_msgSend)objc_msgSend)(psBaseURL, selRelease); psBaseURL = NULL;
    ((FnProtov_objc_msgSend)objc_msgSend)(psHTMLString, selRelease); psHTMLString = NULL;
    fprintf(stderr, "Set up WKWebView\n");

    void *psScript = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(ClsNSString, sel_registerName("stringWithUTF8String:"), (void *)szScript);

    void *pdJsArguments = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSDictionary, selAlloc);
    pdJsArguments = ((FnProtovp_objc_msgSend)objc_msgSend)(pdJsArguments, selInit);

    void *rpPageWorld = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKContentWorld, sel_registerName("pageWorld"));
    struct Prototype_FnPtrWrapperBlock block;
    block.isa = pNSConcreteStackBlock;
    make_wrapper(&block, &onCallAsyncJSComplete, NULL);
    ((FnProtov_5vp_objc_msgSend)objc_msgSend)(
        pWebview, sel_registerName("callAsyncJavaScript"),
        psScript, pdJsArguments, /*inFrame=*/NULL, rpPageWorld,
        /*completionHandler: (void (^)(id result, NSError *error))=*/
        &block);
    fprintf(stderr, "Submitted Asynchronous JS execution\n");

    ((FnProtov_objc_msgSend)objc_msgSend)(pdJsArguments, selRelease); pdJsArguments = NULL;

    ((FnProtov_objc_msgSend)objc_msgSend)(psScript, selRelease); psScript = NULL;


    ((FnProtov_objc_msgSend)objc_msgSend)(pWebview, selRelease); pWebview = NULL;
    fprintf(stderr, "Freed all\n");

    ret = 0;

fail_libs:
// fail_cf:
    if (dlclose(cf)) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to dlclose CoreFoundation: %s\n", errm ? errm : &nul);
    }
fail_webkit:
    if (dlclose(webkit)) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to dlclose WebKit: %s\n", errm ? errm : &nul);
    }
fail_foundation:
    if (dlclose(foundation)) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to dlclose Foundation: %s\n", errm ? errm : &nul);
    }
fail_libSystem:
    if (dlclose(libSystem)) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to dlclose libSystem: %s\n", errm ? errm : &nul);
    }
fail_objc:
    if (dlclose(objc)) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to dlclose libobjc: %s\n", errm ? errm : &nul);
    }
fail_ret:
    return ret;
}
