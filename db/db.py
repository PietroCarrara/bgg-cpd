from .database import Database

__connection = Database()

def connect():
    return Database()