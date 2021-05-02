import os
from .btree import BTree, PersistentBTree
from .persistence import TableFile, InvertedIndexFile, GamePersist, Uint32Persist, Uint32PairPersist, TagPersist

class Database():

    def __init__(self):
        if not os.path.exists('.bgg'):
            os.mkdir('.bgg')

        self.trees = {}
        self.tables = {}
        self.postings = {}

        self.trees['games'] = PersistentBTree(31, '.bgg/games.btree', Uint32PairPersist())
        self.tables['games'] = TableFile('.bgg/games.table', GamePersist())

        self.trees['categories'] = PersistentBTree(15, '.bgg/categories.btree', Uint32PairPersist())
        self.tables['categories'] = TableFile('.bgg/categories.table', TagPersist())

        self.trees['mechanics'] = PersistentBTree(15, '.bgg/mechanics.btree', Uint32PairPersist())
        self.tables['mechanics'] = TableFile('.bgg/mechanics.table', TagPersist())

        self.tables['game_mechanic'] = TableFile('.bgg/game_mechanic.table', Uint32PairPersist())
        self.postings['game_mechanic_mechanic'] = InvertedIndexFile('.bgg/game_mechanic_mechanic', make_hash(512), Uint32Persist(), Uint32Persist(), 16)
        self.postings['game_mechanic_game'] = InvertedIndexFile('.bgg/game_mechanic_game', make_hash(512), Uint32Persist(), Uint32Persist(), 16)

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

        games_ids = BTree(self.trees['games'].order)
        self.tables['games'].delete()
        for game in games:
            index = self.tables['games'].insert(game)
            games_ids.insert(game['id'], index)
        self.trees['games'].dump(games_ids)

        mechanics_ids = BTree(self.trees['mechanics'].order)
        self.tables['mechanics'].delete()
        for mechanic in mechanics:
            index = self.tables['mechanics'].insert(mechanic)
            mechanics_ids.insert(mechanic['id'], index)
        self.trees['mechanics'].dump(mechanics_ids)

        categories_ids = BTree(self.trees['categories'].order)
        self.tables['categories'].delete()
        for category in categories:
            index = self.tables['categories'].insert(category)
            categories_ids.insert(category['id'], index)
        self.trees['categories'].dump(categories_ids)

        self.tables['game_mechanic'].delete()
        self.postings['game_mechanic_game'].delete()
        self.postings['game_mechanic_mechanic'].delete()
        for game_id, mechanic_id in game_mechanic:
            index = self.tables['game_mechanic'].insert((game_id, mechanic_id))
            self.postings['game_mechanic_game'].insert(game_id, index)
            self.postings['game_mechanic_mechanic'].insert(mechanic_id, index)

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