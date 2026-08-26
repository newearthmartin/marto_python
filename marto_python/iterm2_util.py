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


async def send(window, tab_id, commands, if_not_exists=True):
    tab = await get_existing_tab(window, tab_id)
    if tab and if_not_exists:
        return tab
    tab = await get_tab(window, tab_id)
    text = '\n'.join(commands)
    if text and not text.endswith('\n'): text += '\n'
    await tab.current_session.async_send_text(text)
    return tab


# ---------------------------------------------------------------------------
# panes (split views inside a single tab)
# ---------------------------------------------------------------------------

async def get_existing_pane(tab, pane_id):
    for session in tab.sessions:
        if await session.async_get_variable('user.pane_id') == pane_id:
            return session
    return None


async def set_pane_id(session, pane_id):
    await session.async_set_variable('user.pane_id', pane_id)
    await session.async_set_name(pane_id)


async def get_pane(window, tab_id, pane_id, vertical=True):
    """
    Returns (tab, session, is_new). The pane lives in the tab identified by tab_id,
    which is created if needed. vertical=True puts panes side by side (left/right),
    vertical=False stacks them (top/bottom).
    """
    tab = await get_existing_tab(window, tab_id)
    if not tab:
        tab = await window.async_create_tab()
        await set_tab_id(tab, tab_id)
        session = tab.current_session
        await set_pane_id(session, pane_id)
        return tab, session, True
    session = await get_existing_pane(tab, pane_id)
    if session:
        return tab, session, False
    # adopt a lone unlabelled session (tab created before it had named panes)
    if len(tab.sessions) == 1:
        session = tab.sessions[0]
        if not await session.async_get_variable('user.pane_id'):
            await set_pane_id(session, pane_id)
            return tab, session, True
    session = await tab.sessions[-1].async_split_pane(vertical=vertical)
    await set_pane_id(session, pane_id)
    return tab, session, True


async def send_pane(window, tab_id, pane_id, commands, vertical=True, if_not_exists=True):
    tab, session, is_new = await get_pane(window, tab_id, pane_id, vertical=vertical)
    if not is_new and if_not_exists:
        return tab, session
    text = '\n'.join(commands)
    if text and not text.endswith('\n'): text += '\n'
    await session.async_send_text(text)
    return tab, session


async def equalize_panes(connection, tab):
    """Best effort 'Window > Arrange Split Panes Evenly' on the given tab."""
    await tab.async_activate()
    for identifier in ('Arrange Split Panes Evenly', 'Window.Arrange Split Panes Evenly'):
        try:
            await iterm2.MainMenu.async_select_menu_item(connection, identifier)
            return True
        except Exception:
            continue
    return False


async def send_panes(window, tab_id, panes, vertical=True, if_not_exists=True, connection=None):
    """
    Lays out several panes side by side in one tab.
    panes: list of (pane_id, commands) tuples, created left to right (or top to bottom).
    Sequential on purpose: splitting concurrently in the same tab races on the layout.
    """
    tab = None
    for pane_id, commands in panes:
        tab, _ = await send_pane(window, tab_id, pane_id, commands,
                                 vertical=vertical, if_not_exists=if_not_exists)
    if connection and tab and len(tab.sessions) > 1:
        await equalize_panes(connection, tab)
    return tab
