def reduce_extend(a, b):
    a.extend(b)
    return a

def split(arr, length):
    start = 0
    while start < len(arr):
        yield arr[start:start+length]
        start += length
