import os
import sys
import setuptools

from keystoneclient.openstack.common import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

requires = setup.parse_requirements()
depend_links = setup.parse_dependency_links()
tests_require = setup.parse_requirements(['tools/test-requires'])

setuptools.setup(
    name="python-keystoneclient",
    version=setup.get_post_version('keystoneclient'),
    description="Client library for OpenStack Identity API (Keystone)",
    long_description=read('README.rst'),
    url='https://github.com/openstack/python-keystoneclient',
    license='Apache',
    author='Nebula Inc, based on work by Rackspace and Jacob Kaplan-Moss',
    author_email='gabriel.hurley@nebula.com',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: OpenStack',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=requires,
    dependency_links=depend_links,
    cmdclass=setup.get_cmdclass(),

    tests_require=tests_require,
    test_suite="nose.collector",

    entry_points={
        'console_scripts': ['keystone = keystoneclient.shell:main']
    },
    data_files=[('keystoneclient', ['keystoneclient/versioninfo'])],
)
