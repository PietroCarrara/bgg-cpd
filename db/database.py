import os
from .btree import BTree, PersistentBTree
from .persistence import TableFile, GamePersist, Uint32PairPersist, TagPersist

class Database():

    def __init__(self):
        if not os.path.exists('.bgg'):
            os.mkdir('.bgg')

        self.trees = {}
        self.tables = {}

        self.trees['games'] = PersistentBTree(31, '.bgg/games.btree', Uint32PairPersist())
        self.tables['games'] = TableFile('.bgg/games.table', GamePersist())

        self.trees['categories'] = PersistentBTree(15, '.bgg/categories.btree', Uint32PairPersist())
        self.tables['categories'] = TableFile('.bgg/categories.table', TagPersist())

        self.trees['mechanics'] = PersistentBTree(15, '.bgg/mechanics.btree', Uint32PairPersist())
        self.tables['mechanics'] = TableFile('.bgg/mechanics.table', TagPersist())

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

    def get_table_by_tree(self, table, key):
        index = self.trees[table].find(key)

        if index == None:
            return None

        return self.tables[table].load(index)

    def close(self):
        for table in self.tables:
            self.tables[table].close()

        for tree in self.trees:
            self.trees[tree].close()