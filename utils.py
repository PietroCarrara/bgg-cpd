import os
import re
from stop_words import stop_words

def reduce_extend(a, b):
    a.extend(b)
    return a

def reduce_intersection(a, b):
    b = list(b)
    for el in a:
        if el in b:
            yield el

def split(arr, length):
    start = 0
    while start < len(arr):
        yield arr[start:start+length]
        start += length

def openfile(filename):
    return open(filename, 'rb+' if os.path.exists(filename) else 'wb+')

def tokenize(string):
    string = string.lower()

    # Remove links and newlines
    string = re.sub('(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?', ' ', string)
    string = re.sub('\\n', ' ', string)

    string = re.sub('[áãà]', 'a', string)
    string = re.sub('[é]', 'e', string)
    string = re.sub('[í]', 'i', string)
    string = re.sub('[ó]', 'o', string)
    string = re.sub('[ú]', 'u', string)
    string = re.sub('[ñ]', 'n', string)
    string = re.sub('[^a-z ]', '', string)

    res = string.split(' ')

    return list(filter(lambda w: len(w) > 2 and w not in stop_words, res))