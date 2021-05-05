import struct
import os
from utils import openfile

class TableFile():

    def __init__(self, filename, persist):
        self.file = openfile(filename)
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

        # Assert we got a valid positon
        assert self.file.tell() % self.persist.data_size == 0

        # Write the new item
        self.file.write(self.persist.to_bytes(item))

        return index

    def count():
        # Jump to the end
        self.file.seek(0, 2)
        # Count how many items do we have
        total = int(self.file.tell() / self.persist.data_size)

        # Assert it is an integer
        assert self.file.tell() % self.persist.data_size == 0

        return total

    def close(self):
        self.file.close()

class InvertedIndexFile():
    def __init__(self, filename, hash_key, key_persist, value_persist, block_size, allow_duplicates = False):
        self.hash_key = hash_key
        self.value_file = openfile(filename + '.dictionary')
        self.key_file = openfile(filename + '.posting')
        self.key_persist = key_persist
        self.value_persist = value_persist
        self.block_size = block_size
        self.allow_duplicates = allow_duplicates

    def insert(self, key, value):
        position = self.hash_key(key)

        file_position = position * (self.key_persist.data_size + 4)

        while True:
            self.key_file.seek(file_position)
            arr = self.key_file.read(self.key_persist.data_size)

            if len(arr) == 0:
                # Got to the end of the file and have not yet found our key.
                # Insert it here
                self.key_file.write(self.key_persist.to_bytes(key))
                value_index = self.insert_value_new(value)

                self.key_file.write(struct.pack('I', value_index))
                break
            else:
                # Check if we found our key, or if this slot is empty
                file_key = self.key_persist.from_bytes(arr)

                if file_key == key:
                    # Found our key, write the value on it's list
                    index = struct.unpack('I', self.key_file.read(4))[0]
                    self.insert_value_old(value, index)
                    break
                elif file_key == None:
                    # Our slot is empty, write the key here
                    self.key_file.seek(file_position)
                    self.key_file.write(self.key_persist.to_bytes(key))
                    value_index = self.insert_value_new(value)

                    self.key_file.write(struct.pack('I', value_index))
                    break

            file_position += self.key_persist.data_size + 4

    # Inserts a new value into the values file
    def insert_value_new(self, value):
        # Go to the end
        self.value_file.seek(0, 2)
        # Save the new list index
        index = int(self.value_file.tell() / (self.value_persist.data_size * self.block_size + 4))

        # Make sure we got a valid index
        assert self.value_file.tell() % (self.value_persist.data_size * self.block_size + 4) == 0

        # Save the value
        self.value_file.write(self.value_persist.to_bytes(value))

        # Write the rest of the values as empty
        for i in range(self.block_size - 1):
            self.value_file.write(self.value_persist.to_bytes(None))

        # Write the pointer to the next block as 0
        self.value_file.write(struct.pack('I', 0))

        return index

    def insert_value_old(self, value, index):

        while True:
            # Go to the start of the list
            self.value_file.seek(index * (self.value_persist.data_size * self.block_size + 4))

            for i in range(self.block_size):
                v = self.value_persist.from_bytes(self.value_file.read(self.value_persist.data_size))

                if v == None:
                    # Go back to the start of this slot and save the value
                    self.value_file.seek(-self.value_persist.data_size, 1)
                    self.value_file.write(self.value_persist.to_bytes(value))
                    return

                elif not self.allow_duplicates and v == value:
                    return

            # We have read the entire block and found no free slots,
            # advance to the next block
            index = struct.unpack('I', self.value_file.read(4))[0]

            if index == 0:
                # There is no next block, we must add a new one

                # Save the location of the link to the next block
                location = self.value_file.tell() - 4
                # Write the link to the new block
                index = self.insert_value_new(value)
                self.value_file.seek(location)
                self.value_file.write(struct.pack('I', index))
                return

    # Returns (position, found), where position is the byte of the
    # file where the key is located (-1 if we've hit the end of the file while searching),
    # and found is True when we've found the key, False otherwise
    def find_key(self, key):
        position = self.hash_key(key)

        file_position = position * (self.key_persist.data_size + 4)

        while True:
            self.key_file.seek(file_position)
            arr = self.key_file.read(self.key_persist.data_size)

            if len(arr) == 0:
                # Got to the end of the file and have not yet found the key.
                return -1, False
            else:
                # Check if we found our key, or if this slot is empty
                file_key = self.key_persist.from_bytes(arr)

                if file_key == key:
                    # Found our key
                    return (file_position, True)
                elif file_key == None:
                    # Empty slot, the key is not on this file
                    return (file_position, False)

            file_position += self.key_persist.data_size + 4

    def get_values(self, key):
        location, found = self.find_key(key)

        if found:
            # Read the posting index
            self.key_file.seek(location + self.key_persist.data_size)
            index = struct.unpack('I', self.key_file.read(4))[0]

            return self.get_posting_values(index)

        return []

    def get_posting_values(self, index):
        res = []

        while True:
            # Go to the start of the list
            self.value_file.seek(index * (self.value_persist.data_size * self.block_size + 4))

            for i in range(self.block_size):
                v = self.value_persist.from_bytes(self.value_file.read(self.value_persist.data_size))

                if v == None:
                    # End of the list
                    return res
                else:
                    res.append(v)

            # We have read the entire block, advance to the next block
            index = struct.unpack('I', self.value_file.read(4))[0]

            if index == 0:
                # End of the list
                return res


    def delete(self):
        self.value_file.seek(0)
        self.value_file.truncate()
        self.key_file.seek(0)
        self.key_file.truncate()

    def close(self):
        self.value_file.close()
        self.key_file.close()


class Uint32Persist:
    def __init__(self):
        self.data_size = 4
        self.pattern = 'I'

    def to_bytes(self, number):
        # We can't represent this value
        assert number != 4294967295

        if number == None:
            number = 4294967295

        return struct.pack(self.pattern, number)

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        number = struct.unpack(self.pattern, arr)[0]

        if number == 4294967295:
            return None

        return number

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

        self.data_size = 4 * 2 + self.name_limit + self.description_limit + 4 * 5
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

        game['id'], game['year'], game['name'], game['description'], game['min_players'], game['max_players'], game[
            'min_playtime'], game['max_playtime'], game['min_age'] = struct.unpack(self.pattern, arr)

        game['name'] = decode(game['name'])
        game['description'] = decode(game['description'])

        return game

class PublisherPersist():
    def __init__(self):
        self.name_limit = 128
        self.description_limit = 2048

        self.data_size = 4 + self.name_limit + self.description_limit
        self.pattern = f'I{self.name_limit}s{self.description_limit}s'

    def to_bytes(self, publisher):
        if publisher == None:
            return bytes([0] * self.data_size)

        return struct.pack(
            self.pattern,
            publisher['id'],
            limit(publisher['name'], self.name_limit),
            limit(publisher['description'], self.description_limit)
        )

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        # Check for empty value
        if sum(arr) == 0:
            return None

        publisher = {}

        publisher['id'], publisher['name'], publisher['description'] = struct.unpack(self.pattern, arr)

        publisher['name'] = decode(publisher['name'])
        publisher['description'] = decode(publisher['description'])

        return publisher

class CommentPersist():
    def __init__(self):
        self.text_limit = 512

        self.data_size = 4 + self.text_limit + 4 + 4 * 2
        self.pattern = f'I{self.text_limit}sfII'

    def to_bytes(self, comment):
        if comment == None:
            return bytes([0] * self.data_size)

        rating = comment['rating'] if comment['rating'] != None else 0

        game_id = comment['game_id']
        if game_id == None:
            game_id = 0

        expansion_id = comment['expansion_id']
        if expansion_id == None:
            expansion_id = 0

        # Make sure its a valid comment
        assert expansion_id != 0 or game_id != 0

        return struct.pack(
            self.pattern,
            comment['id'],
            limit(comment['text'], self.text_limit),
            rating,
            game_id,
            expansion_id,
        )

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        # Check for empty value
        if sum(arr) == 0:
            return None

        comment = {}

        comment['id'], comment['text'], comment['rating'], comment['game_id'], comment['expansion_id'] = struct.unpack(self.pattern, arr)

        comment['text'] = decode(comment['text'])
        if comment['rating'] == 0:
            comment['rating'] = None

        if comment['game_id'] == 0:
            comment['game_id'] = None

        if comment['expansion_id'] == 0:
            comment['expansion_id'] = None

        return comment

class ExpansionPersist():
    def __init__(self):
        self.name_limit = 128
        self.description_limit = 4096

        self.data_size = 4 + self.name_limit + self.description_limit + 4
        self.pattern = f'I{self.name_limit}s{self.description_limit}sI'

    def to_bytes(self, expansion):
        if expansion == None:
            return bytes([0] * self.data_size)

        return struct.pack(
            self.pattern,
            expansion['id'],
            limit(expansion['name'], self.name_limit),
            limit(expansion['description'], self.description_limit),
            expansion['year']
        )

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        # Check for empty value
        if sum(arr) == 0:
            return None

        expansion = {}

        expansion['id'], expansion['name'], expansion['description'], expansion['year'] = struct.unpack(self.pattern, arr)

        expansion['name'] = decode(expansion['name'])
        expansion['description'] = decode(expansion['description'])

        return expansion


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

class StringPersist():
    def __init__(self, limit):
        self.data_size = limit
        self.pattern = f"f{limit}s"

    def to_bytes(self, string):
        arr = list(string.encode('utf-8'))

        # Make sure it fits
        assert len(arr) <= self.data_size
        # Fill the remaining slots
        for i in range(self.data_size - len(arr)):
            arr.append(0)

        return bytes(arr)

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        return decode(arr)

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