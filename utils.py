import os
import random
import string
from threading import Timer
import yaml
import base64
from threading import Lock
import socket


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def join(loader, node):
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])


yaml.add_constructor('!join', join)

with open('config/site.yaml', 'rb') as file:
    SITE_CONFIG = {}
    INJECT_CONFIG = {}
    with open('config/common.js', "r") as jsFile:
        INJECT_CONFIG['common'] = jsFile.read()
    rules = yaml.load(file,  Loader=yaml.Loader)
    for site in rules['site']:
        SITE_CONFIG[site['origin']] = site
        with open(f"config/{site['inject']}", "r") as jsFile:
            INJECT_CONFIG[site['origin']] = jsFile.read()


def save_file(path, img_string):
    filename = f'cache/{path}'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'wb') as file:
        file.write(base64.b64decode(img_string))


def ranstr(num):
    salt = ''.join(random.sample(string.ascii_letters + string.digits, num))
    return salt


class TimerCache:
    def __init__(self):
        self.dict = {}

    def add(self, k, v):
        self.dict[k] = v

        def r():
            del self.dict[k]
        Timer(300, r).start()

    def get(self, k):
        if k in self.dict:
            return self.dict[k]
        else:
            return None


class ResultStore():
    def __init__(self):
        self.lock = Lock()
        self.items = []

    def add(self, item):
        with self.lock:
            self.items.append(item)

    def getAll(self):
        with self.lock:
            items, self.items = self.items, []
        return items
