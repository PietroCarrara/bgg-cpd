import py_cui
from db.db import connect
from ui.menu_screen import MenuScreen
from ui.ui import ui_pop, ui_push

if __name__ == '__main__':
    root = py_cui.PyCUI(3, 3)
    root._exit_key = None
    root.toggle_unicode_borders()

    ui_push(root, MenuScreen(root))
    root.start()

    # Shut down the database
    connect().close()
