import os
import platform
import struct
import sys

from contextlib import contextmanager, ExitStack
from ctypes import (
    CDLL,
    CFUNCTYPE,
    POINTER,
    Structure,
    c_byte, c_char_p,
    c_size_t, c_uint8,
    c_ulong, c_void_p, c_int,
    cast,
    pointer,
    sizeof,
)
from ctypes.util import find_library
from functools import wraps
from typing import Any, Callable, Generator, Optional, Type, TypeVar, overload


T = TypeVar('T')


class _DefaultTag:
    ...


@overload
def debug_log(msg: T) -> T: ...
@overload
def debug_log(msg, *, ret: T) -> T: ...


def debug_log(msg, *, ret: Any = _DefaultTag):
    sys.stdout.write(str(msg) + '\n')
    sys.stdout.flush()
    if ret is _DefaultTag:
        ret = msg
    return ret


def setup_signature(c_fn, restype: Optional[Type] = None, *argtypes: Type):
    c_fn.argtypes = argtypes
    c_fn.restype = restype
    return c_fn


def cfn_at(addr: int, restype: Optional[Type] = None, *argtypes: Type) -> Callable:
    argss = ', '.join(str(t) for t in argtypes)
    debug_log(f'Casting function pointer {addr} to {restype}(*)({argss})')
    return CFUNCTYPE(restype, *argtypes)(addr)


def as_fnptr(cb: Callable, restype: Optional[Type] = None, *argtypes: Type) -> c_void_p:
    argss = ', '.join(str(t) for t in argtypes)
    fnptr = cast(CFUNCTYPE(restype, *argtypes)(cb), c_void_p)
    debug_log(f'Casting python callable {cb} to {restype}(*)({argss}) at {fnptr.value}')
    return fnptr


class DLError(OSError):
    UNKNOWN_ERROR = b'<unknown error>'

    def __init__(self, fname: bytes, arg: str, err: Optional[bytes]) -> None:
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
    def handle(ret: Optional[int], fname: bytes, arg: str, err: Optional[bytes]) -> int:
        if not ret:
            raise DLError(fname, arg, err)
        return ret

    @staticmethod
    def wrap(fn, fname: bytes, errfn: Callable[[], Optional[bytes]], *partial, success_handle):
        return wraps(fn)(lambda *args: success_handle(DLError.handle(fn(*partial, *args), fname, ''.join(map(str, args)), errfn())))


class NotNull_VoidP(c_void_p):
    def __init__(self, value: int):
        super().__init__(value)

    @property
    def value(self) -> int:
        return super().value  # type: ignore


DLSYM_FUNC = Callable[[bytes], NotNull_VoidP]


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
        debug_log(f'will dlopen {path.decode()}')
        h_lib = DLError.handle(
            fn_dlopen(path, mode),
            b'dlopen', path.decode(), fn_dlerror())
        try:
            yield DLError.wrap(fn_dlsym, b'dlsym', fn_dlerror, c_void_p(h_lib), success_handle=lambda x: c_void_p((lambda x: debug_log(f'dlsym@{x}', ret=x))(x)))
        finally:
            debug_log(f'will dlclose {path.decode()}')
            DLError.handle(
                not fn_dlclose(h_lib),
                b'dlclose', path.decode(), fn_dlerror())
    return dlsym_factory


class objc_super(Structure):
    _fields_ = (
        ('receiver', c_void_p),
        ('super_class', c_void_p),
    )


class PyNeApple:
    __slots__ = (
        '_stack', 'dlsym_of_lib', '_fwks', '_init',
        '_objc', '_system',
        'p_NSConcreteMallocBlock',
        'class_addProtocol', 'class_addMethod', 'class_addIvar',
        'class_conformsToProtocol',
        'objc_getProtocol', 'objc_allocateClassPair', 'objc_registerClassPair',
        'objc_getClass', 'pobjc_msgSend', 'pobjc_msgSendSuper',
        'object_getClass', 'object_getInstanceVariable', 'object_setInstanceVariable',
        'sel_registerName',
    )

    @staticmethod
    def path_to_framework(fwk_name: str, use_findlib: bool = False) -> Optional[str]:
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
            self._fwks: dict[str, DLSYM_FUNC] = {}
            self._init = True

            self._objc = self._stack.enter_context(self.dlsym_of_lib(b'/usr/lib/libobjc.A.dylib', os.RTLD_NOW))
            self._system = self._stack.enter_context(self.dlsym_of_lib(b'/usr/lib/libSystem.B.dylib', os.RTLD_LAZY))
            self.p_NSConcreteMallocBlock = self._system(b'_NSConcreteMallocBlock').value

            self.class_addProtocol = cfn_at(self._objc(b'class_addProtocol').value, c_byte, c_void_p, c_void_p)
            self.class_addMethod = cfn_at(self._objc(b'class_addMethod').value, c_byte, c_void_p, c_void_p, c_void_p, c_char_p)
            self.class_addIvar = cfn_at(self._objc(b'class_addIvar').value, c_byte, c_void_p, c_char_p, c_size_t, c_uint8, c_char_p)
            self.class_conformsToProtocol = cfn_at(self._objc(b'class_conformsToProtocol').value, c_byte, c_void_p, c_void_p)

            self.objc_getProtocol = cfn_at(self._objc(b'objc_getProtocol').value, c_void_p, c_char_p)
            self.objc_allocateClassPair = cfn_at(self._objc(b'objc_allocateClassPair').value, c_void_p, c_void_p, c_char_p, c_size_t)
            self.objc_registerClassPair = cfn_at(self._objc(b'objc_registerClassPair').value, None, c_void_p)
            self.objc_getClass = cfn_at(self._objc(b'objc_getClass').value, c_void_p, c_char_p)
            self.pobjc_msgSend = self._objc(b'objc_msgSend').value
            self.pobjc_msgSendSuper = self._objc(b'objc_msgSendSuper').value

            self.object_getClass = cfn_at(self._objc(b'object_getClass').value, c_void_p, c_void_p)
            self.object_getInstanceVariable = cfn_at(
                self._objc(b'object_getInstanceVariable').value, c_void_p,
                c_void_p, c_char_p, POINTER(c_void_p))
            self.object_setInstanceVariable = cfn_at(
                self._objc(b'object_setInstanceVariable').value, c_void_p,
                c_void_p, c_char_p, c_void_p)

            self.sel_registerName = cfn_at(self._objc(b'sel_registerName').value, c_void_p, c_char_p)
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

    @property
    def dlsym_system(self):
        return self._system

    def open_dylib(self, path: bytes, mode=os.RTLD_LAZY) -> DLSYM_FUNC:
        return self._stack.enter_context(self.dlsym_of_lib(path, mode=mode))

    def load_framework_from_path(self, fwk_name: str, fwk_path: Optional[str] = None, mode=os.RTLD_LAZY) -> DLSYM_FUNC:
        if not fwk_path:
            fwk_path = PyNeApple.path_to_framework(fwk_name)
            if not fwk_path:
                raise ValueError(f'Could not find framework {fwk_name}, please provide a valid path')
        if fwk := self._fwks.get(fwk_name):
            return fwk
        ret = self._fwks[fwk_name] = self.open_dylib(fwk_path.encode(), mode)
        return ret

    @overload
    def send_message(self, obj: c_void_p, sel_name: bytes, *args, restype: Any, argtypes: tuple[Type, ...], is_super: bool = False) -> Optional[int]: ...
    @overload
    def send_message(self, obj: c_void_p, sel_name: bytes, *args, argtypes: tuple[Type, ...], is_super: bool = False) -> None: ...
    @overload
    def send_message(self, obj: c_void_p, sel_name: bytes, *args, restype: Type[c_char_p], argtypes: tuple[Type, ...], is_super: bool = False) -> Optional[bytes]: ...
    @overload
    def send_message(self, obj: c_void_p, sel_name: bytes, *, restype: Any, is_super: bool = False) -> Optional[int]: ...
    @overload
    def send_message(self, obj: c_void_p, sel_name: bytes, *, is_super: bool = False) -> None: ...
    @overload
    def send_message(self, obj: c_void_p, sel_name: bytes, *, restype: Type[c_char_p], is_super: bool = False) -> Optional[bytes]: ...

    def send_message(self, obj: c_void_p, sel_name: bytes, *args, restype: Optional[Type] = None, argtypes: tuple[Type, ...] = (), is_super: bool = False):
        sel = c_void_p(self.sel_registerName(sel_name))
        debug_log(f'SEL for {sel_name.decode()}: {sel.value}')
        if is_super:
            receiver = objc_super(receiver=obj, super_class=c_void_p(self.send_message(self.object_getClass(obj), b'superclass', restype=c_void_p)))
            cfn_at(self.pobjc_msgSendSuper, restype, objc_super, c_void_p, *argtypes)(receiver, sel, *args)
        return cfn_at(self.pobjc_msgSend, restype, c_void_p, c_void_p, *argtypes)(obj, sel, *args)

    def safe_new_object(self, cls: c_void_p, init_name: bytes = b'init', *args, argtypes: tuple[Type, ...] = ()) -> NotNull_VoidP:
        obj = c_void_p(self.send_message(cls, b'alloc', restype=c_void_p))
        if not obj.value:
            raise RuntimeError(f'Failed to alloc object of class {cls}')
        obj = c_void_p(self.send_message(obj, init_name, restype=c_void_p, *args, argtypes=argtypes))
        if not obj.value:
            self.send_message(obj, b'release')
            raise RuntimeError(f'Failed to init object of class {cls}')
        return NotNull_VoidP(obj.value)

    def release_on_exit(self, obj: c_void_p):
        self._stack.callback(lambda: self.send_message(obj, b'release'))

    def safe_objc_getClass(self, name: bytes) -> NotNull_VoidP:
        Cls = c_void_p(self.objc_getClass(name))
        if not Cls.value:
            raise RuntimeError(f'Failed to get class {name.decode()}')
        return NotNull_VoidP(Cls.value)

    def make_block(self, cb: Callable, restype: Optional[Type], *argtypes: Type, signature: Optional[bytes] = None) -> 'ObjCBlock':
        return ObjCBlock(self, cb, restype, *argtypes, signature=signature)


class ObjCBlockDescBase(Structure):
    _fields_ = (
        ('reserved', c_ulong),
        ('size', c_ulong),
    )


class ObjCBlockDescWithSignature(ObjCBlockDescBase):
    _fields_ = (('signature', c_char_p), )


class ObjCBlock(Structure):
    _fields_ = (
        ('isa', c_void_p),
        ('flags', c_int),
        ('reserved', c_int),
        ('invoke', c_void_p),  # FnPtr
        ('desc', POINTER(ObjCBlockDescBase)),
    )
    BLOCK_ST = struct.Struct(b'@PiiPP')
    BLOCKDESC_SIGNATURE_ST = struct.Struct(b'@LLP')
    BLOCKDESC_ST = struct.Struct(b'@LL')
    BLOCK_TYPE = b'@?'

    def __init__(self, pyneapple: PyNeApple, cb: Callable, restype: Optional[Type], *argtypes: Type, signature: Optional[bytes] = None):
        f = 0
        if signature:  # Empty signatures are not acceptable, they should at least be v@?
            f |= 1 << 30
            self._desc = ObjCBlockDescWithSignature(reserved=0, size=sizeof(ObjCBlock), signature=signature)
        else:
            self._desc = ObjCBlockDescBase(reserved=0, size=sizeof(ObjCBlock))
        super().__init__(
            isa=pyneapple.p_NSConcreteMallocBlock,
            flags=f,
            reserved=0,
            invoke=as_fnptr(cb, restype, *argtypes),
            desc=cast(pointer(self._desc), POINTER(ObjCBlockDescBase)),
        )
