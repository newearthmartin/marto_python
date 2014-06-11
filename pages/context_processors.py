from marto_python.pages.models import Pagina, Menu
from marto_python.util import is_site_view
from marto_python.context_processors import site_view_only


@site_view_only
def page(request):
    path = request.path
    if not is_site_view(path):
        return {}
    page = None
    try:
        page = Pagina.objects.get(url=path)
    except Pagina.DoesNotExist:
        pass
    return {'page': page}

@site_view_only
def menu(request):
    try:
        selected = request.session.get('the_menu')
        request.session['the_menu'] = None
        if not selected:
            selected = Menu.objects.get(totalUrl=request.path)
    except Menu.DoesNotExist:
        selected = None

    menus = []
    if selected:
        the_menu = selected
        while the_menu:
            siblings = []
            for menu in Menu.objects.filter(padre=the_menu.padre).order_by('indice').all():
                if selected == menu:
                    menu.selected = True
                if the_menu != selected and the_menu == menu:
                    menu.childSelected = True
                siblings.append(menu)
            menus.insert(0, siblings)
            the_menu = the_menu.padre
        children = selected.children.order_by('indice').all()
        if children:
            menus.append(children)
    else:
        menus.append(Menu.objects.filter(padre=None).order_by('indice').all())
    return {'menus' : menus}
