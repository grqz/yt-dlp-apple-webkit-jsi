"""
A MORE PYTHONIC API
"""

import json
from typing import Optional, cast as py_typecast

from .logging import Logger
from .api import COMM_CBTYPE, LOG_CBTYPE, SENDMSG_CBTYPE, DefaultJSResult, NullTag, WKJS_Task, WKJS_UncaughtException, get_gen

class WKJSE_Factory:
    __slots__ = '_gen', '_sendmsg'

    def __init__(self, logger: Logger):
        self._gen = get_gen(logger)
        self._sendmsg = None

    def __enter__(self):
        assert self._gen is not None and self._sendmsg is None
        self._sendmsg = self._gen.send(None)
        return self._sendmsg

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        assert self._gen is not None and self._sendmsg is not None
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
        self._sendmsg = None
        self._gen = None


class WKJSE_Webview:
    __slots__ = '_send', '_wv', '_ucc_v'

    def __init__(self, sendmsg: SENDMSG_CBTYPE):
        self._send = sendmsg
        self._wv = 0
        self._ucc_v: Optional[int] = None

    @property
    def _ucc(self) -> int:
        assert self._wv
        if not self._ucc_v:
            self._ucc_v = py_typecast(int, self._send(WKJS_Task.GET_USRCONTCTLR, (self._wv, )))
        return self._ucc_v

    def __enter__(self):
        assert not self._wv
        self._wv = self._send(WKJS_Task.NEW_WEBVIEW, ())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        assert self._wv
        self._send(WKJS_Task.FREE_WEBVIEW, (self._wv, ))
        self._wv = 0
        self._ucc_v = None

    def navigate_to(self, host: str, html: str) ->  None:
        self._send(WKJS_Task.NAVIGATE_TO, (self._wv, host, html))

    def execute_js(self, script: str) -> DefaultJSResult:
        res, exc = py_typecast(tuple[DefaultJSResult, Optional[WKJS_UncaughtException]], self._send(WKJS_Task.EXECUTE_JS, (self._wv, script)))
        if exc is not None:
            raise exc
        return res

    def on_script_log(self, cb: LOG_CBTYPE) -> Optional[LOG_CBTYPE]:
        return py_typecast(Optional[LOG_CBTYPE], self._send(WKJS_Task.ON_SCRIPTLOG2, (self._ucc, cb)))

    def on_script_comm(self, cb: COMM_CBTYPE) -> Optional[COMM_CBTYPE]:
        return py_typecast(Optional[COMM_CBTYPE], self._send(WKJS_Task.ON_SCRIPTCOMM2, (self._ucc, cb)))


def jsres_to_json(jsres: DefaultJSResult, **kwargs):
    return json.dumps(None if jsres is NullTag else jsres, **kwargs)


def jsres_to_log1(jsres: DefaultJSResult) -> str:
    if jsres is None:
        return 'undefined'
    elif jsres is NullTag:
        return 'null'
    elif isinstance(jsres, str):
        return jsres
    else:
        return json.dumps(jsres, separators=(',', ':'), default=lambda *_, **__: None)


def jsres_to_log(*jsres: DefaultJSResult):
    return ' '.join(map(jsres_to_log1, jsres)) + '\n'


# TODO(?): container class for log capture
