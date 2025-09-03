#import <Foundation/Foundation.h>
#import <WebKit/WebKit.h>
#import <CoreFoundation/CoreFoundation.h>
#import <CoreGraphics/CoreGraphics.h>

#include "config.h"
#include <stdio.h>
#include <pthread.h>

pthread_cond_t cv = PTHREAD_COND_INITIALIZER;
pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;
BOOL stop = NO;

static inline
void onCallAsyncJSComplete(void *idResult, void *nserrError) {
    fprintf(stderr, "JS Complete! idResult: %p; nserrError: %p\n", idResult, nserrError);
    if (!idResult) return;
    pthread_mutex_lock(&mtx);
    stop = YES;
    pthread_cond_signal(&cv);
    pthread_mutex_unlock(&mtx);
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
    [pWebview callAsyncJavaScript:psScript
        arguments:pdJsArguments
        inFrame:nil
        inContentWorld:rpPageWorld
        completionHandler:^ (id idResult, NSError *nserrError) {
            onCallAsyncJSComplete((void *)idResult, (void *)nserrError);
        }];
    [pdJsArguments release]; pdJsArguments = nil;
    [psScript release]; psScript = nil;
    NSLog(@"Submitted Asynchronous JS execution");
    NSLog(@"Waiting for JS to stop");
    // wait until completionHandler is called, so main doesn't exit early
    pthread_mutex_lock(&mtx);
    while (!stop)
        pthread_cond_wait(&cv, &mtx);
    pthread_mutex_unlock(&mtx);
    [pWebview release]; pWebview = nil;
    NSLog(@"Finished");
    pthread_mutex_destroy(&mtx);
    pthread_cond_destroy(&cv);
    return 0;
}
