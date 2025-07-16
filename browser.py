import time
import logging
from django.conf import settings
from asgiref.sync import sync_to_async
from playwright.async_api import async_playwright
from playwright._impl import _errors as playwright_errors
from marto_python.strings import first_line


logger = logging.getLogger(__name__)


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


async def new_page(browser, page_func):
    context = None
    page = None
    try:
        context = await browser.new_context()
        page = await context.new_page()
        return await page_func(page)
    finally:
        if page: await page.close()
        if context: await context.close()


async def run_on_page(browser, page_url, page_func, logger_extra=None):
    async def fn(page):
        response = await page_goto(page, page_url, logger_extra=logger_extra)
        if response.status != 200: return None
        await page.wait_for_load_state('load')
        return await page_func(page)
    return await new_page(browser, fn)


async def browser_gc(browser, logger_extra=None):
    async def run_fn(page):
        return await page.evaluate('if (window.gc) {gc(); true;} else {false;}')
    gc = await new_page(browser, run_fn)
    if not gc:
        logger.warning('Browser gc not available', extra=logger_extra)
    return gc


async def page_goto(page, url, logger_extra=None):
    logger.info(f'Opening page {url}', extra=logger_extra)
    response = await page.goto(url, timeout=getattr(settings, 'PLAYWRIGHT_TIMEOUT', None))
    if response.status != 200: logger.warning(f'HTTP status {response.status} on {url}', extra=logger_extra)
    return response


async def catch_browser_errors(run_fn, retry=True, logger_extra=None):
    logger_error = sync_to_async(logger.error)

    async def retry_fn():
        time.sleep(5)
        return await catch_browser_errors(run_fn, retry=False, logger_extra=logger_extra)

    retry_msg = ' - Retrying' if retry else ''
    try:
        return await run_fn()
    except playwright_errors.TargetClosedError:
        logger.warning(f'Browser closed!{retry_msg}', extra=logger_extra)
        return await retry_fn() if retry else None
    except playwright_errors.TimeoutError:
        logger.warning(f'Timeout on page', extra=logger_extra)
        return None
    except playwright_errors.Error as e:
        if 'net::ERR_ABORTED' in e.message:
            logger.warning(f'Browser connection aborted!{retry_msg}', extra=logger_extra)
            return await retry_fn() if retry else None
        elif 'ECONNREFUSED' in e.message:
            logger.warning(f'Browser connection refused!{retry_msg}', extra=logger_extra)
            return await retry_fn() if retry else None
        elif 'Target page, context or browser has been closed' in e.message:
            logger.warning(f'Browser/context/page closed!{retry_msg}', extra=logger_extra)
            return await retry_fn() if retry else None
        elif 'net::ERR_SSL_VERSION_OR_CIPHER_MISMATCH' in e.message:
            log_msg = e.message.split('Call log:')[0].strip()
            logger.warning(log_msg, extra=logger_extra)
            return None
        elif 'net::ERR_NAME_NOT_RESOLVED' in e.message:
            logger.warning(first_line(e.message), extra=logger_extra)
            return None
        elif 'Browser.new_context' in e.message:
            logger.warning(e.message + retry_msg, extra=logger_extra)
            return await retry_fn() if retry else None
        elif 'BrowserContext.__exit__' in e.message:
            logger.warning(e.message, extra=logger_extra)
            return None
        else:
            await logger_error(f'Unexpected Playwright.Error - type: {type(e)} - msg: {e.message}', extra=logger_extra)
            return None
    except BaseException as e:
        str_e = str(e)
        if 'connect_over_cdp' in str_e:
            logger.warning(str_e + retry_msg, extra=logger_extra)
            return await retry_fn() if retry else None
        elif 'Connection closed' in str_e:
            logger.warning(str_e + retry_msg, extra=logger_extra)
            return await retry_fn() if retry else None
        else:
            await logger_error(f'Unexpected playwright BaseException - type: {type(e)} - str: {str_e}', extra=logger_extra)
            return None


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
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
