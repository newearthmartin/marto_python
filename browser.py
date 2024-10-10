import logging
import atexit
from django.conf import Settings
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TargetClosedError

logger = logging.getLogger(__name__)

__playwright = None
__browser = None


def __get_playwright():
    global __playwright
    if not __playwright:
        atexit.register(__close)
        __playwright = sync_playwright().start()
    return __playwright


def __get_browser():
    global __browser
    if __browser and not __browser.is_connected():
        logger.warning('Browser is not connected')
        __browser = None
    if not __browser:
        executable_path = getattr(Settings, 'CHROMIUM_PATH', None)
        __browser = __get_playwright().chromium.launch(headless=True, executable_path=executable_path)
    return __browser


def __close():
    if __browser: __browser.close()


def __get_browser_page(page_url, wait_load=True):
    page = __get_browser().new_page()
    page.goto(page_url)
    if wait_load:
        page.wait_for_load_state('load')
    return page


def get_browser_page(page_url, wait_load=True):
    try:
        return __get_browser_page(page_url, wait_load=wait_load)
    except TargetClosedError:
        logger.warning('Browser closed, restarting')
        global __browser
        __browser = None
        return __get_browser_page(page_url, wait_load=wait_load)
