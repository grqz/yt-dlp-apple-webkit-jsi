#import <Foundation/Foundation.h>
#include <stddef.h>
#include "fn_to_block.h"

void *really_makeblock_cbv_2vp(void (*fnptr)(void *, void *, void *), void *userData) {
    void (^__block block)(void *, void *) = [^(void *a, void *b) {
        fnptr((void *)block, a, b);
    } copy];
    return block;
}
