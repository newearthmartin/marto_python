import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone as dt_timezone
from enum import StrEnum
from typing import Any
from django.conf import settings
from asgiref.sync import sync_to_async
from playwright.async_api import async_playwright
from playwright._impl._errors import Error as PlaywrightError
from playwright._impl._network import Response
from marto_python.strings import first_line


logger = logging.getLogger(__name__)


class BrowserFetchError(StrEnum):
    HTTP_4XX = 'http_4xx'                        # 4xx (except 429) — page not reachable / forbidden / gone
    HTTP_5XX = 'http_5xx'                        # 5xx — server error
    TOO_MANY_REQUESTS = 'too_many_requests'      # 429 — transient, treated separately from 4xx
    TIMEOUT = 'timeout'                          # navigation/operation timed out
    NETWORK = 'network'                          # DNS / SSL / cert / address unreachable / connection refused
    BROWSER_CRASH = 'browser_crash'              # browser/context/CDP died
    UNSUPPORTED_CONTENT = 'unsupported_content'  # response wasn't text/html
    UNEXPECTED_ERROR = 'unexpected_error'        # unclassified exception


@dataclass
class FetchResult:
    value: Any = None
    error: BrowserFetchError | None = None
    http_status: int | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(dt_timezone.utc))

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict:
        return {
            'value': self.value,
            'error': self.error.value if self.error else None,
            'http_status': self.http_status,
            'timestamp': int(self.timestamp.timestamp()),
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'FetchResult':
        return cls(
            value=d.get('value'),
            error=BrowserFetchError(d['error']) if d.get('error') else None,
            http_status=d.get('http_status'),
            timestamp=datetime.fromtimestamp(d['timestamp'], tz=dt_timezone.utc),
        )


def get_console_logger(logger_extra=None, text_blacklist: list[str] | None = None):
    def fn(msg):
        if msg.type == 'endGroup': return
        if text_blacklist and any(t for t in text_blacklist if t in msg.text): return
        logger.info(f'{msg.type} - {msg.text}', extra=logger_extra)
    return fn


def get_chromium(p, logger_extra=None):
    chromium_cdp = getattr(settings, 'CHROMIUM_CDP', None)
    if chromium_cdp:
        logger.debug(f'Connecting to Chromium on {chromium_cdp}', extra=logger_extra)
        return p.chromium.connect_over_cdp(chromium_cdp)
    else:
        chromium_path = getattr(settings, 'CHROMIUM_PATH', None)
        chromium_args = getattr(settings, 'CHROMIUM_ARGS', None)
        logger.debug(f'Creating Chromium instance - path: {chromium_path} - args: {chromium_args}', extra=logger_extra)
        return p.chromium.launch(headless=True, executable_path=chromium_path, args=chromium_args)


async def new_page(browser, page_func, console_listener=None, grant_permissions=None):
    context = None
    page = None
    try:
        context = await browser.new_context(bypass_csp=True)
        if grant_permissions:
            await context.grant_permissions(grant_permissions)
        page = await context.new_page()
        if console_listener: page.on('console', console_listener)
        return await page_func(page)
    finally:
        try:
            if page: await page.close()
        except BaseException as e:
            logger.warning(f'Exception while closing page: {first_line(str(e))}')
        try:
            if context: await context.close()
        except BaseException as e:
            logger.warning(f'Exception while closing context: {first_line(str(e))}')


async def run_on_page(browser, page_url, page_func, console_listener=None, log_console=False,
                      log_console_only_error=False, logger_extra=None, grant_permissions=None) -> FetchResult:
    async def fn(page):
        if log_console:
            page.on("console", lambda msg: logger.info(f"[console.{msg.type}] {msg.text}", extra=logger_extra)
                     if not log_console_only_error or msg.type == 'error' else None)
        response = await page_goto(page, page_url, logger_extra=logger_extra)
        status = response.status
        if status != 200:
            if status == 429:
                error = BrowserFetchError.TOO_MANY_REQUESTS
            elif 400 <= status < 500:
                error = BrowserFetchError.HTTP_4XX
            elif 500 <= status < 600:
                error = BrowserFetchError.HTTP_5XX
            else:
                error = BrowserFetchError.NETWORK
            return FetchResult(error=error, http_status=status)
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            logger.warning(f'Content type {content_type} not supported')
            return FetchResult(error=BrowserFetchError.UNSUPPORTED_CONTENT, http_status=status)
        await page.wait_for_load_state('load')
        value = await page_func(page) if page_func else None
        return FetchResult(value=value, http_status=status)
    return await new_page(browser, fn, console_listener=console_listener, grant_permissions=grant_permissions)


async def browser_gc(browser, logger_extra=None, console_listener=None):
    async def run_fn(page):
        return await page.evaluate('if (window.gc) {gc(); true;} else {false;}')
    gc = await new_page(browser, run_fn, console_listener=console_listener)
    if not gc:
        logger.warning('Browser gc not available', extra=logger_extra)
    return gc


async def page_goto(page, url, logger_extra=None) -> Response:
    logger.info(f'Opening page {url}', extra=logger_extra)

    responses = []
    page.on("response", lambda r: responses.append(r))

    try:
        response = await page.goto(url, timeout=getattr(settings, 'PLAYWRIGHT_TIMEOUT', None))
    except PlaywrightError as e:
        str_e = str(e)
        if 'net::ERR_BLOCKED_BY_CLIENT' in str_e:
            logger.warning(f'Exception but continuing - {first_line(str_e)}', extra=logger_extra)
            response = next(r for r in reversed(responses) if r.url == page.url)
        else:
            raise e
    if response.status != 200:
        logger.warning(f'HTTP status {response.status} on {url}', extra=logger_extra)
    return response


BROWSER_CRASH_MARKERS = [
    'net::ERR_ABORTED',
    'net::ERR_EMPTY_RESPONSE',
    'net::ERR_NETWORK_CHANGED',
    'net::ERR_CONNECTION_REFUSED',
    'Target page, context or browser has been closed',
    'connect_over_cdp',
    'Connection closed',
    'Browser.new_context',
    'BrowserContext.new_page',
    'BrowserContext.__exit__',
    'Execution context was destroyed',
    'ECONNREFUSED',
]
NETWORK_MARKERS = [
    'net::ERR_SSL_VERSION_OR_CIPHER_MISMATCH',
    'net::ERR_ADDRESS_UNREACHABLE',
    'net::ERR_NAME_NOT_RESOLVED',
    'net::ERR_CERT_COMMON_NAME_INVALID',
    'net::ERR_CERT_AUTHORITY_INVALID',
    'net::ERR_TOO_MANY_REDIRECTS',
]


def __wrap_result(result) -> FetchResult:
    return result if isinstance(result, FetchResult) else FetchResult(value=result)


async def catch_browser_errors(run_fn, retry=True, logger_extra=None) -> FetchResult:
    async def retry_fn() -> FetchResult:
        time.sleep(5)
        return await catch_browser_errors(run_fn, retry=False, logger_extra=logger_extra)

    retry_msg = ' - Retrying' if retry else ''
    logger_error = sync_to_async(logger.error)
    try:
        return __wrap_result(await run_fn())
    except BaseException as e:
        str_e = getattr(e, 'message', str(e))
        if any(m in str_e for m in BROWSER_CRASH_MARKERS):
            logger.warning(str_e + retry_msg, extra=logger_extra)
            return await retry_fn() if retry else FetchResult(error=BrowserFetchError.BROWSER_CRASH)
        elif 'Timeout' in str_e:
            logger.warning(str_e, extra=logger_extra)
            return FetchResult(error=BrowserFetchError.TIMEOUT)
        elif any(m in str_e for m in NETWORK_MARKERS):
            logger.warning(str_e, extra=logger_extra)
            return FetchResult(error=BrowserFetchError.NETWORK)
        else:
            await logger_error(f'Unexpected playwright exception - type: {type(e)} - {str_e}', extra=logger_extra, exc_info=True)
            return FetchResult(error=BrowserFetchError.UNEXPECTED_ERROR)


class AsyncBrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None

    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_value, traceback): await self.close()

    async def get_browser(self, logger_extra=None):
        await self.__check_browser(logger_extra=logger_extra)
        if not self.playwright: self.playwright = await async_playwright().start()
        if not self.browser: self.browser = await get_chromium(self.playwright, logger_extra=logger_extra)
        return self.browser

    async def __check_browser(self, logger_extra=None):
        if self.browser:
            try:
                session = await self.browser.new_browser_cdp_session()
                await session.send("Target.getTargets")
                await session.detach()
            except BaseException as e:
                logger.warning(f'Exception checking browser: {e}', extra=logger_extra)
                await self.close()

    async def close(self):
        if self.browser:
            try:
                await self.browser.close()
            except BaseException as e:
                logger.warning(f'Exception while closing browser: {first_line(str(e))}')
            self.browser = None
        if self.playwright:
            try:
                await self.playwright.stop()
            except BaseException as e:
                logger.warning(f'Exception while stopping playwright: {first_line(str(e))}')
            self.playwright = None
