import os
import re
from hashlib import md5
from utils import tokenize
from .btree import BTree, PersistentBTree
from .persistence import TableFile, InvertedIndexFile, GamePersist, Uint32Persist, Uint32PairPersist, TagPersist, PublisherPersist, CommentPersist, ExpansionPersist, StringPersist


class Database():

    def __init__(self):
        if not os.path.exists('.bgg'):
            os.mkdir('.bgg')

        self.trees = {}
        self.tables = {}
        self.postings = {}

        # Base documents
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
        # N-N Relations
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
        # Index to search for expansions by the game they expand
        self.postings['expansions_game'] = InvertedIndexFile(
            '.bgg/expansions_game', make_hash(512), Uint32Persist(), Uint32Persist(), 16)
        # Indexes to search comments by the item they comment
        self.postings['comments_game'] = InvertedIndexFile(
            '.bgg/comments_game', make_hash(512), Uint32Persist(), Uint32Persist(), 16)
        self.postings['comments_expansion'] = InvertedIndexFile(
            '.bgg/comments_expansion', make_hash(512), Uint32Persist(), Uint32Persist(), 16)
        # Indexes to search by text content
        self.postings['games_word'] = InvertedIndexFile(
            '.bgg/games_word', make_hash(1024), StringPersist(40), Uint32Persist(), 16)
        self.postings['publishers_word'] = InvertedIndexFile(
            '.bgg/publishers_word', make_hash(1024), StringPersist(40), Uint32Persist(), 16)
        self.postings['mechanics_word'] = InvertedIndexFile(
            '.bgg/mechanics_word', make_hash(1024), StringPersist(40), Uint32Persist(), 16)
        self.postings['categories_word'] = InvertedIndexFile(
            '.bgg/categories_word', make_hash(1024), StringPersist(40), Uint32Persist(), 16)


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
        for p in self.postings:
            self.postings[p].delete()
        # Create the base documents
        self.make_document('games', games, 'id', self.games_hook)
        self.make_document('mechanics', mechanics, 'id', self.mechanics_hook)
        self.make_document('categories', categories, 'id', self.categories_hook)
        self.make_document('publishers', publishers, 'id', self.publishers_hook)
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

    def games_hook(self, game, index):
        self.build_search_index('games', 'name', game, index)
        self.build_search_index('games', 'description', game, index)

    def mechanics_hook(self, mechanic, index):
        self.build_search_index('mechanics', 'name', mechanic, index)

    def categories_hook(self, category, index):
        self.build_search_index('categories', 'name', category, index)

    def publishers_hook(self, publisher, index):
        self.build_search_index('publishers', 'name', publisher, index)
        self.build_search_index('publishers', 'description', publisher, index)

    def comments_hook(self, comment, index):
        if comment['game_id'] != None:
            self.postings['comments_game'].insert(comment['game_id'], index)
        elif comment['expansion_id'] != None:
            self.postings['comments_expansion'].insert(comment['expansion_id'], index)
        else:
            raise Exception('Invalid comment found!')

    def build_search_index(self, document, key, object, index):
        for token in tokenize(object[key]):
            self.postings[document + '_word'].insert(token, index)

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
    return lambda x: int(md5(bytes(str(x), 'utf-8')).hexdigest(), 16) % mod
