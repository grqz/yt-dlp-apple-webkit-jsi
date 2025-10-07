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
from ..webkit_jsi.lib.easy import WKJSE_Factory, WKJSE_Webview, jsres_to_log


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
            self.logger.info(f'received js message in logvchannel {ltype.name}: {args}, calling {jsres_to_log=} on it')
            str_to_log = jsres_to_log(args)
            self.logger.info(f'[JS][{ltype.name}] {str_to_log}')
            if ltype == WKJS_LogType.ERR:
                err += str_to_log
            elif ltype == WKJS_LogType.INFO:
                result += str_to_log

        script = '(()=>{const a = 3; let b = 4; function c(){return Array.from(arguments);} const d = JSON.stringify(c(a,b)); console.log([null, d])})();if(1){try{' + stdin + '}catch(e){console.error(e.toString());}}'
        # script = stdin
        # in -2860285:-2610285
        problematic = script[-2860285:-2735285]
        self.logger.info(f'started solving challenge, {len(script)=}, {problematic.encode()}')
        # TODO: cached facory/webview
        with WKJSE_Factory(Logger(debug=True)) as send, WKJSE_Webview(send) as webview:
            f = lambda x: send(7, (x, ))
            pchr, pchb='𝓏',b'5\xd8\xcf\xdc'.decode('utf-16-le')
            self.logger.debug(f'{(pchr, pchb, pchr==pchb)=}')
            assert f(pchr) and f(pchb)
            segs: list[tuple[int, int]] = []
            def _ctxof(t: tuple[int, int], n=30, e=None):
                l, h = t
                r = problematic[max(0, l - n):min(h + n, len(problematic))]
                if e:
                    r = r.encode(e)
                return r

            segstmp: list[int] = []
            def _sch(l, h):
                s = problematic
                if l==h or f(s[l:h]):
                    return
                if h-l == 1:
                    segstmp.append(l)
                    return
                m = (l+h)//2
                lhvalid, rhvalid = f(s[l:m]), f(s[m:h])
                assert not (lhvalid and rhvalid)
                if not lhvalid and not rhvalid:
                    _sch(l, m)
                    _sch(m, h)
                elif lhvalid:
                    _sch(m, h)
                else:
                    _sch(l, m)

            _sch(0, len(problematic))

            if segstmp:
                l_ch = segstmp[0]
                h_ch = segstmp[0]
                for i in sorted(segstmp)[1:]:
                    if i == h_ch + 1:
                        ...
                    else:
                        segs.append((l_ch, h_ch))
                        l_ch = i
                    h_ch = i
                segs.append((l_ch, h_ch))

                self.logger.info(f'{len(segs)} segments problematic')
                [self.logger.info(f'{t[0]=}, {t[1]=}, {_ctxof(t, 3)=}') for t in segs]
                send(7, (problematic, ))
            send(7, (script, ))
            webview.on_script_log(on_log)
            try:
                webview.execute_js(script)
            except WKJS_UncaughtException as e:
                raise JsChallengeProviderError(repr(e), False)
            self.logger.info(f'Javascript returned {result=}, {err=}')
            if err:
                raise JsChallengeProviderError(f'Error running Apple WebKit: {err}')
            return result


@register_preference(AppleWebKitJCP)
def my_provider_preference(provider: JsChallengeProvider, requests: list[JsChallengeRequest]) -> int:
    return 500
