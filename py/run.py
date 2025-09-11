import sys

from asyncio import Future as co_Fut
from contextlib import ExitStack
from ctypes import (
    POINTER,
    Structure,
    byref,
    c_byte, c_char_p,
    c_double,
    c_long, c_void_p,
)
from typing import Callable, Coroutine, Optional, TypeVar, Union, cast as py_typecast, overload

from .pyneapple_objc import (
    NotNull_VoidP,
    ObjCBlock,
    PyNeApple,
    as_fnptr,
    cfn_at,
    debug_log,
    write_err,
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


VOIDP_ARGTYPE = Optional[int]
T = TypeVar('T')
U = TypeVar('U')


@overload
def str_from_nsstring(pa: PyNeApple, nsstr: NotNull_VoidP) -> str: ...
@overload
def str_from_nsstring(pa: PyNeApple, nsstr: c_void_p, *, default: T = None) -> Union[str, T]: ...


def str_from_nsstring(pa: PyNeApple, nsstr: Union[c_void_p, NotNull_VoidP], *, default: T = None) -> Union[str, T]:
    return py_typecast(bytes, pa.send_message(
        py_typecast(c_void_p, nsstr), b'UTF8String', restype=c_char_p)).decode() if nsstr.value else default


def main():
    navidg_cbdct: 'PFC_NaviDelegate.CBDICT_TYPE' = {}
    try:
        with PyNeApple() as pa:
            class PFC_NaviDelegate:
                CBDICT_TYPE = dict[int, Callable[[], None]]
                SIGNATURE_WEBVIEW_DIDFINISHNAVIGATION = b'v@:@@'

                @staticmethod
                def webView0_didFinishNavigation1(this: VOIDP_ARGTYPE, sel: VOIDP_ARGTYPE, rp_webview: VOIDP_ARGTYPE, rp_navi: VOIDP_ARGTYPE) -> None:
                    debug_log(f'[(PyForeignClass_NavigationDelegate){this} webView: {rp_webview} didFinishNavigation: {rp_navi}]')
                    if cb := navidg_cbdct.get(rp_navi or 0):
                        cb()

            pa.load_framework_from_path('Foundation')
            cf = pa.load_framework_from_path('CoreFoundation')
            pa.load_framework_from_path('WebKit')
            debug_log('Loaded libs')
            NSDictionary = pa.safe_objc_getClass(b'NSDictionary')
            NSString = pa.safe_objc_getClass(b'NSString')
            NSNumber = pa.safe_objc_getClass(b'NSNumber')
            NSObject = pa.safe_objc_getClass(b'NSObject')
            NSURL = pa.safe_objc_getClass(b'NSURL')
            WKContentWorld = pa.safe_objc_getClass(b'WKContentWorld')
            WKWebView = pa.safe_objc_getClass(b'WKWebView')
            WKWebViewConfiguration = c_void_p(pa.objc_getClass(b'WKWebViewConfiguration'))

            CFRunLoopStop = cfn_at(cf(b'CFRunLoopStop').value, None, c_void_p)
            CFRunLoopRun = cfn_at(cf(b'CFRunLoopRun').value, None)
            CFRunLoopGetMain = cfn_at(cf(b'CFRunLoopGetMain').value, c_void_p)
            kCFRunLoopDefaultMode = c_void_p.from_address(cf(b'kCFRunLoopDefaultMode').value)
            CFRunLoopPerformBlock = cfn_at(cf(b'CFRunLoopPerformBlock').value, None, c_void_p, c_void_p, POINTER(ObjCBlock))
            CFRunLoopWakeUp = cfn_at(cf(b'CFRunLoopWakeUp').value, None, c_void_p)
            currloop = c_void_p(cfn_at(cf(b'CFRunLoopGetCurrent').value, c_void_p)())
            mainloop = c_void_p(CFRunLoopGetMain())
            assert currloop.value == mainloop.value
            kcf_true = c_void_p.from_address(cf(b'kCFBooleanTrue').value)

            def schedule_on(loop: c_void_p, pycb: Callable[[], None], *, mode: c_void_p = kCFRunLoopDefaultMode):
                CFRunLoopPerformBlock(loop, mode, pa.make_block(pycb))
                CFRunLoopWakeUp(loop)

            def runcoro_on_current(coro: Coroutine[None, None, T], *, default: U = None) -> Union[T, U]:
                # Default is returned when the coroutine wrongly calls CFRunLoopStop(currloop) or its equivalent
                ret: Union[T, U] = default

                def _coro_step():
                    nonlocal ret
                    try:
                        coro.send(None)
                    except StopIteration as e:
                        CFRunLoopStop(currloop)
                        ret = e.value
                schedule_on(currloop, _coro_step)
                CFRunLoopRun()
                return ret

            Py_NaviDg = pa.objc_allocateClassPair(NSObject, b'PyForeignClass_NavigationDelegate', 0)
            if not Py_NaviDg:
                raise RuntimeError('Failed to allocate class PyForeignClass_NavigationDelegate, did you register twice?')
            pa.class_addMethod(
                Py_NaviDg, pa.sel_registerName(b'webView:didFinishNavigation:'),
                as_fnptr(PFC_NaviDelegate.webView0_didFinishNavigation1, None, c_void_p, c_void_p, c_void_p, c_void_p),
                PFC_NaviDelegate.SIGNATURE_WEBVIEW_DIDFINISHNAVIGATION)
            pa.class_addProtocol(Py_NaviDg, pa.objc_getProtocol(b'WKNavigationDelegate'))
            pa.objc_registerClassPair(Py_NaviDg)
            debug_log('Registered PyForeignClass_NavigationDelegate')

            jsresult_id = c_void_p()
            jsresult_err = c_void_p()

            async def real_main():
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

                    p_webview = pa.safe_new_object(
                        WKWebView, b'initWithFrame:configuration:',
                        CGRect(), p_cfg,
                        argtypes=(CGRect, c_void_p))
                    pa.release_on_exit(p_webview)
                    debug_log('webview init')

                p_navidg = pa.safe_new_object(Py_NaviDg)
                pa.release_on_exit(p_navidg)
                pa.send_message(
                    p_webview, b'setNavigationDelegate:',
                    p_navidg, argtypes=(c_void_p, ))
                debug_log('webview set navidg')

                fut_navidone: co_Fut[None] = co_Fut()
                with ExitStack() as exsk:
                    ps_html = pa.safe_new_object(
                        NSString, b'initWithUTF8String:', HTML,
                        argtypes=(c_char_p, ))
                    exsk.callback(pa.send_message, ps_html, b'release')
                    ps_base_url = pa.safe_new_object(
                        NSString, b'initWithUTF8String:', HOST,
                        argtypes=(c_char_p, ))
                    exsk.callback(pa.send_message, ps_base_url, b'release')
                    purl_base = pa.safe_new_object(
                        NSURL, b'initWithString:', ps_base_url,
                        argtypes=(c_void_p, ))
                    exsk.callback(pa.send_message, purl_base, b'release')

                    rp_navi = py_typecast(NotNull_VoidP, c_void_p(pa.send_message(
                        p_webview, b'loadHTMLString:baseURL:', ps_html, purl_base,
                        restype=c_void_p, argtypes=(c_void_p, c_void_p))))
                    debug_log(f'Navigation started: {rp_navi}')

                    def cb_navi_done():
                        debug_log('navigation done, resolving future')
                        fut_navidone.set_result(None)

                    navidg_cbdct[rp_navi.value] = cb_navi_done

                    debug_log(f'loading: local HTML@{HOST.decode()}')

                    # CFRunLoopWakeUp(mainloop)
                    await fut_navidone
                debug_log('navigation done')

                fut_jsdone: co_Fut[tuple[c_void_p, c_void_p]] = co_Fut()
                with ExitStack() as exsk:
                    ps_script = pa.safe_new_object(
                        NSString, b'initWithUTF8String:', SCRIPT,
                        argtypes=(c_char_p, ))
                    exsk.callback(pa.send_message, ps_script, b'release')

                    pd_jsargs = pa.safe_new_object(NSDictionary)
                    exsk.callback(pa.send_message, pd_jsargs, b'release')

                    rp_pageworld = c_void_p(pa.send_message(
                        WKContentWorld, b'pageWorld',
                        restype=c_void_p))

                    def completion_handler(self: VOIDP_ARGTYPE, id_result: VOIDP_ARGTYPE, err: VOIDP_ARGTYPE):
                        nonlocal jsresult_id, jsresult_err
                        jsresult_id = c_void_p(pa.send_message(c_void_p(id_result or 0), b'copy', restype=c_void_p))
                        pa.release_on_exit(jsresult_id)
                        jsresult_err = c_void_p(pa.send_message(c_void_p(err or 0), b'copy', restype=c_void_p))
                        pa.release_on_exit(jsresult_err)
                        debug_log(f'JS done, resolving future; {id_result=}, {err=}')
                        fut_jsdone.set_result((jsresult_id, jsresult_err))
                        # CFRunLoopStop(mainloop)

                    chblock = pa.make_block(completion_handler, None, POINTER(ObjCBlock), c_void_p, c_void_p)

                    pa.send_message(
                        # Requires iOS 15.0+, maybe test its availability first?
                        p_webview, b'callAsyncJavaScript:arguments:inFrame:inContentWorld:completionHandler:',
                        ps_script, pd_jsargs, c_void_p(None), rp_pageworld, byref(chblock),
                        argtypes=(c_void_p, c_void_p, c_void_p, c_void_p, POINTER(ObjCBlock)))

                    # CFRunLoopWakeUp(mainloop)
                    await fut_jsdone
                # CFRunLoopStop(mainloop)

            runcoro_on_current(real_main())

            if jsresult_err:
                code = pa.send_message(jsresult_err, b'code', restype=c_long)
                s_domain = str_from_nsstring(pa, c_void_p(pa.send_message(
                    jsresult_err, b'domain', restype=c_void_p)), default='<unknown>')
                s_uinfo = str_from_nsstring(pa, c_void_p(pa.send_message(
                    c_void_p(pa.send_message(jsresult_err, b'userInfo', restype=c_void_p)),
                    b'description', restype=c_void_p)), default='<no description provided>')
                raise RuntimeError(f'JS failed: NSError@{jsresult_err.value}, {code=}, domain={s_domain}, user info={s_uinfo}')

            debug_log('JS execution completed')
            if not jsresult_id:
                s_rtype = 'nothing'
                s_result = 'nil'
            elif pa.instanceof(jsresult_id, NSString):
                s_rtype = 'string'
                s_result = str_from_nsstring(pa, py_typecast(NotNull_VoidP, jsresult_id))
            elif pa.instanceof(jsresult_id, NSNumber):
                s_rtype = 'number'
                s_result = str_from_nsstring(pa, py_typecast(NotNull_VoidP, c_void_p(
                    pa.send_message(jsresult_id, b'stringValue', restype=c_void_p))))
            else:
                s_rtype = '<unknown type>'
                s_result = '<unknown>'
            debug_log(f'JS returned {s_rtype}: {s_result}')
    except Exception:
        import traceback
        write_err(traceback.format_exc())
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
