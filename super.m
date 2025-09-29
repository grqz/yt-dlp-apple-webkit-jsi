// to be compiled with -S -masm=intel
#include <cstdio>
#import <Foundation/Foundation.h>

@interface Klass : NSObject
@end

@implementation Klass
- (instancetype) init {
    self = [super init];
    if (!self) return self;
    puts("Hello, FUCLASS!");
    return self;
}
- (void) dealloc {
    puts("Goodbye, FUCLASS!");
    [super dealloc];
}
@end

int main() {
    [[Klass init] release];
}

