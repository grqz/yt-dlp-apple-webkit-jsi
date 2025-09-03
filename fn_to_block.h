#ifndef FN_TO_BLOCK_H
#define FN_TO_BLOCK_H

#include <stdarg.h>

#ifdef __cplusplus
extern "C" {
#endif

// See: https://clang.llvm.org/docs/Block-ABI-Apple.html#high-level
// https://oliver-hu.medium.com/objective-c-blocks-ins-and-outs-840a1c12fb1e
struct Prototype_BlockDescBase {
    unsigned long int reserved;  // 0
    unsigned long int size;  // sizeof(struct Prototype_BlockDescBase)
} static proto_bdesc = {0, sizeof(struct Prototype_BlockDescBase)};
struct Prototype_FnPtrWrapperBlock {
    void *isa;
    int flags;
    int reserved;  // 0
    void (*invoke)();  // struct Prototype_FnPtrWrapperBlock *, ...
    struct Prototype_BlockDescBase *desc;
    void *userData;
};

static inline
void make_wrapper(struct Prototype_FnPtrWrapperBlock *block, void *fnptr, void *userData) {
    block->flags = 0;
    block->reserved = 0;
    block->invoke = fnptr;
    block->desc = &proto_bdesc;
    block->userData = userData;
}

void *really_makeblock_cbv_2vp(void (*fnptr)(void *, void *, void *), void *userData);

void test_call_block_cbv_2vp(void *block_cbv_2vp);

#ifdef __cplusplus
}
#endif

#endif
