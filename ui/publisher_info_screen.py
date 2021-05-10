import py_cui
import ui.game_info_screen as gis
from ui.ui import ui_push
from db.db import connect
from utils import tokenize, intersect
from .list_item import ListItem

class PublisherInfoScreen:
    def __init__(self, ui: py_cui.PyCUI, publisher):
        self.ui = ui
        self.root = ui.create_new_widget_set(3, 3)

        self.publisher = publisher
        self.id = publisher['id']

        self.info = self.root.add_text_block('Publisher 🕮', 0, 0, initial_text=publisher['description'], row_span = 3, column_span = 2)
        self.games = self.root.add_scroll_menu('Games 🎲', 0, 2, row_span=3)

        self.games.add_key_command(py_cui.keys.KEY_ENTER, self.select_game)

        db = connect()

        for game_id, _ in db.get_by_posting('game_publisher', 'publisher', self.id):
            game = db.get_by_key('games', game_id)
            item = ListItem(game, game['name'])
            self.games.add_item(item)

    def select_game(self):
        game = self.games.get()

        if game == None:
            return

        ui_push(self.ui, gis.GameInfoScreen(self.ui, game.value))


    def apply(self):
        self.ui.set_title(f"{self.publisher['name']} (#{self.id})")
        self.ui.apply_widget_set(self.root)
