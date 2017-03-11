
import os
import os.path
import subprocess

from distutils import log
from distutils.core import Command
from distutils.errors import DistutilsSetupError
from distutils.util import change_root, convert_path


class update_icons(Command):
    '''Distutils subcommand to regenerate icon cache'''

    description = 'Regenerates icon cache based on data files'

    user_options = [
        ('install-dir=', 'd',
         "base directory for installing data files "
         "(default: installation base dir)"),
        ('icon-themes-dir=', 'd',
         "base directory for icon themes "
         "(default: {install-dir}/share/icons)"),
        ('root=', None,
         "install everything relative to this alternate root directory"),
        ('force', 'f', "force installation (overwrite existing files)"),
        ]

    boolean_options = ['force']

    def initialize_options(self):
        self.install_dir = None
        self.icon_themes_dir = None
        self.root = None
        self.force = 0
        self.data_files = self.distribution.data_files

    def finalize_options(self):
        self.set_undefined_options(
            'install',
            ('install_data', 'install_dir'),
            # ('icon_themes_dir', 'icon_themes_dir'),
            ('root', 'root'),
            ('force', 'force'),
            )

    def convert_path(self, path):
        path = convert_path(path)
        if not os.path.isabs(path):
            return os.path.join(self.install_dir, path)
        elif self.root:
            return change_root(self.root, path)
        return path

    def run(self):
        dist = self.distribution
        prefix = self.convert_path(self.icon_themes_dir or 'share/icons')
        themes = set()

        for spec in dist.data_files or ():
            if isinstance(spec, str) or not all(spec):
                continue
            dest = self.convert_path(spec[0])
            if not dest.startswith(prefix + os.sep):
                continue
            name, icon = os.path.relpath(dest, prefix).split(os.sep, 1)
            themes.add(name)

        for name in themes:
            path = os.path.join(prefix, name)
            cachefile = os.path.join(path, '.icon-theme.cache')
            permission = (
                os.access(cachefile, os.W_OK) or
                os.access(path, os.W_OK) and not os.path.exists(cachefile)
                )
            if permission or self.force:
                log.info('updating %s' % cachefile)
                err = subprocess.call(['gtk-update-icon-cache', '-f', path])
                if err:
                    log.error('gtk-update-icon-cache call failed')
            elif self.force:
                raise DistutilsSetupError(
                    'no write permissions for %r' % cachefile
                    )
            else:
                log.error('no write permissions for %r' % cachefile)

    def get_inputs(self):
        return []

    def get_outputs(self):
        return []
