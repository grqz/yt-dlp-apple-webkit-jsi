#ifndef FN_TO_BLOCK_H
#define FN_TO_BLOCK_H

#include <stddef.h>

#include "common.h"

#ifdef __cplusplus
extern "C" {
#endif

/* See: https://clang.llvm.org/docs/Block-ABI-Apple.html#high-level
 * https://oliver-hu.medium.com/objective-c-blocks-ins-and-outs-840a1c12fb1e
 */
struct Prototype_BlockDescBase {
    unsigned long int reserved;  /* 0 */
    unsigned long int size;  /* sizeof(BlockLiteral) */
};
struct Prototype_BlockDescCopyDispSign {
    unsigned long int reserved;  /* 0 */
    unsigned long int size;  /* sizeof(BlockLiteral) */
    void (*copy_helper)(void *dst, void *src);
    void (*dispose_helper)(void *src);
    const char *signature;
};
struct Prototype_BlockDescSign {
    unsigned long int reserved;  /* 0 */
    unsigned long int size;  /* sizeof(BlockLiteral) */
    const char *signature;
};
struct Prototype_BlockBase {
    void *isa;
    int flags;
    int reserved;  /* 0 */
    void (*invoke)(void);  /* (struct Prototype_BlockBase *self, ...) */
    struct Prototype_BlockDescBase *desc;
};
struct Prototype_FnPtrWrapperBlock {
    void *isa;
    int flags;
    int reserved;  /* 0 */
    void (*invoke)(void);  /* (struct Prototype_BlockBase *self, ...) */
    struct Prototype_BlockDescBase *desc;
    void *userData;
};
static
struct Prototype_BlockDescBase proto_bdesc = {
    0,
    sizeof(struct Prototype_FnPtrWrapperBlock)
};

static common_inline
void make_wrapper(struct Prototype_FnPtrWrapperBlock *block, void (*fnptr)(void), void *userData) {
    block->flags = 0;
    block->reserved = 0;
    block->invoke = fnptr;
    block->desc = &proto_bdesc;
    block->userData = userData;
}

static common_inline
const char *signatureof(const void *block) {
    struct Prototype_BlockBase *baseBlock = (struct Prototype_BlockBase *)block;
    return (baseBlock->flags & (1 << 30))
        ? (baseBlock->flags & (1 << 25))
        ? (((struct Prototype_BlockDescCopyDispSign *)baseBlock->desc)->signature)
        : (((struct Prototype_BlockDescSign *)baseBlock->desc)->signature)
        : NULL;
}

#ifdef __cplusplus
}
#endif

#endif
