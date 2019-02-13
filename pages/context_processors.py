from marto_python.pages.models import Pagina
from marto_python.util import is_site_view
from marto_python.context_processors import site_view_only


@site_view_only
def page(request):
    path = request.path
    if not is_site_view(path):
        return {}
    pg = None
    try:
        pg = Pagina.objects.get(url=path)
    except Pagina.DoesNotExist:
        pass
    return {'page': pg}
