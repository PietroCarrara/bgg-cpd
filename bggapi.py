import xml.etree.ElementTree as xml
import html
import requests
from bs4 import BeautifulSoup
from functools import reduce
from utils import reduce_extend, split


def fetch_games(all_ids):
    # Resulting games
    games = []

    # Counter to keep track of what batch we are currently processing
    current_batch = 0

    # How many games to fetch in a single request
    batch_size = 500

    # Number of comments we'll be fetching per request
    comments_per_page = 100

    # Per game comment limit
    comment_limit = 200

    for ids in split(all_ids, batch_size):
        page = 1
        # Set page as 0 or lower to stop fetching comments
        while page > 0:
            # Tells if each game has had all of its comments fetch
            has_fetch_all_comments = [True] * batch_size

            with requests.get(f'https://api.geekdo.com/xmlapi2/thing?type=boardgame&id={",".join(map(str, ids))}&comments=1&pagesize={comments_per_page}&page={page}') as req:
                i = 0
                data = xml.fromstring(req.content)

                for item in data:
                    
                    if page == 1:
                        game = {
                            'id': int(item.get('id')),
                            'categories': [],
                            'mechanics': [],
                            'expansions': [],
                            'publishers': [],
                            'comments': [],
                        }
                        games.append(game)
                    else:
                        game = games[current_batch * batch_size + i]

                    for el in item:
                        # Process some properties only if we are seeing this game for the first time
                        if page == 1:
                            if el.tag == 'name' and el.get('type') == 'primary':
                                game['name'] = el.get('value')

                            elif el.tag == 'description':
                                game['description'] = html.unescape(el.text)

                            elif el.tag == 'yearpublished':
                                game['year'] = int(el.get('value'))

                            elif el.tag == 'minplayers':
                                game['min_players'] = int(el.get('value'))

                            elif el.tag == 'maxplayers':
                                game['max_players'] = int(el.get('value'))

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
                                    game['mechanics'].append({
                                        'id': int(el.get('id')),
                                        'name': el.get('value'),
                                    })

                                if link_type == 'boardgameexpansion':
                                    game['expansions'].append({
                                        'id': int(el.get('id')),
                                        'game_id': game['id'],
                                    })

                                if link_type == 'boardgamepublisher':
                                    game['publishers'].append(int(el.get('id')))

                        if el.tag == 'comments':
                            total_comments = int(el.get('totalitems'))

                            # Check if there are still more comments after this page
                            if page * comments_per_page < min(total_comments, comment_limit):
                                has_fetch_all_comments[i] = False

                            for comment in el:
                                rating = comment.get('rating')
                                if rating == 'N/A':
                                    rating = 0
                                else:
                                    rating = float(rating)

                                text = comment.get('value')

                                game['comments'].append({
                                    'rating': rating,
                                    'text': text,
                                })

                    # Next game
                    i += 1

            # Check if all of the comments have been fetch
            if reduce(lambda x, y: x and y, has_fetch_all_comments):
                page = -1
            else:
                page += 1
    # Next games batch
    current_batch += 1

    return games


def fetch_games_expansions(games):
    expansions = reduce(
        reduce_extend,
        map(lambda g: g['expansions'], games)
    )

    res = []

    # Counter to keep track of what batch we are currently processing
    current_batch = 0

    # How many games to fetch in a single request
    batch_len = 500

    # Number of comments we'll be fetching per request
    comments_per_page = 100

    # Per game comment limit
    comment_limit = 200

    for exps in split(expansions, batch_len):
        page = 1

        while page > 0:
            # Tells if each expansion has had all of its comments fetch
            has_fetch_all_comments = [True] * batch_len
            
            ids = map(lambda e: e['id'], exps)

            with requests.get(f'https://api.geekdo.com/xmlapi2/thing?type=boardgameexpansion&id={",".join(map(str, ids))}&comments=1&pagesize={comments_per_page}&page={page}') as req:
                i = 0
                data = xml.fromstring(req.content)

                for item in data:
                    if page == 1:
                        expansion = {
                            'game_id': exps[i]['game_id'],
                            'id': exps[i]['id'],
                            'comments': [],
                        }
                        res.append(expansion)
                    else:
                        expansion = res[batch_len * current_batch + i]

                    for el in item:
                        # Process some information only if we're looking for the first time at this expansion
                        if page == 1:
                            if el.tag == 'name' and el.get('type') == 'primary':
                                expansion['name'] = el.get('value')

                            elif el.tag == 'description':
                                expansion['description'] = html.unescape(el.text)

                            elif el.tag == 'yearpublished':
                                expansion['year'] = int(el.get('value'))

                        if el.tag == 'comments':
                            total_comments = int(el.get('totalitems'))

                            # Check if there are still more comments after this page
                            if page * comments_per_page < min(total_comments, comment_limit):
                                has_fetch_all_comments[i] = False

                            for comment in el:
                                rating = comment.get('rating')
                                if rating == 'N/A':
                                    rating = 0
                                else:
                                    rating = float(rating)

                                text = comment.get('value')

                                expansion['comments'].append({
                                    'rating': rating,
                                    'text': text,
                                })


                    # Next expansion
                    i += 1

            # Check if all of the comments have been fetch
            if reduce(lambda x, y: x and y, has_fetch_all_comments):
                page = -1
            else:
                page += 1

        # Next expansion batch
        current_batch += 1
        
    return res


def fetch_publisher(publisher_id):

    with requests.get(f'https://boardgamegeek.com/boardgamepublisher/{publisher_id}') as res:
        doc = BeautifulSoup(res.content, 'html.parser')

        name = html.unescape(doc.find('meta', {'name': 'title'}).attrs['content'])
        desc = html.unescape(doc.find('meta', {'name': 'description'}).attrs['content'])

    return {
        'id': publisher_id,
        'name': name,
        'description': desc,
    }