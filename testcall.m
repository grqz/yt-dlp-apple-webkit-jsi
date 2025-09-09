#import <CoreFoundation/CoreFoundation.h>
#include <stdio.h>

int main() {
    void * __block ml = CFRunLoopGetMain();
    CFRunLoopPerformBlock(ml, kCFRunLoopDefaultMode, ^{
        fputs("CFRunLoopPerformBlock inner\n", stderr);
        CFRunLoopStop(ml);
    });
    CFRunLoopRun();
    fputs("main finish\n", stderr);
    return 0;
}
