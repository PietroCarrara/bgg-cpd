import os
from time import sleep
import requests
from hashlib import md5

def hash_str(string):
    return md5(bytes(string, 'utf-8')).hexdigest()

def get(url):
    ensure_dir()

    filename = f".cache/{hash_str(url)}"

    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return str(file.read())

    while True:
        with requests.get(url) as req:
            if req.ok:
                content = req.content
                with open(filename, 'wb') as file:
                    file.write(content)
                return content
            # Not ok request, await 30 seconds (this is very, very, very slow)
            sleep(30)

def ensure_dir():
    if not os.path.exists('.cache'):
        os.mkdir('.cache')