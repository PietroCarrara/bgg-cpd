class ListItem:
    def __init__(self, value, display):
        self.value = value
        self.display = display

    def __repr__(self):
        return str(self.display)