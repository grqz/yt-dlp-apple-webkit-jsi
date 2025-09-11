import ctypes
import mmap
import os
import typing

lc = ctypes.CDLL(None, use_errno=True)

psize = os.sysconf('SC_PAGE_SIZE')
pmask = ~(psize - 1)

code = (
    b'\x20\x00\x00\x8b'  # ADD x0, x1, x0
    b'\x00\xa8\x00\x91'  # ADD x0, x0, #0x2a
    b'\xc0\x03\x5f\xd6'  # RET
)
# https://shell-storm.org/online/Online-Assembler-and-Disassembler/?inst=ADD+x0%2C+x1%2C+x0%0D%0AADD+x0%2C+x0%2C+%230x2a%0D%0ARET%0D%0A&arch=arm64&as_format=python#assembly

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
