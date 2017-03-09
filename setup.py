# -*- coding: utf-8 -*-
"""
netflix-browser
===============

Simple web browser for Netflix.

More details on project's README and
`github page <https://github.com/ergoithz/netflix-browser/>`_.

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

sys_path = sys.path[:]
sys.path[:] = (os.path.abspath('netflix'),)
__import__('__meta__')
sys.path[:] = sys_path

meta = sys.modules['__meta__']
meta_app = meta.__app__
meta_version = meta.__version__
meta_license = meta.__license__
meta_repo = 'https://github.com/ergoithz/netflix-browser'

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
    description='Simple web browser for Netflix',
    long_description=meta_doc,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    keywords=['web', 'file', 'browser'],
    packages=[
        'netflix_browser',
        ],
    entry_points={
        'console_scripts': (
            'netflix-browser=netflix_browser.__main__:main'
        )
    },
    package_data={  # ignored by sdist (see MANIFEST.in), used by bdist_wheel
        'browsepy': [
            'netflix_browser/layout.glade'
            ]
        },
    install_requires=['python-gobject'],
    zip_safe=True,
    platforms='any'
)
