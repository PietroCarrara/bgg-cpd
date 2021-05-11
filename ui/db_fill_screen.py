import db_fill
import py_cui
import threading
import queue
from ui.ui import ui_push, ui_pop
from db.db import connect
from utils import tokenize, intersect
from .list_item import ListItem

class DBFillScreen:
    def __init__(self, ui: py_cui.PyCUI):
        self.ui = ui
        self.root = ui.create_new_widget_set(3, 3)

        self.queue = queue.Queue()
        self.thread = None

        self.msg = ''

        self.progress_notifier = ProgressNotifier(
            self.on_message,
            self.on_start_progress,
            self.on_progress,
            self.on_done
        )

        self.ui.set_on_draw_update_func(self.update)

    def update(self):
        while self.queue.qsize() > 0:
            signal, arg = self.queue.get()

            if signal == 'message':
                self.message(arg)

            elif signal == 'start_progress':
                self.start_progress(arg)

            elif signal == 'progress':
                self.progress()

            elif signal == 'done':
                self.done()

    def apply(self):
        self.thread = threading.Thread(target=self.fill)
        self.thread.start()

        self.ui.show_loading_icon_popup('Loading', 'Connecting to database... ')

    def done(self):
        self.queue = queue.Queue()
        self.ui.stop_loading_popup()
        ui_pop(self.ui)

    def fill(self):
        db_fill.fill(self.progress_notifier)
        self.progress_notifier.done()

    def on_message(self, msg):
        self.queue.put(('message', msg))

    def on_start_progress(self, total_items):
        # FIXME: Since the ui library won't let me tell it when we're done loading
        # and instead just assumes it knows how to do it (it doesn't), we have to
        # trick it into thinking we are never done
        self.queue.put(('start_progress', total_items + 1))

    def on_progress(self):
        self.queue.put(('progress', None))

    def on_done(self):
        self.queue.put(('done', None))

    def message(self, msg):
        self.msg = msg
        self.ui.show_message_popup('Loading...', msg)

    def start_progress(self, total_items):
        self.ui.show_loading_bar_popup(self.msg, total_items)

    def progress(self):
        self.ui.increment_loading_bar()

class ProgressNotifier:
    def __init__(self, on_message, on_start_progress, on_progress, on_done):
        self.on_message = on_message
        self.on_start_progress = on_start_progress
        self.on_progress = on_progress
        self.on_done = on_done

    def message(self, msg):
        self.on_message(msg)

    def start_progress(self, total_items):
        self.on_start_progress(total_items)

    def progress(self):
        self.on_progress()

    def done(self):
        self.on_done()