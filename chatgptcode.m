// IM TOO LAZY TO REWRITE CODE SO PUT CHATGPT'S BS HERE JUST TO TEST
#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>

// Keep your existing config symbols
// (expected from "config.h")
#import "config.h"

// This Objective‑C translation keeps the intent of your C code but
// uses normal ObjC APIs instead of dlsym/objc_msgSend.
// It runs without ARC (MRC). Build with -fno-objc-arc.

static volatile BOOL gDidFinish = NO;

static inline void OnCallAsyncJSComplete(id result, NSError *error) {
    fprintf(stderr, "JS Complete! idResult: %p; nserrError: %p\n", (__bridge void *)result, (__bridge void *)error);
    gDidFinish = YES;
}

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        // Basic NSString smoke test (mirrors your NSLog of an NSString created from UTF‑8)
        NSString *hello = [[NSString alloc] initWithUTF8String:"Hello, World!"]; // +1
        NSLog(@"%@", hello);
        [hello release]; // -1

        // --- Configure WKWebView ---
        WKWebViewConfiguration *config = [[WKWebViewConfiguration alloc] init]; // +1

        // Preferences: javascriptCanOpenWindowsAutomatically
        WKPreferences *prefs = [config preferences]; // not retained, owned by config
        [prefs setJavaScriptCanOpenWindowsAutomatically:YES];

        // KVC tweaks equivalent to your setValue:forKey: with kCFBooleanTrue
        // Note: These are private-ish keys; use with care.
        [prefs setValue:(id)kCFBooleanTrue forKey:@"allowFileAccessFromFileURLs"];
        [config setValue:(id)kCFBooleanTrue forKey:@"allowUniversalAccessFromFileURLs"];

        // Create an off‑screen web view (zero rect is fine for headless work)
        WKWebView *web = [[WKWebView alloc] initWithFrame:CGRectZero configuration:config]; // +1
        [config release]; // -1 (web view retains its configuration)

        // Load the provided HTML at base URL
        NSString *html = [[NSString alloc] initWithUTF8String:szHTMLString]; // +1
        NSString *base = [[NSString alloc] initWithUTF8String:szBaseURL]; // +1
        NSURL *baseURL = [[NSURL alloc] initWithString:base]; // +1
        [web loadHTMLString:html baseURL:baseURL];
        [baseURL release]; // -1
        [base release];   // -1
        [html release];   // -1

        // Prepare JavaScript and arguments
        NSString *script = [[NSString alloc] initWithUTF8String:szScript]; // +1
        NSDictionary *args = [[NSDictionary alloc] init]; // +1 (empty like your code)

        WKContentWorld *pageWorld = [WKContentWorld pageWorld];

        // Submit async JS execution
        void (^completion)(id, NSError *) = ^(id result, NSError *error) {
            OnCallAsyncJSComplete(result, error);
        }; // stack block; the API will copy it as needed

        [web callAsyncJavaScript:script
                        arguments:args
                          inFrame:nil
                   inContentWorld:pageWorld
                 completionHandler:completion];

        [args release];   // -1
        [script release]; // -1

        fprintf(stderr, "Submitted Asynchronous JS execution\n");
        fprintf(stderr, "Waiting for JS to stop\n");

        // Pump the run loop until the async callback flips the flag.
        // (Using a pthread condvar would block the runloop and stall WebKit.)
        while (!gDidFinish) {
            [[NSRunLoop currentRunLoop] runMode:NSDefaultRunLoopMode
                                     beforeDate:[NSDate dateWithTimeIntervalSinceNow:0.05]];
        }

        [web release]; // -1
        fprintf(stderr, "Freed all\n");
    }
    return 0;
}
