import sys
import traceback

from pprint import pprint
from typing import cast as py_typecast, Callable, get_args, Optional

from .logging import Logger
from .config import HOST, HTML, SCRIPT
from .api import DefaultJSResult, PyResultType, WKJS_UncaughtException
from .easy import WKJSE_Factory, WKJSE_Webview

def main():
    logger = Logger()
    try:
        def script_comm_cb(res: DefaultJSResult, cb: Callable[[PyResultType, Optional[str]], None]):
            logger.debug_log(f'received in comm channel: {res}')
            if isinstance(res, get_args(PyResultType)):
                cb(py_typecast(PyResultType, res), None)
            else:
                cb(None, f'Received unknown type {type(res)}')
        with WKJSE_Factory(logger) as send, WKJSE_Webview(send) as wv:
            wv.navigate_to(HOST, HTML)
            wv.on_script_log(print)

            # Use `communicate(...)` in JS to call `script_comm_cb`
            # `communicate` returns a promise which will be resolved when `cb` is called
            # It's unnecessary to await the promise if the communication is single-way
            # (Note that `communicate` is a local const variable)
            # See js_to_py.md for limitations
            wv.on_script_comm(script_comm_cb)

            # The above calls are all optional
            # `SCRIPT` is the async function body. `result_pyobj` is the return value of the function
            pprint(wv.execute_js(SCRIPT))
        return 0
    except WKJS_UncaughtException as e:
        logger.write_err(f'Uncaught exception from JS: {e!r}')
        return 1
    except Exception:
        logger.write_err(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
