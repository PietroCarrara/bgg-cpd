import py_cui
import ui.publisher_info_screen as pis
from ui.ui import ui_push
from db.db import connect
from utils import tokenize, intersect
from .list_item import ListItem

class PublisherSearchScreen:
    def __init__(self, ui: py_cui.PyCUI):
        self.ui = ui
        self.root = ui.create_new_widget_set(3, 3)

        self.search_bar = self.root.add_text_box('Search 🔍', 0, 1)
        self.results = self.root.add_scroll_menu('Results 🕮', 1, 1, row_span=2)

        self.search_bar.add_key_command(py_cui.keys.KEY_ENTER, self.search)
        self.results.add_key_command(py_cui.keys.KEY_ENTER, self.select_publisher)

    def search(self):
        self.results.clear()
        self.results.add_item('No items found!')

        string = self.search_bar.get()

        if string == None:
            return

        tokens = tokenize(string)

        if len(tokens) <= 0:
            return

        db = connect()
        indexes = None

        for token in tokens:
            values = db.postings['publishers_word'].get_values(token)
            if len(values) > 0:
                indexes = list(intersect(indexes, values))

        if indexes == None or len(indexes) <= 0:
            return

        self.results.clear()
        for idx in indexes:
            publisher = db.tables['publishers'].load(idx)
            item = ListItem(publisher, publisher['name'])
            self.results.add_item(item)

        self.ui.move_focus(self.results)

    def select_publisher(self):
        publisher = self.results.get()

        if publisher == None:
            return

        ui_push(self.ui, pis.PublisherInfoScreen(self.ui, publisher.value))


    def apply(self):
        self.ui.set_title('Search Publishers')
        self.ui.apply_widget_set(self.root)
        self.ui.move_focus(self.search_bar)
