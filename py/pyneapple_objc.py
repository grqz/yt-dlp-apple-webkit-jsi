import os
import platform
import struct
import sys

from contextlib import contextmanager, ExitStack
from ctypes import CDLL, CFUNCTYPE, c_char_p, c_void_p, c_int
from ctypes.util import find_library
from functools import wraps
from typing import Callable, Generator, Type


def setup_signature(c_fn, restype: Type | None = None, *argtypes: Type):
    c_fn.argtypes = argtypes
    c_fn.restype = restype
    return c_fn


def cfn_at(addr: int, restype: Type | None = None, *argtypes: Type) -> Callable:
    return CFUNCTYPE(restype, *argtypes)(addr)


def objc_type_encode(type: Type | None) -> bytes:
    # How do i detect pointers and arrays?
    ...


class DLError(OSError):
    UNKNOWN_ERROR = b'<unknown error>'

    def __init__(self, fname: bytes, arg: str, err: bytes | None) -> None:
        self.fname = fname
        self.err = err
        self.arg = arg

    def __str__(self) -> str:
        arg = ''
        if self.arg:
            arg = f' {self.arg}'
        errm = self.err or DLError.UNKNOWN_ERROR
        return f'Failed to {self.fname.decode()}{arg}: {errm.decode()}'

    def __repr__(self) -> str:
        return f'DLError(fname={self.fname!r}, arg={self.arg!r}, err={self.err!r})'

    @staticmethod
    def handle(ret: int | None, fname: bytes, arg: str, err: bytes | None) -> int:
        if not ret:
            raise DLError(fname, arg, err)
        return ret

    @staticmethod
    def wrap(fn, fname: bytes, errfn: Callable[[], bytes | None], *partial, success_handle):
        return wraps(fn)(lambda *args: success_handle(DLError.handle(fn(*partial, *args), fname, ''.join(map(str, args)), errfn())))


class VOIDP_NOTNULL:
    @property
    def value(self) -> int: ...


DLSYM_FUNC = Callable[[bytes], VOIDP_NOTNULL]


def dlsym_factory(ldl_openmode: int = os.RTLD_NOW):
    ldl = CDLL(find_library('dl'), mode=ldl_openmode)
    # void *dlopen(const char *file, int mode);
    fn_dlopen = setup_signature(ldl.dlopen, c_void_p, c_char_p, c_int)
    # void *dlsym(void *restrict handle, const char *restrict name);
    fn_dlsym = setup_signature(ldl.dlsym, c_void_p, c_void_p, c_char_p)
    # int dlclose(void *handle);
    fn_dlclose = setup_signature(ldl.dlclose, c_int, c_void_p)
    # char *dlerror(void);
    fn_dlerror = setup_signature(ldl.dlerror, c_char_p)

    @contextmanager
    def dlsym_factory(path: bytes, mode: int = os.RTLD_LAZY) -> Generator[DLSYM_FUNC, None, None]:
        print(f'will dlopen {path.decode()}', flush=True)
        h_lib = DLError.handle(
            fn_dlopen(path, mode),
            b'dlopen', path.decode(), fn_dlerror())
        try:
            yield DLError.wrap(fn_dlsym, b'dlsym', fn_dlerror, c_void_p(h_lib), success_handle=c_void_p)
        finally:
            print(f'will dlclose {path.decode()}', flush=True)
            DLError.handle(
                not fn_dlclose(h_lib),
                b'dlclose', path.decode(), fn_dlerror())
    return dlsym_factory


class PyNeApple:
    BLOCK_ST = struct.Struct(b'@PiiPP')
    BLOCKDESC_SIGNATURE_ST = struct.Struct(b'@LLP')
    BLOCKDESC_ST = struct.Struct(b'@LL')
    __slots__ = '_stack', 'dlsym_of_lib', '_objc', '_system', '_lobjc', 'objc_getClass', 'pobjc_msgSend', 'sel_registerName', 'p_NSConcreteMallocBlock', '_fwks', '_init'

    @staticmethod
    def path_to_framework(fwk_name: str, use_findlib: bool = False):
        if use_findlib:
            return find_library(fwk_name)
        return f'/System/Library/Frameworks/{fwk_name}.framework/{fwk_name}'

    def __init__(self):
        if platform.uname()[0] != 'Darwin':
            print('Warning: kernel is not Darwin, PyNeApple might not function correctly')
        self._init = False

    def __enter__(self):
        if self._init:
            raise RuntimeError('instance already initialized, please create a new instance')
        try:
            self._stack = ExitStack()
            self.dlsym_of_lib = dlsym_factory()
            self._objc = self._stack.enter_context(self.dlsym_of_lib(b'/usr/lib/libobjc.A.dylib', os.RTLD_NOW))
            self._system = self._stack.enter_context(self.dlsym_of_lib(b'/usr/lib/libobjc.A.dylib', os.RTLD_LAZY))
            self._lobjc = CDLL('/usr/lib/libobjc.A.dylib', mode=os.RTLD_NOW)
            self.objc_getClass = cfn_at(self._objc(b'objc_getClass').value, c_void_p, c_char_p)
            self.pobjc_msgSend = self._objc(b'objc_msgSend').value
            self.sel_registerName = cfn_at(self._objc(b'sel_registerName').value, c_void_p, c_char_p)
            self.p_NSConcreteMallocBlock = self._system(b'_NSConcreteMallocBlock')
            self._fwks: dict[str, DLSYM_FUNC] = {}
            self._init = True
            return self
        except Exception as e:
            if hasattr(self, '_stack'):
                self._stack.close()
            raise e

    def __exit__(self, exc_type, exc_value, traceback):
        return self._stack.__exit__(exc_type, exc_value, traceback)

    @property
    def dlsym_objc(self):
        return self._objc

    def load_framework_from_path(self, fwk_name: str, fwk_path: str | None = None, mode=os.RTLD_LAZY) -> DLSYM_FUNC:
        if not fwk_path:
            fwk_path = PyNeApple.path_to_framework(fwk_name)
            if not fwk_path:
                raise ValueError(f'Could not find framework {fwk_name}, please provide a valid path')
        if fwk := self._fwks.get(fwk_name):
            return fwk
        ret = self._fwks[fwk_name] = self._stack.enter_context(self.dlsym_of_lib(fwk_path.encode(), mode=mode))
        return ret

    def send_message(self, obj: c_void_p, sel_name: bytes, *args, restype: Type | None = None, argtypes: tuple[Type, ...] = ()):
        return cfn_at(self.pobjc_msgSend, restype, c_void_p, c_void_p, *argtypes)(obj, c_void_p(self.sel_registerName(sel_name)), *args)

    # def pycb_to_block(self, cb: Callable, *argstype: Type, signature: bytes):
    #     f = 0
    #     if signature is not None:
    #         f |= 1 << 30
    #         desc = PyNeApple.BLOCKDESC_SIGNATURE_ST.pack(0, PyNeApple.BLOCK_ST.size, signature)
    #     else:
    #         desc = PyNeApple.BLOCKDESC_ST.pack(0, PyNeApple.BLOCK_ST.size)
    #     # desc -> &desc
    #     block = PyNeApple.BLOCK_ST.pack(self.p_NSConcreteMallocBlock, f, 0, CFUNCTYPE(None, *argstype)(cb), c_char_p(desc).value)
    #     return desc, block

# class ObjCBlock:
#     # @staticmethod

#     def __init__(self, pyneapple: PyNeApple, cb: Callable, restype: Type | None, *argstype: Type):
#         f = 0
#         if signature is not None:
#             f |= 1 << 30
#             desc = PyNeApple.BLOCKDESC_SIGNATURE_ST.pack(0, PyNeApple.BLOCK_ST.size, signature)
#         else:
#             desc = PyNeApple.BLOCKDESC_ST.pack(0, PyNeApple.BLOCK_ST.size)
#         # desc -> &desc
#         block = PyNeApple.BLOCK_ST.pack(self.p_NSConcreteMallocBlock, f, 0, CFUNCTYPE(None, *argstype)(cb), c_char_p(desc).value)
#         return desc, block


def main():
    with PyNeApple() as pa:
        fndatn = pa.load_framework_from_path('Foundation')
        cf = pa.load_framework_from_path('CoreFoundation')
        print('Loaded fndatn, cf', flush=True)
        NSString = pa.objc_getClass(b'NSString')
        print('objc_getClass NSString', flush=True)
        nstring = pa.send_message(c_void_p(pa.send_message(NSString, b'alloc')), b'initWithUTF8String:', b'Hello, World!', restype=c_void_p, argtypes=(c_char_p,))
        print('Instantiated NSString', flush=True)
        cfn_at(fndatn(b'NSLog').value, None, c_void_p)(nstring)


if __name__ == '__main__':
    sys.exit(main())
