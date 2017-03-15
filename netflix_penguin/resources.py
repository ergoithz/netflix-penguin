
import os.path
import appdirs

from . import __meta__ as meta

dirs = appdirs.AppDirs(meta.__app__, meta.__org__)
layout = os.path.join(meta.__basedir__, 'layout.glade')
cookie_storage = os.path.join(dirs.user_cache_dir, 'storage')
