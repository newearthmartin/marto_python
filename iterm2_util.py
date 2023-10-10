import iterm2


async def get_window(app, connection, window_name):
    if window_name:
        for window in app.windows:
            if await window.async_get_variable('user.window_id') == window_name:
                await window.async_activate()
                return window, False
    window = await iterm2.Window.async_create(connection)
    if window_name:
        await window.async_set_title(window_name)
        await window.async_set_variable('user.window_id', window_name)
    return window, True


async def get_existing_tab(window, tab_id):
    for tab in window.tabs:
        if await tab.async_get_variable('user.tab_id') == tab_id:
            return tab
    return None


async def set_tab_id(tab, tab_id):
    await tab.async_set_variable('user.tab_id', tab_id)
    await tab.async_set_title(tab_id)


async def get_tab(window, tab_id):
    tab = await get_existing_tab(window, tab_id)
    if not tab:
        tab = await window.async_create_tab()
        await set_tab_id(tab, tab_id)
    return tab


async def send(window, tab_id, text, if_not_exists=True):
    tab = await get_existing_tab(window, tab_id)
    if tab and if_not_exists:
        return tab
    tab = await get_tab(window, tab_id)
    await tab.current_session.async_send_text(text)
    return tab
