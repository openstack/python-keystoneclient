import os
import sys
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

requirements = ['httplib2', 'argparse', 'prettytable']
if sys.version_info < (2, 6):
    requirements.append('simplejson')

setup(
    name = "python-keystoneclient",
    version = "2012.1",
    description = "Client library for OpenStack Keystone API",
    long_description = read('README.rst'),
    url = 'https://github.com/openstack/python-keystoneclient',
    license = 'Apache',
    author = 'Nebula Inc, based on work by Rackspace and Jacob Kaplan-Moss',
    author_email = 'gabriel.hurley@nebula.com',
    packages = find_packages(exclude=['tests', 'tests.*']),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires = requirements,

    tests_require = ["nose", "mock", "mox"],
    test_suite = "nose.collector",

    entry_points = {
        'console_scripts': ['keystone = keystoneclient.shell:main']
    }
)
