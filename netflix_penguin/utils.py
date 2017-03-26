import math


SIZE_UNITS = ('bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')


def human_size(size, units=SIZE_UNITS):
    order = int(math.log2(size) / 10) if size else 0
    return '{:.3g} {}'.format(size / (1 << (order * 10)), units[order])


def gtk_set(obj, properties):
    for spec, value in properties.items():
        pobj = obj
        spec = spec.split('.')
        prop = spec.pop()
        for child in spec:
            pobj = getattr(pobj, child)
        getattr(pobj, 'set_%s' % prop.replace('-', '_'))(value)
