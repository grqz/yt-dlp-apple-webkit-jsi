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
    addressof,
    byref,
    c_bool,
    c_byte,
    c_char, c_char_p,
    c_double, c_float,
    c_int, c_int16, c_int32, c_int64, c_int8,
    c_long, c_longdouble, c_longlong,
    c_short,
    c_size_t, c_ssize_t,
    c_ubyte,
    c_uint, c_uint16, c_uint32, c_uint64, c_uint8,
    c_ulong, c_ulonglong, c_ushort,
    c_void_p,
    c_wchar, c_wchar_p,
    cast,
    sizeof,
)
from ctypes.util import find_library
from functools import wraps
from typing import Any, Callable, Generator, Iterable, Optional, Protocol, TypeVar, Union, overload, cast as py_typecast

from .logging import Logger


T = TypeVar('T')


def setup_signature(c_fn, restype: Optional[type] = None, *argtypes: type):
    c_fn.argtypes = argtypes
    c_fn.restype = restype
    return c_fn


def cfn_at(addr: int, restype: Optional[type] = None, *argtypes: type, logger: Logger) -> Callable:
    argss = ', '.join(str(t) for t in argtypes)
    logger.debug_log(f'Casting function pointer {addr} to {restype}(*)({argss})')
    return CFUNCTYPE(restype, *argtypes)(addr)


class DLError(OSError):
    __slots__ = ()
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


class NotNull_VoidP(Protocol):
    @property
    def value(self) -> int: ...


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
    def dlsym_factory(path: bytes, mode: int = os.RTLD_LAZY, *, logger: Logger) -> Generator[DLSYM_FUNC, None, None]:
        logger.debug_log(f'will dlopen {path.decode()}')
        h_lib = DLError.handle(
            fn_dlopen(path, mode),
            b'dlopen', path.decode(), fn_dlerror())
        try:
            yield DLError.wrap(fn_dlsym, b'dlsym', fn_dlerror, c_void_p(h_lib), success_handle=lambda x: c_void_p((lambda x: logger.debug_log(f'dlsym@{x}', ret=x))(x)))
        finally:
            logger.debug_log(f'will dlclose {path.decode()}')
            DLError.handle(
                not fn_dlclose(h_lib),
                b'dlclose', path.decode(), fn_dlerror())
    return dlsym_factory


class objc_super(Structure):
    _fields_ = (
        ('receiver', c_void_p),
        ('super_class', c_void_p),
    )
    __slots__ = ()


class CRet:
    Boolean = type[c_bool]
    Py_Boolean = bool

    Char = type[c_char]
    Py_Char = bytes

    Str = type[c_wchar]
    Py_Str = str

    _IntegralBase = Union[
        type[c_byte], type[c_ubyte], type[c_short], type[c_ushort], type[c_int], type[c_int8],
        type[c_int16], type[c_int32], type[c_int64], type[c_uint], type[c_uint8], type[c_uint16],
        type[c_uint32], type[c_uint64], type[c_long], type[c_ulong], type[c_longlong], type[c_ulonglong],
        type[c_size_t], type[c_ssize_t],
    ]
    if sys.version_info >= (3, 12):
        from ctypes import c_time_t
        Integral = Union[_IntegralBase, type[c_time_t]]
    else:
        Integral = _IntegralBase
    Py_Integral = int

    CharSeq = type[c_char_p]
    Py_CharSeq = Optional[bytes]

    StrSeq = type[c_wchar_p]
    Py_StrSeq = Optional[str]

    PVoid = type[c_void_p]
    Py_PVoid = Optional[int]

    Float = Union[type[c_float], type[c_double], type[c_longdouble]]
    Py_Float = float


NULLABLE_VOIDP = Union[NotNull_VoidP, c_void_p]


class PyNeApple:
    __slots__ = (
        '_stack', 'dlsym_of_lib', '_fwks', '_init', 'logger',
        '_objc', '_system',
        'p_NSConcreteMallocBlock',
        'class_addProtocol', 'class_addMethod', 'class_addIvar',
        'class_conformsToProtocol', 'class_getInstanceMethod', 'class_getName',
        'class_getInstanceVariable',
        'objc_getProtocol',
        'objc_allocateClassPair', 'objc_registerClassPair', 'objc_disposeClassPair',
        'objc_getClass', 'objc_alloc', 'objc_alloc_init', 'objc_release',
        'pobjc_msgSend', 'pobjc_msgSendSuper',
        'object_getClass', 'object_getInstanceVariable', 'object_setInstanceVariable',
        'object_getIvar', 'object_setIvar',
        'method_setImplementation',
        'sel_registerName', 'sel_getName',
    )

    @staticmethod
    def path_to_framework(fwk_name: str, use_findlib: bool = False) -> Optional[str]:
        if use_findlib:
            return find_library(fwk_name)
        return f'/System/Library/Frameworks/{fwk_name}.framework/{fwk_name}'

    def __init__(self, logger: Logger):
        if platform.uname()[0] != 'Darwin':
            print('Warning: kernel is not Darwin, PyNeApple might not function correctly')
        self._init = False
        self.logger = logger

    def cfn_at(self, addr: int, restype: Optional[type] = None, *argtypes: type) -> Callable:
        return cfn_at(addr, restype, *argtypes, logger=self.logger)

    def __enter__(self):
        if self._init:
            raise RuntimeError('instance already initialized, please create a new instance')
        try:
            self._stack = ExitStack()
            self.dlsym_of_lib = dlsym_factory()
            self._fwks: dict[str, DLSYM_FUNC] = {}
            self._init = True

            self._objc = self._stack.enter_context(self.dlsym_of_lib(b'/usr/lib/libobjc.A.dylib', os.RTLD_NOW, logger=self.logger))
            self._system = self._stack.enter_context(self.dlsym_of_lib(b'/usr/lib/libSystem.B.dylib', os.RTLD_LAZY, logger=self.logger))
            self.p_NSConcreteMallocBlock = self._system(b'_NSConcreteMallocBlock').value

            self.class_addProtocol = self.cfn_at(self._objc(b'class_addProtocol').value, c_byte, c_void_p, c_void_p)
            self.class_addMethod = self.cfn_at(self._objc(b'class_addMethod').value, c_byte, c_void_p, c_void_p, c_void_p, c_char_p)
            self.class_addIvar = self.cfn_at(self._objc(b'class_addIvar').value, c_byte, c_void_p, c_char_p, c_size_t, c_uint8, c_char_p)
            self.class_conformsToProtocol = self.cfn_at(self._objc(b'class_conformsToProtocol').value, c_byte, c_void_p, c_void_p)
            self.class_getInstanceMethod = self.cfn_at(self._objc(b'class_getInstanceMethod').value, c_void_p, c_void_p, c_void_p)
            self.class_getName = self.cfn_at(self._objc(b'class_getName').value, c_char_p, c_void_p)
            self.class_getInstanceVariable = self.cfn_at(self._objc(b'class_getInstanceVariable').value, c_void_p, c_void_p, c_char_p)

            self.objc_getProtocol = self.cfn_at(self._objc(b'objc_getProtocol').value, c_void_p, c_char_p)
            self.objc_allocateClassPair = self.cfn_at(self._objc(b'objc_allocateClassPair').value, c_void_p, c_void_p, c_char_p, c_size_t)
            self.objc_registerClassPair = self.cfn_at(self._objc(b'objc_registerClassPair').value, None, c_void_p)
            self.objc_disposeClassPair = self.cfn_at(self._objc(b'objc_disposeClassPair').value, None, c_void_p)
            self.objc_getClass = self.cfn_at(self._objc(b'objc_getClass').value, c_void_p, c_char_p)
            self.objc_alloc = self.cfn_at(self._objc(b'objc_alloc').value, c_void_p, c_void_p)
            self.objc_alloc_init = self.cfn_at(self._objc(b'objc_alloc_init').value, c_void_p, c_void_p)
            self.objc_release = self.cfn_at(self._objc(b'objc_release').value, None, c_void_p)
            self.pobjc_msgSend = self._objc(b'objc_msgSend').value
            self.pobjc_msgSendSuper = self._objc(b'objc_msgSendSuper').value

            self.object_getClass = self.cfn_at(self._objc(b'object_getClass').value, c_void_p, c_void_p)
            self.object_getInstanceVariable = self.cfn_at(
                self._objc(b'object_getInstanceVariable').value, c_void_p,
                c_void_p, c_char_p, POINTER(c_void_p))
            self.object_setInstanceVariable = self.cfn_at(
                self._objc(b'object_setInstanceVariable').value, c_void_p,
                c_void_p, c_char_p, c_void_p)
            self.object_getIvar = self.cfn_at(self._objc(b'object_getIvar').value, c_void_p, c_void_p, c_char_p)
            self.object_setIvar = self.cfn_at(self._objc(b'object_setIvar').value, c_void_p, c_void_p, c_char_p)

            self.method_setImplementation = self.cfn_at(self._objc(b'method_setImplementation').value, c_void_p, c_void_p, c_void_p)

            self.sel_registerName = self.cfn_at(self._objc(b'sel_registerName').value, c_void_p, c_char_p)
            self.sel_getName = self.cfn_at(self._objc(b'sel_getName').value, c_char_p, c_void_p)
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
        return self._stack.enter_context(self.dlsym_of_lib(path, mode=mode, logger=self.logger))

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
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: CRet.Boolean, argtypes: tuple[type, ...], is_super: bool = False) -> CRet.Py_Boolean: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: CRet.Char, argtypes: tuple[type, ...], is_super: bool = False) -> CRet.Py_Char: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: CRet.Str, argtypes: tuple[type, ...], is_super: bool = False) -> CRet.Py_Str: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: CRet.Integral, argtypes: tuple[type, ...], is_super: bool = False) -> CRet.Py_Integral: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: CRet.CharSeq, argtypes: tuple[type, ...], is_super: bool = False) -> CRet.Py_CharSeq: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: CRet.StrSeq, argtypes: tuple[type, ...], is_super: bool = False) -> CRet.Py_StrSeq: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: CRet.PVoid, argtypes: tuple[type, ...], is_super: bool = False) -> CRet.Py_PVoid: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: CRet.Float, argtypes: tuple[type, ...], is_super: bool = False) -> CRet.Py_Float: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: type[T], argtypes: tuple[type, ...], is_super: bool = False) -> T: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype=None, argtypes: tuple[type, ...], is_super: bool = False) -> None: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: CRet.Boolean, is_super: bool = False) -> CRet.Py_Boolean: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: CRet.Char, is_super: bool = False) -> CRet.Py_Char: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: CRet.Str, is_super: bool = False) -> CRet.Py_Str: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: CRet.Integral, is_super: bool = False) -> CRet.Py_Integral: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: CRet.CharSeq, is_super: bool = False) -> CRet.Py_CharSeq: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: CRet.StrSeq, is_super: bool = False) -> CRet.Py_StrSeq: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: CRet.PVoid, is_super: bool = False) -> CRet.Py_PVoid: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: CRet.Float, is_super: bool = False) -> CRet.Py_Float: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype: type[T], is_super: bool = False) -> T: ...
    @overload
    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *, restype=None, is_super: bool = False) -> None: ...

    def send_message(self, obj: NULLABLE_VOIDP, sel_name: bytes, *args, restype: Optional[type] = None, argtypes: tuple[type, ...] = (), is_super: bool = False):
        if restype and issubclass(restype, Structure):
            raise NotImplementedError
        sel = c_void_p(self.sel_registerName(sel_name))
        self.logger.debug_log(f'SEL for {sel_name.decode()}: {sel.value}')
        if is_super:
            klass = self.object_getClass(obj)
            if not klass:
                raise ValueError(f'unexpected nil class of object at {obj.value}')
            receiver = objc_super(receiver=obj, super_class=c_void_p(klass))
            self.logger.debug_log(
                f'supercall2 {sel_name} on {receiver.super_class=}; {receiver.receiver=}; &receiver={addressof(receiver)}')
            return self.cfn_at(
                self._objc(b'objc_msgSendSuper2').value, restype,
                POINTER(objc_super), c_void_p, *argtypes)(byref(receiver), sel, *args)
            assert False, 'Guess why I\'m here'
        return self.cfn_at(self.pobjc_msgSend, restype, c_void_p, c_void_p, *argtypes)(obj, sel, *args)

    def safe_alloc_init(self, cls: NULLABLE_VOIDP) -> NotNull_VoidP:
        if obj := self.objc_alloc_init(cls):
            return py_typecast(NotNull_VoidP, c_void_p(obj))
        raise ValueError(f'Failed to alloc init object of class at {cls.value}')

    def safe_new_object(self, cls: NULLABLE_VOIDP, init_name: bytes, *args, argtypes: tuple[type, ...] = ()) -> NotNull_VoidP:
        obj = c_void_p(self.objc_alloc(cls))
        if not obj.value:
            raise RuntimeError(f'Failed to alloc object of class {cls.value}')
        obj = c_void_p(self.send_message(obj, init_name, *args, restype=c_void_p, argtypes=argtypes))
        if not obj.value:
            self.release_obj(obj)
            raise RuntimeError(f'Failed to init object of class {cls.value} with method {init_name.decode()}')
        return py_typecast(NotNull_VoidP, obj)

    def release_obj(self, obj: NULLABLE_VOIDP) -> None:
        self.logger.debug_log(f'Releasing object at {obj.value}')
        self.objc_release(obj)

    def release_on_exit(self, obj: NULLABLE_VOIDP):
        self._stack.callback(self.release_obj, obj)

    def safe_objc_getClass(self, name: bytes) -> NotNull_VoidP:
        Cls = c_void_p(self.objc_getClass(name))
        if not Cls.value:
            raise RuntimeError(f'Failed to get class {name.decode()}')
        self.logger.debug_log(f'getClass {name.decode()} = {Cls.value}')
        return py_typecast(NotNull_VoidP, Cls.value)

    def make_block(self, cb: Callable, restype: Optional[type] = None, *argtypes: type, signature: Optional[bytes] = None) -> 'ObjCBlock':
        return ObjCBlock(self, cb, restype, *argtypes, signature=signature)

    METH_LIST_TYPE = Iterable[tuple[
        CRet.Py_PVoid,  # method objc selector
        Any,  # method C impl
        CRet.Py_CharSeq,  # method objc signature
    ]]

    def safe_add_meths(self, cls: NotNull_VoidP, meth_list: METH_LIST_TYPE):
        for msel, mcimp, msig in meth_list:
            if not self.class_addMethod(cls, msel, mcimp, msig):
                mname = self.sel_getName(msel) or b''
                raise RuntimeError(f'class_addMethod failed for method {mname}')

    def safe_upd_or_add_meths(self, cls: NotNull_VoidP, meth_list: METH_LIST_TYPE):
        for msel, mcimp, msig in meth_list:
            if imeth := self.class_getInstanceMethod(cls, msel):
                if not self.method_setImplementation(imeth, mcimp):
                    mname = self.sel_getName(msel) or b''
                    raise RuntimeError(f'Failed to update the implementation for {mname}')
            else:
                if not self.class_addMethod(cls, msel, mcimp, msig):
                    mname = self.sel_getName(msel) or b''
                    raise RuntimeError(f'Failed to add implementation for {mname}')

    def safe_get_proto(self, name: bytes):
        if proto := self.objc_getProtocol(name):
            self.logger.debug_log(f'Protocol {name.decode()} at {proto}')
            return py_typecast(NotNull_VoidP, c_void_p(proto))
        raise RuntimeError(f'Failed to get protocol {name}')


    PROTO_LIST_TYPE = Iterable[NotNull_VoidP]
    def safe_add_protos(self, cls: NotNull_VoidP, proto_list: PROTO_LIST_TYPE):
        for proto in proto_list:
            if not self.class_addProtocol(cls, proto):
                raise RuntimeError(f'class_addProtocol failed for protocol at {proto.value}')

    def safe_assert_protos(self, cls: NotNull_VoidP, proto_list: PROTO_LIST_TYPE):
        for proto in proto_list:
            if not self.class_conformsToProtocol(cls, proto):
                raise RuntimeError(
                    f'class PyForeignClass_WebViewHandler already exists '
                    f'but does not conform to the protocol at {proto.value}')

    def instanceof(self, obj: NULLABLE_VOIDP, cls: NULLABLE_VOIDP) -> bool:
        return bool(self.send_message(
            obj, b'isKindOfClass:',
            cls, restype=c_byte, argtypes=(c_void_p, )))


class ObjCBlockDescBase(Structure):
    _fields_ = (
        ('reserved', c_ulong),
        ('size', c_ulong),
    )
    __slots__ = ()


class ObjCBlockDescWithSignature(ObjCBlockDescBase):
    _fields_ = (('signature', c_char_p), )
    __slots__ = ()


class ObjCBlock(Structure):
    _fields_ = (
        ('isa', c_void_p),
        ('flags', c_int),
        ('reserved', c_int),
        ('invoke', c_void_p),  # FnPtr
        ('desc', POINTER(ObjCBlockDescBase)),
    )
    __slots__ = '_invoke', '_desc'
    BLOCK_ST = struct.Struct(b'@PiiPP')
    BLOCKDESC_SIGNATURE_ST = struct.Struct(b'@LLP')
    BLOCKDESC_ST = struct.Struct(b'@LL')
    BLOCK_TYPE = b'@?'

    def __init__(self, pyneapple: PyNeApple, cb: Callable, restype: Optional[type], *argtypes: type, signature: Optional[bytes] = None):
        f = 0
        if signature:  # Empty signatures are not acceptable, they should at least be v@?
            f |= 1 << 30
            self._desc = ObjCBlockDescWithSignature(reserved=0, size=sizeof(ObjCBlock), signature=signature)
        else:
            self._desc = ObjCBlockDescBase(reserved=0, size=sizeof(ObjCBlock))
        self._invoke = CFUNCTYPE(restype, *argtypes)(cb)
        super().__init__(
            isa=pyneapple.p_NSConcreteMallocBlock,
            flags=f,
            reserved=0,
            invoke=cast(self._invoke, c_void_p),
            desc=cast(byref(self._desc), POINTER(ObjCBlockDescBase)),
        )

    def __str__(self):
        return f'<Objective-C Block of isa at {self.isa}, flags: {self.flags}, invoke() pointer at {self.invoke}>'

    def __repr__(self):
        pycbdesc = f'(for Python callback {repr(self._invoke)})' if hasattr(self, '_invoke') else '(foreign function)'
        return f'ObjcBlock{pycbdesc}<isa={self.isa}, flags={self.flags}, reserved={self.reserved}, invoke={self.invoke}, desc={self.desc}>'

    def as_pycb(self, restype: Optional[type], *argtypes: type):
        return CFUNCTYPE(restype, *argtypes)(self.invoke)

    def __hash__(self):
        return id(self)
