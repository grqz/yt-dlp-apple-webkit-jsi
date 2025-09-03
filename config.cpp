#include "config.h"

extern "C" {
    static inline const unsigned char szHTMLString_[] = R"HtmlcontenTT_T(<!DOCTYPE html><html lang="en"><head><title></title></head><body></body></html>)HtmlcontenTT_T";
    static inline const unsigned char szBaseURL_[] = "https://www.youtube.com/robots.txt";
    static inline const unsigned char szScript_[] = R"sz__scRRitp(
    return typeof fetch;
    )sz__scRRitp";
    const unsigned char *szHTMLString = szHTMLString_;
    const unsigned char *szBaseURL = szBaseURL_;
    const unsigned char *szScript = szScript_;
}
