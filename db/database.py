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

        self.tables['game_category'] = TableFile(
            '.bgg/game_category.table', Uint32PairPersist())
        self.postings['game_category_category'] = InvertedIndexFile(
            '.bgg/game_category_category', make_hash(512), Uint32Persist(), Uint32Persist(), 16)
        self.postings['game_category_game'] = InvertedIndexFile(
            '.bgg/game_category_game', make_hash(512), Uint32Persist(), Uint32Persist(), 16)

        self.tables['game_publisher'] = TableFile(
            '.bgg/game_publisher.table', Uint32PairPersist())
        self.postings['game_publisher_publisher'] = InvertedIndexFile(
            '.bgg/game_publisher_publisher', make_hash(512), Uint32Persist(), Uint32Persist(), 16)
        self.postings['game_publisher_game'] = InvertedIndexFile(
            '.bgg/game_publisher_game', make_hash(512), Uint32Persist(), Uint32Persist(), 16)

        self.postings['expansions_game'] = InvertedIndexFile(
            '.bgg/expansions_game', make_hash(512), Uint32Persist(), Uint32Persist(), 16)

        self.postings['comments_game'] = InvertedIndexFile(
            '.bgg/comments_game', make_hash(512), Uint32Persist(), Uint32Persist(), 16)
        self.postings['comments_expansion'] = InvertedIndexFile(
            '.bgg/comments_expansion', make_hash(512), Uint32Persist(), Uint32Persist(), 16)

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
        # Empty some indexes first
        self.postings['expansions_game'].delete()
        self.postings['comments_expansion'].delete()
        self.postings['comments_game'].delete()
        # Create the base documents
        self.make_document('games', games, 'id')
        self.make_document('mechanics', mechanics, 'id')
        self.make_document('categories', categories, 'id')
        self.make_document('publishers', publishers, 'id')
        self.make_document('comments', comments, 'id', self.comments_hook)
        self.make_document('expansions', expansions, 'id', self.expansions_hook)
        # Create the N-N relations
        self.make_relation('game', 'mechanic', game_mechanic)
        self.make_relation('game', 'category', game_category)
        self.make_relation('game', 'publisher', game_publisher)

    def make_document(self, document, data, key, hook=None):
        ids = BTree(self.trees[document].order)
        self.tables[document].delete()
        for element in data:
            index = self.tables[document].insert(element)
            ids.insert(element[key], index)
            if hook != None:
                hook(element, index)
        self.trees[document].dump(ids)

    def make_relation(self, entity_a, entity_b, relation_data, hook=None):
        rel_name = entity_a + '_' + entity_b

        self.tables[rel_name].delete()
        self.postings[rel_name + '_' + entity_a].delete()
        self.postings[rel_name + '_' + entity_b].delete()

        for data_a, data_b in relation_data:
            index = self.tables[rel_name].insert((data_a, data_b))
            self.postings[rel_name + '_' + entity_a].insert(data_a, index)
            self.postings[rel_name + '_' + entity_b].insert(data_b, index)
            if hook != None:
                hook(data_a, data_b, index)

    def expansions_hook(self, expansion, index):
        self.postings['expansions_game'].insert(expansion['game_id'], index)

    def comments_hook(self, comment, index):
        if comment['game_id'] != None:
            self.postings['comments_game'].insert(comment['game_id'], index)
        elif comment['expansion_id'] != None:
            self.postings['comments_expansion'].insert(comment['expansion_id'], index)
        else:
            raise Exception('Invalid comment found!')

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
