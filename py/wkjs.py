import abc
import enum

from dataclasses import dataclass
from typing import Any, Optional, Generator


class WKJS_LogDestination(abc.ABC):
    @abc.abstractmethod
    def write(self, x: bytes) -> None: ...

    def clear(self) -> None:
        raise NotImplementedError

    def __hash__(self) -> int:
        return id(self)


class _WKJS_LogType(enum.Enum):
    TRACE = 0
    DIAG = 1
    INFO = 2
    WARN = 3
    ASSERT = 4
    ERR = 5


class WKJS_LogLevel(enum.IntFlag):
    NONE = 0
    TRACE = 1 << _WKJS_LogType.TRACE.value
    DIAG = 1 << _WKJS_LogType.DIAG.value
    INFO = 1 << _WKJS_LogType.INFO.value
    WARN = 1 << _WKJS_LogType.WARN.value
    ASSERTION = 1 << _WKJS_LogType.ASSERT.value
    ERROR = 1 << _WKJS_LogType.ERR.value
    LEVEL_SILENT = NONE
    LEVEL_ERROR = ERROR
    LEVEL_ASSERTION = ASSERTION | ERROR
    LEVEL_WARN = WARN | ASSERTION
    LEVEL_DIAG = DIAG | WARN
    LEVEL_TRACE = TRACE | DIAG
    LEVEL_DEBUG = LEVEL_TRACE


class WKJS_LogCapture:
    __slots__ = '_ds', '_clr'

    def __init__(self, destinations: dict[WKJS_LogDestination, WKJS_LogLevel], *, allow_clear=False):
        self._ds: tuple[list[WKJS_LogDestination], ...] = ([], [], [], [], [])
        self._clr = (lambda: (dest.clear() for dest in destinations)) if allow_clear else lambda: None
        for dest, lvl in destinations.items():
            while msbit := lvl.value.bit_count():
                self._ds[msbit].append(dest)

    def log(self, msg: str, *, ltyp: _WKJS_LogType):
        [dst.write(msg.encode()) for dst in self._ds[ltyp.value]]

    def clear(self):
        self._clr()


@dataclass
class WKJS_InterpretTask:
    logc: WKJS_LogCapture
    catch_jsexc = True


@dataclass
class WKJS_InterpretResult:
    jsresult: 'Any'  # TODO


class WKJS_Interpreter:
    def __init__(self, **cfg):
        self._active = True

    def shutdown_executor(self):
        self._active = False

    def navigate_to(self, url, html): ...

    def js_executor(self) -> Generator[Optional[WKJS_InterpretResult], WKJS_InterpretTask, None]:
        last_res = None
        while self._active:
            nxtsk = yield last_res
            last_res = (lambda *_, **__: None)(nxtsk)
