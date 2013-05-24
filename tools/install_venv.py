# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2010 OpenStack, LLC
# Copyright 2013 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Installation script for python-keystoneclient's development virtualenv
"""

import os
import subprocess
import sys

import install_venv_common as install_venv


class Debian(install_venv.Distro):
    """This covers all Debian-based distributions."""

    def check_pkg(self, pkg):
        return run_command_with_code(['dpkg', '-l', pkg],
                                     check_exit_code=False)[1] == 0

    def apt_install(self, pkg, **kwargs):
        run_command(['sudo', 'apt-get', 'install', '-y', pkg], **kwargs)

    def apply_patch(self, originalfile, patchfile):
        run_command(['patch', originalfile, patchfile])

    def install_virtualenv(self):
        if self.check_cmd('virtualenv'):
            return

        if not self.check_pkg('python-virtualenv'):
            self.apt_install('python-virtualenv', check_exit_code=False)

        super(Debian, self).install_virtualenv()


class Suse(install_venv.Distro):
    """This covers all SuSE distributions."""

    def check_pkg(self, pkg):
        return run_command_with_code(['rpm', '-q', pkg],
                                     check_exit_code=False)[1] == 0

    def zypper_install(self, pkg, **kwargs):
        run_command(['sudo', 'zypper', '-qn', 'install', pkg], **kwargs)

    def apply_patch(self, originalfile, patchfile):
        run_command(['patch', originalfile, patchfile])

    def install_virtualenv(self):
        if self.check_cmd('virtualenv'):
            return

        if not self.check_pkg('python-virtualenv'):
            self.zypper_install('python-virtualenv', check_exit_code=False)

        super(Suse, self).install_virtualenv()


def print_help():
    help = """
    python-keystoneclient development environment setup is complete.

    python-keystoneclient development uses virtualenv to track and manage
    Python dependencies while in development and testing.

    To activate the python-keystoneclient virtualenv for the extent of your
    current shell session you can run:

    $ source .venv/bin/activate

    Or, if you prefer, you can run commands in the virtualenv on a case by case
    basis by running:

    $ tools/with_venv.sh <your command>

    Also, make test will automatically use the virtualenv.
    """
    print help


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    venv = os.path.join(root, '.venv')
    pip_requires = os.path.join(root, 'requirements.txt')
    test_requires = os.path.join(root, 'test-requirements.txt')
    py_version = "python%s.%s" % (sys.version_info[0], sys.version_info[1])
    project = 'python-keystoneclient'
    install = install_venv.InstallVenv(root, venv, pip_requires, test_requires,
                                       py_version, project)
    if os.path.exists('/etc/SuSE-release'):
        install_venv.Distro = Suse
    elif os.path.exists('/etc/debian_version'):
        install_venv.Distro = Debian
    options = install.parse_args(argv)
    install.check_python_version()
    install.check_dependencies()
    install.create_virtualenv(no_site_packages=options.no_site_packages)
    install.install_dependencies()
    install.run_command([os.path.join(venv, 'bin/python'),
                        'setup.py', 'develop'])
    install.post_process()
    print_help()


if __name__ == '__main__':
    main(sys.argv)
