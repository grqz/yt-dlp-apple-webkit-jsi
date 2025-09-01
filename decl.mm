#import <Foundation/Foundation.h>
#include <stdio.h>
@interface MyCls : NSObject
- (void)meth;
@end

@implementation MyCls
- (void)meth {
    printf("Hello, World!\n");
}
@end

int main() {
    MyCls *obj = [[MyCls alloc] init];
    [obj meth];
    [obj release];
    return 0;
}

