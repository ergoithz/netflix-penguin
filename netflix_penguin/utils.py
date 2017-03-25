import math


SIZE_UNITS = ('bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')


def human_size(size, units=SIZE_UNITS):
    order = int(math.log2(size) / 10) if size else 0
    return '{:.3g} {}'.format(size / (1 << (order * 10)), units[order])
