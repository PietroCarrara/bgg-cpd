import py_cui
from ui.ui import ui_push
from db.db import connect
from utils import tokenize, intersect
from .list_item import ListItem

class ExpansionInfoScreen:
    def __init__(self, ui: py_cui.PyCUI, expansion):
        self.ui = ui
        self.root = ui.create_new_widget_set(3, 3)

        self.expansion = expansion
        self.id = expansion['id']

        self.info = self.root.add_text_block(
            f"Expansion (Year: {self.expansion['year']}) 🕮",
            0,
            0,
            initial_text=expansion['description'],
            row_span = 3,
        )

        self.comments = self.root.add_text_block('Comments 💬', 0, 1, row_span=3, column_span=2)

        db = connect()

        text = ''
        total = 0
        count = 0
        for comment in db.get_by_posting('comments', 'expansion', self.id):
            if comment['rating'] != None:
                text += f"{comment['rating']}/10 - "
                total += comment['rating']
                count += 1

            text += comment['text'] + '\n\n'
        text = f'Average Rating: {total/count}\n\n{text}'

        self.comments.set_text(text)

    def apply(self):
        self.ui.set_title(f"{self.expansion['name']} (#{self.id})")
        self.ui.apply_widget_set(self.root)
