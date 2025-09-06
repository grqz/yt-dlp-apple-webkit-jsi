#include "config.h"
#include "cbmap.h"
#include "fn_to_block.h"

#include <stdio.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>

#include <dlfcn.h>

#define SYSFWK(fwk) "/System/Library/Frameworks/" #fwk ".framework/" #fwk
#define ALIGNOF_STRUCTURE(st) offsetof(struct { char c; st s; }, s)
#define FNPROTO_DECLARE(fn) \
    FnProto_##fn fn
#define LOADSYMBOL_BASE( \
    hLib, symType, sym, assignto, outvar, libName, onFailure) \
    do { \
        assignto = (symType)dlsym(hLib, sym); \
        if (!outvar) { \
            const char *_loadsymbol_internal_errm = dlerror(); \
            fprintf(stderr, \
                "Failed to get \"" sym "\" " \
                "from \"" libName "\": %s\n", \
                _loadsymbol_internal_errm \
                    ? _loadsymbol_internal_errm \
                    : ""); \
            onFailure; \
        } \
    } while (0)
#define LOADSYMBOL_SIMPLE(hLib, symType, sym, failLabel) \
    LOADSYMBOL_BASE(hLib, symType, #sym, sym, sym, #hLib, goto failLabel)
#define LOADSYMBOL_SIMPLE_INITG(hLib, symType, sym, failLabel) \
    LOADSYMBOL_BASE(hLib, symType, #sym, sym = initg_##sym, sym, #hLib, goto failLabel)

#define LOADFUNC(hLib, sym, failLabel) \
    LOADSYMBOL_SIMPLE(hLib, FnProto_##sym, sym, failLabel)
#define LOADFUNC_INITG(hLib, sym, failLabel) \
    LOADSYMBOL_SIMPLE_INITG(hLib, FnProto_##sym, sym, failLabel)
#define LOADFUNC_SETUP(hLib, sym, failLabel) \
    FNPROTO_DECLARE(sym); LOADFUNC(hLib, sym, failLabel)
#define LOADFUNC_SETUP_INITG(hLib, sym, failLabel) \
    FNPROTO_DECLARE(sym); LOADFUNC_INITG(hLib, sym, failLabel)


struct Prototype_CGRect {
    struct { double x, y; } m_orig, m_size;
} static const Proto_CGRectZero = { {0.00, 0.00}, {0.00, 0.00} };

struct Prototype_objc_super {
    void *receiver, *super_class;
};

typedef void *(*FnProto_objc_allocateClassPair)(void *superclass, const char *name, size_t extraBytes);
// typedef void (*FnProto_objc_disposeClassPair)(void *cls);  // unused
typedef void (*FnProto_objc_registerClassPair)(void *cls);

typedef void *(*FnProto_objc_getClass)(const char *name);

typedef void *(*FnProto_objc_getProtocol)(const char *name);

typedef void (*FnProto_objc_msgSend)();
FnProto_objc_msgSend initg_objc_msgSend = NULL;
typedef void (*FnProtov_objc_msgSend)(void *self, void *op);
typedef void (*FnProtov_2vp_objc_msgSend)(void *self, void *op, void *, void *);
typedef void (*FnProtov_5vp_objc_msgSend)(void *self, void *op, void *, void *, void *, void *, void *);
typedef void (*FnProtov_i8_objc_msgSend)(void *self, void *op, signed char);
typedef void (*FnProtov_vp_objc_msgSend)(void *self, void *op, void *);
typedef void *(*FnProtovp_CGRect_vp_objc_msgSend)(void *self, void *op, struct Prototype_CGRect, void *);
typedef void *(*FnProtovp_2vp_objc_msgSend)(void *self, void *op, void *, void *);
typedef void *(*FnProtovp_objc_msgSend)(void *self, void *op);
typedef void *(*FnProtovp_vp_objc_msgSend)(void *self, void *op, void *);
typedef signed char(*FnProtoi8_vp_objc_msgSend)(void *self, void *op, void *);

typedef void (*FnProto_objc_msgSendSuper)();
FnProto_objc_msgSendSuper initg_objc_msgSendSuper = NULL;
typedef void *(*FnProtovp_objc_msgSendSuper)(void *super, void *op);
typedef void (*FnProtov_objc_msgSendSuper)(void *super, void *op);

typedef void *(*FnProto_object_setInstanceVariable)(void *obj, const char *name, void *value);
FnProto_object_setInstanceVariable initg_object_setInstanceVariable = NULL;
typedef void *(*FnProto_object_getInstanceVariable)(void *obj, const char *name, void **outValue);
FnProto_object_getInstanceVariable initg_object_getInstanceVariable = NULL;
typedef void *(*FnProto_object_getClass)(void *obj);
FnProto_object_getClass initg_object_getClass = NULL;

typedef signed char (*FnProto_class_addProtocol)(void *cls, void *protocol);
typedef signed char (*FnProto_class_addMethod)(void *cls, void *name, void *imp, const char *types);
typedef signed char (*FnProto_class_addIvar)(void *cls, const char *name, size_t size, uint8_t alignment, const char *types);

typedef void *(*FnProto_sel_registerName)(const char * str);
FnProto_sel_registerName initg_sel_registerName = NULL;

typedef void (*FnProto_NSLog)(void *format, ...);

typedef void (*FnProto_CFRunLoopRun)(void);

typedef void (*FnProto_CFRunLoopStop)(void *rl);
FnProto_CFRunLoopStop initg_CFRunLoopStop = NULL;

typedef void *(*FnProto_CFRunLoopGetMain)(void);
FnProto_CFRunLoopGetMain initg_CFRunLoopGetMain = NULL;


const signed char kbTrue = 1, kbFalse = 0;
char nul = 0;

static inline
void *CFC_NaviDelegate_init(void *self, void *op) {
    fputs("CFC_NaviDelegate::init\n", stderr);
    struct Prototype_objc_super super = {
        self,
        ((FnProtovp_objc_msgSend)initg_objc_msgSend)(
            initg_object_getClass(self),
            initg_sel_registerName("superclass"))
    };
    self = ((FnProtovp_objc_msgSendSuper)initg_objc_msgSendSuper)(&super, op);
    if (self)
        initg_object_setInstanceVariable(self, "pmCbMap", cbmap_new());
    return self;
}
static inline
void CFC_NaviDelegate_dealloc(void *self, void *op) {
    fputs("CFC_NaviDelegate::dealloc\n", stderr);
    struct Prototype_objc_super super = {
        self,
        ((FnProtovp_objc_msgSend)initg_objc_msgSend)(
            initg_object_getClass(self),
            initg_sel_registerName("superclass"))
    };
    void *pmCbMap = NULL;
    initg_object_getInstanceVariable(self, "pmCbMap", &pmCbMap);
    if (pmCbMap)
        cbmap_free((CallbackMap *)pmCbMap);
    ((FnProtov_objc_msgSendSuper)initg_objc_msgSendSuper)(&super, op);
}

static inline
void CFC_NaviDelegate_webView0_didFinishNavigation1(
    void *self, void *op,
    void *rpwkwvWebView, void *rpwknNavigation
) {
    fputs("CFC_NaviDelegate::webview(WKWebView *_, WKNavigation *didFinishNavigation)\n", stderr);
    void *pmCbMap = NULL;
    initg_object_getInstanceVariable(self, "pmCbMap", &pmCbMap);
    if (pmCbMap)
        cbmap_callpop((CallbackMap *)pmCbMap, rpwknNavigation, rpwknNavigation);
    else
        fputs("webView:didFinishNavigation: pmCbMap unexpectedly null!\n", stderr);
}

static inline
void onNavigationFinished(void *ctx, void *userData) {
    fprintf(stderr, "Finished navigation: %p, userData: %p\n", ctx, userData);
    initg_CFRunLoopStop(initg_CFRunLoopGetMain());
}

struct OnCallAsyncJSCompleteUserData {
    const FnProto_CFRunLoopStop stop;
    const FnProto_CFRunLoopGetMain getmain;
    const FnProto_objc_msgSend objc_msgSend;
    const FnProto_sel_registerName sel_registerName;
    void *idResult;
};

static inline
void onCallAsyncJSComplete(struct Prototype_FnPtrWrapperBlock *self, void *idResult, void *nserrError) {
    fprintf(stderr, "UserData: %p\n", self->userData);
    fprintf(stderr, "JS Complete! idResult: %p; nserrError: %p\n", idResult, nserrError);
    struct OnCallAsyncJSCompleteUserData *userData = self->userData;
    if (nserrError) {
        long code = ((long(*)(void *self, void *op))userData->objc_msgSend)(nserrError, userData->sel_registerName("code"));
        void *rpsDomain = ((FnProtovp_objc_msgSend)userData->objc_msgSend)(nserrError, userData->sel_registerName("domain"));
        const char *szDomain = ((FnProtovp_objc_msgSend)userData->objc_msgSend)(rpsDomain, userData->sel_registerName("UTF8String"));
        void *rpdUserInfo = ((FnProtovp_objc_msgSend)userData->objc_msgSend)(nserrError, userData->sel_registerName("userInfo"));
        void *rpsUserInfo = ((FnProtovp_objc_msgSend)userData->objc_msgSend)(rpdUserInfo, userData->sel_registerName("description"));
        const char *szUserInfo = ((FnProtovp_objc_msgSend)userData->objc_msgSend)(rpsUserInfo, userData->sel_registerName("UTF8String"));
        fprintf(stderr, "Error encountered: code %lu, domain %s, userinfo %s\n", code, szDomain, szUserInfo);
    }
    if (idResult) {
        userData->idResult = ((FnProtovp_objc_msgSend)userData->objc_msgSend)(idResult, userData->sel_registerName("copy"));
    } else {
        userData->idResult = NULL;
    }
    userData->stop(userData->getmain());
}

int main(void) {
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

    FnProto_objc_allocateClassPair objc_allocateClassPair = dlsym(objc, "objc_allocateClassPair");
    if (!objc_allocateClassPair) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get objc_allocateClassPair: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    FnProto_objc_registerClassPair objc_registerClassPair = dlsym(objc, "objc_registerClassPair");
    if (!objc_registerClassPair) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get objc_registerClassPair: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    FnProto_objc_getClass objc_getClass = dlsym(objc, "objc_getClass");
    if (!objc_getClass) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get objc_getClass: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    FnProto_objc_msgSend objc_msgSend = initg_objc_msgSend = dlsym(objc, "objc_msgSend");
    if (!objc_msgSend) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get objc_msgSend: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    LOADFUNC_SETUP_INITG(objc, objc_msgSendSuper, fail_libs);
    LOADFUNC_SETUP(objc, objc_getProtocol, fail_libs);
    LOADFUNC_SETUP_INITG(objc, object_getInstanceVariable, fail_libs);
    LOADFUNC_SETUP_INITG(objc, object_setInstanceVariable, fail_libs);
    LOADFUNC_SETUP_INITG(objc, object_getClass, fail_libs);
    FnProto_class_addMethod class_addMethod = dlsym(objc, "class_addMethod");
    if (!class_addMethod) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get class_addMethod: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    FnProto_class_addIvar class_addIvar = dlsym(objc, "class_addIvar");
    if (!class_addIvar) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get class_addIvar: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }
    LOADFUNC_SETUP(objc, class_addProtocol, fail_libs);
    FnProto_sel_registerName sel_registerName = initg_sel_registerName = dlsym(objc, "sel_registerName");
    if (!sel_registerName) {
        const char *errm = dlerror();
        fprintf(stderr, "Failed to get sel_registerName: %s\n", errm ? errm : &nul);
        goto fail_libs;
    }

    void *p_NSConcreteStackBlock = dlsym(libSystem, "_NSConcreteStackBlock");
    if (!p_NSConcreteStackBlock) {
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
    // FnProto_CFRunLoopRun CFRunLoopRun = dlsym(cf, "CFRunLoopRun");
    // if (!CFRunLoopRun) {
    //     const char *errm = dlerror();
    //     fprintf(stderr, "Failed to get CFRunLoopRun from CoreFoundation: %s\n", errm ? errm : &nul);
    //     goto fail_libs;
    // }
    LOADFUNC_SETUP(cf, CFRunLoopRun, fail_libs);
    LOADFUNC_SETUP_INITG(cf, CFRunLoopGetMain, fail_libs);
    LOADFUNC_SETUP_INITG(cf, CFRunLoopStop, fail_libs);
    // FnProto_CFRunLoopGetMain CFRunLoopGetMain = dlsym(cf, "CFRunLoopGetMain");
    // if (!CFRunLoopGetMain) {
    //     const char *errm = dlerror();
    //     fprintf(stderr, "Failed to get CFRunLoopGetMain from CoreFoundation: %s\n", errm ? errm : &nul);
    //     goto fail_libs;
    // }
    // FnProto_CFRunLoopStop CFRunLoopStop = dlsym(cf, "CFRunLoopStop");
    // if (!CFRunLoopStop) {
    //     const char *errm = dlerror();
    //     fprintf(stderr, "Failed to get CFRunLoopStop from CoreFoundation: %s\n", errm ? errm : &nul);
    //     goto fail_libs;
    // }
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

    void *ClsNSObject = objc_getClass("NSObject");
    if (!ClsNSObject) {
        fputs("Failed to getClass NSObject\n", stderr);
        goto fail_libs;
    }
    void *ClsNSString = objc_getClass("NSString");
    if (!ClsNSString) {
        fputs("Failed to getClass NSString\n", stderr);
        goto fail_libs;
    }
    void *ClsNSNumber = objc_getClass("NSNumber");
    if (!ClsNSNumber) {
        fputs("Failed to getClass NSNumber\n", stderr);
        goto fail_libs;
    }
    void *ClsNSURL = objc_getClass("NSURL");
    if (!ClsNSURL) {
        fputs("Failed to getClass NSURL\n", stderr);
        goto fail_libs;
    }
    void *ClsNSDictionary = objc_getClass("NSDictionary");
    if (!ClsNSDictionary) {
        fputs("Failed to getClass NSDictionary\n", stderr);
        goto fail_libs;
    }
    void *ClsWKWebView = objc_getClass("WKWebView");
    if (!ClsWKWebView) {
        fputs("Failed to getClass WKWebView\n", stderr);
        goto fail_libs;
    }
    void *ClsWKContentWorld = objc_getClass("WKContentWorld");
    if (!ClsWKContentWorld) {
        fputs("Failed to getClass WKContentWorld\n", stderr);
        goto fail_libs;
    }
    void *ClsWKWebViewConfiguration = objc_getClass("WKWebViewConfiguration");
    if (!ClsWKWebViewConfiguration) {
        fputs("Failed to getClass WKWebViewConfiguration\n", stderr);
        goto fail_libs;
    }
    fputs("Loaded classes\n", stderr);
    void *selAlloc = sel_registerName("alloc");
    void *selDealloc = sel_registerName("dealloc");
    void *selInit = sel_registerName("init");
    void *selRelease = sel_registerName("release");
    void *selClass = sel_registerName("class");
    void *selIsKindOfClass = sel_registerName("isKindOfClass:");
    void *selSetVal4K = sel_registerName("setValue:forKey:");
    void *selUTF8Str = sel_registerName("UTF8String");
    void *selInitWithUTF8 = sel_registerName("initWithUTF8String:");
    fputs("Initialised selectors\n", stderr);

    void *ClsCFC_NaviDelegate = objc_allocateClassPair(ClsNSObject, "CForeignClass_NaviDelegate", 0);
    if (!ClsCFC_NaviDelegate) {
        fputs("Failed to allocate class CForeignClass_NaviDelegate, did you register twice?\n", stderr);
        goto fail_libs;
    }
    if (!class_addIvar(
            ClsCFC_NaviDelegate, "pmCbMap", sizeof(CallbackMap *), ALIGNOF_STRUCTURE(CallbackMap *),
            "^v"/*void */)) {
        fputs("Failed to add instance variable pmCbMap to CForeignClass_NaviDelegate, was it added before?\n", stderr);
        goto fail_libs;
    }
    class_addMethod(ClsCFC_NaviDelegate, selInit, &CFC_NaviDelegate_init, "@@:"/* id (*)(id, SEL)*/);
    class_addMethod(ClsCFC_NaviDelegate, selDealloc, &CFC_NaviDelegate_dealloc, "v@:"/*void (*)(id, SEL)*/);
    class_addMethod(
        ClsCFC_NaviDelegate,
        sel_registerName("webView:didFinishNavigation:"),
        &CFC_NaviDelegate_webView0_didFinishNavigation1,
        "v@:@@"/*void (*)(id, SEL, WKWebView *, WKNavigation *)*/);
    class_addProtocol(ClsCFC_NaviDelegate, objc_getProtocol("WKNavigationDelegate"));
    objc_registerClassPair(ClsCFC_NaviDelegate);
    fputs("Registered CFC_NaviDelegate\n", stderr);
    void *pNaviDg = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsCFC_NaviDelegate, selAlloc);
    pNaviDg = ((FnProtovp_objc_msgSend)objc_msgSend)(pNaviDg, selInit);
    CallbackMap *rpmCbMap = NULL;
    object_getInstanceVariable(pNaviDg, "pmCbMap", (void **)&rpmCbMap);
    if (!rpmCbMap) {
        fprintf(stderr, "Failed to initialise CFC_NaviDelegate! Unexpected NULL pmCbMap\n");
        ((FnProtov_objc_msgSend)objc_msgSend)(pNaviDg, selRelease);
        goto fail_libs;
    }

    void *pStr = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
        ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
        selInitWithUTF8, (void *)"Hello, World!");
    fprintf(stderr, "Initialised NSString\n");
    NSLog(pStr);
    fprintf(stderr, "Logged NSString\n");
    ((FnProtov_objc_msgSend)objc_msgSend)(pStr, selRelease); pStr = NULL;
    fprintf(stderr, "Released NSString\n");

    void *pCfg = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKWebViewConfiguration, selAlloc);
    pCfg = ((FnProtovp_objc_msgSend)objc_msgSend)(pCfg, selInit);
    void *pPref = ((FnProtovp_objc_msgSend)objc_msgSend)(pCfg, sel_registerName("preferences"));
    ((FnProtov_i8_objc_msgSend)objc_msgSend)(pPref, sel_registerName("setJavaScriptCanOpenWindowsAutomatically:"), kbTrue);

    void *psSetKey = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
        ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
        selInitWithUTF8, (void *)"allowFileAccessFromFileURLs");
    ((FnProtov_2vp_objc_msgSend)objc_msgSend)(pPref, selSetVal4K, kCFBooleanTrue, psSetKey);
    ((FnProtov_objc_msgSend)objc_msgSend)(psSetKey, selRelease); psSetKey = NULL;

    pPref = NULL;

    psSetKey = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
        ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
        selInitWithUTF8, (void *)"allowUniversalAccessFromFileURLs");
    ((FnProtov_2vp_objc_msgSend)objc_msgSend)(pCfg, selSetVal4K, kCFBooleanTrue, psSetKey);
    ((FnProtov_objc_msgSend)objc_msgSend)(psSetKey, selRelease); psSetKey = NULL;

    void *pWebview = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKWebView, selAlloc);
    pWebview = ((FnProtovp_CGRect_vp_objc_msgSend)objc_msgSend)(pWebview, sel_registerName("initWithFrame:configuration:"), Proto_CGRectZero, pCfg);
    ((FnProtov_objc_msgSend)objc_msgSend)(pCfg, selRelease); pCfg = NULL;
    fprintf(stderr, "Initialised WKWebView\n");

    ((FnProtov_vp_objc_msgSend)objc_msgSend)(pWebview, sel_registerName("setNavigationDelegate:"), pNaviDg);

    {
        void *psHTMLString = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
            ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
            selInitWithUTF8, (void *)szHTMLString);
        void *psBaseURL = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
            ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
            selInitWithUTF8, (void *)szBaseURL);
        void *pnurlBaseURL = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
            ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSURL, selAlloc),
            sel_registerName("initWithString:"), psBaseURL);
        if (!pnurlBaseURL)
            fputs("pnurlBaseURL unexpected nil", stderr);
        if (!psHTMLString)
            fputs("psHTMLString unexpected nil", stderr);

        void *rpNavi = ((FnProtovp_2vp_objc_msgSend)objc_msgSend)(
            pWebview, sel_registerName("loadHTMLString:baseURL:"),
            psHTMLString, pnurlBaseURL);

        cbmap_add(rpmCbMap, rpNavi, onNavigationFinished, NULL);

        ((FnProtov_objc_msgSend)objc_msgSend)(pnurlBaseURL, selRelease); pnurlBaseURL = NULL;
        ((FnProtov_objc_msgSend)objc_msgSend)(psBaseURL, selRelease); psBaseURL = NULL;
        ((FnProtov_objc_msgSend)objc_msgSend)(psHTMLString, selRelease); psHTMLString = NULL;

        fprintf(stderr, "Set up WKWebView, Navigating to: %s\n", szBaseURL);
        CFRunLoopRun();
        fputs("Navigation finished\n", stderr);
    }

    void *psScript = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
        ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
        selInitWithUTF8, (void *)szScript);

    void *pdJsArguments = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSDictionary, selAlloc);
    pdJsArguments = ((FnProtovp_objc_msgSend)objc_msgSend)(pdJsArguments, selInit);

    void *rpPageWorld = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKContentWorld, sel_registerName("pageWorld"));
    struct OnCallAsyncJSCompleteUserData userData = { CFRunLoopStop, CFRunLoopGetMain, objc_msgSend, sel_registerName };
    struct Prototype_FnPtrWrapperBlock block;
    struct {
        unsigned long int reserved;
        unsigned long int size;
        const char *signature;
    } desc = { 0, sizeof(struct Prototype_FnPtrWrapperBlock), /*"v24@?0@8@\"NSError\"16"*/"v@?@@" };
    block.isa = p_NSConcreteStackBlock;
    make_wrapper(&block, &onCallAsyncJSComplete, &userData);
    block.desc = (struct Prototype_BlockDescBase *)&desc;
    block.flags |= (1 << 30);
    ((FnProtov_5vp_objc_msgSend)objc_msgSend)(
        pWebview,
        sel_registerName("callAsyncJavaScript:arguments:inFrame:inContentWorld:completionHandler:"),
        psScript,
        pdJsArguments, /*inFrame=*/NULL, rpPageWorld,
        /*completionHandler: (void (^)(id result, NSError *error))*/
        &block);
    fprintf(stderr, "Submitted asynchronous JS execution\n");

    fprintf(stderr, "Waiting for JS to stop\n");
    CFRunLoopRun();
    fprintf(stderr, "JS stopped\n");

    ((FnProtov_objc_msgSend)objc_msgSend)(pdJsArguments, selRelease); pdJsArguments = NULL;

    ((FnProtov_objc_msgSend)objc_msgSend)(psScript, selRelease); psScript = NULL;

    ((FnProtov_objc_msgSend)objc_msgSend)(pWebview, selRelease); pWebview = NULL;
    ((FnProtov_objc_msgSend)objc_msgSend)(pNaviDg, selRelease); pNaviDg = NULL; rpmCbMap = NULL;

    if (!userData.idResult) {
        fputs("Javascript returned nil\n", stderr);
    } else if (((FnProtoi8_vp_objc_msgSend)objc_msgSend)(userData.idResult, selIsKindOfClass, ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selClass))) {
        const char *szRet = ((FnProtovp_objc_msgSend)objc_msgSend)(userData.idResult, selUTF8Str);
        fprintf(stderr, "Javascript returned string: %s\n", szRet);
    }
    else if (((FnProtoi8_vp_objc_msgSend)objc_msgSend)(userData.idResult, selIsKindOfClass, ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSNumber, selClass))) {
        void *rpsStrVal = ((FnProtovp_objc_msgSend)objc_msgSend)(userData.idResult, sel_registerName("stringValue"));
        const char *szRet = ((FnProtovp_objc_msgSend)objc_msgSend)(rpsStrVal, selUTF8Str);
        fprintf(stderr, "Javascript returned Number: %s\n", szRet);
    } else {
        fputs("Javascript returned unknown object\n", stderr);
    }

    ((FnProtov_objc_msgSend)objc_msgSend)(userData.idResult, selRelease); userData.idResult = NULL;
    fputs("Freed all\n", stderr);

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
