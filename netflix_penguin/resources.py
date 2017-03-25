
import os
import os.path
import appdirs

from . import __meta__ as meta

dirs = appdirs.AppDirs(meta.__app__, meta.__org__)
layout = os.path.join(meta.__basedir__, 'layout.glade')
menu = os.path.join(meta.__basedir__, 'menu.xml')
cache_dir = dirs.user_cache_dir
storage = os.path.join(cache_dir, 'storage')


def create_dirs():
    for dirname in [cache_dir]:
        if not os.path.exists(dirname):
            os.makedirs(dirname)


def count_cache_size():
    return count_size([cache_dir])


def count_size(directories):
    join = os.path.join
    getsize = os.path.getsize
    return sum(
        getsize(join(root, name))
        for directory in directories
        for root, dirs, files in os.walk(directory)
        for name in files
        )
