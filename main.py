import db_fill
import py_cui
from db.db import connect
from ui.menu_screen import MenuScreen

if __name__ == '__main__':
    root = py_cui.PyCUI(3, 3)
    root.toggle_unicode_borders()
    root.set_title('BoardGameGeek')

    MenuScreen(root).apply()
    root.start()
