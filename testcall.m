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
    CFRunLoopPerformBlock(ml, kCFRunLoopDefaultMode, blk);
    CFRunLoopRun();
    fputs("main finish\n", stderr);
    return 0;
}
