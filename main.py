from bggapi import fetch_games

def unique(arr):
    uniq = []

    for i in arr:
        if i in uniq:
            continue
        else:
            uniq.append(i)
            yield i

if __name__ == '__main__':
    print(fetch_games([217372, 217372+1]))