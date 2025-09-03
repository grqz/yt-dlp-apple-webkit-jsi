#include "config.h"

extern "C" {
    static inline const unsigned char szHTMLString_[] = R"HtmlcontenTT_T(<!DOCTYPE html><html lang="en"><head><title></title></head><body></body></html>)HtmlcontenTT_T";
    static inline const unsigned char szBaseURL_[] = "https://www.youtube.com/robots.txt";
    static inline const unsigned char szScript_[] = R"sz__scRRitp(
return await(async ()=>{  // IIAFE
try{
// pot for browser, navigate to https://www.youtube.com/robots.txt first
const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36(KHTML, like Gecko)';
const GOOG_API_KEY = 'AIzaSyDyT5W0Jh49F30Pqqtyfdf7pDLFKLJoAnw';
const REQUEST_KEY = 'O43z0dpjhgX20SCx4KAo'
const YT_BASE_URL = 'https://www.youtube.com';
const GOOG_BASE_URL = 'https://jnn-pa.googleapis.com';

const resp = await fetch('https://jnn-pa.googleapis.com/$rpc/google.internal.waa.v1.Waa/Create', {method: 'POST', body: JSON.stringify([REQUEST_KEY]), headers: {
    'content-type': 'application/json+protobuf',
    'x-goog-api-key': GOOG_API_KEY,
    'x-user-agent': 'grpc-web-javascript/0.1'
}});
return await resp.text();
}catch(e) {return `ERR: ${e}`;}
})();
    )sz__scRRitp";
    const unsigned char *szHTMLString = szHTMLString_;
    const unsigned char *szBaseURL = szBaseURL_;
    const unsigned char *szScript = szScript_;
}
