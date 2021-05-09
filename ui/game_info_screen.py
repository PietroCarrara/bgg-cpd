import py_cui
from .list_item import ListItem
from db.db import connect

class GameInfoScreen:

    def __init__(self, ui, game):
        self.game = game
        self.id = game['id']

        self.ui = ui
        self.root = ui.create_new_widget_set(3, 3)

        db = connect()

        self.root.add_text_block('Information', 0, 0, initial_text=self.info_text())
        self.root.add_text_block('Description', 1, 0, row_span=2, column_span=2, initial_text=game['description'])

        self.expansions = self.root.add_scroll_menu('Expansions', 0, 1, column_span=2)
        self.categories = self.root.add_scroll_menu('Categories', 1, 2)
        self.mechanics = self.root.add_scroll_menu('Mechanics', 2, 2)


        for _, cat_id in db.get_by_posting('game_category', 'game', self.id):
            category = db.get_by_key('categories', cat_id)
            item = ListItem(category, category['name'])
            self.categories.add_item(item)

        for _, mech_id in db.get_by_posting('game_mechanic', 'game', self.id):
            mechanic = db.get_by_key('mechanics', mech_id)
            item = ListItem(mechanic, mechanic['name'])
            self.mechanics.add_item(item)

        for expansion in db.get_by_posting('expansions', 'game', self.id):
            item = ListItem(expansion, expansion['name'])
            self.expansions.add_item(item)

    def info_text(self):
        players = f"{self.game['min_players']} -- {self.game['max_players']}"
        if self.game['min_players'] == self.game['max_players']:
            players = f"{self.game['min_players']}"

        time = f"{self.game['min_playtime']} -- {self.game['max_playtime']}"

        min_age = ''
        if self.game['min_age'] != 0:
            min_age = f"Min. Age:\n•{self.game['min_age']}"

        return f"""Year:
•{self.game['year']}
Players:
•{players}
Playtime:
•{time} mins
{min_age}

"""

    def apply(self):
        self.ui.set_title(f"{self.game['name']} (#{self.game['id']})")
        self.ui.apply_widget_set(self.root)
