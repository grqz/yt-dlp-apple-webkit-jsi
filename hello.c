#include "config.h"
#include "cbmap.h"
#include "fn_to_block.h"

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

#include <dlfcn.h>

#define SYSFWK(fwk) "/System/Library/Frameworks/" #fwk ".framework/" #fwk
#define ALIGNOF_STRUCTURE(st) offsetof(struct { char c; st s; }, s)
#define TRY_DLOPEN(hLib, libPath, mode, failHint, failLabel) \
    void *hLib; \
    do { \
        hLib = dlopen(libPath, mode); \
        if (!hLib) { \
            const char *_try_dlopen_internal_errm = dlerror(); \
            fprintf(stderr, \
                "Failed to load \"" #hLib "\": %s" \
                failHint "\n", _try_dlopen_internal_errm \
                    ? _try_dlopen_internal_errm : ""); \
            goto failLabel; \
        } \
    } while (0)
#define TRY_DLCLOSE(hLib) \
    do { \
        if (dlclose(hLib)) { \
            const char *_try_dlclose_internal_errm = dlerror(); \
            fprintf(stderr, "Failed to dlclose " \
                "\"" #hLib "\": %s\n", \
                _try_dlclose_internal_errm \
                    ? _try_dlclose_internal_errm : ""); \
        } \
    } while (0)

#define FNPROTO_DECLARE(fn) \
    FnProto_##fn fn
#define LOADSYMBOL_BASE( \
    hLib, symType, sym, assignto, libName, onFailure) \
    do { \
        symType _loadsymbol_internal_symbol; \
        *(void **)(&_loadsymbol_internal_symbol) = dlsym(hLib, sym); \
        assignto = _loadsymbol_internal_symbol; \
        if (!_loadsymbol_internal_symbol) { \
            const char *_loadsymbol_internal_errm = dlerror(); \
            fprintf(stderr, \
                "Failed to get \"" sym "\" " \
                "from \"" libName "\": %s\n", \
                _loadsymbol_internal_errm \
                    ? _loadsymbol_internal_errm : ""); \
            onFailure; \
        } \
    } while (0)
#define LOADSYMBOL_OUTVAR(hLib, symType, sym, outvar, failLabel) \
    LOADSYMBOL_BASE(hLib, symType, #sym, outvar, #hLib, goto failLabel)
#define LOADSYMBOL_SIMPLE(hLib, symType, sym, failLabel) \
    LOADSYMBOL_BASE(hLib, symType, #sym, sym, #hLib, goto failLabel)
#define LOADSYMBOL_SIMPLE_INITG(hLib, symType, sym, failLabel) \
    LOADSYMBOL_BASE(hLib, symType, #sym, sym = initg_##sym, #hLib, goto failLabel)

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
};
static struct Prototype_CGRect const Proto_CGRectZero = { {0.00, 0.00}, {0.00, 0.00} };

struct Prototype_objc_super {
    void *receiver, *super_class;
};

typedef void (*Prototype_IMP)(void);

typedef void *(*FnProto_objc_allocateClassPair)(void *superclass, const char *name, size_t extraBytes);
typedef void (*FnProto_objc_registerClassPair)(void *cls);

typedef void *(*FnProto_objc_getClass)(const char *name);
static FnProto_objc_getClass initg_objc_getClass = NULL;
#define INITG_GETCLASS_SETUP(varNamePfx, className, classType, failLabel) \
    classType varNamePfx##className; \
    do { \
        varNamePfx##className = (classType)objc_getClass(#className); \
        if (!varNamePfx##className) { \
            fputs("Failed to getClass \"" #className "\"\n", stderr); \
            goto failLabel; \
        } \
    } while (0)

typedef void *(*FnProto_objc_getProtocol)(const char *name);

typedef void (*FnProto_objc_msgSend)(void);
static FnProto_objc_msgSend initg_objc_msgSend = NULL;
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

typedef void (*FnProto_objc_msgSendSuper)(void);
static FnProto_objc_msgSendSuper initg_objc_msgSendSuper = NULL;
typedef void *(*FnProtovp_objc_msgSendSuper)(void *super, void *op);
typedef void (*FnProtov_objc_msgSendSuper)(void *super, void *op);

typedef void *(*FnProto_object_setInstanceVariable)(void *obj, const char *name, void *value);
static FnProto_object_setInstanceVariable initg_object_setInstanceVariable = NULL;
typedef void *(*FnProto_object_getInstanceVariable)(void *obj, const char *name, void **outValue);
static FnProto_object_getInstanceVariable initg_object_getInstanceVariable = NULL;
typedef void *(*FnProto_object_getClass)(void *obj);
static FnProto_object_getClass initg_object_getClass = NULL;

typedef signed char (*FnProto_class_addProtocol)(void *cls, void *protocol);
typedef signed char (*FnProto_class_addMethod)(void *cls, void *name, Prototype_IMP imp, const char *types);
typedef signed char (*FnProto_class_addIvar)(void *cls, const char *name, size_t size, uint8_t alignment, const char *types);

typedef void *(*FnProto_sel_registerName)(const char * str);
static FnProto_sel_registerName initg_sel_registerName = NULL;

typedef void (*FnProto_CFRunLoopRun)(void);

typedef void (*FnProto_CFRunLoopStop)(void *rl);
static FnProto_CFRunLoopStop initg_CFRunLoopStop = NULL;

typedef void *(*FnProto_CFRunLoopGetMain)(void);
static FnProto_CFRunLoopGetMain initg_CFRunLoopGetMain = NULL;

static common_inline
void *CFC_NaviDelegate_init(void *self, void *op) {
    struct Prototype_objc_super super;
    fputs("CFC_NaviDelegate::init\n", stderr);
    super.receiver = self;
    super.super_class = ((FnProtovp_objc_msgSend)initg_objc_msgSend)(
        initg_object_getClass(self), initg_sel_registerName("superclass"));
    self = ((FnProtovp_objc_msgSendSuper)initg_objc_msgSendSuper)(&super, op);
    if (self)
        initg_object_setInstanceVariable(self, "pmCbMap", cbmap_new());
    return self;
}
static common_inline
void CFC_NaviDelegate_dealloc(void *self, void *op) {
    struct Prototype_objc_super super;
    void *pmCbMap = NULL;
    fputs("CFC_NaviDelegate::dealloc\n", stderr);
    super.receiver = self;
    super.super_class = ((FnProtovp_objc_msgSend)initg_objc_msgSend)(
        initg_object_getClass(self), initg_sel_registerName("superclass"));
    initg_object_getInstanceVariable(self, "pmCbMap", &pmCbMap);
    if (pmCbMap)
        cbmap_free((CallbackMap *)pmCbMap);
    ((FnProtov_objc_msgSendSuper)initg_objc_msgSendSuper)(&super, op);
}
static common_inline
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

static common_inline
void onNavigationFinished(void *ctx, void *userData) {
    fprintf(stderr, "Finished navigation: %p, userData: %p\n", ctx, userData);
    initg_CFRunLoopStop(initg_CFRunLoopGetMain());
}

typedef void *OnCallAsyncJSCompleteUserData;
static common_inline
void onCallAsyncJSComplete(struct Prototype_FnPtrWrapperBlock *self, void *idResult, void *nserrError) {
    OnCallAsyncJSCompleteUserData *pUserData = self->userData;
    fprintf(stderr, "JS Complete! old user data: %p, idResult: %p; nserrError: %p\n", *pUserData, idResult, nserrError);
    if (nserrError) {
        long code = ((long(*)(void *self, void *op))initg_objc_msgSend)(nserrError, initg_sel_registerName("code"));
        void *rpsDomain = ((FnProtovp_objc_msgSend)initg_objc_msgSend)(nserrError, initg_sel_registerName("domain"));
        const char *szDomain = ((FnProtovp_objc_msgSend)initg_objc_msgSend)(rpsDomain, initg_sel_registerName("UTF8String"));
        void *rpdUserInfo = ((FnProtovp_objc_msgSend)initg_objc_msgSend)(nserrError, initg_sel_registerName("userInfo"));
        void *rpsUserInfo = ((FnProtovp_objc_msgSend)initg_objc_msgSend)(rpdUserInfo, initg_sel_registerName("description"));
        const char *szUserInfo = ((FnProtovp_objc_msgSend)initg_objc_msgSend)(rpsUserInfo, initg_sel_registerName("UTF8String"));
        fprintf(stderr, "Error encountered: code %lu, domain %s, userinfo %s\n", code, szDomain, szUserInfo);
    }
    *pUserData = idResult
        ? ((FnProtovp_objc_msgSend)initg_objc_msgSend)(idResult, initg_sel_registerName("copy"))
        : NULL;
    initg_CFRunLoopStop(initg_CFRunLoopGetMain());
}

int main(void) {
    int ret = 1;
    TRY_DLOPEN(objc, "/usr/lib/libobjc.A.dylib", RTLD_NOW, "Are you on APPLE?", fail_ret);
    TRY_DLOPEN(libSystem, "/usr/lib/libSystem.B.dylib", RTLD_LAZY, "Are you on APPLE?", fail_objc);
    /* Load Frameworks */
    TRY_DLOPEN(foundation, SYSFWK(Foundation), RTLD_LAZY, "", fail_libSystem);
    TRY_DLOPEN(webkit, SYSFWK(WebKit), RTLD_LAZY, "", fail_foundation);
    TRY_DLOPEN(cf, SYSFWK(CoreFoundation), RTLD_LAZY, "", fail_webkit);
    fprintf(stderr, "All libraries and frameworks loaded\n");

    LOADFUNC_SETUP(objc, objc_allocateClassPair, fail_libs);
    LOADFUNC_SETUP(objc, objc_registerClassPair, fail_libs);
    LOADFUNC_SETUP_INITG(objc, objc_getClass, fail_libs);
    LOADFUNC_SETUP_INITG(objc, objc_msgSend, fail_libs);
    LOADFUNC_SETUP_INITG(objc, objc_msgSendSuper, fail_libs);
    LOADFUNC_SETUP(objc, objc_getProtocol, fail_libs);
    LOADFUNC_SETUP_INITG(objc, object_getInstanceVariable, fail_libs);
    LOADFUNC_SETUP_INITG(objc, object_setInstanceVariable, fail_libs);
    LOADFUNC_SETUP_INITG(objc, object_getClass, fail_libs);

    LOADFUNC_SETUP(objc, class_addMethod, fail_libs);
    LOADFUNC_SETUP(objc, class_addIvar, fail_libs);
    LOADFUNC_SETUP(objc, class_addProtocol, fail_libs);

    LOADFUNC_SETUP_INITG(objc, sel_registerName, fail_libs);

    void *p_NSConcreteStackBlock;
    LOADSYMBOL_OUTVAR(libSystem, void *, _NSConcreteStackBlock, p_NSConcreteStackBlock, fail_libs);

    LOADFUNC_SETUP(cf, CFRunLoopRun, fail_libs);
    LOADFUNC_SETUP_INITG(cf, CFRunLoopGetMain, fail_libs);
    LOADFUNC_SETUP_INITG(cf, CFRunLoopStop, fail_libs);
    void **pkCFBooleanTrue;
    LOADSYMBOL_OUTVAR(cf, void **, kCFBooleanTrue, pkCFBooleanTrue, fail_libs);
    void *kCFBooleanTrue = *pkCFBooleanTrue;

    INITG_GETCLASS_SETUP(Cls, NSObject, void *, fail_libs);
    INITG_GETCLASS_SETUP(Cls, NSString, void *, fail_libs);
    INITG_GETCLASS_SETUP(Cls, NSNumber, void *, fail_libs);
    INITG_GETCLASS_SETUP(Cls, NSURL, void *, fail_libs);
    INITG_GETCLASS_SETUP(Cls, NSDictionary, void *, fail_libs);

    INITG_GETCLASS_SETUP(Cls, WKWebView, void *, fail_libs);
    INITG_GETCLASS_SETUP(Cls, WKContentWorld, void *, fail_libs);
    INITG_GETCLASS_SETUP(Cls, WKWebViewConfiguration, void *, fail_libs);
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

    void *ClsCFC_NaviDelegate;
    {
        ClsCFC_NaviDelegate = objc_allocateClassPair(ClsNSObject, "CForeignClass_NaviDelegate", 0);
        if (!ClsCFC_NaviDelegate) {
            fputs("Failed to allocate class CForeignClass_NaviDelegate, did you register twice?\n", stderr);
            goto fail_libs;
        }
        struct _getalignof_CbMapPtr { char c; CallbackMap *p; };
        if (!class_addIvar(
                ClsCFC_NaviDelegate, "pmCbMap", sizeof(CallbackMap *), offsetof(struct _getalignof_CbMapPtr, p),
                "^v"/*void */)) {
            fputs("Failed to add instance variable pmCbMap to CForeignClass_NaviDelegate, was it added before?\n", stderr);
            goto fail_libs;
        }
        class_addMethod(ClsCFC_NaviDelegate, selInit, (Prototype_IMP)&CFC_NaviDelegate_init, "@@:"/* id (*)(id, SEL)*/);
        class_addMethod(ClsCFC_NaviDelegate, selDealloc, (Prototype_IMP)&CFC_NaviDelegate_dealloc, "v@:"/*void (*)(id, SEL)*/);
        class_addMethod(
            ClsCFC_NaviDelegate,
            sel_registerName("webView:didFinishNavigation:"),
            (Prototype_IMP)&CFC_NaviDelegate_webView0_didFinishNavigation1,
            "v@:@@"/*void (*)(id, SEL, WKWebView *, WKNavigation *)*/);
        class_addProtocol(ClsCFC_NaviDelegate, objc_getProtocol("WKNavigationDelegate"));
        objc_registerClassPair(ClsCFC_NaviDelegate);
        fputs("Registered CFC_NaviDelegate\n", stderr);
    }
    void *pNaviDg = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsCFC_NaviDelegate, selAlloc);
    pNaviDg = ((FnProtovp_objc_msgSend)objc_msgSend)(pNaviDg, selInit);
    CallbackMap *rpmCbMap = NULL;
    object_getInstanceVariable(pNaviDg, "pmCbMap", (void **)&rpmCbMap);
    if (!rpmCbMap) {
        fprintf(stderr, "Failed to initialise CFC_NaviDelegate! Unexpected NULL pmCbMap\n");
        ((FnProtov_objc_msgSend)objc_msgSend)(pNaviDg, selRelease);
        goto fail_libs;
    }

    void *pWebview;
    {
        void *pCfg = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKWebViewConfiguration, selAlloc);
        pCfg = ((FnProtovp_objc_msgSend)objc_msgSend)(pCfg, selInit);
        void *rpPref = ((FnProtovp_objc_msgSend)objc_msgSend)(pCfg, sel_registerName("preferences"));
        ((FnProtov_i8_objc_msgSend)objc_msgSend)(rpPref, sel_registerName("setJavaScriptCanOpenWindowsAutomatically:"), 1);

        void *psSetKey = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
            ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
            selInitWithUTF8, (void *)"allowFileAccessFromFileURLs");
        ((FnProtov_2vp_objc_msgSend)objc_msgSend)(rpPref, selSetVal4K, kCFBooleanTrue, psSetKey);
        ((FnProtov_objc_msgSend)objc_msgSend)(psSetKey, selRelease);

        psSetKey = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
            ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
            selInitWithUTF8, (void *)"allowUniversalAccessFromFileURLs");
        ((FnProtov_2vp_objc_msgSend)objc_msgSend)(pCfg, selSetVal4K, kCFBooleanTrue, psSetKey);
        ((FnProtov_objc_msgSend)objc_msgSend)(psSetKey, selRelease);

        pWebview = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKWebView, selAlloc);
        pWebview = ((FnProtovp_CGRect_vp_objc_msgSend)objc_msgSend)(pWebview, sel_registerName("initWithFrame:configuration:"), Proto_CGRectZero, pCfg);
        ((FnProtov_objc_msgSend)objc_msgSend)(pCfg, selRelease);

        fputs("Initialised WKWebView\n", stderr);
    }

    {
        ((FnProtov_vp_objc_msgSend)objc_msgSend)(pWebview, sel_registerName("setNavigationDelegate:"), pNaviDg);

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

    OnCallAsyncJSCompleteUserData userData;
    {
        void *psScript = ((FnProtovp_vp_objc_msgSend)objc_msgSend)(
            ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selAlloc),
            selInitWithUTF8, (void *)szScript);

        void *pdJsArguments = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSDictionary, selAlloc);
        pdJsArguments = ((FnProtovp_objc_msgSend)objc_msgSend)(pdJsArguments, selInit);

        void *rpPageWorld = ((FnProtovp_objc_msgSend)objc_msgSend)(ClsWKContentWorld, sel_registerName("pageWorld"));
        struct Prototype_FnPtrWrapperBlock block;
        struct Prototype_BlockDescSign desc = { 0, sizeof(struct Prototype_FnPtrWrapperBlock), "v@?@@"/*void (*)(Block self, id, id)*/ };
        block.isa = p_NSConcreteStackBlock;
        make_wrapper(&block, (Prototype_IMP)&onCallAsyncJSComplete, &userData);
        block.desc = (struct Prototype_BlockDescBase *)&desc;
        block.flags |= (1 << 30);
        ((FnProtov_5vp_objc_msgSend)objc_msgSend)(
            pWebview,
            sel_registerName("callAsyncJavaScript:arguments:inFrame:inContentWorld:completionHandler:"),
            psScript,
            pdJsArguments, /*inFrame:*/NULL, rpPageWorld,
            /*completionHandler: (void (^)(id result, NSError *error))*/&block);
        fprintf(stderr, "Submitted asynchronous JS execution, waiting for JS to stop\n");
        CFRunLoopRun();
        fprintf(stderr, "JS stopped\n");

        ((FnProtov_objc_msgSend)objc_msgSend)(pdJsArguments, selRelease);
        ((FnProtov_objc_msgSend)objc_msgSend)(psScript, selRelease);
    }

    ((FnProtov_objc_msgSend)objc_msgSend)(pWebview, selRelease); pWebview = NULL;
    ((FnProtov_objc_msgSend)objc_msgSend)(pNaviDg, selRelease); pNaviDg = NULL; rpmCbMap = NULL;

    if (!userData) {
        fputs("Javascript returned nil\n", stderr);
    } else if (((FnProtoi8_vp_objc_msgSend)objc_msgSend)(userData, selIsKindOfClass, ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSString, selClass))) {
        const char *szRet = ((FnProtovp_objc_msgSend)objc_msgSend)(userData, selUTF8Str);
        fprintf(stderr, "Javascript returned string: %s\n", szRet);
    }
    else if (((FnProtoi8_vp_objc_msgSend)objc_msgSend)(userData, selIsKindOfClass, ((FnProtovp_objc_msgSend)objc_msgSend)(ClsNSNumber, selClass))) {
        void *rpsStrVal = ((FnProtovp_objc_msgSend)objc_msgSend)(userData, sel_registerName("stringValue"));
        const char *szRet = ((FnProtovp_objc_msgSend)objc_msgSend)(rpsStrVal, selUTF8Str);
        fprintf(stderr, "Javascript returned Number: %s\n", szRet);
    } else {
        fputs("Javascript returned an unknown object\n", stderr);
    }

    ((FnProtov_objc_msgSend)objc_msgSend)(userData, selRelease); userData = NULL;
    fputs("Freed all\n", stderr);

    ret = 0;
fail_libs:;
/*fail_cf:;*/ TRY_DLCLOSE(cf);
fail_webkit:; TRY_DLCLOSE(webkit);
fail_foundation:; TRY_DLCLOSE(foundation);
fail_libSystem:; TRY_DLCLOSE(libSystem);
fail_objc:; TRY_DLCLOSE(objc);
fail_ret:;
    return ret;
}
