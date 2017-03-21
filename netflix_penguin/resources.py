
import os
import os.path
import appdirs

from . import __meta__ as meta

dirs = appdirs.AppDirs(meta.__app__, meta.__org__)
layout = os.path.join(meta.__basedir__, 'layout.glade')
cookie_storage = os.path.join(dirs.user_cache_dir, 'storage')


def create_dirs():
    config_files = [cookie_storage]
    for dirname in map(os.path.dirname, config_files):
        if not os.path.exists(dirname):
            os.makedirs(dirname)
