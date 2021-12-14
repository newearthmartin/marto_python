import pdfkit
from django.conf import settings


def render_to_pdf(html, pdf_out_file, wkhtmltopdf_options=None):
    wkhtmltopdf_path = settings.WKHTMLTOPDF_PATH
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
    }
    if wkhtmltopdf_options:
        options.update(wkhtmltopdf_options)
    pdfkit.from_string(
        html,
        pdf_out_file,
        configuration=pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path) if wkhtmltopdf_path else None,
        options=options
    )
