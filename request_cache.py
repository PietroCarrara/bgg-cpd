import os
import re
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

    with requests.get(url) as req:
        content = req.content
        if req.ok:
            with open(filename, 'wb') as file:
                file.write(content)
        return content

def ensure_dir():
    if not os.path.exists('.cache'):
        os.mkdir('.cache')