import requests
from urllib.parse import urljoin
import functools

r = requests.Session()


def make_post_request(url, data=None, headers=None):
    return r.post(url, data=data, headers=headers)


def make_get_request(url, params=None, headers=None):
    return r.get(url, params=params, headers=headers)


def join_urls(*args):
    uri = functools.reduce(lambda x, y: urljoin(x, y), args)
    return uri


if __name__ == '__main__':
    print(join_urls('http://', 'sdfs', 'sdfsdfsdfd'))