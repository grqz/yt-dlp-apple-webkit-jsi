from .pyneapple_objc import PyNeApple, debug_log
from .run import CGRect

with PyNeApple() as pa:
    pa.load_framework_from_path('WebKit')

    WKWebView = pa.safe_objc_getClass(b'WKWebView')

    therect = CGRect()
    p = pa.safe_new_object(WKWebView, b'initWithFrame:', therect, argtypes=(CGRect, ))
    pa.release_on_exit(p)
    debug_log(f'{p=}')

debug_log('survived')
