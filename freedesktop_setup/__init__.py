
from setuptools.command.install import install as BaseInstall
from setuptools.dist import Distribution as BaseDistribution

from .freedesktop import install_desktop
from .icons import update_icons


class install(BaseInstall):
    sub_commands = BaseInstall.sub_commands + [
        ('install_desktop', None),
        ('update_icons', None),
        ]


class Distribution(BaseDistribution):
    default_cmdclass = {
        'install': install,
        'install_desktop': install_desktop,
        'update_icons': update_icons,
        }

    desktop_entries = None
    icon_themes_dir = None

    def __init__(self, attrs):
        cmdclass = self.default_cmdclass.copy()
        cmdclass.update(attrs.get('cmdclass', ()))
        attrs['cmdclass'] = cmdclass
        super(Distribution, self).__init__(attrs)
