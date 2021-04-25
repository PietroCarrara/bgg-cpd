import xml.etree.ElementTree as xml
import html
import requests
from functools import reduce
from utils import reduce_extend, split


def fetch_games(all_ids):
    games = []

    for ids in split(all_ids, 20):
        with requests.get(f'https://api.geekdo.com/xmlapi2/thing?type=boardgame&id={",".join(map(str, ids))}') as req:
            data = xml.fromstring(req.content)

            for item in data:

                game = {
                    'id': int(item.get('id')),
                    'categories': [],
                    'mechanics': [],
                    'expansions': [],
                    'publishers': [],
                }

                for el in item:
                    if el.tag == 'name' and el.get('type') == 'primary':
                        game['name'] = el.get('value')

                    elif el.tag == 'description':
                        game['description'] = html.unescape(el.text)

                    elif el.tag == 'yearpublished':
                        game['year'] = int(el.get('value'))

                    elif el.tag == 'minplayers':
                        game['min_players'] = int(el.get('value'))

                    elif el.tag == 'maxplayers':
                        game['min_players'] = int(el.get('value'))

                    elif el.tag == 'minplaytime':
                        game['min_playtime'] = int(el.get('value'))

                    elif el.tag == 'maxplaytime':
                        game['max_playtime'] = int(el.get('value'))

                    elif el.tag == 'minage':
                        game['min_age'] = int(el.get('value'))

                    elif el.tag == 'link':
                        link_type = el.get('type')

                        if link_type == 'boardgamecategory':
                            game['categories'].append({
                                'id': int(el.get('id')),
                                'name': el.get('value'),
                            })

                        if link_type == 'boardgamemechanic':
                            game['categories'].append({
                                'id': int(el.get('id')),
                                'name': el.get('value'),
                            })

                        if link_type == 'boardgameexpansion':
                            game['expansions'].append({
                                'id': int(el.get('id')),
                                'game': game['id'],
                            })

                        if link_type == 'boardgamepublisher':
                            game['publishers'].append(int(el.get('id')))

                games.append(game)

    return games


def fetch_games_expansions(games):
    batch_len = 20

    expansions = reduce(
        reduce_extend,
        map(lambda g: g['expansions'], games)
    )

    res = []

    for exps in split(expansions, batch_len):
        i = 0
        ids = map(lambda e: e['id'], exps)

        with requests.get(f'https://api.geekdo.com/xmlapi2/thing?type=boardgameexpansion&id={",".join(map(str, ids))}') as req:
            data = xml.fromstring(req.content)

            for item in data:
                expansion = {
                    'game': exps[i]['game'],
                    'id': exps[i]['id'],
                }

                for el in item:
                    if el.tag == 'name' and el.get('type') == 'primary':
                        expansion['name'] = el.get('value')

                    elif el.tag == 'description':
                        expansion['description'] = html.unescape(el.text)

                    elif el.tag == 'yearpublished':
                        expansion['year'] = int(el.get('value'))

                res.append(expansion)

                # Next expansion
                i += 1

    return res