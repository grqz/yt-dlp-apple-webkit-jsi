import os
import sys
import traceback

from pprint import pformat
from typing import cast as py_typecast, Callable, get_args, Optional

from lib.logging import DefaultLoggerImpl as Logger
from lib.api import NullTag, WKJS_Task, WKJS_UncaughtException, DefaultJSResult, PyResultType, get_gen

from .config import HOST, HTML, SCRIPT

def main():
    logger = Logger(trace=True)
    logger.trace(f'PID: {os.getpid()}')
    if os.getenv('CI'):
        PATH2CORE = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.realpath(__file__))))), 'core')
        if os.path.lexists(PATH2CORE):
            logger.trace(f'removing exisiting file at {PATH2CORE}')
            os.remove(PATH2CORE)
        logger.trace(f'writing symlink to coredump (if any) to {PATH2CORE} for CI')
        os.symlink(f'/cores/core.{os.getpid()}', PATH2CORE)
    gen = get_gen(logger=logger)
    try:
        sendmsg = next(gen)
        sendmsg(7, ())  # default case
        sendmsg(7, ('ordinary string', ))
        sendmsg(7, ('\0' * 28602851, ))
        wv, ucc = py_typecast(tuple[int, int], sendmsg(WKJS_Task.NEW_WEBVIEW, ()))
    except BaseException:
        logger.error(traceback.format_exc())
        return 1
    try:
        sendmsg(WKJS_Task.NAVIGATE_TO, (wv, HOST, HTML))
        sendmsg(WKJS_Task.ON_SCRIPTLOG2, (ucc, print))
        def script_comm_cb(res: DefaultJSResult, cb: Callable[[PyResultType, Optional[str]], None]):
            logger.trace(f'received in comm channel: {res}')
            if res is NullTag:
                cb(None, None)
            elif isinstance(res, get_args(PyResultType)):
                cb(py_typecast(PyResultType, res), None)
            else:
                cb(None, f'Received unknown type {type(res)}')

        # Use `communicate(...)` in JS to call `script_comm_cb`
        # `communicate` returns a promise which will be resolved when `cb` is called
        # It's unnecessary to await the promise if the communication is single-way
        # (Note that `communicate` is a local const variable)
        # See js_to_py.md for limitations
        sendmsg(WKJS_Task.ON_SCRIPTCOMM2, (ucc, script_comm_cb))

        # `SCRIPT` is the async function body. `result_pyobj` is the return value of the function
        result_pyobj, exc = py_typecast(tuple[DefaultJSResult, Optional[WKJS_UncaughtException]], sendmsg(WKJS_Task.EXECUTE_JS, (wv, SCRIPT)))
        if exc is not None:
            logger.error(f'Uncaught exception from JS: {exc!r}')
            raise exc
        logger.trace(f'{pformat(result_pyobj)}')
    except BaseException as e:
        logger.error(f'caught exception {e!r}')
        logger.error(traceback.format_exc())
        return 1
    finally:
        logger.trace('freeing webview')
        sendmsg(WKJS_Task.FREE_WEBVIEW, (wv, ))
        try:
            sendmsg(WKJS_Task.SHUTDOWN, ())
        except StopIteration:
            ...
        else:
            assert 0
        try:
            next(gen)
        except StopIteration:
            return 0
        else:
            assert 0


if __name__ == '__main__':
    sys.exit(main())
