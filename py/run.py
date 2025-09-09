import sys

from contextlib import ExitStack
from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    byref,
    c_byte, c_char_p,
    c_double, c_void_p,
)
from typing import Callable

from .pyneapple_objc import (
    NotNull_VoidP,
    ObjCBlock,
    PyNeApple,
    cfn_at,
    debug_log,
)
from .config import HOST, HTML, SCRIPT


class DoubleDouble(Structure):
    _fields_ = (
        ('x', c_double),
        ('y', c_double),
    )


class CGRect(Structure):
    _fields_ = (
        ('orig', DoubleDouble),
        ('size', DoubleDouble),
    )


def main():
    navidg_cbdct: 'PFC_NaviDelegate.CBDICT_TYPE' = {}
    try:
        with PyNeApple() as pa:
            class PFC_NaviDelegate:
                CBDICT_TYPE = dict[int, Callable[[], None]]
                SIGNATURE_WEBVIEW_DIDFINISHNAVIGATION = b'v@:@@'

                @staticmethod
                def webView0_didFinishNavigation1(this: c_void_p, sel: c_void_p, rp_webview: c_void_p, rp_navi: c_void_p) -> None:
                    if cb := navidg_cbdct.get(rp_navi.value or 0):
                        cb()

            fndatn = pa.load_framework_from_path('Foundation')
            cf = pa.load_framework_from_path('CoreFoundation')
            wk = pa.load_framework_from_path('WebKit')
            debug_log('Loaded libs')
            NSString = pa.safe_objc_getClass(b'NSString')
            NSObject = pa.safe_objc_getClass(b'NSObject')
            NSURL = pa.safe_objc_getClass(b'NSURL')
            WKWebView = pa.safe_objc_getClass(b'WKWebView')
            WKWebViewConfiguration = c_void_p(pa.objc_getClass(b'WKWebViewConfiguration'))

            lstop = cfn_at(cf(b'CFRunLoopStop').value, None, c_void_p)
            lrun = cfn_at(cf(b'CFRunLoopRun').value, None)
            mainloop = cfn_at(cf(b'CFRunLoopGetMain').value, c_void_p)()
            kcf_true = c_void_p.from_address(cf(b'kCFBooleanTrue').value)

            Py_NaviDg = pa.objc_allocateClassPair(NSObject, b'PyForeignClass_NavigationDelegate', 0)
            if not Py_NaviDg:
                raise RuntimeError('Failed to allocate class PyForeignClass_NavigationDelegate, did you register twice?')
            pa.class_addMethod(
                Py_NaviDg, pa.sel_registerName(b'webView:didFinishNavigation:'),
                CFUNCTYPE(None, c_void_p, c_void_p, c_void_p, c_void_p)(PFC_NaviDelegate.webView0_didFinishNavigation1),
                PFC_NaviDelegate.SIGNATURE_WEBVIEW_DIDFINISHNAVIGATION)
            pa.class_addProtocol(Py_NaviDg, pa.objc_getProtocol(b'WKNavigationDelegate'))
            pa.objc_registerClassPair(Py_NaviDg)
            debug_log('Registered PyForeignClass_NavigationDelegate')

            with ExitStack() as exsk:
                p_cfg = pa.safe_new_object(WKWebViewConfiguration)
                exsk.callback(pa.send_message, p_cfg, b'release')

                rp_pref = c_void_p(pa.send_message(p_cfg, b'preferences', restype=c_void_p))
                if not rp_pref.value:
                    raise RuntimeError('Failed to get preferences from WKWebViewConfiguration')
                pa.send_message(
                    rp_pref, b'setJavaScriptCanOpenWindowsAutomatically:',
                    c_byte(1), argtypes=(c_byte,))
                p_setkey0 = pa.safe_new_object(
                    NSString, b'initWithUTF8String:', b'allowFileAccessFromFileURLs',
                    argtypes=(c_char_p, ))
                exsk.callback(pa.send_message, p_setkey0, b'release')
                pa.send_message(
                    rp_pref, b'setValue:forKey:',
                    kcf_true, p_setkey0,
                    argtypes=(c_void_p, c_void_p))
                rp_pref = None

                p_setkey1 = pa.safe_new_object(
                    NSString, b'initWithUTF8String:', b'allowUniversalAccessFromFileURLs',
                    argtypes=(c_char_p, ))
                exsk.callback(pa.send_message, p_setkey1, b'release')
                pa.send_message(
                    p_cfg, b'setValue:forKey:',
                    kcf_true, p_setkey1,
                    argtypes=(c_void_p, c_void_p))

                # rp, for it's released on 'with' exit
                p_webview = pa.safe_new_object(
                    WKWebView, b'initWithFrame:configuration:',
                    CGRect(), p_cfg,
                    argtypes=(CGRect, c_void_p))
                pa.release_on_exit(p_webview)

            rp_navidg = pa.safe_new_object(Py_NaviDg)
            pa.release_on_exit(rp_navidg)
            pa.send_message(
                p_webview, b'setNavigationDelegate:',
                rp_navidg, argtypes=(c_void_p, ))

            with ExitStack() as exsk:
                ps_html = pa.safe_new_object(
                    NSString, b'initWithUTF8String:', HTML,
                    argtypes=(c_char_p, ))
                exsk.callback(pa.send_message, ps_html, b'release')
                ps_base_url = pa.safe_new_object(
                    NSString, b'initWithUTF8String:', SCRIPT,
                    argtypes=(c_char_p, ))
                exsk.callback(pa.send_message, ps_base_url, b'release')
                purl_base = pa.safe_new_object(
                    NSURL, b'initWithString:', ps_base_url,
                    argtypes=(c_void_p, ))
                exsk.callback(pa.send_message, purl_base, b'release')

                rp_navi = NotNull_VoidP(pa.send_message(
                    p_webview, b'loadHTMLString:baseURL:', ps_html, purl_base,
                    restype=c_void_p, argtypes=(c_void_p, c_void_p)) or 0)

                def cb_navi_done():
                    debug_log('Navigation done, stopping loop')
                    lstop(mainloop)

                navidg_cbdct[rp_navi.value] = cb_navi_done

            lrun()
            print('loaded')

            block = pa.make_block(
                lambda self: debug_log('stopping loop', ret=None) or lstop(mainloop),
                None, POINTER(ObjCBlock),
                signature=b'v@?')
            cfn_at(cf(b'CFRunLoopPerformBlock').value, None, c_void_p, c_void_p, POINTER(ObjCBlock))(
                mainloop, c_void_p.from_address(cf(b'kCFRunLoopDefaultMode').value),
                byref(block))
            lrun()
    except Exception:
        import traceback
        sys.stderr.write(traceback.format_exc())
        sys.stderr.flush()
    return 0


if __name__ == '__main__':
    sys.exit(main())
