import logging
import atexit
from django.conf import settings
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TargetClosedError

logger = logging.getLogger(__name__)


def get_browser():
    global __browser
    if not __browser:
        __browser = __get_browser()
    return __browser


def get_browser_page(page_url, wait_load=True):
    try:
        return __get_browser_page(page_url, wait_load=wait_load)
    except TargetClosedError:
        logger.warning('Browser closed, restarting')
        global __browser
        __browser = None
        return __get_browser_page(page_url, wait_load=wait_load)


__playwright = None
__browser = None


def __get_playwright():
    global __playwright
    if not __playwright:
        def close():
            if __browser: __browser.close()
        atexit.register(close)
        __playwright = sync_playwright().start()
    return __playwright


def __get_browser():
    chromium_cdp = getattr(settings, 'CHROMIUM_CDP', None)
    if chromium_cdp:
        logger.info(f'Connecting to Chromium on {chromium_cdp}')
        return __get_playwright().chromium.connect_over_cdp(chromium_cdp)
    else:
        chromium_path = getattr(settings, 'CHROMIUM_PATH', None)
        logger.info('Creating Chromium instance' + (f' - path: {chromium_path}' if chromium_path else ''))
        return __get_playwright().chromium.launch(headless=True, executable_path=chromium_path)


def __get_browser_page(page_url, wait_load=True):
    page = get_browser().new_page()
    page.goto(page_url)
    if wait_load:
        page.wait_for_load_state('load')
    return page
