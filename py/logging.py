import os

from stat import S_ISREG
from typing import Any, TypeVar, overload


T = TypeVar('T')


class Logger:
    class _DefaultTag:
        ...

    STDOUT_IS_ISREG = S_ISREG(os.fstat(1).st_mode)
    STDERR_IS_ISREG = S_ISREG(os.fstat(1).st_mode)

    __slots__ = '_debug',

    def __init__(self, debug=False) -> None:
        self._debug = debug

    @overload
    def debug_log(self, msg: T, *, end='\n') -> T: ...
    @overload
    def debug_log(self, msg, *, end='\n', ret: T) -> T: ...

    def debug_log(self, msg, *, end='\n', ret: Any = _DefaultTag):
        if self._debug:
            os.write(1, (str(msg) + end).encode())
            if Logger.STDOUT_IS_ISREG:
                os.fsync(1)
        return msg if ret is Logger._DefaultTag else ret

    def write_err(self, msg, end='\n'):
        os.write(2, (str(msg) + end).encode())
        if Logger.STDERR_IS_ISREG:
            os.fsync(2)
