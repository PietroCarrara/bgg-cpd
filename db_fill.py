from game_list import game_list
from bggapi import fetch_games, fetch_games_expansions, fetch_publisher
from functools import reduce
from utils import reduce_extend
from db.db import connect

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

    mechanics = unique(reduce(
        reduce_extend,
        map(lambda g: g['mechanics'], games),
        []
    ))

    categories = unique(reduce(
        reduce_extend,
        map(lambda g: g['categories'], games),
        []
    ))

    game_mechanic = []
    for game in games:
        for mechanic in game['mechanics']:
            game_mechanic.append((game['id'], mechanic['id']))

    game_category = []
    for game in games:
        for category in game['categories']:
            game_category.append((game['id'], category['id']))

    publishers_id = unique(reduce(
        reduce_extend,
        map(lambda g: g['publishers'], games),
        []
    ))
    publishers = []
    for id in publishers_id:
        publishers.append(fetch_publisher(id))

    expansions = fetch_games_expansions(games)

    comments = []
    commentIndex = 1
    for game in games:
        for comment in game['comments']:
            comments.append({
                'id': commentIndex,
                'text': comment['text'],
                'game_id': game['id'],
                'rating': comment['rating'],
                'expansion_id': None,
            })
            commentIndex += 1
    for expansion in expansions:
        for comment in expansion['comments']:
            comments.append({
                'id': commentIndex,
                'text': comment['text'],
                'expansion_id': expansion['id'],
                'rating': comment['rating'],
                'game_id': None,
            })
            commentIndex += 1

    game_publisher = []
    for game in games:
        for publisher in game['publishers']:
            game_publisher.append((game['id'], publisher))

    db = connect()

    db.initial_data(
        games,
        mechanics,
        categories,
        publishers,
        comments,
        expansions,
        game_mechanic,
        game_category,
        game_publisher
    )