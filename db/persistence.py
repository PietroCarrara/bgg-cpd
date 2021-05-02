import struct
import os

class TableFile():

    def __init__(self, filename, persist):
        self.file = open(filename, 'rb+' if os.path.exists(filename) else 'wb+')
        self.persist = persist

    # Loads the n-th (0-based) item of the file
    def load(self, n):
        self.file.seek(self.persist.data_size * n)

        return self.persist.from_bytes(self.file.read(self.persist.data_size))

    # Deletes all the data in the table
    def delete(self):
        self.file.seek(0)
        self.file.truncate()

    # Inserts an item and returns its 0-based index
    def insert(self, item):
        # Jump to the end
        self.file.seek(0, 2)
        # Calculate new item's index
        index = int(self.file.tell() / self.persist.data_size)
        # Write the new item
        self.file.write(self.persist.to_bytes(item))

        return index
        
    def close(self):
        self.file.close()


class Uint32PairPersist:
    def __init__(self):
        self.data_size = 4 * 2
        self.pattern = 'II'

    def to_bytes(self, obj):
        if obj == None:
            return bytes([0] * self.data_size)

        a, b = obj
        
        # Make sure we can represent this object
        assert a != 0 or b != 0
        
        return struct.pack(self.pattern, a, b)

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        pair = struct.unpack(self.pattern, arr)

        if pair == (0, 0):
            return None

        return pair


class GamePersist:
    def __init__(self):
        self.name_limit = 128
        self.description_limit = 4096
        
        self.data_size = 4 + 4 + self.name_limit + self.description_limit + 4 + 4 + 4 + 4 + 4
        self.pattern = f'II{self.name_limit}s{self.description_limit}sIIIII'

    def to_bytes(self, game):
        if game == None:
            return bytes([0] * self.data_size)

        return struct.pack(
            self.pattern,
            game['id'],
            game['year'],
            limit(game['name'], self.name_limit),
            limit(game['description'], self.description_limit),
            game['min_players'],
            game['max_players'],
            game['min_playtime'],
            game['max_playtime'],
            game['min_age']
        )

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        # Check for empty value
        if sum(arr) == 0:
            return None

        game = {}

        game['id'], game['year'], game['name'], game['description'], game['min_players'], game['max_players'], game['min_playtime'], game['max_playtime'], game['min_age'] = struct.unpack(self.pattern, arr)

        game['name'] = decode(game['name'])
        game['description'] = decode(game['description'])

        return game

class TagPersist():
    # Persists both categories and mechanics
    def __init__(self):
        self.name_limit = 32
        self.data_size = 4 + self.name_limit
        self.pattern = f'I{self.name_limit}s'

    def to_bytes(self, tag):
        if tag == None:
            return bytes([0] * self.data_size)

        return struct.pack(self.pattern, tag['id'], limit(tag['name'], self.name_limit))

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        if (sum(arr)) == 0:
            return None

        tag = {}

        tag['id'], tag['name'] = struct.unpack(self.pattern, arr)
        tag['name'] = decode(tag['name'])

        return tag

def limit(string, max_size, encoding='utf-8'):
    string = list(string)
    arr = ''.join(string).encode(encoding)

    while len(arr) > max_size:
        # Keep popping until we have a small enough string
        string.pop()
        arr = ''.join(string).encode(encoding)

    return arr

def decode(bts, encoding='utf-8'):
    index = bts.find(0)

    if index != -1:
        bts = bts[:index]

    return bts.decode(encoding)