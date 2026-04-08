import logging
from playwright.async_api import async_playwright
from django.conf import settings
from django.http import HttpResponse


logger = logging.getLogger(__name__)


async def render_to_pdf(html, pdf_out_file, pdf_options=None):
    chromium_path = getattr(settings, 'CHROMIUM_PATH', None)
    chromium_args = getattr(settings, 'CHROMIUM_ARGS', None)
    
    launch_options = {'headless': True}
    if chromium_path: launch_options['executable_path'] = chromium_path
    if chromium_args: launch_options['args'] = chromium_args

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

    playwright = await async_playwright().start()
    browser = None
    page = None
    try:
        browser = await playwright.chromium.launch(**launch_options)
        page = await browser.new_page()
        await page.set_content(html, wait_until='networkidle')
        await page.pdf(path=pdf_out_file, **pdf_options)
    finally:
        if page: await page.close()
        if browser: await browser.close()
        await playwright.stop()


def pdf_response(pdf_filename, contents):
    response = HttpResponse(contents, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={pdf_filename}'
    return response