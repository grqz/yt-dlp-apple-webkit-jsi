"""
A MORE PYTHONIC API
"""

from typing import Optional, cast as py_typecast

from .logging import Logger
from .api import COMM_CBTYPE, LOG_CBTYPE, SENDMSG_CBTYPE, DefaultJSResult, WKJS_Task, get_gen

class WKJSE_Factory:
    __slots__ = '_gen', '_sendmsg'

    def __init__(self, logger: Logger):
        self._gen = get_gen(logger)
        self._sendmsg = None

    def __enter__(self):
        assert self._sendmsg is None
        self._sendmsg = self._gen.send(None)
        return self._sendmsg

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        assert self._sendmsg is not None
        try:
            self._sendmsg(WKJS_Task.SHUTDOWN, ())
        except StopIteration:
            ...
        else:
            assert False, 'shutdown failure (inner)'

        try:
            self._gen.send(None)
        except StopIteration:
            ...
        else:
            assert False, 'shutdown failure (outer)'

class WKJSE_Webview:
    __slots__ = '_send', '_wv'

    def __init__(self, sendmsg: SENDMSG_CBTYPE):
        self._send = sendmsg
        self._wv = 0

    def __enter__(self):
        assert not self._wv
        self._wv = self._send(WKJS_Task.NEW_WEBVIEW, ())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        assert self._wv
        self._send(WKJS_Task.FREE_WEBVIEW, (self._wv, ))

    def navigate_to(self, host: str, html: str) ->  None:
        self._send(WKJS_Task.NAVIGATE_TO, (self._wv, host, html))

    def execute_js(self, script: str) -> DefaultJSResult:
        self._send(WKJS_Task.EXECUTE_JS, (self._wv, script))

    def on_script_log(self, cb: LOG_CBTYPE) -> Optional[LOG_CBTYPE]:
        return py_typecast(Optional[LOG_CBTYPE], self._send(WKJS_Task.ON_SCRIPTLOG, (self._wv, cb)))

    def on_script_comm(self, cb: COMM_CBTYPE) -> Optional[COMM_CBTYPE]:
        return py_typecast(Optional[COMM_CBTYPE], self._send(WKJS_Task.ON_SCRIPTCOMM, (self._wv, cb)))

