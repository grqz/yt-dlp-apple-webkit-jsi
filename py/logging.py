import os

from stat import S_ISREG
from typing import Any, TypeVar, overload


T = TypeVar('T')


class _DefaultTag:
    ...


STDOUT_IS_ISREG = S_ISREG(os.fstat(1).st_mode)
STDERR_IS_ISREG = S_ISREG(os.fstat(1).st_mode)


@overload
def debug_log(msg: T, *, end='\n') -> T: ...
@overload
def debug_log(msg, *, end='\n', ret: T) -> T: ...


def debug_log(msg, *, end='\n', ret: Any = _DefaultTag):
    os.write(1, (str(msg) + end).encode())
    if STDOUT_IS_ISREG:
        os.fsync(1)
    return msg if ret is _DefaultTag else ret


@overload
def dummy_debug_log(msg: T, *, end='\n') -> T: ...
@overload
def dummy_debug_log(msg, *, end='\n', ret: T) -> T: ...


def dummy_debug_log(msg, *, end='\n', ret: Any = _DefaultTag):
    return msg if ret is _DefaultTag else ret


def write_err(msg, end='\n'):
    os.write(2, (str(msg) + end).encode())
    if STDERR_IS_ISREG:
        os.fsync(2)


def dummy_write_err(msg, end='\n'):
    pass
