import abc
import os

from stat import S_ISREG
from typing import Literal, Optional, Union


class AbstractLogger(abc.ABC):
    @abc.abstractmethod
    def trace(self, message: str) -> None:
        pass

    @abc.abstractmethod
    def debug(self, message: str, *, once=False) -> None:
        pass

    @abc.abstractmethod
    def info(self, message: str) -> None:
        pass

    @abc.abstractmethod
    def warning(self, message: str, *, once=False) -> None:
        pass

    @abc.abstractmethod
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
