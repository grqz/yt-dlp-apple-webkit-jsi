from typing import cast as py_typecast

from yt_dlp.extractor.youtube.jsc.provider import (
    JsChallengeProviderError,
    register_provider,
    register_preference,
    JsChallengeProvider,
    JsChallengeRequest,
)

# PRIVATE API! Keep an eye on upstream changes
from yt_dlp.extractor.youtube.jsc._builtin.runtime import JsRuntimeChalBaseJCP

from .webkit_jsi import AppleWebKitMixin, _IEWithAttr
from ..webkit_jsi.lib.logging import AbstractLogger
from ..webkit_jsi.lib.api import WKJS_UncaughtException, WKJS_LogType
from ..webkit_jsi.lib.easy import jsres_to_log


@register_provider
class AppleWebKitJCP(AppleWebKitMixin['AppleWebKitJCP'], JsRuntimeChalBaseJCP):
    __slots__ = ()
    JS_RUNTIME_NAME = AppleWebKitMixin.PROVIDER_NAME

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ie = py_typecast(_IEWithAttr, self.ie)
        self.logger = py_typecast(AbstractLogger, self.logger)
        self._try_init_factory()

    def _run_js_runtime(self, stdin: str, /) -> str:
        self.logger.trace(f'solving challenge, script length: {len(stdin)}')
        result = ''
        err = ''

        def on_log(msg):
            nonlocal result, err
            assert isinstance(msg, dict)
            ltype, args = WKJS_LogType(msg['logType']), msg['argsArr']
            str_to_log = jsres_to_log(*args)
            self.logger.trace(f'[JS][{ltype.name}] {str_to_log}')
            if ltype == WKJS_LogType.ERR:
                err += str_to_log
            elif ltype == WKJS_LogType.INFO:
                result += str_to_log

        # the default exception handler doesn't let you see the stacktrace
        # script = 'try{' + stdin + '}catch(e){console.error(e.toString(), e.stack.toString());}'
        script = stdin
        webview = self._get_webview_lazy()
        webview.on_script_log(on_log)
        try:
            webview.execute_js(script, r'/*__ACTUAL_SCRIPT_CONTENT_PLACEHOLDER__*/')
        except WKJS_UncaughtException as e:
            raise JsChallengeProviderError(repr(e), False)
        self.logger.trace(f'Javascript returned {result=}, {err=}')
        if err:
            raise JsChallengeProviderError(f'Error running Apple WebKit: {err}')
        return result


@register_preference(AppleWebKitJCP)
def apple_webkit_jcp_preference(provider: JsChallengeProvider, requests: list[JsChallengeRequest]) -> int:
    return 500
