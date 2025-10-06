import json
import platform

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
from ..webkit_jsi.lib.easy import WKJSE_Factory, WKJSE_Webview


__version__ = '0.0.1'


@register_provider
class AppleWebKitJCP(JsRuntimeChalBaseJCP):
    PROVIDER_VERSION = __version__
    JS_RUNTIME_NAME = 'apple-webkit-jsi'
    PROVIDER_NAME = 'apple-webkit-jsi'
    BUG_REPORT_LOCATION = 'https://github.com/grqz/yt-dlp-apple-webkit-jsi/issues?q='


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
        pass

    def _run_js_runtime(self, stdin: str, /) -> str:
        result = ''
        err = ''

        def on_log(msg):
            nonlocal result, err
            assert isinstance(msg, dict)
            ltype, args = WKJS_LogType(msg['logType']), msg['argsArr']
            if not args:
                return
            str_to_log = json.dumps(args[0], separators=(',', ':')) + '\n'
            self.logger.info(f'[JS][{ltype.name}] {str_to_log}')
            if ltype == WKJS_LogType.ERR:
                err += str_to_log
            elif ltype == WKJS_LogType.INFO:
                result += str_to_log

        self.logger.info(f'started solving challenge, script length: {len(stdin)}')
        # TODO: cached facory/webview
        with WKJSE_Factory(Logger(debug=True)) as send, WKJSE_Webview(send) as webview:
            webview.on_script_log(on_log)
            try:
                webview.execute_js(stdin)
            except WKJS_UncaughtException as e:
                raise JsChallengeProviderError(repr(e), False)
            self.logger.info(f'Javascript returned {result=}, {err=}')
            if err:
                raise JsChallengeProviderError(f'Error running Apple WebKit: {err}')
            return result


@register_preference(AppleWebKitJCP)
def my_provider_preference(provider: JsChallengeProvider, requests: list[JsChallengeRequest]) -> int:
    return 500
