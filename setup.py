#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#
from __future__ import print_function
from setuptools import setup, find_packages
import os
import os.path

NAME='ros3dui'
VERSION = '0.1'

install_requires = ['tornado']
tests_require = []

ROOT = os.path.dirname(__file__)

def read(fpath):
    """Load file contents"""
    with open(os.path.join(ROOT, fpath)) as inf:
        return inf.read()

def find_data(fpath, prefix=''):
    def walk_helper(outentries, dirname, files):
        for fentry in files:
            full = os.path.join(dirname, fentry)
            # skip directories
            if os.path.isdir(full):
                continue
            outentries.append((os.path.join(prefix, dirname), [full]))

    outentries = []
    os.path.walk(fpath, walk_helper, outentries)
    print ("data files:", outentries)
    return outentries


setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(exclude=['tests', 'tests.*']),
    description="Ros3D Web UI",
    long_description=read("README.rst"),
    install_requires=install_requires,
    tests_require=tests_require,
    author='OpenRnD',
    author_email='ros3d@open-rnd.pl',
    license='closed',
    data_files=find_data('web-data') + ['ros3d-ui-service-reload'],
    scripts=['ros3d-ui']
)
