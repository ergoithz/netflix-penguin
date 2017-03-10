# -*- coding: utf-8 -*-
"""
netflix-penguin
===============

Simple web browser for Netflix.

More details on project's README and
`github page <https://github.com/ergoithz/netflix-penguin/>`_.

License
-------
GPLv3 (see LICENSE file).
"""

import os
import os.path
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

meta_module = 'netflix_penguin'

sys_path = sys.path[:]
sys.path[:] = (os.path.abspath(meta_module),)
__import__('__meta__')
sys.path[:] = sys_path

meta = sys.modules['__meta__']
meta_app = meta.__app__
meta_name = meta.__appname__
meta_description = meta.__description__
meta_version = meta.__version__
meta_license = meta.__license__
meta_organization = meta.__org__
meta_repo = 'https://github.com/%s/%s' % (
    meta_organization,
    meta_app
    )

with open('README.rst') as f:
    meta_doc = f.read()

extra_requires = []

if not hasattr(os, 'scandir') or 'bdist_wheel' in sys.argv:
    extra_requires.append('scandir')

for debugger in ('ipdb', 'pudb', 'pdb'):
    opt = '--debug=%s' % debugger
    if opt in sys.argv:
        os.environ['UNITTEST_DEBUG'] = debugger
        sys.argv.remove(opt)

setup(
    name=meta_app,
    version=meta_version,
    url=meta_repo,
    download_url='%s/archive/%s.tar.gz' % (meta_repo, meta_version),
    license=meta_license,
    author='Felipe A. Hernandez',
    author_email='ergoithz@gmail.com',
    description=meta_description,
    long_description=meta_doc,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        ],
    keywords=['web', 'browser'],
    packages=[meta_module],
    entry_points={
        'console_scripts': ['%s=%s.__main__:main' % (meta_app, meta_module)],
        'gui_scripts': ['%s=%s.__main__:main' % (meta_app, meta_module)],
        },
    desktop_entries={
        meta_app: {
            'Name': meta_name,
            'GenericName': meta_description,
            'Categories': 'AudioVideo;Video;Network;Player;',
            'Icon': meta_app,
            'StartupNotify': 'true',
            },
        },
    package_data={meta_module: ['layout.glade']},
    data_files=[(
            'share/icons/hicolor/{0}x{0}/apps'.format(size),
            ['icons/{}/{}.png'.format(size, meta_app)])
            for size in (16, 22, 24, 32, 48, 128, 256, 512)
        ] + [
            ('share/icons/hicolor/scalable/apps', ['icons/%s.svg' % meta_app])
        ],
    setup_requires=['install_freedesktop'],
    install_requires=['pygobject', 'appdirs'],
    zip_safe=True,
    platforms='any'
    )
