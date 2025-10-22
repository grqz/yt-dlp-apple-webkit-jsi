import os

from typing import Generic, Optional, Protocol, TypeVar
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import version_tuple

from ..webkit_jsi.lib.logging import AbstractLogger, DefaultLoggerImpl as Logger
from ..webkit_jsi.lib.easy import WKJSE_Factory, WKJSE_Webview
from ..webkit_jsi.lib.api import DarwinMinVer


__version__ = '0.0.7'


FACTORY_CACHE_TYPE = WKJSE_Factory
WEBVIEW_CACHE_TYPE = Optional[WKJSE_Webview]


class _IEWithAttr(InfoExtractor):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__yt_dlp_plugin__apple_webkit_jsi__factory: FACTORY_CACHE_TYPE = WKJSE_Factory(Logger())
        self.__yt_dlp_plugin__apple_webkit_jsi__webview: WEBVIEW_CACHE_TYPE = None


class _IECP_Proto(Protocol):
    ie: _IEWithAttr
    logger: AbstractLogger


_T = TypeVar('_T', bound=_IECP_Proto)


class AppleWebKitMixin(Generic[_T]):
    __slots__ = ()
    IS_AVAIL = True
    PROVIDER_VERSION = __version__
    PROVIDER_NAME = 'apple-webkit-jsi'
    BUG_REPORT_LOCATION = 'https://github.com/grqz/yt-dlp-apple-webkit-jsi/issues?q='

    def _try_init_factory(self: _T):
        if not hasattr(self.ie, '__yt_dlp_plugin__apple_webkit_jsi__factory'):
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__factory = WKJSE_Factory(self.logger)
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview = None

    def close(self: _T) -> None:
        # on YDL close
        if self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview is not None:
            self.logger.trace('ydl died, performing cleanup')
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview.__exit__(None, None, None)
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview = None
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__factory.__exit__(None, None, None)
            # the Factory class has assertions, don't have to reset to None

    def is_available(self: _T) -> bool:
        ures = os.uname()
        return AppleWebKitMixin.IS_AVAIL and ures.sysname == 'Darwin' and version_tuple(ures.release) >= DarwinMinVer

    def _get_webview_lazy(self: _T):
        # TODO: maybe start the construction earlier on a-shell to improve performance?
        if self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview is None:
            self.logger.info('Constructing webview')
            try:
                send = self.ie.__yt_dlp_plugin__apple_webkit_jsi__factory.__enter__()
                self.ie.__yt_dlp_plugin__apple_webkit_jsi__factory.set_logger(self.logger)
                self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview = wv = WKJSE_Webview(send).__enter__()
                # TODO: this is yt specific, move to somewhere else
                # wv.navigate_to('https://www.youtube.com/watch?v=yt-dlp-wins', '<!DOCTYPE html><html lang="en"><head><title></title></head><body></body></html>')
            except Exception:
                AppleWebKitMixin.IS_AVAIL = False
                raise
            else:
                self.logger.info('Webview constructed')
                return wv
        else:
            self.ie.__yt_dlp_plugin__apple_webkit_jsi__factory.set_logger(self.logger)
            return self.ie.__yt_dlp_plugin__apple_webkit_jsi__webview

__all__ = []
