import py_cui

from .game_search_screen import GameSearchScreen

class MenuScreen:
    def __init__(self, ui: py_cui.PyCUI):
        self.ui = ui
        self.root = ui.create_new_widget_set(3, 3)

        self.menu = self.root.add_scroll_menu('Operation Selection', 0, 0, row_span=3, column_span=3)
        self.menu.add_item_list([
            '1. Search Games',
            '2. Search Publishers',
        ])
        self.menu.add_key_command(py_cui.keys.KEY_ENTER, self.select_operation)

    def apply(self):
        self.ui.apply_widget_set(self.root)
        self.ui.move_focus(self.menu)

    def select_operation(self):
        option = self.menu.get_selected_item_index()

        if option == 0:
            GameSearchScreen(self.ui).apply()
