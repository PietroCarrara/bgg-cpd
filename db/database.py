import os
from .btree import BTree, PersistentBTree
from .persistence import TableFile, InvertedIndexFile, GamePersist, Uint32Persist, Uint32PairPersist, TagPersist, PublisherPersist, CommentPersist, ExpansionPersist


class Database():

    def __init__(self):
        if not os.path.exists('.bgg'):
            os.mkdir('.bgg')

        self.trees = {}
        self.tables = {}
        self.postings = {}

        self.trees['games'] = PersistentBTree(
            31, '.bgg/games.btree', Uint32PairPersist())
        self.tables['games'] = TableFile('.bgg/games.table', GamePersist())

        self.trees['categories'] = PersistentBTree(
            15, '.bgg/categories.btree', Uint32PairPersist())
        self.tables['categories'] = TableFile(
            '.bgg/categories.table', TagPersist())

        self.trees['mechanics'] = PersistentBTree(
            15, '.bgg/mechanics.btree', Uint32PairPersist())
        self.tables['mechanics'] = TableFile(
            '.bgg/mechanics.table', TagPersist())

        self.trees['publishers'] = PersistentBTree(
            15, '.bgg/publishers.btree', Uint32PairPersist())
        self.tables['publishers'] = TableFile(
            '.bgg/publishers.table', PublisherPersist())

        self.trees['comments'] = PersistentBTree(
            15, '.bgg/comments.btree', Uint32PairPersist())
        self.tables['comments'] = TableFile(
            '.bgg/comments.table', CommentPersist())

        self.trees['expansions'] = PersistentBTree(
            15, '.bgg/expansions.btree', Uint32PairPersist())
        self.tables['expansions'] = TableFile(
            '.bgg/expansions.table', ExpansionPersist())

        self.tables['game_mechanic'] = TableFile(
            '.bgg/game_mechanic.table', Uint32PairPersist())
        self.postings['game_mechanic_mechanic'] = InvertedIndexFile(
            '.bgg/game_mechanic_mechanic', make_hash(512), Uint32Persist(), Uint32Persist(), 16)
        self.postings['game_mechanic_game'] = InvertedIndexFile(
            '.bgg/game_mechanic_game', make_hash(512), Uint32Persist(), Uint32Persist(), 16)

    def initial_data(self,
                     games,
                     mechanics,
                     categories,
                     publishers,
                     comments,
                     expansions,
                     game_mechanic,
                     game_category,
                     game_publisher):
        # Create the base documents
        self.make_document('games', games, 'id')
        self.make_document('mechanics', mechanics, 'id')
        self.make_document('categories', categories, 'id')
        self.make_document('publishers', publishers, 'id')
        self.make_document('comments', comments, 'id')
        self.make_document('expansions', expansions, 'id')

        self.tables['game_mechanic'].delete()
        self.postings['game_mechanic_game'].delete()
        self.postings['game_mechanic_mechanic'].delete()
        for game_id, mechanic_id in game_mechanic:
            index = self.tables['game_mechanic'].insert((game_id, mechanic_id))
            self.postings['game_mechanic_game'].insert(game_id, index)
            self.postings['game_mechanic_mechanic'].insert(mechanic_id, index)

    def make_document(self, document, data, key):
        ids = BTree(self.trees[document].order)
        self.tables[document].delete()
        for element in data:
            index = self.tables[document].insert(element)
            ids.insert(element[key], index)
        self.trees[document].dump(ids)

    def get_by_key(self, table, key):
        index = self.trees[table].find(key)

        if index == None:
            return None

        return self.tables[table].load(index)

    def get_by_posting(self, posting, posting_key, key):
        res = []

        for index in self.postings[posting + '_' + posting_key].get_values(key):
            res.append(self.tables[posting].load(index))

        return res

    def close(self):
        for table in self.tables:
            self.tables[table].close()

        for tree in self.trees:
            self.trees[tree].close()

        for posting in self.postings:
            self.postings[posting].close()


def make_hash(mod):
    return lambda x: abs(hash(x)) % mod
