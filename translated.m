#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>
#import <CoreFoundation/CoreFoundation.h>
#import <CoreGraphics/CoreGraphics.h>

#include "config.h"
#include "fn_to_block.h"
#include <stdio.h>

static inline
void onCallAsyncJSComplete(void *idResult, void *nserrError, void *stop, void *getmain) {
    fprintf(stderr, "JS Complete! idResult: %p; nserrError: %p\n", idResult, nserrError);
    NSLog(@"idResult of type %@", NSStringFromClass([(id)idResult class]));
    if ([(id)idResult isKindOfClass:[NSNumber class]]) {
        fprintf(stderr, "%s\n", [[idResult stringValue] UTF8String]);
    }
    ((void(*)(void *))stop)(((void *(*)(void))getmain)());
    // CFRunLoopStop(CFRunLoopGetMain());
}

int main(void) {
    WKWebViewConfiguration *pCfg = [[WKWebViewConfiguration alloc] init];
    void *pPref = [pCfg preferences];
    [pPref setJavaScriptCanOpenWindowsAutomatically:YES];
    NSString *psSetKey = [[NSString alloc] initWithUTF8String:"allowFileAccessFromFileURLs"];
    [pPref setValue:kCFBooleanTrue forKey:psSetKey];
    [psSetKey release]; psSetKey = nil;
    pPref = nil;
    psSetKey = [[NSString alloc] initWithUTF8String:"allowUniversalAccessFromFileURLs"];
    [pCfg setValue:kCFBooleanTrue forKey:psSetKey];
    [psSetKey release]; psSetKey = nil;
    WKWebView *pWebview = [[WKWebView alloc] initWithFrame:CGRectZero configuration:pCfg];
    [pCfg release]; pCfg = nil;

    NSString *psHTMLString = [[NSString alloc] initWithUTF8String:szHTMLString];
    NSString *psBaseURL = [[NSString alloc] initWithUTF8String:szBaseURL];
    NSURL *pnurlBaseURL = [[NSURL alloc] initWithString:psBaseURL];
    [pWebview loadHTMLString:psHTMLString baseURL:pnurlBaseURL];
    [pnurlBaseURL release]; pnurlBaseURL = nil;
    [psBaseURL release]; psBaseURL = nil;
    [psHTMLString release]; psHTMLString = nil;
    NSLog(@"Set up WKWebView");

    NSString *psScript = [[NSString alloc] initWithUTF8String:szScript];
    NSDictionary *pdJsArguments = [[NSDictionary alloc] init];
    void *rpPageWorld = [WKContentWorld pageWorld];
    void *__block stop = &CFRunLoopStop, *__block getmain = &CFRunLoopGetMain;
    void (^completionHandler)(id, NSError *) = ^(id idResult, NSError *nserrError) {
        onCallAsyncJSComplete((void *)idResult, (void *)nserrError, stop, getmain);
    };
    [pWebview callAsyncJavaScript:psScript
        arguments:pdJsArguments
        inFrame:nil
        inContentWorld:rpPageWorld
        completionHandler:completionHandler];
    const char *signature = signatureof(completionHandler);
    if (!signature) signature = "";
    fputs("block signature: ", stderr);
    while (1) {
        unsigned char c = *(signature++);
        fputc("0123456789abcdef"[c & 0xf], stderr);
        fputc("0123456789abcdef"[c >> 4], stderr);
        if (!c) break;
        fputc(' ', stderr);
    }
    fputc('\n', stderr);
    NSLog(@"Submitted asynchronous JS execution, waiting for JS to stop");
    // wait until completionHandler is called, so main doesn't exit early
    CFRunLoopRun();
    [pdJsArguments release]; pdJsArguments = nil;
    [psScript release]; psScript = nil;
    [pWebview release]; pWebview = nil;
    NSLog(@"Finished");
    return 0;
}
