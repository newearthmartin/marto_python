import logging
from django.http import HttpResponse

from marto_python.browser import AsyncBrowserManager, new_page, catch_browser_errors

logger = logging.getLogger(__name__)


async def render_to_pdf(html, pdf_options=None, logger_extra=None) -> bytes:
    default_options = {
        'format': 'A4',
        'margin': {
            'top': '0.75in',
            'right': '0.75in',
            'bottom': '0.75in',
            'left': '0.75in',
        },
        'print_background': True,
    }
    pdf_options = default_options | (pdf_options or {})

    async def make_pdf(page):
        await page.set_content(html, wait_until='networkidle')
        return await page.pdf(**pdf_options)

    async with AsyncBrowserManager() as browser_manager:
        async def fn():
            browser = await browser_manager.get_browser(logger_extra=logger_extra)
            return await new_page(browser, make_pdf)
        return await catch_browser_errors(fn, logger_extra=logger_extra)


def pdf_response(pdf_filename, contents):
    response = HttpResponse(contents, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={pdf_filename}'
    return response