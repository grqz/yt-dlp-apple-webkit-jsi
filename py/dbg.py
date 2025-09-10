from ctypes import c_bool, c_void_p
from .pyneapple_objc import PyNeApple, cfn_at, debug_log
from .run import CGRect

with PyNeApple() as pa:
    pa.load_framework_from_path('Foundation')
    cf = pa.load_framework_from_path('CoreFoundation')
    pa.load_framework_from_path('WebKit')

    NSThread = pa.safe_objc_getClass(b'NSThread')
    WKWebView = pa.safe_objc_getClass(b'WKWebView')

    i_lcurrent = cfn_at(cf(b'CFRunLoopGetCurrent').value, c_void_p)()
    i_lmain = cfn_at(cf(b'CFRunLoopGetMain').value, c_void_p)()

    assert i_lcurrent == i_lmain, 'current loop not main'

    assert pa.send_message(NSThread, b'isMainThread', restype=c_bool), 'not on main thread'

    therect = CGRect()
    p = pa.safe_new_object(WKWebView, b'initWithFrame:', therect, argtypes=(CGRect, ))
    pa.release_on_exit(p)
    debug_log(f'{p=}')

debug_log('survived')

# RELEASE_ASSERT(isMainRunLoop());
# this assertion failed
# <https://github.com/WebKit/WebKit/blob/1a1fa431f8a684f9b88c05fef1ea9b638fb5f04b/Source/WebKit/UIProcess/Cocoa/WebProcessPoolCocoa.mm#L951>
