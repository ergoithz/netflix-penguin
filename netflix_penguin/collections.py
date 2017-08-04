
import collections


class AttrMappingMixin(object):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class AttrDict(dict, AttrMappingMixin):
    pass


class AttrDefaultDict(collections.defaultdict, AttrMappingMixin):
    pass
