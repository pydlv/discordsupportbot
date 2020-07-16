import json
import shelve
from typing import Any
import os

curdir = os.path.dirname(__file__)
_real_shelve = shelve.open(os.path.join(curdir, 'data'))


class Root(object):
    def __init__(self):
        try:
            self.value = json.loads(_real_shelve["root"])
        except KeyError:
            self.value = {}

    def update_shelve(self):
        _real_shelve["root"] = json.dumps(self.value)
        _real_shelve.sync()

    def __setitem__(self, key, value):
        self.value[key] = value
        self.update_shelve()

    def __delitem__(self, key):
        del self.value[key]
        self.update_shelve()

    def __getitem__(self, item):
        return self.value[item]

    def __contains__(self, item):
        return item in self.value

    def sync(self):
        self.update_shelve()


root = Root()
_shelve = root


def safe_get(k, d):
    if k not in root:
        root[k] = d
        return d
    else:
        return root[k]


class Property(object):
    key: str
    _value: Any

    def __init__(self, key: str, default: Any):
        self.key = key
        self._value = safe_get(key, default)

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return str(self._value)

    def set(self, value: Any):
        self._value = value
        root[self.key] = self._value

    def get(self):
        return self._value

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, value: Any):
        self.set(value)


if __name__ == "__main__":
    while True:
        try:
            user_in = input("Enter JSON with keys and values you would like to change: ")

            decoded = json.loads(user_in)

            for key, value in decoded.items():
                root[key] = value

        except json.decoder.JSONDecodeError:
            print("Invalid JSON.")
