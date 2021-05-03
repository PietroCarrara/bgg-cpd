from .database import Database

__connection = Database()

def connect():
    return __connection