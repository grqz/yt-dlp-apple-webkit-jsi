import abc
import os

from stat import S_ISREG
from typing import Any, Literal, Optional, Protocol, TypeVar, Union, overload


T = TypeVar('T')


class AbstractLogger(Protocol):
    def trace(self, message: str) -> None:
        pass

    def debug(self, message: str, *, once=False) -> None:
        pass

    def info(self, message: str) -> None:
        pass

    def warning(self, message: str, *, once=False) -> None:
        pass

    def error(self, message: str, *, cause=None) -> None:
        pass


class DefaultLoggerImpl(AbstractLogger):
    ST_ISREG = None, S_ISREG(os.fstat(1).st_mode), S_ISREG(os.fstat(2).st_mode)

    __slots__ = '_trace', '_logged'

    def __init__(self, *, trace=False) -> None:
        self._trace = trace
        self._logged: dict[int, set[str]] = {}

    def _out(self, msg: str, *, flush: bool, fd: Union[Literal[1], Literal[2]], once: Optional[int] = None):
        if once is not None:
            loggedmsgs = self._logged.get(once)
            if loggedmsgs is None:
                loggedmsgs = self._logged[once] = set()
            if msg in loggedmsgs:
                return
            else:
                loggedmsgs.add(msg)
        os.write(fd, (msg + '\n').encode())
        if flush and DefaultLoggerImpl.ST_ISREG[fd]:
            os.fsync(fd)

    def trace(self, message: str) -> None:
        if not self._trace:
            return
        self._out(message, flush=True, fd=2)

    def debug(self, message: str, *, once=False) -> None:
        self._out(message, flush=True, fd=2, once=0 if once else None)

    def info(self, message: str) -> None:
        self._out(message, flush=False, fd=1)

    def warning(self, message: str, *, once=False) -> None:
        self._out(message, flush=False, fd=2, once=1 if once else None)

    def error(self, message: str, *, cause=None) -> None:
        self._out(message + f' (caused by {cause!r})' if cause is not None else message, flush=False, fd=2)


# class Logger:
#     class _DefaultTag:
#         ...
# 
#     STDOUT_IS_ISREG = S_ISREG(os.fstat(1).st_mode)
#     STDERR_IS_ISREG = S_ISREG(os.fstat(1).st_mode)
# 
#     __slots__ = '_debug',
# 
#     def __init__(self, debug=False) -> None:
#         self._debug = debug
# 
#     @overload
#     def debug_log(self, msg: T, *, end='\n') -> T: ...
#     @overload
#     def debug_log(self, msg, *, end='\n', ret: T) -> T: ...
# 
#     def debug_log(self, msg, *, end='\n', ret: Any = _DefaultTag):
#         if self._debug:
#             os.write(1, (str(msg) + end).encode())
#             if Logger.STDOUT_IS_ISREG:
#                 os.fsync(1)
#         return msg if ret is Logger._DefaultTag else ret
# 
#     def write_err(self, msg, end='\n'):
#         os.write(2, (str(msg) + end).encode())
#         if Logger.STDERR_IS_ISREG:
#             os.fsync(2)
