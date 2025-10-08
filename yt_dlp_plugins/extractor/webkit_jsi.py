import platform
from typing import Optional, cast as py_typecast

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.extractor.youtube.jsc.provider import (
    JsChallengeProviderError,
    register_provider,
    register_preference,
    JsChallengeProvider,
    JsChallengeRequest,
)

# PRIVATE API!
from yt_dlp.extractor.youtube.jsc._builtin.runtime import JsRuntimeChalBaseJCP

from ..webkit_jsi.lib.logging import AbstractLogger, DefaultLoggerImpl as Logger
from ..webkit_jsi.lib.api import WKJS_UncaughtException, WKJS_LogType
from ..webkit_jsi.lib.easy import WKJSE_Factory, WKJSE_Webview, jsres_to_log


__version__ = '0.0.2'


FACTORY_CACHE_TYPE = WKJSE_Factory
WEBVIEW_CACHE_TYPE = Optional[WKJSE_Webview]


class IEWithAttr(InfoExtractor):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__yt_dlp_plugin__apple_webkit_jsi__factory: FACTORY_CACHE_TYPE = WKJSE_Factory(Logger())
        self.__yt_dlp_plugin__apple_webkit_jsi__webview: WEBVIEW_CACHE_TYPE = None


@register_provider
class AppleWebKitJCP(JsRuntimeChalBaseJCP):
    __slots__ = ()
    PROVIDER_VERSION = __version__
    JS_RUNTIME_NAME = 'apple-webkit-jsi'
    PROVIDER_NAME = 'apple-webkit-jsi'
    BUG_REPORT_LOCATION = 'https://github.com/grqz/yt-dlp-apple-webkit-jsi/issues?q='

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.debug('<debug: Init>')
        self.logger.trace('<trace: Init>')
        self.logger.info(f'loglevel<init>: {self.logger.log_level}')
        self.ie = py_typecast(IEWithAttr, self.ie)
        if not hasattr(self.ie, '__yt_dlp_plugin__apple_webkit_jsi__factory'):
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__factory = WKJSE_Factory(py_typecast(AbstractLogger, self.logger))
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview = None

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
        if self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview is not None:
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview.__exit__(None, None, None)
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview = None
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__factory.__exit__(None, None, None)
            # the Factory class
        super().close()

    @property
    def lazy_webview(self):
        if self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview is None:
            self.logger.info('Constructing webview')
            send = self.ie.__yt_dlp_plugin__apple_webkit_jsi__factory.__enter__()
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview = wv = WKJSE_Webview(send).__enter__()
            wv.navigate_to('https://www.youtube.com/watch?v=yt-dlp-wins', '<!DOCTYPE html><html lang="en"><head><title></title></head><body></body></html>')
            self.logger.info('Webview constructed')
            return wv
        else:
            return self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview

    def _run_js_runtime(self, stdin: str, /) -> str:
        self.logger.debug('<debug: Run JS Runtime>')
        self.logger.trace('<trace: Run JS Runtime>')
        self.logger.error(f'loglevel<_run_js_runtime>: {self.logger.log_level}')
        # TODO: trace logs don't show up even with jsc_trace=true
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
        script = 'try{' + stdin + '}catch(e){console.error(e.toString(), e.stack);}'
        # script = stdin
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
