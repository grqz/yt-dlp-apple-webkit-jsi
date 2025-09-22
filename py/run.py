import datetime as dt
import os
import sys

from contextlib import AsyncExitStack
from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    byref,
    c_bool,
    c_byte,
    c_char_p,
    c_double,
    c_float,
    c_int16,
    c_int32,
    c_int64,
    c_int8,
    c_long,
    c_uint64,
    c_ulong,
    c_void_p,
    string_at,
)
from dataclasses import dataclass
from pprint import pformat
from threading import Condition
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generator,
    Generic,
    Optional,
    TypeVar,
    Union,
    cast as py_typecast,
    overload
)

from .pyneapple_objc import (
    CRet,
    NotNull_VoidP,
    ObjCBlock,
    PyNeApple,
)
from .config import HOST, HTML, SCRIPT
from .logging import Logger


T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')


class CFRL_Future(Awaitable[T]):
    __slots__ = '_cbs', '_done', '_result'

    def __init__(self):
        self._cbs: list[Callable[['CFRL_Future[T]'], None]] = []
        self._done = False
        self._result: Optional[T] = None

    def result(self) -> T:
        if not self._done:
            raise RuntimeError('result method called upon a future that is not yet resolved')
        return py_typecast(T, self._result)

    def add_done_callback(self, cb: Callable[['CFRL_Future[T]'], None]) -> None:
        if not self._done:
            self._cbs.append(cb)
        else:
            cb(self)

    def set_result(self, res: T) -> None:
        if self._done:
            raise RuntimeError('double resolve')
        self._result = res
        self._done = True
        for cb in self._cbs:
            cb(self)
        self._cbs.clear()

    def done(self) -> bool:
        return self._done

    def __await__(self) -> Generator[Any, Any, T]:
        if self._done:
            return py_typecast(T, self._result)
        else:
            yield self


@dataclass
class CFRL_CoroResult(Generic[T]):
    ret: T
    rexc: Optional[BaseException] = None


class DoubleDouble(Structure):
    _fields_ = (
        ('x', c_double),
        ('y', c_double),
    )
    __slots__ = ()


class CGRect(Structure):
    _fields_ = (
        ('orig', DoubleDouble),
        ('size', DoubleDouble),
    )
    __slots__ = ()


class MacTypes:
    SInt8 = c_int8
    Py_SInt8 = int
    SInt16 = c_int16
    Py_SInt16 = int
    SInt32 = c_int32
    Py_SInt32 = int
    SInt64 = c_int64
    Py_SInt64 = int

    Float32 = c_float
    Py_Float32 = float
    Float64 = c_double
    Py_Float64 = float


NSUTF8StringEncoding = 4


@overload
def str_from_nsstring(pa: PyNeApple, nsstr: NotNull_VoidP) -> str: ...
@overload
def str_from_nsstring(pa: PyNeApple, nsstr: c_void_p, *, default: T = None) -> Union[str, T]: ...


def str_from_nsstring(pa: PyNeApple, nsstr: Union[c_void_p, NotNull_VoidP], *, default: T = None) -> Union[str, T]:
    if not nsstr.value:
        return default
    length = pa.send_message(nsstr, b'lengthOfBytesUsingEncoding:', NSUTF8StringEncoding, restype=c_ulong, argtypes=(c_ulong, ))
    if not length:
        assert pa.send_message(nsstr, b'canBeConvertedToEncoding:', NSUTF8StringEncoding, restype=c_byte, argtypes=(c_ulong, )), (
            'NSString cannot be losslessly converted to UTF-8')
        return ''
    return string_at(py_typecast(int, pa.send_message(nsstr, b'UTF8String', restype=c_void_p)), length).decode()


@dataclass
class _UnknownStructure:
    typename: str


class _NullTag:
    ...


_JSResultType = Union[
    T,  # type[None], undefined
    U,  # type[None], null
    str,
    int,
    float,
    dt.datetime,
    dict['_JSResultType', '_JSResultType'],
    list['_JSResultType'],
    V,  # type[_UnkownStructure]
]


def main():
    logger = Logger(debug=True)
    logger.debug_log(f'PID: {os.getpid()}')
    if os.getenv('CI'):
        PATH2CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'core')
        if os.path.lexists(PATH2CORE):
            logger.debug_log(f'removing exisiting file at {PATH2CORE}')
            os.remove(PATH2CORE)
        logger.debug_log(f'writing symlink to coredump (if any) to {PATH2CORE} for CI')
        os.symlink(f'/cores/core.{os.getpid()}', PATH2CORE)
    navidg_cbdct: 'PFC_WVHandler.CBDICT_TYPE' = {}
    try:
        with PyNeApple(logger=logger) as pa:
            pa.load_framework_from_path('Foundation')
            cf = pa.load_framework_from_path('CoreFoundation')
            pa.load_framework_from_path('WebKit')
            logger.debug_log('Loaded libs')
            NSArray = pa.safe_objc_getClass(b'NSArray')
            NSDate = pa.safe_objc_getClass(b'NSDate')
            NSDictionary = pa.safe_objc_getClass(b'NSDictionary')
            NSString = pa.safe_objc_getClass(b'NSString')
            NSNull = pa.safe_objc_getClass(b'NSNull')
            NSNumber = pa.safe_objc_getClass(b'NSNumber')
            NSObject = pa.safe_objc_getClass(b'NSObject')
            NSURL = pa.safe_objc_getClass(b'NSURL')
            WKContentWorld = pa.safe_objc_getClass(b'WKContentWorld')
            WKWebView = pa.safe_objc_getClass(b'WKWebView')
            WKWebViewConfiguration = pa.safe_objc_getClass(b'WKWebViewConfiguration')
            WKUserContentController = pa.safe_objc_getClass(b'WKUserContentController')

            WKNavigationDelegate = pa.objc_getProtocol(b'WKNavigationDelegate')
            WKScriptMessageHandler = pa.objc_getProtocol(b'WKScriptMessageHandler')

            CFRunLoopStop = pa.cfn_at(cf(b'CFRunLoopStop').value, None, c_void_p)
            CFRunLoopRun = pa.cfn_at(cf(b'CFRunLoopRun').value, None)
            CFRunLoopGetMain = pa.cfn_at(cf(b'CFRunLoopGetMain').value, c_void_p)
            kCFRunLoopDefaultMode = c_void_p.from_address(cf(b'kCFRunLoopDefaultMode').value)
            CFRunLoopPerformBlock = pa.cfn_at(cf(b'CFRunLoopPerformBlock').value, None, c_void_p, c_void_p, POINTER(ObjCBlock))
            CFRunLoopWakeUp = pa.cfn_at(cf(b'CFRunLoopWakeUp').value, None, c_void_p)
            currloop = c_void_p(pa.cfn_at(cf(b'CFRunLoopGetCurrent').value, c_void_p)())
            mainloop = c_void_p(CFRunLoopGetMain())
            if currloop.value != mainloop.value:
                logger.write_err('warning: running code on another loop is an experimental feature')
            CFDateGetAbsoluteTime = pa.cfn_at(cf(b'CFDateGetAbsoluteTime').value, c_double, c_void_p)
            CFNumberGetValue = pa.cfn_at(cf(b'CFNumberGetValue').value, c_bool, c_void_p, c_long, c_void_p)
            kCFNumberFloat64Type = c_long(6)
            kCFNumberLongLongType = c_long(11)
            CFDictionaryApplyFunction = pa.cfn_at(cf(b'CFDictionaryApplyFunction').value, None, c_void_p, c_void_p, c_void_p)
            CFArrayGetCount = pa.cfn_at(cf(b'CFArrayGetCount').value, c_long, c_void_p)
            CFArrayGetValueAtIndex = pa.cfn_at(cf(b'CFArrayGetValueAtIndex').value, c_void_p, c_void_p, c_long)

            type_to_largest: dict[bytes, tuple[c_long, Union[type[c_int64], type[c_uint64], type[c_double]]]] = {
                b'c': (kCFNumberLongLongType, c_int64),
                b'C': (kCFNumberLongLongType, c_uint64),
                b's': (kCFNumberLongLongType, c_int64),
                b'S': (kCFNumberLongLongType, c_uint64),
                b'i': (kCFNumberLongLongType, c_int64),
                b'I': (kCFNumberLongLongType, c_uint64),
                b'l': (kCFNumberLongLongType, c_int64),
                b'L': (kCFNumberLongLongType, c_uint64),
                b'q': (kCFNumberLongLongType, c_int64),
                b'Q': (kCFNumberLongLongType, c_uint64),
                b'f': (kCFNumberFloat64Type, c_double),
                b'd': (kCFNumberFloat64Type, c_double),
            }

            kCFBooleanTrue = c_void_p.from_address(cf(b'kCFBooleanTrue').value)

            def schedule_on(loop: c_void_p, pycb: Callable[[], None], *, var_keepalive: set, mode=kCFRunLoopDefaultMode):
                block: ObjCBlock

                def _pycb_real():
                    pycb()
                    var_keepalive.remove(block)
                block = pa.make_block(_pycb_real)
                var_keepalive.add(block)
                CFRunLoopPerformBlock(loop, mode, byref(block))
                CFRunLoopWakeUp(loop)

            def _runcoro_on_loop_base(
                coro: Coroutine[Any, Any, T],
                *,
                var_keepalive: set,
                loop: c_void_p,
                default: U = None,
                finish: Callable[[BaseException], None]
            ) -> CFRL_CoroResult[Union[T, U]]:
                # Default is returned when the coroutine wrongly calls CFRunLoopStop(currloop) or its equivalent
                res = CFRL_CoroResult[Union[T, U]](default)
                logger.debug_log(f'_runcoro_on_loop_base: starting coroutine: {coro=}')

                def _coro_step(v: Any = None, *, exc: Optional[BaseException] = None):
                    nonlocal res
                    logger.debug_log(f'coro step: {v=}; {exc=}')
                    fut: CFRL_Future
                    try:
                        if exc is not None:
                            fut = coro.throw(exc)
                        else:
                            fut = coro.send(v)
                        # TODO: support awaitables that aren't futures
                    except StopIteration as si:
                        logger.debug_log(f'stopping with return value: {si.value=}')
                        res.ret = si.value
                        finish(si)
                        return
                    except BaseException as e:
                        logger.debug_log(f'will throw exc raised from coro: {e=}')
                        res.rexc = e
                        finish(e)
                        return
                    else:
                        logger.debug_log(f'attaching done cb to: {fut=}')

                    def _on_fut_done(f: CFRL_Future):
                        logger.debug_log(f'fut done: {f=}')
                        try:
                            fut_res = f.result()
                        except BaseException as fut_err:
                            logger.debug_log(f'fut exc: {fut_err=}, scheduling exc callback')

                            def _exc_cb(fut_err=fut_err):
                                logger.debug_log(f'fut exc cb: calling _coro_step with {fut_err=}')
                                _coro_step(exc=fut_err)
                            scheduled = _exc_cb
                        else:
                            logger.debug_log(f'fut res: {fut_res=}, scheduling done callback')

                            def _normal_cb():
                                logger.debug_log(f'fut cb, calling _coro_step with {fut_res=}')
                                _coro_step(fut_res)
                            scheduled = _normal_cb
                        schedule_on(loop, scheduled, var_keepalive=var_keepalive)
                    fut.add_done_callback(_on_fut_done)
                    logger.debug_log(f'added done callback {_on_fut_done=}')

                schedule_on(loop, _coro_step, var_keepalive=var_keepalive)
                return res

            def runcoro_on_current(coro: Coroutine[Any, Any, T], *, default: U = None) -> Union[T, U]:
                var_keepalive = set()
                res = _runcoro_on_loop_base(coro, var_keepalive=var_keepalive, loop=currloop, default=default, finish=lambda exc: CFRunLoopStop(currloop))
                CFRunLoopRun()
                logger.debug_log(f'runcoro_on_current done: {res.rexc=}; {res.ret=}')
                if res.rexc is not None:
                    raise res.rexc from None
                return res.ret

            def runcoro_on_loop(coro: Coroutine[Any, Any, T], *, loop=mainloop, default: U = None) -> Union[T, U]:
                if loop.value == currloop.value:
                    return runcoro_on_current(coro, default=default)
                finished = False
                cv = Condition()
                var_keepalive = set()

                def finish(e: Union[BaseException, StopIteration]):
                    nonlocal finished
                    with cv:
                        finished = True
                        cv.notify()
                res = _runcoro_on_loop_base(coro, var_keepalive=var_keepalive, loop=loop, default=default, finish=finish)
                with cv:
                    while not finished:
                        cv.wait()

                logger.debug_log(f'runcoro_on_loop done: {res.rexc=}; {res.ret=}')
                if res.rexc is not None:
                    raise res.rexc from None
                return res.ret

            class PFC_WVHandler:
                CBDICT_TYPE = dict[int, Callable[[], None]]

                SIGNATURE_WEBVIEW_DIDFINISHNAVIGATION = b'v@:@@'
                SEL_WEBVIEW_DIDFINISHNAVIGATION = pa.sel_registerName(b'webView:didFinishNavigation:')

                @staticmethod
                def webView0_didFinishNavigation1(this: CRet.Py_PVoid, sel: CRet.Py_PVoid, rp_webview: CRet.Py_PVoid, rp_navi: CRet.Py_PVoid) -> None:
                    logger.debug_log(f'[(PyForeignClass_WebViewHandler){this} webView: {rp_webview} didFinishNavigation: {rp_navi}]')
                    if cb := navidg_cbdct.get(rp_navi or 0):
                        cb()

                SIGNATURE_USERCONTENTCONTROLLER_DIDRECEIVESCRIPTMESSAGE = b'v@:@@'
                SEL_USERCONTENTCONTROLLER_DIDRECEIVESCRIPTMESSAGE = pa.sel_registerName(b'userContentController:didReceiveScriptMessage:') 
                @staticmethod
                def userContentController0_didReceiveScriptMessage1(this: CRet.Py_PVoid, sel: CRet.Py_PVoid, rp_usrcontctlr: CRet.Py_PVoid, rp_sm: CRet.Py_PVoid) -> None:
                    logger.debug_log(f'[(PyForeignClass_WebViewHandler){this} userContentController: {rp_usrcontctlr} didReceiveScriptMessage: {rp_sm}]')
                    # TODO

            PFC_WVHandler.webView0_didFinishNavigation1 = CFUNCTYPE(
                None,
                c_void_p, c_void_p, c_void_p, c_void_p)(PFC_WVHandler.webView0_didFinishNavigation1)

            PFC_WVHandler.userContentController0_didReceiveScriptMessage1 = CFUNCTYPE(
                None,
                c_void_p, c_void_p, c_void_p, c_void_p)(PFC_WVHandler.userContentController0_didReceiveScriptMessage1)

            Py_WVHandler = pa.objc_allocateClassPair(NSObject, b'PyForeignClass_WebViewHandler', 0)
            if not Py_WVHandler:
                Py_WVHandler = pa.safe_objc_getClass(b'PyForeignClass_WebViewHandler')
                logger.debug_log('Failed to allocate class PyForeignClass_WebViewHandler')
                if not pa.class_conformsToProtocol(Py_WVHandler, WKNavigationDelegate):
                    raise RuntimeError(
                        'class PyForeignClass_WebViewHandler already exists '
                        'but does not conform to the WKNavigationDelegate protocol')
                if not pa.class_conformsToProtocol(Py_WVHandler, WKScriptMessageHandler):
                    raise RuntimeError(
                        'class PyForeignClass_WebViewHandler already exists '
                        'but does not conform to the WKScriptMessageHandler protocol')
                if imeth := pa.class_getInstanceMethod(Py_WVHandler, PFC_WVHandler.SEL_WEBVIEW_DIDFINISHNAVIGATION):
                    pa.method_setImplementation(imeth, PFC_WVHandler.webView0_didFinishNavigation1)
                    logger.debug_log('Updated the implementation of PyForeignClass_WebViewHandler (on navigation finish)')
                else:
                    pa.class_addMethod(
                        Py_WVHandler, PFC_WVHandler.SEL_WEBVIEW_DIDFINISHNAVIGATION,
                        PFC_WVHandler.webView0_didFinishNavigation1,
                        PFC_WVHandler.SIGNATURE_WEBVIEW_DIDFINISHNAVIGATION)
                    logger.debug_log('Added the implementation for PyForeignClass_WebViewHandler (on navigation finish)')

                if imeth := pa.class_getInstanceMethod(Py_WVHandler, PFC_WVHandler.SEL_USERCONTENTCONTROLLER_DIDRECEIVESCRIPTMESSAGE):
                    pa.method_setImplementation(imeth, PFC_WVHandler.userContentController0_didReceiveScriptMessage1)
                    logger.debug_log('Updated the implementation of PyForeignClass_WebViewHandler (on script message)')
                else:
                    pa.class_addMethod(
                        Py_WVHandler, PFC_WVHandler.SEL_USERCONTENTCONTROLLER_DIDRECEIVESCRIPTMESSAGE,
                        PFC_WVHandler.userContentController0_didReceiveScriptMessage1,
                        PFC_WVHandler.SIGNATURE_USERCONTENTCONTROLLER_DIDRECEIVESCRIPTMESSAGE)
                    logger.debug_log('Added the implementation for PyForeignClass_WebViewHandler (on script message)')
            else:
                if not pa.class_addMethod(
                        Py_WVHandler, PFC_WVHandler.SEL_WEBVIEW_DIDFINISHNAVIGATION,
                        PFC_WVHandler.webView0_didFinishNavigation1,
                        PFC_WVHandler.SIGNATURE_WEBVIEW_DIDFINISHNAVIGATION):
                    pa.objc_disposeClassPair(Py_WVHandler)
                    raise RuntimeError('class_addMethod failed (on navigation finished)')
                if not pa.class_addMethod(
                        Py_WVHandler, PFC_WVHandler.SEL_USERCONTENTCONTROLLER_DIDRECEIVESCRIPTMESSAGE,
                        PFC_WVHandler.userContentController0_didReceiveScriptMessage1,
                        PFC_WVHandler.SIGNATURE_USERCONTENTCONTROLLER_DIDRECEIVESCRIPTMESSAGE):
                    pa.objc_disposeClassPair(Py_WVHandler)
                    raise RuntimeError('class_addMethod failed (on script message)')

                if not pa.class_addProtocol(Py_WVHandler, WKNavigationDelegate):
                    pa.objc_disposeClassPair(Py_WVHandler)
                    raise RuntimeError('class_addProtocol failed for WKNavigationDelegate')
                if not pa.class_addProtocol(Py_WVHandler, WKScriptMessageHandler):
                    pa.objc_disposeClassPair(Py_WVHandler)
                    raise RuntimeError('class_addProtocol failed for WKScriptMessageHandler')
                pa.objc_registerClassPair(Py_WVHandler)
                logger.debug_log('Registered PyForeignClass_WebViewHandler')

            jsresult_id = c_void_p()
            jsresult_err = c_void_p()

            async def real_main():
                p_wvhandler = pa.safe_new_object(Py_WVHandler)
                pa.release_on_exit(p_wvhandler)

                async with AsyncExitStack() as exsk:
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
                        kCFBooleanTrue, p_setkey0,
                        argtypes=(c_void_p, c_void_p))
                    rp_pref = None

                    p_setkey1 = pa.safe_new_object(
                        NSString, b'initWithUTF8String:', b'allowUniversalAccessFromFileURLs',
                        argtypes=(c_char_p, ))
                    exsk.callback(pa.send_message, p_setkey1, b'release')
                    pa.send_message(
                        p_cfg, b'setValue:forKey:',
                        kCFBooleanTrue, p_setkey1,
                        argtypes=(c_void_p, c_void_p))

                    p_usrcontctlr = pa.safe_new_object(WKUserContentController)
                    exsk.callback(pa.send_message, p_usrcontctlr, b'release')

                    p_handler_name = pa.safe_new_object(
                        NSString, b'initWithUTF8String:', b'pywk',
                        argtypes=(c_char_p, ))
                    exsk.callback(pa.send_message, p_handler_name, b'release')
                    pa.send_message(
                        p_usrcontctlr, b'addScriptMessageHandler:name:',
                        p_wvhandler, p_handler_name,
                        argtypes=(c_void_p, c_void_p))

                    pa.send_message(
                        p_cfg, b'setUserContentController:', p_usrcontctlr,
                        argtypes=(c_void_p, ))

                    p_webview = pa.safe_new_object(
                        WKWebView, b'initWithFrame:configuration:',
                        CGRect(), p_cfg,
                        argtypes=(CGRect, c_void_p))
                    pa.release_on_exit(p_webview)
                    logger.debug_log('webview init')

                pa.send_message(
                    p_webview, b'setNavigationDelegate:',
                    p_wvhandler, argtypes=(c_void_p, ))
                logger.debug_log('webview set navidg')

                fut_navidone: CFRL_Future[None] = CFRL_Future()
                async with AsyncExitStack() as exsk:
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
                    logger.debug_log(f'Navigation started: {rp_navi}')

                    def cb_navi_done():
                        logger.debug_log('navigation done, resolving future')
                        fut_navidone.set_result(None)

                    navidg_cbdct[rp_navi.value] = cb_navi_done

                    logger.debug_log(f'loading: local HTML@{HOST.decode()}')

                    await fut_navidone
                logger.debug_log('navigation done')

                fut_jsdone: CFRL_Future[tuple[c_void_p, c_void_p]] = CFRL_Future()
                async with AsyncExitStack() as exsk:
                    ps_script = pa.safe_new_object(
                        NSString, b'initWithUTF8String:', SCRIPT,
                        argtypes=(c_char_p, ))
                    exsk.callback(pa.send_message, ps_script, b'release')

                    pd_jsargs = pa.safe_new_object(NSDictionary)
                    exsk.callback(pa.send_message, pd_jsargs, b'release')

                    rp_pageworld = c_void_p(pa.send_message(
                        WKContentWorld, b'pageWorld',
                        restype=c_void_p))

                    def completion_handler(self: CRet.Py_PVoid, id_result: CRet.Py_PVoid, err: CRet.Py_PVoid):
                        nonlocal jsresult_id, jsresult_err
                        jsresult_id = c_void_p(pa.send_message(c_void_p(id_result or 0), b'copy', restype=c_void_p))
                        pa.release_on_exit(jsresult_id)
                        jsresult_err = c_void_p(pa.send_message(c_void_p(err or 0), b'copy', restype=c_void_p))
                        pa.release_on_exit(jsresult_err)
                        logger.debug_log(f'JS done, resolving future; {id_result=}, {err=}')
                        fut_jsdone.set_result((jsresult_id, jsresult_err))

                    chblock = pa.make_block(completion_handler, None, POINTER(ObjCBlock), c_void_p, c_void_p)

                    pa.send_message(
                        # Requires iOS 15.0+, maybe test its availability first?
                        p_webview, b'callAsyncJavaScript:arguments:inFrame:inContentWorld:completionHandler:',
                        ps_script, pd_jsargs, c_void_p(None), rp_pageworld, byref(chblock),
                        argtypes=(c_void_p, c_void_p, c_void_p, c_void_p, POINTER(ObjCBlock)))

                    await fut_jsdone

            runcoro_on_loop(real_main(), loop=mainloop)

            if jsresult_err:
                code = pa.send_message(jsresult_err, b'code', restype=c_long)
                s_domain = str_from_nsstring(pa, c_void_p(pa.send_message(
                    jsresult_err, b'domain', restype=c_void_p)), default='<unknown>')
                s_uinfo = str_from_nsstring(pa, c_void_p(pa.send_message(
                    c_void_p(pa.send_message(jsresult_err, b'userInfo', restype=c_void_p)),
                    b'description', restype=c_void_p)), default='<no description provided>')
                raise RuntimeError(f'JS failed: NSError@{jsresult_err.value}, {code=}, domain={s_domain}, user info={s_uinfo}')

            logger.debug_log('JS execution completed')

            def pyobj_from_nsobj_jsresult(
                pa: PyNeApple,
                jsobj: c_void_p,
                *,
                visited: dict[int, _JSResultType[T, U, V]],
                undefined: T = None,
                null: U = None,
                on_unknown_st: Callable[[str], V] = _UnknownStructure,
            ) -> _JSResultType[T, U, V]:
                if not jsobj.value:
                    logger.debug_log(f'undefined@{jsobj.value}')
                    return undefined
                elif visitedobj := visited.get(jsobj.value):
                    logger.debug_log(f'visited@{jsobj.value}')
                    return visitedobj
                elif pa.instanceof(jsobj, NSNull):
                    logger.debug_log(f'null@{jsobj.value}')
                    visited[jsobj.value] = null
                    return null
                elif pa.instanceof(jsobj, NSString):
                    logger.debug_log(f'str@{jsobj.value}')
                    s_res = str_from_nsstring(pa, py_typecast(NotNull_VoidP, jsobj))
                    visited[jsobj.value] = s_res
                    return s_res
                elif pa.instanceof(jsobj, NSNumber):
                    logger.debug_log(f'num s @{jsobj.value}')
                    kcf_numtyp, restyp = type_to_largest[py_typecast(bytes, pa.send_message(
                        jsobj, b'objCType', restype=c_char_p))]
                    n_res = restyp()
                    if not CFNumberGetValue(jsobj, kcf_numtyp, byref(n_res)):
                        sval = str_from_nsstring(pa, py_typecast(NotNull_VoidP, c_void_p(
                            pa.send_message(jsresult_id, b'stringValue', restype=c_void_p))))
                        raise RuntimeError(f'CFNumberGetValue failed on CFNumberRef@{jsobj.value}, stringValue: {sval}')
                    n_resv = n_res.value
                    visited[jsobj.value] = n_resv
                    logger.debug_log(f'num e {n_resv.__class__.__name__}@{jsobj.value}')
                    return n_resv
                elif pa.instanceof(jsobj, NSDate):
                    dte1970 = py_typecast(float, CFDateGetAbsoluteTime(jsobj)) + 978307200.0
                    # dte1970 = pa.send_message(jsobj, b'timeIntervalSince1970', restype=c_double)
                    py_dte = dt.datetime.fromtimestamp(dte1970, dt.timezone.utc)
                    visited[jsobj.value] = py_dte
                    return py_dte
                elif pa.instanceof(jsobj, NSDictionary):
                    d = {}
                    visited[jsobj.value] = d

                    @CFUNCTYPE(None, c_void_p, c_void_p, c_void_p)
                    def visitor(k: CRet.Py_PVoid, v: CRet.Py_PVoid, userarg: CRet.Py_PVoid):
                        nonlocal d
                        logger.debug_log(f'visit s dict@{userarg=}; {k=}; {v=}')
                        k_ = pyobj_from_nsobj_jsresult(pa, c_void_p(k), visited=visited, undefined=undefined, null=null, on_unknown_st=on_unknown_st)
                        v_ = pyobj_from_nsobj_jsresult(pa, c_void_p(v), visited=visited, undefined=undefined, null=null, on_unknown_st=on_unknown_st)
                        logger.debug_log(f'visit e dict@{userarg=}; {k_=}; {v_=}')
                        d[k_] = v_

                    CFDictionaryApplyFunction(jsobj, visitor, jsobj)
                    return d
                elif pa.instanceof(jsobj, NSArray):
                    larr = CFArrayGetCount(jsobj)
                    arr = []
                    visited[jsobj.value] = arr
                    for i in range(larr):
                        v = CFArrayGetValueAtIndex(jsobj, i)
                        logger.debug_log(f'visit s arr@{jsobj.value}; {v=}')
                        v_ = pyobj_from_nsobj_jsresult(pa, c_void_p(v), visited=visited, undefined=undefined, null=null, on_unknown_st=on_unknown_st)
                        logger.debug_log(f'visit e arr@{jsobj.value}; {v_=}')
                        arr.append(v_)
                    return arr
                else:
                    tn = py_typecast(bytes, pa.class_getName(pa.object_getClass(jsobj))).decode()
                    logger.debug_log(f'unk@{jsobj.value=}; {tn=}')
                    unk_res = on_unknown_st(tn)
                    visited[jsobj.value] = unk_res
                    return unk_res

            result_pyobj = pyobj_from_nsobj_jsresult(pa, jsresult_id, visited={}, null=_NullTag)
            print(f'{pformat(result_pyobj)}')
    except Exception:
        import traceback
        logger.write_err(traceback.format_exc())
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
