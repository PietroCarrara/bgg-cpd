import py_cui
import ui.game_info_screen as gis
from .list_item import ListItem
from db.db import connect
from functools import reduce
from utils import tokenize, intersect, reduce_intersection
from .ui import ui_push

class GameSearchScreen():

    def __init__(self, ui: py_cui.PyCUI, mechanics = None, categories = None):
        self.categories = categories or []
        self.mechanics = mechanics or []

        self.ui = ui
        self.root = ui.create_new_widget_set(3, 3)

        self.search_box = self.root.add_text_box('Search 🔍', 0, 0)
        self.result_list = self.root.add_scroll_menu('Results 🕮', 2, 0, column_span=2)

        self.mechanics_search = self.root.add_text_box('Mechanics 🔍', 0, 1)
        self.mechanics_result = self.root.add_checkbox_menu('Mechanics 🕮', 0, 2)

        self.categories_search = self.root.add_text_box('Categories 🔍', 1, 2)
        self.categories_result = self.root.add_checkbox_menu('Categories 🕮', 2, 2)

        self.search_box.add_key_command(py_cui.keys.KEY_ENTER, self.search)
        self.mechanics_search.add_key_command(py_cui.keys.KEY_ENTER, self.search_mechanics)
        self.categories_search.add_key_command(py_cui.keys.KEY_ENTER, self.search_categories)

        self.categories_result.add_key_command(py_cui.keys.KEY_ENTER, self.select_category)
        self.mechanics_result.add_key_command(py_cui.keys.KEY_ENTER, self.select_mechanic)

        self.result_list.add_key_command(py_cui.keys.KEY_ENTER, self.select_result)

        self.current_filter = self.root.add_block_label('Current Filters 📝', 1, 0, column_span=2, center=False)

        self.update_filters_text()

    def search(self):
        db = connect()

        game_search = list(tokenize(self.search_box.get()))

        game_ids = None
        mechanics_ids = None
        categories_ids = None

        if len(game_search) > 0:
            ids = []
            for token in game_search:
                # Append array of ids
                ids.append(list(map(
                    lambda g: g['id'],
                    db.get_by_posting('games', 'word', token)
                )))

            game_ids = list(reduce(
                reduce_intersection,
                ids
            ))

        if len(self.mechanics) > 0:
            ids = []
            for mechanic_item in self.mechanics:
                mechanic_id = mechanic_item.value
                ids.append(list(map(
                    lambda tuple: tuple[0],
                    db.get_by_posting('game_mechanic', 'mechanic', mechanic_id)
                )))

            mechanics_ids = list(reduce(
                reduce_intersection,
                ids
            ))

        if len(self.categories) > 0:
            ids = []
            for category_item in self.categories:
                category_id = category_item.value
                ids.append(list(map(
                    lambda tuple: tuple[0],
                    db.get_by_posting('game_category', 'category', category_id)
                )))

            categories_ids = list(reduce(
                reduce_intersection,
                ids
            ))


        results = list(intersect(intersect(game_ids, mechanics_ids), categories_ids) or [])

        self.present_results(results)

    def present_results(self, ids):
        db = connect()

        self.result_list.clear()
        if len(ids) <= 0:
            self.result_list.add_item('No items found!')
            return

        self.ui.move_focus(self.result_list)
        for game_id in ids:
            game = db.get_by_key('games', game_id)

            item = ListItem(game, game['name'])
            self.result_list.add_item(item)

    def search_mechanics(self):
        db = connect()

        self.mechanics_result.clear()
        for mechanic in db.get_by_posting('mechanics', 'word', self.mechanics_search.get()):
            item = ListItem(mechanic['id'], mechanic['name'])
            self.mechanics_result.add_item(item)
            if is_in(self.mechanics, item):
                self.mechanics_result.mark_item_as_checked(item)

        if len(self.mechanics_result.get_item_list()) > 0:
            self.ui.move_focus(self.mechanics_result)

    def search_categories(self):
        db = connect()

        self.categories_result.clear()
        for category in db.get_by_posting('categories', 'word', self.categories_search.get()):
            item = ListItem(category['id'], category['name'])
            self.categories_result.add_item(item)
            if is_in(self.categories, item):
                self.categories_result.mark_item_as_checked(item)

        if len(self.categories_result.get_item_list()) > 0:
            self.ui.move_focus(self.categories_result)

    def update_filters_text(self):
        mechanics = ', '.join(map(str, self.mechanics))
        categories = ', '.join(map(str, self.categories))

        self.current_filter.set_title(f'Mechanics: {mechanics}\nCategories: {categories}')

    def select_category(self):
        category = self.categories_result.get()
        if category == None:
            return

        toggle_item(self.categories, category)

        self.update_filters_text()
        self.search()

    def select_mechanic(self):
        mechanic = self.mechanics_result.get()
        if mechanic == None:
            return

        toggle_item(self.mechanics, mechanic)

        self.update_filters_text()
        self.search()

    def select_result(self):
        game = self.result_list.get()
        if game == None:
            return

        ui_push(self.ui, gis.GameInfoScreen(self.ui, game.value))

    def apply(self):
        self.ui.set_title('Search Games')
        self.ui.apply_widget_set(self.root)
        self.ui.move_focus(self.search_box)
        self.search()

def is_in(arr, item):
    for i in arr:
        if i.value == item.value and i.display == item.display:
            return True

    return False

def toggle_item(arr, item):
    for i in arr:
        if i.value == item.value and i.display == item.display:
            arr.remove(i)
            return

    arr.append(item)