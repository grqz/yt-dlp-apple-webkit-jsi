import ctypes
import mmap
import os
import typing

lc = ctypes.CDLL(None, use_errno=True)

psize = os.sysconf('SC_PAGE_SIZE')
pmask = ~(psize - 1)

code = bytes.fromhex('20 00 00 8b 00 a8 00 91 c0 03 5f d6')

alloclen = (len(code) + psize - 1) // psize * psize
print(f'{alloclen=}')
mem = mmap.mmap(-1, length=alloclen, prot=mmap.PROT_READ | mmap.PROT_WRITE, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS, offset=0)
pmem = ctypes.addressof(ctypes.c_char_p.from_buffer(mem))
mem.write(code)

lc.mprotect.argtypes = ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int
lc.mprotect.restype = ctypes.c_int
ppgstart = pmem & pmask
if lc.mprotect(ppgstart, (alloclen + pmem - ppgstart), mmap.PROT_READ | mmap.PROT_EXEC):
    errno = ctypes.get_errno()
    raise OSError(f'mprotect failed: {errno}: {os.strerror(errno)}')

fn = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64)(typing.cast(int, pmem))
print('executing')
print(f'{fn(1, 2)=}')
print(f'{fn(0, 38)=}')

lc.munmap.argtypes = ctypes.c_void_p, ctypes.c_size_t
lc.munmap.restype = ctypes.c_int
lc.munmap(pmem, alloclen)
