# Copyright 2016 Felipe A. Hernandez
# Copyright 2015 Jacob Welsh
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from distutils import log
from distutils.core import Command


class install_desktop(Command):
    '''Distutils subcommand to generate desktop entry files'''

    description = 'Generate and install desktop entry files'

    user_options = [
        ('script-dir=', None, 'installation directory for Python scripts'),
        ('data-dir=', None, 'installation directory for data files'),
        ]

    def initialize_options(self):
        self.root = None
        self.data_dir = None
        self.script_dir = None
        self.outfiles = []

    def finalize_options(self):
        self.set_undefined_options(
            'install',
            ('root', 'root'),
            ('install_data', 'data_dir'),
            ('install_scripts', 'script_dir'),
            )

    def run(self):
        dist = self.distribution
        if dist.desktop_entries is None:
            desktop_entries = {}
        else:
            desktop_entries = dist.desktop_entries

        scripts = set(desktop_entries.keys())

        if dist.entry_points and 'gui_scripts' in dist.entry_points:
            scripts.update(
                s.split('=')[0].strip()
                for s in dist.entry_points['gui_scripts']
                )

        if not scripts:
            return

        if not self.root:
            self.root = '/'

        target_script_dir = '/' + os.path.relpath(self.script_dir, self.root)

        current_umask = os.umask(0)
        os.umask(current_umask)

        dest_dir = os.path.join(self.data_dir, 'share/applications')
        self.mkpath(dest_dir)

        for script in scripts:
            data = {
                'Name': script,
                'Icon': script,
                'Type': 'Application',
                'Exec': os.path.join(target_script_dir, script)
            }
            data.update(desktop_entries.get(script) or ())
            dest_file = os.path.join(dest_dir, '%s.desktop' % script)

            log.info('writing ' + dest_file)
            with open(dest_file, 'w') as f:
                f.write('[Desktop Entry]\n')
                f.writelines([
                    '%s=%s\n' % (key, value)
                    for key, value in sorted(data.items())
                    ])
            os.chmod(dest_file, 0o777 - current_umask)
            self.outfiles.append(dest_file)

    def get_inputs(self):
        return []

    def get_outputs(self):
        return self.outfiles
