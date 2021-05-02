import os
from .btree import BTree, PersistentBTree
from .persistence import TableFile, GamePersist, Uint32PairPersist

class Database():

    def __init__(self):
        if not os.path.exists('.bgg'):
            os.mkdir('.bgg')

        self.trees = {}
        self.tables = {}

        self.trees['games'] = PersistentBTree(31, '.bgg/games.btree', Uint32PairPersist())
        self.tables['games'] = TableFile('.bgg/games.table', GamePersist())

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

        game_ids = BTree(31)

        self.tables['games'].delete()
        for game in games:
            index = self.tables['games'].insert(game)
            game_ids.insert(game['id'], index)
        self.trees['games'].dump(game_ids)

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