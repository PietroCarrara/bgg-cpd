from game_list import game_list
from bggapi import fetch_games, fetch_games_expansions
from functools import reduce
from utils import reduce_extend

def unique(arr):
    uniq = []

    for i in arr:
        if i in uniq:
            continue
        else:
            uniq.append(i)
            yield i


def fill():
    games = fetch_games(game_list)

    categories = unique(reduce(
        reduce_extend,
        map(lambda g: g['categories'], games)
    ))

    mechanics = unique(reduce(
        reduce_extend,
        map(lambda g: g['mechanics'], games)
    ))

    publishers_id = unique(reduce(
        reduce_extend,
        map(lambda g: g['publishers'], games)
    ))

    # TODO: Get publishers

    expansions = fetch_games_expansions(games)

    print(expansions)