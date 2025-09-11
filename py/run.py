import dataclasses
import sys

from contextlib import AsyncExitStack, ExitStack
from ctypes import (
    POINTER,
    Structure,
    byref,
    c_byte, c_char_p,
    c_double,
    c_long, c_void_p,
)
from threading import Condition
from typing import Any, Awaitable, Callable, Coroutine, Generator, Generic, Optional, TypeVar, Union, cast as py_typecast, overload

from .pyneapple_objc import (
    CRet,
    NotNull_VoidP,
    ObjCBlock,
    PyNeApple,
    as_fnptr,
    cfn_at,
    debug_log,
    write_err,
)
from .config import HOST, HTML, SCRIPT


T = TypeVar('T')
U = TypeVar('U')


class CFEL_Future(Awaitable[T]):
    def __init__(self):
        self._cbs: list[Callable[['CFEL_Future[T]'], None]] = []
        self._done = False
        self._result: Optional[T] = None

    def result(self) -> T:
        if not self._done:
            raise RuntimeError('result method called upon a future that is not yet resolved')
        return py_typecast(T, self._result)

    def add_done_callback(self, cb: Callable[['CFEL_Future[T]'], None]) -> None:
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


@dataclasses.dataclass
class CFEL_CoroResult(Generic[T]):
    ret: T
    rexc: Optional[BaseException] = None


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
                def webView0_didFinishNavigation1(this: CRet.Py_PVoid, sel: CRet.Py_PVoid, rp_webview: CRet.Py_PVoid, rp_navi: CRet.Py_PVoid) -> None:
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
            if currloop.value != mainloop.value:
                debug_log('warning: running code on another loop is an experimental feature')
            kcf_true = c_void_p.from_address(cf(b'kCFBooleanTrue').value)

            def schedule_on(loop: c_void_p, pycb: Callable[[], None], *, mode: c_void_p = kCFRunLoopDefaultMode):
                CFRunLoopPerformBlock(loop, mode, pa.make_block(pycb))
                CFRunLoopWakeUp(loop)

            def _runcoro_on_loop_base(
                coro: Coroutine[Any, Any, T],
                *,
                active_cbs: set,
                loop: c_void_p,
                default: U = None,
                finish: Callable[[bool, Union[BaseException, StopIteration]], None]
            ) -> CFEL_CoroResult[Union[T, U]]:
                # Default is returned when the coroutine wrongly calls CFRunLoopStop(currloop) or its equivalent
                res = CFEL_CoroResult[Union[T, U]](default)
                debug_log(f'_runcoro_on_loop_base: starting coroutine: {coro=}')

                def _coro_step(v: Any = None, *, exc: Optional[BaseException] = None):
                    nonlocal res
                    debug_log(f'coro step: {v=}; {exc=}')
                    fut: CFEL_Future
                    try:
                        if exc is not None:
                            fut = coro.throw(exc)
                        else:
                            fut = coro.send(v)
                    except StopIteration as si:
                        debug_log(f'stopping with return value: {si.value=}')
                        finish(True, si)
                        res.ret = si.value
                        return
                    except BaseException as e:
                        debug_log(f'will throw exc raised from coro: {e=}')
                        finish(False, e)
                        res.rexc = e
                        return
                    else:
                        debug_log(f'attaching done cb to: {fut=}')

                    def _on_fut_done(f: CFEL_Future):
                        debug_log(f'fut done: {f=}')
                        try:
                            fut_res = f.result()
                        except BaseException as fut_err:
                            debug_log(f'fut exc: {fut_err=}, scheduling exc callback')

                            def _exc_cb(fut_err=fut_err):
                                debug_log(f'fut exc cb: calling _coro_step with {fut_err=}')
                                _coro_step(exc=fut_err)
                                active_cbs.remove(_exc_cb)
                            scheduled = _exc_cb
                        else:
                            debug_log(f'fut res: {fut_res=}, scheduling done callback')

                            def _normal_cb():
                                debug_log(f'fut cb, calling _coro_step with {fut_res=}')
                                _coro_step(fut_res)
                                active_cbs.remove(_normal_cb)
                            scheduled = _normal_cb
                        active_cbs.add(scheduled)
                        schedule_on(loop, scheduled)
                        active_cbs.remove(_on_fut_done)
                    active_cbs.add(_on_fut_done)
                    fut.add_done_callback(_on_fut_done)
                    debug_log(f'added done callback {_on_fut_done=}')

                active_cbs.add(_coro_step)
                schedule_on(loop, _coro_step)
                return res

            def runcoro_on_current(coro: Coroutine[Any, Any, T], *, default: U = None) -> Union[T, U]:
                active_cbs = set()
                res = _runcoro_on_loop_base(coro, active_cbs=active_cbs, loop=currloop, default=default, finish=lambda s, e: CFRunLoopStop(currloop))
                CFRunLoopRun()
                debug_log(f'runcoro_on_current done: {res.rexc=}; {res.ret=}')
                if res.rexc is not None:
                    raise res.rexc from None
                return res.ret

            def runcoro_on_loop(coro: Coroutine[Any, Any, T], *, loop=mainloop, default: U = None) -> Union[T, U]:
                if loop.value == currloop.value:
                    return runcoro_on_current(coro, default=default)
                finished = False
                cv = Condition()
                active_cbs = set()

                def finish(s: bool, e: Union[BaseException, StopIteration]):
                    nonlocal finished
                    with cv:
                        finished = True
                        cv.notify()
                res = _runcoro_on_loop_base(coro, active_cbs=active_cbs, loop=loop, default=default, finish=finish)
                with cv:
                    while not finished:
                        cv.wait()

                debug_log(f'runcoro_on_loop done: {res.rexc=}; {res.ret=}')
                if res.rexc is not None:
                    raise res.rexc from None
                return res.ret

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
            # TODO: replace with Coroutine return?

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

                fut_navidone: CFEL_Future[None] = CFEL_Future()
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
                    debug_log(f'Navigation started: {rp_navi}')

                    def cb_navi_done():
                        debug_log('navigation done, resolving future')
                        fut_navidone.set_result(None)

                    navidg_cbdct[rp_navi.value] = cb_navi_done

                    debug_log(f'loading: local HTML@{HOST.decode()}')

                    await fut_navidone
                debug_log('navigation done')

                fut_jsdone: CFEL_Future[tuple[c_void_p, c_void_p]] = CFEL_Future()
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
                        debug_log(f'JS done, resolving future; {id_result=}, {err=}')
                        fut_jsdone.set_result((jsresult_id, jsresult_err))

                    chblock = pa.make_block(completion_handler, None, POINTER(ObjCBlock), c_void_p, c_void_p)

                    pa.send_message(
                        # Requires iOS 15.0+, maybe test its availability first?
                        p_webview, b'callAsyncJavaScript:arguments:inFrame:inContentWorld:completionHandler:',
                        ps_script, pd_jsargs, c_void_p(None), rp_pageworld, byref(chblock),
                        argtypes=(c_void_p, c_void_p, c_void_p, c_void_p, POINTER(ObjCBlock)))

                    await fut_jsdone

            # TODO: jsresult_id, jsresult_err =
            runcoro_on_loop(real_main(), loop=mainloop)

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
