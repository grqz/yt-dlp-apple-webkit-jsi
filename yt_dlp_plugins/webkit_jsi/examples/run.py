import os
import sys

from pprint import pformat
from typing import cast as py_typecast, Callable, get_args, Optional

from lib.logging import Logger
from lib.api import WKJS_Task, WKJS_UncaughtException, DefaultJSResult, PyResultType, get_gen

from .config import HOST, HTML, SCRIPT

def main():
    logger = Logger(debug=True)
    logger.debug_log(f'PID: {os.getpid()}')
    if os.getenv('CI'):
        PATH2CORE = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.realpath(__file__))))), 'core')
        if os.path.lexists(PATH2CORE):
            logger.debug_log(f'removing exisiting file at {PATH2CORE}')
            os.remove(PATH2CORE)
        logger.debug_log(f'writing symlink to coredump (if any) to {PATH2CORE} for CI')
        os.symlink(f'/cores/core.{os.getpid()}', PATH2CORE)
    gen = get_gen(logger=logger)
    try:
        sendmsg = next(gen)
        wv = sendmsg(WKJS_Task.NEW_WEBVIEW, ())
        try:
            sendmsg(WKJS_Task.NAVIGATE_TO, (wv, HOST, HTML))
            sendmsg(WKJS_Task.ON_SCRIPTLOG, (wv, print))
            def script_comm_cb(res: DefaultJSResult, cb: Callable[[PyResultType, Optional[str]], None]):
                logger.debug_log(f'received in comm channel: {res}')
                if isinstance(res, get_args(PyResultType)):
                    cb(py_typecast(PyResultType, res), None)
                else:
                    cb(None, f'Received unknown type {type(res)}')

            # Use `communicate(...)` in JS to call `script_comm_cb`
            # `communicate` returns a promise which will be resolved when `cb` is called
            # It's unnecessary to await the promise if the communication is single-way
            # (Note that `communicate` is a local const variable)
            # See js_to_py.md for limitations
            sendmsg(WKJS_Task.ON_SCRIPTCOMM, (wv, script_comm_cb))

            # `SCRIPT` is the async function body. `result_pyobj` is the return value of the function
            result_pyobj = py_typecast(DefaultJSResult, sendmsg(WKJS_Task.EXECUTE_JS, (wv, SCRIPT)))
            logger.debug_log(f'{pformat(result_pyobj)}')
        except WKJS_UncaughtException as e:
            logger.write_err(f'Uncaught exception from JS: {e!r}')
        finally:
            sendmsg(WKJS_Task.FREE_WEBVIEW, (wv, ))
            try:
                sendmsg(WKJS_Task.SHUTDOWN, ())
            except StopIteration:
                ...
            next(gen)
    except StopIteration:
        return 0
    except Exception:
        import traceback
        logger.write_err(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
