#include <stddef.h>
#include "fn_to_block.h"

void test_call_block_cbv_2vp(void *block_cbv_2vp, void *a, void *b) {
    ((void(^)(void *, void *))block_cbv_2vp)(a, b);
}
