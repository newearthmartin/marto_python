import logging
import atexit
from django.conf import settings
from playwright.async_api import async_playwright
from playwright._impl._errors import TargetClosedError

logger = logging.getLogger(__name__)


async def get_browser():
    global __browser
    if not __browser:
        __browser = await __get_browser()
    return __browser


async def get_browser_page(page_url, wait_load=True):
    try:
        return await __get_browser_page(page_url, wait_load=wait_load)
    except TargetClosedError:
        logger.warning('Browser closed, restarting')
        global __browser
        __browser = None
        return await __get_browser_page(page_url, wait_load=wait_load)


__playwright = None
__browser = None


async def __get_playwright():
    global __playwright
    if not __playwright:
        __playwright = await async_playwright().start()
    return __playwright


async def __get_browser():
    p = await __get_playwright()
    chromium_cdp = getattr(settings, 'CHROMIUM_CDP', None)
    if chromium_cdp:
        logger.info(f'Connecting to Chromium on {chromium_cdp}')
        return await p.chromium.connect_over_cdp(chromium_cdp)
    else:
        chromium_path = getattr(settings, 'CHROMIUM_PATH', None)
        logger.info('Creating Chromium instance' + (f' - path: {chromium_path}' if chromium_path else ''))
        return await p.chromium.launch(headless=True, executable_path=chromium_path)


async def __get_browser_page(page_url, wait_load=True):
    browser = await get_browser()
    page = await browser.new_page()
    await page.goto(page_url)
    if wait_load:
        await page.wait_for_load_state('load')
    return page
