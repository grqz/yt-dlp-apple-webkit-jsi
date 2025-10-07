import platform
from typing import Optional

from yt_dlp.extractor.youtube.jsc.provider import (
    JsChallengeProviderError,
    register_provider,
    register_preference,
    JsChallengeProvider,
    JsChallengeRequest,
)

# PRIVATE API!
from yt_dlp.extractor.youtube.jsc._builtin.runtime import JsRuntimeChalBaseJCP

from ..webkit_jsi.lib.logging import Logger
from ..webkit_jsi.lib.api import WKJS_UncaughtException, WKJS_LogType
from ..webkit_jsi.lib.easy import WKJSE_Factory, WKJSE_Webview, jsres_to_log


__version__ = '0.0.1'


@register_provider
class AppleWebKitJCP(JsRuntimeChalBaseJCP):
    __slots__ = '_lazy_factory', '_lazy_webview'
    PROVIDER_VERSION = __version__
    JS_RUNTIME_NAME = 'apple-webkit-jsi'
    PROVIDER_NAME = 'apple-webkit-jsi'
    BUG_REPORT_LOCATION = 'https://github.com/grqz/yt-dlp-apple-webkit-jsi/issues?q='

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy_factory = WKJSE_Factory(Logger())
        self._lazy_webview: Optional[WKJSE_Webview] = None

    def is_available(self) -> bool:
        """
        Check if the provider is available (e.g. all required dependencies are available)
        This is used to determine if the provider should be used and to provide debug information.
        IMPORTANT: This method SHOULD NOT make any network requests or perform any expensive operations.
        Since this is called multiple times, we recommend caching the result.
        """
        # TODO: test version
        return platform.uname()[0] == 'Darwin'

    def close(self):
        # Optional close hook, called when YoutubeDL is closed.
        if self._lazy_webview:
            self._lazy_webview.__exit__(None, None, None)
            self._lazy_factory.__exit__(None, None, None)
        super().close()

    @property
    def lazy_webview(self):
        if self._lazy_webview is None:
            self.logger.info('Constructing webview')
            send = self._lazy_factory.__enter__()
            self._lazy_webview = WKJSE_Webview(send).__enter__()
            self._lazy_webview.navigate_to('https://www.youtube.com/watch?v=yt-dlp-wins', '<!DOCTYPE html><html lang="en"><head><title></title></head><body></body></html>')
            self.logger.info('Webview constructed')
        return self._lazy_webview

    def _run_js_runtime(self, stdin: str, /) -> str:
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

        script = 'try{' + stdin + '}catch(e){console.error(e.toString(), e.stack);}'
        # script = stdin
        # TODO: make this logger compatible with dlp's
        # with WKJSE_Factory(Logger()) as send, WKJSE_Webview(send) as webview:
        webview = self.lazy_webview
        webview.on_script_log(on_log)
        try:
            webview.execute_js(script)
        except WKJS_UncaughtException as e:
            raise JsChallengeProviderError(repr(e), False)
        self.logger.trace(f'Javascript returned {result=}, {err=}')
        if err:
            raise JsChallengeProviderError(f'Error running Apple WebKit: {err}')
        return result


@register_preference(AppleWebKitJCP)
def my_provider_preference(provider: JsChallengeProvider, requests: list[JsChallengeRequest]) -> int:
    return 500
