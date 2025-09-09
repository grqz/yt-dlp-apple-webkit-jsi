#import <CoreFoundation/CoreFoundation.h>
#include <stdio.h>
#include "fn_to_block.h"

int main(void) {
    void * __block ml = CFRunLoopGetMain();
    void (^blk)(void) = ^{
        fputs("CFRunLoopPerformBlock inner\n", stderr);
        CFRunLoopStop(ml);
    };
    void *pblock;
    *((void **)&pblock) = blk;
    char *signature = (char *)signatureof(pblock);
    if (!signature) signature = "";
    fprintf(stderr, "signature(%s)\n", signature);

    struct Prototype_BlockBase *baseBlock = (struct Prototype_BlockBase *)[pblock copy];
    if (baseBlock->flags & (1 << 30)) {
        if (baseBlock->flags & (1 << 25))
            (((struct Prototype_BlockDescCopyDispSign *)baseBlock->desc)->signature) = "v@?";
        else
            (((struct Prototype_BlockDescSign *)baseBlock->desc)->signature) = "v@?";
    }
    ((void (*)(void *, void *, void *))CFRunLoopPerformBlock)(ml, kCFRunLoopDefaultMode, baseBlock);
    [baseBlock release];
    CFRunLoopRun();
    fputs("main finish\n", stderr);
    return 0;
}
