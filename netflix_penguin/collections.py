
import collections


class AttrDefaultDict(collections.defaultdict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value
