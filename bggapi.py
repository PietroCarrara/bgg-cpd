import xml.etree.ElementTree as xml
import html
import requests

def fetch_games(ids):
    games = []

    with requests.get(f'https://api.geekdo.com/xmlapi2/thing?type=boardgame&id={",".join(map(str, ids))}') as req:
        data = xml.fromstring(req.content)

        game = {
            'id': id,
            'categories': [],
            'mechanics': [],
            'expansions': [],
            'publishers': [],
        }

        for item in data:
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
                        game['expansions'].append(int(el.get('id')))

                    if link_type == 'boardgamepublisher':
                        game['publishers'].append(int(el.get('id')))

        games.append(game)

    return games