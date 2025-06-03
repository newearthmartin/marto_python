import logging
from django.conf import settings
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from playwright._impl import _errors as playwright_errors


logger = logging.getLogger(__name__)


def run_on_page(page_url, func, logger_extra=None):
    def run_fn():
        with sync_playwright() as p:
            with get_chromium(p) as browser:
                with browser.new_context() as context:
                    with context.new_page() as page:
                        response = open_page(page, page_url)
                        if response.status != 200: return None
                        page.wait_for_load_state('load')
                        return func(page)

    logger.info(f'Opening page - {page_url}', extra=logger_extra)
    return run_catching_errors(run_fn, logger_extra=logger_extra)


def get_chromium(p, logger_extra=None):
    chromium_cdp = getattr(settings, 'CHROMIUM_CDP', None)
    if chromium_cdp:
        logger.debug(f'Connecting to Chromium on {chromium_cdp}', extra=logger_extra)
        return p.chromium.connect_over_cdp(chromium_cdp)
    else:
        chromium_path = getattr(settings, 'CHROMIUM_PATH', None)
        logger.debug(f'Creating Chromium instance - path: {chromium_path}', extra=logger_extra)
        return p.chromium.launch(headless=True, executable_path=chromium_path)


async def async_open_page(page, url):
    response = await page.goto(url, timeout=getattr(settings, 'PLAYWRIGHT_TIMEOUT', None))
    if response.status != 200: logger.warning(f'HTTP status {response.status} on {url}')
    return response


def open_page(page, url):
    response = page.goto(url, timeout=getattr(settings, 'PLAYWRIGHT_TIMEOUT', None))
    if response.status != 200: logger.warning(f'HTTP status {response.status} on {url}')
    return response

def run_catching_errors(run_fn, retry=True, logger_extra=None):
    try:
        return run_fn()
    except playwright_errors.TargetClosedError:
        logger.warning('Browser closed! retrying once', extra=logger_extra)
        return run_fn() if retry else None
    except playwright_errors.TimeoutError:
        logger.warning(f'Timeout on page', extra=logger_extra)
        return None
    except playwright_errors.Error as e:
        if 'net::ERR_ABORTED' in e.message:
            logger.warning('Browser connection aborted! retrying once', extra=logger_extra)
            return run_fn() if retry else None
        elif 'ECONNREFUSED' in e.message:
            logger.warning('Browser connection refused! retrying once', extra=logger_extra)
            return run_fn() if retry else None
        elif 'connect_over_cdp' in e.message:
            logger.warning(f'Browser connection error! {e.message.split('\n')[0]} - retrying once', extra=logger_extra)
            return run_fn() if retry else None
        elif 'net::ERR_SSL_VERSION_OR_CIPHER_MISMATCH' in e.message:
            log_msg = e.message.split('Call log:')[0].strip()
            logger.warning(log_msg, extra=logger_extra)
            return None
        elif 'net::ERR_NAME_NOT_RESOLVED' in e.message:
            logger.warning(e.message.split('\n')[0], extra=logger_extra)
            return None
        else:
            logger.warning(f'Unexpected error in playwright - {e.message} - {str(e)} - {type(e)}', extra=logger_extra)
            raise e


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
                await self.browser.send("Target.getTargets")
            except Exception as e:
                logger.error(e,  exc_info=True, extra=logger_extra)
                await self.close()

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
